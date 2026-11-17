"""Genera el Deployment usando una referencia de imagen con digest."""

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TEMPLATE = (
    ROOT / "k8s/hardened/deployment.hardened.yaml"
)

PLACEHOLDER = (
    "localhost:5001/securebank-api@sha256:REPLACE_DIGEST"
)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(
            "Uso: python scripts/render_k8s.py IMAGEN_CON_DIGEST SALIDA"
        )

    image = sys.argv[1]
    output = Path(sys.argv[2])

    pattern = r"[a-z0-9][a-z0-9._:/-]*@sha256:[a-f0-9]{64}"

    if not re.fullmatch(pattern, image):
        raise SystemExit(
            "La imagen debe incluir una referencia OCI "
            "y un digest sha256 de 64 caracteres"
        )

    if output.resolve() == TEMPLATE.resolve():
        raise SystemExit(
            "La salida no puede sobrescribir la plantilla"
        )

    content = TEMPLATE.read_text(encoding="utf-8")

    if content.count(PLACEHOLDER) != 1:
        raise SystemExit(
            "La plantilla debe contener exactamente un marcador"
        )

    rendered = content.replace(PLACEHOLDER, image)

    if "REPLACE_DIGEST" in rendered:
        raise SystemExit("Quedan marcadores sin reemplazar")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")

    print(f"Deployment generado: {output}")
    print(f"Imagen: {image}")


if __name__ == "__main__":
    main()
