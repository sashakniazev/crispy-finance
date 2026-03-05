from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..domain.transactions import TransactionsService
from ..schemas.transactions import TransactionCreate, TransactionResponse

router = APIRouter(tags=["Transactions"])


def _get_transactions_service(session: AsyncSession = Depends(get_session)) -> TransactionsService:
    return TransactionsService(session)


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    service: TransactionsService = Depends(_get_transactions_service),
) -> TransactionResponse:
    return await service.create_transaction(data)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    service: TransactionsService = Depends(_get_transactions_service),
) -> TransactionResponse:
    return await service.get_transaction(transaction_id)
