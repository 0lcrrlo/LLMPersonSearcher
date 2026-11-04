from typing import List

from pydantic import BaseModel, Field


class ItemCondition(BaseModel):
    category: str = Field(description="Item category, such as upper_body or bag")
    colors: List[str] = Field(default_factory=list)
    item_type: str = Field(default="")


class PersonSearchCondition(BaseModel):
    clothing: List[ItemCondition] = Field(default_factory=list)
    accessories: List[ItemCondition] = Field(default_factory=list)
    gender: str = Field(default="")
