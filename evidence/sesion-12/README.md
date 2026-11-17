# Evidencias de la sesión 12

Despliegue efímero de SecureBank API en Kind con Calico.

## Resultados

- Deployment desplegado correctamente.
- Kubesec: manifiesto válido y 14 puntos.
- Ocho comprobaciones de hardening aprobadas.
- Tres comprobaciones de acceso de red aprobadas.
- Cliente autorizado: HTTP 200.
- Cliente sin la etiqueta requerida: conexión agotada.

La prueba de red cubre entrada; no verifica el bloqueo de salida.

## Ejecución verificada

https://github.com/martinjara-design/securebank-api/actions/runs/44039205375

## Documentación

../../k8s/hardened/README.md
