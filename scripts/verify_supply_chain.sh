#!/usr/bin/env bash
set -euo pipefail

# Verifica la firma y la attestation del SBOM para un digest concreto.
# Uso:
# bash scripts/verify_supply_chain.sh IMAGEN IDENTIDAD [CARPETA_RESULTADOS]

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Uso: $0 IMAGEN_CON_DIGEST IDENTIDAD_ESPERADA [CARPETA_RESULTADOS]" >&2
  exit 1
fi

IMAGE_REFERENCE="$1"
EXPECTED_IDENTITY="$2"
OUTPUT_DIRECTORY="${3:-reports/supply-chain/verification}"
OIDC_ISSUER="https://token.actions.githubusercontent.com"

if [[ ! "$IMAGE_REFERENCE" =~ ^ghcr\.io/[a-z0-9._/-]+@sha256:[a-f0-9]{64}$ ]]; then
  echo "ERROR: debes indicar una imagen de GHCR mediante su digest SHA-256." >&2
  exit 1
fi

if [[ -z "$EXPECTED_IDENTITY" ]]; then
  echo "ERROR: falta la identidad esperada del workflow firmante." >&2
  exit 1
fi

if ! command -v cosign >/dev/null 2>&1; then
  echo "ERROR: Cosign no está instalado." >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIRECTORY"

printf '%s\n' "$IMAGE_REFERENCE" \
  > "$OUTPUT_DIRECTORY/image-reference.txt"

printf '%s\n' "$EXPECTED_IDENTITY" \
  > "$OUTPUT_DIRECTORY/expected-identity.txt"

echo "Verificando firma de la imagen..."

cosign verify \
  --certificate-identity "$EXPECTED_IDENTITY" \
  --certificate-oidc-issuer "$OIDC_ISSUER" \
  "$IMAGE_REFERENCE" \
  > "$OUTPUT_DIRECTORY/signature.json"

echo "Verificando attestation CycloneDX del SBOM..."

cosign verify-attestation \
  --type cyclonedx \
  --certificate-identity "$EXPECTED_IDENTITY" \
  --certificate-oidc-issuer "$OIDC_ISSUER" \
  "$IMAGE_REFERENCE" \
  > "$OUTPUT_DIRECTORY/sbom-attestation.json"

test -s "$OUTPUT_DIRECTORY/signature.json"
test -s "$OUTPUT_DIRECTORY/sbom-attestation.json"

echo "PASS: firma y attestation SBOM verificadas para el digest indicado."
