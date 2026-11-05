import json
from pathlib import Path
from typing import Dict, Iterator, Optional


class AnnotationReader:
    """Read the dataset's frame annotations and resolve source images."""

    def __init__(self, annotation_root: Path, image_root: Path) -> None:
        self.annotation_root = annotation_root
        self.image_root = image_root

    def records(self) -> Iterator[Dict[str, object]]:
        for annotation_path in sorted(self.annotation_root.rglob("annotation_*.json")):
            payload = json.loads(annotation_path.read_text(encoding="utf-8"))
            video_id = annotation_path.stem
            if video_id.startswith("annotation_"):
                video_id = video_id[len("annotation_") :]
            for frame in payload.get("frames", []):
                image_path = self._find_image(video_id, frame["image"])
                if image_path is None:
                    continue
                for index, annotation in enumerate(frame.get("annotations", [])):
                    category = annotation.get("category", {})
                    if category.get("code") not in {"person", "child"}:
                        continue
                    label = annotation.get("label", {})
                    yield {
                        "video_id": video_id,
                        "frame_number": frame["number"],
                        "image_path": str(image_path),
                        "category": category.get("code"),
                        "annotation_index": index,
                        "global_id": self._global_id(category),
                        "x": label.get("x", 0),
                        "y": label.get("y", 0),
                        "width": label.get("width", 0),
                        "height": label.get("height", 0),
                    }

    def _find_image(self, video_id: str, image_name: str) -> Optional[Path]:
        matches = list(self.image_root.rglob(f"{video_id}/{image_name}"))
        return matches[0] if matches else None

    @staticmethod
    def _global_id(category: Dict[str, object]) -> Optional[str]:
        for attribute in category.get("attributes", []):
            if attribute.get("code") == "global_id":
                return str(attribute.get("value"))
        return None
