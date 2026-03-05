import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..adapters.accounts.repository import AccountRepository
from ..adapters.transactions.repository import TransactionRepository
from ..models.enums import EntryType
from ..models.models import OrmTransaction, OrmTransactionEntry
from ..schemas.transactions import TransactionCreate, TransactionResponse


class TransactionsService:
    def __init__(self, session: AsyncSession) -> None:  
        self.session = session
        self.repo = TransactionRepository(session)
        self.accounts_repo = AccountRepository(session)

    async def create_transaction(self, data: TransactionCreate) -> TransactionResponse:
        self._validate_entries(data)

        account_ids = [e.account_id for e in data.entries]
        accounts = await self.accounts_repo.get_accounts_by_ids(account_ids)
        existing = {a.id for a in accounts}
        missing = [str(aid) for aid in account_ids if aid not in existing]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The following account_ids do not exist: {', '.join(missing)}",
            )

        tx = OrmTransaction(description=data.description)
        tx.entries = [
            OrmTransactionEntry(
                account_id=e.account_id,
                type=e.type,
                amount=e.amount,
            )
            for e in data.entries
        ]

        tx = await self.repo.create(tx)
        await self.session.commit()
        return TransactionResponse.model_validate(tx)
    
    async def get_transaction(self, transaction_id: uuid.UUID) -> TransactionResponse:
        transaction = await self.repo.get_by_id(transaction_id)
        if transaction is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transaction '{transaction_id}' not found")
        return TransactionResponse.model_validate(transaction)
    
    @staticmethod
    def _validate_entries(data: TransactionCreate) -> None:
        if len(data.entries) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A transaction must have at least 2 entries",
            )

        has_debit = any(e.type == EntryType.DEBIT for e in data.entries)
        has_credit = any(e.type == EntryType.CREDIT for e in data.entries)
        if not has_debit or not has_credit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A transaction must have at least one DEBIT and one CREDIT entry",
            )


        debit_total = sum(
            e.amount for e in data.entries if e.type == EntryType.DEBIT
        )
        credit_total = sum(
            e.amount for e in data.entries if e.type == EntryType.CREDIT
        )
        if debit_total != credit_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Debits ({debit_total}) must equal credits ({credit_total})",
            )
