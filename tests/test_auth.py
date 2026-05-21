from zentao_cli.auth import client_from_profile
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
