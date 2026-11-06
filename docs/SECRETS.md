# Procedimiento de gestión y rotación de secretos — SecureBank API

> Entregable Sesión 07 · Sistemas Automatizados DevSecOps (UBO)
> Versión 1.0 · Equipo: Martín Jara, Sebastián Chacón, Nelson Arévalo, Alexander Ruiz-Tagle, Valentina León
> Roles según `POL`: Secret custodian = Martín Jara · Code owner = Nelson Arévalo · Release Manager = Sebastián Chacón · Developer = Alexander Ruiz-Tagle · Reviewer = Valentina León

**Regla número uno:** ningún secreto vive en el código, en el historial de Git, en logs ni en imágenes. Todo secreto se lee del entorno o de un gestor de secretos.

## §1 · Inventario de secretos

| Secreto | Tipo | Dónde se usa | Dónde se almacena hoy | Riesgo |
|---|---|---|---|---|
| `SECUREBANK_JWT_SECRET` | Clave de firma HS256 | `securebank_api/auth.py` | Variable de entorno (local: `.env` excluido por `.gitignore`) | Alto: permite falsificar tokens |
| Contraseñas de usuarios demo (`alice`, `bob`) | Password | `securebank_api/db.py` (`_seed`) | Variables de entorno `SECUREBANK_DEMO_*_PASSWORD`; si faltan se generan al azar. Base SQLite **en memoria** | Bajo: sin literales en el código |
| `GITHUB_TOKEN` | Token efímero de Actions | `.github/workflows/ci.yml` | Lo emite GitHub por ejecución; permisos `contents: read` | Bajo: expira al terminar el job |
| Cuentas GitHub de los integrantes | Credenciales + MFA | Acceso al repo | GitHub (MFA obligatorio según `POL`) | Alto si se pierde el 2º factor |
| Llaves GPG de firma de commits | Private key | Firma de commits (`POL`) | Máquina de cada integrante | Alto: nunca deben salir del equipo |
| Secretos de DAST (Sesión 8) | Por definir | — | — | Se agregará a este inventario en la Sesión 8 |

**Corrección aplicada en la Sesión 07 (usuarios demo):** las contraseñas de `alice` y `bob` ya no están en el código; se leen del entorno (`.env.example`) y las pruebas generan valores efímeros en `tests/conftest.py`.

**Corrección aplicada en la Sesión 07:** `auth.py` tenía un valor por defecto literal (`"dev-only-change-me"`) para el secreto JWT. Eso es un secreto hardcodeado de facto, porque un despliegue que olvide la variable firmaría tokens con una clave pública. Ahora la app **no arranca** si `SECUREBANK_JWT_SECRET` falta o tiene menos de 32 caracteres (prueba `test_jwt_secret_obligatorio`).

## §2 · Alternativas elegidas

| Caso | Alternativa | Justificación |
|---|---|---|
| Desarrollo local | Variables de entorno vía `.env` (excluido del repo) + `.env.example` como plantilla | Es la opción más simple y suficiente para una API de curso; el secreto nunca entra al control de versiones |
| Pruebas unitarias | Secreto **efímero** generado por ejecución (`tests/conftest.py`) | Sigue el principio de credenciales temporales: no existe nada que filtrar ni rotar |
| CI/CD | `GITHUB_TOKEN` efímero + GitHub Actions Secrets para cualquier valor persistente futuro | Cifrado nativo; se inyecta solo durante el job |
| Producción (objetivo) | Secret manager (HashiCorp Vault o KMS del proveedor) con rotación y auditoría de lecturas; OIDC para que el pipeline no guarde credenciales cloud | Es la opción más robusta; no se implementa aún porque el proyecto no tiene despliegue real |

Principio rector: **credenciales temporales antes que permanentes** siempre que sea posible.

Generar un secreto JWT válido:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## §3 · Configuración de Gitleaks

Tres capas, de la más cercana al desarrollador a la más lejana:

1. **Pre-commit hook local** — `.pre-commit-config.yaml` (Gitleaks `v8.18.4`). Instalar con `pip install pre-commit && pre-commit install`. Bloquea el commit antes de que exista en el historial.
2. **Reglas del proyecto** — `.gitleaks.toml`: extiende las reglas por defecto y agrega `securebank-env-secret-literal-default`, que detecta `os.environ.get("..._SECRET", "<literal>")`. Esa regla existe porque las reglas por defecto no marcaron el fallback de `auth.py`.
3. **Job en CI** — `.github/workflows/ci.yml`, job `secret-scan`: escanea el historial completo (`fetch-depth: 0`), usa un binario fijado por versión y checksum SHA-256, y falla con `--exit-code 1`. Los demás jobs declaran `needs: secret-scan`, así que SAST, SCA y Package no se ejecutan si hay un secreto.

