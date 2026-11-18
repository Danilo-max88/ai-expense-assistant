from datetime import date, datetime

from pydantic import BaseModel, Field

VALID_CATEGORIES = [
    "food",
    "transport",
    "housing",
    "entertainment",
    "health",
    "shopping",
    "other",
]


class ExpenseBase(BaseModel):
    amount: float = Field(gt=0)
    category: str
    description: str
    date: date


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseOut(ExpenseBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ParseTextRequest(BaseModel):
    text: str = Field(min_length=1)


class SummaryResponse(BaseModel):
    period_label: str
    total: float
    by_category: dict[str, float]
    insight: str
