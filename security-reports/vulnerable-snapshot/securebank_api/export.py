"""
Exportador de reportes transaccionales.

VERSION VULNERABLE (snapshot pre-corrección, solo para generar el
reporte SAST 'before' — ver docs/security-reports/). Usa os.system()
con concatenación directa de entrada del usuario (CWE-78).
"""
import os
from pathlib import Path

from flask import Blueprint, request, jsonify, g
from .auth import require_auth
from .db import log_event

bp = Blueprint("export", __name__)

REPORTS_DIR = Path("/tmp/securebank_reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@bp.get("/export")
@require_auth
def export_report():
    filename = request.args.get("f", "")
    target_path = REPORTS_DIR / filename
    target_path.write_text("date,origin,target,amount\n")

    # VULNERABLE — concatenación de entrada de usuario en un comando de
    # shell (CWE-78 / Command Injection).
    os.system("cat " + filename)
    return jsonify({"content": "ok"}), 200
