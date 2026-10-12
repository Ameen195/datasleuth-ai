
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["application"] == "DataSleuth AI"


def test_investigation_rejects_non_csv_files():
    response = client.post(
        "/api/v1/investigations",
        files={
            "baseline": ("baseline.txt", b"a,b\n1,2\n", "text/plain"),
            "current": ("current.csv", b"a,b\n1,2\n", "text/csv"),
        },
    )

    assert response.status_code == 400
