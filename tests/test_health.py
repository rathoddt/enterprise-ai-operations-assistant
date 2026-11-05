from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():

    response = client.get("/")

    assert response.status_code == 200

    assert (
        response.json()["application"]
        == "Enterprise AI Operations Assistant"
    )


def test_health_endpoint():

    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_chat_endpoint():

    payload = {
        "question": "What is our payment policy?"
    }

    response = client.post(
        "/api/v1/assistant/chat",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "success"
    assert data["conversation_id"] is not None


def test_chat_validation():

    payload = {
        "question": "Hi"
    }

    response = client.post(
        "/api/v1/assistant/chat",
        json=payload
    )

    assert response.status_code == 422


def test_chat_rejects_extra_fields():

    payload = {
        "question": "What is our payment policy?",
        "unexpected": "value"
    }

    response = client.post(
        "/api/v1/assistant/chat",
        json=payload
    )

    assert response.status_code == 422