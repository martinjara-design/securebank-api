"""
Exportador de reportes transaccionales.

Corrección aplicada (hallazgo Semgrep 'command injection detected' /
CWE-78, ejercicio de 5 vulnerabilidades de la Sesión 05): se reemplaza
os.system() con concatenación de entrada del usuario por una lectura
directa del archivo desde Python (sin subprocesos ni shell), de modo
que el nombre de archivo nunca se interpreta como shell.
"""
import re
import tempfile
from pathlib import Path

from flask import Blueprint, request, jsonify, g
from .auth import require_auth
from .db import log_event

bp = Blueprint("export", __name__)

# Portable (Linux/macOS/Windows): antes "/tmp/..." y el binario "cat" solo
# existían en Linux.
REPORTS_DIR = Path(tempfile.gettempdir()) / "securebank_reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Solo nombres de archivo simples — sin separadores de ruta, sin
# metacaracteres de shell (control adicional de allowlist).
_SAFE_FILENAME = re.compile(r"^[a-zA-Z0-9_\-]{1,64}\.csv$")


@bp.get("/export")
@require_auth
def export_report():
    filename = request.args.get("f", "")

    if not _SAFE_FILENAME.match(filename):
        log_event(
            "export_rejected_unsafe_filename",
            username=g.current_user,
            detail=filename,
        )
        return jsonify({"error": "nombre de archivo inválido"}), 400

    target_path = REPORTS_DIR / filename
    target_path.write_text("date,origin,target,amount\n")  # datos de ejemplo

    # SEGURO — sin shell ni subprocesos: el archivo se lee desde Python y el
    # nombre ya fue validado por allowlist. Antes: os.system("cat " + filename)
    # permitía RCE vía ';' o '|' en el nombre de archivo (CWE-78).
    content = target_path.read_text()
    return jsonify({"content": content}), 200
