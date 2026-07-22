from fastapi.testclient import TestClient

from app.modules.monitor.monitor_enum import MonitorStatusEnum
from app.modules.monitor.monitor_schema import CreateMonitor
from tests.conftest import API_PREFIX

BASE = f"{API_PREFIX}/monitors"


def _new_monitor_payload(**overrides) -> dict:
    payload = {
        "name": "API principal",
        "url": "https://example.com/health",
        "method": "get",
        "intervalSeconds": 30,
        "timeoutMs": 2000,
        "enabled": True,
    }
    payload.update(overrides)
    return payload


def _create_monitor(client: TestClient, auth_headers: dict[str, str], **overrides) -> dict:
    response = client.post(BASE, json=_new_monitor_payload(**overrides), headers=auth_headers)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_monitor(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(BASE, json=_new_monitor_payload(), headers=auth_headers)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["id"]
    assert data["method"] == "GET"
    assert data["status"] == MonitorStatusEnum.UNKNOWN
    assert data["consecutiveFailures"] == 0
    assert data["consecutiveSuccesses"] == 0


def test_list_monitors_with_filters(client: TestClient, auth_headers: dict[str, str]) -> None:
    _create_monitor(client, auth_headers)
    _create_monitor(client, auth_headers, name="Monitor desativado", enabled=False)

    response = client.get(
        BASE,
        params={"keyword": "principal", "enabled": "true", "status": "unknown"},
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["pagination"]["total"] == 1
    assert data["list"][0]["name"] == "API principal"


def test_get_update_and_delete_monitor(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = _create_monitor(client, auth_headers)

    response = client.get(f"{BASE}/{created['id']}", headers=auth_headers)
    assert response.status_code == 200

    response = client.put(
        f"{BASE}/{created['id']}",
        json={"name": "API atualizada", "timeoutMs": 3000},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "API atualizada"
    assert response.json()["timeoutMs"] == 3000

    response = client.delete(f"{BASE}/{created['id']}", headers=auth_headers)
    assert response.status_code == 204
    assert client.get(f"{BASE}/{created['id']}", headers=auth_headers).status_code == 404


def test_monitor_validation(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        BASE,
        json=_new_monitor_payload(url="not-a-url", intervalSeconds=0),
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_monitor_requires_authentication(client: TestClient) -> None:
    response = client.get(BASE)

    assert response.status_code in (401, 403)


def test_create_monitor_schema_normalizes_method() -> None:
    monitor = CreateMonitor(name="Monitor", url="https://example.com", method=" post ")

    assert monitor.method == "POST"
