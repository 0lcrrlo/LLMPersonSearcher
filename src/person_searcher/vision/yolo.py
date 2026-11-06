from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional


class YOLOPersonDetector:
    """Run Ultralytics YOLO and expose only person detections."""

    def __init__(
        self,
        model_name: str = "yolo11n.pt",
        confidence: float = 0.25,
        model: Any = None,
    ) -> None:
        if not 0 < confidence <= 1:
            raise ValueError("confidence must be greater than 0 and at most 1.")
        self.model_name = model_name
        self.confidence = confidence
        self._model = model

    @property
    def model(self) -> Any:
        if self._model is None:
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise RuntimeError(
                    "YOLO detection requires the 'ultralytics' package. "
                    "Install it with: pip install -e '.[yolo]'"
                ) from exc
            self._model = YOLO(self.model_name)
        return self._model

    def detect(self, image_path: Path) -> Iterator[Dict[str, object]]:
        results = self.model.predict(
            source=str(image_path),
            conf=self.confidence,
            verbose=False,
        )
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            names = getattr(result, "names", {})
            for index, box in enumerate(boxes):
                class_id = int(box.cls[0].item())
                class_name = names.get(class_id, str(class_id))
                if class_name != "person":
                    continue
                coordinates = box.xyxy[0].tolist()
                yield {
                    "detection_index": index,
                    "class_name": class_name,
                    "confidence": float(box.conf[0].item()),
                    "x": max(0, round(coordinates[0])),
                    "y": max(0, round(coordinates[1])),
                    "x2": max(0, round(coordinates[2])),
                    "y2": max(0, round(coordinates[3])),
                }


def detection_to_record(
    image_path: Path,
    detection: Dict[str, object],
    *,
    split: str,
    event_class: str,
    video_id: str,
    frame_number: int,
    source_video: str = "",
) -> Dict[str, object]:
    """Convert a YOLO box into the common person_detection input record."""

    x = int(detection["x"])
    y = int(detection["y"])
    x2 = int(detection["x2"])
    y2 = int(detection["y2"])
    return {
        "split": split,
        "event_class": event_class,
        "video_id": video_id,
        "source_video": source_video,
        "frame_number": frame_number,
        "image_path": str(image_path),
        "category": "person",
        "annotation_index": int(detection["detection_index"]),
        "global_id": f"yolo:{video_id}:{frame_number}:{detection['detection_index']}",
        "x": x,
        "y": y,
        "width": max(0, x2 - x),
        "height": max(0, y2 - y),
        "confidence": float(detection["confidence"]),
    }
