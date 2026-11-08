# SecureBank API · SecurePipeline

[![CI](https://github.com/martinjara-design/securebank-api/actions/workflows/ci.yml/badge.svg)](https://github.com/martinjara-design/securebank-api/actions/workflows/ci.yml)

Proyecto transversal del curso **Sistemas Automatizados DevSecOps** (UBO · Ingeniería Informática). API REST bancaria endurecida sesión a sesión: repositorio seguro → threat model → CI/CD → SAST → SCA/SBOM → secretos.

## Pipeline v1.2

```
Secret Scan (Gitleaks) → Build & Unit Tests → SAST (Semgrep) → SCA + SBOM (Trivy + gate CVSS) → [Aprobación] → Package
```

## Entregables por sesión

| Sesión | Entregable | Dónde | Estado |
|---|---|---|---|
| 1 · Intro DevSecOps | Diagrama del ciclo (PDF 1 página) | [`docs/sesion-01/`](docs/sesion-01/README.md) | ✅ |
| 2 · Git y repos seguros | Política `POL-REPO-001` + `CODEOWNERS` | [`POL-REPO-001.md`](POL-REPO-001.md), [`.github/CODEOWNERS`](.github/CODEOWNERS) | ✅ falta configurar protección de `main` y handles reales |
| 3 · Threat Modeling | Threat model (12 amenazas), DFD, security stories | [`docs/threat-model.md`](docs/threat-model.md), [`docs/security-stories.md`](docs/security-stories.md) | ✅ |
| 4 · CI/CD | Pipeline CI + análisis del pipeline inseguro | [`.github/workflows/ci.yml`](.github/workflows/ci.yml), [`docs/sesion-04-pipeline-inseguro.md`](docs/sesion-04-pipeline-inseguro.md) | ✅ falta confirmar ejecución en verde |
| 5 · SAST | Reportes SARIF antes/después, clasificación OWASP, diff | [`security-reports/`](security-reports/) | ✅ 6 → 0 hallazgos |
| 6 · SCA y SBOM | SBOM CycloneDX, reporte de vulnerabilidades, policy gate | [`reports/`](reports/README.md), [`scripts/cvss_gate.py`](scripts/cvss_gate.py) | 🟡 base local lista; oficiales los genera el CI |
| 7 · Secretos | `docs/SECRETS.md`, `.gitleaks.toml`, pre-commit, job `secret-scan` | [`docs/SECRETS.md`](docs/SECRETS.md) | 🟡 falta enlace a ejecución real de bloqueo |

Decisiones técnicas: [`docs/BITACORA.md`](docs/BITACORA.md).

## Estructura

```
securebank-api/
├── .github/{workflows/ci.yml, CODEOWNERS}
├── .semgrep-rules/        .gitleaks.toml     .pre-commit-config.yaml   .env.example
├── securebank_api/        # API Flask
├── tests/                 # 15 pruebas (conftest.py aporta variables de entorno de test)
├── docs/                  # threat model, stories, SECRETS, bitácora, sesión 1 y 4
├── security-reports/      # SAST (sesión 5)
├── reports/  evidence/    # SCA/SBOM (sesión 6) y evidencia de Gitleaks (sesión 7)
├── scripts/cvss_gate.py
├── POL-REPO-001.md
└── requirements{,-dev,-sast}.txt
```

## Ejecutar localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export SECUREBANK_JWT_SECRET=$(python -c "import secrets;print(secrets.token_hex(32))")  # o copiar .env.example a .env
pytest tests/ -v --cov=securebank_api
python -m securebank_api.app
```
SAST: `pip install -r requirements-sast.txt && semgrep --config=.semgrep-rules/securebank-rules.yaml --error securebank_api/` · Secretos: `gitleaks detect -c .gitleaks.toml --redact -v`.

## Pendiente antes de entregar (necesita GitHub)
1. Branch protection en `main` según `POL-REPO-001.md` (status checks: `secret-scan`, `build-test`, `sast`, `sca`) y Environment `security-approval` con revisores.
2. Reemplazar `@usuario-*` en `CODEOWNERS` por los handles reales.
3. Primera ejecución de Actions en verde; copiar SBOM/vulns oficiales a `reports/`.
4. Rama `test/secret-leak` para la evidencia del §6 de `docs/SECRETS.md`.

prueba
