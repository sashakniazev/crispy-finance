from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.models import (
    OrmTransaction,
)


class TransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, tx: OrmTransaction) -> OrmTransaction:
        self.session.add(tx)
        await self.session.flush()
        await self.session.refresh(tx)
        return tx

    async def get_by_id(self, transaction_id: UUID) -> OrmTransaction | None:
        stmt = (
            select(OrmTransaction)
            .options(selectinload(OrmTransaction.entries))
            .where(OrmTransaction.id == transaction_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()