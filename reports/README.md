# reports/ · Sesión 6 (SCA y SBOM)

## Reportes oficiales (generados por el pipeline)

Generados por el job `sca` de `.github/workflows/ci.yml` en la ejecución #8 (merge del PR #1 a `main`), con Trivy y el policy gate `scripts/cvss_gate.py`.

| Archivo | Qué es |
|---|---|
| `securebank-sbom.cdx.json` | SBOM en formato CycloneDX 1.5 generado por Trivy a partir de `requirements.txt` |
| `securebank-vulns.json` | Reporte de vulnerabilidades de Trivy, con puntajes CVSS |
| `securebank-vulns.md` | Tabla de decisión por CVE según la política CVSS |

**Resultado en `main`:** 0 CVEs, 0 bloqueantes, 0 que requieran aprobación.

## Política CVSS (semáforo)

| CVSS | Decisión |
|---|---|
| >= 9.0 | Bloqueado: el pipeline falla |
| 7.0 a 8.9 | Requiere aprobación de un revisor (Environment `security-approval`) |
| < 7.0 | Se registra y se sigue |

## Evidencia del antes y el después

| Archivo | Qué es | Origen |
|---|---|---|
| `securebank-vulns-before.pip-audit.json` | Dependencias directas antes de actualizar: 24 avisos en Flask 3.0.3 y PyJWT 2.9.0 | `pip-audit --no-deps` |
| `securebank-vulns.pip-audit.json` | Después de actualizar a Flask 3.1.3 y PyJWT 2.15.0: 0 vulnerabilidades, incluyendo dependencias transitivas | `pip-audit` |
| `../evidence/sca-gate-bloqueo.md` | Prueba en el pipeline con las versiones vulnerables: 17 CVEs, 2 bloqueantes (CVSS 9.1), 8 con aprobación requerida | Rama `test/sca-vulnerable` |

`pip-audit` no entrega puntaje CVSS, por eso la clasificación por semáforo la hace el gate sobre el reporte de Trivy.

## Decisión de remediación

Flask 3.0.3 → 3.1.3 y PyJWT 2.9.0 → 2.15.0 (ver `docs/BITACORA.md`). Los 15 tests pasan con las versiones nuevas.