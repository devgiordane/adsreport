"""Generic base repository with common CRUD operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from adsreport.db.session import get_session

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    model_class: type[T]

    def __init__(self, session: Session | None = None) -> None:
        self._owns_session = session is None
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

    def close(self) -> None:
        if self._owns_session:
            self._session.close()

    def __enter__(self) -> BaseRepository[T]:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if exc_type is not None:
            self._session.rollback()
        self.close()
