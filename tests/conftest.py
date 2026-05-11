"""pytest configuration and shared fixtures."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from adsreport.db.base import Base
from adsreport.db.session import get_engine, get_session


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path) -> Generator[None, None, None]:
    """Each test gets a fresh in-memory SQLite database."""
    import adsreport.db.session as db_module
    import adsreport.db.models  # noqa: F401 — ensure models are registered

    os.environ["ADSREPORT_DATA_DIR"] = str(tmp_path)
    db_module._engine = None
    db_module._SessionLocal = None

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    db_module._engine = None
    db_module._SessionLocal = None


@pytest.fixture
def session() -> Generator[Session, None, None]:
    s = get_session()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def admin_user(session: Session) -> object:
    from tests.factories import UserFactory

    user = UserFactory.create()
    session.add(user)
    session.commit()
    return user
