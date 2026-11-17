"""Comprueba el acceso permitido y bloqueado a la API."""

import copy
import json
import subprocess
from pathlib import Path


OUTPUT = Path("reports/k8s/network-checks.json")

PROBE = """
import sys
from urllib.error import URLError
from urllib.request import urlopen

try:
    with urlopen(sys.argv[1], timeout=4) as response:
        if response.status != 200:
            raise RuntimeError("Respuesta HTTP inesperada")
        print("HTTP 200")
except TimeoutError:
    print("Conexion agotada")
    sys.exit(75)
except URLError as error:
    if isinstance(error.reason, TimeoutError):
        print("Conexion agotada")
        sys.exit(75)
    raise
"""


def kubectl(*args, body=None):
    return subprocess.run(
        ["kubectl", "-n", "securebank", *args],
        input=body,
        text=True,
        capture_output=True,
        check=True,
        timeout=150,
    ).stdout


def client(name, authorized, pod_spec):
    labels = {"network-test": "securebank"}

    if authorized:
        labels["access"] = "securebank-api"

    container = pod_spec["containers"][0]

    return {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": name,
            "namespace": "securebank",
            "labels": labels,
        },
        "spec": {
            "serviceAccountName": "securebank-api",
            "automountServiceAccountToken": False,
            "restartPolicy": "Never",
            "securityContext": copy.deepcopy(
                pod_spec["securityContext"]
            ),
            "containers": [
                {
                    "name": "client",
                    "image": container["image"],
                    "imagePullPolicy": "Always",
                    "command": [
                        "python",
                        "-c",
                        "import time; time.sleep(600)",
                    ],
                    "securityContext": copy.deepcopy(
                        container["securityContext"]
                    ),
                    "resources": {
                        "requests": {
                            "cpu": "10m",
                            "memory": "32Mi",
                        },
                        "limits": {
                            "cpu": "100m",
                            "memory": "64Mi",
                        },
                    },
                }
            ],
        },
    }


def probe(name, url):
    return subprocess.run(
        [
            "kubectl",
            "-n",
            "securebank",
            "exec",
            name,
            "--",
            "python",
            "-c",
            PROBE,
            url,
        ],
        text=True,
        capture_output=True,
        timeout=20,
    )


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    deployment = json.loads(
        kubectl("get", "deployment", "securebank-api", "-o", "json")
    )
    service = json.loads(
        kubectl("get", "service", "securebank-api", "-o", "json")
    )

    pod_spec = deployment["spec"]["template"]["spec"]
    address = service["spec"]["clusterIP"]
    url = f"http://{address}:8080/health"

    manifests = {
        "apiVersion": "v1",
        "kind": "List",
        "items": [
            client("network-allowed", True, pod_spec),
            client("network-denied", False, pod_spec),
        ],
    }

    kubectl("apply", "-f", "-", body=json.dumps(manifests))

    kubectl(
        "wait",
        "--for=condition=Ready",
        "pods",
        "-l",
        "network-test=securebank",
        "--timeout=120s",
    )

    checks = {}

    allowed = probe("network-allowed", url)
    checks["authorized_client_http_200"] = allowed.returncode == 0

    denied = probe("network-denied", url)
    checks["unauthorized_client_timeout"] = denied.returncode == 75

    # Repetimos el control positivo para comprobar que la API sigue viva.
    repeated = probe("network-allowed", url)
    checks["authorized_client_still_reachable"] = (
        repeated.returncode == 0
    )

    result = {
        "target": url,
        "checks": checks,
        "details": {
            "allowed": allowed.stdout + allowed.stderr,
            "denied": denied.stdout + denied.stderr,
            "repeated": repeated.stdout + repeated.stderr,
        },
    }

    OUTPUT.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2))

    if not all(checks.values()):
        raise SystemExit("Fallo la comprobacion de NetworkPolicy")


if __name__ == "__main__":
    main()
