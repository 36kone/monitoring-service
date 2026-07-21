from fastapi.testclient import TestClient

from tests.conftest import API_PREFIX

BASE = f"{API_PREFIX}/users"


def _new_user_payload(**overrides) -> dict:
    payload = {
        "name": "Usuário Teste",
        "email": "usuario.teste@example.com",
        "password": "senha123",
        "phone": "5511999999999",
    }
    payload.update(overrides)
    return payload


def _create_user(client: TestClient, auth_headers: dict[str, str], **overrides) -> dict:
    response = client.post(BASE, json=_new_user_payload(**overrides), headers=auth_headers)
    assert response.status_code in (200, 201), response.text
    return response.json()


def test_create_user(client: TestClient, auth_headers: dict[str, str]) -> None:
    payload = _new_user_payload()

    response = client.post(BASE, json=payload, headers=auth_headers)

    assert response.status_code == 201, response.text

    data = response.json()
    assert data["id"] is not None
    assert data["email"] == payload["email"]
    assert data["name"] == payload["name"]


def test_list_users(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get(BASE, headers=auth_headers)

    assert response.status_code == 200, response.text

    data = response.json()
    assert "pagination" in data
    assert "list" in data
    assert isinstance(data["list"], list)
    assert data["pagination"]["total"] >= 1


def test_list_users_with_filters(client: TestClient, auth_headers: dict[str, str]) -> None:
    _create_user(client, auth_headers)

    response = client.get(
        BASE,
        params={"keyword": "Usuário", "status": "active", "roles": ["user"]},
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "pagination" in data
    assert isinstance(data["list"], list)


def test_get_user_by_id(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = _create_user(client, auth_headers)

    response = client.get(f"{BASE}/{created['id']}", headers=auth_headers)

    assert response.status_code == 200, response.text
    assert response.json()["id"] == created["id"]


def test_update_user(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = _create_user(client, auth_headers)

    response = client.put(
        f"{BASE}/{created['id']}",
        json={"name": "Usuário Atualizado"},
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Usuário Atualizado"


def test_delete_user(client: TestClient, auth_headers: dict[str, str]) -> None:
    created = _create_user(client, auth_headers)

    delete_response = client.delete(f"{BASE}/{created['id']}", headers=auth_headers)

    assert delete_response.status_code == 204

    second_delete = client.delete(f"{BASE}/{created['id']}", headers=auth_headers)
    assert second_delete.status_code == 404


def test_get_user_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get(f"{BASE}/00000000-0000-0000-0000-000000000000", headers=auth_headers)

    assert response.status_code == 404


def test_create_user_with_invalid_payload(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(BASE, json={}, headers=auth_headers)

    assert response.status_code == 422
