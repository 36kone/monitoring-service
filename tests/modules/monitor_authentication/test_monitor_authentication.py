from fastapi.testclient import TestClient

from tests.conftest import API_PREFIX

MONITORS = f"{API_PREFIX}/monitors"


def test_create_and_read_api_key_authentication(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    monitor_response = client.post(
        MONITORS,
        json={"name": "Private API", "url": "https://example.com", "method": "GET"},
        headers=auth_headers,
    )
    assert monitor_response.status_code == 201, monitor_response.text
    monitor_id = monitor_response.json()["id"]

    response = client.put(
        f"{MONITORS}/{monitor_id}/authentication",
        json={
            "authType": "api_key",
            "credentials": {"apiKey": "secret-value", "headerName": "X-API-Key"},
        },
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["authType"] == "api_key"
    assert response.json()["configured"] is True
    assert "secret-value" not in response.text

    response = client.get(
        f"{MONITORS}/{monitor_id}/authentication", headers=auth_headers
    )
    assert response.status_code == 200, response.text
    assert response.json()["configured"] is True
    assert "secret-value" not in response.text
