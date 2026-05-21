from pathlib import Path

from zentao_cli.config import Profile, load_profile, save_profile


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
