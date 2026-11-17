"""Genera politicas Kyverno con identidad exacta, sin expresiones amplias."""
import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('Uso: render_admission.py IDENTIDAD SALIDA')
identity = sys.argv[1]
pattern = r'https://github\.com/martinjara-design/securebank-api/\.github/workflows/supply-chain\.yml@refs/heads/(main|feature/cierre-entrega|feature/sesion-13-supply-chain)'
if not re.fullmatch(pattern, identity):
    raise SystemExit('Identidad fuera de las ramas autorizadas del laboratorio')
keyless = {
    'subject': identity,
    'issuer': 'https://token.actions.githubusercontent.com',
    'rekor': {'url': 'https://rekor.sigstore.dev'},
}
attestors = [{'count': 1, 'entries': [{'keyless': keyless}]}]
match = {'any': [{'resources': {'kinds': ['Pod'], 'namespaces': ['securebank']}}]}
registry = 'ghcr.io/martinjara-design/securebank-api'
policy = {
    'apiVersion': 'kyverno.io/v1', 'kind': 'ClusterPolicy',
    'metadata': {'name': 'securebank-signed-images',
                 'annotations': {'pod-policies.kyverno.io/autogen-controllers': 'none'}},
    'spec': {
        'validationFailureAction': 'Enforce', 'background': False,
        'webhookConfiguration': {'failurePolicy': 'Fail', 'timeoutSeconds': 30},
        'rules': [{'name': 'verify-signature-and-sbom', 'match': match,
                   'verifyImages': [{
                       'imageReferences': [registry + '*'], 'type': 'Cosign',
                       'required': True, 'verifyDigest': True, 'mutateDigest': False,
                       'imageRegistryCredentials': {'secrets': ['ghcr-read']},
                       'attestors': attestors,
                       'attestations': [{
                           'predicateType': 'https://cyclonedx.org/bom',
                           'attestors': attestors,
                       }],
                   }]}],
    },
}
# Sin esta segunda politica una imagen de otro registro no coincidiria con verifyImages.
allow_registry = {
    'apiVersion': 'kyverno.io/v1', 'kind': 'ClusterPolicy',
    'metadata': {'name': 'securebank-trusted-registry',
                 'annotations': {'pod-policies.kyverno.io/autogen-controllers': 'none'}},
    'spec': {
        'validationFailureAction': 'Enforce', 'background': False,
        'webhookConfiguration': {'failurePolicy': 'Fail', 'timeoutSeconds': 30},
        'rules': [{'name': 'require-trusted-registry-and-digest', 'match': match,
                   'validate': {'message': 'Solo se admiten imagenes SecureBank por digest.',
                                'pattern': {'spec': {
                                    'containers': [{'image': registry + '@sha256:*'}],
                                    '=(initContainers)': [{'image': registry + '@sha256:*'}],
                                    '=(ephemeralContainers)': [{'image': registry + '@sha256:*'}],
                                }}}}],
    },
}
# JSON es un subconjunto valido de YAML; dos documentos Kubernetes.
output = Path(sys.argv[2])
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(policy, indent=2) + '\n---\n' + json.dumps(allow_registry, indent=2) + '\n')
