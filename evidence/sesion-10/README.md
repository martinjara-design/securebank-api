# Evidencias de la sesión 10

Comparación de SecureBank API con Docker y Trivy.

- v1/: archivos del artefacto docker-security-v1.
- v2/: archivos del artefacto docker-security-v2.
- Informe: ../../docker/REPORT.md

Ambas imágenes respondieron correctamente en /health.

v2 reduce tamaño y paquetes, pero conserva hallazgos
Critical y High. El workflow comparativo no acredita
que la imagen esté aprobada para desplegar.
