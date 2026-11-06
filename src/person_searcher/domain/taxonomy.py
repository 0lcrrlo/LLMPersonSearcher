from typing import Dict

from .models import ItemCondition, PersonSearchCondition


CATEGORY_ALIASES: Dict[str, str] = {
    "상의": "upper_body",
    "upper": "upper_body",
    "upper_body": "upper_body",
    "하의": "lower_body",
    "lower": "lower_body",
    "lower_body": "lower_body",
    "아우터": "outerwear",
    "outerwear": "outerwear",
    "가방": "bag",
    "bag": "bag",
    "신발": "shoes",
    "shoes": "shoes",
    "모자": "hat",
    "hat": "hat",
}

COLOR_ALIASES: Dict[str, str] = {
    "파란": "blue",
    "파란색": "blue",
    "blue": "blue",
    "검은": "black",
    "검은색": "black",
    "black": "black",
    "빨간": "red",
    "빨간색": "red",
    "red": "red",
    "흰": "white",
    "흰색": "white",
    "white": "white",
    "회색": "gray",
    "grey": "gray",
    "gray": "gray",
    "남색": "navy",
    "navy": "navy",
}

TYPE_ALIASES: Dict[str, str] = {
    "반팔티": "t_shirt",
    "티셔츠": "t_shirt",
    "shirt": "t_shirt",
    "t_shirt": "t_shirt",
    "청바지": "jeans",
    "pants": "jeans",
    "jeans": "jeans",
    "백팩": "backpack",
    "backpack": "backpack",
    "크로스백": "cross_body_bag",
    "cross_body_bag": "cross_body_bag",
}


def normalize_condition(condition: PersonSearchCondition) -> PersonSearchCondition:
    """Convert parser output into the canonical English taxonomy."""

    def normalize_item(item: ItemCondition) -> ItemCondition:
        return ItemCondition(
            category=CATEGORY_ALIASES.get(item.category, item.category),
            colors=[COLOR_ALIASES.get(color, color) for color in item.colors],
            item_type=TYPE_ALIASES.get(item.item_type, item.item_type),
        )

    return PersonSearchCondition(
        clothing=[normalize_item(item) for item in condition.clothing],
        accessories=[normalize_item(item) for item in condition.accessories],
        gender=condition.gender,
    )
