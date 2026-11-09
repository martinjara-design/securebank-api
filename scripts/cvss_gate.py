#!/usr/bin/env python3
"""Policy gate CVSS (Sesión 6) — semáforo de decisión sobre el reporte de Trivy.

  CVSS >= 9.0  -> BLOQUEADO (exit 1)                          parche inmediato
  CVSS 7.0-8.9 -> REQUIERE APROBACIÓN (needs_approval=true)   Tech Lead / Security Champion
  CVSS  < 7.0  -> REGISTRAR                                   backlog de deuda técnica

Uso:
  cvss_gate.py trivy-report.json [--sbom sbom.cdx.json]
                                 [--out reports/securebank-vulns.md]
                                 [--html reports/securebank-vulns.html]

Cada CVE sale con su decisión y una justificación breve. Si se entrega --sbom, el
reporte indica cuántos componentes se analizaron (un "0 CVEs" sin componentes
analizados no significaría nada). Escribe `blocked` y `needs_approval` en
$GITHUB_OUTPUT cuando existe.
"""
import argparse
import html
import json
import os
import sys

CRITICAL, HIGH = 9.0, 7.0


def max_cvss(vuln):
    best = 0.0
    for src in (vuln.get("CVSS") or {}).values():
        for key in ("V3Score", "V2Score"):
            if isinstance(src.get(key), (int, float)):
                best = max(best, float(src[key]))
    return best


def classify(score):
    if score >= CRITICAL:
        return "BLOQUEADO"
    if score >= HIGH:
        return "REQUIERE APROBACIÓN"
    return "REGISTRAR"


def justify(decision, fixed):
    fix = f"actualizar a {fixed}" if fixed != "—" else "sin parche publicado, monitorear"
    if decision == "BLOQUEADO":
        return f"CVSS >= 9.0: la política detiene el pipeline; {fix}."
    if decision == "REQUIERE APROBACIÓN":
        return f"CVSS 7.0-8.9: requiere aprobación humana; {fix} o aceptar el riesgo por escrito."
    return "CVSS < 7.0: se registra en el backlog de deuda técnica, sin detener el pipeline."


def load_components(path):
    if not path:
        return None
    try:
        return len(json.load(open(path)).get("components", []))
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--sbom", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--html", default=None)
    a = ap.parse_args()

    data = json.load(open(a.report))
    rows = []
    for res in data.get("Results", []):
        for v in res.get("Vulnerabilities") or []:
            s = max_cvss(v)
            fixed = v.get("FixedVersion") or "—"
            d = classify(s)
            rows.append((s, v.get("VulnerabilityID"), v.get("PkgName"),
                         v.get("InstalledVersion"), fixed, d, justify(d, fixed)))
    rows.sort(key=lambda r: r[0], reverse=True)
    n_block = sum(r[5] == "BLOQUEADO" for r in rows)
    n_appr = sum(r[5] == "REQUIERE APROBACIÓN" for r in rows)
    blocked, approval = n_block > 0, n_appr > 0
    ncomp = load_components(a.sbom)
    scope = (f"Componentes analizados (SBOM): **{ncomp}** · " if ncomp is not None else "")

    head = ["CVE", "Componente", "Versión", "Corregida en", "CVSS", "Decisión", "Justificación"]
    lines = ["# Reporte de componentes vulnerables (política CVSS)\n",
             f"{scope}CVEs: **{len(rows)}** · bloqueantes: **{n_block}** · "
             f"requieren aprobación: **{n_appr}**\n",
             "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        lines.append(f"| {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[0]} | {r[5]} | {r[6]} |")
    if not rows:
        lines.append("| — | — | — | — | — | Sin vulnerabilidades conocidas | "
                     "Ningún componente analizado tiene CVEs en la base de Trivy. |")
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)

    if a.html:
        color = {"BLOQUEADO": "#b3261e", "REQUIERE APROBACIÓN": "#b26a00", "REGISTRAR": "#2e6b34"}
        trs = "".join(
            "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r[1:5]) +
            f"<td>{r[0]}</td><td style='color:{color[r[5]]};font-weight:600'>{html.escape(r[5])}</td>"
            f"<td>{html.escape(r[6])}</td></tr>" for r in rows) or \
            "<tr><td colspan='7'>Sin vulnerabilidades conocidas.</td></tr>"
        doc = (
            "<!doctype html><html lang='es'><meta charset='utf-8'>"
            "<title>SecureBank API · componentes vulnerables</title>"
            "<style>body{font:14px system-ui;margin:2rem;color:#1b1b1b}"
            "table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:6px 8px;"
            "text-align:left;vertical-align:top}th{background:#eef4fb}</style>"
            "<h1>Reporte de componentes vulnerables (política CVSS)</h1>"
            f"<p>{html.escape(scope.replace('**', ''))}CVEs: <b>{len(rows)}</b> · "
            f"bloqueantes: <b>{n_block}</b> · requieren aprobación: <b>{n_appr}</b></p>"
            "<table><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr>" + trs + "</table></html>")
        open(a.html, "w", encoding="utf-8").write(doc)

    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"blocked={str(blocked).lower()}\nneeds_approval={str(approval).lower()}\n")
    if blocked:
        print("::error::CVE con CVSS >= 9.0 — pipeline bloqueado por política.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
