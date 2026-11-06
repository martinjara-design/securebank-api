"""
Endpoints de cuentas.

Corrección aplicada (amenaza #06 del Threat Model, IDOR en
GET /accounts/{id}): la autorización se resuelve por *propiedad del
recurso* contra el usuario del JWT, nunca confiando en el {id} de la URL.
"""
from flask import Blueprint, jsonify, g
from .db import get_db, log_event
from .auth import require_auth

bp = Blueprint("accounts", __name__)


@bp.get("/accounts/<account_id>")
@require_auth
def get_account(account_id):
    db = get_db()
    account = db.execute(
        "SELECT * FROM accounts WHERE id = ?", (account_id,)
    ).fetchone()

    if account is None:
        return jsonify({"error": "cuenta no encontrada"}), 404

    # SEGURO — autorización por recurso: solo el dueño (o un admin) puede
    # consultar el saldo. Antes: cualquier {id} devolvía el saldo ajeno.
    if account["owner_username"] != g.current_user and g.current_role != "admin":
        log_event(
            "unauthorized_account_access",
            username=g.current_user,
            detail=f"account={account_id}",
        )
        return jsonify({"error": "forbidden"}), 403

    return jsonify(
        {"id": account["id"], "owner": account["owner_username"], "balance": account["balance"]}
    ), 200
