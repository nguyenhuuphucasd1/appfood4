from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import DATABASE_URL, DATA_DIR


DATA_DIR.mkdir(parents=True, exist_ok=True)


def _enable_sqlite_foreign_keys(dbapi_connection, _) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def create_database_engine(database_url: str) -> Engine:
    is_sqlite = database_url.startswith("sqlite")
    kwargs: dict = {}
    if is_sqlite:
        kwargs["connect_args"] = {"check_same_thread": False}
        if database_url in {"sqlite://", "sqlite:///:memory:"}:
            # Share the same in-memory connection across FastAPI/TestClient threads.
            kwargs["poolclass"] = StaticPool
    database_engine = create_engine(database_url, **kwargs)
    if is_sqlite:
        event.listen(database_engine, "connect", _enable_sqlite_foreign_keys)
    return database_engine


engine = create_database_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
