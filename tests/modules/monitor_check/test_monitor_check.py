from fastapi.testclient import TestClient

from app.modules.monitor.monitor_enum import MonitorStatusEnum
from app.modules.monitor_check.monitor_check_schema import CreateMonitorCheck
from tests.conftest import API_PREFIX

MONITORS_BASE = f"{API_PREFIX}/monitors"


def _create_monitor(client: TestClient, auth_headers: dict[str, str]) -> dict:
    response = client.post(
        MONITORS_BASE,
        json={
            "name": "API para checks",
            "url": "https://example.com/health",
            "method": "GET",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_check(
    client: TestClient,
    auth_headers: dict[str, str],
    monitor_id: str,
    **overrides,
) -> dict:
    payload = {
        "status": "up",
        "statusCode": 200,
        "success": True,
        "latencyMs": 143,
        "timedOut": False,
    }
    payload.update(overrides)
    response = client.post(
        f"{MONITORS_BASE}/{monitor_id}/checks",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_monitor_check(client: TestClient, auth_headers: dict[str, str]) -> None:
    monitor = _create_monitor(client, auth_headers)

    response = client.post(
        f"{MONITORS_BASE}/{monitor['id']}/checks",
        json={
            "status": "down",
            "statusCode": 503,
            "success": False,
            "error": "Service unavailable",
            "timedOut": False,
        },
        headers=auth_headers,
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["monitorId"] == monitor["id"]
    assert data["status"] == "down"
    assert data["statusCode"] == 503
    assert data["success"] is False


def test_list_monitor_checks_with_filters(client: TestClient, auth_headers: dict[str, str]) -> None:
    monitor = _create_monitor(client, auth_headers)
    _create_check(client, auth_headers, monitor["id"])
    _create_check(
        client,
        auth_headers,
        monitor["id"],
        status="down",
        statusCode=500,
        success=False,
    )

    response = client.get(
        f"{MONITORS_BASE}/{monitor['id']}/checks",
        params={"status": "down", "success": "false"},
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["pagination"]["total"] == 1
    assert data["list"][0]["statusCode"] == 500


def test_get_update_and_delete_monitor_check(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    monitor = _create_monitor(client, auth_headers)
    check = _create_check(client, auth_headers, monitor["id"])
    url = f"{MONITORS_BASE}/{monitor['id']}/checks/{check['id']}"

    response = client.get(url, headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["id"] == check["id"]

    response = client.put(
        url,
        json={"status": "degraded", "latencyMs": 900},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "degraded"
    assert response.json()["latencyMs"] == 900

    response = client.delete(url, headers=auth_headers)
    assert response.status_code == 204
    assert client.get(url, headers=auth_headers).status_code == 404


def test_monitor_check_requires_existing_monitor(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{MONITORS_BASE}/00000000-0000-0000-0000-000000000000/checks",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_monitor_check_validation(client: TestClient, auth_headers: dict[str, str]) -> None:
    monitor = _create_monitor(client, auth_headers)

    response = client.post(
        f"{MONITORS_BASE}/{monitor['id']}/checks",
        json={"statusCode": 99, "latencyMs": -1},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_monitor_check_schema_defaults() -> None:
    check = CreateMonitorCheck()

    assert check.status == MonitorStatusEnum.UNKNOWN
    assert check.success is False
    assert check.timed_out is False
