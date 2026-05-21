from __future__ import annotations


class ZentaoCliError(Exception):
    """Base class for user-facing CLI errors."""


class AuthError(ZentaoCliError):
    """Raised when login state is missing, expired, or invalid."""


class ApiError(ZentaoCliError):
    """Raised when Zentao returns an API-level error."""


class NetworkError(ZentaoCliError):
    """Raised when the CLI cannot reach Zentao."""


class ConfigError(ZentaoCliError):
    """Raised when local configuration is missing or invalid."""


class NotFoundError(ZentaoCliError):
    """Raised when a requested Zentao resource does not exist."""
