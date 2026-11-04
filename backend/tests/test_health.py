import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_returns_200(async_client: AsyncClient):
    """Test that the /api/v1/health endpoint is reachable and returns status 200 operational."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["service"] == "DocuMind Backend Core"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"
