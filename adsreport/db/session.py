"""SQLAlchemy engine and session factory."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from adsreport.constants import DB_FILENAME

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def _db_path() -> Path:
    data_dir = Path(os.environ.get("ADSREPORT_DATA_DIR", Path.home() / ".adsreport"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / DB_FILENAME


def get_engine() -> object:
    global _engine
    if _engine is None:
        url = f"sqlite:///{_db_path()}"
        _engine = create_engine(url, connect_args={"check_same_thread": False})

        # Enable WAL mode for better concurrent read performance
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_conn: object, _: object) -> None:
            cursor = dbapi_conn.cursor()  # type: ignore[union-attr]
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


def get_session() -> Session:
    return get_session_factory()()


def init_db() -> None:
    """Create all tables if they don't exist and run pending migrations."""
    from adsreport.db.base import Base
    import adsreport.db.models  # noqa: F401 — ensure all models are imported

    Base.metadata.create_all(bind=get_engine())
