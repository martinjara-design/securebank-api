"""
Calculadora de tasas de interés.

Corrección aplicada (hallazgo Semgrep 'python.lang.security.audit.eval-detected'
/ CWE-95, ejercicio de la Sesión 05): eval() sobre entrada del usuario
permite ejecución arbitraria de código. Se reemplaza por un evaluador
aritmético restringido, construido sobre el AST de Python, que solo
admite números y los operadores +, -, *, /, ** y paréntesis.
"""
import ast
import operator

from flask import Blueprint, request, jsonify, g
from .auth import require_auth
from .db import log_event

bp = Blueprint("calc", __name__)

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARYOPS = {ast.USub: operator.neg, ast.UAdd: operator.pos}


class UnsafeExpression(ValueError):
    pass


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](
            _safe_eval(node.left), _safe_eval(node.right)
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return _ALLOWED_UNARYOPS[type(node.op)](_safe_eval(node.operand))
    raise UnsafeExpression("expresión no permitida")


def safe_arithmetic_eval(expression: str):
    """Evalúa una expresión aritmética simple sin exponer eval()/exec()
    a la entrada del usuario. Antes: eval(payload) permitía RCE."""
    parsed = ast.parse(expression, mode="eval")
    return _safe_eval(parsed)


@bp.post("/calc/rate")
@require_auth
def calc_rate():
    data = request.get_json(silent=True) or {}
    expression = data.get("expression", "")

    try:
        result = safe_arithmetic_eval(expression)
    except (UnsafeExpression, SyntaxError, TypeError, ZeroDivisionError):
        log_event("calc_rejected_expression", username=g.current_user, detail=expression)
        return jsonify({"error": "expresión inválida"}), 400

    return jsonify({"result": result}), 200
