"""Exception hierarchy for AdsReport."""

from __future__ import annotations


class AdsReportError(Exception):
    """Base exception for all application errors."""


class ConfigError(AdsReportError):
    """Settings are missing, invalid, or corrupt."""


class CryptoError(AdsReportError):
    """Encryption/decryption failure — usually a wrong password."""


class AuthError(AdsReportError):
    """Authentication or authorization failure."""


class OnboardingError(AdsReportError):
    """Onboarding wizard step validation failure."""


class FacebookError(AdsReportError):
    """Error communicating with the Facebook Marketing API."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class FacebookRateLimitError(FacebookError):
    """Hit the Facebook API rate limit; caller should back off."""


class SyncError(AdsReportError):
    """Sync job encountered a non-recoverable error."""


class RepositoryError(AdsReportError):
    """Database operation failed."""


class ValidationError(AdsReportError):
    """User-supplied input failed validation."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message
