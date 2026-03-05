import os
import pathlib

from pydantic import BaseModel

class Settings(BaseModel):
    base_dir: pathlib.Path = pathlib.Path(__file__).parent.resolve()
    DEBUG: int = int(os.environ.get("DEBUG", True))
    # LOCAL: int = int(os.environ.get("LOCAL", False))
    # FILE_SIZE: int = int(os.environ.get("FILE_SIZE", 1024 * 1024 * 30))

    server_host: str = "0.0.0.0"
    server_port: int = 8005

    db_host: str = os.environ.get("DB_HOST")
    db_username: str = os.environ.get("DB_USERNAME")
    db_password: str = os.environ.get("DB_PASSWORD")
    db_database: str = os.environ.get("DB_DATABASE")


settings = Settings()
