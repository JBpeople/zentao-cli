from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _user_name(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("account") or value.get("realname") or "")
    return str(value or "")


@dataclass(frozen=True)
class Session:
    session_name: str
    session_id: str


@dataclass(frozen=True)
class User:
    account: str
    realname: str = ""


@dataclass(frozen=True)
class Product:
    id: int
    name: str
    code: str = ""
    status: str = ""
    type: str = ""
    owner: str = ""

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> Product:
        return cls(
            id=int(payload.get("id", 0)),
            name=str(payload.get("name", "")),
            code=str(payload.get("code", "")),
            status=str(payload.get("status", "")),
            type=str(payload.get("type", "")),
            owner=_user_name(payload.get("PO") or payload.get("owner")),
        )


@dataclass(frozen=True)
class Project:
    id: int
    name: str
    code: str = ""
    status: str = ""
    model: str = ""
    owner: str = ""

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> Project:
        return cls(
            id=int(payload.get("id", 0)),
            name=str(payload.get("name", "")),
            code=str(payload.get("code", "")),
            status=str(payload.get("status", "")),
            model=str(payload.get("model", "")),
            owner=_user_name(payload.get("PM") or payload.get("owner")),
        )


@dataclass(frozen=True)
class Execution:
    id: int
    name: str
    project: str = ""
    status: str = ""
    type: str = ""
    begin: str = ""
    end: str = ""

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> Execution:
        return cls(
            id=int(payload.get("id", 0)),
            name=str(payload.get("name", "")),
            project=str(payload.get("projectName") or payload.get("project") or ""),
            status=str(payload.get("status", "")),
            type=str(payload.get("type", "")),
            begin=str(payload.get("begin", "")),
            end=str(payload.get("end", "")),
        )


@dataclass(frozen=True)
class Task:
    id: int
    name: str
    project: str = ""
    status: str = ""
    priority: str = ""
    deadline: str = ""
    assigned_to: str = ""

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> Task:
        return cls(
            id=int(payload.get("id", 0)),
            name=str(payload.get("name", "")),
            project=str(payload.get("projectName") or payload.get("project") or ""),
            status=str(payload.get("status", "")),
            priority=str(payload.get("pri") or payload.get("priority") or ""),
            deadline=str(payload.get("deadline", "")),
            assigned_to=_user_name(payload.get("assignedTo") or payload.get("assigned_to")),
        )


@dataclass(frozen=True)
class Bug:
    id: int
    title: str
    status: str = ""
    severity: str = ""
    assigned_to: str = ""

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> Bug:
        return cls(
            id=int(payload.get("id", 0)),
            title=str(payload.get("title", "")),
            status=str(payload.get("status", "")),
            severity=str(payload.get("severity", "")),
            assigned_to=_user_name(payload.get("assignedTo") or payload.get("assigned_to")),
        )


@dataclass(frozen=True)
class Story:
    id: int
    title: str
    status: str = ""
    stage: str = ""
    product: str = ""
    priority: str = ""
    category: str = ""
    type: str = ""

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> Story:
        return cls(
            id=int(payload.get("id", 0)),
            title=str(payload.get("title", "")),
            status=str(payload.get("status", "")),
            stage=str(payload.get("stage", "")),
            product=str(payload.get("productName") or payload.get("product") or ""),
            priority=str(payload.get("pri") or payload.get("priority") or ""),
            category=str(payload.get("category", "")),
            type=str(payload.get("type", "")),
        )
