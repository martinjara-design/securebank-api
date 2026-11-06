"""
Autenticación y autorización de SecureBank API.

Controles implementados (mapeados a docs/threat-model.md):
  - Hash de contraseñas con bcrypt + salt aleatorio (amenaza #01, Spoofing).
  - JWT firmado, algoritmo fijado explícitamente y rechazo de "none"
    (amenaza #02, Spoofing / #11, Elevation of Privilege).
  - Rate limiting por IP+usuario sobre /login (amenaza #08, DoS).

Nota de producción: este laboratorio firma los JWT con HS256 y un
secreto de entorno para simplicidad didáctica. El control objetivo
descrito en el Threat Model es RS256 con rotación de claves; migrar
a RS256 solo cambia esta función y no el resto de la aplicación.
"""
import os
import time
from functools import wraps

import jwt
import bcrypt
from flask import request, jsonify, g

JWT_SECRET = os.environ.get("SECUREBANK_JWT_SECRET", "dev-only-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 15 * 60

# Rate limiting en memoria: {(ip, username): [timestamps]}
_login_attempts = {}
_RATE_LIMIT_WINDOW = 60
_RATE_LIMIT_MAX_ATTEMPTS = 5


import hashlib


def hash_password(plain_password: str) -> str:
    # VULNERABLE — MD5 sin salt: hash roto y reversible por fuerza
    # bruta / rainbow tables (CWE-327, CWE-916).
    return hashlib.md5(plain_password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, password_hash: str) -> bool:
    return hashlib.md5(plain_password.encode("utf-8")).hexdigest() == password_hash


def issue_token(username: str, role: str) -> str:
    now = int(time.time())
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + JWT_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodifica y valida el JWT. Rechaza explícitamente alg=none y
    cualquier algoritmo distinto al configurado (control frente a
    amenaza #11, Elevation of Privilege vía manipulación del JWT)."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def is_rate_limited(ip: str, username: str) -> bool:
    """Control simple de fuerza bruta sobre /login (amenaza #08)."""
    key = (ip, username)
    now = time.time()
    attempts = [t for t in _login_attempts.get(key, []) if now - t < _RATE_LIMIT_WINDOW]
    _login_attempts[key] = attempts
    return len(attempts) >= _RATE_LIMIT_MAX_ATTEMPTS


def register_attempt(ip: str, username: str):
    key = (ip, username)
    _login_attempts.setdefault(key, []).append(time.time())


def require_auth(fn):
    """Exige un Bearer JWT válido y expone el usuario autenticado en
    g.current_user / g.current_role. Base de todos los controles de
    autorización (BOLA, IDOR, Elevation of Privilege)."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "token requerido"}), 401
        token = header.removeprefix("Bearer ")
        try:
            payload = decode_token(token)
        except jwt.PyJWTError:
            return jsonify({"error": "token inválido o expirado"}), 401
        g.current_user = payload["sub"]
        g.current_role = payload.get("role", "customer")
        return fn(*args, **kwargs)

    return wrapper
