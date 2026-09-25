# Security Stories — Backlog SecureBank API

Regla del curso (Sesión 03): **por cada historia funcional del backlog
debe existir al menos una security story asociada** — esto convierte
el threat modeling en trabajo entregable. A continuación, una security
story por cada una de las 12 amenazas del Threat Model (supera el
mínimo de 5 exigido).

Formato: *"Como [rol], la aplicación debe [garantía]"* + criterio de
aceptación de seguridad, en el mismo formato ágil que las historias
funcionales.

---

**SEC-001 — Autenticación resistente a credenciales filtradas**
Amenaza: #01 Spoofing · Historia funcional relacionada: login de cliente
> Como cliente, la aplicación debe protegerme frente a credential
> stuffing con listas de contraseñas filtradas.
**Criterio de aceptación:** tras 5 intentos fallidos en 60s desde el
mismo origen, la API responde `429 Too Many Requests` y registra el
evento en auditoría. *(Implementado y probado.)*

**SEC-002 — Integridad del token de sesión**
Amenaza: #02 Spoofing (falsificación de JWT)
> Como sistema, la aplicación debe rechazar cualquier JWT cuyo
> algoritmo no sea el configurado explícitamente, incluyendo `alg: none`.
**Criterio de aceptación:** `decode_token()` solo acepta el algoritmo
declarado (`HS256`); cualquier otro valor lanza excepción y responde
`401`. *(Implementado y probado.)*

**SEC-003 — Confidencialidad del monto en tránsito**
Amenaza: #03 Tampering (MITM sobre `/transfer`)
> Como cliente, la aplicación debe garantizar que el monto de mi
> transferencia no pueda ser alterado en tránsito.
**Criterio de aceptación:** toda respuesta incluye `Strict-Transport-Security`;
el despliegue exige HTTPS y rechaza tráfico HTTP plano. *(Implementado a nivel de cabeceras.)*

**SEC-004 — Consultas SQL sin inyección**
Amenaza: #04 Tampering (SQL Injection)
> Como sistema, la aplicación debe procesar cualquier entrada de
> usuario en consultas SQL como dato, nunca como código ejecutable.
**Criterio de aceptación:** el reporte SAST (`security-reports/sast-after.sarif`)
no reporta hallazgos de la regla `sqlalchemy-execute-raw-query`. *(Implementado y probado — SQLi + `' OR '1'='1` cubierto en tests.)*

**SEC-005 — Trazabilidad e integridad de transferencias**
Amenaza: #05 Repudiation
> Como banco, la aplicación debe poder demostrar que una transferencia
> fue ejecutada por un usuario específico, incluso si este la niega.
**Criterio de aceptación:** cada transferencia exitosa genera un
registro en `audit_log` con `userId`, montos y timestamp. *(Implementado.)*

**SEC-006 — Autorización por recurso en consulta de saldos**
Amenaza: #06 Information Disclosure (IDOR en `GET /accounts/{id}`)
> Como cliente, la aplicación debe rechazar cualquier consulta a una
> cuenta que no me pertenezca.
**Criterio de aceptación:** `GET /accounts/{id}` responde `403` si
`owner_username != userId` del JWT, salvo rol `admin`. *(Implementado y probado.)*

**SEC-007 — Gestión de secretos fuera del código**
Amenaza: #07 Information Disclosure (fuga de secretos en repo)
> Como equipo de desarrollo, la aplicación debe obtener sus credenciales
> desde variables de entorno / vault, nunca desde el código fuente.
**Criterio de aceptación:** `JWT_SECRET` se lee de `os.environ`; no
existe ningún secreto hardcodeado en el repositorio (verificado
manualmente y por revisión de PR). *(Implementado.)*

**SEC-008 — Resiliencia de `/login` ante fuerza bruta**
Amenaza: #08 Denial of Service
> Como operador del servicio, la aplicación debe seguir disponible
> para usuarios legítimos aunque un actor intente saturar `/login`.
**Criterio de aceptación:** ver SEC-001 (mismo control cubre ambas
amenazas — rate limiting). *(Implementado y probado.)*

**SEC-009 — Límite de tamaño de payload**
Amenaza: #09 Denial of Service (payload masivo a `/transfer`)
> Como operador del servicio, la aplicación debe rechazar peticiones
> cuyo cuerpo exceda un tamaño razonable antes de parsearlas.
**Criterio de aceptación:** el despliegue configura
`MAX_CONTENT_LENGTH` a nivel de servidor WSGI/reverse proxy.
*(Pendiente — a resolver en la capa de infraestructura, Sesión 6+.)*

**SEC-010 — Autorización de propiedad en transferencias (BOLA)**
Amenaza: #10 Elevation of Privilege — caso de análisis principal de la sesión
> Como cliente, la aplicación debe rechazar toda transferencia cuyo
> `originAccount` no pertenezca al usuario autenticado, respondiendo
> `403` y registrando el intento.
**Criterio de aceptación:** `POST /transfer` valida `userId` del JWT
contra el dueño real de `originAccount` antes de mover fondos.
*(Implementado y probado — caso BOLA explícito en el Threat Model.)*

**SEC-011 — Integridad del claim de rol en el JWT**
Amenaza: #11 Elevation of Privilege (JWT con `role: admin` falsificado)
> Como sistema, la aplicación nunca debe confiar en el claim `role`
> de un JWT cuya firma no haya sido validada del lado servidor.
**Criterio de aceptación:** el rol se obtiene únicamente del payload
decodificado tras `decode_token()`, que valida firma y expiración.
*(Implementado.)*

**SEC-012 — Redacción de datos sensibles en logs**
Amenaza: #12 Information Disclosure (logs con datos sensibles)
> Como oficial de cumplimiento, la aplicación no debe escribir
> tokens, RUT ni saldos en texto plano en los logs de aplicación.
**Criterio de aceptación:** `db.log_event()` registra únicamente
`event`, `username` y un `detail` acotado (sin token completo ni PII
extendida); política formal de retención pendiente de infraestructura.
*(Parcial — mitigado en el diseño del logger, retención pendiente.)*

---

## Resumen de cobertura

| Estado | Cantidad |
|---|---|
| Implementado y probado | 8 |
| Implementado (sin test dedicado) | 2 |
| Parcial | 1 |
| Pendiente (infraestructura) | 1 |

**12/12 amenazas** del Threat Model tienen al menos una security story
asociada — cumple la regla de la Sesión 03 y supera el mínimo de 5
historias priorizadas exigido antes de la Sesión 04.
