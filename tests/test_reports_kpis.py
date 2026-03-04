from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token


client = TestClient(app)


def get_auth_header():
    token = create_access_token({"sub": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}


def test_get_kpis():
    resp = client.get("/api/v1/reports/kpis", headers=get_auth_header())
    assert resp.status_code == 200
    data = resp.json()
    assert "total_passengers" in data
