"""Dataset annotation and crop ingestion."""

from .annotations import AnnotationReader
from .cropper import CropWriter

__all__ = ["AnnotationReader", "CropWriter"]
