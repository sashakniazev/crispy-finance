import uvicorn

from .settings import settings


uvicorn.run(
    'crispy-finance.app:app',
    host=settings.server_host,
    port=settings.server_port,
    forwarded_allow_ips="*",
    workers=4,
    reload=True if settings.DEBUG else False,
)
