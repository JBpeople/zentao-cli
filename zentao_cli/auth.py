from __future__ import annotations

from getpass import getpass
import os

import typer

from zentao_cli.client import ZentaoClient
from zentao_cli.config import Profile, load_profile, load_project_env, save_profile
from zentao_cli.errors import AuthError

ZENTAO_URL = "ZENTAO_URL"
ZENTAO_USERNAME = "ZENTAO_USERNAME"
ZENTAO_PASSWORD = "ZENTAO_PASSWORD"


def env_credentials() -> tuple[str, str, str] | None:
    file_values = load_project_env()
    values = {
        ZENTAO_URL: os.environ.get(ZENTAO_URL) or file_values.get(ZENTAO_URL),
        ZENTAO_USERNAME: os.environ.get(ZENTAO_USERNAME) or file_values.get(ZENTAO_USERNAME),
        ZENTAO_PASSWORD: os.environ.get(ZENTAO_PASSWORD) or file_values.get(ZENTAO_PASSWORD),
    }
    if all(values.values()):
        return values[ZENTAO_URL], values[ZENTAO_USERNAME], values[ZENTAO_PASSWORD]  # type: ignore[return-value]
    return None


def require_profile() -> Profile:
    profile = load_profile()
    if profile is None:
        raise AuthError("Not logged in. Run: zentao login")
    return profile


def current_username() -> str:
    credentials = env_credentials()
    if credentials is not None:
        return credentials[1]
    return require_profile().username


def client_from_profile() -> ZentaoClient:
    credentials = env_credentials()
    if credentials is not None:
        base_url, username, password = credentials
        login_client = ZentaoClient(base_url)
        session = login_client.login(username, password)
        save_profile(
            Profile(
                base_url=base_url,
                username=username,
                session_name=session.session_name,
                session_id=session.session_id,
            )
        )
        return ZentaoClient(
            base_url,
            session_name=session.session_name,
            session_id=session.session_id,
        )

    profile = require_profile()
    return ZentaoClient(
        profile.base_url,
        session_name=profile.session_name,
        session_id=profile.session_id,
    )


def login_interactive() -> None:
    credentials = env_credentials()
    if credentials is None:
        base_url = typer.prompt("Zentao URL")
        username = typer.prompt("Username")
        password = getpass("Password: ")
    else:
        base_url, username, password = credentials
    client = ZentaoClient(base_url)
    session = client.login(username, password)
    save_profile(
        Profile(
            base_url=base_url,
            username=username,
            session_name=session.session_name,
            session_id=session.session_id,
        )
    )
    typer.echo(f"Logged in as {username}")
