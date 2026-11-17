# Comparación de imágenes Docker — Sesión 10

Fecha: 17 de noviembre de 2026.
Proyecto: SecureBank API / SecurePipeline.

## Objetivo

Comparar una imagen de referencia v1 con una imagen endurecida v2,
aplicando mínimo privilegio y midiendo tamaño, paquetes y
vulnerabilidades mediante Docker y Trivy.

## Entorno y procedimiento

GitHub Actions construyó ambas imágenes desde el mismo código
y archivo requirements.txt, con --pull y --no-cache.

- v1: docker/Dockerfile.v1, etiqueta securebank:v1.
- v2: docker/Dockerfile.v2, etiqueta securebank:v2-secure.

Se registraron propiedades de las imágenes, historial de capas,
usuario efectivo y respuesta de /health.

Trivy analizó paquetes de sistema y librerías, incluyendo
vulnerabilidades sin corrección disponible e inventario de paquetes.

## Resultados medidos

| Medición | v1 | v2 |
|---|---:|---:|
| Tamaño informado por Docker, bytes | 383324553 | 50362093 |
| Tamaño decimal, MB | 383,32 | 50,36 |
| Paquetes detectados | 459 | 135 |
| Paquetes Debian | 429 | 105 |
| Paquetes Python | 30 | 30 |
| Hallazgos Critical | 20 | 2 |
| Hallazgos High | 692 | 101 |
| Hallazgos Medium | 2074 | 148 |
| Hallazgos Low | 1570 | 110 |
| Hallazgos Unknown | 92 | 5 |
| Total de registros de vulnerabilidad | 4448 | 366 |
| Usuario efectivo | root, UID 0 | appuser, UID 10001 |
| Puertos declarados | 8080/tcp y 22/tcp | 8080/tcp |
| Respuesta de /health | status=ok | status=ok |

Reducción del tamaño: 86,86%.

Los conteos de vulnerabilidades corresponden a registros del
reporte por paquete afectado, no a CVE únicos.

Los paquetes se cuentan por tipo, nombre y versión detectados.
El inventario refleja la cobertura de Trivy, no todos los archivos
presentes en la imagen.

## Cambios aplicados y justificación

1. Base completa sustituida por python:3.11-slim-bookworm:
   reduce los paquetes del sistema y la superficie de ataque.

2. USER 10001:10001:
   ejecuta la aplicación sin privilegios de root.

3. pip install --no-cache-dir:
   evita conservar la caché de instalación en la imagen final.

4. Solo EXPOSE 8080:
   elimina la declaración innecesaria del puerto 22.
   EXPOSE no publica puertos ni activa un servidor SSH.

5. Copia explícita de requirements.txt y securebank_api:
   limita el contenido incorporado a la imagen.

6. .dockerignore:
   excluye secretos, historial Git, entornos locales, evidencias
   y la copia antigua anidada del proyecto.
   Esta protección se aplica a ambas construcciones.

## Comprobación de funcionamiento

Ambas imágenes arrancaron con:

- Sistema de archivos raíz de solo lectura.
- /tmp temporal.
- Capabilities eliminadas.
- no-new-privileges habilitado.
- Clave JWT efímera proporcionada en ejecución.

Ambas respondieron en /health con:

    {"service":"securebank-api","status":"ok"}

Esto verifica el arranque y la ruta de salud, no todos los
endpoints ni todos los controles de seguridad de la API.

## Riesgos residuales

La imagen v2 mantiene 2 registros Critical y 101 High.

Los Critical reportados corresponden a:

- CVE-2025-7458, paquete libsqlite3-0.
- CVE-2023-45853, paquete zlib1g.

El reporte no proporciona FixedVersion para estos dos registros.
Debe revisarse su aplicabilidad y el estado del proveedor antes
de decidir una mitigación o excepción.

Trivy también identifica correcciones disponibles para dos
registros High de paquetes Python:

- jaraco.context: versión instalada 5.3.0; FixedVersion 6.1.0.
- wheel: versión instalada 0.45.1; FixedVersion 0.46.2.

Estos valores proceden del reporte y requieren evaluar la
actualización o eliminación del componente y volver a escanear.

Las imágenes base usan tags mutables. Para mayor trazabilidad,
debe evaluarse fijar sus digests y mantenerlos actualizados.

requirements.txt no constituye un lock completo de dependencias
transitivas con hashes.

## Evidencias

Artefactos de GitHub Actions:

- docker-security-v1
- docker-security-v2

Cada artefacto contiene:

- trivy.json
- image-inspect.json
- image-history.txt
- usuario.txt
- health.json
- build.log
- container.log
- fecha.txt

Los escaneos se ejecutaron el 17/11/2026 aproximadamente a las
05:30–05:31 UTC, equivalentes a las 02:30–02:31 en Chile.

## Conclusión

v2 reduce tamaño, paquetes y registros de vulnerabilidad,
manteniendo el arranque de la API y eliminando la ejecución root.

La mejora no elimina todos los riesgos. La comparación usa
exit-code=0 para producir los dos reportes; por tanto, un resultado
verde no representa aprobación de seguridad para desplegar.
