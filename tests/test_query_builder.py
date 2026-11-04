from person_searcher.domain.models import ItemCondition, PersonSearchCondition
from person_searcher.domain.taxonomy import normalize_condition
from person_searcher.query.builder import build_mongo_query


def test_query_uses_elem_match_for_each_item():
    condition = PersonSearchCondition(
        clothing=[
            ItemCondition(category="upper_body", colors=["blue"], item_type="t_shirt")
        ]
    )
    assert build_mongo_query(condition) == {
        "$and": [
            {
                "clothing": {
                    "$elemMatch": {
                        "category": "upper_body",
                        "color": {"$in": ["blue"]},
                        "type": "t_shirt",
                    }
                }
            }
        ]
    }


def test_taxonomy_normalizes_existing_korean_parser_output():
    condition = PersonSearchCondition(
        clothing=[ItemCondition(category="상의", colors=["파란색"], item_type="반팔티")]
    )
    normalized = normalize_condition(condition)
    assert normalized.clothing[0].model_dump() == {
        "category": "upper_body",
        "colors": ["blue"],
        "item_type": "t_shirt",
    }
