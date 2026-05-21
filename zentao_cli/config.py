from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "zentao-cli"
DEFAULT_PROFILE = "default"
PROJECT_ENV_PATH = Path(".env")


@dataclass(frozen=True)
class Profile:
    base_url: str
    username: str
    session_name: str
    session_id: str


def default_config_path() -> Path:
    return Path(user_config_dir(APP_NAME)) / "config.toml"


def load_project_env(path: Path = PROJECT_ENV_PATH) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def load_profile(profile_name: str = DEFAULT_PROFILE, path: Path | None = None) -> Profile | None:
    config_path = path or default_config_path()
    if not config_path.exists():
        return None

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    raw_profile = data.get(profile_name)
    if not raw_profile:
        return None

    return Profile(
        base_url=raw_profile["base_url"],
        username=raw_profile["username"],
        session_name=raw_profile["session_name"],
        session_id=raw_profile["session_id"],
    )


def save_profile(profile: Profile, profile_name: str = DEFAULT_PROFILE, path: Path | None = None) -> None:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        f"[{profile_name}]\n"
        f'base_url = "{profile.base_url}"\n'
        f'username = "{profile.username}"\n'
        f'session_name = "{profile.session_name}"\n'
        f'session_id = "{profile.session_id}"\n'
    )
    config_path.write_text(content, encoding="utf-8")
