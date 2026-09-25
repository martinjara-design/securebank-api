"""
Calculadora de tasas de interés.

VERSION VULNERABLE (snapshot pre-corrección, solo para generar el
reporte SAST 'before'). Usa eval() directamente sobre la entrada del
usuario (CWE-95 / ejecución de código arbitrario).
"""
from flask import Blueprint, request, jsonify, g
from .auth import require_auth
from .db import log_event

bp = Blueprint("calc", __name__)


@bp.post("/calc/rate")
@require_auth
def calc_rate():
    data = request.get_json(silent=True) or {}
    expression = data.get("expression", "")

    # VULNERABLE — eval() sobre entrada externa (CWE-95 / RCE).
    result = eval(expression)
    return jsonify({"result": result}), 200
