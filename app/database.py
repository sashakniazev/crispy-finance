from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .settings import settings

db_url = f"postgresql+asyncpg://{settings.db_username}:{settings.db_password}@{settings.db_host}/{settings.db_database}"

engine = create_async_engine(
    db_url,
    echo=False,
    pool_pre_ping=True,
)

Session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session():
    session = Session()
    try:
        yield session
    finally:
        await session.close()