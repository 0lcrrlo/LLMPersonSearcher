import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from person_searcher.domain.models import PersonAttribute

class SQLiteStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS person_detection (
                    id INTEGER PRIMARY KEY,
                    split TEXT NOT NULL,
                    event_class TEXT NOT NULL,
                    video_id TEXT NOT NULL,
                    source_video TEXT NOT NULL,
                    frame_number INTEGER NOT NULL,
                    global_id TEXT,
                    category TEXT NOT NULL,
                    annotation_index INTEGER NOT NULL,
                    source_image TEXT NOT NULL,
                    crop_path TEXT NOT NULL,
                    x INTEGER NOT NULL,
                    y INTEGER NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_detection_video_frame
                    ON person_detection(video_id, frame_number);
                CREATE INDEX IF NOT EXISTS idx_detection_global_id
                    ON person_detection(global_id);
                CREATE INDEX IF NOT EXISTS idx_detection_event
                    ON person_detection(event_class, split);
                CREATE INDEX IF NOT EXISTS idx_detection_category
                    ON person_detection(category);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_detection_unique
                    ON person_detection(video_id, frame_number, annotation_index);
                CREATE TABLE IF NOT EXISTS person_attribute (
                    id INTEGER PRIMARY KEY,
                    detection_id INTEGER NOT NULL,
                    attribute_group TEXT NOT NULL
                        CHECK (attribute_group IN ('clothing', 'accessories')),
                    category TEXT NOT NULL,
                    color TEXT,
                    item_type TEXT,
                    confidence REAL CHECK (
                        confidence IS NULL OR (confidence >= 0 AND confidence <= 1)
                    ),
                    source TEXT NOT NULL,
                    FOREIGN KEY (detection_id) REFERENCES person_detection(id),
                    UNIQUE (
                        detection_id, attribute_group, category, color, item_type, source
                    )
                );
                CREATE INDEX IF NOT EXISTS idx_attribute_detection
                    ON person_attribute(detection_id);
                CREATE INDEX IF NOT EXISTS idx_attribute_lookup
                    ON person_attribute(attribute_group, category, color, item_type);
                """
            )

    def add_detection(self, record: Dict[str, object], crop_path: Path) -> None:
        self.add_detections([(record, crop_path)])

    def add_detections(
        self, detections: Iterable[Tuple[Dict[str, object], Path]]
    ) -> None:
        rows = [
            (
                record["split"],
                record["event_class"],
                record["video_id"],
                record["source_video"],
                record["frame_number"],
                record["global_id"],
                record["category"],
                record["annotation_index"],
                record["image_path"],
                str(crop_path),
                record["x"],
                record["y"],
                record["width"],
                record["height"],
            )
            for record, crop_path in detections
        ]
        if not rows:
            return
        with sqlite3.connect(self.database_path) as connection:
            connection.executemany(
                """
                INSERT OR IGNORE INTO person_detection
                (split, event_class, video_id, source_video, frame_number,
                 global_id, category, annotation_index, source_image, crop_path,
                 x, y, width, height)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def add_attributes(self, attributes: Iterable[PersonAttribute]) -> None:
        rows = [
            (
                attribute.detection_id,
                attribute.attribute_group,
                attribute.category,
                attribute.color,
                attribute.item_type,
                attribute.confidence,
                attribute.source,
            )
            for attribute in attributes
        ]
        if not rows:
            return
        with sqlite3.connect(self.database_path) as connection:
            connection.executemany(
                """
                INSERT OR IGNORE INTO person_attribute
                (detection_id, attribute_group, category, color, item_type,
                 confidence, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
