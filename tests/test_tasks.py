import pytest


@pytest.mark.asyncio
async def test_create_task(client, auth_headers):
    res = await client.post(
        "/tasks",
        json={"title": "Estudar FastAPI", "description": "Aprender async"},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Estudar FastAPI"
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_tasks(client, auth_headers):
    await client.post("/tasks", json={"title": "Task A"}, headers=auth_headers)
    await client.post("/tasks", json={"title": "Task B"}, headers=auth_headers)
    res = await client.get("/tasks", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total"] == 2


@pytest.mark.asyncio
async def test_get_task_by_id(client, auth_headers):
    create_res = await client.post(
        "/tasks", json={"title": "Fetch me"}, headers=auth_headers
    )
    task_id = create_res.json()["id"]
    res = await client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == task_id


@pytest.mark.asyncio
async def test_update_task_status(client, auth_headers):
    create_res = await client.post(
        "/tasks", json={"title": "Update me"}, headers=auth_headers
    )
    task_id = create_res.json()["id"]
    res = await client.patch(
        f"/tasks/{task_id}/status",
        json={"status": "done"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "done"


@pytest.mark.asyncio
async def test_delete_task(client, auth_headers):
    create_res = await client.post(
        "/tasks", json={"title": "Delete me"}, headers=auth_headers
    )
    task_id = create_res.json()["id"]
    res = await client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert res.status_code == 204
    res = await client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_task_requires_auth(client):
    res = await client.get("/tasks")
    assert res.status_code == 403
