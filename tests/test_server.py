import pytest
from httpx import AsyncClient, ASGITransport
from codeguard.server import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_create_session(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/session", json={"workspace": "/tmp"})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data


@pytest.mark.asyncio
async def test_get_history_empty(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/session/fake-id/history")
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.asyncio
async def test_credentials_status(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/credentials/status")
        assert resp.status_code == 200
        assert "configured" in resp.json()
