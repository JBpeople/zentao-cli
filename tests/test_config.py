from pathlib import Path

from zentao_cli.config import Profile, find_project_env_path, load_profile, load_project_env, save_profile


def test_save_and_load_default_profile(tmp_path: Path):
    path = tmp_path / "config.toml"
    profile = Profile(
        base_url="https://zentao.example.com",
        username="alice",
        session_name="zentaosid",
        session_id="abc123",
    )

    save_profile(profile, path=path)
    loaded = load_profile(path=path)

    assert loaded == profile


def test_load_missing_profile_returns_none(tmp_path: Path):
    assert load_profile(path=tmp_path / "missing.toml") is None


def test_load_project_env_reads_simple_key_values(tmp_path: Path):
    path = tmp_path / ".env"
    path.write_text(
        "\n".join(
            [
                "ZENTAO_URL=https://zentao.example.com",
                "ZENTAO_USERNAME=alice",
                'ZENTAO_PASSWORD="secret"',
                "# ignored comment",
            ]
        ),
        encoding="utf-8",
    )

    values = load_project_env(path=path)

    assert values == {
        "ZENTAO_URL": "https://zentao.example.com",
        "ZENTAO_USERNAME": "alice",
        "ZENTAO_PASSWORD": "secret",
    }


def test_find_project_env_path_searches_parent_directories(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("WECOM_BOT_ID=bot-1\n", encoding="utf-8")
    nested = tmp_path / ".worktrees" / "feature"
    nested.mkdir(parents=True)

    assert find_project_env_path(start=nested) == env_path
