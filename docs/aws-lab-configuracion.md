# Sesión 11: terminar plan/apply en AWS

El workflow `iac-deploy.yml` implementa **scan → gate → plan → apply**. Es manual, solo admite main y no aplica por defecto. No se ha ejecutado en AWS desde esta corrección.

## Requisitos externos

Se necesita una cuenta AWS de laboratorio autorizada. El módulo crea dos EC2, RDS Multi-AZ, EBS, KMS, S3 y otros servicios con costo. RDS tiene protección de eliminación y snapshot final: no usar una cuenta personal sin revisar presupuesto y limpieza.

1. Crear environments `aws-lab` y `aws-apply`; en ambos permitir exclusivamente main. Configurar un revisor obligatorio en `aws-apply` antes del primer uso.
2. Proveer un rol de despliegue existente con OIDC GitHub. Sus sujetos de confianza deben ser exactamente `repo:martinjara-design/securebank-api:environment:aws-lab` y `repo:martinjara-design/securebank-api:environment:aws-apply`, con aud `sts.amazonaws.com`. Este es un rol de bootstrap, no el rol vacío `securebank-lab-ci-role` definido en el módulo.
3. Preparar un backend S3 independiente, privado, cifrado y versionado, con permisos para estado y bloqueo nativo `.tflock`. No usar los buckets administrados por este mismo módulo como backend.
4. Preparar dos buckets destino de replicación independientes, versionados, privados y cifrados con KMS. El rol S3 del módulo debe poder escribir en ellos y usar sus claves; si son de otra cuenta, requieren políticas del bucket y KMS correspondientes. Revisar región, retención y destino antes de aplicar.
5. Crear el secreto GitHub `TF_PLAN_PASSPHRASE` con al menos 32 caracteres aleatorios, disponible para ambos environments. El repositorio es publico: el workflow cifra el plan y su texto antes de subir el artefacto; no publicar la frase de cifrado.
6. Configurar en Settings → Secrets and variables → Actions → Variables (o en ambos environments):

| Variable | Valor |
|---|---|
| `AWS_ROLE_ARN` | ARN del rol OIDC autorizado para plan y creación del laboratorio |
| `TF_STATE_BUCKET` | Nombre del bucket de estado existente |
| `TF_REPLICATION_DESTINATIONS` | JSON con `backups` y `logs`, cada uno con `bucket_arn` y `kms_key_arn` |

Los ARN no son contraseñas. No compartir access keys ni claves privadas; el workflow usa OIDC.

## Ejecución

1. Ejecutar **Terraform AWS - plan y apply controlados**, rama main, con `apply=false`. El gate cloud no usa las antiguas excepciones de replicación. También comprueba destinos existentes antes del plan.
2. Descargar el artefacto y descifrar `terraform-review.tar.gpg` localmente con GPG y la frase configurada; extraer y revisar `plan.txt`, permisos y costos. El plan y su texto se publican cifrados, caducan al dia siguiente y no deben subirse en claro al repositorio ni al aula.
3. Ejecutar de nuevo con `apply=true`; se generará un nuevo plan de esa ejecución. Revisarlo en la pausa del environment `aws-apply` y aprobar solamente ese plan. Apply verifica su checksum y aplica el archivo guardado sin recalcularlo.
4. Conservar capturas y un resumen redactado de plan/apply, sin estado ni secretos. Acordar la limpieza de recursos con el titular de la cuenta.

## Gate y excepción restante

La medición local corregida tiene 47 recursos, 141 controles aprobados, 1 fallido y 0 omitidos (99,30%). Falta confirmar esta medición y Terraform validate en GitHub Actions.

El único fallo restante es `CKV_AWS_145` sobre `aws_s3_bucket.logs`: el destino de server access logging requiere SSE-S3 por compatibilidad AWS. Se conserva cifrado AES256, acceso privado y HTTPS. La clasificación MEDIUM es contextual del equipo, no una severidad oficial de Checkov; caduca el 17/12/2026. Una severidad HIGH/CRITICAL que suministre el scanner siempre bloquea, incluso si hay excepción.

Referencia AWS: https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html

No afirmar cumplimiento del criterio cloud del profesor hasta obtener plan/apply reales y la aceptación de la excepción contextual. Si no existe cuenta AWS del curso, pedir al docente que confirme si acepta el alcance estático; no sustituir apply por un echo.
