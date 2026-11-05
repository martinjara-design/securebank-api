"""
Pruebas unitarias — etapa 'Unit Tests' del pipeline SecurePipeline.

Cubren: autenticación, autorización por recurso (IDOR/BOLA), rate
limiting, exportación segura y el evaluador aritmético seguro. No
requieren red ni una base de datos externa (SQLite en memoria).
"""
import json
import pytest

from securebank_api.app import create_app
from securebank_api.calc import safe_arithmetic_eval, UnsafeExpression


@pytest.fixture()
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


def _login(client, username, password):
    resp = client.post(
        "/login",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )
    return resp


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_login_success(client):
    resp = _login(client, "alice", "Alice#2026Secure")
    assert resp.status_code == 200
    assert "token" in resp.get_json()


def test_login_invalid_credentials(client):
    resp = _login(client, "alice", "wrong-password")
    assert resp.status_code == 401


def test_login_rejects_sql_injection_payload(client):
    """El username ' OR '1'='1 debe tratarse como texto literal, no SQL."""
    resp = _login(client, "' OR '1'='1", "whatever")
    assert resp.status_code == 401


def test_account_access_forbidden_for_non_owner(client):
    token = _login(client, "bob", "Bob#2026Secure").get_json()["token"]
    # bob intenta consultar la cuenta 1001, que pertenece a alice (IDOR)
    resp = client.get(
        "/accounts/1001", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_account_access_allowed_for_owner(client):
    token = _login(client, "alice", "Alice#2026Secure").get_json()["token"]
    resp = client.get(
        "/accounts/1001", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["owner"] == "alice"


def test_transfer_blocked_for_non_owner_account_bola(client):
    """Caso analizado en docs/threat-model.md: BOLA en POST /transfer."""
    token = _login(client, "bob", "Bob#2026Secure").get_json()["token"]
    resp = client.post(
        "/transfer",
        data=json.dumps(
            {"originAccount": "1001", "targetAccount": "2001", "amount": 500000}
        ),
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_transfer_success_for_owner(client):
    token = _login(client, "alice", "Alice#2026Secure").get_json()["token"]
    resp = client.post(
        "/transfer",
        data=json.dumps(
            {"originAccount": "1001", "targetAccount": "2001", "amount": 1000}
        ),
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_transfer_requires_auth(client):
    resp = client.post(
        "/transfer",
        data=json.dumps({"originAccount": "1001", "targetAccount": "2001", "amount": 100}),
        content_type="application/json",
    )
    assert resp.status_code == 401


def test_welcome_escapes_script_tag(client):
    resp = client.get("/welcome?name=<script>alert(1)</script>")
    assert b"<script>" not in resp.data
    assert b"&lt;script&gt;" in resp.data


def test_export_rejects_unsafe_filename(client):
    token = _login(client, "alice", "Alice#2026Secure").get_json()["token"]
    resp = client.get(
        "/export?f=report.csv; rm -rf /",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_export_accepts_safe_filename(client):
    token = _login(client, "alice", "Alice#2026Secure").get_json()["token"]
    resp = client.get(
        "/export?f=movimientos.csv",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_safe_arithmetic_eval_computes_expression():
    assert safe_arithmetic_eval("100 * (1 + 0.05)") == pytest.approx(105.0)


def test_safe_arithmetic_eval_rejects_code_injection():
    with pytest.raises((UnsafeExpression, SyntaxError)):
        safe_arithmetic_eval("__import__('os').system('id')")


def test_rate_limiting_blocks_after_threshold(client):
    for _ in range(5):
        _login(client, "carol", "wrong-password")
    resp = _login(client, "carol", "wrong-password")
    assert resp.status_code == 429
