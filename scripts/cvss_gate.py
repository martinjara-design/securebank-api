#!/usr/bin/env python3
"""Policy gate CVSS (Sesión 6) — semáforo de decisión sobre el reporte de Trivy.

  CVSS >= 9.0  -> BLOQUEADO (exit 1)               parche inmediato
  CVSS 7.0-8.9 -> REQUIERE APROBACIÓN (needs_approval=true)  Tech Lead / Security Champion
  CVSS  < 7.0  -> REGISTRAR Y CONTINUAR            backlog de deuda técnica

Uso: cvss_gate.py trivy-report.json [--out reports/securebank-vulns.md]
Escribe `blocked` y `needs_approval` en $GITHUB_OUTPUT cuando existe.
"""
import argparse
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    data = json.load(open(a.report))
    rows = []
    for res in data.get("Results", []):
        for v in res.get("Vulnerabilities") or []:
            s = max_cvss(v)
            rows.append((s, v.get("VulnerabilityID"), v.get("PkgName"),
                         v.get("InstalledVersion"), v.get("FixedVersion") or "—",
                         classify(s)))
    rows.sort(reverse=True)
    blocked = any(r[5] == "BLOQUEADO" for r in rows)
    approval = any(r[5] == "REQUIERE APROBACIÓN" for r in rows)

    lines = ["# Reporte de componentes vulnerables (política CVSS)\n",
             f"Total de CVEs: **{len(rows)}** · bloqueantes: "
             f"**{sum(r[5]=='BLOQUEADO' for r in rows)}** · requieren aprobación: "
             f"**{sum(r[5]=='REQUIERE APROBACIÓN' for r in rows)}**\n",
             "| CVE | Componente | Versión | Corregida en | CVSS | Decisión |",
             "|---|---|---|---|---|---|"]
    lines += [f"| {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[0]} | {r[5]} |" for r in rows]
    if not rows:
        lines.append("| — | — | — | — | — | Sin vulnerabilidades conocidas |")
    text = "\n".join(lines) + "\n"
    print(text)
    if a.out:
        open(a.out, "w").write(text)

    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"blocked={str(blocked).lower()}\n"
                    f"needs_approval={str(approval).lower()}\n")
    if blocked:
        print("::error::CVE con CVSS >= 9.0 — pipeline bloqueado por política.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
