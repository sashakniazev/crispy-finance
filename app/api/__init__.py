from fastapi import APIRouter

from . import transactions
from . import accounts
from . import service

router = APIRouter()

router.include_router(service.router)
router.include_router(transactions.router, prefix="/transactions")
router.include_router(accounts.router, prefix="/accounts")

