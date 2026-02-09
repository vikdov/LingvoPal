from sqlalchemy.ext.asyncio import (
    create_async_engine,
)
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
