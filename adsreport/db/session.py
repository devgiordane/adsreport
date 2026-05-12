"""SQLAlchemy engine and session factory."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import create_engine, event, text
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

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _ensure_ad_account_sync_enabled(engine)
    _ensure_insight_unique_index(engine)


def _ensure_ad_account_sync_enabled(engine: Engine) -> None:
    """Keep existing databases compatible with per-account sync selection."""
    with engine.begin() as conn:
        columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(ad_accounts)"))
        }
        if "sync_enabled" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE ad_accounts "
                    "ADD COLUMN sync_enabled BOOLEAN NOT NULL DEFAULT 0"
                )
            )
            conn.execute(
                text(
                    "UPDATE ad_accounts "
                    "SET sync_enabled = CASE WHEN is_default = 1 THEN 1 ELSE 0 END"
                )
            )


def _ensure_insight_unique_index(engine: Engine) -> None:
    """Keep existing databases from using the old single-account insight index."""
    with engine.begin() as conn:
        conn.execute(text("DROP INDEX IF EXISTS ix_insights_level_entity_date"))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_insights_account_level_entity_date "
                "ON insights (ad_account_id, level, entity_id, date)"
            )
        )
