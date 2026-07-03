from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from zentao_cli.config import load_project_env

DEFAULT_WEBSOCKET_URL = "wss://openws.work.weixin.qq.com"
SUBSCRIBE_CMD = "aibot_subscribe"
MESSAGE_CALLBACK_CMD = "aibot_msg_callback"
RESPOND_MESSAGE_CMD = "aibot_respond_msg"
PING_CMD = "ping"
PONG_CMD = "pong"

logger = logging.getLogger(__name__)


class MessageResponder(Protocol):
    async def respond(self, message: WeComIncomingMessage) -> str:
        """Return the text response for one incoming WeCom message."""


@dataclass(frozen=True)
class WeComBotConfig:
    bot_id: str
    secret: str
    websocket_url: str = DEFAULT_WEBSOCKET_URL
    reconnect_seconds: float = 5.0

    @classmethod
    def from_env(cls) -> WeComBotConfig:
        file_values = load_project_env()
        bot_id = os.environ.get("WECOM_BOT_ID") or file_values.get("WECOM_BOT_ID")
        secret = os.environ.get("WECOM_BOT_SECRET") or file_values.get("WECOM_BOT_SECRET")
        if not bot_id:
            raise RuntimeError("WECOM_BOT_ID is required.")
        if not secret:
            raise RuntimeError("WECOM_BOT_SECRET is required.")
        return cls(
            bot_id=bot_id,
            secret=secret,
            websocket_url=os.environ.get("WECOM_WS_URL")
            or file_values.get("WECOM_WS_URL")
            or DEFAULT_WEBSOCKET_URL,
            reconnect_seconds=float(
                os.environ.get("WECOM_RECONNECT_SECONDS")
                or file_values.get("WECOM_RECONNECT_SECONDS")
                or "5"
            ),
        )


@dataclass(frozen=True)
class WeComIncomingMessage:
    user_id: str
    chat_id: str
    message_id: str
    text: str
    raw: dict[str, Any]

    @property
    def session_id(self) -> str:
        return f"wecom:{self.chat_id}:{self.user_id}"


def build_subscribe_frame(config: WeComBotConfig) -> dict[str, Any]:
    return {
        "cmd": SUBSCRIBE_CMD,
        "body": {
            "bot_id": config.bot_id,
            "secret": config.secret,
        },
    }


def build_response_frame(message: WeComIncomingMessage, content: str) -> dict[str, Any]:
    return {
        "cmd": RESPOND_MESSAGE_CMD,
        "body": {
            "msgid": message.message_id,
            "chatid": message.chat_id,
            "msgtype": "text",
            "text": {"content": content},
        },
    }


def build_pong_frame(frame: dict[str, Any]) -> dict[str, Any]:
    body = frame.get("body") if isinstance(frame.get("body"), dict) else {}
    return {"cmd": PONG_CMD, "body": body}


def parse_text_message(frame: dict[str, Any]) -> WeComIncomingMessage | None:
    if frame.get("cmd") != MESSAGE_CALLBACK_CMD:
        return None

    body = _dict_value(frame, "body")
    text = _text_content(body)
    if not text:
        return None

    user_id = _first_string(
        _dict_value(body, "from").get("userid"),
        _dict_value(body, "from").get("user_id"),
        body.get("from_userid"),
        body.get("fromUserId"),
        body.get("userid"),
        body.get("user_id"),
    )
    chat_id = _first_string(
        body.get("chatid"),
        body.get("chat_id"),
        _dict_value(body, "chat").get("id"),
        user_id,
    )
    message_id = _first_string(body.get("msgid"), body.get("msg_id"), body.get("message_id"))
    if not user_id or not chat_id or not message_id:
        return None

    return WeComIncomingMessage(
        user_id=user_id,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        raw=frame,
    )


async def handle_frame(
    frame: dict[str, Any],
    responder: MessageResponder,
    send_frame: Callable[[dict[str, Any]], Any],
) -> bool:
    if frame.get("cmd") == PING_CMD:
        await _maybe_await(send_frame(build_pong_frame(frame)))
        return True

    message = parse_text_message(frame)
    if message is None:
        return False

    response = await responder.respond(message)
    await _maybe_await(send_frame(build_response_frame(message, response)))
    return True


class AdkAgentResponder:
    def __init__(
        self,
        *,
        app: Any | None = None,
        runner: Runner | None = None,
        app_name: str = "zentao_wecom",
    ) -> None:
        self.app_name = app_name
        if runner is not None:
            self.runner = runner
            return

        if app is None:
            try:
                from zentao_agent.agent import app as zentao_app
            except ImportError:
                from zentao_agent.agent import root_agent

                self.runner = Runner(
                    agent=root_agent,
                    session_service=InMemorySessionService(),
                    auto_create_session=True,
                )
                return

            app = zentao_app

        self.runner = Runner(
            app=app,
            session_service=InMemorySessionService(),
            auto_create_session=True,
        )

    async def respond(self, message: WeComIncomingMessage) -> str:
        content = types.Content(
            role="user",
            parts=[types.Part(text=message.text)],
        )
        final_text = ""
        async for event in self.runner.run_async(
            user_id=message.user_id,
            session_id=message.session_id,
            new_message=content,
        ):
            text = _event_text(event)
            if text:
                final_text = text
        return final_text or "No response was produced."


class WeComLongConnectionClient:
    def __init__(
        self,
        config: WeComBotConfig,
        responder: MessageResponder,
    ) -> None:
        self.config = config
        self.responder = responder

    async def run_forever(self) -> None:
        while True:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("WeCom long connection failed; reconnecting.")
                await asyncio.sleep(self.config.reconnect_seconds)

    async def run_once(self) -> None:
        import websockets

        async with websockets.connect(self.config.websocket_url) as websocket:
            await websocket.send(_json_dumps(build_subscribe_frame(self.config)))

            async def send_frame(frame: dict[str, Any]) -> None:
                await websocket.send(_json_dumps(frame))

            async for raw_frame in websocket:
                frame = json.loads(raw_frame)
                if isinstance(frame, dict):
                    await handle_frame(frame, self.responder, send_frame)


async def amain() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    config = WeComBotConfig.from_env()
    client = WeComLongConnectionClient(config, AdkAgentResponder())
    await client.run_forever()


def main() -> None:
    asyncio.run(amain())


def _dict_value(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _text_content(body: dict[str, Any]) -> str:
    candidates = (
        _dict_value(body, "text").get("content"),
        _dict_value(body, "message").get("text"),
        body.get("content"),
        body.get("text"),
    )
    return _first_string(*candidates)


def _first_string(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _event_text(event: Any) -> str:
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None) or []
    texts = [getattr(part, "text", "") for part in parts]
    return "\n".join(text for text in texts if text)


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


async def _maybe_await(value: Any) -> None:
    if inspect.isawaitable(value):
        await value


if __name__ == "__main__":
    main()
