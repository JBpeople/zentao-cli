from __future__ import annotations

from getpass import getpass

import typer

from zentao_cli.client import ZentaoClient
from zentao_cli.config import Profile, load_profile, save_profile
from zentao_cli.errors import AuthError


def require_profile() -> Profile:
    profile = load_profile()
    if profile is None:
        raise AuthError("Not logged in. Run: zentao login")
    return profile


def client_from_profile() -> ZentaoClient:
    profile = require_profile()
    return ZentaoClient(
        profile.base_url,
        session_name=profile.session_name,
        session_id=profile.session_id,
    )


def login_interactive() -> None:
    base_url = typer.prompt("Zentao URL")
    username = typer.prompt("Username")
    password = getpass("Password: ")
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
