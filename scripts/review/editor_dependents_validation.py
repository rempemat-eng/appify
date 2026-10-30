#!/usr/bin/env python3
"""Bounded EDITOR-DEPENDENTS receiver; SOURCE ONLY until exact lead allocation.

Adapted from reviewed #401 fdb9cbe5 (controller blob c503be58).
Separate immutable #396 game plus its actual stdlib validator inputs; no GUI,
save/reopen/export/bake/runtime acceptance is inferred from these eight methods.
No imports, engine or tests are authorised by publishing this candidate.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import time
import traceback
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

# Receiver history stays on the original candidate; only source/ is executed.
CANDIDATE_BASE_SHA = "3c925bc42a34ed8c3cc86b2dddd77e08e38cbe41"
CANDIDATE_BASE_TREE = "490e0985c46b90ad7cbe5bb4f9cbe14e762e67c6"
PRIOR_CANDIDATE_SHA = "d3da0885114da2cfab92747ad767191244e99199"
PRIOR_CANDIDATE_TREE = "3b5a416d5201f88477515c1bc1ecdcebd54dcb23"
GAME_SHA = "12ea03fd3e0c9921b2d35b061f77ccb551586f9c"
GAME_TREE = "9ce15ff835c7aafea2a0915bd182935bf04d4cfe"
GROUND_PATH = "game/world/terrain/terrain_ground.gd"
CANDIDATE_GROUND_BLOB = "eae36ad6268bb5dbba40f36b2b12041c4979038a"
GROUND_BLOB = "3e1f1c30a942cac648864ea7210ac436ec03c34f"
TEST_BLOB = "af4bc24645ed06d69d987070f866d5e774246465"
PRODUCTION_BLOB = "effd244781b1e71c5d990b14df82258280e93811"
GAME_COUNT = 6687
GAME_BYTES = 87861809
# Exact existing files only. scripts/ and scripts/art/ are namespace packages.
# check_zone reads size_guide.json even with a supplied library/material map.
PYTHON_INPUTS = {
    "scripts/art/kit/__init__.py": ("e69de29bb2d1d6434b8b29ae775ad8c2e48c5391", 0),
    "scripts/art/kit/relations.py": ("dd6b718b24f9f681cd5450ecbb0216e6a1ae8420", 19542),
    "scripts/art/size_guide.json": ("f30ecb3249d771e5dc6cdf6546d50400b118cf57", 45069),
    "scripts/review/__init__.py": ("e69de29bb2d1d6434b8b29ae775ad8c2e48c5391", 0),
    "scripts/review/ground_rules.py": ("0bfe3fff9d74f3b1ecd07afe1ff27b0940143f68", 18956),
    "scripts/review/kit_scene.py": ("6c71732fb52cbe86e8fa723c4d09a0af4d553371", 28305),
}
PYTHON_COUNT = 6
PYTHON_BYTES = 111872
TEST_PATH = "game/test/test_world_editor_dependent_edits.gd"
REPORT_DIR = "reports-editor-dependents"
ENGINE_SHA256 = "8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e"
ENGINE_BYTES = 146414384
ARCHIVE_SHA512 = "9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65"
ENGINE_NAME = "Godot_v4.7.2-stable_linux.x86_64"
ENGINE_URL = "https://github.com/godotengine/godot/releases/download/4.7.2-stable/" + ENGINE_NAME + ".zip"
OWNED_LIMIT = 512 * 1024**2
FREE_RESERVE = 256 * 1024**2
RSS_LIMIT = 1536 * 1024**2
LOG_LIMIT = 4 * 1024**2
OWNED_PATHS = {".github/workflows/editor-dependents-validation.yml",
               "scripts/review/editor_dependents_validation.py"}
METHODS = (
    "test_startup_canary_real_intake_and_adapter",
    "test_paint_beneath_existing_footprint_refreshes_rules_and_undo_redo",
    "test_route_relation_distance_boundary_and_interacting_water_prohibition",
    "test_tier_change_breaks_stair_deck_route_and_import_is_unshippable",
    "test_moving_stair_support_immediately_refreshes_validation_and_bake",
    "test_deleting_stair_support_exposes_route_without_stale_bake",
    "test_moving_related_seat_revalidates_instead_of_reusing_green",
    "test_rejections_preserve_document_and_existing_redo_branch",
)
STALE_BAKE_MESSAGES = {
    "test_moving_stair_support_immediately_refreshes_validation_and_bake":
        "Moved painted stair must invalidate its previous baked ground",
    "test_deleting_stair_support_exposes_route_without_stale_bake":
        "Deleted painted stair must invalidate its previous baked ground",
}
ERROR_PATTERN = re.compile(r"SCRIPT ERROR:|^ERROR:|Parse Error|Failed loading resource|Cannot open file", re.M)
PYTHON_ERROR_PATTERN = re.compile(
    r"Traceback \(most recent call last\):|ModuleNotFoundError:|ImportError:|FileNotFoundError:"
    r"|editor\.validator_(?:io|failed|protocol)"
)

# Tiny separate editor project: measure actual APIs/settings file, not merely env.
PROBE = '''@tool
extends EditorPlugin
func _enter_tree() -> void:
    call_deferred("_paths")
func _paths() -> void:
    await get_tree().process_frame
    var paths = EditorInterface.get_editor_paths()
    var settings = EditorInterface.get_editor_settings()
    var out = {
        "version": Engine.get_version_info(), "executable": OS.get_executable_path(),
        "os_config": OS.get_config_dir(), "os_data": OS.get_data_dir(), "os_cache": OS.get_cache_dir(),
        "os_user": OS.get_user_data_dir(), "user_uri": ProjectSettings.globalize_path("user://"),
        "editor_config": paths.get_config_dir(), "editor_data": paths.get_data_dir(),
        "editor_cache": paths.get_cache_dir(),
        "project_settings": ProjectSettings.globalize_path(paths.get_project_settings_dir()),
        "settings_resource": settings.resource_path,
        "self_contained": paths.is_self_contained(), "portable_marker": paths.get_self_contained_file()
    }
    var file = FileAccess.open(OS.get_environment("EDITOR_DEPENDENTS_CANARY_OUTPUT"), FileAccess.WRITE)
    if file == null:
        push_error("EDITOR_DEPENDENTS canary output open failed")
        get_tree().quit(2)
        return
    file.store_string(JSON.stringify(out) + "\\n")
    file.close()
    print("EDITOR_DEPENDENTS_CANARY_PATHS=" + JSON.stringify(out))
    get_tree().quit(0)
'''


def digest(path: Path, kind: str = "sha256") -> str:
    h = hashlib.new(kind)
    with path.open("rb") as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def blob(path: Path) -> str:
    h = hashlib.sha1(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def diagnostic_text(path: Path) -> str:
    # Raw bytes stay untouched in the artifact. Strip terminal escapes for scanning only.
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", path.read_text(errors="replace")).replace("\r", "")


def orphan_diagnostics(text: str) -> list[str]:
    found = []
    for line in text.splitlines():
        if re.search(r"ObjectDB instances leaked|resources? still in use|RID.*leak", line, re.I):
            found.append(line)
        elif re.search(r"\borphans?\b", line, re.I):
            # Diagnostic words/counts, not GdUnitOrphan* class registration.
            counts = re.findall(
                r"\borphans?(?:\s+nodes?)?\s*[:=]\s*(\d+)\b|\b(\d+)\s+orphans?(?:\s+nodes?)?\b",
                line, re.I
            )
            if not counts or any(int(first or second) > 0 for first, second in counts):
                found.append(line)
    return found


def git(repo: Path, *args: str) -> bytes:
    # Metadata only; no hooks, lazy network fetch, refresh, index or worktree writes.
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1"}
    command = ["git", "-C", str(repo), *args]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=30, env=env, check=False)
    if result.returncode:
        raise RuntimeError(f"metadata command failed {command!r}: {result.stderr.decode(errors='replace')}")
    return result.stdout


def tree(repo: Path, ref: str = "HEAD") -> dict[str, tuple[str, str]]:
    entries = {}
    for raw in git(repo, "ls-tree", "-r", "-z", ref).split(b"\0"):
        if not raw:
            continue
        header, name = raw.split(b"\t", 1)
        mode, kind, sha = header.decode().split()
        if kind != "blob":
            raise RuntimeError("Non-blob/submodule in source tree")
        entries[os.fsdecode(name)] = (mode, sha)
    return entries


def proc_group(pgid: int) -> dict[int, dict[str, int | str]]:
    members = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            value = (entry / "stat").read_text()
            fields = value[value.rfind(")") + 2:].split()
            if int(fields[2]) == pgid:
                members[int(entry.name)] = dict(state=fields[0], start=int(fields[19]),
                                               ppid=int(fields[1]), pgid=int(fields[2]),
                                               rss=int(fields[21]) * os.sysconf("SC_PAGE_SIZE"))
        except (FileNotFoundError, ProcessLookupError):
            continue
    return members


def direct_children() -> dict[int, dict]:
    result = {}
    children = Path(f"/proc/self/task/{os.getpid()}/children").read_text().split()
    for number in children:
        pid = int(number)
        try:
            value = Path(f"/proc/{pid}/stat").read_text()
            fields = value[value.rfind(")") + 2:].split()
            if int(fields[1]) == os.getpid():
                result[pid] = {"start": int(fields[19]), "pgid": int(fields[2]), "state": fields[0]}
        except (FileNotFoundError, ProcessLookupError):
            continue
    return result


class Controller:
    def __init__(self, args: argparse.Namespace):
        self.candidate = args.candidate.resolve(strict=True)
        self.source = args.source.resolve(strict=True)
        self.root = args.root.resolve(strict=True)
        self.game = self.source / "game"
        self.evidence = self.root / "evidence"
        self.event_sha = args.event_sha
        self.phases = {name: {"state": "NOT RUN"} for name in ("canary", "import", "check-only", "focused")}
        self.guards = {}
        self.engine = self.root / "engine" / ENGINE_NAME
        self.initial = None
        self.candidate_initial = None
        self.output = {"state": "SETUP_FAILED", "workflow_sha": self.event_sha,
                       "tested_game_sha": GAME_SHA, "tested_game_tree": GAME_TREE,
                       "phases": self.phases, "guards": self.guards,
                       "qualification": "Eight unexecuted controls until this exact allocated invocation. No GUI/bake/runtime/full-suite/Ready/acceptance."}
        self.owned_roots = (self.root, self.source, self.candidate)

    def capacity(self) -> dict:
        used = 0
        mutable_roots = (self.root, self.game / ".godot", self.game / "reports-editor-dependents")

        def scan_error(error: OSError) -> None:
            # Only mutable duty outputs may vanish. Tracked/candidate source,
            # permission failures and every other I/O error still fail closed.
            if isinstance(error, FileNotFoundError) and error.filename is not None:
                path = Path(error.filename)
                if any(path.is_relative_to(p) for p in mutable_roots):
                    return
                # Godot's observed asset-side atomic .import-XXXXXX sibling.
                # Only the established exact-source snapshot grants ownership;
                # canonical assets/sidecars and tracked lookalikes stay strict.
                initial = getattr(self, "initial", None)
                if (self.game == self.source / "game" and path.is_relative_to(self.game)
                        and isinstance(initial, dict) and initial.get("head") == GAME_SHA
                        and initial.get("tree") == GAME_TREE):
                    tracked = initial.get("game")
                    relative = path.relative_to(self.source).as_posix()
                    temporary = re.fullmatch(r"(.+\.import)-[A-Za-z0-9]{6}", relative)
                    if (isinstance(tracked, dict) and temporary and relative not in tracked
                            and temporary[1] in tracked
                            and temporary[1].removesuffix(".import") in tracked):
                        return
            raise error

        for root in self.owned_roots:
            for base, dirs, files in os.walk(root, followlinks=False, onerror=scan_error):
                for name in dirs + files:
                    p = Path(base) / name
                    try:
                        info = p.lstat()
                    except FileNotFoundError as error:
                        scan_error(error)
                        continue
                    if stat.S_ISLNK(info.st_mode):
                        raise RuntimeError(f"Unexpected writable/source symlink: {p}")
                    used += info.st_blocks * 512
        free = min(shutil.disk_usage(p).free for p in self.owned_roots)
        value = {"owned_allocated_bytes": used, "free_bytes": free}
        if used > OWNED_LIMIT or free < FREE_RESERVE:
            raise RuntimeError(f"owned disk/reserve limit: {value}")
        return value

    def snapshot(self) -> dict:
        if git(self.source, "rev-parse", "HEAD").decode().strip() != GAME_SHA:
            raise RuntimeError("Test source HEAD moved")
        if git(self.source, "rev-parse", "HEAD^{tree}").decode().strip() != GAME_TREE:
            raise RuntimeError("Test source tree mismatch")
        expected = tree(self.source)
        game_rows, python_rows = {}, {}
        for name, (mode, sha) in expected.items():
            if not name.startswith("game/") and name not in PYTHON_INPUTS:
                continue
            p = self.source / name
            info = p.lstat()
            if mode not in ("100644", "100755") or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise RuntimeError(f"Nonphysical/shared source: {name}")
            actual = blob(p)
            executable = bool(info.st_mode & 0o111)
            if actual != sha or executable != (mode == "100755"):
                raise RuntimeError(f"Source content/mode changed: {name}")
            row = {"mode": mode, "blob": sha, "sha256": digest(p), "bytes": info.st_size}
            (game_rows if name.startswith("game/") else python_rows)[name] = row
        if len(game_rows) != GAME_COUNT or sum(x["bytes"] for x in game_rows.values()) != GAME_BYTES:
            raise RuntimeError("Exact game subtree inventory differs")
        if (len(python_rows) != PYTHON_COUNT
                or sum(x["bytes"] for x in python_rows.values()) != PYTHON_BYTES
                or {name: (row["blob"], row["bytes"]) for name, row in python_rows.items()} != PYTHON_INPUTS):
            raise RuntimeError("Exact Python validator/input closure differs")
        for absent in ("scripts/__init__.py", "scripts/art/__init__.py"):
            if absent in expected or (self.source / absent).exists():
                raise RuntimeError("Namespace package unexpectedly replaced by an initializer")
        if game_rows[TEST_PATH]["blob"] != TEST_BLOB or game_rows["game/game.gd"]["blob"] != PRODUCTION_BLOB:
            raise RuntimeError("Frozen test/production pin differs")
        if game_rows[GROUND_PATH]["blob"] != GROUND_BLOB or game_rows[GROUND_PATH]["bytes"] != 14449:
            raise RuntimeError("Corrected executed TerrainGround pin differs")
        test_text = (self.source / TEST_PATH).read_text()
        if tuple(re.findall(r"^func (test_\w+)\(", test_text, re.M)) != METHODS:
            raise RuntimeError("Eight authored methods differ")
        git_dir = Path(git(self.source, "rev-parse", "--absolute-git-dir").decode().strip())
        if (git_dir / "objects/info/alternates").exists():
            raise RuntimeError("Source checkout borrows object storage")
        index = git_dir / "index"
        return {"head": GAME_SHA, "tree": GAME_TREE, "game": game_rows,
                "python_closure": python_rows, "index_sha256": digest(index)}

    def setup(self) -> None:
        if os.environ.get("GITHUB_REPOSITORY") != "rempemat-eng/appify":
            raise RuntimeError("Unexpected repository")
        if os.environ.get("GITHUB_RUN_ATTEMPT") != "1":
            raise RuntimeError("Only the first allocated workflow attempt may run")
        if sys.platform != "linux" or platform.machine() not in ("x86_64", "AMD64") or sys.version_info[:2] != (3, 12):
            raise RuntimeError("Requires existing Linux x86_64 / CPython3.12 hosting")
        if not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal"):
            raise RuntimeError("No identity-safe escaped-child collection support")
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
        workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve(strict=True)
        if self.source != workspace / "source" or self.candidate != workspace / "runner":
            raise RuntimeError("Not the two fresh duty-specific checkouts")
        if self.root != Path(os.environ["RUNNER_TEMP"]).resolve(strict=True) / "editor-dependents":
            raise RuntimeError("Unexpected private runtime root")
        if not re.fullmatch(r"[0-9a-f]{40}", self.event_sha) or self.event_sha != os.environ["GITHUB_SHA"]:
            raise RuntimeError("Immutable workflow event SHA mismatch")
        if os.environ.get("GITHUB_REF") != "refs/heads/codex/editor-dependents-validation-run":
            raise RuntimeError("Execution ref is not lead-controlled run ref")
        if git(self.candidate, "rev-parse", "HEAD").decode().strip() != self.event_sha:
            raise RuntimeError("Workflow/controller checkout differs from event")
        if Path(os.environ.get("PYTHON", "")).resolve(strict=True) != Path(sys.executable).resolve(strict=True):
            raise RuntimeError("Hosted PYTHON must explicitly select this CPython executable")
        if any((self.game / name).exists() for name in (".godot", REPORT_DIR, TEST_PATH.removeprefix("game/") + ".uid")):
            raise RuntimeError("Project has prior import/report/UID state; requires fresh physical checkout")
        # The workflow opens controller.log before spawning this process.
        if set(self.root.iterdir()) != {self.evidence} or set(self.evidence.iterdir()) != {
            self.evidence / "bootstrap.json", self.evidence / "controller.log"
        }:
            raise RuntimeError("Duty runtime/evidence is not fresh")
        # Candidate depth=3 retains original3c925 -> prior d3da -> this child.
        # The corrected game is a separate genuine child of original3c925.
        headers = git(self.candidate, "cat-file", "commit", "HEAD").decode().split("\n\n", 1)[0]
        parents = [line.removeprefix("parent ") for line in headers.splitlines() if line.startswith("parent ")]
        if parents != [PRIOR_CANDIDATE_SHA]:
            raise RuntimeError("Candidate must be a genuine sole child of frozen #402 d3da")
        history_headers = {}
        for sha, expected_tree, expected_parent in (
            (PRIOR_CANDIDATE_SHA, PRIOR_CANDIDATE_TREE, CANDIDATE_BASE_SHA),
            (CANDIDATE_BASE_SHA, CANDIDATE_BASE_TREE, "45ed3cad029c106977e6c0c833913dcb1c614fbd"),
        ):
            if git(self.candidate, "rev-parse", sha + "^{tree}").decode().strip() != expected_tree:
                raise RuntimeError("Immutable candidate history tree differs")
            value = git(self.candidate, "cat-file", "commit", sha).decode().split("\n\n", 1)[0]
            if [line.removeprefix("parent ") for line in value.splitlines()
                    if line.startswith("parent ")] != [expected_parent]:
                raise RuntimeError("Immutable candidate history parent differs")
            history_headers[sha] = value
        source_headers = git(self.source, "cat-file", "commit", "HEAD").decode().split("\n\n", 1)[0]
        if [line.removeprefix("parent ") for line in source_headers.splitlines()
                if line.startswith("parent ")] != [CANDIDATE_BASE_SHA]:
            raise RuntimeError("Corrected game must be a genuine sole child of original #396")
        source_tree, candidate_tree = tree(self.source), tree(self.candidate)
        base_tree = tree(self.candidate, CANDIDATE_BASE_SHA)
        prior_tree = tree(self.candidate, PRIOR_CANDIDATE_SHA)
        base_delta = {name for name in base_tree.keys() | candidate_tree.keys()
                      if base_tree.get(name) != candidate_tree.get(name)}
        prior_delta = {name for name in base_tree.keys() | prior_tree.keys()
                       if base_tree.get(name) != prior_tree.get(name)}
        receiving_delta = {name for name in prior_tree.keys() | candidate_tree.keys()
                           if prior_tree.get(name) != candidate_tree.get(name)}
        game_delta = {name for name in base_tree.keys() | source_tree.keys()
                      if base_tree.get(name) != source_tree.get(name)}
        delta = {name for name in source_tree.keys() | candidate_tree.keys()
                 if source_tree.get(name) != candidate_tree.get(name)}
        if (base_delta != OWNED_PATHS or prior_delta != OWNED_PATHS
                or receiving_delta != OWNED_PATHS or game_delta != {GROUND_PATH}
                or delta != OWNED_PATHS | {GROUND_PATH}
                or any(name in base_tree or name in source_tree for name in OWNED_PATHS)
                or any(prior_tree.get(name, (None,))[0] != "100644" for name in OWNED_PATHS)
                or base_tree.get(GROUND_PATH) != ("100644", CANDIDATE_GROUND_BLOB)
                or candidate_tree.get(GROUND_PATH) != ("100644", CANDIDATE_GROUND_BLOB)
                or source_tree.get(GROUND_PATH) != ("100644", GROUND_BLOB)):
            raise RuntimeError(f"Candidate cumulative scope differs: {sorted(delta)}")
        candidate_rows = {}
        for name in sorted(OWNED_PATHS):
            p = self.candidate / name
            if p.is_symlink() or p.stat().st_nlink != 1 or candidate_tree[name] != ("100644", blob(p)):
                raise RuntimeError("Candidate executable source differs from immutable event tree")
            target = self.evidence / Path(name).name
            shutil.copyfile(p, target)
            candidate_rows[name] = {"blob": blob(p), "sha256": digest(p)}
        self.candidate_initial = candidate_rows
        # Project checkout is the new physical project, NOT a link/copy of any donor.
        self.initial = self.snapshot()
        write_json(self.evidence / "source-before.json", self.initial)
        write_json(self.evidence / "candidate.json", {"event_sha": self.event_sha,
                   "tree": git(self.candidate, "rev-parse", "HEAD^{tree}").decode().strip(),
                   "commit_headers": headers, "history_headers": history_headers,
                   "candidate_base_sha": CANDIDATE_BASE_SHA, "candidate_base_tree": CANDIDATE_BASE_TREE,
                   "prior_candidate_sha": PRIOR_CANDIDATE_SHA, "prior_candidate_tree": PRIOR_CANDIDATE_TREE,
                   "tested_game_sha": GAME_SHA, "tested_game_tree": GAME_TREE,
                   "tested_game_headers": source_headers, "base_delta": sorted(base_delta),
                   "receiving_delta": sorted(receiving_delta), "game_delta": sorted(game_delta),
                   "delta": sorted(delta), "tested_source_parent": "separate corrected checkout; workflow retains original game"})
        # Retain full actual game AND actual Python inputs before engine setup.
        # The snapshot describes these bytes, never an invented successful import.
        with tarfile.open(self.evidence / "source-inputs.tar.gz", "x:gz") as archive:
            for number, name in enumerate(sorted(self.initial["game"] | self.initial["python_closure"])):
                archive.add(self.source / name, arcname=name, recursive=False)
                if number % 128 == 0:
                    self.capacity()
        self.capacity()
        roots = {"XDG_CONFIG_HOME": self.root / "config",
                 "XDG_DATA_HOME": self.root / "data", "XDG_CACHE_HOME": self.root / "cache",
                 "XDG_RUNTIME_DIR": self.root / "runtime", "TMPDIR": self.root / "tmp"}
        self.env = {**os.environ, **{k: str(v) for k, v in roots.items()},
                    "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1",
                    "PYTHON": str(Path(sys.executable).resolve(strict=True)),
                    "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
        # Preserve inherited proxies/CA bindings; never dump ambient credentials.
        for p in roots.values():
            p.mkdir(mode=0o700)
        write_json(self.evidence / "private-roots.json", {k: str(v) for k, v in roots.items()})
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER, owns only this controller's descendants
            raise OSError(ctypes.get_errno(), "Cannot establish actual orphan collection")
        write_json(self.evidence / "host.json", {"python": sys.version, "platform": platform.platform(),
                   "affinity": sorted(os.sched_getaffinity(0)),
                   "validator_python": self.env["PYTHON"],
                   "fit": "UNMEASURED; no automatic budget increase",
                   "limits": {
                       "rss_group_bytes": RSS_LIMIT, "owned_bytes": OWNED_LIMIT,
                       "reserve_bytes": FREE_RESERVE, "log_phase_bytes": LOG_LIMIT},
                   "rss_qualification": "Linux /proc aggregate group RSS sampled in the monitor loop (50ms select interval; IO can extend it). Actual maximum monitor gap is recorded; observed overshoot fails."})
        self.get_engine()

    def get_engine(self) -> None:
        # A partial/mismatching download is part of failure evidence, not a lost temp file.
        archive = self.evidence / "engine-download.zip"
        started = time.monotonic()
        downloaded = 0
        try:
            with urllib.request.urlopen(ENGINE_URL, timeout=30) as response, archive.open("xb") as output:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    downloaded += len(chunk)
                    if downloaded > 100 * 1024**2 or time.monotonic() - started > 120:
                        raise RuntimeError("Pinned engine download exceeded bounded setup")
                    output.write(chunk)
                    self.capacity()
        finally:
            write_json(self.evidence / "engine-download.json", {"url": ENGINE_URL,
                       "received_bytes": downloaded, "elapsed_s": time.monotonic() - started,
                       "retained_bytes": archive.stat().st_size if archive.exists() else 0,
                       "retained_sha512": digest(archive, "sha512") if archive.exists() else None,
                       "expected_sha512": ARCHIVE_SHA512})
        actual_archive = digest(archive, "sha512")
        write_json(self.evidence / "engine-download.json", {"url": ENGINE_URL, "bytes": downloaded,
                   "sha512": actual_archive, "expected_sha512": ARCHIVE_SHA512})
        if actual_archive != ARCHIVE_SHA512:
            raise RuntimeError("Official pinned archive unavailable/mismatch; no substitution")
        self.engine.parent.mkdir(mode=0o700)
        with zipfile.ZipFile(archive) as packed:
            matches = [x for x in packed.infolist() if x.filename == ENGINE_NAME]
            if len(matches) != 1 or matches[0].is_dir() or matches[0].file_size != ENGINE_BYTES:
                raise RuntimeError("Pinned archive member differs")
            with packed.open(matches[0]) as src, self.engine.open("xb") as dst:
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    dst.write(chunk)
                    self.capacity()
        self.engine.chmod(0o700)
        if digest(self.engine) != ENGINE_SHA256 or self.engine.stat().st_nlink != 1:
            raise RuntimeError("Pinned physical executable bytes mismatch")
        if set(self.engine.parent.iterdir()) != {self.engine}:
            raise RuntimeError("Portable marker/settings beside copied executable")
        self.engine_guard = {"bytes": self.engine.stat().st_size, "sha256": digest(self.engine)}
        write_json(self.evidence / "engine.json", self.engine_guard)
        # Retire only this verified, task-owned download after retaining exact hashes.
        # No original/donor/cache path is removed. Mismatching downloads remain intact.
        archive.unlink()
        self.output["verified_download_retired"] = True
        self.capacity()

    def phase(self, name: str, command: list[str], seconds: int) -> dict:
        result = {"state": "STARTING", "command": command, "timeout_seconds": seconds,
                  "started_at": time.time(), "wait4": [], "limits": [], "peak_sampled_group_rss": 0}
        self.phases[name] = result
        write_json(self.evidence / (name + ".json"), result)
        log_path = self.evidence / (name + ".log")
        process = None
        selector = selectors.DefaultSelector()
        reason = None
        started = time.monotonic()
        previous_sample = started
        result["max_monitor_gap_s"] = 0.0
        try:
            self.capacity()
            process = subprocess.Popen(command, cwd=self.game, env=self.env, start_new_session=True,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            result["pid"] = result["pgid"] = process.pid
            leader = proc_group(process.pid).get(process.pid)
            if leader is None:
                raise RuntimeError("Cannot retain owned leader identity")
            result["leader_start_ticks"] = leader["start"]
            os.set_blocking(process.stdout.fileno(), False)
            selector.register(process.stdout, selectors.EVENT_READ)
            eof = False
            ended_at = None
            total = 0
            next_disk_check = started
            with log_path.open("xb") as log:
                while True:
                    now = time.monotonic()
                    result["max_monitor_gap_s"] = max(result["max_monitor_gap_s"], now - previous_sample)
                    previous_sample = now
                    members = proc_group(process.pid)
                    rss = sum(int(x["rss"]) for x in members.values())
                    result["peak_sampled_group_rss"] = max(result["peak_sampled_group_rss"], rss)
                    if rss > RSS_LIMIT:
                        reason = "group RSS limit"; break
                    if now - started > seconds:
                        reason = "phase timeout"; break
                    if now >= next_disk_check:
                        self.capacity()
                        next_disk_check = now + 0.5
                    # WNOWAIT preserves the leader/PGID until last group disposition.
                    terminal = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                    if terminal is not None and ended_at is None:
                        ended_at = now
                    for key, _mask in selector.select(0.05):
                        data = os.read(key.fileobj.fileno(), 65536)
                        if not data:
                            eof = True
                            selector.unregister(key.fileobj)
                        else:
                            remaining = LOG_LIMIT - total
                            log.write(data[:remaining]); total += min(remaining, len(data))
                            if len(data) > remaining:
                                reason = "raw log limit; retained prefix is incomplete"
                                break
                    if reason:
                        break
                    if ended_at is not None and (eof or now - ended_at > 1):
                        break
            result["remaining_before_cleanup"] = proc_group(process.pid)
            if any(x["state"] != "Z" for pid, x in result["remaining_before_cleanup"].items() if pid != process.pid):
                reason = reason or "owned descendants survived leader"
        except BaseException as error:
            reason = f"controller/prerequisite failure: {type(error).__name__}: {error}"
        finally:
            selector.close()
            if process is not None:
                # Never poll/wait/reap the leader before this last group kill: no PGID reuse window.
                try:
                    # A waitable direct child remains reserved even if initial /proc
                    # inspection failed. Never let early monitoring failure skip cleanup.
                    os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                    if os.getpgid(process.pid) != process.pid:
                        raise RuntimeError("Owned child is not its session/group leader")
                    held = proc_group(process.pid).get(process.pid)
                    if held is None or (result.get("leader_start_ticks") is not None and
                                        held["start"] != result["leader_start_ticks"]):
                        reason = reason or "leader identity read failed; direct child still waitable"
                    for sig, grace in ((signal.SIGTERM, 0.25), (signal.SIGKILL, 0.0)):
                        try:
                            os.killpg(process.pid, sig)
                        except ProcessLookupError:
                            pass
                        if grace:
                            time.sleep(grace)
                    try:
                        deadline = time.monotonic() + 5
                        while True:
                            pid, status, usage = os.wait4(process.pid, os.WNOHANG)
                            if pid or time.monotonic() >= deadline:
                                break
                            time.sleep(0.02)
                        if not pid:
                            raise RuntimeError("Owned leader wait4 collection deadline")
                        process.returncode = os.waitstatus_to_exitcode(status)
                        result["exit"] = process.returncode
                        result["wait4"].append({"pid": pid, "status": status,
                            "exit": process.returncode, "user_s": usage.ru_utime,
                            "system_s": usage.ru_stime, "maxrss_kib": usage.ru_maxrss})
                    except ChildProcessError:
                        reason = reason or "leader actual wait4 unavailable"
                    end = time.monotonic() + 5
                    result["escaped_children"] = []
                    while True:
                        children = direct_children()
                        for child_pid, identity in children.items():
                            if identity["pgid"] == process.pid or identity["state"] == "Z":
                                continue
                            reason = reason or "owned descendant escaped process group"
                            # Adopted direct children only, bound by a pidfd; no numeric
                            # group signal after leader reaping and no unrelated-PID kill.
                            try:
                                fd = os.pidfd_open(child_pid, 0)
                                try:
                                    current = direct_children().get(child_pid)
                                    if current is None or (current["start"], current["pgid"]) != (identity["start"], identity["pgid"]):
                                        raise RuntimeError("Escaped-child identity changed")
                                    signal.pidfd_send_signal(fd, signal.SIGKILL)
                                    result["escaped_children"].append({"pid": child_pid, **identity, "kill": "sent via pidfd"})
                                finally:
                                    os.close(fd)
                            except ProcessLookupError:
                                result["escaped_children"].append({"pid": child_pid, **identity, "kill": "already exited"})
                        try:
                            pid, status, usage = os.wait4(-1, os.WNOHANG)
                        except ChildProcessError:
                            pid = 0
                        if pid:
                            result["wait4"].append({"pid": pid, "status": status,
                                "exit": os.waitstatus_to_exitcode(status), "user_s": usage.ru_utime,
                                "system_s": usage.ru_stime, "maxrss_kib": usage.ru_maxrss})
                        remaining = proc_group(process.pid)
                        if (not remaining and not direct_children()) or time.monotonic() >= end:
                            break
                        time.sleep(0.02)
                    result["remaining_after_collection"] = remaining
                    result["direct_children_after_collection"] = direct_children()
                    if remaining or result["direct_children_after_collection"]:
                        reason = reason or "owned process group not absent after collection"
                except BaseException as error:
                    reason = reason or f"actual group cleanup/collection failed: {error!r}"
                finally:
                    # A wait deadline/cleanup exception must still retain the actual
                    # remaining-process evidence; it never proves runtime release.
                    try:
                        result["remaining_after_collection"] = proc_group(process.pid)
                        result["direct_children_after_collection"] = direct_children()
                        if result["remaining_after_collection"] or result["direct_children_after_collection"]:
                            reason = reason or "owned runtime not fully collected"
                    except BaseException as error:
                        result["final_process_snapshot_error"] = repr(error)
                        reason = reason or "final process absence unproven"
                if process.stdout is not None:
                    process.stdout.close()
            result.update(state="FAILED" if reason else "COLLECTED", controller_error=reason,
                          elapsed_s=time.monotonic() - started, finished_at=time.time())
            if log_path.exists():
                result.update(log_sha256=digest(log_path), log_bytes=log_path.stat().st_size)
            write_json(self.evidence / (name + ".json"), result)
        return result

    def require_clean(self, name: str, result: dict) -> str:
        path = self.evidence / (name + ".log")
        text = diagnostic_text(path) if path.exists() else ""
        if result.get("exit") != 0 or result["state"] != "COLLECTED" or ERROR_PATTERN.search(text) or orphan_diagnostics(text):
            raise RuntimeError(f"{name} prerequisite failed; preserve raw errors even exit0: {result.get('controller_error')}")
        return text

    def canary(self) -> None:
        probe = self.root / "probe"
        plugin = probe / "addons/editor_dependents_paths"
        plugin.mkdir(parents=True)
        (probe / "project.godot").write_text('config_version=5\n[application]\nconfig/name="EDITOR_DEPENDENTSPathCanary"\n[editor_plugins]\nenabled=PackedStringArray("res://addons/editor_dependents_paths/plugin.cfg")\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
        (plugin / "plugin.cfg").write_text('[plugin]\nname="EDITOR_DEPENDENTSPathCanary"\ndescription="Private engine path canary"\nauthor="MyGame"\nversion="1"\nscript="paths.gd"\n')
        (plugin / "paths.gd").write_text(PROBE)
        output = self.evidence / "actual-engine-paths.json"
        self.env["EDITOR_DEPENDENTS_CANARY_OUTPUT"] = str(output)
        result = self.phase("canary", [str(self.engine), "--headless", "--audio-driver", "Dummy",
                                      "--editor", "--path", str(probe)], 20)
        self.require_clean("canary", result)
        paths = json.loads(output.read_text())
        if paths["self_contained"] or paths["portable_marker"]:
            raise RuntimeError("Actual engine is self-contained")
        if tuple(paths["version"].get(k) for k in ("major", "minor", "patch")) != (4, 7, 2):
            raise RuntimeError("Actual pinned engine version differs")
        expected = {"os_config": self.root / "config", "os_data": self.root / "data",
                    "os_cache": self.root / "cache", "editor_config": self.root / "config/godot",
                    "editor_data": self.root / "data/godot", "editor_cache": self.root / "cache/godot",
                    "project_settings": probe / ".godot/editor", "executable": self.engine}
        for key, path in expected.items():
            if Path(paths[key]).resolve() != path.resolve():
                raise RuntimeError(f"Actual {key} escapes expected private location")
        for key in ("os_user", "user_uri"):
            if not Path(paths[key]).resolve().is_relative_to((self.root / "data").resolve()):
                raise RuntimeError(f"Actual {key} escapes private data")
        settings = Path(paths["settings_resource"]).resolve(strict=True)
        if not settings.is_relative_to((self.root / "config/godot").resolve()) or not settings.is_file() or settings.stat().st_size == 0:
            raise RuntimeError("Actual settings resource/file not private")
        self.guards["actual_engine_containment"] = {"state": "PASS", "settings_sha256": digest(settings)}

    def reconcile(self, result: dict) -> None:
        """Read this vendored writer's actual XML; fail-fast omissions are NOTRUN."""
        self.output["state"] = "FOCUSED_RESULTS_UNCLASSIFIED"
        reports = self.game / REPORT_DIR
        files = sorted(reports.rglob("results.xml")) if reports.exists() else []
        text = diagnostic_text(self.evidence / "focused.log")
        findings = {
            "expected": list(METHODS), "observed": [], "methods": {m: "NOTRUN" for m in METHODS},
            "raw_error_headers": [line for line in text.splitlines() if ERROR_PATTERN.search(line)],
            "python_validator_errors": [line for line in text.splitlines() if PYTHON_ERROR_PATTERN.search(line)],
            "orphan_diagnostics": orphan_diagnostics(text), "totals": [],
            "xml_files": [str(p.relative_to(self.game)) for p in files], "case_evidence": [],
        }
        # Write an inventory even if XML is absent, malformed or only partial.
        try:
            if len(files) != 1:
                raise RuntimeError("Need exactly one fresh vendored JUnit results.xml")
            root = ET.parse(files[0]).getroot()
            suites = list(root.findall("testsuite"))
            suite_name = "test_world_editor_dependent_edits"
            if (root.tag != "testsuites" or len(suites) != 1
                    or suites[0].get("package") != "test"
                    or suites[0].get("name") != suite_name):
                raise RuntimeError("JUnit does not identify the sole requested editor suite")
            suite = suites[0]
            # The pinned writer emits declared/discovered tests=8 even when
            # fail-fast stops after the first failing case. Actual testcase
            # children, not that total, determine which methods ran.
            for element in (root, suite):
                values = {key: int(element.get(key, "0"))
                          for key in ("tests", "failures", "errors", "skipped", "flaky")}
                findings["totals"].append(values)
                if values["tests"] != len(METHODS) or any(values[k] for k in ("errors", "skipped", "flaky")):
                    raise RuntimeError("Wrong discovery totals or XML errors/skips/flaky")
            cases = list(suite.findall("testcase"))
            names = [case.get("name", "") for case in cases]
            findings["observed"] = names
            if not names or names != list(METHODS[:len(names)]):
                raise RuntimeError("Unexpected/duplicate/non-prefix methods; not fail-fast evidence")
            if list(root.iter("testcase")) != cases:
                raise RuntimeError("Unexpected testcase outside the sole requested suite")
            failed = []
            failure_count = 0
            for case in cases:
                name = case.get("name")
                failures = case.findall("failure")
                errors, skipped = case.findall("error"), case.findall("skipped")
                evidence = {
                    "method": name, "classname": case.get("classname"),
                    "failures": [dict(node.attrib, text=node.text or "") for node in failures],
                    "errors": [dict(node.attrib, text=node.text or "") for node in errors],
                    "skipped": [dict(node.attrib, text=node.text or "") for node in skipped],
                }
                findings["case_evidence"].append(evidence)
                if case.get("classname") != suite_name or errors or skipped:
                    raise RuntimeError("Case identity/error/skip is not editor assertion evidence")
                if any(node.get("type") != "FAILURE" for node in failures):
                    raise RuntimeError("Orphan/termination/interruption is not a target assertion")
                findings["methods"][name] = "FAIL" if failures else "PASS"
                if failures:
                    failed.append(name)
                failure_count += len(failures)
            # GdUnit counts failed assertions, not necessarily failed methods.
            if any(total["failures"] != failure_count for total in findings["totals"]):
                raise RuntimeError("XML aggregate failures disagree with actual failure elements")
            if (result["state"] != "COLLECTED" or result.get("exit") is None
                    or findings["raw_error_headers"] or findings["python_validator_errors"]
                    or findings["orphan_diagnostics"]):
                raise RuntimeError("Controller/raw engine/Python/orphan errors are not target editor RED")
            if findings["methods"][METHODS[0]] != "PASS":
                raise RuntimeError("Real intake/adapter startup failed; no target editor RED")
            if not failed:
                if names != list(METHODS) or result["exit"] != 0:
                    raise RuntimeError("Incomplete success/exit is not eight passing methods")
                self.output["state"] = "EIGHT_FOCUSED_PASS"
                self.output["focused_suite_pass"] = True
            elif failed == [names[-1]] and result["exit"] == 100:
                # Preserve a real assertion FAIL without calling unrelated fixture
                # or rule failures the hypothesised stale-bake production defect.
                name = failed[0]
                failures = cases[-1].findall("failure")
                message = STALE_BAKE_MESSAGES.get(name)
                target = bool(message) and all(
                    message in (node.text or "")
                    and node.get("message", "").startswith("FAILED: res://" + TEST_PATH.removeprefix("game/") + ":")
                    for node in failures
                )
                self.output["state"] = ("STALE_BAKE_ASSERTION_RED_REQUIRES_LEAD_REVIEW" if target
                                        else "OTHER_EDITOR_ASSERTION_FAIL_REQUIRES_LEAD_REVIEW")
            else:
                raise RuntimeError("Failure/exit does not match actual fail-fast assertion semantics")
        finally:
            findings["classification"] = self.output["state"]
            write_json(self.evidence / "focused-inventory.json", findings)

    def run(self) -> int:
        failure = None
        try:
            self.setup()
            self.canary()
            self.require_clean("import", self.phase("import", [str(self.engine), "--headless", "--audio-driver", "Dummy",
                                                             "--path", str(self.game), "--import"], 180))
            self.require_clean("check-only", self.phase("check-only", [
                str(self.engine), "--headless", "--audio-driver", "Dummy",
                "--path", str(self.game), "--check-only", "--script",
                "res://" + TEST_PATH.removeprefix("game/")], 20))
            self.reconcile(self.phase("focused", [str(self.engine), "--headless", "--audio-driver", "Dummy",
                "--path", str(self.game), "-s", "res://addons/gdUnit4/bin/GdUnitCmdTool.gd",
                "--ignoreHeadlessMode", "-a", "res://" + TEST_PATH.removeprefix("game/"), "-rd", REPORT_DIR], 90))
        except BaseException as error:
            failure = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
            self.output["state"] = "PREREQUISITE_OR_NON_TARGET_FAILURE"
        finally:
            # Independent final retention attempts; one failing guard must not suppress other evidence.
            final_errors = []
            if self.candidate_initial is not None:
                try:
                    actual = {name: {"blob": blob(self.candidate / name), "sha256": digest(self.candidate / name)}
                              for name in sorted(OWNED_PATHS)}
                    write_json(self.evidence / "candidate-after.json", actual)
                    if actual != self.candidate_initial or git(self.candidate, "rev-parse", "HEAD").decode().strip() != self.event_sha:
                        raise RuntimeError("Workflow/controller source changed")
                    self.guards["candidate"] = "PASS"
                except BaseException as error:
                    final_errors.append(repr(error))
            if self.initial is not None:
                try:
                    after = self.snapshot()
                    write_json(self.evidence / "source-after.json", after)
                    if after != self.initial:
                        raise RuntimeError("Tracked game/Python inputs/index changed during validation")
                    self.guards["frozen_game"] = "PASS"
                except BaseException as error:
                    final_errors.append(repr(error))
            try:
                if self.engine.exists():
                    after_engine = {"bytes": self.engine.stat().st_size, "sha256": digest(self.engine)}
                    write_json(self.evidence / "engine-after.json", after_engine)
                    if after_engine != getattr(self, "engine_guard", None) or set(self.engine.parent.iterdir()) != {self.engine}:
                        raise RuntimeError("Engine/marker guard changed")
                    self.guards["engine"] = "PASS"
            except BaseException as error:
                final_errors.append(repr(error))
            try:
                reports = self.game / "reports-editor-dependents"
                if reports.exists():
                    shutil.copytree(reports, self.evidence / "gdunit-reports")
                uid = self.source / (TEST_PATH + ".uid")
                if uid.exists():
                    shutil.copyfile(uid, self.evidence / uid.name)
                self.output["final_capacity"] = self.capacity()
            except BaseException as error:
                final_errors.append(repr(error))
            self.output.update(failure=failure, final_errors=final_errors, finished_at=time.time(),
                               gui_workflow_pass=False, production_correction_authorised=False)
            if final_errors:
                self.output["state"] = "FINAL_GUARD_OR_COLLECTION_FAILURE"
            write_json(self.evidence / "result.json", self.output)
            manifest = {str(p.relative_to(self.evidence)): {"bytes": p.stat().st_size, "sha256": digest(p)}
                        for p in sorted(self.evidence.rglob("*")) if p.is_file() and not p.is_symlink()}
            write_json(self.evidence / "evidence-manifest.json", manifest)
        # Only actual eight-method green with all final guards can succeed.
        # A RED, partial fail-fast, setup or collection failure remains nonzero.
        return 0 if self.output["state"] == "EIGHT_FOCUSED_PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--event-sha", required=True)
    args = parser.parse_args()
    def interrupted(signum: int, _frame: object) -> None:
        raise InterruptedError(f"Controller received signal {signum}; retain/collect owned children")
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    return Controller(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
