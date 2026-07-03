from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol

from aibot import WSClient, WSClientOptions, generate_req_id
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from zentao_cli.config import load_project_env

DEFAULT_PROCESSING_TEXT = "正在思考中..."
DEFAULT_WELCOME_TEXT = "您好！我是禅道智能助手，有什么可以帮您？"


class MessageResponder(Protocol):
    async def respond(self, message: WeComIncomingMessage) -> str:
        """Return the text response for one incoming WeCom message."""


@dataclass(frozen=True)
class WeComBotConfig:
    bot_id: str
    secret: str
    ws_url: str = ""

    @classmethod
    def from_env(cls) -> WeComBotConfig:
        file_values = load_project_env()
        bot_id = _env_value(file_values, "WECHAT_BOT_ID", "WECOM_BOT_ID")
        secret = _env_value(file_values, "WECHAT_BOT_SECRET", "WECOM_BOT_SECRET")
        if not bot_id:
            raise RuntimeError("WECHAT_BOT_ID is required.")
        if not secret:
            raise RuntimeError("WECHAT_BOT_SECRET is required.")
        return cls(
            bot_id=bot_id,
            secret=secret,
            ws_url=_env_value(file_values, "WECHAT_BOT_WS_URL", "WECOM_WS_URL"),
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


def create_ws_client(config: WeComBotConfig) -> WSClient:
    return WSClient(
        WSClientOptions(
            bot_id=config.bot_id,
            secret=config.secret,
            ws_url=config.ws_url,
        )
    )


def extract_text_message(frame: dict[str, Any]) -> WeComIncomingMessage | None:
    body = _dict_value(frame, "body")
    text = _first_string(
        _dict_value(body, "text").get("content"),
        _dict_value(body, "message").get("text"),
        body.get("content"),
        body.get("text"),
    )
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
    message_id = _first_string(body.get("msgid"), body.get("msg_id"), _dict_value(frame, "headers").get("req_id"))
    if not user_id or not chat_id or not message_id:
        return None

    return WeComIncomingMessage(
        user_id=user_id,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        raw=frame,
    )


def register_handlers(
    ws_client: WSClient,
    responder: MessageResponder,
    *,
    processing_text: str = DEFAULT_PROCESSING_TEXT,
    welcome_text: str = DEFAULT_WELCOME_TEXT,
) -> WSClient:
    @ws_client.on("authenticated")
    def on_authenticated() -> None:
        print("WeCom bot authenticated.")

    @ws_client.on("message.text")
    async def on_text(frame: dict[str, Any]) -> None:
        message = extract_text_message(frame)
        if message is None:
            return

        stream_id = generate_req_id("stream")
        await ws_client.reply_stream(frame, stream_id, processing_text, False)
        try:
            response = await responder.respond(message)
        except Exception as exc:  # pragma: no cover - exercised by real runtime.
            response = f"处理失败：{exc}"
        await ws_client.reply_stream(frame, stream_id, response, True)

    @ws_client.on("event.enter_chat")
    async def on_enter_chat(frame: dict[str, Any]) -> None:
        await ws_client.reply_welcome(
            frame,
            {
                "msgtype": "text",
                "text": {"content": welcome_text},
            },
        )

    return ws_client


class AdkAgentResponder:
    def __init__(
        self,
        *,
        app: Any | None = None,
        runner: Runner | None = None,
    ) -> None:
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
        return final_text or "没有生成可发送的回复。"


def build_client(
    config: WeComBotConfig | None = None,
    responder: MessageResponder | None = None,
) -> WSClient:
    ws_client = create_ws_client(config or WeComBotConfig.from_env())
    register_handlers(ws_client, responder or AdkAgentResponder())
    return ws_client


def main() -> None:
    build_client().run()


def _env_value(file_values: dict[str, str], *names: str) -> str:
    for name in names:
        value = os.environ.get(name) or file_values.get(name)
        if value:
            return value
    return ""


def _dict_value(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


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


if __name__ == "__main__":
    main()
