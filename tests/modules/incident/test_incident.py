from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.modules.incident.incident_enum import IncidentStatusEnum
from app.modules.incident.incident_schema import CreateIncident
from tests.conftest import API_PREFIX

MONITORS_BASE = f"{API_PREFIX}/monitors"
INCIDENTS_BASE = f"{API_PREFIX}/incidents"


def _create_monitor(client: TestClient, auth_headers: dict[str, str]) -> dict:
    response = client.post(
        MONITORS_BASE,
        json={
            "name": "API com incidentes",
            "url": "https://example.com/health",
            "method": "GET",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_incident(
    client: TestClient,
    auth_headers: dict[str, str],
    monitor_id: str,
    **overrides,
) -> dict:
    payload = {"status": "open"}
    payload.update(overrides)
    response = client.post(
        f"{INCIDENTS_BASE}/{monitor_id}",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_incident(client: TestClient, auth_headers: dict[str, str]) -> None:
    monitor = _create_monitor(client, auth_headers)

    response = client.post(
        f"{INCIDENTS_BASE}/{monitor['id']}",
        json={"status": "open"},
        headers=auth_headers,
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["id"]
    assert data["monitorId"] == monitor["id"]
    assert data["status"] == IncidentStatusEnum.OPEN
    assert data["resolvedAt"] is None


def test_list_incidents_with_status_filter(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    monitor = _create_monitor(client, auth_headers)
    _create_incident(client, auth_headers, monitor["id"])
    _create_incident(
        client,
        auth_headers,
        monitor["id"],
        status="resolved",
        resolvedAt=datetime.now(UTC).isoformat(),
        durationSeconds=120,
    )

    response = client.get(
        f"{INCIDENTS_BASE}/{monitor['id']}",
        params={"status": "resolved"},
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["pagination"]["total"] == 1
    assert data["list"][0]["status"] == "resolved"
    assert data["list"][0]["durationSeconds"] == 120


def test_get_update_and_delete_incident(client: TestClient, auth_headers: dict[str, str]) -> None:
    monitor = _create_monitor(client, auth_headers)
    incident = _create_incident(client, auth_headers, monitor["id"])
    url = f"{INCIDENTS_BASE}/{monitor['id']}/{incident['id']}"
    resolved_at = datetime.now(UTC)

    response = client.get(url, headers=auth_headers)
    assert response.status_code == 200, response.text

    response = client.put(
        url,
        json={
            "status": "resolved",
            "resolvedAt": resolved_at.isoformat(),
            "durationSeconds": 45,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "resolved"
    assert response.json()["durationSeconds"] == 45

    response = client.delete(url, headers=auth_headers)
    assert response.status_code == 204
    assert client.get(url, headers=auth_headers).status_code == 404


def test_incident_requires_existing_monitor(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{INCIDENTS_BASE}/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_incident_validation(client: TestClient, auth_headers: dict[str, str]) -> None:
    monitor = _create_monitor(client, auth_headers)
    started_at = datetime.now(UTC)

    response = client.post(
        f"{INCIDENTS_BASE}/{monitor['id']}",
        json={
            "status": "resolved",
            "startedAt": started_at.isoformat(),
            "resolvedAt": (started_at - timedelta(seconds=1)).isoformat(),
            "durationSeconds": -1,
        },
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_incident_schema_defaults() -> None:
    incident = CreateIncident()

    assert incident.status == IncidentStatusEnum.OPEN
    assert incident.started_at is None
    assert incident.resolved_at is None
