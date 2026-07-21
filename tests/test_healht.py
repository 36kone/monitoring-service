"""Teste inicial: valida que a infraestrutura de testes está funcionando."""

from fastapi.testclient import TestClient
import pytest


def test_client_fixture_is_working(client: TestClient) -> None:
    assert client is not None


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/core/health")

    assert response.status_code == 200
    assert response.json()["message"] == "Core Running OK"
    assert response.json()["databaseAlive"] is True


def test_health_check_database_unavailable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Com o banco fora, o health devolve 503 mas ainda com o corpo do HealthMessage."""

    def _db_down(*args, **kwargs):
        raise Exception("banco indisponível")

    monkeypatch.setattr("app.api.v1.health.health_controller.get_db", _db_down)

    response = client.get("/api/core/health")

    assert response.status_code == 503
    body = response.json()
    assert body["databaseAlive"] is False
    assert body["message"] == "Database unavailable"
