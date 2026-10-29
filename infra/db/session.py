import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError(
        'DATABASE_URL is not set, Copy it from .env.example and add it to .env'
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)
