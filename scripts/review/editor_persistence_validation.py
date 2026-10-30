#!/usr/bin/env python3
"""Bounded EDITOR-PERSISTENCE receiver; SOURCE ONLY until exact lead allocation.

Adapted from reviewed #402 c2cd7baa (controller blob f40ef659), originally #401.
Reuse #402 c2cd7baa private-engine/actual-wait collection. Immutable #398 game,
six Python and two GdUnit persistence methods; no displayed GUI, complete editor,
nonempty-piece/cell-coordinate, full-suite or acceptance inference.
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
import resource
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

GAME_SHA = "6903f8d5d729f5eb9d4beef20d33869465308c66"
GAME_TREE = "e4dfae3eb183426e3a44fd004436eb1ed18b53d7"
GAME_PARENT = "45ed3cad029c106977e6c0c833913dcb1c614fbd"
TEST_BLOB = "a61671b648277d1c2ba290de51cdff74b475a1c9"
PRODUCTION_BLOB = "effd244781b1e71c5d990b14df82258280e93811"
GAME_COUNT = 6688
GAME_BYTES = 87857335
# Static import/data closure of unchanged bake, validator and exact tiny fixture.
# Full game supplies library/schema/terrain/index/fixtures. No master raster is
# reached by this pieces=[] lawn-only probe. scripts/art are namespace packages.
PYTHON_INPUTS = {'.github/workflows/verify.yml': ('97a2d95b8b5d6c801ad0258cf44cbb6474a07a1e', 2165),
 'art/house-palette.json': ('7e97a7463b3641425e667d7b7764f34510489a54', 20444),
 'art/scenes/woodland.json': ('4ddc7ed7b91d413f897388969579b4d06a2a7486', 31704),
 'scripts/art/biomes/woodland.json': ('6da96e5aa39b945288b2a71e826e7e6b535a7559', 8822),
 'scripts/art/house_palette.py': ('8a816d1799abd1fc22931a2c93fbe620a14a200e', 17753),
 'scripts/art/kit/__init__.py': ('e69de29bb2d1d6434b8b29ae775ad8c2e48c5391', 0),
 'scripts/art/kit/bake.py': ('f881fbd63808b8e5c4f77cae6b53780550e9c7e6', 24361),
 'scripts/art/kit/build.py': ('054206b5ea00d227ae0a33075a0b0b2e0355d4b5', 18911),
 'scripts/art/kit/compose.py': ('4435017b23a5d50ed0a5e8801abc536b84854416', 12458),
 'scripts/art/kit/dressing.py': ('e4b4db15f45a0f1e202012a7c8d506e6f4970c5f', 8356),
 'scripts/art/kit/edges.py': ('28fdf16622c7a0bed0f8d427e2ed6938fc7bcd69', 23944),
 'scripts/art/kit/fills.py': ('3cbde218f4ea757a7327887060a60dfd65138df4', 18297),
 'scripts/art/kit/relations.py': ('dd6b718b24f9f681cd5450ecbb0216e6a1ae8420', 19542),
 'scripts/art/kit/schema.py': ('056c1f9a30d49e203badd97624458130c79c81b2', 14148),
 'scripts/art/kit/structures.py': ('6a2a9e4f1a70802fed4abef4e37b22ddc7d3354c', 15623),
 'scripts/art/kit/surface.py': ('fb9b1688e8352350845d5669135e83cecfce8bf3', 22240),
 'scripts/art/kit/test_bake_publication.py': ('09c5502d10976aa083cc7ac95b6e06858d0af70e', 12505),
 'scripts/art/native/__init__.py': ('424a4a68c50941eb2550d4bcbdd8dff8fd5c37b9', 2747),
 'scripts/art/native/accents.json': ('d612eb0e6c3eb7eedf8cf878186c26bc1aaa9486', 921),
 'scripts/art/native/animate.py': ('a18a7df99b9e351aabc3155ac901877c5a668369', 5604),
 'scripts/art/native/chars.py': ('864c53227701a7a7c346ab41de75664650f40d81', 23727),
 'scripts/art/native/compose.py': ('b6abc53b110b870c82755ce149e71c93448c2b6b', 29597),
 'scripts/art/native/ctx.py': ('c79cfda10603fcc7092a4b879dc552c01d88f6c1', 1506),
 'scripts/art/native/foliage.py': ('53a1b9800f139fa2afe42ace29b89a71843cda00', 40423),
 'scripts/art/native/ground.py': ('c74a4b8ffed4f48c2f7e6cc6e0a0d200407069f9', 5072),
 'scripts/art/native/palette.py': ('7685bc30fa29bf2c6fe87cfdc4e2ecae2f908b28', 6189),
 'scripts/art/native/props.py': ('4a7396cac80431c1080d62510cbd9c2fa7a30132', 84233),
 'scripts/art/native/raster.py': ('5b19ed242b81eb492bf38b422993b398be30b764', 16968),
 'scripts/art/native/rig.py': ('0cdc88a77ac6d8c9c5ca0764f03f60fd99f1f203', 7427),
 'scripts/art/native/rocks.py': ('915357f9e61528d1c296ab41533cca6fdffcc276', 21773),
 'scripts/art/native/screen.py': ('a7e04486c835a87f281e3785bbabde1e72df178e', 73374),
 'scripts/art/native/softedge.py': ('d57d6e1a875e3b9c5aa78d2768af5f8a46c20b1e', 5048),
 'scripts/art/native/softgrid.py': ('365cdd330b3a1628a1e7eca1114648262a506dab', 27518),
 'scripts/art/native/softground.py': ('6ad07c557eefa864f1140332e382b2ef8f3101a1', 112143),
 'scripts/art/native/terrain/__init__.py': ('955bbcf2a5172718655203a0cc8f6d08671b60ee', 2792),
 'scripts/art/native/terrain/decals.py': ('fbbac154045fa4e1205561ad21554838c79874a4', 8622),
 'scripts/art/native/terrain/noise.py': ('0d879d5d85126774b9df5b1b11fa81d88037cc10', 1660),
 'scripts/art/native/terrain/scene.py': ('406f9f63e988bfb1fe8410dbffd444116d555915', 81041),
 'scripts/art/native/terrain/sheets.py': ('1c2072d629a5c7f259b93fd303061826e255999d', 43948),
 'scripts/art/native/terrain/tiles.py': ('e0d05e1c0ddc525a4dd952ae557353178d3a5e2f', 45209),
 'scripts/art/native/village.py': ('78f5e5c48602242d26a52f2e0ce9dbd37610d999', 178366),
 'scripts/art/native/water.py': ('8a18feda4c9d6f8580471a61157529ad8293c637', 22027),
 'scripts/art/pixel.py': ('bc0112b14f9eba4f5b8cf6ff18309603826f8c81', 7894),
 'scripts/art/size_guide.json': ('f30ecb3249d771e5dc6cdf6546d50400b118cf57', 45069),
 'scripts/art/water_flow.py': ('4e1ebf799cae783c35642f6c1b9e34463ed300e0', 8888),
 'scripts/review/__init__.py': ('e69de29bb2d1d6434b8b29ae775ad8c2e48c5391', 0),
 'scripts/review/ground_rules.py': ('0bfe3fff9d74f3b1ecd07afe1ff27b0940143f68', 18956),
 'scripts/review/kit_scene.py': ('6c71732fb52cbe86e8fa723c4d09a0af4d553371', 28305)}
PYTHON_COUNT = 48
PYTHON_BYTES = 1228320
TEST_PATH = "game/test/test_kit_zone_persistence.gd"
REPORT_DIR = "reports-editor-persistence"
DEPENDENCIES = {"Pillow": "12.3.0", "numpy": "2.5.3", "scipy": "1.18.1"}
PY_MODULE = "scripts.art.kit.test_bake_publication"
PY_CANARIES = ("Canary.test_real_tiny_bake_and_current_check",
               "ExportCLI.test_cli_canary_build_export_rebuild")
PY_FAULTS = ("PublicationFaults.test_failed_png_write_cannot_remain_current",
             "PublicationFaults.test_failed_second_bake_does_not_advertise_mixed_generation",
             "ExportCLI.test_rejected_export_preserves_previous_valid_document",
             "ExportCLI.test_kernel_interrupted_export_preserves_or_recovers_document")
ASSERTION_BOUNDARIES = {
    PY_FAULTS[0]: ("failed publication was advertised current",),
    PY_FAULTS[1]: ("failed publication was advertised current",),
    PY_FAULTS[2]: ("invalid export accepted", "rejection overwrote valid output"),
    PY_FAULTS[3]: ("no previous valid document or recoverable published document",),
}
ENGINE_SHA256 = "8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e"
ENGINE_BYTES = 146414384
ARCHIVE_SHA512 = "9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65"
ENGINE_NAME = "Godot_v4.7.2-stable_linux.x86_64"
ENGINE_URL = "https://github.com/godotengine/godot/releases/download/4.7.2-stable/" + ENGINE_NAME + ".zip"
OWNED_LIMIT = 512 * 1024**2
FREE_RESERVE = 256 * 1024**2
RSS_LIMIT = 2048 * 1024**2
LOG_LIMIT = 4 * 1024**2
OWNED_PATHS = {".github/workflows/editor-persistence-validation.yml",
               "scripts/review/editor_persistence_validation.py"}
METHODS = (
    "test_minimal_authored_zone_survives_disk_export_and_rebuild",
    "test_native_deletions_and_literal_ids_survive_two_saved_generations",
)
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
    var file = FileAccess.open(OS.get_environment("EDITOR_PERSISTENCE_CANARY_OUTPUT"), FileAccess.WRITE)
    if file == null:
        push_error("EDITOR_PERSISTENCE canary output open failed")
        get_tree().quit(2)
        return
    file.store_string(JSON.stringify(out) + "\\n")
    file.close()
    print("EDITOR_PERSISTENCE_CANARY_PATHS=" + JSON.stringify(out))
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


PYTHON_OBSERVER = "import json, os, sys, traceback, unittest\nfrom pathlib import Path\n\nselectors = json.loads(sys.argv[1])\noutput = Path(sys.argv[2])\nbase = Path(os.environ['PERSISTENCE_OUT'])\nstate = {'expected': selectors, 'observed': [], 'methods': {n: {'state': 'NOTRUN'} for n in selectors}}\nclass Result(unittest.TextTestResult):\n    def startTest(self, test):\n        self.current = test.id().removeprefix('scripts.art.kit.test_bake_publication.')\n        self.before = set(base.iterdir())\n        state['observed'].append(self.current)\n        state['methods'][self.current] = {'state': 'STARTED', 'id': test.id()}\n        output.write_text(json.dumps(state, indent=2) + '\\n')\n        super().startTest(test)\n    def addSuccess(self, test):\n        state['methods'][self.current]['state'] = 'PASS'\n        super().addSuccess(test)\n    def addFailure(self, test, err):\n        state['methods'][self.current].update(state='FAIL', exception_type=err[0].__name__,\n            message=str(err[1]), traceback=''.join(traceback.format_exception(*err)))\n        super().addFailure(test, err)\n    def addError(self, test, err):\n        state['methods'][self.current].update(state='ERROR', exception_type=err[0].__name__,\n            message=str(err[1]), traceback=''.join(traceback.format_exception(*err)))\n        super().addError(test, err)\n    def addSkip(self, test, reason):\n        state['methods'][self.current].update(state='SKIP', reason=reason)\n        super().addSkip(test, reason)\n    def addSubTest(self, test, subtest, err):\n        if err is not None:\n            state['methods'][self.current].update(state='ERROR', message='unexpected subtest',\n                traceback=''.join(traceback.format_exception(*err)))\n        super().addSubTest(test, subtest, err)\n    def stopTest(self, test):\n        state['methods'][self.current]['evidence_roots'] = [str(p) for p in sorted(set(base.iterdir()) - self.before)]\n        output.write_text(json.dumps(state, indent=2) + '\\n')\n        super().stopTest(test)\ntry:\n    suite = unittest.defaultTestLoader.loadTestsFromNames(\n        ['scripts.art.kit.test_bake_publication.' + n for n in selectors])\n    result = unittest.TextTestRunner(verbosity=2, failfast=True, resultclass=Result).run(suite)\n    state['success'] = result.wasSuccessful()\n    state['testsRun'] = result.testsRun\nexcept BaseException:\n    state['harness_error'] = traceback.format_exc()\n    raise\nfinally:\n    output.write_text(json.dumps(state, indent=2) + '\\n')\nsys.exit(0 if state.get('success') else 1)\n"

class Controller:
    def __init__(self, args: argparse.Namespace):
        self.candidate = args.candidate.resolve(strict=True)
        self.source = args.source.resolve(strict=True)
        self.root = args.root.resolve(strict=True)
        self.game = self.source / "game"
        self.evidence = self.root / "evidence"
        self.event_sha = args.event_sha
        self.phases = {name: {"state": "NOT RUN"} for name in ("dependencies", "versions", "canary", "import", "check-only", "python-canaries", "focused", "python-faults")}
        self.guards = {}
        self.engine = self.root / "engine" / ENGINE_NAME
        self.initial = None
        self.candidate_initial = None
        self.output = {"state": "SETUP_FAILED", "workflow_sha": self.event_sha,
                       "tested_game_sha": GAME_SHA, "tested_game_tree": GAME_TREE,
                       "phases": self.phases, "guards": self.guards,
                       "qualification": "Eight unexecuted controls until this exact allocated invocation. No displayed GUI/full-suite/Ready/whole-editor acceptance."}
        self.output["methods"] = {m: "NOTRUN" for m in
                                  PY_CANARIES + METHODS + PY_FAULTS}
        self.dependencies_initial = None
        self.transaction_started = None
        self.collection_used = 0.0
        self.owned_roots = (self.root, self.source, self.candidate)

    def capacity(self) -> dict:
        used = 0
        mutable_roots = (self.root, self.game / ".godot", self.game / "reports-editor-persistence")

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
        output = self.root / "test-output"
        if output.exists():
            # Retain all publication/CLI evidence and refuse over-budget output.
            output_bytes = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
            if output_bytes > 64 * 1024**2:
                raise RuntimeError("Combined test-output64MiB limit")
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
        test_text = (self.source / TEST_PATH).read_text()
        if tuple(re.findall(r"^func (test_\w+)\(", test_text, re.M)) != METHODS:
            raise RuntimeError("Two authored GdUnit methods differ")
        python_text = (self.source / "scripts/art/kit/test_bake_publication.py").read_text()
        expected_python = [name.rsplit(".", 1)[-1] for name in PY_CANARIES + PY_FAULTS]
        if sorted(re.findall(r"^    def (test_\w+)\(", python_text, re.M)) != sorted(expected_python):
            raise RuntimeError("Six authored Python methods differ")
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
        if self.root != Path(os.environ["RUNNER_TEMP"]).resolve(strict=True) / "editor-persistence":
            raise RuntimeError("Unexpected private runtime root")
        if not re.fullmatch(r"[0-9a-f]{40}", self.event_sha) or self.event_sha != os.environ["GITHUB_SHA"]:
            raise RuntimeError("Immutable workflow event SHA mismatch")
        if os.environ.get("GITHUB_REF") != "refs/heads/codex/editor-persistence-validation-run":
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
        headers = git(self.candidate, "cat-file", "commit", "HEAD").decode().split("\n\n", 1)[0]
        parents = [line.removeprefix("parent ") for line in headers.splitlines() if line.startswith("parent ")]
        if parents != [GAME_SHA]:
            raise RuntimeError("Receiver must be a genuine sole child of frozen #398 6903")
        source_headers = git(self.source, "cat-file", "commit", "HEAD").decode().split("\n\n", 1)[0]
        if [line.removeprefix("parent ") for line in source_headers.splitlines()
                if line.startswith("parent ")] != [GAME_PARENT]:
            raise RuntimeError("Frozen398 must retain genuine375 sole parent")
        source_tree, candidate_tree = tree(self.source), tree(self.candidate)
        if git(self.candidate, "rev-parse", GAME_SHA + "^{tree}").decode().strip() != GAME_TREE:
            raise RuntimeError("Receiver parent tree differs from tested source")
        delta = {name for name in source_tree.keys() | candidate_tree.keys()
                 if source_tree.get(name) != candidate_tree.get(name)}
        if delta != OWNED_PATHS or any(name in source_tree for name in OWNED_PATHS):
            raise RuntimeError(f"Two NEW receiving paths only: {sorted(delta)}")
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
                   "commit_headers": headers, "tested_game_sha": GAME_SHA,
                   "tested_game_tree": GAME_TREE, "tested_game_headers": source_headers,
                   "delta": sorted(delta), "receiving_source": candidate_rows})
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
        self.env.update({"PERSISTENCE_OUT": str(self.root / "test-output"),
                         "PERSISTENCE_GAME": str(self.game), "GODOT": str(self.engine),
                         "PYTHONPATH": os.pathsep.join((str(self.root / "dependencies"), str(self.source))),
                         "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
        (self.root / "test-output").mkdir(mode=0o700)
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
                   "closure_qualification": "48 pinned Python/config inputs + full game; lawn-only pieces=[] probe. No master-raster load, original paint execution or new generation is granted.",
                   "scientific_stage": "Fresh private target; exact versions, all package byte hashes before/after. Counted inside512MiB duty, not hidden staging; fit UNMEASURED.",
                   "fit": "UNMEASURED; no automatic budget increase",
                   "limits": {
                       "rss_group_bytes": RSS_LIMIT, "owned_bytes": OWNED_LIMIT,
                       "address_space_per_process": 4 * 1024**3,
                       "test_output_bytes": 64 * 1024**2, "import_active_s": 180,
                       "whole_eight_active_s": 240, "whole_eight_collection_s": 30,
                       "setup_dependency_active_s": 120, "job_outer_minutes": 15,
                       "reserve_bytes": FREE_RESERVE, "log_phase_bytes": LOG_LIMIT},
                   "rss_qualification": "Linux /proc aggregate group RSS sampled in the monitor loop (50ms select interval; IO can extend it). Actual maximum monitor gap is recorded; observed overshoot fails."})


    def dependency_snapshot(self) -> dict:
        rows = {}
        base = self.root / "dependencies"
        for p in sorted(base.rglob("*")):
            if p.is_symlink():
                raise RuntimeError("Private dependency symlink unsupported")
            if p.is_file():
                if p.stat().st_nlink != 1:
                    raise RuntimeError("Private dependency is not physically independent")
                rows[str(p.relative_to(base))] = {"bytes": p.stat().st_size, "sha256": digest(p)}
        if not rows:
            raise RuntimeError("Private scientific stage is empty")
        return rows

    def install_dependencies(self) -> None:
        # setup() already verifies attempt/ref/source/scope/private roots. Exact
        # main885b version convention, fresh private --target, no cache or donor.
        requirements = (self.source / ".github/workflows/verify.yml").read_text()
        if any(f"{name}=={version}" not in requirements for name, version in DEPENDENCIES.items()):
            raise RuntimeError("Pinned scientific convention differs")
        target = self.root / "dependencies"
        target.mkdir(mode=0o700)
        result = self.phase("dependencies", [sys.executable, "-I", "-B", "-m", "pip", "install",
            "--disable-pip-version-check", "--no-input", "--no-cache-dir", "--only-binary=:all:",
            "--no-compile", "--no-deps", "--target", str(target),
            *[name + "==" + version for name, version in DEPENDENCIES.items()]], 120)
        self.require_clean("dependencies", result)
        output = self.evidence / "scientific-versions.json"
        code = ("import json, os, sys; from pathlib import Path; import PIL, numpy, scipy; "
                "mods=[PIL,numpy,scipy]; "
                "value={'python':sys.version,'packages':{n:{'version':m.__version__,'file':m.__file__} "
                "for n,m in zip(['Pillow','numpy','scipy'],mods)}}; "
                "Path(sys.argv[1]).write_text(json.dumps(value,indent=2)+'\\n')")
        self.require_clean("versions", self.phase("versions", [sys.executable, "-B", "-c", code, str(output)], 20))
        versions = json.loads(output.read_text())
        for name, version in DEPENDENCIES.items():
            row = versions["packages"][name]
            if row["version"] != version or not Path(row["file"]).resolve(strict=True).is_relative_to(target):
                raise RuntimeError("Scientific stage substituted version or ambient dependency")
        self.dependencies_initial = self.dependency_snapshot()
        write_json(self.evidence / "dependencies-before.json", self.dependencies_initial)

    def python_stage(self, name: str, selected: tuple[str, ...]) -> None:
        observer = self.root / "python_observer.py"
        if observer.exists():
            if observer.read_text() != PYTHON_OBSERVER:
                raise RuntimeError("Receiving Python observer changed")
        else:
            observer.write_text(PYTHON_OBSERVER)
            shutil.copyfile(observer, self.evidence / observer.name)
        inventory_path = self.evidence / (name + "-inventory.json")
        result = self.phase(name, [sys.executable, "-B", str(observer), json.dumps(selected), str(inventory_path)], 240)
        if result["state"] != "COLLECTED" or result.get("exit") not in (0, 1):
            raise RuntimeError("Python stage collection/exit failed; no target RED")
        inventory = json.loads(inventory_path.read_text())
        observed = inventory.get("observed", [])
        if (inventory.get("expected") != list(selected) or inventory.get("harness_error")
                or not observed or observed != list(selected[:len(observed)])
                or set(inventory.get("methods", {})) != set(selected)):
            raise RuntimeError("Python discovery/identity/partial observer failure")
        failed = []
        for method in selected:
            row = inventory["methods"][method]
            self.output["methods"][method] = row["state"]
            if method not in observed:
                if row["state"] != "NOTRUN":
                    raise RuntimeError("Unstarted Python method is not NOTRUN")
                continue
            if row["state"] not in ("PASS", "FAIL"):
                raise RuntimeError("Python import/setup/error/skip is not target assertion RED")
            roots = row.get("evidence_roots", [])
            prefix = method.rsplit(".", 1)[-1] + "-"
            if len(roots) != 1:
                raise RuntimeError("Need one actual retained method evidence root")
            root = Path(roots[0]).resolve(strict=True)
            if root.parent != self.root / "test-output" or not root.name.startswith(prefix):
                raise RuntimeError("Method evidence escaped exact private output")
            self.audit_cli(method, root, row)
            if row["state"] == "FAIL":
                failed.append(method)
                boundaries = ASSERTION_BOUNDARIES.get(method, ())
                trace = row.get("traceback", "")
                if (row.get("exception_type") != "AssertionError" or "test_bake_publication.py" not in trace
                        or not any(message in row.get("message", "") for message in boundaries)):
                    raise RuntimeError("Prerequisite/other assertion failure; no intended persistence RED")
                # Real tests assert these observations before their defect assertion.
                if method.startswith("PublicationFaults.") and not all((root / (n + ".json")).is_file() for n in ("before", "after")):
                    raise RuntimeError("No retained actual publication fault snapshots")
        log = diagnostic_text(self.evidence / (name + ".log"))
        if ERROR_PATTERN.search(log) or orphan_diagnostics(log):
            raise RuntimeError("Raw Python-stage engine/orphan failure is not persistence RED")
        if failed:
            if name != "python-faults" or failed != [observed[-1]] or result["exit"] != 1:
                raise RuntimeError("Canary or non-failfast failure")
            self.output["state"] = "PERSISTENCE_ASSERTION_RED_REQUIRES_LEAD_REVIEW"
            raise RuntimeError("Exact persistence assertion failed; later controls remain NOTRUN")
        if (observed != list(selected) or inventory.get("testsRun") != len(selected)
                or inventory.get("success") is not True or result["exit"] != 0):
            raise RuntimeError("Incomplete Python success")

    def audit_cli(self, method: str, root: Path, result: dict) -> None:
        calls = sorted(root.glob("call-*.json"), key=lambda p: int(p.name.split("-")[1].split(".")[0]))
        if not method.startswith("ExportCLI."):
            if calls:
                raise RuntimeError("Unexpected CLI call from bake-only method")
            return
        expected_calls = 4 if method in (PY_CANARIES[1], PY_FAULTS[3]) else 3
        if len(calls) != expected_calls:
            raise RuntimeError("CLI stage incomplete, timeout or prerequisite failure")
        evidence = []
        for i, path in enumerate(calls, 1):
            if path.name != f"call-{i}.json":
                raise RuntimeError("CLI command/evidence sequence gap")
            call = json.loads(path.read_text())
            expected_argument = ("--plan=" if i % 2 else "--export=")
            if method == PY_FAULTS[2] and i == 3:
                expected_argument = "--export="
            argv = call.get("argv", [])
            if (argv[:7] != [str(self.engine), "--headless", "--audio-driver", "Dummy", "--path",
                             str(self.game), "--script"] or len(argv) != 11
                    or argv[7:9] != ["res://tools/kit_zone.gd", "--"]
                    or not argv[9].startswith(expected_argument) or not argv[10].startswith("--out=")):
                raise RuntimeError("CLI command/engine/project identity mismatch")
            for argument in argv[9:]:
                if not Path(argument.split("=", 1)[1]).resolve().is_relative_to(root):
                    raise RuntimeError("CLI input/output escapes owned method evidence")
            text = ""
            for suffix in ("stdout", "stderr"):
                log = root / f"call-{i}.{suffix}"
                if log.is_symlink() or log.stat().st_size > LOG_LIMIT:
                    raise RuntimeError("CLI raw log missing/nonphysical/over4MiB")
                text += diagnostic_text(log) + "\n"
            if ERROR_PATTERN.search(text) or orphan_diagnostics(text) or PYTHON_ERROR_PATTERN.search(text):
                raise RuntimeError("Raw inner engine/Python/orphan diagnostic; no target RED")
            exceptional = i == expected_calls and method in PY_FAULTS[2:]
            if not exceptional and (call.get("returncode") != 0 or call.get("file_limit") is not None):
                raise RuntimeError("CLI prerequisite failed")
            if method == PY_FAULTS[2] and exceptional:
                if call.get("file_limit") is not None or call.get("returncode") not in (0, 1):
                    raise RuntimeError("Rejected-export unexpected signal/exit or file limit")
                # exit0 is precisely the asserted production failure, never canary success.
                if result["state"] == "PASS" and call.get("returncode") == 0:
                    raise RuntimeError("Rejected-export PASS contradicts actual call")
            if method == PY_FAULTS[3] and exceptional:
                sizes = {p.name: p.stat().st_size for p in (root / "outputs").iterdir() if p.is_file()}
                if call.get("file_limit") != 4096 or 4096 not in sizes.values():
                    raise RuntimeError("Intended real4096-byte kernel boundary not reached")
                if call.get("returncode") != -signal.SIGXFSZ:
                    raise RuntimeError("No actual SIGXFSZ interruption at asserted boundary")
                evidence.append({"expected_signal": "SIGXFSZ", "actual_exit": call["returncode"],
                                 "boundary_bytes": 4096, "output_sizes": sizes})
            evidence.append({"call": path.name, **call})
        result["receiving_cli_audit"] = evidence
        write_json(self.evidence / (method + "-cli.json"), result)

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
        if self.transaction_started is not None:
            remaining = 240 - (time.monotonic() - self.transaction_started - self.collection_used)
            if remaining <= 0 or self.collection_used >= 30:
                raise RuntimeError("Whole-eight active/collection aggregate budget exhausted")
            seconds = min(seconds, remaining)
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
            def child_limits():
                resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
                resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024**2, 64 * 1024**2))
            process = subprocess.Popen(command, cwd=self.game, env=self.env, start_new_session=True,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=child_limits)
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
            collection_start = time.monotonic()
            collection_deadline = collection_start + (min(10, max(0, 30 - self.collection_used))
                if self.transaction_started is not None else 10)
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
                        deadline = min(time.monotonic() + 5, collection_deadline)
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
                    end = min(time.monotonic() + 5, collection_deadline)
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
            if self.transaction_started is not None:
                self.collection_used += time.monotonic() - collection_start
                if self.collection_used > 30:
                    reason = reason or "Whole-eight collection exceeded30s"
                result["aggregate_active_s"] = time.monotonic() - self.transaction_started - self.collection_used
                result["aggregate_collection_s"] = self.collection_used
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
        (probe / "project.godot").write_text('config_version=5\n[application]\nconfig/name="EDITOR_PERSISTENCEPathCanary"\n[editor_plugins]\nenabled=PackedStringArray("res://addons/editor_dependents_paths/plugin.cfg")\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
        (plugin / "plugin.cfg").write_text('[plugin]\nname="EDITOR_PERSISTENCEPathCanary"\ndescription="Private engine path canary"\nauthor="MyGame"\nversion="1"\nscript="paths.gd"\n')
        (plugin / "paths.gd").write_text(PROBE)
        output = self.evidence / "actual-engine-paths.json"
        self.env["EDITOR_PERSISTENCE_CANARY_OUTPUT"] = str(output)
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
            suite_name = "test_kit_zone_persistence"
            if (root.tag != "testsuites" or len(suites) != 1
                    or suites[0].get("package") != "test"
                    or suites[0].get("name") != suite_name):
                raise RuntimeError("JUnit does not identify the sole requested editor suite")
            suite = suites[0]
            # The pinned writer emits declared/discovered tests=2 even when
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
            if not failed:
                if names != list(METHODS) or result["exit"] != 0:
                    raise RuntimeError("Incomplete success/exit is not two passing GdUnit methods")
                self.output["state"] = "TWO_GDUNIT_PASS"
                self.output["focused_suite_pass"] = True
            elif failed == [names[-1]] and result["exit"] == 100:
                # Exact unchanged test assertion is evidence, not GUI acceptance.
                self.output["state"] = "PERSISTENCE_GDUNIT_ASSERTION_FAIL_REQUIRES_LEAD_REVIEW"
            else:
                raise RuntimeError("Failure/exit does not match actual fail-fast assertion semantics")
        finally:
            self.output["methods"].update(findings["methods"])
            findings["classification"] = self.output["state"]
            write_json(self.evidence / "focused-inventory.json", findings)

    def run(self) -> int:
        failure = None
        try:
            self.setup()
            self.install_dependencies()
            self.get_engine()
            self.canary()
            self.require_clean("import", self.phase("import", [str(self.engine), "--headless", "--audio-driver", "Dummy",
                                                             "--path", str(self.game), "--import"], 180))
            self.transaction_started = time.monotonic()
            self.require_clean("check-only", self.phase("check-only", [
                str(self.engine), "--headless", "--audio-driver", "Dummy",
                "--path", str(self.game), "--check-only", "--script",
                "res://" + TEST_PATH.removeprefix("game/")], 20))
            self.python_stage("python-canaries", PY_CANARIES)
            self.reconcile(self.phase("focused", [str(self.engine), "--headless", "--audio-driver", "Dummy",
                "--path", str(self.game), "-s", "res://addons/gdUnit4/bin/GdUnitCmdTool.gd",
                "--ignoreHeadlessMode", "-a", "res://" + TEST_PATH.removeprefix("game/"), "-rd", REPORT_DIR], 90))
            if self.output["state"] != "TWO_GDUNIT_PASS":
                raise RuntimeError("GdUnit stage did not pass; fault methods remain NOTRUN")
            self.python_stage("python-faults", PY_FAULTS)
            if any(state != "PASS" for state in self.output["methods"].values()):
                raise RuntimeError("Not all eight persistence controls passed")
            self.output["state"] = "EIGHT_PERSISTENCE_PASS"
        except BaseException as error:
            failure = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
            if self.output["state"] not in ("PERSISTENCE_ASSERTION_RED_REQUIRES_LEAD_REVIEW",
                                           "PERSISTENCE_GDUNIT_ASSERTION_FAIL_REQUIRES_LEAD_REVIEW"):
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
                if self.dependencies_initial is not None:
                    after_dependencies = self.dependency_snapshot()
                    write_json(self.evidence / "dependencies-after.json", after_dependencies)
                    if after_dependencies != self.dependencies_initial:
                        raise RuntimeError("Private scientific dependency bytes changed")
                    self.guards["dependencies"] = "PASS"
            except BaseException as error:
                final_errors.append("dependencies: " + repr(error))
            # Independent best-effort attempts: a guard/archive failure never
            # prevents retention of the other original failed-method artifacts.
            for label, source in {"test-output": self.root / "test-output",
                                  "private-data": self.root / "data"}.items():
                try:
                    if source.exists():
                        with tarfile.open(self.evidence / (label + ".tar.gz"), "x:gz") as archive:
                            archive.add(source, arcname=label)
                except BaseException as error:
                    final_errors.append(label + ": " + repr(error))
            try:
                reports = self.game / REPORT_DIR
                if reports.exists():
                    shutil.copytree(reports, self.evidence / "gdunit-reports")
            except BaseException as error:
                final_errors.append("gdunit-reports: " + repr(error))
            try:
                uid = self.source / (TEST_PATH + ".uid")
                if uid.exists():
                    shutil.copyfile(uid, self.evidence / uid.name)
            except BaseException as error:
                final_errors.append("generated-uid: " + repr(error))
            try:
                self.output["final_capacity"] = self.capacity()
            except BaseException as error:
                final_errors.append("capacity: " + repr(error))
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
        return 0 if self.output["state"] == "EIGHT_PERSISTENCE_PASS" else 1


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
