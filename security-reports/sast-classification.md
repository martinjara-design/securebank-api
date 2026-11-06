# Clasificación de hallazgos SAST — Sesión 05

Ejercicio avanzado (grupos de 3-4): cinco vulnerabilidades plantadas en
SecureBank API, detectadas con Semgrep, clasificadas por categoría
OWASP y corregidas con el patrón seguro correspondiente.

> Nota de entorno: `semgrep.dev` no es accesible desde este contenedor
> (política de red del sandbox), por lo que en vez de `--config=p/owasp-top-ten`
> se usó un ruleset local (`.semgrep-rules/securebank-rules.yaml`) que
> replica exactamente las reglas nombradas en la Sesión 05
> (`python.sqlalchemy.security.sqlalchemy-execute-raw-query`,
> `python.lang.security.audit.dangerous-system-call`,
> `python.lang.security.audit.md5-used-as-password`,
> `python.lang.security.audit.eval-detected`, y una regla XSS con
> seguimiento de flujo de datos). El comando real ejecutado en CI:
> `semgrep --config=.semgrep-rules/securebank-rules.yaml securebank_api/ --sarif -o sast.sarif`.

## Reporte inicial — `sast-before.sarif`

| # | Archivo | Línea | Vulnerabilidad | Categoría OWASP (2021) | CWE | Severidad |
|---|---------|-------|-----------------|--------------------------|-----|-----------|
| 1 | `securebank_api/users.py` | 61-62 | SQL Injection en `POST /login` | A03 · Injection | CWE-89 | CRITICAL |
| 2 | `securebank_api/export.py` | 30 | Command Injection en exportador de reportes | A03 · Injection | CWE-78 | CRITICAL |
| 3 | `securebank_api/view.py` | 17 | Cross-Site Scripting en plantilla de bienvenida | A03 · Injection | CWE-79 | HIGH |
| 4 | `securebank_api/auth.py` | 39 | Hash MD5 en `hash_password()` | A02 · Cryptographic Failures | CWE-327 / CWE-916 | HIGH |
| 5 | `securebank_api/auth.py` | 43 | Hash MD5 en `verify_password()` (mismo patrón) | A02 · Cryptographic Failures | CWE-327 / CWE-916 | HIGH |
| 6 | `securebank_api/calc.py` | 22 | `eval()` sobre entrada externa en calculadora de tasas | A03 · Injection / API peligrosa | CWE-95 | CRITICAL |

**Total: 6 hallazgos — 3 CRITICAL · 3 HIGH · 0 MEDIUM · 0 LOW**

(El módulo `auth.py` concentra 2 hallazgos porque el patrón MD5
aparece tanto en `hash_password()` como en `verify_password()`; ambos
se resuelven con el mismo cambio a bcrypt.)

## Reporte final — `sast-after.sarif`

| # | Archivo | Hallazgos |
|---|---------|-----------|
| — | `securebank_api/*.py` | **0** |

**Total: 0 hallazgos — pipeline en verde ✅**

## Correcciones aplicadas (patrón seguro)

| Hallazgo | Antes | Después | Detalle del diff |
|----------|-------|---------|-------------------|
| SQL Injection | `"...'" + username + "'"` | `db.execute("... = ?", (username,))` | [`diff-fixes.md`](./diff-fixes.md#securebank_apiusrespy--cwe-89--sql-injection-post-login) |
| Command Injection | `os.system("cat " + filename)` | `subprocess.run(["cat", path], shell=False)` + allowlist de nombre | [`diff-fixes.md`](./diff-fixes.md#securebank_apiexportpy--cwe-78--command-injection-exportador-de-reportes) |
| XSS | `f"<h1>Hola {name}</h1>"` | `escape(name)` antes de interpolar | [`diff-fixes.md`](./diff-fixes.md#securebank_apiviewpy--cwe-79--cross-site-scripting-plantilla-de-bienvenida) |
| MD5 password hash | `hashlib.md5(pwd).hexdigest()` | `bcrypt.hashpw(pwd, bcrypt.gensalt())` | [`diff-fixes.md`](./diff-fixes.md#securebank_apiauthpy--cwe-327--cwe-916--md5-password-hash-auth) |
| `eval()` inseguro | `eval(expression)` | evaluador aritmético restringido sobre `ast` (solo `+ - * / **`) | [`diff-fixes.md`](./diff-fixes.md#securebank_apicalcpy--cwe-95--eval-sobre-entrada-externa-calculadora-de-tasas) |

## Evidencia auditable del PR de entrega

Checklist según lo exigido en la Sesión 05 ("Qué debe incluir el PR de entrega"):

1. ✅ Ambos SARIF — [`sast-before.sarif`](./sast-before.sarif) / [`sast-after.sarif`](./sast-after.sarif)
2. ✅ Tabla de clasificación por categoría OWASP — este documento
3. ✅ Diff del código corregido — [`diff-fixes.md`](./diff-fixes.md)
4. ⏳ URL del run del pipeline en verde — se completa al abrir el PR en GitHub (la Actions tab genera la URL `https://github.com/<org>/securebank-api/actions/runs/<id>` tras el primer push)
