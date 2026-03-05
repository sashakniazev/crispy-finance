from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..adapters.accounts.repository import AccountRepository
from ..models.models import OrmAccount
from ..schemas.accounts import AccountCreate, AccountResponse
from ..schemas.transactions import TransactionResponse


class AccountsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AccountRepository(session)

    async def create_account(self, data: AccountCreate) -> AccountResponse:
        if existing := await self.repo.get_by_name(data.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Account with name '{data.name}' already exists",
            )

        account = await self.repo.create(OrmAccount(**data.model_dump()))
        await self.session.commit()
        
        return AccountResponse(
            id=account.id,
            name=account.name,
            type=account.type,
            balance=Decimal("0"),
        )

    async def get_accounts(self) -> list[AccountResponse]:
        rows = await self.repo.get_accounts_with_balances()
        return [
            AccountResponse(
                id=acc.id,
                name=acc.name,
                type=acc.type,
                balance=balance,
            )
            for acc, balance in rows
        ]
    
    async def get_account(self, account_id: UUID) -> AccountResponse:
        rows = await self.repo.get_accounts_with_balances(account_id)
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account '{account_id}' not found",
            )
        acc, balance = rows[0]
        return AccountResponse(
            id=acc.id,
            name=acc.name,
            type=acc.type,
            balance=balance,
        )

    async def get_account_transactions(
        self, account_id: UUID, date_from: datetime | None = None, date_to: datetime | None = None,
    ) -> list[TransactionResponse]:
        account = await self.repo.get_by_id(account_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account '{account_id}' not found",
            )

        txs = await self.repo.get_transactions_for_account(account_id, date_from, date_to)
        return [TransactionResponse.model_validate(tx) for tx in txs]