from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agentflow.core.config import Setting

settings = Setting()

engine = create_engine(
    settings.DATABASE_URL.get_secret_value(),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)
