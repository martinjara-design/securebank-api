"""
Autenticación y autorización de SecureBank API.

Controles implementados (mapeados a docs/threat-model.md):
  - Hash de contraseñas con bcrypt + salt aleatorio (amenaza #01, Spoofing).
  - JWT firmado, algoritmo fijado explícitamente y rechazo de "none"
    (amenaza #02, Spoofing / #11, Elevation of Privilege).
  - Rate limiting por IP+usuario sobre /login (amenaza #08, DoS).


"""
import os
import time
from functools import wraps

import jwt
import bcrypt
from flask import request, jsonify, g

def _load_jwt_secret() -> str:
    """Lee el secreto JWT del entorno. Falla cerrado: sin valor por defecto.

    Sesión 07 (Secret Management): un fallback literal como "dev-only-change-me"
    es un secreto hardcodeado de facto, porque cualquier despliegue que olvide
    definir la variable queda firmando tokens con una clave pública conocida.
    """
    value = os.environ.get("SECUREBANK_JWT_SECRET", "")
    if len(value) < 32:
        raise RuntimeError(
            "SECUREBANK_JWT_SECRET no definido o demasiado corto (mínimo 32 "
            "caracteres). Ver docs/SECRETS.md §2."
        )
    return value


JWT_SECRET = _load_jwt_secret()
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_SECONDS = 15 * 60

# Rate limiting en memoria: {(ip, username): [timestamps]}
_login_attempts = {}
_RATE_LIMIT_WINDOW = 60
_RATE_LIMIT_MAX_ATTEMPTS = 5


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except ValueError:
        return False


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
