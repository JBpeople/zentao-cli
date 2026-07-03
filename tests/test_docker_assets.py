from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_asset(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_dockerfile_installs_package_and_runs_wecom_bot():
    dockerfile = read_asset("Dockerfile")

    assert "FROM python:3.12-slim" in dockerfile
    assert "WORKDIR /app" in dockerfile
    assert "COPY pyproject.toml README.md LICENSE ./" in dockerfile
    assert "COPY zentao_cli ./zentao_cli" in dockerfile
    assert "COPY zentao_agent ./zentao_agent" in dockerfile
    assert "python -m pip install --no-cache-dir -e ." in dockerfile
    assert 'CMD ["zentao-wecom-bot"]' in dockerfile


def test_docker_compose_runs_bot_with_runtime_env_file():
    compose = read_asset("docker-compose.yml")

    assert "zentao-wecom-bot:" in compose
    assert "build:" in compose
    assert "context: ." in compose
    assert "env_file:" in compose
    assert "- .env" in compose
    assert "restart: unless-stopped" in compose
    assert 'command: ["zentao-wecom-bot"]' in compose


def test_dockerignore_excludes_local_state_and_secrets():
    dockerignore = read_asset(".dockerignore")

    for pattern in [
        ".env",
        ".env.*",
        ".git",
        ".worktrees/",
        ".venv/",
        "__pycache__/",
        ".pytest_cache/",
        ".tmp-pytest/",
    ]:
        assert pattern in dockerignore
