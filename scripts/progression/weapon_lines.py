#!/usr/bin/env python3
"""Extract the existing PR290 proposal without interpreting or activating its mechanics."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "debdf9495bd32966e1f1b65a67a5e6964b62b743"
OUTPUT = ROOT / "game/data/weapon_lines.json"
CATALOGUE = "game/data/progression/catalogue.json"
STATUS = "proposal; weapon table unapproved (PR290); all balance values are placeholders"


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def git(*args):
    result = subprocess.run(["git", "--no-replace-objects", *args], cwd=ROOT, capture_output=True, check=False)
    if result.returncode:
        raise ValueError("cannot read pinned source: " + result.stderr.decode(errors="replace").strip())
    return result.stdout


def extract():
    catalogue = json.loads(git("show", SOURCE + ":" + CATALOGUE))
    ids = catalogue["characters"]
    if not isinstance(ids, list) or len(ids) != 14 or any(not isinstance(x, str) or not re.fullmatch(r"[a-z_]+", x) for x in ids) or len(set(ids)) != 14:
        raise ValueError("pinned catalogue does not contain fourteen unique folk IDs")
    lines = []
    for name in ids:
        path = f"game/data/progression/{name}.json"
        original = json.loads(git("show", SOURCE + ":" + path))
        if original["id"] != name:
            raise ValueError("source identity mismatch: " + name)
        weapon = original["weapon"]
        lines.append({"id": name, "source_path": path,
                      "source_blob": git("rev-parse", SOURCE + ":" + path).decode().strip(),
                      "weapon_sha256": digest(weapon), "weapon": weapon})
    return {"schema_version": 1, "status": STATUS, "approved": False,
            "mechanics_applied": False,
            "source": {"commit": SOURCE, "pr": 290, "catalogue_path": CATALOGUE,
                       "catalogue_blob": git("rev-parse", SOURCE + ":" + CATALOGUE).decode().strip()},
            "lines": lines}


def validate(document):
    if not isinstance(document, dict) or type(document.get("schema_version")) is not int or document["schema_version"] != 1:
        raise ValueError("unsupported document schema")
    if document.get("approved") is not False or document.get("mechanics_applied") is not False or document.get("status") != STATUS:
        raise ValueError("proposal/approval status changed")
    source = document.get("source")
    if not isinstance(source, dict) or source.get("commit") != SOURCE or source.get("pr") != 290 or source.get("catalogue_path") != CATALOGUE or not re.fullmatch(r"[a-f0-9]{40}", str(source.get("catalogue_blob", ""))):
        raise ValueError("missing or unsupported source provenance")
    records = document.get("lines")
    if not isinstance(records, list) or len(records) != 14:
        raise ValueError("expected fourteen weapon lines")
    seen = set()
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not re.fullmatch(r"[a-z_]+", row["id"]) or row["id"] in seen:
            raise ValueError("malformed/duplicate folk ID")
        seen.add(row["id"])
        if row.get("source_path") != f"game/data/progression/{row['id']}.json" or not re.fullmatch(r"[a-f0-9]{40}", str(row.get("source_blob", ""))):
            raise ValueError("malformed source path/blob")
        weapon = row.get("weapon")
        if not isinstance(weapon, dict) or row.get("weapon_sha256") != digest(weapon):
            raise ValueError("weapon content fingerprint mismatch: " + row["id"])
        tiers = weapon.get("tiers")
        if not isinstance(tiers, list) or len(tiers) != 4:
            raise ValueError("expected four stages: " + row["id"])
        for index, tier in enumerate(tiers):
            if not isinstance(tier, dict) or type(tier.get("tier")) is not int or tier["tier"] != index + 1 or type(tier.get("level")) is not int or tier["level"] != [1, 8, 16, 24][index]:
                raise ValueError("stage/level mismatch: " + row["id"])
            for key in ["name", "form"]:
                if not isinstance(tier.get(key), str) or not tier[key].strip():
                    raise ValueError("missing stage " + key)
            if not isinstance(tier.get("requires"), dict) or tier["requires"].get("level") != tier["level"] or not isinstance(tier.get("mechanics"), dict):
                raise ValueError("malformed stage requirements/mechanics")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true", help="compare every weapon with the pinned Git source")
    group.add_argument("--check-stored", action="store_true", help="offline structure/provenance/fingerprint check; no Git objects needed")
    parser.add_argument("--path", type=Path, default=OUTPUT)
    args = parser.parse_args()
    try:
        if args.check_stored:
            validate(json.loads(args.path.read_text()))
        else:
            expected = extract()
            validate(expected)
            if args.check:
                stored = json.loads(args.path.read_text())
                validate(stored)
                if stored != expected:
                    raise ValueError("stored table differs from pinned source")
            else:
                args.path.parent.mkdir(parents=True, exist_ok=True)
                text = json.dumps(expected, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
                with tempfile.NamedTemporaryFile("w", dir=args.path.parent, delete=False, encoding="utf-8") as f:
                    tmp = Path(f.name)
                    f.write(text)
                try:
                    os.replace(tmp, args.path)
                finally:
                    tmp.unlink(missing_ok=True)
        print("weapon lines: 14 lines / 56 stages; proposal only, mechanics inactive")
        return 0
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print("weapon lines: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
