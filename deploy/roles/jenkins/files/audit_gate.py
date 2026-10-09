#!/usr/bin/env python3
"""Gate de sécurité des dépendances (J2 ex. 13).

pip-audit liste les vulnérabilités mais ne donne pas leur sévérité.
Ce script lit le rapport JSON de pip-audit, récupère la sévérité de chaque
vulnérabilité dans la base OSV (api.osv.dev) et échoue si au moins une
atteint le seuil (CRITICAL par défaut).

Usage : python3 audit_gate.py pip-audit.json [--fail-on CRITICAL|HIGH|MODERATE|LOW]
Codes retour : 0 = gate OK, 1 = gate KO, 2 = impossible de conclure (fail closed)
"""
import argparse
import json
import math
import sys
import urllib.request

LEVELS = ["UNKNOWN", "LOW", "MODERATE", "HIGH", "CRITICAL"]
OSV_URL = "https://api.osv.dev/v1/vulns/{}"

# --- Calcul du score de base CVSS v3.x (repli si OSV ne donne pas de niveau) --
W = {
    "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2},
    "AC": {"L": 0.77, "H": 0.44},
    "UI": {"N": 0.85, "R": 0.62},
    "C": {"H": 0.56, "L": 0.22, "N": 0.0},
}
PR = {"U": {"N": 0.85, "L": 0.62, "H": 0.27}, "C": {"N": 0.85, "L": 0.68, "H": 0.5}}


def roundup(x):
    i = round(x * 100000)
    return i / 100000.0 if i % 10000 == 0 else (math.floor(i / 10000) + 1) / 10.0


def cvss3_score(vector):
    m = dict(p.split(":") for p in vector.split("/")[1:])
    s = m["S"]
    iss = 1 - (1 - W["C"][m["C"]]) * (1 - W["C"][m["I"]]) * (1 - W["C"][m["A"]])
    impact = 6.42 * iss if s == "U" else 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15
    expl = 8.22 * W["AV"][m["AV"]] * W["AC"][m["AC"]] * PR[s][m["PR"]] * W["UI"][m["UI"]]
    if impact <= 0:
        return 0.0
    raw = impact + expl if s == "U" else 1.08 * (impact + expl)
    return roundup(min(raw, 10))


def level_from_score(score):
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MODERATE"
    return "LOW" if score > 0 else "UNKNOWN"


# --- Interrogation OSV --------------------------------------------------------
def fetch(vuln_id):
    req = urllib.request.Request(OSV_URL.format(vuln_id), headers={"User-Agent": "audit-gate"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def severity_of(vuln):
    """Renvoie (niveau, score, identifiant utilisé)."""
    ids = [vuln["id"]] + list(vuln.get("aliases", []))
    # Les fiches GitHub (GHSA) portent un niveau déjà calculé : on les essaie d'abord
    ids.sort(key=lambda i: 0 if i.startswith("GHSA-") else 1)
    best = ("UNKNOWN", 0.0, vuln["id"])
    for vid in ids:
        if vid.startswith("CVE-"):
            continue  # OSV ne sert pas les CVE en direct, elles sont en alias
        try:
            rec = fetch(vid)
        except Exception:
            continue
        lvl = str(rec.get("database_specific", {}).get("severity", "")).upper()
        score = 0.0
        for sev in rec.get("severity", []):
            if sev.get("type") == "CVSS_V3":
                try:
                    score = cvss3_score(sev["score"])
                except Exception:
                    pass
        if lvl not in LEVELS[1:]:
            lvl = level_from_score(score)
        if LEVELS.index(lvl) > LEVELS.index(best[0]):
            best = (lvl, score, vid)
        if best[0] != "UNKNOWN":
            break
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--fail-on", default="CRITICAL", choices=LEVELS[1:])
    args = ap.parse_args()

    with open(args.report) as f:
        data = json.load(f)

    rows, unknown = [], 0
    for dep in data.get("dependencies", []):
        for v in dep.get("vulns", []):
            lvl, score, used = severity_of(v)
            unknown += lvl == "UNKNOWN"
            cves = [a for a in v.get("aliases", []) if a.startswith("CVE-")]
            rows.append((LEVELS.index(lvl), dep["name"], dep["version"], v["id"],
                         ",".join(cves) or "-", lvl, score, ",".join(v.get("fix_versions", [])) or "-"))

    rows.sort(reverse=True)
    print(f"{'PAQUET':<12} {'VERSION':<9} {'VULN':<20} {'CVE':<16} {'SÉVÉRITÉ':<9} {'CVSS':>4}  CORRIGÉ EN")
    for _, name, ver, vid, cve, lvl, score, fix in rows:
        print(f"{name:<12} {ver:<9} {vid:<20} {cve:<16} {lvl:<9} {score:>4}  {fix}")

    threshold = LEVELS.index(args.fail_on)
    blocking = [r for r in rows if r[0] >= threshold]
    print()
    if blocking:
        print(f"GATE DÉPENDANCES : ÉCHEC - {len(blocking)} vulnérabilité(s) de sévérité >= {args.fail_on} :")
        for _, name, ver, vid, cve, lvl, score, fix in blocking:
            print(f"  - {name} {ver} : {cve if cve != '-' else vid} ({lvl}, CVSS {score}) -> mettre à jour vers {fix}")
        return 1
    if unknown:
        print(f"GATE DÉPENDANCES : INDÉTERMINÉ - sévérité introuvable pour {unknown} vulnérabilité(s) (OSV injoignable ?)")
        return 2
    print(f"GATE DÉPENDANCES : OK - aucune vulnérabilité >= {args.fail_on} ({len(rows)} de sévérité inférieure)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
