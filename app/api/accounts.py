from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..domain.accounts import AccountsService
from ..schemas.accounts import AccountCreate, AccountResponse
from ..schemas.transactions import TransactionResponse

router = APIRouter(tags=["Accounts"])


def _get_accounts_service(
    session: AsyncSession = Depends(get_session),
) -> AccountsService:
    return AccountsService(session)

@router.post("",response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    service: AccountsService = Depends(_get_accounts_service),
) -> AccountResponse:
    return await service.create_account(data)


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    service: AccountsService = Depends(_get_accounts_service),
) -> list[AccountResponse]:
    return await service.get_accounts()


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: UUID,
    service: AccountsService = Depends(_get_accounts_service),
) -> AccountResponse:
    return await service.get_account(account_id)


@router.get("/{account_id}/transactions", response_model=list[TransactionResponse])
async def get_account_transactions(
    account_id: UUID,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: AccountsService = Depends(_get_accounts_service),
) -> list[TransactionResponse]:
    return await service.get_account_transactions(
        account_id, limit, offset, date_from, date_to
    )
