import pytest


@pytest.mark.asyncio
async def test_register(client):
    res = await client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "pass123"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == "alice"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    payload = {"username": "bob", "email": "bob@example.com", "password": "pass123"}
    await client.post("/auth/register", json=payload)
    res = await client.post(
        "/auth/register",
        json={"username": "bob", "email": "other@example.com", "password": "pass123"},
    )
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post(
        "/auth/register",
        json={"username": "carol", "email": "carol@example.com", "password": "pass123"},
    )
    res = await client.post(
        "/auth/login",
        json={"username": "carol", "password": "pass123"},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        "/auth/register",
        json={"username": "dave", "email": "dave@example.com", "password": "pass123"},
    )
    res = await client.post(
        "/auth/login",
        json={"username": "dave", "password": "wrongpass"},
    )
    assert res.status_code == 401
