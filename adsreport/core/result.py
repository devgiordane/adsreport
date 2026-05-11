"""Result[T, E] type for service-layer return values.

Avoids exception-driven flow for expected failure paths (validation errors,
API errors that the UI needs to display as messages, not crash).

Usage:
    def do_thing() -> Result[str, ValidationError]:
        if bad:
            return Err(ValidationError("field", "msg"))
        return Ok("value")

    result = do_thing()
    if result.is_ok():
        use(result.unwrap())
    else:
        show_error(result.unwrap_err())
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, NoReturn, TypeVar

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_err(self) -> NoReturn:
        raise ValueError("Called unwrap_err() on Ok")

    def map(self, fn: Callable[[T], U]) -> "Ok[U]":
        return Ok(fn(self.value))

    def map_err(self, fn: Callable[[object], object]) -> "Ok[T]":
        return self


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> NoReturn:
        if isinstance(self.error, BaseException):
            raise self.error
        raise ValueError(str(self.error))

    def unwrap_err(self) -> E:
        return self.error

    def map(self, fn: Callable[[object], object]) -> "Err[E]":
        return self

    def map_err(self, fn: Callable[[E], U]) -> "Err[U]":  # type: ignore[type-var]
        return Err(fn(self.error))  # type: ignore[arg-type]


Result = Ok[T] | Err[E]
