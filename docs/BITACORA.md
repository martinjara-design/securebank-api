# Bitácora de decisiones · SecureBank API
Resumen de las decisiones técnicas por sesión. Complementa el documento "Análisis y Toma de Decisiones: Proyecto SecureBank API".

| Sesión | Decisión | Motivo |
|---|---|---|
| 2 | `main` protegida con un ruleset: PR obligatorio, 1 aprobación, revisión de Code Owners, resolución de conversaciones, 4 status checks obligatorios, sin force push ni borrado y sin lista de bypass (`POL-REPO-001.md`) | Cubrir los 7 riesgos del repositorio. Prueba: un push directo a `main` fue rechazado (GH013, "Changes must be made through a pull request") |
| 2 | Commits firmados (GPG/SSH): exigidos por la política, pendientes de activar en el ruleset | Requiere que cada integrante registre su clave en GitHub |
| 2 | `CODEOWNERS` con `@nelsinho13` y `@martinjara-design` en cada ruta crítica | Cada PR lo aprueba la otra persona: nadie aprueba su propio cambio |
| 3 | 12 amenazas STRIDE, 3 trust boundaries, 12 security stories | Mínimo exigido: 10 amenazas y 5 stories |
| 4 | GitHub Actions; permisos mínimos; acciones por versión fija | Corregir R1–R4 del pipeline inseguro |
| 4 | Gitleaks se descarga validando su checksum con el nombre original del archivo | La primera versión del paso fallaba al verificar el hash |
| 5 | Semgrep como SAST; 6 hallazgos → 0 | Liviano, políglota, fácil en CI |
| 6 | Trivy (CVSS + SBOM CycloneDX 1.5); semáforo: ≥ 9.0 bloquea · 7.0–8.9 aprobación humana (Environment `security-approval`) · < 7.0 se registra | Reglas claras y automáticas; evita bypass por umbrales demasiado estrictos |
| 6 | `trivy-action` fijada en v0.36.0 por hash de commit | Los tags de la acción cambiaron de formato (`0.28.0` → `v0.28.0`); el hash es inmutable y evita que un tag movido altere el pipeline |
| 6 | Dependencias actualizadas: Flask 3.0.3 → 3.1.3, PyJWT 2.9.0 → 2.15.0 | `pip-audit` reportó CVEs en ambas (reporte "antes" en `reports/`); tras el cambio 0 hallazgos y 15/15 tests |
| 6 | Prueba del gate con las versiones viejas: 17 CVEs, 2 bloqueantes (CVSS 9.1), 8 con aprobación requerida; el pipeline falló | Demuestra que el semáforo bloquea en un PR real (`evidence/sca-gate-bloqueo.md`) |
| 6 | Environment `security-approval` con 2 revisores requeridos | Un CVE con CVSS de 7.0 a 8.9 pausa el pipeline hasta la aprobación humana |
| 6 | `requirements-dev.txt` sin `pip-audit` ni `semgrep`; Semgrep en `requirements-sast.txt` | Ambos exigen versiones incompatibles de `tomli`: el `pip install` del CI fallaba |
| 7 | Gitleaks como primera etapa (`secret-scan`), historial completo, exit ≠ 0 bloquea | Fail fast: no gastar recursos en código ya comprometido |
| 7 | Prueba del bloqueo: un PR con un token falso hizo fallar `secret-scan` y omitió los demás jobs | Evidencia en `docs/SECRETS.md` §6 y `evidence/secret-scan-bloqueo.png` |
| 7 | Excepción en `.gitleaksignore` para el commit `c64a19e` (`ci.yml`, línea 58) | Falso positivo en un comentario; no hay ningún secreto |
| 7 | Secreto JWT y contraseñas demo fuera del código; la app falla si `SECUREBANK_JWT_SECRET` falta o tiene menos de 32 caracteres | Principio "ningún secreto en el código"; fail closed |
| 7 | Rotación JWT cada 90 días; respuesta Detectar → Revocar → Rotar → Limpiar → Notificar | Ver `docs/SECRETS.md` |
| 7 | Se corrigió un status check requerido con nombre antiguo (`Build · Unit Tests`) por `Build & Unit Tests` | El nombre del check debe coincidir con el job actual de `ci.yml`; si no, el PR queda esperando un check que nunca llega |
| 7 | Un commit de prueba (push directo antes de activar el ruleset) dejó una línea en el README y un bloque pegado en `POL-REPO-001.md`; se revirtió por PR | Se detectó antes de entregar; desde entonces `main` solo admite cambios por PR |