# Diff de correcciones aplicadas — Sesión 05 (SAST)

Generado a partir de una ejecución real de `diff -u` entre el snapshot
vulnerable (`security-reports/vulnerable-snapshot/`, usado únicamente
para producir `sast-before.sarif`) y el código corregido en
`securebank_api/`. Cada bloque corresponde a un hallazgo Semgrep del
reporte `sast-before.sarif` que queda en cero en `sast-after.sarif`.


## `securebank_api/users.py` — CWE-89 · SQL Injection (POST /login)

```diff
--- security-reports/vulnerable-snapshot/securebank_api/users.py	2026-09-23 20:30:28.334516128 +0000
+++ securebank_api/users.py	2026-09-23 20:29:30.991958535 +0000
@@ -57,9 +57,11 @@
         return jsonify({"error": "demasiados intentos, intenta más tarde"}), 429
 
     db = get_db()
-    # VULNERABLE — concatenación de strings (CWE-89 / SQL Injection).
-    query = "SELECT * FROM users WHERE username='" + username + "'"
-    row = db.execute(query).fetchone()
+    # SEGURO — consulta parametrizada: el username nunca se concatena
+    # dentro de la sentencia SQL (fix de CWE-89 / SQL Injection).
+    row = db.execute(
+        "SELECT * FROM users WHERE username = ?", (username,)
+    ).fetchone()
 
     if row is None or not verify_password(password, row["password_hash"]):
         # Solo los intentos fallidos cuentan para el rate limit — evita
```


## `securebank_api/auth.py` — CWE-327 / CWE-916 · MD5 password hash (auth)

```diff
--- security-reports/vulnerable-snapshot/securebank_api/auth.py	2026-09-23 20:30:40.620377284 +0000
+++ securebank_api/auth.py	2026-09-23 20:27:56.161860806 +0000
@@ -30,17 +30,18 @@
 _RATE_LIMIT_MAX_ATTEMPTS = 5
 
 
-import hashlib
-
-
 def hash_password(plain_password: str) -> str:
-    # VULNERABLE — MD5 sin salt: hash roto y reversible por fuerza
-    # bruta / rainbow tables (CWE-327, CWE-916).
-    return hashlib.md5(plain_password.encode("utf-8")).hexdigest()
+    salt = bcrypt.gensalt()
+    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")
 
 
 def verify_password(plain_password: str, password_hash: str) -> bool:
-    return hashlib.md5(plain_password.encode("utf-8")).hexdigest() == password_hash
+    try:
+        return bcrypt.checkpw(
+            plain_password.encode("utf-8"), password_hash.encode("utf-8")
+        )
+    except ValueError:
+        return False
 
 
 def issue_token(username: str, role: str) -> str:
```


## `securebank_api/export.py` — CWE-78 · Command Injection (exportador de reportes)

```diff
--- security-reports/vulnerable-snapshot/securebank_api/export.py	2026-09-23 20:30:32.928046912 +0000
+++ securebank_api/export.py	2026-09-23 20:28:17.012306451 +0000
@@ -1,11 +1,14 @@
 """
 Exportador de reportes transaccionales.
 
-VERSION VULNERABLE (snapshot pre-corrección, solo para generar el
-reporte SAST 'before' — ver docs/security-reports/). Usa os.system()
-con concatenación directa de entrada del usuario (CWE-78).
+Corrección aplicada (hallazgo Semgrep 'command injection detected' /
+CWE-78, ejercicio de 5 vulnerabilidades de la Sesión 05): se reemplaza
+os.system() con concatenación de entrada del usuario por
+subprocess.run() con una lista de argumentos y shell=False, de modo
+que el nombre de archivo nunca se interpreta como shell.
 """
-import os
+import re
+import subprocess
 from pathlib import Path
 
 from flask import Blueprint, request, jsonify, g
@@ -17,15 +20,35 @@
 REPORTS_DIR = Path("/tmp/securebank_reports")
 REPORTS_DIR.mkdir(parents=True, exist_ok=True)
 
+# Solo nombres de archivo simples — sin separadores de ruta, sin
+# metacaracteres de shell (control adicional de allowlist).
+_SAFE_FILENAME = re.compile(r"^[a-zA-Z0-9_\-]{1,64}\.csv$")
+
 
 @bp.get("/export")
 @require_auth
 def export_report():
     filename = request.args.get("f", "")
+
+    if not _SAFE_FILENAME.match(filename):
+        log_event(
+            "export_rejected_unsafe_filename",
+            username=g.current_user,
+            detail=filename,
+        )
+        return jsonify({"error": "nombre de archivo inválido"}), 400
+
     target_path = REPORTS_DIR / filename
-    target_path.write_text("date,origin,target,amount\n")
+    target_path.write_text("date,origin,target,amount\n")  # datos de ejemplo
 
-    # VULNERABLE — concatenación de entrada de usuario en un comando de
-    # shell (CWE-78 / Command Injection).
-    os.system("cat " + filename)
-    return jsonify({"content": "ok"}), 200
+    # SEGURO — sin shell, argumentos como lista, filename ya validado
+    # por allowlist. Antes: os.system("cat " + filename) permitía RCE
+    # vía ';' o '|' en el nombre de archivo (CWE-78).
+    result = subprocess.run(
+        ["cat", str(target_path)],
+        shell=False,
+        capture_output=True,
+        text=True,
+        timeout=5,
+    )
+    return jsonify({"content": result.stdout}), 200
```


