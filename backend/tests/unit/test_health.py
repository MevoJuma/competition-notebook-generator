import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Test platform root endpoint returns valid metadata."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "platform" in data
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_check_endpoint(async_client: AsyncClient):
    """Test health check endpoint returns 200 and storage status."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "storage" in data
    assert data["storage"]["upload_dir_exists"] is True
    assert data["storage"]["generated_dir_exists"] is True


@pytest.mark.asyncio
async def test_api_v1_health_check_endpoint(async_client: AsyncClient):
    """Test /api/v1/health check endpoint alias."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
