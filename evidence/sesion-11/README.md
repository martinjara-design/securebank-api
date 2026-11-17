# Evidencias de la sesión 11

Laboratorio de análisis estático de infraestructura AWS con Terraform
y Checkov. No se ejecutaron terraform plan ni terraform apply.

## Resultados

| Medición | Before | After |
|---|---:|---:|
| Recursos analizados | 20 | 44 |
| Controles aprobados | 41 | 132 |
| Controles fallidos | 60 | 3 |
| Controles omitidos | 0 | 0 |
| Security Score | 40,59% | 97,78% |
| Decisión del gate | Rechazar | Permitir con excepciones |

After incorpora recursos auxiliares, por lo que cambió el conjunto
de controles evaluados. Los tres fallos finales permanecen en el score.

## Archivos

- before/: contenido del artefacto iac-before.
- after/: contenido del artefacto iac-after.
- gate/: contenido del artefacto iac-gate.
- pipeline-iac.png: captura de las auditorías, validaciones y gate.

Política: ../../policies/iac-policy.json
Informe: ../../docs/reporte-iac-securebank.pdf

## Ejecución verificada

https://github.com/martinjara-design/securebank-api/actions/runs/44032754453
