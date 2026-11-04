import json
from typing import Any, Dict

from person_searcher.domain.models import PersonSearchCondition
from person_searcher.domain.taxonomy import normalize_condition


class OllamaQueryParser:
    """Parse structured search conditions through a local Ollama model."""

    def __init__(self, model: str = "qwen2.5:7b", client: Any = None) -> None:
        self.model = model
        self._client = client

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

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract clothing and accessories from the query. "
                        "Return only the requested JSON schema. Do not invent "
                        "attributes that are not present."
                    ),
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
