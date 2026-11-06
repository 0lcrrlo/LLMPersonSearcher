from typing import List, Literal, Optional

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


class PersonAttribute(BaseModel):
    """One normalized visual attribute belonging to one detection."""

    detection_id: int
    attribute_group: Literal["clothing", "accessories"]
    category: str
    color: Optional[str] = None
    item_type: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source: str = "vision"
