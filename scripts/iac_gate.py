"""Evalúa un reporte Checkov con la política del laboratorio."""

import json
import math
import sys
from datetime import date, datetime, timezone
from pathlib import Path


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError("Contador ausente o invalido")
    return value


def evaluate(report, policy):
    if policy.get("scope") != "laboratorio-estatico-sin-despliegue":
        raise ValueError("Alcance de politica no permitido")

    minimum = policy["minimum_score"]
    if type(minimum) not in (int, float) or not math.isfinite(minimum):
        raise ValueError("Umbral de score invalido")
    if not 0 <= minimum <= 100:
        raise ValueError("Umbral fuera de rango")

    max_skipped = integer(policy["maximum_skipped_checks"])
    summary = report["summary"]
    results = report["results"]

    passed = integer(summary["passed"])
    failed = integer(summary["failed"])
    skipped = integer(summary["skipped"])
    parsing_errors = integer(summary["parsing_errors"])
    resources = integer(summary["resource_count"])

    for field, expected in (
        ("passed_checks", passed),
        ("failed_checks", failed),
        ("skipped_checks", skipped),
    ):
        entries = results[field]
        if not isinstance(entries, list) or len(entries) != expected:
            raise ValueError(f"Reporte inconsistente: {field}")

    if resources == 0 or passed + failed == 0:
        raise ValueError("Reporte sin recursos o controles evaluados")

    score = passed / (passed + failed) * 100
    reasons = []
    allowed = set()

    exceptions = policy["exceptions"]
    if not isinstance(exceptions, list):
        raise ValueError("Lista de excepciones invalida")

    today = datetime.now(timezone.utc).date()

    for exception in exceptions:
        check_id = exception["check_id"]
        resource = exception["resource"]
        reason = exception["reason"]

        if not all(
            isinstance(value, str) and value.strip()
            for value in (check_id, resource, reason)
        ):
            raise ValueError("Excepcion incompleta")

        if "*" in check_id or "*" in resource:
            raise ValueError("No se permiten excepciones con comodines")

        pair = (check_id, resource)

        if pair in allowed:
            raise ValueError("Excepcion duplicada")

        allowed.add(pair)

        if date.fromisoformat(exception["expires"]) < today:
            reasons.append(
                f"Excepcion vencida: {check_id} / {resource}"
            )

    unexpected = []

    for finding in results["failed_checks"]:
        pair = (finding["check_id"], finding["resource"])

        if pair not in allowed:
            unexpected.append({
                "check_id": pair[0],
                "resource": pair[1],
            })

    if parsing_errors or results.get("parsing_errors"):
        reasons.append("Existen errores de parseo")

    if score < minimum:
        reasons.append(
            f"Score {score:.2f}% inferior al minimo {minimum}%"
        )

    if skipped > max_skipped:
        reasons.append("Se supera el limite de controles omitidos")

    if unexpected:
        reasons.append("Existen fallos no exceptuados")

    return {
        "scope": policy["scope"],
        "allow": not reasons,
        "score": round(score, 2),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "unexpected_failures": unexpected,
        "deny": reasons,
    }


def main():
    if len(sys.argv) != 4:
        raise SystemExit(
            "Uso: python scripts/iac_gate.py REPORTE POLITICA SALIDA"
        )

    report_path, policy_path, output_path = map(
        Path, sys.argv[1:]
    )

    try:
        report = json.loads(
            report_path.read_text(encoding="utf-8-sig")
        )
        policy = json.loads(
            policy_path.read_text(encoding="utf-8-sig")
        )
        decision = evaluate(report, policy)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
    ) as error:
        decision = {
            "allow": False,
            "deny": [f"Entrada invalida: {error}"],
        }

    text = json.dumps(
        decision,
        indent=2,
        ensure_ascii=False,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text + "\n", encoding="utf-8")

    print(text)
    raise SystemExit(0 if decision["allow"] else 1)


if __name__ == "__main__":
    main()
