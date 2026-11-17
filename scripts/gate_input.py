"""Convierte reportes de seguridad y cobertura en una entrada para OPA."""

import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def find_report(directory, filename):
    matches = list(directory.rglob(filename))

    if len(matches) != 1:
        raise ValueError(
            f"Se requiere un solo {filename}; encontrados: {len(matches)}"
        )

    return matches[0]


def read_json(directory, filename):
    path = find_report(directory, filename)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sarif_results(report):
    runs = report.get("runs")

    if not isinstance(runs, list) or not runs:
        raise ValueError("Reporte SARIF sin ejecuciones")

    findings = []

    for run in runs:
        for invocation in run.get("invocations", []):
            if invocation.get("executionSuccessful") is False:
                raise ValueError("El analizador SARIF no terminó correctamente")

        results = run.get("results", [])

        if not isinstance(results, list):
            raise ValueError("Resultados SARIF inválidos")

        findings.extend(results)

    return findings


def build_input(directory):
    secrets = read_json(directory, "gitleaks.sarif")
    sast = read_json(directory, "sast.sarif")
    sca = read_json(directory, "securebank-vulns.json")
    dast = read_json(directory, "report.json")

    metrics = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "secrets": len(sarif_results(secrets)),
        "coverage": 0,
        "internet_exposed": False,
        "dast_high": 0,
    }

    # Semgrep SARIF: error se considera High y warning, Medium.
    # Esta clasificación es una decisión conservadora del proyecto.
    for finding in sarif_results(sast):
        level = finding.get("level", "warning")

        if level == "error":
            metrics["high"] += 1
        elif level == "warning":
            metrics["medium"] += 1
        elif level not in ("note", "none"):
            raise ValueError(f"Nivel SARIF desconocido: {level}")

    results = sca.get("Results")

    if not isinstance(results, list):
        raise ValueError("Reporte Trivy sin Results válidos")

    for result in results:
        vulnerabilities = result.get("Vulnerabilities") or []

        if not isinstance(vulnerabilities, list):
            raise ValueError("Lista de vulnerabilidades Trivy inválida")

        for vulnerability in vulnerabilities:
            severity = vulnerability.get("Severity", "").upper()

            if severity in ("CRITICAL", "HIGH", "MEDIUM"):
                metrics[severity.lower()] += 1
            elif severity not in ("LOW", "UNKNOWN"):
                raise ValueError(
                    f"Severidad Trivy desconocida: {severity}"
                )

    sites = dast.get("site")

    if not isinstance(sites, list) or not sites:
        raise ValueError("Reporte ZAP sin sitios analizados")

    for site in sites:
        alerts = site.get("alerts")

        if not isinstance(alerts, list):
            raise ValueError("Reporte ZAP sin lista de alertas válida")

        for alert in alerts:
            risk = str(alert.get("riskcode", ""))

            if risk == "3":
                metrics["high"] += 1
                metrics["dast_high"] += 1
            elif risk == "2":
                metrics["medium"] += 1
            elif risk not in ("0", "1"):
                raise ValueError(f"Riesgo ZAP desconocido: {risk}")

    coverage_path = find_report(directory, "coverage.xml")
    coverage_root = ET.parse(coverage_path).getroot()
    line_rate = float(coverage_root.attrib["line-rate"])

    if not math.isfinite(line_rate) or not 0 <= line_rate <= 1:
        raise ValueError("Cobertura inválida")

    metrics["coverage"] = round(line_rate * 100, 4)

    return metrics


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python scripts/gate_input.py DIRECTORIO_REPORTES"
        )

    directory = Path(sys.argv[1])

    if not directory.is_dir():
        raise SystemExit("No existe el directorio de reportes")

    try:
        metrics = build_input(directory)
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError) as error:
        raise SystemExit(f"No se puede evaluar el gate: {error}")

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
