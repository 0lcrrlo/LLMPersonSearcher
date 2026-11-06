import sqlite3
from pathlib import Path
from typing import Dict, List, Optional


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
