from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExpenseShareInput(BaseModel):
    participant_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class ExpenseShareResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    expense_id: UUID
    participant_id: UUID
    amount: Decimal
