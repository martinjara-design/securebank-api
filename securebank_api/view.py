"""
Plantilla de bienvenida.

Corrección aplicada (hallazgo Semgrep 'flask-secure-templates: XSS' /
CWE-79, ejercicio de la Sesión 05): la entrada del usuario se escapa
con markupsafe.escape() antes de insertarla en el HTML de respuesta —
nunca se interpola texto sin escapar dentro de una plantilla.
"""
from flask import Blueprint, request
from markupsafe import escape

bp = Blueprint("view", __name__)


@bp.get("/welcome")
def welcome():
    name = request.args.get("name", "cliente")
    # SEGURO — escape() neutraliza <, >, ", ' y & antes de renderizar.
    # Antes: f"<h1>Hola {name}</h1>" permitía inyectar <script>...</script>.
    safe_name = escape(name)
    return f"<h1>Hola {safe_name}</h1>", 200, {"Content-Type": "text/html"}
