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
    args = parser.parse_args()

    reader = AnnotationReader(args.annotations, args.images)
    writer = CropWriter(args.crops)
    store = SQLiteStore(args.database)
    args.database.parent.mkdir(parents=True, exist_ok=True)
    store.initialize()

    count = 0
    for record in reader.records():
        crop_path = writer.write(record)
        store.add_detection(record, crop_path)
        count += 1
    print(f"Ingested {count} person detections.")


if __name__ == "__main__":
    main()
