# POL-REPO-001 · Política de Repositorios Seguros
Versión 1.1 · Proyecto SecureBank API · UBO Ingeniería Informática

## 1 – Alcance
Esta política es de cumplimiento obligatorio y aplica a todos los repositorios de código productivo, preproductivo (entornos de desarrollo, QA, staging) y de infraestructura como código de la organización.

## 2 – Roles y responsabilidades
- **Developer:** Alexander Ruiz-Tagle — desarrolla en ramas `feature/*` y abre PRs.
- **Reviewer:** Valentina León — revisa y aprueba PRs; no aprueba los propios.
- **Code owner:** Nelson Arévalo — dueño de archivos críticos (`CODEOWNERS`): pipelines, configuración de seguridad.
- **Release Manager:** Sebastián Chacón — único que crea releases y tags firmados.
- **Secret custodian:** Martín Jara — único que crea, rota o revoca secretos (ver `docs/SECRETS.md`).

## 3 – Reglas técnicas obligatorias
- **MFA obligatorio** en la plataforma para todo integrante y colaborador.
- **`main` protegida:** inmutable; prohibidos push directo, `--force` y borrado, también para administradores.
- **Pull request obligatorio** con ≥ 1 aprobación de un par; las aprobaciones previas se descartan ante nuevos commits; conversaciones resueltas antes del merge.
- **CODEOWNERS:** los archivos críticos exigen la aprobación de su dueño.
- **Commits firmados** (GPG/SSH) y asociados al perfil del autor.
- **Escaneo de secretos** (Gitleaks) bloqueante en cada push/PR, más hook `pre-commit` local.
- **Status checks obligatorios:** `secret-scan`, `build-test`, `sast`, `sca`; sin verde no hay merge.

### Cobertura de los 7 riesgos de la Sesión 2
| Riesgo | Control |
|---|---|
| R.01 Exposición de secretos | Gitleaks en pre-commit y CI; secretos solo en GitHub Secrets/Vault; `.gitignore` de `.env`, `*.pem`, `credentials.json` |
| R.02 Modificación maliciosa | Code review obligatorio + CODEOWNERS |
| R.03 Eliminación de ramas | Protección de `main`; force-push y borrado prohibidos |
| R.04 Commits no autorizados | Commits firmados + MFA |
| R.05 Colaboradores externos | Mínimo privilegio, roles temporales, revisión trimestral de accesos, offboarding inmediato |
| R.06 PRs hostiles | Workflows de forks requieren aprobación; los forks no reciben secretos; cambios en `.github/workflows/` pasan por CODEOWNERS |
| R.07 Repo como activo de negocio | Todo lo anterior + historial auditable; `main` siempre desplegable |

## 4 – Matriz "¿quién puede qué?"
| Pregunta | ¿Quién puede? | Restricciones y controles |
|---|---|---|
| **Q1 Merge** | Reviewers y Code owner | Checks en verde + ≥ 1 aprobación humana; sin auto-merge de dependencias |
| **Q2 Modificar pipelines** | Code owner y Secret custodian | Aprobación obligatoria y explícita del Code owner (CODEOWNERS sobre `.github/workflows/`); acciones pinneadas por versión |
| **Q3 Crear releases** | Solo el Release Manager | Sobre commits de `main` con tag firmado y SBOM adjunto |
| **Q4 Modificar secretos** | Solo el Secret custodian | Mínimo privilegio; cada acceso queda auditado |

## 5 – Excepciones y revisión
- **Emergencia (caída o vulnerabilidad crítica en producción):** el Code owner o el Release Manager pueden omitir la aprobación previa del PR. El pipeline de escaneos se ejecuta igualmente; la revisión del cambio ocurre dentro de 24 h y se registra en la bitácora.
- **Solicitud de excepción:** issue etiquetado `excepcion-politica` con motivo, alcance y fecha de expiración; la aprueba el Code owner.
- **Revisión de la política:** al cierre de cada sesión que incorpore un control nuevo y, como mínimo, cada trimestre. Los accesos se revisan cada trimestre.
# POL-REPO-001 §3/§4 - archivos criticos exigen aprobacion de un dueno.
*                          @nelsinho13 @martinjara-design
/.github/workflows/        @nelsinho13 @martinjara-design
/.gitleaks.toml            @nelsinho13 @martinjara-design
/.gitleaksignore           @nelsinho13 @martinjara-design
/.pre-commit-config.yaml   @nelsinho13 @martinjara-design
/docs/SECRETS.md           @nelsinho13 @martinjara-design
/scripts/cvss_gate.py      @nelsinho13 @martinjara-design
/requirements*.txt         @nelsinho13 @martinjara-design