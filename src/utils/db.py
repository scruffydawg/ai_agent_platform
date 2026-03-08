from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from src.config import POSTGRES_URL
from src.utils.logger import logger

Base = declarative_base()
engine = create_async_engine(POSTGRES_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"Failed to connect to Postgres: {e}")

async def get_db():
    async with async_session() as session:
        yield session
