from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.models.enums import EntryType


class TransactionEntryCreate(BaseModel):
    account_id: UUID
    type: EntryType
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("amount must be positive")
        return v


class TransactionCreate(BaseModel):
    description: str
    entries: list[TransactionEntryCreate]

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("description must not be empty")
        return v


class TransactionEntryResponse(BaseModel):
    id: UUID
    account_id: UUID
    type: EntryType
    amount: Decimal

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    id: UUID
    created_at: datetime
    description: str
    entries: list[TransactionEntryResponse]

    model_config = {"from_attributes": True}
    