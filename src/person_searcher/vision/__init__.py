"""Computer-vision detection adapters."""

from .yolo import YOLOPersonDetector

__all__ = ["YOLOPersonDetector"]
from .reid import ColorHistogramEmbedder, cosine_similarity, rank_similar_crops

__all__ = ["ColorHistogramEmbedder", "cosine_similarity", "rank_similar_crops"]
