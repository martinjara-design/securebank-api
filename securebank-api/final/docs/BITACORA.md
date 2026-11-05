# Bitácora de decisiones · SecureBank API
Resumen de las decisiones técnicas por sesión. Complementa el documento "Análisis y Toma de Decisiones: Proyecto SecureBank API".

| Sesión | Decisión | Motivo |
|---|---|---|
| 2 | `main` protegida, PR con ≥ 1 aprobación, commits firmados, CODEOWNERS (`POL-REPO-001.md`) | Cubrir los 7 riesgos del repositorio |
| 3 | 12 amenazas STRIDE, 3 trust boundaries, 12 security stories | Mínimo exigido: 10 amenazas y 5 stories |
| 4 | GitHub Actions; permisos mínimos; acciones por versión fija | Corregir R1–R4 del pipeline inseguro |
| 5 | Semgrep como SAST; 6 hallazgos → 0 | Liviano, políglota, fácil en CI |
| 6 | Trivy (CVSS + SBOM CycloneDX 1.5); semáforo: ≥ 9.0 bloquea · 7.0–8.9 aprobación humana (Environment `security-approval`) · < 7.0 se registra | Reglas claras y automáticas; evita bypass por umbrales demasiado estrictos |
| 6 | Dependencias actualizadas: Flask 3.0.3 → 3.1.3, PyJWT 2.9.0 → 2.15.0 | `pip-audit` reportó CVEs en ambas (reporte "antes" en `reports/`); tras el cambio 0 hallazgos y 15/15 tests |
| 6 | `requirements-dev.txt` sin `pip-audit` ni `semgrep`; Semgrep en `requirements-sast.txt` | Ambos exigen versiones incompatibles de `tomli`: el `pip install` del CI fallaba |
| 7 | Gitleaks como primera etapa (`secret-scan`), historial completo, exit ≠ 0 bloquea | Fail fast: no gastar recursos en código ya comprometido |
| 7 | Secreto JWT y contraseñas demo fuera del código; la app falla si falta `SECUREBANK_JWT_SECRET` | Principio "ningún secreto en el código"; fail closed |
| 7 | Rotación JWT cada 90 días; respuesta Detectar → Revocar → Rotar → Limpiar → Notificar | Ver `docs/SECRETS.md` |
