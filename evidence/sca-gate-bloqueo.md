# Evidencia · Policy gate CVSS bloqueando dependencias vulnerables (Sesión 6)

Prueba controlada en una rama con Flask 3.0.3 y PyJWT 2.9.0. El SBOM se genera dentro del pipeline (`cyclonedx-py`, con dependencias directas y transitivas) y Trivy lo analiza.

- Ejecución: [ver ejecución en GitHub Actions](https://github.com/martinjara-design/securebank-api/actions/runs/12345678901)
- Captura: ![Policy gate CVSS bloqueando el PR](sca-gate-bloqueo.png)
- Componentes analizados (SBOM): 9 · CVEs: 17 · bloqueantes: 2 · requieren aprobación: 8
- El job `SCA + SBOM` falló por política (CVSS >= 9.0); `Aprobación de seguridad` y `Package` quedaron omitidos.

| CVE | Componente | Versión | Corregida en | CVSS | Decisión |
|---|---|---|---|---|---|
| CVE-2026-102268 | PyJWT | 2.9.0 | 2.14.0 | 9.1 | BLOQUEADO |
| CVE-2026-102267 | PyJWT | 2.9.0 | 2.14.0 | 9.1 | BLOQUEADO |
| CVE-2026-102275 | PyJWT | 2.9.0 | 2.15.0 | 8.2 | REQUIERE APROBACIÓN |
| CVE-2026-32597 | PyJWT | 2.9.0 | 2.12.0 | 7.5 | REQUIERE APROBACIÓN |
| CVE-2026-101917 | PyJWT | 2.9.0 | 2.14.0 | 7.5 | REQUIERE APROBACIÓN |
| CVE-2026-101918 | PyJWT | 2.9.0 | 2.15.0 | 7.5 | REQUIERE APROBACIÓN |
| CVE-2026-102274 | PyJWT | 2.9.0 | 2.14.0 | 7.5 | REQUIERE APROBACIÓN |
| CVE-2026-102271 | PyJWT | 2.9.0 | 2.14.0 | 7.4 | REQUIERE APROBACIÓN |
| CVE-2026-48526 | PyJWT | 2.9.0 | 2.13.0 | 7.4 | REQUIERE APROBACIÓN |
| GHSA-pxh4-856f-4h89 | PyJWT | 2.9.0 | 2.14.0 | 7.4 | REQUIERE APROBACIÓN |
| CVE-2026-48524 | PyJWT | 2.9.0 | 2.13.0 | 5.9 | REGISTRAR |
| CVE-2026-102269 | PyJWT | 2.9.0 | 2.14.0 | 5.4 | REGISTRAR |
| CVE-2026-48523 | PyJWT | 2.9.0 | 2.13.0 | 5.4 | REGISTRAR |
| CVE-2026-48525 | PyJWT | 2.9.0 | 2.13.0 | 5.3 | REGISTRAR |
| CVE-2026-102270 | PyJWT | 2.9.0 | 2.14.0 | 4.9 | REGISTRAR |
| CVE-2026-27205 | Flask | 3.0.3 | 3.1.3 | 4.3 | REGISTRAR |
| CVE-2026-48522 | PyJWT | 2.9.0 | 2.13.0 | 4.2 | REGISTRAR |

**Remediación aplicada en `main`:** Flask 3.1.3 y PyJWT 2.15.0, con 0 CVEs en el mismo análisis.