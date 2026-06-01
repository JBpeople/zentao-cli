from __future__ import annotations

import json
from typing import Any

import httpx

from zentao_cli.errors import ApiError, NetworkError, NotFoundError
from zentao_cli.models import Bug, Execution, Product, Project, Session, Story, Task

DEFAULT_PAGE_SIZE = 100


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

    def _classic_url(self) -> str:
        return f"{self.base_url}/index.php"

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.session_id:
            headers["Token"] = self.session_id
        return headers

    def _classic_headers(self) -> dict[str, str]:
        return {
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0",
            "Referer": self._classic_url(),
        }

    def _cookies(self) -> dict[str, str]:
        if not self.session_id:
            return {}
        return {self.session_name or "zentaosid": self.session_id}

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

        if not response.content:
            return {}
        try:
            data = response.json()
        except ValueError as exc:
            body_preview = response.text.strip()[:200]
            raise ApiError(f"Zentao API returned a non-JSON response: {body_preview}") from exc
        if isinstance(data, dict) and data.get("error"):
            raise ApiError(str(data["error"]))
        if not isinstance(data, dict):
            raise ApiError("Zentao API returned a non-object response")
        return data

    def _classic_request(self, method: str, params: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        try:
            response = httpx.request(
                method,
                self._classic_url(),
                params=params,
                headers=self._classic_headers(),
                cookies=self._cookies(),
                timeout=self.timeout,
                **kwargs,
            )
        except httpx.HTTPError as exc:
            raise NetworkError(str(exc)) from exc

        if response.status_code >= 400:
            raise ApiError(self._error_message(response))

        if not response.content:
            return {}
        try:
            data = response.json()
        except ValueError as exc:
            body_preview = response.text.strip()[:200]
            raise ApiError(f"Zentao API returned a non-JSON response: {body_preview}") from exc
        if not isinstance(data, dict):
            raise ApiError("Zentao API returned a non-object response")
        if data.get("error"):
            raise ApiError(str(data["error"]))
        if str(data.get("result", "")).lower() == "fail":
            raise ApiError(_message_from_payload(data))
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

    def _paged_request(
        self,
        path: str,
        collection_key: str,
        params: dict[str, Any] | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        fetch_all: bool = False,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        current_page = page
        base_params = params or {}

        while True:
            request_params = {
                **base_params,
                "page": current_page,
                "limit": page_size,
            }
            data = self._request("GET", path, params=request_params)
            raw_items = data.get(collection_key) or data.get("data") or []
            if not isinstance(raw_items, list):
                raise ApiError("Zentao API returned a non-list collection")
            results.extend(raw_items)

            if not fetch_all:
                break
            total = _int_or_none(data.get("recTotal") or data.get("total"))
            if not raw_items:
                break
            if total is not None and len(results) >= total:
                break
            if len(raw_items) < page_size:
                break
            current_page += 1

        return results

    def login(self, username: str, password: str) -> Session:
        data = self._request("POST", "tokens", json={"account": username, "password": password})
        session_id = str(data.get("token") or data.get("sessionID") or data.get("session_id") or "")
        session_name = str(data.get("sessionName") or data.get("session_name") or "zentaosid")
        if not session_id:
            raise ApiError("Zentao login response did not include a session token")
        return Session(session_name=session_name, session_id=session_id)

    def list_products(
        self,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        fetch_all: bool = False,
    ) -> list[Product]:
        raw_products = self._paged_request("products", "products", page=page, page_size=page_size, fetch_all=fetch_all)
        return [Product.from_api(item) for item in raw_products]

    def get_product(self, product_id: int) -> Product:
        data = self._request("GET", f"products/{product_id}")
        return Product.from_api(data.get("product") or data.get("data") or data)

    def list_projects(
        self,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        fetch_all: bool = False,
    ) -> list[Project]:
        raw_projects = self._paged_request("projects", "projects", page=page, page_size=page_size, fetch_all=fetch_all)
        return [Project.from_api(item) for item in raw_projects]

    def get_project(self, project_id: int) -> Project:
        data = self._request("GET", f"projects/{project_id}")
        return Project.from_api(data.get("project") or data.get("data") or data)

    def list_executions(
        self,
        project: int,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        fetch_all: bool = False,
    ) -> list[Execution]:
        raw_executions = self._paged_request(
            f"projects/{project}/executions",
            "executions",
            page=page,
            page_size=page_size,
            fetch_all=fetch_all,
        )
        return [Execution.from_api(item) for item in raw_executions]

    def get_execution(self, execution_id: int) -> Execution:
        data = self._request("GET", f"executions/{execution_id}")
        return Execution.from_api(data.get("execution") or data.get("data") or data)

    def create_task(
        self,
        execution: int,
        name: str,
        est_started: str,
        deadline: str,
        story: int | None = None,
        task_type: str = "devel",
        assigned_to: str | None = None,
        estimate: float | None = None,
        pri: int = 3,
        desc: str | None = None,
    ) -> Task:
        payload: dict[str, Any] = {
            "name": name,
            "type": task_type,
            "pri": pri,
            "estStarted": est_started,
            "deadline": deadline,
        }
        if story is not None:
            payload["story"] = story
        if assigned_to:
            payload["assignedTo"] = assigned_to
        if estimate is not None:
            payload["estimate"] = estimate
        if desc:
            payload["desc"] = desc

        data = self._request("POST", f"executions/{execution}/tasks", json=payload)
        task_payload = data.get("task") or data.get("data") or data
        if isinstance(task_payload, dict) and task_payload.get("name"):
            return Task.from_api(task_payload)
        task_id = _id_from_payload(data, "id", "taskID")
        if task_id is None:
            raise ApiError("Zentao did not return the created task id")
        return self.get_task(task_id)

    def link_story(self, execution_id: int, story_id: int) -> dict[str, Any]:
        data = self._classic_request(
            "POST",
            params={
                "m": "execution",
                "f": "linkStory",
                "t": "json",
                "objectID": execution_id,
            },
            data={"stories[]": str(story_id)},
        )
        if not data:
            return {"execution": execution_id, "story": story_id, "linked": True}
        if not _is_link_story_success(data):
            raise ApiError("Zentao did not confirm the story link; it may have returned the link page instead.")
        return {"execution": execution_id, "story": story_id, "linked": True, **data}

    def list_tasks(
        self,
        execution: int,
        mine: bool = False,
        status: str | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        fetch_all: bool = False,
    ) -> list[Task]:
        params: dict[str, Any] = {}
        if mine:
            params["mine"] = 1
        if status:
            params["status"] = status
        raw_tasks = self._paged_request(
            f"executions/{execution}/tasks",
            "tasks",
            params=params,
            page=page,
            page_size=page_size,
            fetch_all=fetch_all,
        )
        return [Task.from_api(item) for item in raw_tasks]

    def get_task(self, task_id: int) -> Task:
        data = self._request("GET", f"tasks/{task_id}")
        return Task.from_api(data.get("task") or data.get("data") or data)

    def delete_task(self, task_id: int) -> dict[str, Any]:
        data = self._request("DELETE", f"tasks/{task_id}")
        return {"id": task_id, "deleted": True, **data}

    def update_task(
        self,
        task_id: int,
        name: str | None = None,
        status: str | None = None,
        assigned_to: str | None = None,
        estimate: float | None = None,
        deadline: str | None = None,
        est_started: str | None = None,
        pri: int | None = None,
        desc: str | None = None,
        task_type: str | None = None,
    ) -> Task:
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if status is not None:
            payload["status"] = status
        if assigned_to is not None:
            payload["assignedTo"] = assigned_to
        if estimate is not None:
            payload["estimate"] = estimate
        if deadline is not None:
            payload["deadline"] = deadline
        if est_started is not None:
            payload["estStarted"] = est_started
        if pri is not None:
            payload["pri"] = pri
        if desc is not None:
            payload["desc"] = desc
        if task_type is not None:
            payload["type"] = task_type
        if not payload:
            raise ApiError("Use at least one field to update a task")

        data = self._request("PUT", f"tasks/{task_id}", json=payload)
        return Task.from_api(data.get("task") or data.get("data") or data)

    def update_task_status(self, task_id: int, status: str) -> Task:
        return self.update_task(task_id, status=status)

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
        execution: int,
        assigned_to: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        fetch_all: bool = False,
    ) -> list[Bug]:
        params = {"assignedTo": assigned_to, "status": status}
        clean_params = {key: value for key, value in params.items() if value}
        raw_bugs = self._paged_request(
            f"executions/{execution}/bugs",
            "bugs",
            params=clean_params,
            page=page,
            page_size=page_size,
            fetch_all=fetch_all,
        )
        return [Bug.from_api(item) for item in raw_bugs]

    def get_bug(self, bug_id: int) -> Bug:
        data = self._request("GET", f"bugs/{bug_id}")
        return Bug.from_api(data.get("bug") or data.get("data") or data)

    def delete_bug(self, bug_id: int) -> dict[str, Any]:
        data = self._request("DELETE", f"bugs/{bug_id}")
        return {"id": bug_id, "deleted": True, **data}

    def update_bug(
        self,
        bug_id: int,
        title: str | None = None,
        steps: str | None = None,
        severity: int | None = None,
        pri: int | None = None,
        bug_type: str | None = None,
        assigned_to: str | None = None,
        deadline: str | None = None,
    ) -> Bug:
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if steps is not None:
            payload["steps"] = steps
        if severity is not None:
            payload["severity"] = severity
        if pri is not None:
            payload["pri"] = pri
        if bug_type is not None:
            payload["type"] = bug_type
        if assigned_to is not None:
            payload["assignedTo"] = assigned_to
        if deadline is not None:
            payload["deadline"] = deadline
        if not payload:
            raise ApiError("Use at least one field to update a bug")

        data = self._request("PUT", f"bugs/{bug_id}", json=payload)
        return Bug.from_api(data.get("bug") or data.get("data") or data)

    def create_bug(
        self,
        execution: int,
        title: str,
        steps: str,
        product: int | None = None,
        severity: int = 3,
        pri: int = 3,
        bug_type: str = "codeerror",
        assigned_to: str | None = None,
        opened_build: str = "trunk",
        deadline: str | None = None,
    ) -> Bug:
        explicit_product = product is not None
        if product is None:
            product_ids = self._execution_product_ids(execution)
            if len(product_ids) == 1:
                product = product_ids[0]
            elif len(product_ids) > 1:
                raise ApiError(f"Execution {execution} has multiple linked products; pass --product explicitly")
            else:
                raise ApiError(f"Execution {execution} has no linked products")
        if explicit_product and product is not None:
            self._product_scope(product)

        payload: dict[str, Any] = {
            "execution": execution,
            "title": title,
            "steps": steps,
            "severity": severity,
            "pri": pri,
            "type": bug_type,
            "openedBuild": [opened_build],
        }
        if assigned_to:
            payload["assignedTo"] = assigned_to
        if deadline:
            payload["deadline"] = deadline

        data = self._request("POST", f"products/{product}/bugs", json=payload)
        bug_payload = data.get("bug") or data.get("data") or data
        if isinstance(bug_payload, dict) and bug_payload.get("title"):
            return Bug.from_api(bug_payload)
        bug_id = _id_from_payload(data, "id", "bugID")
        if bug_id is None:
            raise ApiError("Zentao did not return the created bug id")
        return self.get_bug(bug_id)

    def list_stories(
        self,
        product: int | None = None,
        execution: int | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        fetch_all: bool = False,
    ) -> list[Story]:
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if execution is not None:
            raw_stories = self._paged_request(
                f"executions/{execution}/stories",
                "stories",
                params=params,
                page=page,
                page_size=page_size,
                fetch_all=fetch_all,
            )
            return [Story.from_api(item) for item in raw_stories]
        products = self._product_scope(product)
        stories: list[Story] = []
        for product_id in products:
            raw_stories = self._paged_request(
                f"products/{product_id}/stories",
                "stories",
                params=params,
                page=page,
                page_size=page_size,
                fetch_all=fetch_all,
            )
            stories.extend(Story.from_api(item) for item in raw_stories)
        return stories

    def get_story(self, story_id: int) -> Story:
        data = self._request("GET", f"stories/{story_id}")
        return Story.from_api(data.get("story") or data.get("data") or data)

    def delete_story(self, story_id: int) -> dict[str, Any]:
        data = self._request("DELETE", f"stories/{story_id}")
        return {"id": story_id, "deleted": True, **data}

    def update_story(self, story_id: int, title: str, spec: str, verify: str | None = None) -> Story:
        return self.change_story(story_id=story_id, title=title, spec=spec, verify=verify)

    def create_story(
        self,
        title: str,
        spec: str,
        product: int | None = None,
        execution: int | None = None,
        verify: str | None = None,
        pri: int = 3,
        category: str = "feature",
        status: str = "draft",
    ) -> Story:
        if execution is not None:
            return self._create_story_in_execution(
                execution=execution,
                product=product,
                title=title,
                spec=spec,
                verify=verify,
                pri=pri,
                category=category,
                status=status,
            )
        if product is None:
            raise ApiError("Use product or execution to create a story")

        self._product_scope(product)
        payload: dict[str, Any] = {
            "product": product,
            "title": title,
            "spec": spec,
            "pri": pri,
            "category": category,
            "status": status,
        }
        if verify:
            payload["verify"] = verify

        data = self._request("POST", "stories", json=payload)
        story_payload = data.get("story") or data.get("data") or data
        if "title" not in story_payload and story_payload.get("id"):
            return self.get_story(int(story_payload["id"]))
        return Story.from_api(story_payload)

    def _create_story_in_execution(
        self,
        execution: int,
        title: str,
        spec: str,
        product: int | None = None,
        verify: str | None = None,
        pri: int = 3,
        category: str = "feature",
        status: str = "draft",
    ) -> Story:
        explicit_product = product is not None
        if product is None:
            product_ids = self._execution_product_ids(execution)
            if len(product_ids) == 1:
                product = product_ids[0]
            elif len(product_ids) > 1:
                raise ApiError(f"Execution {execution} has multiple linked products; pass --product explicitly")
            else:
                raise ApiError(f"Execution {execution} has no linked products")
        if explicit_product and product is not None:
            self._product_scope(product)

        product_id = product
        payload: dict[str, Any] = {
            "title": title,
            "spec": spec,
            "pri": pri,
            "category": category,
            "type": "story",
            "execution": execution,
            "product": product,
            "status": status,
            "needNotReview": 1,
        }
        if verify:
            payload["verify"] = verify

        data = self._classic_request(
            "POST",
            params={
                "m": "story",
                "f": "create",
                "t": "json",
                "productID": product_id,
                "branch": "",
                "moduleID": 0,
                "storyID": 0,
                "objectID": execution,
                "bugID": 0,
                "planID": 0,
                "todoID": 0,
                "extra": "",
                "storyType": "story",
            },
            data=payload,
        )
        story_id = _story_id_from_payload(data)
        if story_id is None:
            raise ApiError("Zentao did not return the created story id")
        return self.get_story(story_id)

    def _execution_product_ids(self, execution: int) -> list[int]:
        data = self._classic_request(
            "GET",
            params={
                "m": "execution",
                "f": "linkStory",
                "t": "json",
                "objectID": execution,
            },
        )
        page_data = data.get("data")
        if isinstance(page_data, str):
            try:
                page_data = json.loads(page_data)
            except ValueError as exc:
                raise ApiError("Zentao did not return execution product data") from exc
        if not isinstance(page_data, dict):
            page_data = data
        product_pairs = page_data.get("productPairs") or {}
        if not isinstance(product_pairs, dict):
            return []
        return [_id for _id in (_int_or_none(product_id) for product_id in product_pairs) if _id is not None]

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


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _message_from_payload(payload: dict[str, Any]) -> str:
    message = payload.get("message") or payload.get("messages") or payload.get("error")
    if not message and isinstance(payload.get("load"), dict):
        message = payload["load"].get("alert")
    if isinstance(message, dict):
        return "; ".join(str(item) for item in message.values())
    if isinstance(message, list):
        return "; ".join(str(item) for item in message)
    if message:
        return str(message)
    return "Zentao API returned a failure response"


def _is_link_story_success(payload: dict[str, Any]) -> bool:
    if str(payload.get("result", "")).lower() == "success":
        return True
    if payload.get("load") or payload.get("closeModal"):
        return True
    return False


def _story_id_from_payload(payload: dict[str, Any]) -> int | None:
    return _id_from_payload(payload, "id", "storyID")


def _id_from_payload(payload: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            parsed = _int_or_none(value)
            if parsed is not None:
                return parsed
    for container_key in ("story", "task", "bug", "data"):
        nested = payload.get(container_key)
        if isinstance(nested, dict):
            nested_id = _id_from_payload(nested, *keys)
            if nested_id is not None:
                return nested_id
    return None
