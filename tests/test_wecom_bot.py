from __future__ import annotations

import asyncio

from zentao_agent.wecom_bot import (
    WeComBotConfig,
    WeComIncomingMessage,
    create_ws_client,
    extract_text_message,
    register_handlers,
)


def test_config_reads_wechat_env_names(monkeypatch):
    monkeypatch.setenv("WECHAT_BOT_ID", "bot-1")
    monkeypatch.setenv("WECHAT_BOT_SECRET", "secret-1")

    config = WeComBotConfig.from_env()

    assert config.bot_id == "bot-1"
    assert config.secret == "secret-1"


def test_config_reads_project_env_when_process_env_is_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("WECHAT_BOT_ID", raising=False)
    monkeypatch.delenv("WECHAT_BOT_SECRET", raising=False)
    nested = tmp_path / ".worktrees" / "feature"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "WECHAT_BOT_ID=bot-from-file",
                "WECHAT_BOT_SECRET=secret-from-file",
                "WECHAT_BOT_WS_URL=wss://example.invalid",
            ]
        ),
        encoding="utf-8",
    )

    config = WeComBotConfig.from_env()

    assert config.bot_id == "bot-from-file"
    assert config.secret == "secret-from-file"
    assert config.ws_url == "wss://example.invalid"


def test_create_ws_client_uses_sdk_options():
    config = WeComBotConfig(bot_id="bot-1", secret="secret-1", ws_url="wss://example.invalid")

    client = create_ws_client(config)

    assert client._options.bot_id == "bot-1"
    assert client._options.secret == "secret-1"
    assert client._options.ws_url == "wss://example.invalid"


def test_extract_text_message_from_sdk_frame():
    frame = {
        "headers": {"req_id": "req-1"},
        "body": {
            "msgid": "msg-1",
            "chatid": "chat-1",
            "from": {"userid": "user-1"},
            "text": {"content": "show my tasks"},
        },
    }

    assert extract_text_message(frame) == WeComIncomingMessage(
        user_id="user-1",
        chat_id="chat-1",
        message_id="msg-1",
        text="show my tasks",
        raw=frame,
    )


def test_register_handlers_replies_with_agent_result(monkeypatch):
    class FakeClient:
        def __init__(self) -> None:
            self.handlers = {}
            self.streams = []

        def on(self, event):
            def decorator(func):
                self.handlers[event] = func
                return func

            return decorator

        async def reply_stream(self, frame, stream_id, content, finish=False):
            self.streams.append((frame, stream_id, content, finish))

        async def reply_welcome(self, frame, body):
            self.welcome = (frame, body)

    class FakeResponder:
        def __init__(self) -> None:
            self.messages = []

        async def respond(self, message):
            self.messages.append(message)
            return "agent result"

    monkeypatch.setattr("zentao_agent.wecom_bot.generate_req_id", lambda prefix: f"{prefix}-1")
    client = FakeClient()
    responder = FakeResponder()
    register_handlers(client, responder)
    frame = {
        "body": {
            "msgid": "msg-1",
            "chatid": "chat-1",
            "from": {"userid": "user-1"},
            "text": {"content": "list bugs"},
        }
    }

    asyncio.run(client.handlers["message.text"](frame))

    assert responder.messages[0].session_id == "wecom:chat-1:user-1"
    assert client.streams == [
        (frame, "stream-1", "正在思考中...", False),
        (frame, "stream-1", "agent result", True),
    ]
