import argparse
from pathlib import Path

from person_searcher.ingestion import AnnotationReader, CropWriter
from person_searcher.storage.sqlite import SQLiteStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Create person crops from annotations.")
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--crops", type=Path, default=Path("artifacts/crops"))
    parser.add_argument("--database", type=Path, default=Path("artifacts/search.db"))
    parser.add_argument("--limit", type=int, default=0, help="0 means all records")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--event-class", help="Only ingest one event class")
    args = parser.parse_args()
    if args.limit < 0 or args.batch_size <= 0:
        parser.error("--limit must be >= 0 and --batch-size must be > 0")

    reader = AnnotationReader(args.annotations, args.images)
    writer = CropWriter(args.crops)
    store = SQLiteStore(args.database)
    args.database.parent.mkdir(parents=True, exist_ok=True)
    store.initialize()

    count = 0
    detections = []
    for record in reader.records():
        if args.event_class and record["event_class"] != args.event_class:
            continue
        crop_path = writer.write(record)
        detections.append((record, crop_path))
        count += 1
        if len(detections) >= args.batch_size:
            store.add_detections(detections)
            detections.clear()
        if args.limit and count >= args.limit:
            break
    store.add_detections(detections)
    print(f"Ingested {count} person detections.")


if __name__ == "__main__":
    main()
