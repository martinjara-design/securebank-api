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
    if policy.get("scope") not in ("laboratorio-estatico-sin-despliegue", "aws-lab"):
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
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    classified = []
    exceptions_by_pair = {(e["check_id"], e["resource"]): e for e in exceptions}


    for finding in results["failed_checks"]:
        pair = (finding["check_id"], finding["resource"])

        exception = exceptions_by_pair.get(pair, {})
        # Checkov OSS puede omitir severidad. Una excepcion no puede ocultar
        # una severidad HIGH/CRITICAL proporcionada por el scanner.
        scanner_severity = finding.get("severity")
        if isinstance(scanner_severity, dict):
            scanner_severity = scanner_severity.get("name")
        if isinstance(scanner_severity, str):
            scanner_severity = scanner_severity.upper()
        contextual = exception.get("contextual_severity")
        if contextual is not None and contextual not in ("LOW", "MEDIUM"):
            raise ValueError("Solo se admiten excepciones contextuales LOW/MEDIUM")
        severity = scanner_severity or contextual or (
            "CRITICAL" if pair[0] in ("CKV_AWS_24", "CKV_AWS_20") else "HIGH"
        )
        if severity not in severity_counts:
            raise ValueError("Severidad desconocida")
        severity_counts[severity] += 1
        classified.append({"check_id": pair[0], "resource": pair[1],
                           "severity": severity,
                           "source": "scanner" if scanner_severity else "politica-contextual-del-equipo"})
        if pair not in allowed or severity in ("CRITICAL", "HIGH"):
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
        "resources": resources,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "unexpected_failures": unexpected,
        "severity_counts": severity_counts,
        "classified_failures": classified,
        "severity_note": "Clasificacion contextual del equipo cuando Checkov no proporciona severidad; no es una severidad oficial del scanner.",
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
