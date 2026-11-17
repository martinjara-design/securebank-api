"""Comprueba autorización por cuenta contra la API en ejecución."""

import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8080"


def request(method, path, body=None, token=None):
    headers = {}
    data = None

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(
        BASE_URL + path,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(req, timeout=10) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.loads(error.read())


def login(username, password):
    status, body = request(
        "POST",
        "/login",
        {"username": username, "password": password},
    )

    if status != 200 or not body.get("token"):
        raise RuntimeError(f"No se pudo autenticar a {username}")

    return body["token"]


def check(label, path, expected_status, token=None, owner=None):
    status, body = request("GET", path, token=token)

    if status != expected_status:
        raise RuntimeError(
            f"{label}: esperado {expected_status}, recibido {status}"
        )

    if owner is not None and body.get("owner") != owner:
        raise RuntimeError(f"{label}: propietario incorrecto")

    if expected_status in (401, 403):
        if any(field in body for field in ("balance", "owner", "id")):
            raise RuntimeError(f"{label}: respuesta con datos de cuenta")

    print(f"PASS: {label} -> HTTP {status}")


def main():
    alice_token = login(
        "alice",
        os.environ["SECUREBANK_DEMO_ALICE_PASSWORD"],
    )
    bob_token = login(
        "bob",
        os.environ["SECUREBANK_DEMO_BOB_PASSWORD"],
    )

    check("Sin token", "/accounts/1001", 401)

    check(
        "Alice consulta su cuenta",
        "/accounts/1001",
        200,
        alice_token,
        owner="alice",
    )
    check(
        "Bob consulta su cuenta",
        "/accounts/2001",
        200,
        bob_token,
        owner="bob",
    )
    check(
        "Alice intenta consultar la cuenta de Bob",
        "/accounts/2001",
        403,
        alice_token,
    )
    check(
        "Bob intenta consultar la cuenta de Alice",
        "/accounts/1001",
        403,
        bob_token,
    )

    print("Resultado: las cinco comprobaciones pasaron.")


if __name__ == "__main__":
    main()
