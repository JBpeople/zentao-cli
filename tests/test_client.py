import json

import httpx
import respx

from zentao_cli.client import ZentaoClient
from zentao_cli.errors import ApiError, NotFoundError
from zentao_cli.models import Execution, Product, Project, Story, Task


@respx.mock
def test_login_parses_session():
    route = respx.post("https://zentao.example.com/api.php/v1/tokens").mock(
        return_value=httpx.Response(
            200,
            json={"token": "abc123", "sessionName": "zentaosid"},
        )
    )

    client = ZentaoClient("https://zentao.example.com")
    session = client.login("alice", "secret")

    assert route.called
    assert session.session_name == "zentaosid"
    assert session.session_id == "abc123"


@respx.mock
def test_list_tasks_returns_normalized_tasks():
    route = respx.get("https://zentao.example.com/api.php/v1/executions/303/tasks").mock(
        return_value=httpx.Response(
            200,
            json={"tasks": [{"id": 1, "name": "Fix login", "status": "doing"}]},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_name="zentaosid", session_id="abc123")
    tasks = client.list_tasks(execution=303, mine=True)

    assert route.called
    assert tasks == [Task(id=1, name="Fix login", status="doing")]


@respx.mock
def test_list_products_returns_normalized_products():
    route = respx.get("https://zentao.example.com/api.php/v1/products").mock(
        return_value=httpx.Response(
            200,
            json={
                "products": [
                    {
                        "id": 5,
                        "name": "Platform",
                        "code": "PLAT",
                        "status": "normal",
                        "type": "product",
                        "PO": {"account": "alice"},
                    }
                ]
            },
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    products = client.list_products()

    assert route.called
    assert products == [Product(id=5, name="Platform", code="PLAT", status="normal", type="product", owner="alice")]


@respx.mock
def test_list_products_sends_page_parameters():
    route = respx.get("https://zentao.example.com/api.php/v1/products").mock(
        return_value=httpx.Response(
            200,
            json={"products": [{"id": 5, "name": "Platform"}]},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    products = client.list_products(page=2, page_size=50)

    assert products[0].id == 5
    assert route.calls.last.request.url.params["page"] == "2"
    assert route.calls.last.request.url.params["limit"] == "50"


@respx.mock
def test_list_products_fetch_all_pages_until_total_is_reached():
    respx.get("https://zentao.example.com/api.php/v1/products", params={"page": "1", "limit": "2"}).mock(
        return_value=httpx.Response(
            200,
            json={"products": [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}], "recTotal": 3},
        )
    )
    respx.get("https://zentao.example.com/api.php/v1/products", params={"page": "2", "limit": "2"}).mock(
        return_value=httpx.Response(
            200,
            json={"products": [{"id": 3, "name": "C"}], "recTotal": 3},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    products = client.list_products(page_size=2, fetch_all=True)

    assert [product.id for product in products] == [1, 2, 3]


@respx.mock
def test_get_product_returns_normalized_product():
    respx.get("https://zentao.example.com/api.php/v1/products/5").mock(
        return_value=httpx.Response(
            200,
            json={"id": 5, "name": "Platform", "status": "normal", "PO": {"account": "alice"}},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    product = client.get_product(5)

    assert product.id == 5
    assert product.name == "Platform"
    assert product.owner == "alice"


@respx.mock
def test_list_projects_returns_normalized_projects():
    route = respx.get("https://zentao.example.com/api.php/v1/projects").mock(
        return_value=httpx.Response(
            200,
            json={
                "projects": [
                    {
                        "id": 12,
                        "name": "CRM Upgrade",
                        "code": "CRM",
                        "status": "doing",
                        "model": "scrum",
                        "PM": {"account": "alice"},
                    }
                ]
            },
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    projects = client.list_projects()

    assert route.called
    assert projects == [
        Project(id=12, name="CRM Upgrade", code="CRM", status="doing", model="scrum", owner="alice")
    ]


@respx.mock
def test_get_project_returns_normalized_project():
    respx.get("https://zentao.example.com/api.php/v1/projects/12").mock(
        return_value=httpx.Response(
            200,
            json={"project": {"id": 12, "name": "CRM Upgrade", "status": "doing", "PM": {"account": "alice"}}},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    project = client.get_project(12)

    assert project.id == 12
    assert project.name == "CRM Upgrade"
    assert project.owner == "alice"


@respx.mock
def test_list_executions_returns_normalized_executions():
    route = respx.get("https://zentao.example.com/api.php/v1/projects/12/executions").mock(
        return_value=httpx.Response(
            200,
            json={
                "executions": [
                    {
                        "id": 303,
                        "name": "Sprint 1",
                        "projectName": "CRM Upgrade",
                        "status": "doing",
                        "type": "sprint",
                    }
                ]
            },
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    executions = client.list_executions(project=12)

    assert route.called
    assert executions == [Execution(id=303, name="Sprint 1", project="CRM Upgrade", status="doing", type="sprint")]


@respx.mock
def test_get_execution_returns_normalized_execution():
    respx.get("https://zentao.example.com/api.php/v1/executions/303").mock(
        return_value=httpx.Response(
            200,
            json={"execution": {"id": 303, "name": "Sprint 1", "projectName": "CRM Upgrade", "status": "doing"}},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    execution = client.get_execution(303)

    assert execution.id == 303
    assert execution.name == "Sprint 1"
    assert execution.project == "CRM Upgrade"


@respx.mock
def test_create_task_posts_execution_task_payload():
    create_route = respx.post(
        "https://zentao.example.com/api.php/v1/executions/303/tasks",
    ).mock(
        return_value=httpx.Response(
            201,
            json={
                "id": 9,
                "name": "Build import",
                "status": "wait",
                "assignedTo": {"account": "alice"},
            },
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    task = client.create_task(
        execution=303,
        name="Build import",
        est_started="2026-06-01",
        deadline="2026-06-05",
        task_type="devel",
        assigned_to="alice",
        estimate=2.5,
        pri=3,
    )

    assert create_route.called
    assert create_route.calls.last.request.headers["token"] == "abc123"
    assert json.loads(create_route.calls.last.request.content) == {
        "name": "Build import",
        "type": "devel",
        "pri": 3,
        "estStarted": "2026-06-01",
        "deadline": "2026-06-05",
        "assignedTo": "alice",
        "estimate": 2.5,
    }
    assert task.id == 9
    assert task.assigned_to == "alice"


@respx.mock
def test_create_task_posts_story_when_provided():
    create_route = respx.post(
        "https://zentao.example.com/api.php/v1/executions/303/tasks",
    ).mock(
        return_value=httpx.Response(
            201,
            json={"id": 10, "name": "Build story", "status": "wait", "storyID": 789},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    task = client.create_task(
        execution=303,
        story=789,
        name="Build story",
        est_started="2026-06-01",
        deadline="2026-06-05",
    )

    assert create_route.called
    assert json.loads(create_route.calls.last.request.content) == {
        "name": "Build story",
        "type": "devel",
        "pri": 3,
        "estStarted": "2026-06-01",
        "deadline": "2026-06-05",
        "story": 789,
    }
    assert task.id == 10


@respx.mock
def test_delete_task_sends_delete_request():
    route = respx.delete("https://zentao.example.com/api.php/v1/tasks/9").mock(
        return_value=httpx.Response(200, json={"result": "success"})
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    result = client.delete_task(9)

    assert route.called
    assert route.calls.last.request.headers["token"] == "abc123"
    assert result == {"id": 9, "deleted": True, "result": "success"}


@respx.mock
def test_update_task_posts_partial_payload():
    route = respx.put("https://zentao.example.com/api.php/v1/tasks/9").mock(
        return_value=httpx.Response(
            200,
            json={"task": {"id": 9, "name": "Build import v2", "status": "doing", "assignedTo": {"account": "bob"}}},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    task = client.update_task(
        9,
        name="Build import v2",
        status="doing",
        assigned_to="bob",
        estimate=3.5,
        deadline="2026-06-10",
        est_started="2026-06-02",
        pri=2,
        desc="Updated task body",
        task_type="test",
    )

    assert route.called
    assert json.loads(route.calls.last.request.content) == {
        "name": "Build import v2",
        "status": "doing",
        "assignedTo": "bob",
        "estimate": 3.5,
        "deadline": "2026-06-10",
        "estStarted": "2026-06-02",
        "pri": 2,
        "desc": "Updated task body",
        "type": "test",
    }
    assert task.id == 9
    assert task.name == "Build import v2"


@respx.mock
def test_link_story_posts_story_to_execution():
    route = respx.post(
        "https://zentao.example.com/index.php",
        params={"m": "execution", "f": "linkStory", "t": "json", "objectID": "303"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={"result": "success", "load": True},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    result = client.link_story(execution_id=303, story_id=789)

    assert route.called
    assert route.calls.last.request.headers["content-type"] == "application/x-www-form-urlencoded"
    assert "Token" not in route.calls.last.request.headers
    assert route.calls.last.request.headers["x-requested-with"] == "XMLHttpRequest"
    assert route.calls.last.request.content == b"stories%5B%5D=789"
    assert result == {"execution": 303, "story": 789, "linked": True, "result": "success", "load": True}


@respx.mock
def test_link_story_handles_empty_success_response():
    route = respx.post(
        "https://zentao.example.com/index.php",
        params={"m": "execution", "f": "linkStory", "t": "json", "objectID": "303"},
    ).mock(
        return_value=httpx.Response(200, content=b"")
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    result = client.link_story(execution_id=303, story_id=789)

    assert route.called
    assert result == {"execution": 303, "story": 789, "linked": True}


@respx.mock
def test_successful_non_json_response_raises_api_error():
    respx.post(
        "https://zentao.example.com/index.php",
        params={"m": "execution", "f": "linkStory", "t": "json", "objectID": "303"},
    ).mock(
        return_value=httpx.Response(200, text="<html>login</html>")
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")

    try:
        client.link_story(execution_id=303, story_id=789)
    except ApiError as exc:
        assert "non-json response" in str(exc).lower()
        assert "<html>login</html>" in str(exc)
    else:
        raise AssertionError("Expected ApiError")


@respx.mock
def test_failed_json_response_raises_api_error():
    respx.post(
        "https://zentao.example.com/index.php",
        params={"m": "execution", "f": "linkStory", "t": "json", "objectID": "303"},
    ).mock(
        return_value=httpx.Response(200, json={"result": "fail", "message": "没有权限"})
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")

    try:
        client.link_story(execution_id=303, story_id=789)
    except ApiError as exc:
        assert str(exc) == "没有权限"
    else:
        raise AssertionError("Expected ApiError")


@respx.mock
def test_link_story_rejects_link_page_payload_without_save_confirmation():
    respx.post(
        "https://zentao.example.com/index.php",
        params={"m": "execution", "f": "linkStory", "t": "json", "objectID": "303"},
    ).mock(
        return_value=httpx.Response(200, json={"status": "success", "data": "{\"allStories\":[{\"id\":789}]}"})
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")

    try:
        client.link_story(execution_id=303, story_id=789)
    except ApiError as exc:
        assert "did not confirm" in str(exc)
    else:
        raise AssertionError("Expected ApiError")


@respx.mock
def test_http_error_uses_api_error_message():
    respx.get("https://zentao.example.com/api.php/v1/bugs").mock(
        return_value=httpx.Response(400, json={"error": "Need product id."})
    )

    client = ZentaoClient("https://zentao.example.com")

    try:
        client._request("GET", "bugs")
    except ApiError as exc:
        assert str(exc) == "Need product id."
    else:
        raise AssertionError("Expected ApiError")


@respx.mock
def test_list_bugs_uses_execution_scope():
    route = respx.get("https://zentao.example.com/api.php/v1/executions/303/bugs").mock(
        return_value=httpx.Response(
            200,
            json={"bugs": [{"id": 7, "title": "Crash", "status": "active"}]},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    bugs = client.list_bugs(execution=303)

    assert route.called
    assert bugs[0].id == 7
    assert bugs[0].title == "Crash"


@respx.mock
def test_list_bugs_passes_filters_to_execution_scope():
    route = respx.get("https://zentao.example.com/api.php/v1/executions/303/bugs").mock(
        return_value=httpx.Response(
            200,
            json={"bugs": [{"id": 7, "title": "Crash", "assignedTo": {"account": "alice"}}]},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    bugs = client.list_bugs(execution=303, assigned_to="alice", status="active")

    assert route.called
    assert route.calls.last.request.url.params["assignedTo"] == "alice"
    assert route.calls.last.request.url.params["status"] == "active"
    assert bugs[0].assigned_to == "alice"


@respx.mock
def test_list_bugs_fetch_all_pages_preserves_filters():
    respx.get(
        "https://zentao.example.com/api.php/v1/executions/303/bugs",
        params={"assignedTo": "alice", "status": "active", "page": "1", "limit": "1"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={"bugs": [{"id": 7, "title": "Crash"}], "recTotal": 2},
        )
    )
    respx.get(
        "https://zentao.example.com/api.php/v1/executions/303/bugs",
        params={"assignedTo": "alice", "status": "active", "page": "2", "limit": "1"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={"bugs": [{"id": 8, "title": "UI bug"}], "recTotal": 2},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    bugs = client.list_bugs(execution=303, assigned_to="alice", status="active", page_size=1, fetch_all=True)

    assert [bug.id for bug in bugs] == [7, 8]


@respx.mock
def test_create_bug_posts_product_bug_payload():
    respx.get(
        "https://zentao.example.com/index.php",
        params={"m": "execution", "f": "linkStory", "t": "json", "objectID": "303"},
    ).mock(return_value=httpx.Response(200, json={"status": "success", "data": "{\"productPairs\":{\"5\":\"Platform\"}}"}))
    create_route = respx.post(
        "https://zentao.example.com/api.php/v1/products/5/bugs",
    ).mock(
        return_value=httpx.Response(
            201,
            json={"id": 7, "title": "Crash on import", "status": "active", "severity": "3"},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    bug = client.create_bug(
        execution=303,
        title="Crash on import",
        steps="Open import and click submit.",
        severity=3,
        pri=3,
    )

    assert create_route.called
    assert create_route.calls.last.request.headers["token"] == "abc123"
    assert json.loads(create_route.calls.last.request.content) == {
        "title": "Crash on import",
        "execution": 303,
        "steps": "Open import and click submit.",
        "severity": 3,
        "pri": 3,
        "type": "codeerror",
        "openedBuild": ["trunk"],
    }
    assert bug.id == 7


@respx.mock
def test_delete_bug_sends_delete_request():
    route = respx.delete("https://zentao.example.com/api.php/v1/bugs/7").mock(
        return_value=httpx.Response(200, json={"result": "success"})
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    result = client.delete_bug(7)

    assert route.called
    assert route.calls.last.request.headers["token"] == "abc123"
    assert result == {"id": 7, "deleted": True, "result": "success"}


@respx.mock
def test_update_bug_posts_partial_payload():
    route = respx.put("https://zentao.example.com/api.php/v1/bugs/7").mock(
        return_value=httpx.Response(
            200,
            json={"bug": {"id": 7, "title": "Crash on import v2", "status": "active", "assignedTo": {"account": "bob"}}},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    bug = client.update_bug(
        7,
        title="Crash on import v2",
        steps="Updated steps",
        severity=2,
        pri=1,
        bug_type="config",
        assigned_to="bob",
        deadline="2026-06-10",
    )

    assert route.called
    assert json.loads(route.calls.last.request.content) == {
        "title": "Crash on import v2",
        "steps": "Updated steps",
        "severity": 2,
        "pri": 1,
        "type": "config",
        "assignedTo": "bob",
        "deadline": "2026-06-10",
    }
    assert bug.id == 7
    assert bug.title == "Crash on import v2"


@respx.mock
def test_list_stories_uses_product_scope_when_product_is_provided():
    respx.get("https://zentao.example.com/api.php/v1/products").mock(
        return_value=httpx.Response(200, json={"products": [{"id": 5}]})
    )
    route = respx.get("https://zentao.example.com/api.php/v1/products/5/stories").mock(
        return_value=httpx.Response(
            201,
            json={"stories": [{"id": 9, "title": "Login story", "status": "active"}]},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    stories = client.list_stories(product=5)

    assert route.called
    assert stories[0].id == 9
    assert stories[0].title == "Login story"


@respx.mock
def test_list_stories_uses_execution_scope_when_execution_is_provided():
    route = respx.get("https://zentao.example.com/api.php/v1/executions/303/stories").mock(
        return_value=httpx.Response(
            200,
            json={"stories": [{"id": 9, "title": "Login story", "status": "active"}]},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    stories = client.list_stories(execution=303)

    assert route.called
    assert stories[0].id == 9
    assert stories[0].title == "Login story"


@respx.mock
def test_list_stories_passes_status_to_execution_scope():
    route = respx.get("https://zentao.example.com/api.php/v1/executions/303/stories").mock(
        return_value=httpx.Response(
            200,
            json={"stories": [{"id": 9, "title": "Login story", "status": "active"}]},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    stories = client.list_stories(execution=303, status="active")

    assert route.called
    assert route.calls.last.request.url.params["status"] == "active"
    assert stories[0].status == "active"


@respx.mock
def test_list_stories_rejects_unknown_product_before_querying_stories():
    respx.get("https://zentao.example.com/api.php/v1/products").mock(
        return_value=httpx.Response(200, json={"products": [{"id": 5}]})
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")

    try:
        client.list_stories(product=1000)
    except NotFoundError as exc:
        assert str(exc) == "Product 1000 was not found or is not visible"
    else:
        raise AssertionError("Expected NotFoundError")


@respx.mock
def test_create_story_posts_story_payload():
    respx.get("https://zentao.example.com/api.php/v1/products").mock(
        return_value=httpx.Response(200, json={"products": [{"id": 5}]})
    )
    route = respx.post("https://zentao.example.com/api.php/v1/stories").mock(
        return_value=httpx.Response(
            201,
            json={
                "story": {
                    "id": 42,
                    "title": "Improve onboarding",
                    "status": "active",
                    "pri": "2",
                    "type": "story",
                }
            },
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    story = client.create_story(
        product=5,
        title="Improve onboarding",
        spec="As a user, I can finish onboarding.",
        verify="Given a new user, when they complete steps, then they see the dashboard.",
        pri=2,
        category="feature",
        status="draft",
    )

    assert route.called
    assert json.loads(route.calls.last.request.content) == {
        "product": 5,
        "title": "Improve onboarding",
        "spec": "As a user, I can finish onboarding.",
        "verify": "Given a new user, when they complete steps, then they see the dashboard.",
        "pri": 2,
        "category": "feature",
        "status": "draft",
    }
    assert story == Story(id=42, title="Improve onboarding", status="active", priority="2", type="story")


@respx.mock
def test_create_story_in_execution_posts_classic_story_create_payload():
    respx.get(
        "https://zentao.example.com/index.php",
        params={"m": "execution", "f": "linkStory", "t": "json", "objectID": "303"},
    ).mock(return_value=httpx.Response(200, json={"status": "success", "data": "{\"productPairs\":{\"5\":\"Platform\"}}"}))
    create_route = respx.post(
        "https://zentao.example.com/index.php",
        params={
            "m": "story",
            "f": "create",
            "t": "json",
            "productID": "5",
            "branch": "",
            "moduleID": "0",
            "storyID": "0",
            "objectID": "303",
            "bugID": "0",
            "planID": "0",
            "todoID": "0",
            "extra": "",
            "storyType": "story",
        },
    ).mock(return_value=httpx.Response(200, json={"result": "success", "id": 42}))
    respx.get("https://zentao.example.com/api.php/v1/stories/42").mock(
        return_value=httpx.Response(
            200,
            json={"story": {"id": 42, "title": "Improve onboarding", "status": "active", "product": 5}},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    story = client.create_story(
        execution=303,
        title="Improve onboarding",
        spec="As a user, I can finish onboarding.",
        pri=2,
        category="feature",
        status="draft",
    )

    assert create_route.called
    assert "Token" not in create_route.calls.last.request.headers
    assert create_route.calls.last.request.headers["x-requested-with"] == "XMLHttpRequest"
    assert dict(create_route.calls.last.request.url.params)["objectID"] == "303"
    assert create_route.calls.last.request.content == (
        b"title=Improve+onboarding&spec=As+a+user%2C+I+can+finish+onboarding."
        b"&pri=2&category=feature&type=story&execution=303&product=5&status=draft&needNotReview=1"
    )
    assert story == Story(id=42, title="Improve onboarding", status="active", product="5")


@respx.mock
def test_create_story_in_execution_requires_product_when_execution_has_multiple_products():
    respx.get(
        "https://zentao.example.com/index.php",
        params={"m": "execution", "f": "linkStory", "t": "json", "objectID": "303"},
    ).mock(
        return_value=httpx.Response(
            200,
            json={"status": "success", "data": "{\"productPairs\":{\"5\":\"Platform\",\"6\":\"Mobile\"}}"},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")

    try:
        client.create_story(execution=303, title="Missing product", spec="Need product")
    except ApiError as exc:
        assert "--product" in str(exc)
    else:
        raise AssertionError("Expected ApiError")


@respx.mock
def test_create_story_rejects_unknown_product_before_posting():
    respx.get("https://zentao.example.com/api.php/v1/products").mock(
        return_value=httpx.Response(200, json={"products": [{"id": 5}]})
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")

    try:
        client.create_story(product=1000, title="Missing", spec="No product")
    except NotFoundError as exc:
        assert str(exc) == "Product 1000 was not found or is not visible"
    else:
        raise AssertionError("Expected NotFoundError")


@respx.mock
def test_delete_story_sends_delete_request():
    route = respx.delete("https://zentao.example.com/api.php/v1/stories/42").mock(
        return_value=httpx.Response(200, json={"result": "success"})
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    result = client.delete_story(42)

    assert route.called
    assert route.calls.last.request.headers["token"] == "abc123"
    assert result == {"id": 42, "deleted": True, "result": "success"}


@respx.mock
def test_change_story_posts_change_payload():
    route = respx.post("https://zentao.example.com/api.php/v1/stories/42/change").mock(
        return_value=httpx.Response(
            200,
            json={
                "story": {
                    "id": 42,
                    "title": "Improve onboarding v2",
                    "status": "active",
                    "pri": "2",
                }
            },
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    story = client.change_story(
        story_id=42,
        title="Improve onboarding v2",
        spec="Updated story body",
        verify="Updated acceptance criteria",
    )

    assert route.called
    assert json.loads(route.calls.last.request.content) == {
        "title": "Improve onboarding v2",
        "spec": "Updated story body",
        "verify": "Updated acceptance criteria",
    }
    assert story.id == 42
    assert story.title == "Improve onboarding v2"


@respx.mock
def test_update_story_uses_change_endpoint():
    route = respx.post("https://zentao.example.com/api.php/v1/stories/42/change").mock(
        return_value=httpx.Response(
            200,
            json={"story": {"id": 42, "title": "Improve onboarding v3", "status": "active"}},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    story = client.update_story(
        story_id=42,
        title="Improve onboarding v3",
        spec="Updated body",
        verify="Updated verify",
    )

    assert route.called
    assert json.loads(route.calls.last.request.content) == {
        "title": "Improve onboarding v3",
        "spec": "Updated body",
        "verify": "Updated verify",
    }
    assert story.id == 42
    assert story.title == "Improve onboarding v3"
