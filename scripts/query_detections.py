import argparse
import json
from pathlib import Path

from person_searcher.storage import DetectionRepository


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query event-related person detections from SQLite."
    )
    parser.add_argument("--database", type=Path, default=Path("artifacts/search.db"))
    parser.add_argument("--event-class")
    parser.add_argument("--split")
    parser.add_argument("--video-id")
    parser.add_argument("--global-id")
    parser.add_argument("--category", choices=["person", "child"])
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if args.limit <= 0:
        parser.error("--limit must be greater than zero.")
    if not args.database.exists():
        parser.error(f"Database does not exist: {args.database}")

    repository = DetectionRepository(args.database)
    results = repository.find(
        event_class=args.event_class,
        split=args.split,
        video_id=args.video_id,
        global_id=args.global_id,
        category=args.category,
        limit=args.limit,
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n총 {len(results)}건")


if __name__ == "__main__":
    main()
