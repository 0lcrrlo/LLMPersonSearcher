from typing import Any, Dict, List

from person_searcher.domain.models import ItemCondition, PersonSearchCondition


def _elem_match(path: str, item: ItemCondition) -> Dict[str, Any]:
    match: Dict[str, Any] = {}
    if item.category:
        match["category"] = item.category
    if item.colors:
        match["color"] = {"$in": item.colors}
    if item.item_type:
        match["type"] = item.item_type
    return {path: {"$elemMatch": match}}


def build_mongo_query(condition: PersonSearchCondition) -> Dict[str, Any]:
    """Build a MongoDB filter while keeping attributes on one array element."""

    clauses: List[Dict[str, Any]] = []
    for item in condition.clothing:
        clause = _elem_match("clothing", item)
        if clause["clothing"]["$elemMatch"]:
            clauses.append(clause)
    for item in condition.accessories:
        clause = _elem_match("accessories", item)
        if clause["accessories"]["$elemMatch"]:
            clauses.append(clause)
    return {"$and": clauses} if clauses else {}
