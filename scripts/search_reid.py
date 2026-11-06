import argparse
import json
import sqlite3
from pathlib import Path

from person_searcher.query.ollama_parser import OllamaQueryParser
from person_searcher.storage import DetectionRepository
from person_searcher.storage.few_shot import FewShotStore
from person_searcher.vision.reid import rank_similar_crops


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rank person crops by lightweight visual similarity."
    )
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--database", type=Path, default=Path("artifacts/search.db"))
    parser.add_argument("--query", help="Optional natural-language candidate filter")
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if args.limit <= 0:
        parser.error("--limit must be greater than zero.")
    if not args.database.exists():
        parser.error(f"Database does not exist: {args.database}")
    if not args.reference.is_file():
        parser.error(f"Reference image does not exist: {args.reference}")

    repository = DetectionRepository(args.database)
    try:
        condition = None
        if args.query:
            examples = FewShotStore(args.database)
            examples.initialize()
            condition = OllamaQueryParser(
                model=args.model,
                examples=examples,
            ).parse(args.query)
            candidates = repository.search_attributes(condition, limit=args.limit)
        else:
            candidates = repository.find(category="person", limit=args.limit)
        ranked = rank_similar_crops(args.reference, candidates)
    except (RuntimeError, ValueError, FileNotFoundError, sqlite3.Error) as exc:
        raise SystemExit(f"Re-ID search failed: {exc}") from exc

    if condition is not None:
        print("Parsed condition:")
        print(json.dumps(condition.model_dump(), ensure_ascii=False, indent=2))
    print("\nRanked matches:")
    print(json.dumps(ranked, ensure_ascii=False, indent=2))
    print(f"\n총 {len(ranked)}건")


if __name__ == "__main__":
    main()
