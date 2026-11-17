# Evidencias de la sesión 8

Se ejecutó ZAP Baseline contra SecureBank API en un contenedor
efímero de GitHub Actions.

## Resultados

- Inicial: 1 alerta media, 5 bajas y 1 informativa.
- Final: 0 alertas altas, medias o bajas y 1 informativa de caché.
- Las cinco comprobaciones BOLA pasaron.
- Los accesos a cuentas ajenas fueron rechazados con HTTP 403.

Estos resultados se limitan a las rutas y casos examinados.

## Ejecución verificada

https://github.com/martinjara-design/securebank-api/actions/runs/44013110939

## Archivos

- report.json: resultados finales de ZAP.
- report.html: reporte visual final.
- bola-results.txt: resultados de autorización.
- fecha.txt: fecha registrada por el workflow.
- imagen-zap.txt: digest de la imagen ZAP.
- version-zap.txt: versión utilizada.

Informe: ../../docs/reporte-dast-securebank.pdf
