from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel, field_validator

from ..models.enums import AccountType


class AccountCreate(BaseModel):
    name: str
    type: AccountType

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="name must not be empty"
            )
        return v


class AccountResponse(BaseModel):
    id: UUID
    name: str
    type: AccountType
    balance: Decimal

    model_config = {"from_attributes": True}
