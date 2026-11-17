# Subir las correcciones juntas

Base revisada: main ac2718bd6e8dfb458b7560c978c0742b538befa6.

1. Descomprimir `securebank-correcciones-finales.zip`.
2. En GitHub crear desde main la rama **feature/cierre-entrega**.
3. En la raiz del repositorio, Add file → Upload files. Arrastrar el CONTENIDO del ZIP: las carpetas .github, docs, evidence, k8s, policies, scripts, terraform, tests y los archivos .gitignore y .gitattributes. No arrastrar una carpeta contenedora que cambie las rutas.
4. GitHub debe mostrar archivos como `.github/workflows/supply-chain.yml` y `k8s/hardened/deployment.hardened.yaml`. Subir tambien los PDF: se reemplazan sus versiones anteriores. Todos los archivos tienen menos de 25 MB.
5. Commit: **fix: cerrar entregables de IaC Kubernetes y supply chain**.
6. La rama feature/cierre-entrega ejecuta Supply Chain, incluyendo controles de calidad, build, firma, SBOM, cluster Kind, Kyverno, despliegue y rechazo de imagen sin firma. Ejecuta tambien la auditoria IaC. Esperar sus resultados.
7. Crear PR a main, solicitar revision de martinjara-design y fusionar cuando los controles esten aprobados. La ejecucion en main debe volver a verificar y desplegar con la identidad de main.
8. Descargar el artefacto supply-chain y conservar rollout, health.json, policy.yaml, admission-test/result.json, admission-negative.log y controles positivos. Conservar tambien el nuevo gate IaC y las validaciones Terraform.

## Cambios incluidos

- Manifiesto final Kubernetes con digest real; plantilla separada para el renderer.
- Gate de calidad antes de publicar/desplegar; firma y SBOM verificados inmediatamente antes de apply.
- Kyverno 1.19.2 con identidad exacta, registro permitido, digest y attestation obligatorios. Prueba de admision negativa real con controles positivos antes/despues.
- Terraform: replicacion de backups/logs, proveedor OIDC consultado en lugar de duplicado, backend remoto y workflow manual scan → gate → plan → apply. El plan se cifra antes de guardarse como artefacto en un repositorio publico.
- Gate de IaC: HIGH/CRITICAL bloquean aunque exista excepcion; reporte contextual explicito y diez pruebas.
- PDF DAST actualizado; informe IaC de 3 paginas actualizado; analisis supply chain de 1 pagina.

## Comprobado localmente

- Checkov 3.4.5: 47 recursos, 141 passed, 1 failed, 0 skipped; score 99,30%.
- Gate acepta el fallo SSE-S3 documentado y bloquea severidades altas.
- 10 pruebas del gate aprobadas.
- Workflows verificados con actionlint 1.7.7.
- Scripts Bash verificados con bash -n; Python compilado.
- Politicas verificadas contra el CRD oficial de Kyverno 3.9.2.
- Helm genera correctamente la instalacion del chart.
- PDF: DAST 3 paginas, IaC 3 paginas, analisis 1 pagina.

## Pendiente de plataforma

Terraform validate necesita ejecutarse en Actions: el entorno local no permite el socket Unix del proveedor. Docker/Kind/Kyverno no se pudieron ejecutar aqui: no hay Docker. No se ha desplegado en AWS ni se ha configurado una cuenta. Consultar `docs/aws-lab-configuracion.md`; no ejecutar apply hasta revisar costos, rol, estado, destinos y aprobaciones.

El unico fallo IaC se mantiene visible: CKV_AWS_145 en el destino de logs SSE-S3. Su severidad MEDIUM es contextual del equipo, no oficial del scanner; requiere aceptacion de esa justificacion por el docente. La excepcion vence el 17/12/2026.
