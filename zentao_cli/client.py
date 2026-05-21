from __future__ import annotations

from typing import Any

import httpx

from zentao_cli.errors import ApiError, NetworkError, NotFoundError
from zentao_cli.models import Bug, Product, Session, Story, Task


class ZentaoClient:
    def __init__(
        self,
        base_url: str,
        session_name: str | None = None,
        session_id: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session_name = session_name
        self.session_id = session_id
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api.php/v1/{path.lstrip('/')}"

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.session_id:
            headers["Token"] = self.session_id
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = httpx.request(
                method,
                self._url(path),
                headers=self._headers(),
                timeout=self.timeout,
                **kwargs,
            )
        except httpx.HTTPError as exc:
            raise NetworkError(str(exc)) from exc

        if response.status_code >= 400:
            raise ApiError(self._error_message(response))

        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            raise ApiError(str(data["error"]))
        if not isinstance(data, dict):
            raise ApiError("Zentao API returned a non-object response")
        return data

    def _error_message(self, response: httpx.Response) -> str:
        try:
            data = response.json()
        except ValueError:
            return f"Zentao API returned HTTP {response.status_code}"

        if isinstance(data, dict):
            message = data.get("error") or data.get("message")
            if message:
                return str(message)
        return f"Zentao API returned HTTP {response.status_code}"

    def _product_ids(self) -> list[int]:
        return [product.id for product in self.list_products()]

    def _product_scope(self, product: int | None) -> list[int]:
        product_ids = self._product_ids()
        if product is None:
            return product_ids
        if product not in product_ids:
            raise NotFoundError(f"Product {product} was not found or is not visible")
        return [product]

    def login(self, username: str, password: str) -> Session:
        data = self._request("POST", "tokens", json={"account": username, "password": password})
        session_id = str(data.get("token") or data.get("sessionID") or data.get("session_id") or "")
        session_name = str(data.get("sessionName") or data.get("session_name") or "zentaosid")
        if not session_id:
            raise ApiError("Zentao login response did not include a session token")
        return Session(session_name=session_name, session_id=session_id)

    def list_products(self) -> list[Product]:
        data = self._request("GET", "products")
        raw_products = data.get("products") or data.get("data") or []
        return [Product.from_api(item) for item in raw_products]

    def get_product(self, product_id: int) -> Product:
        data = self._request("GET", f"products/{product_id}")
        return Product.from_api(data.get("product") or data.get("data") or data)

    def list_tasks(self, execution: int, mine: bool = False, status: str | None = None) -> list[Task]:
        params: dict[str, Any] = {}
        if mine:
            params["mine"] = 1
        if status:
            params["status"] = status
        data = self._request("GET", f"executions/{execution}/tasks", params=params)
        raw_tasks = data.get("tasks") or data.get("data") or []
        return [Task.from_api(item) for item in raw_tasks]

    def get_task(self, task_id: int) -> Task:
        data = self._request("GET", f"tasks/{task_id}")
        return Task.from_api(data.get("task") or data.get("data") or data)

    def update_task_status(self, task_id: int, status: str) -> Task:
        data = self._request("PUT", f"tasks/{task_id}", json={"status": status})
        return Task.from_api(data.get("task") or data.get("data") or data)

    def comment_task(self, task_id: int, content: str) -> None:
        self._request("POST", f"tasks/{task_id}/comments", json={"content": content})

    def finish_task(self, task_id: int, comment: str | None = None) -> Task:
        payload: dict[str, Any] = {}
        if comment:
            payload["comment"] = comment
        data = self._request("POST", f"tasks/{task_id}/finish", json=payload)
        return Task.from_api(data.get("task") or data.get("data") or data)

    def list_bugs(
        self,
        product: int | None = None,
        assigned_to: str | None = None,
        status: str | None = None,
    ) -> list[Bug]:
        params = {"assignedTo": assigned_to, "status": status}
        clean_params = {key: value for key, value in params.items() if value}
        products = self._product_scope(product)
        bugs: list[Bug] = []
        for product_id in products:
            data = self._request("GET", f"products/{product_id}/bugs", params=clean_params)
            raw_bugs = data.get("bugs") or data.get("data") or []
            bugs.extend(Bug.from_api(item) for item in raw_bugs)
        return bugs

    def get_bug(self, bug_id: int) -> Bug:
        data = self._request("GET", f"bugs/{bug_id}")
        return Bug.from_api(data.get("bug") or data.get("data") or data)

    def list_stories(self, product: int | None = None, status: str | None = None) -> list[Story]:
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        products = self._product_scope(product)
        stories: list[Story] = []
        for product_id in products:
            data = self._request("GET", f"products/{product_id}/stories", params=params)
            raw_stories = data.get("stories") or data.get("data") or []
            stories.extend(Story.from_api(item) for item in raw_stories)
        return stories

    def get_story(self, story_id: int) -> Story:
        data = self._request("GET", f"stories/{story_id}")
        return Story.from_api(data.get("story") or data.get("data") or data)

    def create_story(
        self,
        product: int,
        title: str,
        spec: str,
        verify: str | None = None,
        pri: int = 3,
        category: str = "feature",
    ) -> Story:
        self._product_scope(product)
        payload: dict[str, Any] = {
            "product": product,
            "title": title,
            "spec": spec,
            "pri": pri,
            "category": category,
        }
        if verify:
            payload["verify"] = verify

        data = self._request("POST", "stories", json=payload)
        story_payload = data.get("story") or data.get("data") or data
        if "title" not in story_payload and story_payload.get("id"):
            return self.get_story(int(story_payload["id"]))
        return Story.from_api(story_payload)

    def change_story(
        self,
        story_id: int,
        title: str,
        spec: str,
        verify: str | None = None,
    ) -> Story:
        payload: dict[str, Any] = {"title": title, "spec": spec}
        if verify:
            payload["verify"] = verify

        data = self._request("POST", f"stories/{story_id}/change", json=payload)
        story_payload = data.get("story") or data.get("data") or data
        if "title" not in story_payload and story_payload.get("id"):
            return self.get_story(int(story_payload["id"]))
        return Story.from_api(story_payload)
