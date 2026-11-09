# reports/ · Sesión 6 (SCA y SBOM)

## Reportes oficiales (generados por el pipeline)

Generados por el job `sca` de `.github/workflows/ci.yml` en la ejecución de `main` [42693723835](https://github.com/martinjara-design/securebank-api/actions/runs/42693723835). El SBOM se produce dentro del pipeline con `cyclonedx-py`, Trivy analiza ese SBOM y el policy gate `scripts/cvss_gate.py` aplica la política CVSS.

| Archivo | Qué es |
|---|---|
| `securebank-sbom.cdx.json` | SBOM CycloneDX 1.5 generado por el job `sca` con `cyclonedx-py`: dependencias directas y transitivas, con PURL y licencia |
| `securebank-vulns.json` | Salida JSON de Trivy sobre el SBOM, con puntajes CVSS |
| `securebank-vulns.md` | Reporte legible: CVE, componente, CVSS, decisión según el semáforo y justificación |
| `securebank-vulns.html` | El mismo reporte en HTML |

**Resultado en `main`:** 9 componentes analizados, 0 CVEs, 0 bloqueantes, 0 que requieran aprobación.

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
| `../evidence/sca-gate-bloqueo.md` | Prueba en el pipeline con las versiones vulnerables: 9 componentes, 17 CVEs, 2 bloqueantes (CVSS 9.1) y 8 con aprobación requerida; el job falló por política | PR de prueba con Flask 3.0.3 y PyJWT 2.9.0 |

`pip-audit` no entrega puntaje CVSS, por eso la clasificación por semáforo la hace el gate sobre el reporte de Trivy.

## Decisión de remediación

Flask 3.0.3 → 3.1.3 y PyJWT 2.9.0 → 2.15.0 (ver `docs/BITACORA.md`). Los 15 tests pasan con las versiones nuevas.