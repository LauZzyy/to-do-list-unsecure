#!/usr/bin/env python3
"""Convertit la section [packages] d'un Pipfile en requirements.txt.

Le Pipfile reste l'unique source de vérité des dépendances : le déploiement
(Ansible) et le contrôle (pip-audit dans Jenkins) lisent les MÊMES versions.

Usage : python3 ci/pipfile_to_requirements.py [Pipfile] > requirements.txt
"""
import sys
import tomllib


def to_requirement(name, spec):
    extras = ""
    if isinstance(spec, dict):
        if spec.get("extras"):
            extras = "[" + ",".join(spec["extras"]) + "]"
        spec = spec.get("version", "*")
    spec = str(spec).strip()
    if spec in ("", "*"):
        return f"{name}{extras}"
    return f"{name}{extras}{spec}"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "Pipfile"
    with open(path, "rb") as f:
        pipfile = tomllib.load(f)
    for name, spec in pipfile.get("packages", {}).items():
        print(to_requirement(name, spec))


if __name__ == "__main__":
    main()
