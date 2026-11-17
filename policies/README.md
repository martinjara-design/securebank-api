# Security Policy v1.0

Política de SecureBank API implementada con OPA y Rego.
Fecha: 17 de noviembre de 2026.

## Umbrales y justificación

| Control | Condición | Justificación |
|---|---|---|
| Critical | 0 | Evitar empaquetar software con hallazgos críticos. |
| High | Máximo 2 en entorno interno | Limitar la deuda de seguridad del laboratorio. |
| High con exposición a Internet | 0 | Aplicar mayor exigencia a servicios públicos. |
| Medium | Máximo 20 | Establecer un límite explícito de deuda revisable por el equipo. |
| Secretos | 0 | Evitar publicar credenciales detectadas. |
| Cobertura | Al menos 80% | Cumplir el mínimo de la sesión 9. |
| High de DAST | 0 | Bloquear hallazgos de riesgo alto observados en ejecución. |
| Métricas | Completas y válidas | No interpretar reportes ausentes como ausencia de hallazgos. |

Los límites son decisiones del proyecto, no garantías de ausencia
de vulnerabilidades. Los controles anteriores de Gitleaks,
Semgrep y CVSS siguen vigentes y pueden ser más restrictivos.

## Entradas y clasificación

El script scripts/gate_input.py procesa los reportes descargados
de una misma ejecución:

- Gitleaks SARIF: número de secretos detectados.
- Semgrep SARIF: error se clasifica como High y warning como Medium.
- Trivy JSON: severidades Critical, High y Medium.
- ZAP JSON: High y Medium por tipo de alerta, no por instancia.
- Coverage XML: porcentaje de líneas ejecutadas por las pruebas.

Critical, High y Medium suman los conteos de las herramientas.
No se realiza deduplicación entre herramientas.

internet_exposed=false describe el entorno local y efímero
del laboratorio. Para un servicio público debe establecerse true.

## Decisión

OPA permite continuar únicamente cuando no existen motivos
de bloqueo. Package depende del éxito de Security Gate (OPA).

La evaluación obligatoria usa:

    opa eval --fail \
      -d policies/security-policy-v1.rego \
      -i input.json \
      'data.securepipeline.gate.allow = true'

Se usa un solo signo = para que una decisión false no produzca
un resultado válido y el comando termine con error.

## Pruebas y evidencias

- 14 pruebas automáticas aprobadas.
- Caso real permitido: allow=true y Package ejecutado.
- Caso sintético rechazado: secrets=1, gate fallido y
  Package (demostracion) omitido.
- El contador sintético no representa una credencial real.
- La rama feature/test-security-gate-block no se fusiona a main.

Ejecución real con el comando corregido:
https://github.com/martinjara-design/securebank-api/actions/runs/44020914843

Demostración de bloqueo:
https://github.com/martinjara-design/securebank-api/actions/runs/44019965414

## Mantenimiento

Todo cambio de umbral requiere justificación, actualización
de pruebas y revisión mediante Pull Request.
