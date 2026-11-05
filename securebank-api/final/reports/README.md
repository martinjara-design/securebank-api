# reports/ · Sesión 6 (SCA y SBOM)

| Archivo | Qué es | Origen |
|---|---|---|
| `securebank-sbom.cdx.json` | SBOM CycloneDX 1.5 (10 componentes, directos y transitivos, con PURL) | Línea base generada con `cyclonedx-py` |
| `securebank-vulns-before.pip-audit.json` | Dependencias directas **antes** de actualizar: 24 avisos en Flask 3.0.3 y PyJWT 2.9.0 | `pip-audit --no-deps` |
| `securebank-vulns.pip-audit.json` | Después de actualizar Flask 3.1.3 y PyJWT 2.15.0: **0 vulnerabilidades** (con dependencias transitivas) | `pip-audit` |

Los archivos oficiales de entrega, `securebank-sbom.cdx.json`, `securebank-vulns.json` y `securebank-vulns.md` (con CVSS y semáforo), los **regenera el job `sca`** de `ci.yml` con Trivy y los publica como artefacto. Copiarlos aquí desde el artefacto de la primera ejecución verde antes de entregar.

`pip-audit` no entrega puntaje CVSS, por eso la clasificación por semáforo la hace el gate sobre el reporte de Trivy.
