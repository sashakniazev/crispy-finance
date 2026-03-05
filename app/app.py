import logging

from fastapi import FastAPI
from . import api

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="Financial Book",
    version="1.0.0",
)


app.include_router(api.router)