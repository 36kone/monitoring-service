from fastapi.testclient import TestClient

from tests.conftest import API_PREFIX


def test_dashboard_home_returns_ok(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get(f"{API_PREFIX}/dashboards/home", headers=auth_headers)

    assert response.status_code == 200, response.text
