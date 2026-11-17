"""Preflight AWS de destinos existentes; no crea ni modifica recursos."""
import json
import os
import subprocess


def aws(*args):
    return json.loads(subprocess.check_output(['aws', *args, '--output', 'json'], text=True))


targets = json.loads(os.environ['TF_VAR_replication_destinations'])
if set(targets) != {'backups', 'logs'}:
    raise SystemExit('Configura TF_REPLICATION_DESTINATIONS con backups y logs.')
for name, target in targets.items():
    bucket = target['bucket_arn'].removeprefix('arn:aws:s3:::')
    if bucket == target['bucket_arn'] or '/' in bucket:
        raise SystemExit('ARN de bucket invalido')
    versioning = aws('s3api', 'get-bucket-versioning', '--bucket', bucket)
    if versioning.get('Status') != 'Enabled':
        raise SystemExit(f'{name}: destino sin versionado activo')
    public = aws('s3api', 'get-public-access-block', '--bucket', bucket)['PublicAccessBlockConfiguration']
    if not all(public.get(k) is True for k in ('BlockPublicAcls','IgnorePublicAcls','BlockPublicPolicy','RestrictPublicBuckets')):
        raise SystemExit(f'{name}: falta bloqueo de acceso publico')
    rules = aws('s3api', 'get-bucket-encryption', '--bucket', bucket)['ServerSideEncryptionConfiguration']['Rules']
    if not any(r.get('ApplyServerSideEncryptionByDefault',{}).get('SSEAlgorithm') == 'aws:kms' for r in rules):
        raise SystemExit(f'{name}: falta cifrado KMS')
    key = target['kms_key_arn']
    region = key.split(':')[3]
    metadata = aws('kms', 'describe-key', '--key-id', key, '--region', region)['KeyMetadata']
    if metadata['KeyState'] != 'Enabled':
        raise SystemExit(f'{name}: clave KMS no habilitada')
    print(f'PASS: destino {name} versionado, privado y cifrado; clave habilitada.')
