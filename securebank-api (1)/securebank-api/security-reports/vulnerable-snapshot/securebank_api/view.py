"""
Plantilla de bienvenida.

VERSION VULNERABLE (snapshot pre-corrección, solo para generar el
reporte SAST 'before'). Interpola la entrada del usuario sin escapar
en el HTML de respuesta (CWE-79 / XSS).
"""
from flask import Blueprint, request

bp = Blueprint("view", __name__)


@bp.get("/welcome")
def welcome():
    name = request.args.get("name", "cliente")
    # VULNERABLE — sin escape: permite inyectar <script>...</script>.
    return f"<h1>Hola {name}</h1>", 200, {"Content-Type": "text/html"}
