import math
from pathlib import Path
from typing import Dict, Iterable, List

from PIL import Image


class ColorHistogramEmbedder:
    """Create a lightweight, model-free visual embedding for a crop."""

    def __init__(self, bins_per_channel: int = 8) -> None:
        if bins_per_channel <= 0:
            raise ValueError("bins_per_channel must be greater than zero.")
        self.bins_per_channel = bins_per_channel

    def embed(self, image_path: Path) -> List[float]:
        if not image_path.is_file():
            raise FileNotFoundError(f"Image does not exist: {image_path}")
        with Image.open(image_path) as image:
            resized = image.convert("RGB").resize((64, 128))
            pixels = [
                resized.getpixel((x, y))
                for y in range(resized.height)
                for x in range(resized.width)
            ]

        bins = self.bins_per_channel
        histogram = [0.0] * (bins * 3)
        for red, green, blue in pixels:
            for channel, value in enumerate((red, green, blue)):
                bucket = min(value * bins // 256, bins - 1)
                histogram[channel * bins + bucket] += 1.0
        norm = math.sqrt(sum(value * value for value in histogram))
        if norm == 0.0:
            raise ValueError(f"Unable to create an embedding for: {image_path}")
        return [value / norm for value in histogram]


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    left_values = list(left)
    right_values = list(right)
    if len(left_values) != len(right_values) or not left_values:
        raise ValueError("Embeddings must be non-empty and have the same size.")
    return sum(a * b for a, b in zip(left_values, right_values))


def rank_similar_crops(
    reference_path: Path,
    candidates: Iterable[Dict[str, object]],
    *,
    embedder: ColorHistogramEmbedder | None = None,
) -> List[Dict[str, object]]:
    """Return candidate detections ranked by visual similarity."""

    active_embedder = embedder or ColorHistogramEmbedder()
    reference = active_embedder.embed(reference_path)
    ranked: List[Dict[str, object]] = []
    for candidate in candidates:
        crop_path = Path(str(candidate["crop_path"]))
        score = cosine_similarity(reference, active_embedder.embed(crop_path))
        ranked.append({**candidate, "similarity": round(score, 6)})
    return sorted(
        ranked,
        key=lambda result: float(result["similarity"]),
        reverse=True,
    )
