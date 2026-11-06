import argparse
import json
from pathlib import Path

from person_searcher.query.ollama_parser import OllamaQueryParser
from person_searcher.storage import DetectionRepository
from person_searcher.storage.few_shot import FewShotStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search stored person crops with a natural-language query."
    )
    parser.add_argument("query", help="Natural-language person description")
    parser.add_argument("--database", type=Path, default=Path("artifacts/search.db"))
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if args.limit <= 0:
        parser.error("--limit must be greater than zero.")
    if not args.database.exists():
        parser.error(f"Database does not exist: {args.database}")

    examples = FewShotStore(args.database)
    examples.initialize()
    try:
        condition = OllamaQueryParser(
            model=args.model,
            examples=examples,
        ).parse(args.query)
        results = DetectionRepository(args.database).search_attributes(
            condition,
            limit=args.limit,
        )
    except Exception as exc:
        raise SystemExit(f"Person search failed: {exc}") from exc

    print("Parsed condition:")
    print(json.dumps(condition.model_dump(), ensure_ascii=False, indent=2))
    print("\nMatches:")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n총 {len(results)}건")


if __name__ == "__main__":
    main()
