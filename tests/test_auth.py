from zentao_cli.auth import client_from_profile, current_username
from zentao_cli.config import Profile
from zentao_cli.models import Session


def test_client_from_profile_uses_env_credentials_before_saved_profile(mocker):
    login_client = mocker.Mock()
    login_client.login.return_value = Session(session_name="zentaosid", session_id="fresh-token")
    client_cls = mocker.patch("zentao_cli.auth.ZentaoClient", side_effect=[login_client, mocker.DEFAULT])
    mocker.patch(
        "zentao_cli.auth.env_credentials",
        return_value=("https://zentao.example.com", "alice", "secret"),
    )
    save_profile = mocker.patch("zentao_cli.auth.save_profile")

    client = client_from_profile()

    login_client.login.assert_called_once_with("alice", "secret")
    save_profile.assert_called_once_with(
        Profile(
            base_url="https://zentao.example.com",
            username="alice",
            session_name="zentaosid",
            session_id="fresh-token",
        )
    )
    client_cls.assert_called_with(
        "https://zentao.example.com",
        session_name="zentaosid",
        session_id="fresh-token",
    )
    assert client is client_cls.return_value


def test_current_username_uses_env_credentials_first(mocker):
    mocker.patch(
        "zentao_cli.auth.env_credentials",
        return_value=("https://zentao.example.com", "alice", "secret"),
    )
    require_profile = mocker.patch("zentao_cli.auth.require_profile")

    assert current_username() == "alice"
    require_profile.assert_not_called()


def test_current_username_uses_saved_profile_without_env(mocker):
    mocker.patch("zentao_cli.auth.env_credentials", return_value=None)
    mocker.patch(
        "zentao_cli.auth.require_profile",
        return_value=Profile(
            base_url="https://zentao.example.com",
            username="bob",
            session_name="zentaosid",
            session_id="saved-token",
        ),
    )

    assert current_username() == "bob"
