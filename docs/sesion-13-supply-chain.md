# Sesión 13: seguridad de la cadena de suministro

## Objetivo

Publicar una imagen identificada por digest, generar su SBOM
CycloneDX y verificar su firma e identidad antes de permitir
continuar el workflow.

## Implementación

La imagen se construye mediante docker/Dockerfile.v2 y se publica
en GitHub Container Registry (GHCR).

Syft genera el inventario SBOM en formato CycloneDX. Cosign firma
el digest de la imagen y una attestation que contiene el SBOM.

La firma utiliza la identidad OIDC de GitHub Actions, sin almacenar
una clave privada permanente en el repositorio.

La verificación exige:
- El digest exacto de la imagen.
- La identidad exacta del workflow firmante.
- El emisor https://token.actions.githubusercontent.com.
- Una attestation firmada de tipo CycloneDX.

Cosign también verifica el certificado y la evidencia de inclusión
en el registro de transparencia.

## Evidencias y resultados

### Control positivo

Imagen verificada:

ghcr.io/martinjara-design/securebank-api@sha256:7e1736dcb45a2e33b29c80fd2c23403f0f21e8c8685d2e904533ed6c45c5a837

Identidad autorizada para esta prueba:

https://github.com/martinjara-design/securebank-api/.github/workflows/supply-chain.yml@refs/heads/feature/sesion-13-supply-chain

Resultado: firma y attestation CycloneDX verificadas.
El contenido del SBOM descargado coincide con el incluido
en la attestation.

Ejecución:
https://github.com/martinjara-design/securebank-api/actions/runs/44041510986

### Control negativo

Se construyó una imagen derivada con metadatos diferentes,
sin firmarla. Su digest fue:

ghcr.io/martinjara-design/securebank-api@sha256:c1d936214501401f9cf199fc2e9e1f03e99e52dc4ea3a63965bdac64f255f6d1

La imagen firmada pasó primero el control positivo.
Después, la imagen sin firma fue rechazada con:

Error: no signatures found

El gate terminó con error y el job de continuación quedó omitido.
El fallo de esta ejecución es intencional.

Ejecución:
https://github.com/martinjara-design/securebank-api/actions/runs/44042691069

## Análisis del caso

Una etiqueta de imagen puede apuntar a contenidos distintos.
Usar el digest fija el contenido que se verifica. La firma permite
comprobar qué identidad autorizada lo firmó; la attestation vincula
un inventario SBOM firmado con ese mismo digest.

La prueba negativa demuestra que copiar o modificar una imagen
firmada no transfiere su firma al nuevo digest. Sin una firma
aceptada, el workflow impide continuar.

## Alcance y limitaciones

La prueba demuestra verificación obligatoria dentro de los workflows
de esta sesión. No instala un controlador de admisión en Kubernetes
ni conecta todavía esta verificación con su despliegue.

El control negativo confía expresamente en la identidad de la rama
de laboratorio. Un consumidor de producción debe exigir la identidad
autorizada de main y sus controles de revisión.

Una firma válida acredita procedencia e integridad respecto del
firmante; no garantiza ausencia de vulnerabilidades ni que el
contenido del SBOM sea completo. Los controles SAST, SCA, DAST
y de imágenes siguen siendo necesarios.
