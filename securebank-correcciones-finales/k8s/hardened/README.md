# Kubernetes endurecido — Sesión 12

## Objetivo

Desplegar SecureBank API en un clúster efímero de Kind,
aplicando mínimo privilegio y verificando los controles.

## Archivos

- namespace.yaml: Namespace con política restricted y ServiceAccount.
- deployment.hardened.yaml: plantilla del Deployment.
- service.yaml: Service interno ClusterIP.
- networkpolicy.yaml: restricciones de entrada y salida.

## Justificación de controles

| Control | Justificación |
|---|---|
| runAsNonRoot y UID/GID 10001 | Ejecutar sin privilegios de root. |
| readOnlyRootFilesystem | Impedir modificaciones del sistema raíz. |
| emptyDir para /tmp | Permitir archivos temporales sin habilitar escritura en la raíz. |
| capabilities.drop ALL | Eliminar capabilities Linux innecesarias. |
| allowPrivilegeEscalation=false | Impedir que el proceso obtenga nuevos privilegios. |
| seccompProfile RuntimeDefault | Aplicar el filtro seccomp del runtime. |
| Requests y limits | Reservar y limitar CPU y memoria. |
| automountServiceAccountToken=false | Evitar el montaje automático del token de Kubernetes. |
| secretKeyRef | Obtener la clave JWT desde un Secret generado en ejecución. |
| Imagen por digest | Identificar la imagen desplegada mediante su digest. |
| Probes de salud | Comprobar arranque, disponibilidad y funcionamiento. |
| Service ClusterIP | Mantener el servicio dentro de la red del clúster. |
| NetworkPolicy | Restringir el tráfico de los Pods de la API. |

## Construcción y despliegue

El workflow kubernetes-security.yml:

1. Instala Kind y kubectl.
2. Crea el clúster y un registro local.
3. Instala Calico para aplicar NetworkPolicy.
4. Construye docker/Dockerfile.v2 y publica en el registro local.
5. Obtiene el digest y genera el Deployment.
6. Analiza el manifiesto con Kubesec.
7. Crea un Secret JWT temporal.
8. Valida los manifiestos contra el servidor y los aplica.
9. Comprueba rollout, salud, hardening y acceso de red.
10. Guarda evidencias y elimina el laboratorio.

La plantilla contiene REPLACE_DIGEST. El script render_k8s.py
lo sustituye antes de aplicar el Deployment.

## Resultados verificados

Ejecución:
https://github.com/martinjara-design/securebank-api/actions/runs/44039205375

- Deployment desplegado correctamente.
- /health respondió status=ok.
- Kubesec: valid=true y score=14 puntos.
- Ocho comprobaciones de hardening aprobadas.
- Tres comprobaciones de NetworkPolicy de entrada aprobadas.

### Hardening comprobado dentro del contenedor

- UID 10001 y GID 10001.
- Token de ServiceAccount ausente.
- Capabilities efectivas en cero.
- NoNewPrivs activado.
- Filtro seccomp activo.
- Sistema de archivos raíz de solo lectura.
- /tmp permite escritura temporal.

### Red comprobada

- Cliente con access=securebank-api: HTTP 200.
- Cliente sin esa etiqueta: conexión agotada.
- Repetición desde el cliente autorizado: HTTP 200.

La prueba usa la IP del Service para evitar confundir
un problema de DNS con un bloqueo de red.

## Interpretación de Kubesec

Los 14 puntos son una puntuación de la herramienta,
no un porcentaje de seguridad.

La recomendación sobre la anotación antigua de seccomp
no invalida la configuración actual: se utiliza
securityContext.seccompProfile y se comprobó el filtro
en ejecución.

El perfil AppArmor específico no está configurado.

## Alcance y límites

Se usa una réplica porque SQLite vive en memoria.
No se ha implementado persistencia compartida.

La política declara bloqueo de salida, pero las pruebas
realizadas verifican únicamente el tráfico de entrada.

El Secret se genera durante la ejecución y no se incluye
su contenido en las evidencias. No se ha validado cifrado
de Secrets en etcd.

El registro y el clúster son efímeros. El manifiesto generado
se refiere al registro del laboratorio; para reproducirlo
hay que recrear el entorno y construir la imagen.

Las pruebas de hardening no acreditan ausencia de CVE
en la imagen. Firma y verificación de procedencia quedan
pendientes para la sesión 13.

## Corrección de cierre

`deployment.hardened.yaml` contiene ahora un digest GHCR real de la prueba firmada de sesión 13, sin `REPLACE_DIGEST`. El marcador se conserva exclusivamente en `deployment.template.yaml`, usado por `scripts/render_k8s.py` para generar cada despliegue.

Antes de aplicar manualmente, crear Namespace/ServiceAccount con `namespace.yaml`, el Secret `securebank-secrets` (clave `jwt-secret`) y, si GHCR es privado, el imagePullSecret `ghcr-read`. No versionar los valores de esos secretos. Después se puede aplicar `deployment.hardened.yaml`, Service y NetworkPolicy. El digest de referencia se firmó en la rama de sesión 13; una política que confía exclusivamente en main requiere el digest producido por el workflow en main, como hace automáticamente el nuevo flujo de despliegue.

El workflow `supply-chain.yml` instala Kyverno y despliega exactamente el digest que acaba de verificar. La nueva evidencia de admission y rollout debe provenir de una ejecución real antes de dar por cerrada la corrección.
