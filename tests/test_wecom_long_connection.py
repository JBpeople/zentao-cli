from __future__ import annotations

import asyncio

from zentao_agent.wecom_long_connection import (
    WeComBotConfig,
    WeComIncomingMessage,
    build_response_frame,
    build_subscribe_frame,
    handle_frame,
    parse_text_message,
)


def test_config_reads_required_env(monkeypatch):
    monkeypatch.setenv("WECOM_BOT_ID", "bot-1")
    monkeypatch.setenv("WECOM_BOT_SECRET", "secret-1")

    config = WeComBotConfig.from_env()

    assert config.bot_id == "bot-1"
    assert config.secret == "secret-1"
    assert config.websocket_url == "wss://openws.work.weixin.qq.com"


def test_build_subscribe_frame():
    config = WeComBotConfig(bot_id="bot-1", secret="secret-1")

    assert build_subscribe_frame(config) == {
        "cmd": "aibot_subscribe",
        "body": {
            "bot_id": "bot-1",
            "secret": "secret-1",
        },
    }


def test_parse_text_message_from_callback_frame():
    frame = {
        "cmd": "aibot_msg_callback",
        "body": {
            "msgid": "msg-1",
            "chatid": "chat-1",
            "from": {"userid": "user-1"},
            "text": {"content": "show my tasks"},
        },
    }

    message = parse_text_message(frame)

    assert message == WeComIncomingMessage(
        user_id="user-1",
        chat_id="chat-1",
        message_id="msg-1",
        text="show my tasks",
        raw=frame,
    )


def test_parse_text_message_ignores_non_message_frames():
    assert parse_text_message({"cmd": "aibot_subscribe"}) is None


def test_build_response_frame():
    message = WeComIncomingMessage(
        user_id="user-1",
        chat_id="chat-1",
        message_id="msg-1",
        text="show my tasks",
        raw={},
    )

    assert build_response_frame(message, "result") == {
        "cmd": "aibot_respond_msg",
        "body": {
            "msgid": "msg-1",
            "chatid": "chat-1",
            "msgtype": "text",
            "text": {"content": "result"},
        },
    }


def test_handle_frame_calls_responder_and_sends_response():
    class FakeResponder:
        def __init__(self) -> None:
            self.messages: list[WeComIncomingMessage] = []

        async def respond(self, message: WeComIncomingMessage) -> str:
            self.messages.append(message)
            return "agent result"

    sent_frames = []
    responder = FakeResponder()
    frame = {
        "cmd": "aibot_msg_callback",
        "body": {
            "msgid": "msg-1",
            "chatid": "chat-1",
            "from": {"userid": "user-1"},
            "text": {"content": "list bugs"},
        },
    }

    handled = asyncio.run(handle_frame(frame, responder, sent_frames.append))

    assert handled is True
    assert responder.messages[0].text == "list bugs"
    assert sent_frames == [
        {
            "cmd": "aibot_respond_msg",
            "body": {
                "msgid": "msg-1",
                "chatid": "chat-1",
                "msgtype": "text",
                "text": {"content": "agent result"},
            },
        }
    ]
