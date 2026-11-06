import argparse
from pathlib import Path
from typing import Iterator, Tuple

from person_searcher.ingestion import CropWriter
from person_searcher.storage import SQLiteStore
from person_searcher.vision.yolo import YOLOPersonDetector, detection_to_record


def iter_frames(images_root: Path) -> Iterator[Tuple[Path, str, int]]:
    for image_path in sorted(images_root.rglob("*.jpg")):
        if not image_path.stem.startswith("frame_"):
            continue
        try:
            frame_number = int(image_path.stem.removeprefix("frame_"))
        except ValueError:
            continue
        yield image_path, image_path.parent.name, frame_number


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect people with YOLO and store crops.")
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--event-class", required=True)
    parser.add_argument("--split", default="inference")
    parser.add_argument("--database", type=Path, default=Path("artifacts/search.db"))
    parser.add_argument("--crops", type=Path, default=Path("artifacts/crops"))
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    if args.limit < 0:
        parser.error("--limit must be >= 0")

    detector = YOLOPersonDetector(args.model, args.confidence)
    writer = CropWriter(args.crops)
    store = SQLiteStore(args.database)
    store.initialize()
    detections = []
    frames_seen = 0
    for image_path, video_id, frame_number in iter_frames(args.images):
        frames_seen += 1
        for detection in detector.detect(image_path):
            record = detection_to_record(
                image_path,
                detection,
                split=args.split,
                event_class=args.event_class,
                video_id=video_id,
                frame_number=frame_number,
            )
            detections.append((record, writer.write(record)))
        store.add_detections(detections)
        detections.clear()
        if args.limit and frames_seen >= args.limit:
            break
    print(f"Processed {frames_seen} frames and stored {len(detections)} detections.")


if __name__ == "__main__":
    main()
