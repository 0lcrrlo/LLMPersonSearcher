import json
import sqlite3
from pathlib import Path
from typing import Iterable, List, Tuple

from person_searcher.domain.models import PersonSearchCondition


DEFAULT_EXAMPLES: Tuple[Tuple[str, PersonSearchCondition], ...] = (
    (
        "어두운 아노락 입은 사람 찾아줘",
        PersonSearchCondition(
            clothing=[
                {
                    "category": "outerwear",
                    "colors": ["black", "navy", "gray"],
                    "item_type": "anorak",
                }
            ]
        ),
    ),
    (
        "빨간 모자 쓴 사람",
        PersonSearchCondition(
            accessories=[
                {
                    "category": "hat",
                    "colors": ["red"],
                    "item_type": "hat",
                }
            ]
        ),
    ),
    (
        "파란 반팔티에 검은 청바지를 입은 사람",
        PersonSearchCondition(
            clothing=[
                {
                    "category": "upper_body",
                    "colors": ["blue"],
                    "item_type": "t_shirt",
                },
                {
                    "category": "lower_body",
                    "colors": ["black"],
                    "item_type": "jeans",
                },
            ]
        ),
    ),
)


class FewShotStore:
    """Persist validated natural-language parsing examples in SQLite."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialize(self, seed_defaults: bool = True) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS few_shot_examples (
                    id INTEGER PRIMARY KEY,
                    natural_query TEXT NOT NULL UNIQUE,
                    parsed_json TEXT NOT NULL
                )
                """
            )
            if seed_defaults:
                for query, condition in DEFAULT_EXAMPLES:
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO few_shot_examples
                        (natural_query, parsed_json) VALUES (?, ?)
                        """,
                        (query, condition.model_dump_json()),
                    )

    def add(self, query: str, condition: PersonSearchCondition) -> None:
        if not query.strip():
            raise ValueError("Few-shot query must not be empty.")
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO few_shot_examples (natural_query, parsed_json)
                VALUES (?, ?)
                ON CONFLICT(natural_query) DO UPDATE SET parsed_json=excluded.parsed_json
                """,
                (query, condition.model_dump_json()),
            )

    def fetch(self, limit: int = 3) -> List[Tuple[str, PersonSearchCondition]]:
        if limit <= 0:
            return []
        with sqlite3.connect(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT natural_query, parsed_json
                FROM few_shot_examples ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            (query, PersonSearchCondition.model_validate(json.loads(payload)))
            for query, payload in rows
        ]

    def prompt_text(self, limit: int = 3) -> str:
        examples = self.fetch(limit)
        return "\n\n".join(
            "Input: {query}\nOutput: {output}".format(
                query=query,
                output=condition.model_dump_json(),
            )
            for query, condition in examples
        )
