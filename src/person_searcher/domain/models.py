from typing import List

from pydantic import AliasChoices, BaseModel, Field


class ItemCondition(BaseModel):
    category: str = Field(description="Item category, such as upper_body or bag")
    colors: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("colors", "color"),
    )
    item_type: str = Field(
        default="",
        validation_alias=AliasChoices("item_type", "type"),
    )


class PersonSearchCondition(BaseModel):
    clothing: List[ItemCondition] = Field(default_factory=list)
    accessories: List[ItemCondition] = Field(default_factory=list)
    gender: str = Field(default="")
