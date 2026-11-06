from pathlib import Path
from typing import Dict

from PIL import Image


class CropWriter:
    def __init__(self, output_root: Path) -> None:
        self.output_root = output_root

    def write(self, record: Dict[str, object]) -> Path:
        source = Path(str(record["image_path"]))
        output_dir = (
            self.output_root
            / str(record["split"])
            / str(record["event_class"])
            / str(record["video_id"])
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / (
            f"{record['frame_number']}_{record['annotation_index']}.jpg"
        )
        with Image.open(source) as image:
            left = max(0, int(record["x"]))
            top = max(0, int(record["y"]))
            right = min(image.width, left + max(0, int(record["width"])))
            bottom = min(image.height, top + max(0, int(record["height"])))
            if right <= left or bottom <= top:
                raise ValueError(f"Invalid bounding box in {source}.")
            image.crop((left, top, right, bottom)).save(output_path, quality=95)
        return output_path
