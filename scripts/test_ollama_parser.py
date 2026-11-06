import argparse
import json
from pathlib import Path

from person_searcher.query.ollama_parser import OllamaQueryParser
from person_searcher.storage.few_shot import FewShotStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one real natural-language query through Ollama."
    )
    parser.add_argument("query", help="Natural-language person description")
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--database", type=Path, default=Path("artifacts/search.db"))
    args = parser.parse_args()

    examples = FewShotStore(args.database)
    examples.initialize()
    query_parser = OllamaQueryParser(model=args.model, examples=examples)
    try:
        condition = query_parser.parse(args.query)
    except Exception as exc:
        raise SystemExit(f"Ollama parsing failed: {exc}") from exc

    print(json.dumps(condition.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
