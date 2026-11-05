import json
from typing import Any, Dict, Optional

from person_searcher.domain.models import PersonSearchCondition
from person_searcher.domain.taxonomy import normalize_condition
from person_searcher.storage.few_shot import FewShotStore


class OllamaQueryParser:
    """Parse structured search conditions through a local Ollama model."""

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        client: Any = None,
        examples: Optional[FewShotStore] = None,
    ) -> None:
        self.model = model
        self._client = client
        self.examples = examples

    @property
    def client(self) -> Any:
        if self._client is None:
            try:
                import ollama
            except ImportError as exc:
                raise RuntimeError(
                    "Ollama parsing requires the 'ollama' package."
                ) from exc
            self._client = ollama
        return self._client

    def parse(self, query: str) -> PersonSearchCondition:
        if not query.strip():
            raise ValueError("Search query must not be empty.")

        system_prompt = (
            "Extract clothing and accessories from the query. "
            "Return only the requested JSON schema. Do not invent "
            "attributes that are not present. Normalize subjective colors: "
            "'어두운' means black, navy, or gray; '밝은' means white or ivory. "
        )
        if self.examples is not None:
            examples = self.examples.prompt_text()
            if examples:
                system_prompt += "\nUse these examples as guidance:\n" + examples

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": query},
            ],
            format=PersonSearchCondition.model_json_schema(),
            options={"temperature": 0.0},
        )
        content = response.message.content
        try:
            payload: Dict[str, Any] = json.loads(content)
            parsed = PersonSearchCondition.model_validate(payload)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError("Ollama returned an invalid search condition.") from exc
        return normalize_condition(parsed)
