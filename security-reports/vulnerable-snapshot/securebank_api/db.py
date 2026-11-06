"""
Capa de acceso a datos de SecureBank API.

Usa SQLite en memoria para mantener el laboratorio autocontenido y
reproducible (sin dependencias externas de base de datos). Todas las
consultas usan parámetros ligados (placeholders) — nunca concatenación
de strings — como control frente a SQL Injection (ver docs/threat-model.md,
amenaza #04).
"""
import sqlite3
import threading

_local = threading.local()


def get_db():
    """Devuelve una conexión SQLite por hilo, con el esquema ya creado."""
    if not hasattr(_local, "conn"):
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _init_schema(conn)
        _local.conn = conn
    return _local.conn


def _init_schema(conn):
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer'
        );

        CREATE TABLE accounts (
            id TEXT PRIMARY KEY,
            owner_username TEXT NOT NULL,
            balance INTEGER NOT NULL,
            FOREIGN KEY (owner_username) REFERENCES users(username)
        );

        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin_account TEXT NOT NULL,
            target_account TEXT NOT NULL,
            amount INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            username TEXT,
            detail TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()
    _seed(conn)


def _seed(conn):
    from .auth import hash_password

    demo_users = [
        ("alice", "Alice#2026Secure", "customer"),
        ("bob", "Bob#2026Secure", "customer"),
    ]
    for username, pwd, role in demo_users:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, hash_password(pwd), role),
        )

    conn.execute(
        "INSERT INTO accounts (id, owner_username, balance) VALUES (?, ?, ?)",
        ("1001", "alice", 500000),
    )
    conn.execute(
        "INSERT INTO accounts (id, owner_username, balance) VALUES (?, ?, ?)",
        ("2001", "bob", 150000),
    )
    conn.commit()


def log_event(event: str, username: str = None, detail: str = None):
    """Registra un evento de auditoría (control frente a Repudiation)."""
    conn = get_db()
    conn.execute(
        "INSERT INTO audit_log (event, username, detail) VALUES (?, ?, ?)",
        (event, username, detail),
    )
    conn.commit()
