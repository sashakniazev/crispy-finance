from fastapi import APIRouter
from fastapi import status
from fastapi.responses import Response


router = APIRouter(tags=["Service"])


@router.post("/health")
async def health() -> Response:
    return Response(status_code=status.HTTP_200_OK)
