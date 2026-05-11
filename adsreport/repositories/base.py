"""Generic base repository with common CRUD operations."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from adsreport.db.session import get_session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    model_class: type[T]

    def __init__(self, session: Session | None = None) -> None:
        self._session = session or get_session()

    @property
    def session(self) -> Session:
        return self._session

    def get_by_id(self, id: str) -> T | None:
        return self.session.get(self.model_class, id)

    def save(self, obj: T) -> T:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def bulk_save(self, objects: list[T]) -> None:
        for obj in objects:
            self.session.add(obj)
        self.session.commit()

    def delete(self, obj: T) -> None:
        self.session.delete(obj)
        self.session.commit()

    def __del__(self) -> None:
        try:
            self._session.close()
        except Exception:
            pass