## `securebank_api/view.py` — CWE-79 · Cross-Site Scripting (plantilla de bienvenida)

```diff
--- security-reports/vulnerable-snapshot/securebank_api/view.py	2026-09-23 20:30:36.134563258 +0000
+++ securebank_api/view.py	2026-09-23 20:28:21.072306692 +0000
@@ -1,11 +1,13 @@
 """
 Plantilla de bienvenida.
 
-VERSION VULNERABLE (snapshot pre-corrección, solo para generar el
-reporte SAST 'before'). Interpola la entrada del usuario sin escapar
-en el HTML de respuesta (CWE-79 / XSS).
+Corrección aplicada (hallazgo Semgrep 'flask-secure-templates: XSS' /
+CWE-79, ejercicio de la Sesión 05): la entrada del usuario se escapa
+con markupsafe.escape() antes de insertarla en el HTML de respuesta —
+nunca se interpola texto sin escapar dentro de una plantilla.
 """
 from flask import Blueprint, request
+from markupsafe import escape
 
 bp = Blueprint("view", __name__)
 
@@ -13,5 +15,7 @@
 @bp.get("/welcome")
 def welcome():
     name = request.args.get("name", "cliente")
-    # VULNERABLE — sin escape: permite inyectar <script>...</script>.
-    return f"<h1>Hola {name}</h1>", 200, {"Content-Type": "text/html"}
+    # SEGURO — escape() neutraliza <, >, ", ' y & antes de renderizar.
+    # Antes: f"<h1>Hola {name}</h1>" permitía inyectar <script>...</script>.
+    safe_name = escape(name)
+    return f"<h1>Hola {safe_name}</h1>", 200, {"Content-Type": "text/html"}
```


## `securebank_api/calc.py` — CWE-95 · eval() sobre entrada externa (calculadora de tasas)

```diff
--- security-reports/vulnerable-snapshot/securebank_api/calc.py	2026-09-23 20:30:44.078501600 +0000
+++ securebank_api/calc.py	2026-09-23 20:28:30.140307231 +0000
@@ -1,16 +1,55 @@
 """
 Calculadora de tasas de interés.
 
-VERSION VULNERABLE (snapshot pre-corrección, solo para generar el
-reporte SAST 'before'). Usa eval() directamente sobre la entrada del
-usuario (CWE-95 / ejecución de código arbitrario).
+Corrección aplicada (hallazgo Semgrep 'python.lang.security.audit.eval-detected'
+/ CWE-95, ejercicio de la Sesión 05): eval() sobre entrada del usuario
+permite ejecución arbitraria de código. Se reemplaza por un evaluador
+aritmético restringido, construido sobre el AST de Python, que solo
+admite números y los operadores +, -, *, /, ** y paréntesis.
 """
+import ast
+import operator
+
 from flask import Blueprint, request, jsonify, g
 from .auth import require_auth
 from .db import log_event
 
 bp = Blueprint("calc", __name__)
 
+_ALLOWED_BINOPS = {
+    ast.Add: operator.add,
+    ast.Sub: operator.sub,
+    ast.Mult: operator.mul,
+    ast.Div: operator.truediv,
+    ast.Pow: operator.pow,
+}
+_ALLOWED_UNARYOPS = {ast.USub: operator.neg, ast.UAdd: operator.pos}
+
+
+class UnsafeExpression(ValueError):
+    pass
+
+
+def _safe_eval(node):
+    if isinstance(node, ast.Expression):
+        return _safe_eval(node.body)
+    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
+        return node.value
+    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
+        return _ALLOWED_BINOPS[type(node.op)](
+            _safe_eval(node.left), _safe_eval(node.right)
+        )
+    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
+        return _ALLOWED_UNARYOPS[type(node.op)](_safe_eval(node.operand))
+    raise UnsafeExpression("expresión no permitida")
+
+
+def safe_arithmetic_eval(expression: str):
+    """Evalúa una expresión aritmética simple sin exponer eval()/exec()
+    a la entrada del usuario. Antes: eval(payload) permitía RCE."""
+    parsed = ast.parse(expression, mode="eval")
+    return _safe_eval(parsed)
+
 
 @bp.post("/calc/rate")
 @require_auth
@@ -18,6 +57,10 @@
     data = request.get_json(silent=True) or {}
     expression = data.get("expression", "")
 
-    # VULNERABLE — eval() sobre entrada externa (CWE-95 / RCE).
-    result = eval(expression)
+    try:
+        result = safe_arithmetic_eval(expression)
+    except (UnsafeExpression, SyntaxError, TypeError, ZeroDivisionError):
+        log_event("calc_rejected_expression", username=g.current_user, detail=expression)
+        return jsonify({"error": "expresión inválida"}), 400
+
     return jsonify({"result": result}), 200
```
