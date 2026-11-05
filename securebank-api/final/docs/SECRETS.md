# Procedimiento de gestión y rotación de secretos · SecureBank API
Entregable Sesión 7 · Responsable del documento: Secret Custodian (ver `POL-REPO-001.md`)

## §1 Inventario de secretos
| Secreto | Tipo | Dónde vive hoy | Dónde vivía antes |
|---|---|---|---|
| `SECUREBANK_JWT_SECRET` | Clave de firma JWT (HS256) | Variable de entorno; GitHub Secrets en CI | Valor por defecto en `securebank_api/auth.py` — **eliminado**; la app no arranca sin él |
| `SECUREBANK_DEMO_ALICE_PW` / `_BOB_PW` | Contraseñas de usuarios demo | Variable de entorno (tests: `tests/conftest.py`, fixtures) | Literales en `securebank_api/db.py` — **eliminadas**; si faltan se genera una aleatoria |
| `GITHUB_TOKEN` | Token efímero del job | Generado por GitHub en cada ejecución | — (permisos mínimos por job) |
| Futuras credenciales de BD / cloud | Connection strings, API keys | Pendiente (hoy SQLite en memoria) | — |

Hallazgo inicial de esta sesión: el escaneo manual del código encontró los dos puntos de la tabla marcados como "eliminado". El historial completo de Git fue escaneado con Gitleaks y no contiene secretos reales.

## §2 Alternativas elegidas
| Caso | Alternativa | Justificación |
|---|---|---|
| Desarrollo local | Variables de entorno desde `.env` (ignorado por git; plantilla en `.env.example`) | Simple, nada en el repo |
| CI/CD | GitHub Secrets inyectados solo durante el job | Cifrado nativo, sin infraestructura extra |
| Producción (futuro) | HashiCorp Vault o KMS del proveedor + credenciales temporales vía OIDC | Rotación y auditoría centralizadas; sin credenciales estáticas |

Principio: preferir credenciales temporales a permanentes siempre que sea posible.

## §3 Configuración de Gitleaks
- **Archivo:** [`.gitleaks.toml`](../.gitleaks.toml): extiende las reglas por defecto, agrega la regla `securebank-env-literal` y una allowlist mínima (fixtures de test, reportes de CVE, esta documentación).
- **Pre-commit:** [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) → `pip install pre-commit && pre-commit install`.
- **CI:** job `secret-scan` en `.github/workflows/ci.yml`: primera etapa, escanea el historial completo, `exit != 0` falla el pipeline y bloquea SAST, SCA y Package.
- Cambios a la allowlist requieren PR y aprobación de Code owner + Secret custodian (CODEOWNERS).

## §4 Política de rotación
| Credencial | Frecuencia | Responsable |
|---|---|---|
| `SECUREBANK_JWT_SECRET` | Cada 90 días y ante cualquier sospecha | Secret custodian |
| Tokens personales / PAT | ≤ 30 días; preferir no usarlos | Cada dueño |
| Credenciales de BD / cloud (futuras) | Cada 90 días, o temporales vía OIDC | Secret custodian + DevOps |
| Contraseñas demo | Solo entornos de desarrollo; nunca reutilizar en otro sistema | Developer |

Rotar el JWT invalida todas las sesiones activas: se hace fuera de horario o con ventana comunicada. Cada rotación se registra en la bitácora (fecha, motivo, responsable; nunca el valor).

## §5 Procedimiento de respuesta ante una fuga
Borrar el commit **no** elimina el secreto: queda en el historial, forks, clones, logs y caches. Se asume comprometido.

| # | Paso | Plazo | Responsable | Acción |
|---|---|---|---|---|
| 1 | **Detectar** | Minuto 0 | Quien reciba la alerta | Confirmar tipo de secreto, commit y alcance (`gitleaks detect -v --redact`) |
| 2 | **Revocar** | ≤ 15 min | Secret custodian | Invalidar en el proveedor / GitHub Secrets |
| 3 | **Rotar** | Sin downtime | Secret custodian + DevOps | Generar uno nuevo, cargarlo en GitHub Secrets, redesplegar |
| 4 | **Limpiar historial** | Coordinado | Code owner | `git filter-repo` o BFG; avisar para re-clonar; invalidar caches y forks |
| 5 | **Notificar** | Post-mortem | Code owner | Informar al equipo y docente, auditar usos del secreto, registrar en la bitácora |

Prioridad: revocar antes que limpiar.

## §6 Evidencia de un ciclo real
Prueba controlada en un repositorio temporal con un secreto de prueba (formato inválido a propósito) en un commit: Gitleaks detectó 3 hallazgos (`github-pat`, `generic-api-key`, `securebank-env-literal`) y terminó con **exit code 1**. Salida redactada en [`evidence/gitleaks-bloqueo.txt`](../evidence/gitleaks-bloqueo.txt). En el repositorio limpio, el mismo comando termina con exit 0.

**Pendiente (requiere GitHub):** adjuntar aquí el enlace a la ejecución de Actions donde `secret-scan` falla en una rama de prueba (`test/secret-leak`) y captura de pantalla. Eliminar la rama después de la captura.
