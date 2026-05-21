from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any


def _to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    return value


def json_payload(data: Any) -> str:
    return json.dumps({"ok": True, "data": _to_plain(data)}, ensure_ascii=False, indent=2)


def error_payload(error: Exception) -> str:
    return json.dumps(
        {
            "ok": False,
            "error": {"type": error.__class__.__name__, "message": str(error)},
        },
        ensure_ascii=False,
        indent=2,
    )
