# SecureBank API · SecurePipeline

[![CI](https://github.com/<ORG>/securebank-api/actions/workflows/ci.yml/badge.svg)](https://github.com/<ORG>/securebank-api/actions/workflows/ci.yml)

> Reemplaza `<ORG>` por tu organización/usuario de GitHub al subir el
> repo — el badge se activa solo tras el primer push a `main`.

Proyecto transversal del curso **Sistemas Automatizados DevSecOps**
(UBO · Ingeniería Informática). SecureBank API es una API REST
bancaria construida de forma incremental, sesión a sesión, aplicando
prácticas DevSecOps de extremo a extremo: threat modeling → pipeline
CI/CD → SAST → (SCA/DAST en próximas sesiones).

## Estado del pipeline — v1.1

```
Checkout → Setup → Install deps → Build → Unit Tests → SAST (Semgrep) → Package
```

| Sesión | Entregable | Estado |
|---|---|---|
| 03 · Threat Modeling | `docs/threat-model.md` + `docs/security-stories.md` | ✅ 12 amenazas, 12 security stories |
| 04 · CI/CD Pipeline | `.github/workflows/ci.yml` (etapas checkout·install·build·test·artifact) | ✅ Pipeline v1.0 funcional |
| 05 · SAST | Etapa `sast` en el pipeline + `security-reports/` | ✅ 6 hallazgos → 0 hallazgos |

## Estructura del repositorio

```
securebank-api/
├── .github/workflows/ci.yml       # Pipeline v1.1 (Build → Test → SAST → Package)
├── .semgrep-rules/                # Ruleset SAST local (réplica de p/owasp-top-ten)
├── securebank_api/                # Código de la API (Flask)
│   ├── app.py                     # App factory + cabeceras de seguridad
│   ├── auth.py                    # JWT + bcrypt + rate limiting
│   ├── users.py                   # /login /register (consultas parametrizadas)
│   ├── accounts.py                # /accounts/{id} (fix IDOR)
│   ├── transfer.py                # /transfer (fix BOLA)
│   ├── export.py                  # /export (fix Command Injection)
│   ├── view.py                    # /welcome (fix XSS)
│   ├── calc.py                    # /calc/rate (fix eval inseguro)
│   └── db.py                      # Capa de datos (SQLite en memoria)
├── tests/test_basic.py            # 15 pruebas unitarias (etapa Unit Tests)
├── docs/
│   ├── threat-model.md            # Entregable Sesión 03 — DFD + STRIDE (12 amenazas)
│   └── security-stories.md        # Backlog de security stories (12)
├── security-reports/
│   ├── sast-before.sarif          # Reporte SAST inicial — 6 hallazgos
│   ├── sast-after.sarif           # Reporte SAST final — 0 hallazgos
│   ├── sast-classification.md     # Clasificación OWASP de los hallazgos
│   ├── diff-fixes.md              # Diff línea a línea de cada corrección
│   └── vulnerable-snapshot/       # Código pre-corrección (solo para trazabilidad SAST)
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Cómo correr el proyecto localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Tests
pytest tests/ -v --cov=securebank_api

# SAST (mismo comando que corre en CI)
semgrep --config=.semgrep-rules/securebank-rules.yaml --sarif -o sast.sarif securebank_api/

# Levantar la API
python -m securebank_api.app
```

## Modelo de amenazas y controles

Ver [`docs/threat-model.md`](docs/threat-model.md) para el DFD completo
(3 trust boundaries), el análisis STRIDE con 12 amenazas y su control
propuesto, y el caso de análisis BOLA en `POST /transfer`.

## Seguridad en el pipeline mismo

El workflow (`ci.yml`) aplica el principio de mínimo privilegio
(`permissions: contents: read`), usa únicamente GitHub Actions
oficiales pinneadas por versión, fija las dependencias vía
`requirements-dev.txt`, y no contiene ningún secreto en texto plano
— ver los comentarios R1-R4 al inicio del archivo, que documentan las
correcciones aplicadas sobre el ejercicio de pipeline inseguro de la
Sesión 04.

## Reportes SAST (Sesión 05)

Ver [`security-reports/sast-classification.md`](security-reports/sast-classification.md)
para la tabla de clasificación OWASP completa. Resumen:

| | CRITICAL | HIGH | Total |
|---|---|---|---|
| Antes (`sast-before.sarif`) | 3 | 3 | **6** |
| Después (`sast-after.sarif`) | 0 | 0 | **0** |

## Próxima sesión

Sesión 06 — SCA (Software Composition Analysis): escaneo del árbol de
dependencias, identificación de CVEs y emisión de un SBOM firmado.
Etapa nueva en el pipeline: `Build → Unit Tests → SAST → SCA → Package`.
