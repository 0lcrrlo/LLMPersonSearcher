"""Persistence adapters."""

from .few_shot import FewShotStore
from .detection_repository import DetectionRepository

__all__ = ["DetectionRepository", "FewShotStore"]
