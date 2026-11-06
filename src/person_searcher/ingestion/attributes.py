import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from person_searcher.domain.attribute_mapping import condition_to_attributes
from person_searcher.domain.models import PersonSearchCondition, PersonAttribute


def load_manual_attributes(path: Path) -> List[PersonAttribute]:
    """Load detection attributes from a JSON file for the initial demo pipeline."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Unable to read attribute JSON: {path}") from exc
    if not isinstance(payload, list):
        raise ValueError("Attribute JSON must contain a list of detection records.")

    attributes: List[PersonAttribute] = []
    for index, record in enumerate(payload):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index} must be a JSON object.")
        if "detection_id" not in record:
            raise ValueError(f"Record {index} is missing detection_id.")
        try:
            detection_id = int(record["detection_id"])
            condition = PersonSearchCondition.model_validate(
                {key: value for key, value in record.items() if key != "detection_id"}
            )
            confidence = float(record.get("confidence", 1.0))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid attribute record at index {index}.") from exc
        attributes.extend(
            condition_to_attributes(
                detection_id,
                condition,
                confidence=confidence,
                source="manual",
            )
        )
    return attributes
