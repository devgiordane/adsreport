"""SQLAlchemy engine and session factory."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from adsreport.constants import DB_FILENAME

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.engine import Engine

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _db_path() -> Path:
    data_dir = Path(os.environ.get("ADSREPORT_DATA_DIR", Path.home() / ".adsreport"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / DB_FILENAME


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = f"sqlite:///{_db_path()}"
        _engine = create_engine(url, connect_args={"check_same_thread": False})

        # Enable WAL mode for better concurrent read performance
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_conn: Any, _: object) -> None:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


def get_session() -> Session:
    return get_session_factory()()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a short-lived session boundary for callbacks, services, and jobs."""
    session = get_session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables if they don't exist and run pending migrations."""
    import adsreport.db.models  # noqa: F401 — ensure all models are imported
    from adsreport.db.base import Base

    Base.metadata.create_all(bind=get_engine())
