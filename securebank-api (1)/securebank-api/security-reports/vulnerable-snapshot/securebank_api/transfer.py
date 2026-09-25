"""
Endpoint POST /transfer.

Corrección aplicada (amenaza #10 del Threat Model, BOLA — Broken Object
Level Authorization, OWASP API #1): antes de ejecutar la operación se
extrae el userId del JWT firmado y se compara contra el dueño real de
originAccount. Si no coincide -> 403 Forbidden + registro de auditoría,
tal como especifica la security story asociada (docs/security-stories.md).
"""
from flask import Blueprint, request, jsonify, g
from .db import get_db, log_event
from .auth import require_auth

bp = Blueprint("transfer", __name__)


@bp.post("/transfer")
@require_auth
def transfer():
    data = request.get_json(silent=True) or {}
    origin_account = data.get("originAccount")
    target_account = data.get("targetAccount")
    amount = data.get("amount")

    if not origin_account or not target_account or not isinstance(amount, int) or amount <= 0:
        return jsonify({"error": "originAccount, targetAccount y amount (entero > 0) son requeridos"}), 400

    db = get_db()
    origin = db.execute(
        "SELECT * FROM accounts WHERE id = ?", (origin_account,)
    ).fetchone()
    target = db.execute(
        "SELECT * FROM accounts WHERE id = ?", (target_account,)
    ).fetchone()

    if origin is None or target is None:
        return jsonify({"error": "cuenta origen o destino no existe"}), 404

    # SEGURO — control BOLA: el dueño de originAccount debe ser el
    # usuario autenticado. Ver caso de análisis en docs/threat-model.md.
    if origin["owner_username"] != g.current_user:
        log_event(
            "bola_attempt_blocked",
            username=g.current_user,
            detail=f"originAccount={origin_account}",
        )
        return jsonify({"error": "forbidden"}), 403

    if origin["balance"] < amount:
        return jsonify({"error": "fondos insuficientes"}), 400

    db.execute(
        "UPDATE accounts SET balance = balance - ? WHERE id = ?",
        (amount, origin_account),
    )
    db.execute(
        "UPDATE accounts SET balance = balance + ? WHERE id = ?",
        (amount, target_account),
    )
    db.execute(
        "INSERT INTO transactions (origin_account, target_account, amount) VALUES (?, ?, ?)",
        (origin_account, target_account, amount),
    )
    db.commit()
    log_event(
        "transfer_executed",
        username=g.current_user,
        detail=f"{origin_account}->{target_account}:{amount}",
    )
    return jsonify({"status": "ok"}), 200
