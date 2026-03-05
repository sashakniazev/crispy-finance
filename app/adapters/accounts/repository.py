from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.models import (
    AccountType,
    EntryType,
    OrmAccount,
    OrmTransaction,
    OrmTransactionEntry,
)


class AccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    async def create(self, account: OrmAccount) -> OrmAccount:
        self.session.add(account)
        await self.session.flush()
        await self.session.refresh(account)
        return account

    async def get_by_name(self, name: str) -> OrmAccount | None:
        stmt = select(OrmAccount).where(OrmAccount.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self) -> list[OrmAccount]:
        stmt = select(OrmAccount).order_by(OrmAccount.name)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, account_id: UUID) -> OrmAccount | None:
        stmt = select(OrmAccount).where(OrmAccount.id == account_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def get_accounts_with_balances(
        self, account_id: UUID | None = None
    ) -> list[tuple[OrmAccount, Decimal]]:
        debit_sum = func.coalesce(
            func.sum(
                case(
                    (
                        OrmTransactionEntry.type == EntryType.DEBIT,
                        OrmTransactionEntry.amount,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("debit_total")

        credit_sum = func.coalesce(
            func.sum(
                case(
                    (
                        OrmTransactionEntry.type == EntryType.CREDIT,
                        OrmTransactionEntry.amount,
                    ),
                    else_=0,
                )
            ),
            0,
        ).label("credit_total")

        sums_sq = (
            select(
                OrmTransactionEntry.account_id.label("account_id"),
                debit_sum,
                credit_sum,
            )
            .group_by(OrmTransactionEntry.account_id)
            .subquery("acc_sums")
        )
        # ASSET/EXPENSE: debit - credit
        # LIABILITY/REVENUE: credit - debit
        balance_expr = case(
            (
                OrmAccount.type.in_([AccountType.ASSET, AccountType.EXPENSE]),
                func.coalesce(sums_sq.c.debit_total, 0)
                - func.coalesce(sums_sq.c.credit_total, 0),
            ),
            else_=func.coalesce(sums_sq.c.credit_total, 0)
            - func.coalesce(sums_sq.c.debit_total, 0),
        ).label("balance")

        stmt = (
            select(OrmAccount, balance_expr)
            .outerjoin(sums_sq, sums_sq.c.account_id == OrmAccount.id)
            .order_by(OrmAccount.name)
        )
        if account_id is not None:
            stmt = stmt.where(OrmAccount.id == account_id)

        result = await self.session.execute(stmt)
        return result.all()

    async def get_transactions_for_account(
        self, account_id: UUID, date_from: datetime | None = None, date_to: datetime | None = None,
    ) -> list[OrmTransaction]:

        entry_exists = (
            exists()
            .where(OrmTransactionEntry.transaction_id == OrmTransaction.id)
            .where(OrmTransactionEntry.account_id == account_id)
        )

        stmt = (
            select(OrmTransaction)
            .where(entry_exists)
            .options(selectinload(OrmTransaction.entries))
            .order_by(OrmTransaction.created_at.desc())
        )

        if date_from is not None:
            stmt = stmt.where(OrmTransaction.created_at >= date_from)

        if date_to is not None:
            stmt = stmt.where(OrmTransaction.created_at <= date_to)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_accounts_by_ids(self, account_ids: list[UUID]) -> list[OrmAccount]:
        stmt = select(OrmAccount).where(OrmAccount.id.in_(account_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())