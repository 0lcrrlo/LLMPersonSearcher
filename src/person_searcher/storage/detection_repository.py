import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from person_searcher.domain.models import ItemCondition, PersonSearchCondition
from person_searcher.domain.taxonomy import normalize_condition


class DetectionRepository:
    """Read event-related person detections from the indexed SQLite store."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def find(
        self,
        *,
        event_class: Optional[str] = None,
        split: Optional[str] = None,
        video_id: Optional[str] = None,
        global_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, object]]:
        if limit <= 0:
            raise ValueError("limit must be greater than zero.")

        clauses = []
        parameters: List[object] = []
        filters = {
            "event_class": event_class,
            "split": split,
            "video_id": video_id,
            "global_id": global_id,
            "category": category,
        }
        for column, value in filters.items():
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)

        query = """
            SELECT id, split, event_class, video_id, source_video,
                   frame_number, global_id, category, annotation_index,
                   source_image, crop_path, x, y, width, height
            FROM person_detection
        """
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY video_id, frame_number, annotation_index LIMIT ?"
        parameters.append(limit)

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def attributes_for(self, detection_id: int) -> List[Dict[str, object]]:
        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, detection_id, attribute_group, category, color,
                       item_type, confidence, source
                FROM person_attribute
                WHERE detection_id = ?
                ORDER BY attribute_group, category, color, item_type
                """,
                (detection_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def search_attributes(
        self,
        condition: PersonSearchCondition,
        *,
        limit: int = 100,
    ) -> List[Dict[str, object]]:
        """Find detections whose stored attributes satisfy every query item."""

        if limit <= 0:
            raise ValueError("limit must be greater than zero.")
        if condition.gender:
            raise ValueError(
                "gender search is not supported until gender is stored as an attribute."
            )

        normalized = normalize_condition(condition)
        items = [
            ("clothing", item) for item in normalized.clothing
        ] + [
            ("accessories", item) for item in normalized.accessories
        ]
        if not items:
            raise ValueError("at least one clothing or accessory condition is required.")

        clauses: List[str] = []
        parameters: List[object] = []
        for group, item in items:
            if not _has_constraints(item):
                continue
            match = [
                "attribute.detection_id = detection.id",
                "attribute.attribute_group = ?",
            ]
            parameters.append(group)
            if item.category:
                match.append("attribute.category = ?")
                parameters.append(item.category)
            if item.colors:
                placeholders = ", ".join("?" for _ in item.colors)
                match.append(f"attribute.color IN ({placeholders})")
                parameters.extend(item.colors)
            if item.item_type:
                match.append("attribute.item_type = ?")
                parameters.append(item.item_type)
            clauses.append(
                "EXISTS (SELECT 1 FROM person_attribute AS attribute WHERE "
                + " AND ".join(match)
                + ")"
            )

        if not clauses:
            raise ValueError("at least one non-empty attribute condition is required.")

        query = """
            SELECT detection.id, detection.split, detection.event_class,
                   detection.video_id, detection.source_video,
                   detection.frame_number, detection.global_id,
                   detection.category, detection.annotation_index,
                   detection.source_image, detection.crop_path,
                   detection.x, detection.y, detection.width, detection.height
            FROM person_detection AS detection
            WHERE
        """ + " AND ".join(clauses)
        query += """
            ORDER BY detection.video_id, detection.frame_number,
                     detection.annotation_index
            LIMIT ?
        """
        parameters.append(limit)

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]


def _has_constraints(item: ItemCondition) -> bool:
    return bool(item.category or item.colors or item.item_type)
