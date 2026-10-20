"""Настройки из переменных окружения."""

import os
from dataclasses import dataclass
from typing import Optional

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
TRUE_VALUES = ("1", "true", "yes", "on")
FALSE_VALUES = ("0", "false", "no", "off")


class ConfigError(ValueError):
    """Некорректное значение переменной окружения."""


def _raw(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return value.strip()


def _int(name: str, default: int, minimum: int) -> int:
    raw = _raw(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from None
    if value < minimum:
        raise ConfigError(f"{name} must be >= {minimum}, got {value}")
    return value


def _optional_int(name: str) -> Optional[int]:
    raw = _raw(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from None


def _bool(name: str, default: bool) -> bool:
    raw = _raw(name)
    if raw is None:
        return default
    if raw.lower() in TRUE_VALUES:
        return True
    if raw.lower() in FALSE_VALUES:
        return False
    raise ConfigError(f"{name} must be true or false, got {raw!r}")


def _log_level(name: str, default: str) -> str:
    raw = _raw(name)
    if raw is None:
        return default
    if raw.upper() not in LOG_LEVELS:
        raise ConfigError(f"{name} must be one of {', '.join(LOG_LEVELS)}, got {raw!r}")
    return raw.upper()


@dataclass(frozen=True)
class Settings:
    log_level: str = "INFO"
    max_attempts: int = 3
    tasks_per_session: int = 10
    max_sessions: int = 1000
    accept_e_for_yo: bool = True
    random_seed: Optional[int] = None

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            log_level=_log_level("LOG_LEVEL", defaults.log_level),
            max_attempts=_int("MAX_ATTEMPTS", defaults.max_attempts, minimum=1),
            tasks_per_session=_int("TASKS_PER_SESSION", defaults.tasks_per_session, minimum=1),
            max_sessions=_int("MAX_SESSIONS", defaults.max_sessions, minimum=1),
            accept_e_for_yo=_bool("ACCEPT_E_FOR_YO", defaults.accept_e_for_yo),
            random_seed=_optional_int("RANDOM_SEED"),
        )
