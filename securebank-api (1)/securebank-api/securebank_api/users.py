"""
Endpoints de usuarios: login y registro.

Corrección aplicada (ver docs/security-reports/diff-fixes.md, hallazgo
Semgrep python.sqlalchemy.security.sqlalchemy-execute-raw-query / CWE-89):
toda consulta usa placeholders (?) — el driver separa código de datos,
la entrada del usuario nunca se interpreta como SQL.
"""
from flask import Blueprint, request, jsonify
from .db import get_db, log_event
from .auth import (
    verify_password,
    hash_password,
    issue_token,
    is_rate_limited,
    register_attempt,
)

bp = Blueprint("users", __name__)


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or len(password) < 10:
        return jsonify({"error": "username y password (>=10 chars) son requeridos"}), 400

    db = get_db()
    existing = db.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    if existing:
        return jsonify({"error": "usuario ya existe"}), 409

    db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'customer')",
        (username, hash_password(password)),
    )
    db.commit()
    log_event("user_registered", username=username)
    return jsonify({"status": "created", "username": username}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")
    client_ip = request.remote_addr or "unknown"

    # Control frente a fuerza bruta / DoS (amenaza #08 del Threat Model)
    if is_rate_limited(client_ip, username):
        log_event("login_rate_limited", username=username, detail=client_ip)
        return jsonify({"error": "demasiados intentos, intenta más tarde"}), 429

    db = get_db()
    # SEGURO — consulta parametrizada: el username nunca se concatena
    # dentro de la sentencia SQL (fix de CWE-89 / SQL Injection).
    row = db.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()

    if row is None or not verify_password(password, row["password_hash"]):
        # Solo los intentos fallidos cuentan para el rate limit — evita
        # bloquear a un usuario legítimo por su propio historial de éxito.
        register_attempt(client_ip, username)
        log_event("login_failed", username=username, detail=client_ip)
        return jsonify({"error": "credenciales inválidas"}), 401

    token = issue_token(row["username"], row["role"])
    log_event("login_success", username=username)
    return jsonify({"token": token}), 200
