#!/usr/bin/env bash
set -euo pipefail
SIGNED_IMAGE="${1:?Falta imagen}"
IDENTITY="${2:?Falta identidad}"
OUT=reports/supply-chain/admission-test
mkdir -p "$OUT"
DEMO_TAG="ghcr.io/${GITHUB_REPOSITORY,,}:unsigned-admission-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
docker build -f docker/Dockerfile.unsigned-demo \
  --build-arg "BASE_IMAGE=$SIGNED_IMAGE" \
  --label "org.securebank.demo.run=${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}" \
  -t "$DEMO_TAG" .
docker push "$DEMO_TAG"
UNSIGNED_IMAGE=$(docker image inspect --format '{{index .RepoDigests 0}}' "$DEMO_TAG")
[[ "$UNSIGNED_IMAGE" =~ ^ghcr\.io/[a-z0-9._/-]+@sha256:[a-f0-9]{64}$ ]]
[[ "$UNSIGNED_IMAGE" != "$SIGNED_IMAGE" ]]
printf '%s\n' "$UNSIGNED_IMAGE" > "$OUT/unsigned-image.txt"
# Confirmar que la imagen realmente existe y es accesible antes de probar el rechazo.
docker manifest inspect "$UNSIGNED_IMAGE" > "$OUT/unsigned-manifest.json"

if bash scripts/verify_supply_chain.sh "$UNSIGNED_IMAGE" "$IDENTITY" "$OUT/cosign" \
  > "$OUT/cosign-negative.log" 2>&1; then
  echo 'ERROR: Cosign acepto una imagen de prueba sin firma.' >&2
  exit 1
fi
# Un error de red o autenticacion no demuestra ausencia de firma.
if ! grep -qi 'no signatures found' "$OUT/cosign-negative.log"; then
  cat "$OUT/cosign-negative.log"
  exit 1
fi
python3 - "$UNSIGNED_IMAGE" <<'PY'
import json,sys
from pathlib import Path
obj=json.loads(Path('reports/supply-chain/deployment/deployment-live.json').read_text())
pod={'apiVersion':'v1','kind':'Pod','metadata':{'name':'unsigned-admission-test','namespace':'securebank'},
     'spec':obj['spec']['template']['spec']}
pod['spec']['containers'][0]['image']=sys.argv[1]
Path('reports/supply-chain/admission-test/unsigned-pod.json').write_text(json.dumps(pod))
pod['metadata']['name']='signed-admission-control'
pod['spec']['containers'][0]['image']=obj['spec']['template']['spec']['containers'][0]['image']
Path('reports/supply-chain/admission-test/signed-pod.json').write_text(json.dumps(pod))
PY
# Control positivo del webhook con los mismos campos del Pod negativo.
kubectl create --dry-run=server -f "$OUT/signed-pod.json" \
  > "$OUT/admission-positive.log" 2>&1
if kubectl create -f "$OUT/unsigned-pod.json" > "$OUT/admission-negative.log" 2>&1; then
  kubectl -n securebank delete pod unsigned-admission-test --wait=false
  echo 'ERROR: el admission controller acepto la imagen sin firma.' >&2
  exit 1
fi
python3 - <<'PY'
import json
from pathlib import Path
p=Path('reports/supply-chain/admission-test')
text=(p/'admission-negative.log').read_text().lower()
if 'securebank-signed-images' not in text or not any(s in text for s in ('signature', 'attestation', 'verification')):
    raise SystemExit('Rechazo por causa inesperada: '+text)
(p/'result.json').write_text(json.dumps({'signed_admission_allowed':True,
    'unsigned_cosign_rejected':True,'unsigned_admission_rejected':True},indent=2))
print(text)
PY
[[ -z "$(kubectl -n securebank get pod unsigned-admission-test --ignore-not-found -o name)" ]]
# Repetir control positivo para descartar indisponibilidad del webhook.
kubectl create --dry-run=server -f "$OUT/signed-pod.json" \
  > "$OUT/admission-positive-after.log" 2>&1
echo 'PASS: imagen firmada desplegada; imagen sin firma rechazada por Cosign y Kyverno.'
