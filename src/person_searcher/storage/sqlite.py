import sqlite3
from pathlib import Path
from typing import Dict, Iterable, Tuple

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