Excepción justificada en `allowlist`: `security-reports/vulnerable-snapshot/` contiene código vulnerable a propósito (trazabilidad del SAST de la Sesión 05). Toda excepción nueva debe justificarse en el pull request y aprobarla el Code owner.

Los pipelines que fallan por un secreto **no se resuelven agregando una excepción**: se trata como incidente (§5).

## §4 · Política de rotación

| Credencial | Frecuencia | Responsable | Disparadores de rotación inmediata |
|---|---|---|---|
| `SECUREBANK_JWT_SECRET` | Cada 90 días | Secret custodian (Martín Jara) | Sospecha de fuga; salida de un integrante con acceso; alerta de Gitleaks |
| Tokens personales de acceso (PAT) | Máximo 90 días de vida | Cada integrante | Fuga, cambio de equipo o dispositivo perdido |
| Llaves GPG de firma | Cada 12 meses | Cada integrante | Equipo comprometido o perdido |
| `GITHUB_TOKEN` | Automática (por ejecución) | GitHub | — |

**Rotar el secreto JWT (sin downtime relevante):** los tokens duran 15 minutos (`JWT_EXPIRY_SECONDS`), por lo que cambiar la clave solo obliga a iniciar sesión de nuevo.

1. Generar el nuevo valor con el comando del §2.
2. Actualizarlo donde corresponda (`.env` local; secret del entorno de despliegue).
3. Reiniciar el servicio.
4. Verificar: un token firmado con la clave anterior debe responder `401`.
5. Registrar fecha, motivo y responsable en la bitácora del equipo.

## §5 · Procedimiento de respuesta ante una fuga

Aplica cuando Gitleaks (pre-commit, CI) o un tercero detecta un secreto. Se asume compromiso desde el minuto 0: **borrar el commit no resuelve nada**, porque el secreto persiste en el historial, forks, clones, logs y cachés.

| # | Paso | Plazo | Responsable | Acciones | Evidencia |
|---|---|---|---|---|---|
| 1 | **Detectar** | Minuto 0 | Reviewer (Valentina León) | Confirmar tipo de secreto, qué protege y desde qué commit está expuesto (`gitleaks detect -v`) | Reporte `gitleaks-report.sarif` |
| 2 | **Revocar** | ≤ 15 min | Secret custodian (Martín Jara) | Invalidar la credencial en el proveedor correspondiente. Es la acción prioritaria | Captura/registro de la revocación |
| 3 | **Rotar** | Sin downtime | Release Manager (Sebastián Chacón) | Generar una credencial nueva (§4), publicarla por el canal seguro y redesplegar | Registro de redespliegue |
| 4 | **Limpiar historial** | Coordinado | Code owner (Nelson Arévalo) | Reescribir con `git filter-repo`, forzar push **solo con autorización explícita** (`POL` prohíbe `--force` en `main`: se requiere excepción documentada), pedir a colaboradores re-clonar, invalidar cachés | Hash del historial limpio |
| 5 | **Notificar y aprender** | Post-mortem | Developer (Alexander Ruiz-Tagle) | Avisar a las partes interesadas, auditar usos del secreto durante la exposición y documentar la causa raíz | Acta del incidente |

Regla de orden: **revocar antes que limpiar.** La limpieza del historial es secundaria porque el secreto ya pudo ser copiado.

## §6 · Evidencia de un ciclo real

Ejecución local de Gitleaks `v8.18.4` con la configuración de este repo (`.gitleaks.toml`). Los valores se muestran redactados; el commit de prueba usa credenciales **falsas**.

**A. Estado corregido del repositorio — pasa:**

```
INF 1 commits scanned.
INF scan completed in 19.4ms
INF no leaks found
exit=0
```

**B. Commit con un secreto de prueba (`app_config.py`) — bloquea:**

```
RuleID:  aws-access-token                         File: app_config.py  Line: 1
RuleID:  generic-api-key                          File: app_config.py  Line: 2
RuleID:  securebank-env-secret-literal-default    File: app_config.py  Line: 3
WRN leaks found: 3
exit=1
```

Con `exit=1` el job `secret-scan` queda en estado *failed* y los jobs `build-test`, `sast`, `sca` y `package` no se ejecutan.

> **Pendiente de adjuntar por el equipo:** captura de la pestaña *Actions* de GitHub mostrando el job `secret-scan` en rojo sobre un pull request con un secreto de prueba. Lo anterior se ejecutó localmente; la captura en GitHub debe hacerse una vez que `ci.yml` esté en el repo.
