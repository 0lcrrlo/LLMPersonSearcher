import sqlite3
from pathlib import Path
from typing import Dict


class SQLiteStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS person_detection (
                    id INTEGER PRIMARY KEY,
                    video_id TEXT NOT NULL,
                    frame_number INTEGER NOT NULL,
                    global_id TEXT,
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
                """
            )

    def add_detection(self, record: Dict[str, object], crop_path: Path) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO person_detection
                (video_id, frame_number, global_id, source_image, crop_path,
                 x, y, width, height)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["video_id"],
                    record["frame_number"],
                    record["global_id"],
                    record["image_path"],
                    str(crop_path),
                    record["x"],
                    record["y"],
                    record["width"],
                    record["height"],
                ),
            )
