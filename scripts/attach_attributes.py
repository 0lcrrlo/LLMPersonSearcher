import argparse
import sqlite3
from pathlib import Path

from person_searcher.ingestion.attributes import load_manual_attributes
from person_searcher.storage.sqlite import SQLiteStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Attach manually labeled attributes to stored detections."
    )
    parser.add_argument("--database", type=Path, default=Path("artifacts/search.db"))
    parser.add_argument("--attributes", type=Path, required=True)
    args = parser.parse_args()

    if not args.database.exists():
        parser.error(f"Database does not exist: {args.database}")
    try:
        attributes = load_manual_attributes(args.attributes)
        with sqlite3.connect(args.database) as connection:
            ids = {
                row[0]
                for row in connection.execute("SELECT id FROM person_detection")
            }
        unknown_ids = sorted(
            {attribute.detection_id for attribute in attributes} - ids
        )
        if unknown_ids:
            raise ValueError(
                "Attribute JSON references unknown detection IDs: "
                + ", ".join(str(value) for value in unknown_ids)
            )
        SQLiteStore(args.database).add_attributes(attributes)
    except (OSError, ValueError, sqlite3.Error) as exc:
        raise SystemExit(f"Attribute ingestion failed: {exc}") from exc

    print(f"Attached {len(attributes)} attributes.")


if __name__ == "__main__":
    main()
