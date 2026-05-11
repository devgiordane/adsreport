"""Authentication service: login, logout, password management."""

from __future__ import annotations

from datetime import UTC, datetime

from werkzeug.security import check_password_hash, generate_password_hash

from adsreport.constants import DEFAULT_ADMIN_USERNAME
from adsreport.core.crypto import re_encrypt_all
from adsreport.core.errors import AuthError, ValidationError
from adsreport.core.result import Err, Ok, Result
from adsreport.db.models.user import User
from adsreport.repositories.user_repo import UserRepository


class AuthService:
    def __init__(self) -> None:
        self._repo = UserRepository()

    def login(self, username: str, password: str) -> Result[User, AuthError]:
        user = self._repo.get_by_username(username)
        if user is None or not user.is_active:
            return Err(AuthError("Invalid username or password."))
        if not check_password_hash(user.password_hash, password):
            return Err(AuthError("Invalid username or password."))
        user.last_login_at = datetime.now(tz=UTC)
        self._repo.save(user)
        from adsreport.services.config_loader import reload_config

        reload_config(password=password)
        return Ok(user)

    def create_admin(self, username: str, password: str) -> Result[User, ValidationError]:
        if len(password) < 8:
            return Err(ValidationError("password", "Must be at least 8 characters."))
        if self._repo.get_by_username(username) is not None:
            return Err(ValidationError("username", "Username already taken."))
        user = User(
            username=username or DEFAULT_ADMIN_USERNAME,
            password_hash=generate_password_hash(password),
            is_active=True,
        )
        self._repo.save(user)
        return Ok(user)

    def reset_admin_password(self, new_password: str, old_password: str | None = None) -> None:
        user = self._repo.get_admin()
        if user is None:
            raise AuthError("No admin user found.")
        if old_password:
            re_encrypt_all(old_password, new_password)
        user.password_hash = generate_password_hash(new_password)
        self._repo.save(user)

    def change_password(
        self, user: User, old_password: str, new_password: str
    ) -> Result[None, AuthError | ValidationError]:
        if not check_password_hash(user.password_hash, old_password):
            return Err(AuthError("Current password is incorrect."))
        if len(new_password) < 8:
            return Err(ValidationError("new_password", "Must be at least 8 characters."))
        re_encrypt_all(old_password, new_password)
        user.password_hash = generate_password_hash(new_password)
        self._repo.save(user)
        return Ok(None)
