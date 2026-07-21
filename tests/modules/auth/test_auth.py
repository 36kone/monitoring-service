from fastapi.testclient import TestClient

from tests.conftest import API_PREFIX
from tests.seed import ADMIN_EMAIL, ADMIN_PASSWORD

BASE = f"{API_PREFIX}/auth"


def test_read_current_user(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get(f"{BASE}/me", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["id"] is not None


def test_update_current_user(client: TestClient, auth_headers: dict[str, str]) -> None:
    # email/phone são obrigatórios no update (evita sobrescrever com None).
    response = client.put(
        f"{BASE}/me",
        json={"name": "Admin Atualizado", "email": ADMIN_EMAIL, "phone": "5511111111111"},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Admin Atualizado"


def test_verify_by_password(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        f"{BASE}/verify-by-password", json={"password": ADMIN_PASSWORD}, headers=auth_headers
    )
    assert response.status_code in (200, 204), response.text


def test_forgot_password_valid_email(client: TestClient) -> None:
    response = client.post(
        f"{BASE}/forgot-password",
        json={"email": ADMIN_EMAIL},
    )
    assert response.status_code == 200, response.text


def test_forgot_password_unknown_email(client: TestClient) -> None:
    response = client.post(
        f"{BASE}/forgot-password",
        json={"email": "naoexiste@example.com"},
    )
    assert response.status_code == 404


def test_change_password_success(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.put(
        f"{BASE}/change-password",
        json={"current_password": ADMIN_PASSWORD, "new_password": "outraSenha456"},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text


def test_change_password_wrong_current(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.put(
        f"{BASE}/change-password",
        json={"current_password": "senha-errada", "new_password": "outraSenha456"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_setup_2fa_for_authenticated_user(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(f"{BASE}/me/setup-2fa", headers=auth_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "otp_secret" in body or "otpSecret" in body
