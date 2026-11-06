"""Dataset annotation and crop ingestion."""

from .annotations import AnnotationReader
from .attributes import load_manual_attributes
from .cropper import CropWriter

__all__ = ["AnnotationReader", "CropWriter", "load_manual_attributes"]
