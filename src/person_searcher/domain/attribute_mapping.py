from typing import List

from .models import PersonAttribute, PersonSearchCondition
from .taxonomy import normalize_condition


def condition_to_attributes(
    detection_id: int,
    condition: PersonSearchCondition,
    *,
    confidence: float = 1.0,
    source: str = "vision",
) -> List[PersonAttribute]:
    """Map normalized condition fields to rows in ``person_attribute``.

    ``ItemCondition.colors`` is a list for LLM queries, while the database
    stores one color per row so each attribute remains independently indexed.
    """

    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1.")

    normalized = normalize_condition(condition)
    attributes: List[PersonAttribute] = []
    for group_name in ("clothing", "accessories"):
        for item in getattr(normalized, group_name):
            colors = item.colors or [None]
            for color in colors:
                attributes.append(
                    PersonAttribute(
                        detection_id=detection_id,
                        attribute_group=group_name,
                        category=item.category,
                        color=color,
                        item_type=item.item_type or None,
                        confidence=confidence,
                        source=source,
                    )
                )
    return attributes
