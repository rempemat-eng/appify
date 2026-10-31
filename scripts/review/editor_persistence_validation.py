#!/usr/bin/env python3
"""Bounded editor receiver; SOURCE ONLY until exact lead allocation.

Adapted from reviewed #402 c2cd7baa (controller blob f40ef659), originally #401.
Reuse #402 c2cd7baa private-engine/actual-wait collection. H5 on combined #407 uses
six Python and ten frozen GdUnit methods; no displayed GUI, complete editor,
nonempty-piece/cell-coordinate, full-suite or acceptance inference.
Opt-in DISPLAYED_SMOKE uses the existing plugin only, with undo/restoration
and bake refusals; it does not establish successful save/bake/walk acceptance.
No imports, engine or tests are authorised by publishing this candidate.
VULKAN_INVENTORY is a separate metadata-only opt-in: no engine, project,
scientific stage or native query. Loader discovery gaps remain explicit.
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

GAME_SHA = "feb37c31d6de71e20df096df4df4d32ed1fa93ed"
INVENTORY_RECEIVER_PARENT = "a6573383083eb39f2967ccd554e7ed85fcde279f"
INVENTORY_RECEIVER_PARENT_TREE = "7ab98e2e903af5dd572c188cb96b5360a202b572"
AUTH_RECEIVER_PARENT = "444e767d021efe08d37fd12e07ac4de46a831296"
AUTH_RECEIVER_PARENT_TREE = "35dc21c7e2635685f3eea94de53368217aaf2fac"
TOOL_RECEIVER_PARENT = "cbf823804359fb879b0fbd2054ab1ed7b472093c"
TOOL_RECEIVER_PARENT_TREE = "3239a7eaf5c98e425b7a242ccc49545152537c91"
MESA_PACKAGE = {
    "package": "mesa-utils-bin", "version": "9.0.0-2", "architecture": "amd64",
    "url": "https://archive.ubuntu.com/ubuntu/pool/universe/m/mesa-demos/mesa-utils-bin_9.0.0-2_amd64.deb",
    "metadata": "https://packages.ubuntu.com/en/noble/amd64/mesa-utils-bin/download",
    "filelist": "https://packages.ubuntu.com/noble/amd64/mesa-utils-bin/filelist",
    "bytes": 164440, "sha256": "d64539eb18416708948d7857506946a024637e4c6147d91a28a42868e038cb00",
    "member": "usr/bin/glxinfo.x86_64-linux-gnu", "member_limit": 256 * 1024,
    "expanded_limit": 2 * 1024**2, "entry_limit": 64,
}
DISPLAY_RECEIVER_PARENT = "79a4fb5162df4599c5db5573b095b60e661194d3"
DISPLAY_RECEIVER_PARENT_TREE = "2fddb86ded9ce68f0a96821946d9a58b6352bc70"
MODES = ("H5_COMBINED", "DISPLAYED_SMOKE", "VULKAN_INVENTORY")
GAME_TREE = "d902afb2c331cc4067d4c4804abc29eb5ae3d6d2"
GAME_PARENT = "52caf926c92337a7a6b0c36dfe73184ec4712e8c"
GAME_PARENT_TREE = "04fb2a163594a0e4bb345181b5ee43d2a9ebe19c"
GAME_GRANDPARENT = "b9a37cbbe5aefdfe5b0e9fbdb43bda335e793008"
GAME_GRANDPARENT_TREE = "b0aa3feb0c48afd8d819ca902cebaae6da19adcf"
ORIGINAL_GAME_SHA = "6903f8d5d729f5eb9d4beef20d33869465308c66"
ORIGINAL_GAME_TREE = "e4dfae3eb183426e3a44fd004436eb1ed18b53d7"
ORIGINAL_GAME_PARENT = "45ed3cad029c106977e6c0c833913dcb1c614fbd"
RECEIVER_PARENT = "7c14adf06ada859205552b02b340769f7a6f9c99"
RECEIVER_PARENT_TREE = "5832aba48dbdc25b48ca402efe6fb81bff0b27a5"
PRIOR_RECEIVER = "6c76f5290b18fe2367624ca6fb41177a0dbe42b5"
PRIOR_RECEIVER_TREE = "0064acc7b4f1a47da156bb1492c1a07837536afc"
EARLIER_RECEIVER = "597ce2e0fd68a872a7b4b31535033ddde702746a"
EARLIER_RECEIVER_TREE = "5ff44f05022c66089167f40150075c265851eb30"
OLDER_RECEIVER = "63273684792073573c571148c4bbc07c4486267b"
OLDER_RECEIVER_TREE = "0305ff7b941f8f92c211da625511ff2abe42a021"
ORIGINAL_RECEIVER = "5de271d77f26dbbc5641bac0ef6635aef021c34b"
ORIGINAL_RECEIVER_TREE = "62b470d5934699bed72660f5a011e66b3f3da854"
TEST_BLOB = "a61671b648277d1c2ba290de51cdff74b475a1c9"
PRODUCTION_BLOB = "effd244781b1e71c5d990b14df82258280e93811"
EXPORT_BLOB = "f34b6960393dbbcb8724140810509cae090c46c7"
DEPENDENT_TEST_BLOB = "af4bc24645ed06d69d987070f866d5e774246465"
KIT_PIECE_BLOB = "c9098c7e79a5eb7e336683e195d37d6bd283501a"
GROUND_BLOB = "d25d92c7f6c257be724cd7e1a86b7353e44e2e78"
GAME_COUNT = 6689
GAME_BYTES = 87869357
# Static import/data closure of corrected bake, unchanged validator and tiny fixture.
# Full game supplies library/schema/terrain/index/fixtures. No master raster is
# reached by this pieces=[] lawn-only probe. scripts/art are namespace packages.
PYTHON_INPUTS = {'.github/workflows/verify.yml': ('97a2d95b8b5d6c801ad0258cf44cbb6474a07a1e', 2165),
 'art/house-palette.json': ('7e97a7463b3641425e667d7b7764f34510489a54', 20444),
 'art/scenes/woodland.json': ('4ddc7ed7b91d413f897388969579b4d06a2a7486', 31704),
 'scripts/art/biomes/woodland.json': ('6da96e5aa39b945288b2a71e826e7e6b535a7559', 8822),
 'scripts/art/house_palette.py': ('8a816d1799abd1fc22931a2c93fbe620a14a200e', 17753),
 'scripts/art/kit/__init__.py': ('e69de29bb2d1d6434b8b29ae775ad8c2e48c5391', 0),
 'scripts/art/kit/bake.py': ('449f47013ecae318343fc915c5b65d12b9021432', 25290),
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
PYTHON_BYTES = 1229249
TEST_PATH = "game/test/test_kit_zone_persistence.gd"
DEPENDENT_TEST_PATH = "game/test/test_world_editor_dependent_edits.gd"
TEST_PATHS = (TEST_PATH, DEPENDENT_TEST_PATH)
GENERATED_UID_PATHS = tuple(path + ".uid" for path in TEST_PATHS)
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
OWNED_LIMIT = 768 * 1024**2
FREE_RESERVE = 256 * 1024**2
RSS_LIMIT = 2048 * 1024**2
LOG_LIMIT = 4 * 1024**2
OWNED_PATHS = {".github/workflows/editor-persistence-validation.yml",
               "scripts/review/editor_persistence_validation.py"}
PERSISTENCE_METHODS = (
    "test_minimal_authored_zone_survives_disk_export_and_rebuild",
    "test_native_deletions_and_literal_ids_survive_two_saved_generations",
)
DEPENDENT_METHODS = (
    "test_startup_canary_real_intake_and_adapter",
    "test_paint_beneath_existing_footprint_refreshes_rules_and_undo_redo",
    "test_route_relation_distance_boundary_and_interacting_water_prohibition",
    "test_tier_change_breaks_stair_deck_route_and_import_is_unshippable",
    "test_moving_stair_support_immediately_refreshes_validation_and_bake",
    "test_deleting_stair_support_exposes_route_without_stale_bake",
    "test_moving_related_seat_revalidates_instead_of_reusing_green",
    "test_rejections_preserve_document_and_existing_redo_branch",
)
METHODS = PERSISTENCE_METHODS + DEPENDENT_METHODS
GD_SUITES = {
    "test_kit_zone_persistence": (TEST_PATH, TEST_BLOB, PERSISTENCE_METHODS),
    "test_world_editor_dependent_edits": (DEPENDENT_TEST_PATH, DEPENDENT_TEST_BLOB, DEPENDENT_METHODS),
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
    # Atomic replacement keeps the provisional failure intact if sealing expires.
    temporary = path.with_name(path.name + ".partial")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    temporary.replace(path)


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

def mesa_host() -> dict:
    release = platform.freedesktop_os_release()
    libc = os.confstr("CS_GNU_LIBC_VERSION")
    if (release.get("ID") != "ubuntu" or release.get("VERSION_ID") != "24.04"
            or release.get("VERSION_CODENAME") != "noble" or platform.machine() != "x86_64"
            or not re.fullmatch(r"glibc 2\.(3[89]|[4-9][0-9])", libc or "")):
        raise RuntimeError("Pinned Mesa tool requires actual Ubuntu Noble amd64/glibc>=2.38")
    return {"id": release["ID"], "version": release["VERSION_ID"],
            "codename": release["VERSION_CODENAME"], "machine": platform.machine(), "libc": libc}


def mesa_fields(text: str) -> dict:
    fields = {}
    for line in text.splitlines():
        if line.startswith(" "):
            fields[key] += " " + line.strip()
        elif ": " in line:
            key, value = line.split(": ", 1)
            fields[key] = value
    return fields


def mesa_binary(path: Path) -> dict:
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_mode & 0o6022 or not os.access(path, os.X_OK)
            or not 64 <= info.st_size <= MESA_PACKAGE["member_limit"]):
        raise RuntimeError("Mesa glxinfo is not a bounded physical executable")
    with path.open("rb") as file:
        header = file.read(20)
    if header[:6] != b"\x7fELF\x02\x01" or header[18:20] != b"\x3e\x00":
        raise RuntimeError("Mesa glxinfo is not Linux ELF64 little-endian x86-64")
    return {"path": str(path), "bytes": info.st_size, "sha256": digest(path), "mode": stat.S_IMODE(info.st_mode)}


def installed_mesa() -> dict | None:
    path = Path("/usr/bin") / Path(MESA_PACKAGE["member"]).name
    found = shutil.which("glxinfo")
    if found and Path(found).resolve(strict=True) != path:
        raise RuntimeError("PATH glxinfo shadows the canonical Ubuntu package executable")
    if not os.path.lexists(path):
        return None
    status = Path("/var/lib/dpkg/status")
    if status.stat().st_size > 32 * 1024**2:
        raise RuntimeError("Host dpkg status metadata bound")
    records = [mesa_fields(p) for p in status.read_text().split("\n\n") if p.startswith("Package: mesa-utils-bin\n")]
    if len(records) != 1:
        raise RuntimeError("Canonical Mesa executable lacks unique installed package identity")
    record = records[0]
    if (any(record.get(key.title()) != MESA_PACKAGE[key] for key in ("package", "version", "architecture"))
            or record.get("Status") != "install ok installed" or path.lstat().st_uid != 0):
        raise RuntimeError("Installed Mesa package version/architecture/status/owner differs")
    matches = [Path("/var/lib/dpkg/info") / (name + ".md5sums")
               for name in ("mesa-utils-bin", "mesa-utils-bin:amd64")]
    matches = [p for p in matches if p.is_file()]
    if len(matches) != 1 or matches[0].stat().st_size > 64 * 1024:
        raise RuntimeError("Installed Mesa integrity metadata absent/ambiguous/oversized")
    rows = [line.split() for line in matches[0].read_text().splitlines()]
    expected = [row[0] for row in rows if len(row) == 2 and row[1] == MESA_PACKAGE["member"]]
    if len(expected) != 1 or digest(path, "md5") != expected[0]:
        raise RuntimeError("Canonical Mesa executable differs from host package integrity record")
    return {**mesa_binary(path), "origin": "installed Ubuntu dpkg package", "package": record,
            "integrity_record_sha256": digest(matches[0]), "integrity": "host dpkg MD5 matched; SHA256 observed, not an archive-member comparison"}


def mesa_tool_stage(args: argparse.Namespace) -> int:
    root = args.root.resolve(strict=True)
    output = root / "evidence/display-tool"
    output.mkdir(mode=0o700)
    plan = json.loads((root / "evidence/display-tool-plan.json").read_text())
    receipt = {"state": "INCOMPLETE", "host": mesa_host(), "wait4": [], "package": MESA_PACKAGE}
    children = []
    write_json(output / "provenance.json", receipt)

    def collect(process: subprocess.Popen, seconds: float = 20) -> int:
        deadline = time.monotonic() + seconds
        while True:
            pid, status, usage = os.wait4(process.pid, os.WNOHANG)
            if pid:
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("Mesa child actual wait4 deadline")
            time.sleep(0.02)
        process.returncode = os.waitstatus_to_exitcode(status)
        receipt["wait4"].append({"pid": pid, "status": status, "exit": process.returncode,
            "user_s": usage.ru_utime, "system_s": usage.ru_stime, "maxrss_kib": usage.ru_maxrss})
        return process.returncode

    def start(command: list[str], stdout):
        def limits():
            resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024, 64 * 1024))
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout,
                                   stderr=None, preexec_fn=limits)
        children.append(process)
        receipt.setdefault("children", []).append({"pid": process.pid, "pgid": os.getpgid(process.pid)})
        write_json(output / "provenance.json", receipt)
        if os.getpgid(process.pid) != os.getpgrp():
            raise RuntimeError("Mesa bootstrap child escaped its monitored group")
        return process

    try:
        if args.mode != "DISPLAYED_SMOKE" or os.getpgrp() != os.getpid():
            raise RuntimeError("Mesa stage requires the allocated monitored phase group")
        if os.environ.get("GITHUB_REF") != "refs/heads/codex/editor-persistence-validation-run":
            raise RuntimeError("Mesa stage is not on the allocated execution ref")
        for row in plan["bootstrap"].values():
            path = Path(row["path"])
            if path.stat().st_size != row["bytes"] or digest(path) != row["sha256"]:
                raise RuntimeError("Mesa bootstrap executable changed before use")
        receipt["bootstrap"] = plan["bootstrap"]
        binary = installed_mesa()
        if binary != plan["installed"]:
            raise RuntimeError("Installed Mesa identity changed after preflight")
        if binary is None:
            package = output / "mesa-utils-bin_9.0.0-2_amd64.deb"
            received = 0
            try:
                # Same bounded urllib/chunk/hash pattern as existing get_engine;
                # one literal vendor URL only, no mirrors/retry/install/scripts.
                class NoPackageRedirect(urllib.request.HTTPRedirectHandler):
                    def redirect_request(self, *_args, **_kwargs):
                        raise RuntimeError("Pinned Mesa vendor redirect refused")
                opener = urllib.request.build_opener(NoPackageRedirect())
                with opener.open(MESA_PACKAGE["url"], timeout=10) as response, package.open("xb") as dst:
                    if response.geturl() != MESA_PACKAGE["url"]:
                        raise RuntimeError("Mesa vendor URL redirected; no fallback")
                    for chunk in iter(lambda: response.read(65536), b""):
                        received += len(chunk)
                        if received > MESA_PACKAGE["bytes"]:
                            raise RuntimeError("Pinned Mesa compressed byte bound")
                        dst.write(chunk)
            finally:
                receipt["download"] = {"received": received, "retained_bytes": package.stat().st_size if package.exists() else 0,
                    "sha256": digest(package) if package.exists() else None}
            if received != MESA_PACKAGE["bytes"] or digest(package) != MESA_PACKAGE["sha256"]:
                raise RuntimeError("Pinned official Mesa package size/SHA256 mismatch")
            control = output / "control.txt"
            with control.open("xb") as dst:
                process = start([plan["bootstrap"]["dpkg-deb"]["path"], "--field", str(package)], dst)
                if collect(process) != 0:
                    raise RuntimeError("dpkg-deb refused pinned package control")
            if control.stat().st_size > 16384:
                raise RuntimeError("Mesa control metadata bound")
            fields = mesa_fields(control.read_text())
            if (any(fields.get(key.title()) != MESA_PACKAGE[key] for key in ("package", "version", "architecture"))
                    or not 0 < int(fields.get("Installed-Size", "0")) <= 2048):
                raise RuntimeError("Mesa package control identity/expanded bound differs")
            receipt["control"] = fields
            path = output / Path(MESA_PACKAGE["member"]).name
            process = start([plan["bootstrap"]["dpkg-deb"]["path"], "--fsys-tarfile", str(package)], subprocess.PIPE)
            seen, expanded, found = set(), 0, 0
            with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
                for member in archive:
                    name = member.name.removeprefix("./")
                    if (name in seen or len(seen) >= MESA_PACKAGE["entry_limit"] or name.startswith("/")
                            or ".." in Path(name).parts or not (member.isfile() or member.isdir())):
                        raise RuntimeError("Mesa payload path/type/count bound")
                    seen.add(name)
                    expanded += member.size
                    if expanded > MESA_PACKAGE["expanded_limit"]:
                        raise RuntimeError("Mesa expanded payload byte bound")
                    if name == MESA_PACKAGE["member"]:
                        if not member.isfile() or member.mode != 0o755 or not 64 <= member.size <= MESA_PACKAGE["member_limit"]:
                            raise RuntimeError("Exact Mesa glxinfo member identity/size/mode differs")
                        found += 1
                        with archive.extractfile(member) as src, path.open("xb") as dst:
                            shutil.copyfileobj(src, dst, 65536)
            process.stdout.close()
            if collect(process) != 0 or found != 1:
                raise RuntimeError("Mesa payload extraction/unique member failed")
            path.chmod(0o755)
            binary = {**mesa_binary(path), "origin": "private pinned Ubuntu package", "package_sha256": digest(package)}
            receipt.update(payload_entries=len(seen), expanded_bytes=expanded)
        path = Path(binary["path"])
        dependencies = output / "ldd.txt"
        with dependencies.open("xb") as dst:
            process = start([plan["bootstrap"]["ldd"]["path"], str(path)], dst)
            if collect(process) != 0:
                raise RuntimeError("Mesa runtime dependency/ABI inspection failed")
        text = dependencies.read_text()
        if len(text) > 16384 or "not found" in text.lower() or "libc.so.6" not in text or "=>" not in text:
            raise RuntimeError("Mesa required library/ABI unavailable; no automatic package installation")
        receipt.update(binary=binary, state="VERIFIED")
    except BaseException as error:
        receipt.update(state="FAILED", failure={"type": type(error).__name__, "message": str(error)})
    finally:
        for process in children:
            if process.returncode is not None:
                continue
            try:
                # Direct unreaped child identity prevents numeric PID reuse.
                if os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
                    os.kill(process.pid, signal.SIGTERM)
                collect(process, 2)
            except BaseException as error:
                receipt["state"] = "FAILED"
                receipt.setdefault("cleanup_errors", []).append(repr(error))
        # The existing outer phase remains authoritative for final group kill,
        # adoption/wait4 and absence, including a killed/incomplete bootstrap.
        write_json(output / "provenance.json", receipt)
    return 0 if receipt["state"] == "VERIFIED" else 1


def displayed_lifetime(args: argparse.Namespace) -> int:
    """Receiving-only child: one authenticated server/editor group, no game harness."""
    root, game = args.root.resolve(strict=True), args.source.resolve(strict=True) / "game"
    output = root / "test-output/displayed-smoke"
    receipt_path = output / "lifetime.json"
    authority_dir = root / "runtime/display-authority"
    authority = authority_dir / "Xauthority"
    denied_authority = authority_dir / "no-authority"
    receipt = {"state": "INCOMPLETE", "pid": os.getpid(), "pgid": os.getpgrp(),
               "processes": {}, "wait4": [], "cleanup_errors": []}
    children, handles = {}, []
    failure = None

    def save() -> None:
        write_json(receipt_path, receipt)

    def launch(name: str, command: list[str], env: dict, **kwargs) -> subprocess.Popen:
        if hasattr(kwargs.get("stdout"), "fileno"):
            def tool_log_limit():
                resource.setrlimit(resource.RLIMIT_FSIZE, (LOG_LIMIT, LOG_LIMIT))
            kwargs["preexec_fn"] = tool_log_limit
        process = subprocess.Popen(command, cwd=game, env=env, **kwargs)
        children[name] = process
        identity = proc_group(os.getpgrp()).get(process.pid)
        if identity is None:
            raise RuntimeError("Displayed child did not remain in its monitored group")
        receipt["processes"][name] = {"pid": process.pid, **identity}
        save()
        return process

    def collect(name: str, seconds: float) -> int:
        process = children[name]
        deadline = time.monotonic() + seconds
        while True:
            pid, status, usage = os.wait4(process.pid, os.WNOHANG)
            if pid:
                process.returncode = os.waitstatus_to_exitcode(status)
                receipt["wait4"].append({"name": name, "pid": pid, "status": status,
                    "exit": process.returncode, "user_s": usage.ru_utime,
                    "system_s": usage.ru_stime, "maxrss_kib": usage.ru_maxrss})
                save()
                return process.returncode
            if time.monotonic() >= deadline:
                raise TimeoutError("Displayed child collection deadline: " + name)
            time.sleep(0.02)

    def raw_log(name: str):
        handle = (output / name).open("xb")
        handles.append(handle)
        return handle

    try:
        if (args.mode != "DISPLAYED_SMOKE" or os.getpgrp() != os.getpid()
                or os.environ.get("GITHUB_REF") != "refs/heads/codex/editor-persistence-validation-run"):
            raise RuntimeError("Displayed child requires its allocated private phase group")
        capabilities = json.loads((root / "evidence/display-capabilities.json").read_text())
        tools = capabilities["tools"]
        base_env = dict(os.environ)
        for key in ("DISPLAY", "XAUTHORITY", "WAYLAND_DISPLAY"):
            base_env.pop(key, None)
        authority_dir.mkdir(mode=0o700)
        for p in (authority, denied_authority):
            fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(fd)
        display = next((number for number in range(200, 300)
                        if not os.path.lexists(f"/tmp/.X{number}-lock")
                        and not os.path.lexists(f"/tmp/.X11-unix/X{number}")), None)
        if display is None:
            raise RuntimeError("No unused bounded display number; no fallback")
        receipt.update(display=display, authority={"path": str(authority), "mode": "0600",
                       "protocol": "MIT-MAGIC-COOKIE-1", "cookie_recorded": False})
        save()
        auth = launch("xauth", [tools["xauth"]["path"], "-q", "-f", str(authority)], base_env,
                      stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cookie = os.urandom(16).hex()
        auth.stdin.write(f"add :{display} MIT-MAGIC-COOKIE-1 {cookie}\n".encode())
        auth.stdin.close()
        del cookie
        if collect("xauth", 5) != 0:
            raise RuntimeError("Private Xauthority creation failed; diagnostics suppressed")
        info = authority.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or not 1 <= info.st_size <= 4096):
            raise RuntimeError("Private authority metadata invalid")
        receipt["authority"].update(bytes=info.st_size, uid=info.st_uid)
        server = launch("Xvfb", [tools["Xvfb"]["path"], f":{display}", "-screen", "0", "1920x1080x24",
                         "-nolisten", "tcp", "-noreset", "+extension", "GLX", "-auth", str(authority)],
                        base_env, stdin=subprocess.DEVNULL, stdout=raw_log("xvfb.log"), stderr=subprocess.STDOUT)
        socket = Path(f"/tmp/.X11-unix/X{display}")
        lock = Path(f"/tmp/.X{display}-lock")
        deadline = time.monotonic() + 8
        while not socket.exists() or not lock.exists():
            if os.waitid(os.P_PID, server.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
                raise RuntimeError("Authenticated Xvfb exited before readiness")
            if time.monotonic() >= deadline:
                raise TimeoutError("Authenticated Xvfb socket readiness deadline")
            time.sleep(0.02)
        if int(lock.read_text().strip()) != server.pid or not stat.S_ISSOCK(socket.lstat().st_mode):
            raise RuntimeError("Display lock/socket not owned by actual server")
        receipt["display_files"] = {str(p): {"inode": p.lstat().st_ino, "uid": p.lstat().st_uid}
                                    for p in (socket, lock)}
        gui_env = {**base_env, "DISPLAY": f":{display}", "XAUTHORITY": str(authority)}
        # H7 reproduced this exact pinned Mesa build's ordinary255/raw65280
        # denial. Upstream source was unavailable; this is observed binary evidence.
        denied_info = denied_authority.lstat()
        if (not stat.S_ISREG(denied_info.st_mode) or denied_info.st_nlink != 1
                or denied_info.st_uid != os.getuid() or stat.S_IMODE(denied_info.st_mode) != 0o600
                or denied_info.st_size != 0):
            raise RuntimeError("Unauthenticated probe requires a physical empty private credential file")
        if os.waitid(os.P_PID, server.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
            raise RuntimeError("Authenticated Xvfb exited before refusal probe")
        launch("unauthorized-glx", [tools["glxinfo"]["path"], "-B"],
               {**gui_env, "XAUTHORITY": str(denied_authority)}, stdin=subprocess.DEVNULL,
               stdout=raw_log("unauthorized-glx.log"), stderr=subprocess.STDOUT)
        denied_exit = collect("unauthorized-glx", 5)
        denied_wait = receipt["wait4"][-1]
        if (denied_wait["name"] != "unauthorized-glx"
                or denied_wait["pid"] != children["unauthorized-glx"].pid
                or not os.WIFEXITED(denied_wait["status"])
                or os.WEXITSTATUS(denied_wait["status"]) != 255
                or denied_exit != 255 or denied_wait["status"] != 65280):
            raise RuntimeError("Pinned Mesa unauthenticated probe did not return ordinary255/raw65280")
        handles[-1].flush()
        denied = (output / "unauthorized-glx.log").read_text(errors="replace")
        if ("Authorization required, but no authorization protocol specified" not in denied
                or f"Error: unable to open display :{display}" not in denied):
            raise RuntimeError("Both pinned Mesa X11 authentication refusal diagnostics were not observed")
        if os.waitid(os.P_PID, server.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
            raise RuntimeError("Authenticated Xvfb exited during refusal probe")
        for p in (socket, lock):
            info = p.lstat()
            before = receipt["display_files"][str(p)]
            if (info.st_ino != before["inode"] or info.st_uid != before["uid"]
                    or info.st_uid != os.getuid()):
                raise RuntimeError("Owned display lock/socket identity changed during refusal probe")
        if (not stat.S_ISSOCK(socket.lstat().st_mode) or not stat.S_ISREG(lock.lstat().st_mode)
                or int(lock.read_text().strip()) != server.pid
                or any(getattr(denied_authority.lstat(), field) != getattr(denied_info, field)
                       for field in ("st_dev", "st_ino", "st_mode", "st_nlink", "st_uid",
                                     "st_size", "st_mtime_ns", "st_ctime_ns"))):
            raise RuntimeError("Live owned display or empty credential changed during refusal probe")
        receipt["auth_refusal_observed"] = True
        receipt["auth_refusal_evidence"] = {"exit": denied_exit, "raw_wait_status": denied_wait["status"],
            "both_diagnostics": True, "server_alive": True, "owned_display_identity": True,
            "credential_empty": True, "basis": "actual pinned Mesa H7; not full authenticated smoke acceptance"}
        save()
        launch("authenticated-glx", [tools["glxinfo"]["path"], "-B"], gui_env,
               stdin=subprocess.DEVNULL, stdout=raw_log("authenticated-glx.log"), stderr=subprocess.STDOUT)
        if collect("authenticated-glx", 5) != 0:
            raise RuntimeError("Authenticated OpenGL unavailable")
        for handle in handles:
            handle.flush()
        glx = (output / "authenticated-glx.log").read_text(errors="replace")
        if "OpenGL renderer string:" not in glx or "OpenGL version string:" not in glx:
            raise RuntimeError("Actual authenticated GLX backend missing")
        png, report = output / "editor.png", output / "displayed-smoke.json"
        receipt["editor_started_ns"] = time.time_ns()
        command = [str(root / "engine" / ENGINE_NAME), "--editor", "--display-driver", "x11",
                   "--rendering-method", "gl_compatibility", "--rendering-driver", "opengl3",
                   "--audio-driver", "Dummy", "--resolution", "1920x1080", "--path", str(game),
                   "res://zones/kitlab/kitlab.tscn", "--", "--we-show=Ground",
                   "--we-smoke-report=" + str(report), "--we-capture=" + str(png)]
        receipt["editor_command"] = command
        receipt["private_environment"] = {key: gui_env[key] for key in
            ("DISPLAY", "XAUTHORITY", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_RUNTIME_DIR", "TMPDIR")}
        save()
        editor = launch("editor", command, gui_env, stdin=subprocess.DEVNULL)
        deadline = time.monotonic() + 45
        while os.waitid(os.P_PID, editor.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            if os.waitid(os.P_PID, server.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
                raise RuntimeError("Xvfb ended before editor/capture completion")
            if time.monotonic() >= deadline:
                raise TimeoutError("Displayed editor deadline")
            time.sleep(0.02)
        if collect("editor", 1) != 0:
            raise RuntimeError("Displayed editor returned nonzero")
        if os.waitid(os.P_PID, server.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
            raise RuntimeError("Xvfb not alive through editor exit/capture")
        receipt["server_alive_through_editor_exit"] = True
        for p in (png, report):
            info = p.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or info.st_mtime_ns < receipt["editor_started_ns"] or not 0 < info.st_size <= 64 * 1024**2):
                raise RuntimeError("Missing/nonphysical/stale displayed output")
        # The verified private Pillow stage checks the original rendered bytes.
        sys.path.insert(0, str(root / "dependencies"))
        from PIL import Image
        with Image.open(png) as image:
            if image.format != "PNG" or image.size != (1920, 1080):
                raise RuntimeError("Displayed capture is not original1920x1080 PNG")
            image.verify()
        with Image.open(png) as image:
            image.load()
            if not any(lo != hi for lo, hi in image.convert("RGB").getextrema()):
                raise RuntimeError("Displayed viewport capture is empty/flat")
        receipt["capture"] = {"bytes": png.stat().st_size, "sha256": digest(png),
                              "size": [1920, 1080], "pillow_verify": True}
        receipt["report"] = {"bytes": report.stat().st_size, "sha256": digest(report)}
    except BaseException as error:
        failure = {"type": type(error).__name__, "message": str(error)}
    finally:
        # All children are direct, unreaped identities until collect(); never
        # signal a reaped numeric PID. Outer phase still owns last group cleanup.
        for name in reversed(list(children)):
            process = children[name]
            if process.returncode is not None:
                continue
            try:
                if os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
                    os.kill(process.pid, signal.SIGTERM)
                code = collect(name, 2)
                if name == "Xvfb" and code != 0:
                    raise RuntimeError("Xvfb did not terminate cleanly")
            except BaseException as error:
                receipt["cleanup_errors"].append(name + ": " + repr(error))
        for handle in handles:
            handle.close()
        try:
            for p in (authority, denied_authority):
                if p.exists() or p.is_symlink():
                    info = p.lstat()
                    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
                        raise RuntimeError("Authority cleanup refused nonphysical/unowned file")
                    p.unlink()
            receipt["authority_removed"] = not authority.exists() and not denied_authority.exists()
            receipt["display_files_absent"] = all(not os.path.lexists(p) for p in receipt.get("display_files", {}))
            if direct_children() or not receipt["display_files_absent"] or (authority_dir.exists() and list(authority_dir.iterdir())):
                raise RuntimeError("Displayed children/display locks/private authority state remain")
        except BaseException as error:
            receipt["cleanup_errors"].append(repr(error))
        receipt["failure"] = failure
        receipt["state"] = "COLLECTED" if failure is None and not receipt["cleanup_errors"] else "FAILED"
        save()
    return 0 if receipt["state"] == "COLLECTED" else 1


def vulkan_inventory(args: argparse.Namespace) -> int:
    """Bounded installed metadata only; never load a library or choose a driver.

    Exact Vulkan ABI: Godot4.7.2 ed1daf0b vendored vulkan_core.h header335,
    VkExtensionProperties char[256]+uint32 and VkResult int32, SUCCESS0/INCOMPLETE5.
    NULL-layer enumeration can execute implicit layers (Loader1.3.275's
    pre-instance interface); their closure and this installed build's compiled
    discovery roots are not authenticated here. Keep that query NOT RUN.
    """
    output = args.root / "evidence/vulkan-inventory-observation.json"
    result = {"state": "INCOMPLETE", "selectors": {}, "loader": [],
              "directories": [], "manifests": [], "libraries": [], "gaps": [],
              "extension_query": {"state": "NOT RUN", "returncode": None,
                  "extensions": None, "required": ["VK_KHR_surface"],
                  "platform_candidates": ["VK_KHR_xlib_surface", "VK_KHR_xcb_surface", "VK_KHR_wayland_surface"],
                  "reason": "Installed-loader compiled discovery roots and implicit-layer execution closure are unqualified; metadata-only inventory, no native call."},
              "qualification": "Observed host metadata only; no Vulkan/driver/GUI/game acceptance or VSync capability follows."}
    def save() -> None:
        if len(json.dumps(result, sort_keys=True, indent=2).encode()) > 256 * 1024:
            raise RuntimeError("Inventory observation256KiB bound; prior receipt retained")
        write_json(output, result)
    save()
    hashed = 0
    cache = {}
    manifest_bytes = {}
    def observe(path: Path, maximum: int) -> dict:
        nonlocal hashed
        row = {"path": str(path), "exists": path.exists() or path.is_symlink()}
        if not row["exists"]:
            return row
        resolved = path.resolve(strict=True)
        allowed = (Path("/usr/lib/x86_64-linux-gnu"), Path("/usr/share/vulkan"),
                   Path("/usr/local/share/vulkan"), Path("/usr/local/etc/vulkan"),
                   Path("/etc/vulkan"), Path("/etc/xdg/vulkan"))
        if not any(resolved.is_relative_to(base) for base in allowed):
            return {**row, "gap": "Outside bounded canonical system metadata/library roots; not read"}
        info = resolved.stat()
        row.update(canonical=str(resolved), bytes=info.st_size, mode=oct(stat.S_IMODE(info.st_mode)),
                   uid=info.st_uid, gid=info.st_gid, links=info.st_nlink)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o6022
                or not 0 < info.st_size <= maximum):
            return {**row, "gap": "Not a bounded root-owned non-writable regular system file; not read"}
        if str(resolved) not in cache:
            checksum, size, header, chunks = hashlib.sha256(), 0, b"", []
            with resolved.open("rb") as handle:
                for chunk in iter(lambda: handle.read(65536), b""):
                    size += len(chunk)
                    hashed += len(chunk)
                    if size > maximum or hashed > 128 * 1024**2:
                        raise RuntimeError("Inventory file/aggregate input128MiB bound")
                    if not header:
                        header = chunk[:20]
                    checksum.update(chunk)
                    if maximum == 16 * 1024:
                        chunks.append(chunk)
            after = resolved.stat()
            if (size != info.st_size or any(getattr(after, key) != getattr(info, key) for key in
                    ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_mode", "st_uid", "st_gid"))):
                raise RuntimeError("Installed inventory input changed while hashing")
            cache[str(resolved)] = checksum.hexdigest()
            if maximum == 16 * 1024:
                manifest_bytes[str(resolved)] = b"".join(chunks)
            if header.startswith(b"\x7fELF"):
                row["elf"] = {"class": header[4], "byte_order": header[5],
                              "machine": int.from_bytes(header[18:20], "little")}
        row["sha256"] = cache[str(resolved)]
        row["trust"] = "Observed root-owned installed host bytes; not independently authenticated package bytes"
        return row
    try:
        result["host"] = mesa_host()
        candidate = args.candidate.resolve(strict=True)
        headers = git(candidate, "cat-file", "commit", "HEAD").decode().split("\n\n", 1)[0]
        if (git(candidate, "rev-parse", "HEAD").decode().strip() != args.event_sha
                or [line[7:] for line in headers.splitlines() if line.startswith("parent ")]
                != [INVENTORY_RECEIVER_PARENT]
                or git(candidate, "rev-parse", INVENTORY_RECEIVER_PARENT + "^{tree}").decode().strip()
                != INVENTORY_RECEIVER_PARENT_TREE):
            raise RuntimeError("Inventory candidate is not the exact genuine sole-a657 child")
        changed = set(git(candidate, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").decode().splitlines())
        if changed != OWNED_PATHS:
            raise RuntimeError("Inventory candidate must change exactly the two existing receiver paths")
        expected = {}
        for raw in git(candidate, "ls-tree", "-z", "HEAD", "--", *sorted(OWNED_PATHS)).split(b"\0"):
            if raw:
                header, name = raw.split(b"\t", 1)
                mode, kind, sha = header.decode().split()
                expected[os.fsdecode(name)] = (mode, kind, sha)
        if (set(expected) != OWNED_PATHS or any(expected[name] != ("100644", "blob", blob(candidate / name))
                or stat.S_IMODE((candidate / name).stat().st_mode) != 0o644 for name in OWNED_PATHS)):
            raise RuntimeError("Inventory working source bytes/modes differ from immutable event tree")
        result["candidate"] = {"headers": headers, "delta": sorted(changed), "immutable_paths": expected}
        # Selector values are data only. Never dump the environment or modify a selector.
        keys = ("VK_DRIVER_FILES", "VK_ICD_FILENAMES", "VK_ADD_DRIVER_FILES",
                "VK_LOADER_DRIVERS_SELECT", "VK_LOADER_DRIVERS_DISABLE", "VK_LAYER_PATH",
                "VK_ADD_LAYER_PATH", "VK_INSTANCE_LAYERS", "VK_LOADER_LAYERS_ENABLE",
                "VK_LOADER_LAYERS_DISABLE", "VK_LOADER_LAYERS_ALLOW", "VK_LOADER_DISABLE_INST_EXT_FILTER")
        for key in keys:
            value = os.environ.get(key)
            if value is not None and (len(value.encode()) > 4096 or any(ord(c) < 32 for c in value)):
                raise RuntimeError("Inventory selector length/control-character bound")
            result["selectors"][key] = value
        result["dynamic_linker_overrides_present"] = {key: bool(os.environ.get(key)) for key in
                                                     ("LD_LIBRARY_PATH", "LD_PRELOAD", "LD_AUDIT")}
        for path in (Path("/usr/lib/x86_64-linux-gnu/libvulkan.so.1"), Path("/lib/x86_64-linux-gnu/libvulkan.so.1")):
            result["loader"].append(observe(path, 16 * 1024**2))
        home = Path(os.environ["HOME"])
        roots = [os.environ.get("XDG_CONFIG_HOME") or str(home / ".config")]
        for key, default in (("XDG_CONFIG_DIRS", "/etc/xdg"), ("XDG_DATA_DIRS", "/usr/local/share:/usr/share")):
            values = (os.environ.get(key) or default).split(":")
            if len(values) > 4:
                raise RuntimeError("Inventory XDG root-count bound")
            roots += [value for value in values if value]
        roots += ["/usr/local/etc", "/etc", os.environ.get("XDG_DATA_HOME") or str(home / ".local/share")]
        roots = list(dict.fromkeys(roots))
        if len(roots) > 12 or any(not Path(x).is_absolute() or len(x.encode()) > 4096 for x in roots):
            raise RuntimeError("Inventory requires bounded absolute XDG/HOME roots")
        manifests = 0
        for root in roots:
            for suffix in ("icd.d", "implicit_layer.d", "explicit_layer.d"):
                directory = Path(root) / "vulkan" / suffix
                row = {"path": str(directory), "exists": directory.exists() or directory.is_symlink(), "json_files": 0}
                result["directories"].append(row)
                if not row["exists"]:
                    continue
                if directory.is_symlink() or not directory.is_dir():
                    row["gap"] = "Nonphysical directory; not traversed"
                    continue
                entries = []
                for entry in directory.iterdir():
                    entries.append(entry)
                    if len(entries) > 64:
                        raise RuntimeError("Inventory directory-entry64 bound")
                for path in sorted(entries):
                    if path.suffix != ".json":
                        continue
                    manifests += 1
                    row["json_files"] += 1
                    if manifests > 64:
                        raise RuntimeError("Inventory manifest64 bound")
                    record = observe(path, 16 * 1024)
                    record["kind"] = suffix
                    result["manifests"].append(record)
                    if "sha256" not in record:
                        continue
                    document = json.loads(manifest_bytes[record["canonical"]])
                    if not isinstance(document, dict):
                        raise RuntimeError("Inventory manifest must be a JSON object")
                    record["file_format_version"] = document.get("file_format_version")
                    nodes = [document["ICD"]] if suffix == "icd.d" and "ICD" in document else []
                    if suffix != "icd.d":
                        nodes = document.get("layers", [document["layer"]] if "layer" in document else [])
                    if not isinstance(nodes, list) or len(nodes) > 8 or any(not isinstance(x, dict) for x in nodes):
                        raise RuntimeError("Inventory manifest-node8/type bound")
                    record["bindings"] = []
                    for node in nodes:
                        binding = {key: node[key] for key in ("name", "api_version", "library_path", "component_layers", "override_paths") if key in node}
                        if len(json.dumps(binding).encode()) > 8192:
                            raise RuntimeError("Inventory manifest binding8KiB bound")
                        record["bindings"].append(binding)
                        library = node.get("library_path")
                        if library is None:
                            binding["gap"] = "No direct native library binding; layer/component closure not resolved"
                        elif not isinstance(library, str) or not library or len(library.encode()) > 4096:
                            raise RuntimeError("Inventory library-path bound/type")
                        elif "/" not in library:
                            binding["gap"] = "Bare SONAME uses dynamic-linker search; no binding guessed"
                        else:
                            target = Path(library)
                            if not target.is_absolute():
                                target = path.parent / target
                            result["libraries"].append(observe(target, 64 * 1024**2))
                if suffix == "implicit_layer.d" and row["json_files"]:
                    row["gap"] = "Pre-instance query may execute implicit/recursive layers; not loaded"
                save()
        result["gaps"] = ["Standard candidate roots only; installed loader compile-time roots and active driver/layer resolution are unproved.",
                          "Instance extensions/returncode NOT RUN, not absent; no Vulkan/ICD/layer native library was invoked.",
                          "No X11/GLX swap-control query; VSync warning remains separate."]
        result["hashed_input_bytes"] = hashed
        result["state"] = "METADATA_ONLY"
        return 0
    except BaseException as error:
        result["state"] = "INCOMPLETE"
        result["failure"] = {"type": type(error).__name__, "message": str(error)}
        return 1
    finally:
        save()


class Controller:
    def __init__(self, args: argparse.Namespace):
        self.candidate = args.candidate.resolve(strict=True)
        self.source = args.source.resolve(strict=args.mode != "VULKAN_INVENTORY")
        self.root = args.root.resolve(strict=True)
        self.game = self.source / "game"
        self.evidence = self.root / "evidence"
        self.event_sha = args.event_sha
        self.mode = args.mode
        self.active_limit = 60 if self.mode == "DISPLAYED_SMOKE" else 240
        self.phases = {name: {"state": "NOT RUN"} for name in ("dependencies", "versions", "canary", "import", "check-only", "python-canaries", "focused", "python-faults")}
        self.guards = {}
        self.engine = self.root / "engine" / ENGINE_NAME
        self.initial = None
        self.candidate_initial = None
        self.output = {"state": "SETUP_FAILED", "workflow_sha": self.event_sha,
                       "tested_game_sha": GAME_SHA, "tested_game_tree": GAME_TREE,
                       "phases": self.phases, "guards": self.guards,
                       "qualification": "Sixteen unexecuted combined controls until this exact allocated invocation. No displayed GUI/full-suite/Ready/whole-editor acceptance."}
        self.output["methods"] = {m: "NOTRUN" for m in
                                  PY_CANARIES + METHODS + PY_FAULTS}
        self.output["mode"] = self.mode
        if self.mode == "DISPLAYED_SMOKE":
            self.phases["display-tool"] = {"state": "NOT RUN"}
            self.phases["displayed-smoke"] = {"state": "NOT RUN"}
            self.output["qualification"] = "Displayed existing editor smoke only: undo/restoration and bake refusals. No H5 rerun, successful save/bake/walk or manual acceptance."
            self.output["prior_h5"] = {"receiver": DISPLAY_RECEIVER_PARENT, "source": GAME_SHA,
                                       "result_and_release": 6535314296, "controls": "16 PASS frozen; not repeated"}
        self.dependencies_initial = None
        self.generated_uids_initial = None
        self.transaction_started = None
        self.collection_used = 0.0
        self.budget_failure = None
        self.terminal_started = None
        self.owned_roots = (self.root, self.source, self.candidate)
        if self.mode == "VULKAN_INVENTORY":
            self.active_limit = 15
            self.owned_roots = (self.root, self.candidate)
            self.phases["vulkan-inventory"] = {"state": "NOT RUN"}
            self.output["qualification"] = "Metadata-only Vulkan inventory. Engine, project, scientific dependencies, native query, GUI and all H5 controls NOT RUN; no driver acceptance."

    def budget_remaining(self) -> float:
        if self.transaction_started is None:
            # Setup/import are separate phases. Their failed terminal retention
            # gets at most30s, never a fresh successful sixteen-control transaction.
            return 30 - (time.monotonic() - self.terminal_started)
        return min(self.active_limit - (time.monotonic() - self.transaction_started - self.collection_used),
                   self.active_limit + 30 - (time.monotonic() - self.transaction_started))

    def budget_expired(self, _signum: int = 0, _frame: object = None) -> None:
        self.budget_failure = "Whole transaction active/collection or failed-setup terminal budget exhausted"
        raise TimeoutError(self.budget_failure)

    def arm_budget(self) -> None:
        remaining = self.budget_remaining()
        if self.budget_failure or remaining <= 0 or self.collection_used > 30:
            self.budget_expired()
        # Covers between-phase audits, finite copy/hash chunks and terminal work.
        # The phase finally disarms this before identity-safe kill/wait/absence;
        # expiry itself never establishes collection or release.
        signal.setitimer(signal.ITIMER_REAL, remaining)

    def budget_receipt(self) -> dict:
        now = time.monotonic()
        wall = None if self.transaction_started is None else now - self.transaction_started
        return {"wall_s": wall, "active_s": None if wall is None else wall - self.collection_used,
                "collection_s": self.collection_used, "active_limit_s": self.active_limit,
                "collection_limit_s": 30, "failure": self.budget_failure,
                "terminal_s": None if self.terminal_started is None else now - self.terminal_started,
                "qualification": "Controller transaction only; checkout/setup/import and network artifact upload have the separate15min job outer. Blocking OS calls may delay observation; measured overrun fails closed."}

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
        if self.mode == "VULKAN_INVENTORY" and sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file()) > 1024**2:
            raise RuntimeError("Inventory logs+outputs1MiB limit")
        if used > (64 * 1024**2 if self.mode == "VULKAN_INVENTORY" else OWNED_LIMIT) or free < FREE_RESERVE:
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
        if game_rows["game/game.gd"]["blob"] != PRODUCTION_BLOB:
            raise RuntimeError("Frozen test/production pin differs")
        for path, expected_blob, methods in GD_SUITES.values():
            if game_rows[path]["blob"] != expected_blob:
                raise RuntimeError("Frozen GdUnit suite pin differs")
            test_text = (self.source / path).read_text()
            if tuple(re.findall(r"^func (test_\w+)\(", test_text, re.M)) != methods:
                raise RuntimeError("Frozen ten-method GdUnit inventory differs")
        if len(METHODS) != 10 or len(set(METHODS)) != 10:
            raise RuntimeError("Combined GdUnit identities are not ten distinct methods")
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

    def generated_uids(self) -> dict:
        """Guard only the two importer-generated test UIDs; other source stays strict."""
        expected = tree(self.source)
        rows = {}
        for raw in git(self.source, "ls-files", "--others", "-z").split(b"\0"):
            if not raw:
                continue
            name = os.fsdecode(raw)
            if name.startswith(("game/.godot/", "game/" + REPORT_DIR + "/")):
                continue
            if name not in GENERATED_UID_PATHS:
                raise RuntimeError(f"Unexpected untracked source output: {name}")
        for name in GENERATED_UID_PATHS:
            p = self.source / name
            if name in expected or p.is_symlink():
                raise RuntimeError("Generated UID is tracked or a symlink")
            if not p.exists():
                continue
            info = p.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or not p.resolve(strict=True).is_relative_to(self.game)
                    or info.st_mode & 0o111 or not 1 <= info.st_size <= 64):
                raise RuntimeError("Generated UID is not a bounded private physical file")
            data = p.read_bytes()
            if not re.fullmatch(rb"uid://[a-z0-9]+\n?", data):
                raise RuntimeError("Generated UID content is not an engine UID")
            rows[name] = {"bytes": len(data), "sha256": digest(p), "mode": stat.S_IMODE(info.st_mode)}
        if self.generated_uids_initial is not None:
            for name, row in self.generated_uids_initial.items():
                if rows.get(name) != row:
                    raise RuntimeError("An observed post-import UID changed or disappeared")
        return rows

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
        if (any((self.game / name).exists() for name in (".godot", REPORT_DIR))
                or any((self.source / name).exists() or (self.source / name).is_symlink()
                       for name in GENERATED_UID_PATHS)):
            raise RuntimeError("Project has prior import/report/UID state; requires fresh physical checkout")
        # The workflow opens controller.log before spawning this process.
        if set(self.root.iterdir()) != {self.evidence} or set(self.evidence.iterdir()) != {
            self.evidence / "bootstrap.json", self.evidence / "controller.log"
        }:
            raise RuntimeError("Duty runtime/evidence is not fresh")
        headers = git(self.candidate, "cat-file", "commit", "HEAD").decode().split("\n\n", 1)[0]
        parents = [line.removeprefix("parent ") for line in headers.splitlines() if line.startswith("parent ")]
        if parents != [INVENTORY_RECEIVER_PARENT]:
            raise RuntimeError("Inventory receiver must be a genuine sole child of frozen405a657")
        inventory_parent_headers = git(self.candidate, "cat-file", "commit", INVENTORY_RECEIVER_PARENT).decode().split("\n\n", 1)[0]
        if ([line.removeprefix("parent ") for line in inventory_parent_headers.splitlines() if line.startswith("parent ")]
                != [AUTH_RECEIVER_PARENT] or git(self.candidate, "rev-parse", INVENTORY_RECEIVER_PARENT + "^{tree}").decode().strip()
                != INVENTORY_RECEIVER_PARENT_TREE):
            raise RuntimeError("Frozen H8 auth-refusal receiver ancestry/tree changed")
        auth_parent_headers = git(self.candidate, "cat-file", "commit", AUTH_RECEIVER_PARENT).decode().split("\n\n", 1)[0]
        if ([line.removeprefix("parent ") for line in auth_parent_headers.splitlines() if line.startswith("parent ")]
                != [TOOL_RECEIVER_PARENT] or git(self.candidate, "rev-parse", AUTH_RECEIVER_PARENT + "^{tree}").decode().strip()
                != AUTH_RECEIVER_PARENT_TREE):
            raise RuntimeError("Frozen H7 tool receiver ancestry/tree changed")
        tool_parent_headers = git(self.candidate, "cat-file", "commit", TOOL_RECEIVER_PARENT).decode().split("\n\n", 1)[0]
        if ([line.removeprefix("parent ") for line in tool_parent_headers.splitlines() if line.startswith("parent ")]
                != [DISPLAY_RECEIVER_PARENT] or git(self.candidate, "rev-parse", TOOL_RECEIVER_PARENT + "^{tree}").decode().strip()
                != TOOL_RECEIVER_PARENT_TREE):
            raise RuntimeError("Frozen H6 receiver ancestry/tree changed")
        display_parent_headers = git(self.candidate, "cat-file", "commit", DISPLAY_RECEIVER_PARENT).decode().split("\n\n", 1)[0]
        if ([line.removeprefix("parent ") for line in display_parent_headers.splitlines() if line.startswith("parent ")]
                != [RECEIVER_PARENT] or git(self.candidate, "rev-parse", DISPLAY_RECEIVER_PARENT + "^{tree}").decode().strip()
                != DISPLAY_RECEIVER_PARENT_TREE):
            raise RuntimeError("Frozen H5 receiver ancestry/tree changed")
        prior_headers = git(self.candidate, "cat-file", "commit", RECEIVER_PARENT).decode().split("\n\n", 1)[0]
        if ([line.removeprefix("parent ") for line in prior_headers.splitlines() if line.startswith("parent ")]
                != [PRIOR_RECEIVER] or git(self.candidate, "rev-parse", RECEIVER_PARENT + "^{tree}").decode().strip()
                != RECEIVER_PARENT_TREE):
            raise RuntimeError("Rebound405 receiver ancestry/tree changed")
        middle_headers = git(self.candidate, "cat-file", "commit", PRIOR_RECEIVER).decode().split("\n\n", 1)[0]
        if ([line.removeprefix("parent ") for line in middle_headers.splitlines() if line.startswith("parent ")]
                != [EARLIER_RECEIVER] or git(self.candidate, "rev-parse", PRIOR_RECEIVER + "^{tree}").decode().strip()
                != PRIOR_RECEIVER_TREE):
            raise RuntimeError("Profile405 receiver ancestry/tree changed")
        earlier_headers = git(self.candidate, "cat-file", "commit", EARLIER_RECEIVER).decode().split("\n\n", 1)[0]
        if ([line.removeprefix("parent ") for line in earlier_headers.splitlines() if line.startswith("parent ")]
                != [OLDER_RECEIVER] or git(self.candidate, "rev-parse", EARLIER_RECEIVER + "^{tree}").decode().strip()
                != EARLIER_RECEIVER_TREE):
            raise RuntimeError("Profile405 receiver ancestry/tree changed")
        older_headers = git(self.candidate, "cat-file", "commit", OLDER_RECEIVER).decode().split("\n\n", 1)[0]
        if ([line.removeprefix("parent ") for line in older_headers.splitlines() if line.startswith("parent ")]
                != [ORIGINAL_RECEIVER] or git(self.candidate, "rev-parse", OLDER_RECEIVER + "^{tree}").decode().strip()
                != OLDER_RECEIVER_TREE):
            raise RuntimeError("Corrected405 receiver ancestry/tree changed")
        original_headers = git(self.candidate, "cat-file", "commit", ORIGINAL_RECEIVER).decode().split("\n\n", 1)[0]
        if ([line.removeprefix("parent ") for line in original_headers.splitlines() if line.startswith("parent ")]
                != [ORIGINAL_GAME_SHA] or git(self.candidate, "rev-parse", ORIGINAL_RECEIVER + "^{tree}").decode().strip()
                != ORIGINAL_RECEIVER_TREE):
            raise RuntimeError("Original405 receiver ancestry/tree changed")
        source_headers = git(self.source, "cat-file", "commit", "HEAD").decode().split("\n\n", 1)[0]
        if [line.removeprefix("parent ") for line in source_headers.splitlines()
                if line.startswith("parent ")] != [GAME_PARENT]:
            raise RuntimeError("Combined407 must retain genuine52 sole parent")
        source_parent_headers = git(self.source, "cat-file", "commit", GAME_PARENT).decode().split("\n\n", 1)[0]
        if ([line.removeprefix("parent ") for line in source_parent_headers.splitlines() if line.startswith("parent ")]
                != [GAME_GRANDPARENT] or git(self.source, "rev-parse", GAME_PARENT + "^{tree}").decode().strip()
                != GAME_PARENT_TREE):
            raise RuntimeError("Corrected398 export parent ancestry/tree changed")
        source_grandparent_headers = git(self.source, "cat-file", "commit", GAME_GRANDPARENT).decode().split("\n\n", 1)[0]
        if ([line.removeprefix("parent ") for line in source_grandparent_headers.splitlines() if line.startswith("parent ")]
                != [ORIGINAL_GAME_SHA] or git(self.source, "rev-parse", GAME_GRANDPARENT + "^{tree}").decode().strip()
                != GAME_GRANDPARENT_TREE):
            raise RuntimeError("Corrected398 bake parent ancestry/tree changed")
        baseline_headers = git(self.source, "cat-file", "commit", ORIGINAL_GAME_SHA).decode().split("\n\n", 1)[0]
        if [line.removeprefix("parent ") for line in baseline_headers.splitlines()
                if line.startswith("parent ")] != [ORIGINAL_GAME_PARENT]:
            raise RuntimeError("Original398 must retain genuine375 sole parent")
        for repo in (self.source, self.candidate):
            if git(repo, "rev-parse", ORIGINAL_GAME_SHA + "^{tree}").decode().strip() != ORIGINAL_GAME_TREE:
                raise RuntimeError("Original game baseline tree differs")
        source_tree, candidate_tree = tree(self.source), tree(self.candidate)
        baseline_tree = tree(self.source, ORIGINAL_GAME_SHA)
        # The corrected production child is deliberately NOT a receiver ancestor.
        delta = {name for name in baseline_tree.keys() | candidate_tree.keys()
                 if baseline_tree.get(name) != candidate_tree.get(name)}
        if delta != OWNED_PATHS or any(name in baseline_tree for name in OWNED_PATHS):
            raise RuntimeError(f"Two NEW receiving paths only: {sorted(delta)}")
        production_delta = {name for name in baseline_tree.keys() | source_tree.keys()
                            if baseline_tree.get(name) != source_tree.get(name)}
        if (production_delta != {"scripts/art/kit/bake.py", "game/tools/kit_zone.gd", DEPENDENT_TEST_PATH,
                                  "game/world/terrain/kit_piece.gd", "game/world/terrain/terrain_ground.gd"}
                or source_tree.get("scripts/art/kit/bake.py") != ("100644", PYTHON_INPUTS["scripts/art/kit/bake.py"][0])
                or source_tree.get("game/tools/kit_zone.gd") != ("100644", EXPORT_BLOB)
                or source_tree.get(DEPENDENT_TEST_PATH) != ("100644", DEPENDENT_TEST_BLOB)
                or source_tree.get("game/world/terrain/kit_piece.gd") != ("100644", KIT_PIECE_BLOB)
                or source_tree.get("game/world/terrain/terrain_ground.gd") != ("100644", GROUND_BLOB)):
            raise RuntimeError(f"Combined407 must change only five pinned production paths: {sorted(production_delta)}")
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
        write_json(self.evidence / "generated-uids-before.json", self.generated_uids())
        write_json(self.evidence / "source-before.json", self.initial)
        write_json(self.evidence / "candidate.json", {"event_sha": self.event_sha,
                   "tree": git(self.candidate, "rev-parse", "HEAD^{tree}").decode().strip(),
                   "commit_headers": headers, "tested_game_sha": GAME_SHA,
                    "receiver_parent": INVENTORY_RECEIVER_PARENT, "receiver_parent_headers": inventory_parent_headers,
                    "auth_receiver_parent": AUTH_RECEIVER_PARENT, "auth_receiver_parent_headers": auth_parent_headers,
                   "tool_receiver_parent": TOOL_RECEIVER_PARENT, "tool_receiver_parent_headers": tool_parent_headers,
                   "display_receiver_parent": DISPLAY_RECEIVER_PARENT, "display_receiver_parent_headers": display_parent_headers,
                   "h5_receiver_parent": RECEIVER_PARENT, "h5_receiver_parent_headers": prior_headers,
                   "prior_receiver": PRIOR_RECEIVER, "prior_receiver_headers": middle_headers,
                   "earlier_receiver": EARLIER_RECEIVER, "earlier_receiver_headers": earlier_headers,
                   "older_receiver": OLDER_RECEIVER, "older_receiver_headers": older_headers,
                   "original_receiver": ORIGINAL_RECEIVER, "original_receiver_headers": original_headers,
                   "original_game_sha": ORIGINAL_GAME_SHA, "original_game_tree": ORIGINAL_GAME_TREE,
                   "original_game_headers": baseline_headers, "production_delta": sorted(production_delta),
                   "tested_game_tree": GAME_TREE, "tested_game_headers": source_headers,
                   "tested_game_parent": GAME_PARENT, "tested_game_parent_headers": source_parent_headers,
                   "tested_game_grandparent": GAME_GRANDPARENT, "tested_game_grandparent_headers": source_grandparent_headers,
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
        if self.mode == "DISPLAYED_SMOKE":
            for key in ("DISPLAY", "XAUTHORITY", "WAYLAND_DISPLAY"):
                self.env.pop(key, None)
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
                   "closure_qualification": ("48 pinned Python/config inputs + full game; existing kitlab five-piece smoke only, no successful bake/painter/new generation."
                       if self.mode == "DISPLAYED_SMOKE" else "48 pinned Python/config inputs + full game; lawn-only pieces=[] probe. No master-raster load, original paint execution or new generation is granted."),
                   "scientific_stage": "Fresh private target; exact versions, all package byte hashes before/after. Counted inside reviewed768MiB duty, not hidden staging; full import/test/packaging fit UNMEASURED.",
                   "fit": ("DISPLAYED_SMOKE fit at768MiB UNMEASURED; prior frozen79a H5 measured in result6535314296; no automatic increase"
                       if self.mode == "DISPLAYED_SMOKE" else "Full import/test/packaging fit at768MiB UNMEASURED; no automatic budget increase"),
                   "owned_profile_provenance": {
                       "source_only_go": 6532961903, "h1_result": 6532930623,
                       "independent_receipt": 6532962554,
                       "prior_owned_limit_bytes": 512 * 1024**2,
                       "h1_refused_owned_bytes": 537354240,
                       "complete_extraction_projection_bytes": 608271152,
                       "after_verified_zip_retirement_projection_bytes": 530410728,
                       "qualification": "H1 stopped during extraction before canary/import/the original eight persistence controls. Projections hold other H1 footprint fixed; they are not measured complete extraction or import/test/packaging fit. Original partials retained; no guard waived."},
                   "limits": {
                       "rss_group_bytes": RSS_LIMIT, "owned_bytes": OWNED_LIMIT,
                       "address_space_per_process": 4 * 1024**3,
                       "test_output_bytes": 64 * 1024**2, "import_active_s": 180,
                       "whole_sixteen_active_s": 240, "whole_sixteen_collection_s": 30,
                       "selected_mode": self.mode, "selected_active_s": self.active_limit,
                       "displayed_smoke_active_s": 60, "displayed_smoke_collection_s": 30,
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

    def prepare_display_tool(self) -> None:
        host = mesa_host()
        installed = installed_mesa()
        # Refuse every other missing display prerequisite before any acquisition.
        self.display_capabilities("display-capabilities-before-tool.json", missing_glx_ok=True)
        bootstrap = {}
        for name in (("ldd", "dpkg-deb") if installed is None else ("ldd",)):
            found = shutil.which(name)
            if not found:
                raise RuntimeError("Missing actual Mesa bootstrap capability: " + name)
            path = Path(found).resolve(strict=True)
            bootstrap[name] = {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}
        plan = {"host": host, "installed": installed, "bootstrap": bootstrap, "package": MESA_PACKAGE,
                "bounds": {"phase_active_s": 30, "shared_dependency_active_s": 120,
                           "compressed_bytes": 164440, "expanded_bytes": 2 * 1024**2,
                           "selected_member_bytes": 256 * 1024, "entries": 64},
                "qualification": "Installed canonical package first; only absence allows this one fixed private package. Payload/metadata proposed<=2MiB plus existing4MiB phase log, all inside768MiB duty; fit UNMEASURED."}
        write_json(self.evidence / "display-tool-plan.json", plan)
        result = self.phase("display-tool", [sys.executable, "-I", "-B", str(Path(__file__).resolve()),
            "--mode", "DISPLAYED_SMOKE", "--mesa-tool-child", "--candidate", str(self.candidate),
            "--source", str(self.source), "--root", str(self.root), "--event-sha", self.event_sha], 30)
        self.require_clean("display-tool", result)
        receipt = json.loads((self.evidence / "display-tool/provenance.json").read_text())
        if (receipt.get("state") != "VERIFIED" or len(receipt.get("wait4", [])) != (3 if installed is None else 1)
                or any(row["exit"] != 0 for row in receipt.get("wait4", []))):
            raise RuntimeError("Mesa tool stage not actually verified/collected")
        self.glxinfo_identity = receipt["binary"]
        self.display_tool_plan = plan
        write_json(self.evidence / "display-tool-before.json", self.glxinfo_identity)

    def display_capabilities(self, receipt_name: str = "display-capabilities.json", missing_glx_ok: bool = False) -> dict:
        tools, missing = {}, []
        for name in ("Xvfb", "xauth", "glxinfo"):
            if name == "glxinfo":
                identity = getattr(self, "glxinfo_identity", None)
                if identity is None or identity["origin"] == "installed Ubuntu dpkg package":
                    actual = installed_mesa()
                else:
                    actual = {**mesa_binary(Path(identity["path"])), "origin": identity["origin"],
                              "package_sha256": digest(self.evidence / "display-tool/mesa-utils-bin_9.0.0-2_amd64.deb")}
                    if actual["package_sha256"] != MESA_PACKAGE["sha256"]:
                        raise RuntimeError("Retained Mesa package changed")
                if identity is not None and actual != identity:
                    raise RuntimeError("Selected Mesa tool/package identity changed")
                if actual is None:
                    missing.append(name)
                else:
                    tools[name] = actual
                continue
            found = shutil.which(name)
            if found is None:
                missing.append(name)
                continue
            path = Path(found).resolve(strict=True)
            if not path.is_file() or not os.access(path, os.X_OK):
                missing.append(name)
                continue
            tools[name] = {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}
        # Loader lookup only: no unmonitored ldconfig/compiler/package process.
        libraries = {}
        for name in ("libGL.so.1", "libGLX.so.0"):
            try:
                libraries[name] = ctypes.CDLL(name)._name
            except OSError:
                libraries[name] = None
        missing += [name for name, value in libraries.items() if not value]
        bootstrap = {}
        for name, row in getattr(self, "display_tool_plan", {}).get("bootstrap", {}).items():
            path = Path(row["path"])
            bootstrap[name] = {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}
            if bootstrap[name] != row:
                raise RuntimeError("Mesa bootstrap executable changed after staging")
        value = {"tools": tools, "bootstrap": bootstrap, "libraries": libraries, "missing": missing, "host": mesa_host(),
                 "qualification": "Canonical installed package identity or exact private pinned Mesa member; real authenticated GLX/editor still required. No system install/unpinned fallback."}
        write_json(self.evidence / receipt_name, value)
        if [name for name in missing if not (missing_glx_ok and name == "glxinfo")]:
            raise RuntimeError("Missing hosted display capability: " + ", ".join(missing))
        return value

    def displayed_smoke(self) -> None:
        output = self.root / "test-output/displayed-smoke"
        output.mkdir(mode=0o700)
        if self.display_capabilities("display-capabilities-after-import.json") != self.display_capabilities_initial:
            raise RuntimeError("Host display capabilities changed before GUI phase")
        result = self.phase("displayed-smoke", [sys.executable, "-I", "-B", str(Path(__file__).resolve()),
            "--mode", "DISPLAYED_SMOKE", "--display-child", "--candidate", str(self.candidate),
            "--source", str(self.source), "--root", str(self.root), "--event-sha", self.event_sha], 60)
        text = self.require_clean("displayed-smoke", result)
        lifetime = json.loads((output / "lifetime.json").read_text())
        report_path, png = output / "displayed-smoke.json", output / "editor.png"
        report = json.loads(report_path.read_text())
        lines = re.findall(r"^WORLD_EDITOR_SMOKE (.+)$", text, re.M)
        if len(lines) != 1 or json.loads(lines[0]) != report:
            raise RuntimeError("Displayed file JSON is not the one actual logged smoke result")
        if (report.get("ok") is not True or report.get("failures") != []
                or report.get("pieces") != 5 or report.get("captures") != [str(png)]
                or report.get("gestures") != {"cases": 6, "tools": ["brush", "rectangle", "route", "variant"],
                                               "cancellations": ["escape", "lost_button"]}
                or any(type(report.get(key)) is not int or report[key] <= 0
                       for key in ("palette_materials", "palette_pieces"))):
            raise RuntimeError("Existing displayed smoke did not meet its exact report contract")
        expected = {"xauth", "Xvfb", "unauthorized-glx", "authenticated-glx", "editor"}
        waits = lifetime.get("wait4", [])
        exits = {row["name"]: row["exit"] for row in waits}
        processes = lifetime.get("processes", {})
        if (lifetime.get("state") != "COLLECTED" or lifetime.get("failure") is not None
                or lifetime.get("cleanup_errors") != [] or set(exits) != expected or len(waits) != len(expected)
                or set(processes) != expected or lifetime.get("pid") != result["pid"]
                or lifetime.get("pgid") != result["pgid"] or not lifetime.get("auth_refusal_observed")
                or not lifetime.get("server_alive_through_editor_exit")
                or any(exits[name] != 0 for name in expected - {"unauthorized-glx"})
                or exits["unauthorized-glx"] != 1 or not lifetime.get("authority_removed")
                or not lifetime.get("display_files_absent")
                or any(row["pgid"] != result["pgid"] or row["ppid"] != result["pid"]
                       for row in processes.values())):
            raise RuntimeError("Displayed authentication/server/editor actual collection incomplete")
        for key, path in (("capture", png), ("report", report_path)):
            row = lifetime.get(key, {})
            if row.get("sha256") != digest(path) or row.get("bytes") != path.stat().st_size:
                raise RuntimeError("Displayed output changed after lifetime receipt")
        if lifetime["capture"].get("size") != [1920, 1080] or lifetime["capture"].get("pillow_verify") is not True:
            raise RuntimeError("Original1920x1080 capture verification missing")
        backend = [line for line in text.splitlines()
                   if "OpenGL API" in line and "Compatibility" in line and "Using Device:" in line]
        if len(backend) != 1:
            raise RuntimeError("Actual editor OpenGL compatibility backend not observed")
        for name in ("xvfb.log", "unauthorized-glx.log", "authenticated-glx.log"):
            if (output / name).stat().st_size > LOG_LIMIT:
                raise RuntimeError("Display tool raw-log limit exceeded")
        self.output["displayed_smoke"] = {"state": "PASS_PENDING_TERMINAL_GUARDS", "report": report,
            "capture": lifetime["capture"], "render_backend": backend, "lifetime": lifetime,
            "source_pins": {name: self.initial["game"][name] for name in
                ("game/addons/world_editor/plugin.gd", "game/addons/world_editor/smoke.gd", "game/zones/kitlab/kitlab.tscn")},
            "qualification": "Real displayed existing smoke; scene restored without SAVE, bake refusals only. No successful author/save/reopen/export/bake/reimport/walk/collision or manual acceptance."}
        self.output["state"] = "DISPLAYED_SMOKE_PENDING_TERMINAL_GUARDS"

    def retire_display_authority(self) -> None:
        # Never copy/hash cookie bytes into evidence. Also runs if the lifetime
        # was killed, after phase() has attempted actual group collection.
        directory = self.root / "runtime/display-authority"
        removed = []
        for name in ("Xauthority", "no-authority"):
            path = directory / name
            if not os.path.lexists(path):
                continue
            info = path.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > 4096):
                raise RuntimeError("Private display authority retirement refused unsafe metadata")
            path.unlink()
            removed.append(name)
        if directory.exists() and list(directory.iterdir()):
            raise RuntimeError("Private display authority has unexpected residual files")
        write_json(self.evidence / "display-authority-retired.json", {"removed_names": removed,
                   "empty": True, "cookie_recorded": False})

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
        if name in ("display-tool", "dependencies", "versions") and hasattr(self, "dependency_deadline"):
            remaining = self.dependency_deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("Shared tool/scientific dependency120s budget exhausted")
            seconds = min(seconds, remaining)
        if self.transaction_started is not None:
            remaining = self.active_limit - (time.monotonic() - self.transaction_started - self.collection_used)
            if remaining <= 0 or self.collection_used >= 30:
                raise RuntimeError("Selected-mode active/collection aggregate budget exhausted")
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
                address_limit = 256 * 1024**2 if self.mode == "VULKAN_INVENTORY" else 4 * 1024**3
                file_limit = 1024**2 if self.mode == "VULKAN_INVENTORY" else 64 * 1024**2
                resource.setrlimit(resource.RLIMIT_AS, (address_limit, address_limit))
                resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))
            # Do not inject an asynchronous exception into Popen's ownership
            # handoff (child may exist before the handle is returned). The
            # existing phase monitor and actual collection deadlines take over;
            # all elapsed time is still charged and checked after collection.
            signal.setitimer(signal.ITIMER_REAL, 0)
            process = subprocess.Popen(command, cwd=self.candidate if self.mode == "VULKAN_INVENTORY" else self.game, env=self.env, start_new_session=True,
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
                    if rss > (256 * 1024**2 if self.mode == "VULKAN_INVENTORY" else RSS_LIMIT):
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
                            remaining = (1024**2 if self.mode == "VULKAN_INVENTORY" else LOG_LIMIT) - total
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
            # Never asynchronously interrupt the existing identity-safe actual
            # collection. Its original bounded wait deadlines remain authoritative.
            signal.setitimer(signal.ITIMER_REAL, 0)
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
                    reason = reason or "Selected-mode collection exceeded30s"
                result["aggregate_active_s"] = time.monotonic() - self.transaction_started - self.collection_used
                result["aggregate_collection_s"] = self.collection_used
            result.update(state="FAILED" if reason else "COLLECTED", controller_error=reason,
                          elapsed_s=time.monotonic() - started, finished_at=time.time())
            if log_path.exists():
                result.update(log_sha256=digest(log_path), log_bytes=log_path.stat().st_size)
            write_json(self.evidence / (name + ".json"), result)
            if self.transaction_started is not None:
                self.arm_budget()
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
        """Read both vendored suites; actual case children establish execution."""
        self.output["state"] = "FOCUSED_RESULTS_UNCLASSIFIED"
        reports = self.game / REPORT_DIR
        files = sorted(reports.rglob("results.xml")) if reports.exists() else []
        text = diagnostic_text(self.evidence / "focused.log")
        findings = {
            "expected": list(METHODS), "observed": [], "methods": {m: "NOTRUN" for m in METHODS},
            "expected_suites": {name: list(spec[2]) for name, spec in GD_SUITES.items()},
            "expected_discovered": len(METHODS),
            "raw_error_headers": [line for line in text.splitlines() if ERROR_PATTERN.search(line)],
            "python_validator_errors": [line for line in text.splitlines() if PYTHON_ERROR_PATTERN.search(line)],
            "orphan_diagnostics": orphan_diagnostics(text), "totals": [],
            "xml_files": [str(p.relative_to(self.game)) for p in files], "case_evidence": [],
        }
        try:
            if len(files) != 1:
                raise RuntimeError("Need exactly one fresh vendored JUnit results.xml")
            root = ET.parse(files[0]).getroot()
            suites = list(root.findall("testsuite"))
            suite_names = [suite.get("name", "") for suite in suites]
            if (root.tag != "testsuites" or not suites
                    or suite_names != list(GD_SUITES)[:len(suites)]):
                raise RuntimeError("JUnit suites are not the requested ordered pair/prefix")
            root_values = {key: int(root.get(key, "0"))
                           for key in ("tests", "failures", "errors", "skipped", "flaky")}
            findings["totals"].append(dict(suite="ALL", **root_values))
            findings["reported_discovered"] = root_values["tests"]
            if any(root_values[k] for k in ("errors", "skipped", "flaky")):
                raise RuntimeError("XML errors/skips/flaky cannot qualify as combined GREEN")
            cases_all, names_all, failed = [], [], []
            failure_count = declared_count = 0
            for suite in suites:
                suite_name = suite.get("name")
                expected_methods = GD_SUITES[suite_name][2]
                values = {key: int(suite.get(key, "0"))
                          for key in ("tests", "failures", "errors", "skipped", "flaky")}
                findings["totals"].append(dict(suite=suite_name, **values))
                if (suite.get("package") != "test" or values["tests"] != len(expected_methods)
                        or any(values[k] for k in ("errors", "skipped", "flaky"))):
                    raise RuntimeError("Wrong per-suite identity/discovery/error counts")
                declared_count += values["tests"]
                cases = list(suite.findall("testcase"))
                names = [case.get("name", "") for case in cases]
                if not names or names != list(expected_methods[:len(names)]):
                    raise RuntimeError("Unexpected/duplicate/non-prefix methods in requested suite")
                cases_all.extend(cases)
                names_all.extend(names)
                findings["observed"] = names_all
                suite_failures = 0
                suite_failed = []
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
                        suite_failed.append(name)
                    suite_failures += len(failures)
                if values["failures"] != suite_failures:
                    raise RuntimeError("Per-suite failure totals disagree with failure elements")
                if suite_failed and suite_failed != [names[-1]]:
                    raise RuntimeError("Suite cases do not match vendored fail-fast semantics")
                if not suite_failed and names != list(expected_methods):
                    raise RuntimeError("Suite stopped without a target assertion")
                failure_count += suite_failures
            # Fail-fast breaks the inner case loop, not the executor's suite
            # loop. Each suite has its own execution prefix; absent cases stay
            # NOTRUN even though the writer declares that suite's full size.
            if list(root.iter("testcase")) != cases_all:
                raise RuntimeError("Unexpected testcase outside the requested suites")
            if root_values["tests"] != declared_count or root_values["failures"] != failure_count:
                raise RuntimeError("Root counters disagree with actual suite/case evidence")
            if (result["state"] != "COLLECTED" or result.get("exit") is None
                    or findings["raw_error_headers"] or findings["python_validator_errors"]
                    or findings["orphan_diagnostics"]):
                raise RuntimeError("Controller/raw engine/Python/orphan errors are not target editor RED")
            if not failed:
                if suite_names != list(GD_SUITES) or names_all != list(METHODS) or result["exit"] != 0:
                    raise RuntimeError("Incomplete success/exit is not ten passing GdUnit methods")
                self.output["state"] = "TEN_GDUNIT_PASS"
                self.output["focused_suite_pass"] = True
            elif result["exit"] == 100:
                self.output["state"] = "COMBINED_GDUNIT_ASSERTION_FAIL_REQUIRES_LEAD_REVIEW"
            else:
                raise RuntimeError("Failure/exit does not match actual fail-fast assertion semantics")
        finally:
            self.output["methods"].update(findings["methods"])
            findings["classification"] = self.output["state"]
            write_json(self.evidence / "focused-inventory.json", findings)

    def inventory_only(self) -> int:
        """Use the existing monitored phase/actual collection, without full setup."""
        self.transaction_started = time.monotonic()
        errors = []
        observation = None
        try:
            self.arm_budget()
            if (self.mode != "VULKAN_INVENTORY" or sys.platform != "linux" or sys.version_info[:2] != (3, 12)
                    or os.environ.get("GITHUB_RUN_ATTEMPT") != "1"
                    or os.environ.get("GITHUB_REF") != "refs/heads/codex/editor-persistence-validation-run"
                    or self.event_sha != os.environ.get("GITHUB_SHA")
                    or not re.fullmatch(r"[0-9a-f]{40}", self.event_sha)):
                raise RuntimeError("Inventory requires its exact allocated Linux/CPython3.12 event/ref/attempt1")
            workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve(strict=True)
            if (self.candidate != workspace / "runner" or self.source != workspace / "source"
                    or self.source.exists() or self.source.is_symlink()
                    or self.root != Path(os.environ["RUNNER_TEMP"]).resolve(strict=True) / "editor-persistence"
                    or set(self.root.iterdir()) != {self.evidence}
                    or set(self.evidence.iterdir()) != {self.evidence / "bootstrap.json", self.evidence / "controller.log"}):
                raise RuntimeError("Inventory requires fresh receiver-only checkout/evidence; no production checkout")
            if (not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal")
                    or Path(os.environ.get("PYTHON", "")).resolve(strict=True) != Path(sys.executable).resolve(strict=True)):
                raise RuntimeError("Inventory requires existing explicit Python and identity-safe collection")
            os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
            roots = {"XDG_CONFIG_HOME": self.root / "config", "XDG_DATA_HOME": self.root / "data",
                     "XDG_CACHE_HOME": self.root / "cache", "XDG_RUNTIME_DIR": self.root / "runtime", "TMPDIR": self.root / "tmp"}
            self.env = {**os.environ, **{k: str(v) for k, v in roots.items()},
                        "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
            for path in roots.values():
                path.mkdir(mode=0o700)
            libc = ctypes.CDLL(None, use_errno=True)
            if libc.prctl(36, 1, 0, 0, 0) != 0:
                raise OSError(ctypes.get_errno(), "Cannot establish existing actual orphan collection")
            self.candidate_initial = {}
            for name in sorted(OWNED_PATHS):
                path = self.candidate / name
                info = path.lstat()
                if path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 256 * 1024:
                    raise RuntimeError("Inventory receiving source must be bounded physical files")
                self.candidate_initial[name] = {"blob": blob(path), "sha256": digest(path)}
                shutil.copyfile(path, self.evidence / path.name)
            write_json(self.evidence / "candidate.json", self.candidate_initial)
            write_json(self.evidence / "host.json", {"mode": self.mode,
                "limits": {"active_s": 15, "group_rss_bytes": 256 * 1024**2,
                           "owned_bytes": 64 * 1024**2, "logs_and_outputs_bytes": 1024**2, "cpu": 1},
                "qualification": "Proposed bounds; actual inventory/fit remains unmeasured until allocated. No science, engine, project or native query."})
            self.capacity()
            phase = self.phase("vulkan-inventory", [sys.executable, "-I", "-B", str(Path(__file__).resolve()),
                "--mode", "VULKAN_INVENTORY", "--vulkan-inventory-child", "--candidate", str(self.candidate),
                "--source", str(self.source), "--root", str(self.root), "--event-sha", self.event_sha], 15)
            if phase.get("exit") != 0 or phase.get("state") != "COLLECTED":
                raise RuntimeError("Inventory phase incomplete; retain raw logs/actual collection")
            path = self.evidence / "vulkan-inventory-observation.json"
            if path.is_symlink() or not 0 < path.stat().st_size <= 256 * 1024:
                raise RuntimeError("Inventory observation must be bounded physical JSON")
            observation = json.loads(path.read_text())
            if (observation.get("state") != "METADATA_ONLY"
                    or observation.get("extension_query", {}).get("state") != "NOT RUN"
                    or observation["extension_query"].get("returncode") is not None):
                raise RuntimeError("Inventory cannot claim an unexecuted native query")
        except BaseException as error:
            errors.append({"type": type(error).__name__, "message": str(error)})
        finally:
            self.terminal_started = time.monotonic()
            signal.setitimer(signal.ITIMER_REAL, 0)
            try:
                self.arm_budget()
                if self.candidate_initial is not None:
                    after = {name: {"blob": blob(self.candidate / name), "sha256": digest(self.candidate / name)} for name in sorted(OWNED_PATHS)}
                    write_json(self.evidence / "candidate-after.json", after)
                    if after != self.candidate_initial:
                        raise RuntimeError("Inventory receiver inputs changed")
                    self.guards["candidate"] = "PASS"
                self.output["final_capacity"] = self.capacity()
                self.arm_budget()
            except BaseException as error:
                errors.append({"type": type(error).__name__, "message": str(error)})
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
            observation_path = self.evidence / "vulkan-inventory-observation.json"
            self.output.update(state="VULKAN_METADATA_ONLY" if not errors and observation else "INVENTORY_INCOMPLETE_FAILURE",
                errors=errors, observation=({"file": observation_path.name, "state": observation["state"],
                    "bytes": observation_path.stat().st_size, "sha256": digest(observation_path)} if observation else None), budget=self.budget_receipt(),
                gui_workflow_pass=False, production_correction_authorised=False)
            write_json(self.evidence / "result.json", self.output)
            try:
                self.output["final_capacity"] = self.capacity()
            except BaseException as error:
                self.output["state"] = "INVENTORY_INCOMPLETE_FAILURE"
                self.output["errors"].append({"type": type(error).__name__, "message": str(error)})
                write_json(self.evidence / "result.json", self.output)
            if self.budget_remaining() <= 0 or self.collection_used > 30:
                self.output["state"] = "INVENTORY_INCOMPLETE_FAILURE"
                self.output["errors"].append({"type": "TimeoutError", "message": "Inventory aggregate/final receipt budget exhausted"})
                write_json(self.evidence / "result.json", self.output)
        return 0 if self.output["state"] == "VULKAN_METADATA_ONLY" else 1

    def run(self) -> int:
        if self.mode == "VULKAN_INVENTORY":
            return self.inventory_only()
        failure = None
        try:
            self.setup()
            if self.mode == "DISPLAYED_SMOKE":
                self.dependency_deadline = time.monotonic() + 120
                self.prepare_display_tool()
                self.display_capabilities_initial = self.display_capabilities()
            self.install_dependencies()
            self.get_engine()
            self.canary()
            self.require_clean("import", self.phase("import", [str(self.engine), "--headless", "--audio-driver", "Dummy",
                                                             "--path", str(self.game), "--import"], 180))
            self.generated_uids_initial = self.generated_uids()
            write_json(self.evidence / "generated-uids-after-import.json", self.generated_uids_initial)
            self.transaction_started = time.monotonic()
            self.arm_budget()
            write_json(self.evidence / "result.json", {"state": "TRANSACTION_INCOMPLETE_FAILURE",
                       "workflow_sha": self.event_sha, "tested_game_sha": GAME_SHA,
                       "mode": self.mode, "qualification": "Provisional failure until the selected mode, terminal guards and packaging finish within budget."})
            if self.mode == "DISPLAYED_SMOKE":
                self.displayed_smoke()
            else:
                self.require_clean("check-only", self.phase("check-only", [
                    str(self.engine), "--headless", "--audio-driver", "Dummy",
                    "--path", str(self.game), "--check-only", "--script",
                    "res://" + TEST_PATH.removeprefix("game/")], 20))
                self.python_stage("python-canaries", PY_CANARIES)
                self.reconcile(self.phase("focused", [str(self.engine), "--headless", "--audio-driver", "Dummy",
                    "--path", str(self.game), "-s", "res://addons/gdUnit4/bin/GdUnitCmdTool.gd",
                    "--ignoreHeadlessMode", "-a", "res://" + TEST_PATH.removeprefix("game/"),
                    "-a", "res://" + DEPENDENT_TEST_PATH.removeprefix("game/"), "-rd", REPORT_DIR], 90))
                if self.output["state"] != "TEN_GDUNIT_PASS":
                    raise RuntimeError("GdUnit stage did not pass; fault methods remain NOTRUN")
                self.python_stage("python-faults", PY_FAULTS)
                if any(state != "PASS" for state in self.output["methods"].values()):
                    raise RuntimeError("Not all sixteen combined controls passed")
                self.output["state"] = "SIXTEEN_COMBINED_PENDING_TERMINAL_GUARDS"
        except BaseException as error:
            failure = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
            if self.output["state"] not in ("PERSISTENCE_ASSERTION_RED_REQUIRES_LEAD_REVIEW",
                                           "COMBINED_GDUNIT_ASSERTION_FAIL_REQUIRES_LEAD_REVIEW"):
                self.output["state"] = "PREREQUISITE_OR_NON_TARGET_FAILURE"
        finally:
            self.terminal_started = time.monotonic()
            # A durable fail-closed receipt precedes EVERY terminal copy/hash/tar.
            # Disarm only for this fixed-size emergency receipt; its time remains
            # charged to the transaction and is checked before any PASS promotion.
            signal.setitimer(signal.ITIMER_REAL, 0)
            write_json(self.evidence / "result.json", {"state": "TERMINAL_INCOMPLETE_FAILURE",
                       "workflow_sha": self.event_sha, "tested_game_sha": GAME_SHA,
                       "prior_state": self.output["state"], "budget": self.budget_receipt(),
                       "qualification": "No terminal success yet; originals retained by always-upload paths even if archives are cut short."})
            # Independent final retention attempts; one failing guard must not suppress other evidence.
            final_errors = []
            archives = {}
            if self.mode == "DISPLAYED_SMOKE":
                try:
                    # Exact two secret-file retirement is cleanup, even after
                    # expiry; elapsed time still counts and cannot produce PASS.
                    self.retire_display_authority()
                except BaseException as error:
                    final_errors.append("display-authority: " + repr(error))
                try:
                    self.arm_budget()
                    if (getattr(self, "display_capabilities_initial", None) is not None
                            and self.display_capabilities("display-capabilities-after.json") != self.display_capabilities_initial):
                        raise RuntimeError("Host display tools/libraries changed")
                    self.guards["display_host_authority"] = "PASS"
                except BaseException as error:
                    final_errors.append("display-host-authority: " + repr(error))
            if self.candidate_initial is not None:
                try:
                    self.arm_budget()
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
                    self.arm_budget()
                    after = self.snapshot()
                    write_json(self.evidence / "source-after.json", after)
                    if after != self.initial:
                        raise RuntimeError("Tracked game/Python inputs/index changed during validation")
                    self.guards["frozen_game"] = "PASS"
                except BaseException as error:
                    final_errors.append(repr(error))
            if self.initial is not None:
                try:
                    self.arm_budget()
                    uid_rows = self.generated_uids()
                    write_json(self.evidence / "generated-uids-final.json", uid_rows)
                    self.guards["generated_uids"] = {"state": "PASS", "allowed": list(GENERATED_UID_PATHS),
                                                     "observed": uid_rows}
                except BaseException as error:
                    final_errors.append("generated-uids-guard: " + repr(error))
            try:
                self.arm_budget()
                if self.engine.exists():
                    after_engine = {"bytes": self.engine.stat().st_size, "sha256": digest(self.engine)}
                    write_json(self.evidence / "engine-after.json", after_engine)
                    if after_engine != getattr(self, "engine_guard", None) or set(self.engine.parent.iterdir()) != {self.engine}:
                        raise RuntimeError("Engine/marker guard changed")
                    self.guards["engine"] = "PASS"
            except BaseException as error:
                final_errors.append(repr(error))
            try:
                self.arm_budget()
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
                    self.arm_budget()
                    if source.exists():
                        archives[label] = "INCOMPLETE"
                        with tarfile.open(self.evidence / (label + ".tar.gz"), "x:gz") as archive:
                            # Finite, physical regular files only; tarfile copies
                            # in bounded chunks under the same active timer.
                            total = count = 0
                            for base, dirs, files in os.walk(source, followlinks=False):
                                for item in dirs + files:
                                    if (Path(base) / item).is_symlink():
                                        raise RuntimeError("Output archive symlink refused")
                                for name in files:
                                    path = Path(base) / name
                                    info = path.lstat()
                                    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                                        raise RuntimeError("Output archive nonphysical file refused")
                                    count += 1
                                    total += info.st_size
                                    if count > 20000 or total > OWNED_LIMIT:
                                        raise RuntimeError("Terminal archive entry/byte bound")
                                    archive.add(path, arcname=str(Path(label) / path.relative_to(source)), recursive=False)
                        archives[label] = "COMPLETE"
                except BaseException as error:
                    final_errors.append(label + ": " + repr(error))
            try:
                self.arm_budget()
                reports = self.game / REPORT_DIR
                if reports.exists():
                    shutil.copytree(reports, self.evidence / "gdunit-reports")
            except BaseException as error:
                final_errors.append("gdunit-reports: " + repr(error))
            for name in GENERATED_UID_PATHS:
                try:
                    self.arm_budget()
                    uid = self.source / name
                    if uid.exists() or uid.is_symlink():
                        info = uid.lstat()
                        if (uid.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                                or not uid.resolve(strict=True).is_relative_to(self.game) or info.st_size > 64):
                            raise RuntimeError("Cannot safely retain nonphysical/oversized generated UID")
                        shutil.copyfile(uid, self.evidence / uid.name)
                except BaseException as error:
                    final_errors.append("generated-uid " + name + ": " + repr(error))
            try:
                self.arm_budget()
                self.output["final_capacity"] = self.capacity()
            except BaseException as error:
                final_errors.append("capacity: " + repr(error))
            try:
                self.arm_budget()
                manifest, total = {}, 0
                for p in self.evidence.rglob("*"):
                    if p.name in ("result.json", "result.json.partial", "evidence-manifest.json", "evidence-manifest.json.partial"):
                        continue  # Final result is a separately sealed receipt.
                    if p.is_file() and not p.is_symlink():
                        size = p.stat().st_size
                        total += size
                        if len(manifest) >= 20000 or total > OWNED_LIMIT:
                            raise RuntimeError("Terminal evidence manifest entry/byte bound")
                        manifest[str(p.relative_to(self.evidence))] = {"bytes": size, "sha256": digest(p)}
                write_json(self.evidence / "evidence-manifest.json", manifest)
                self.arm_budget()  # Includes time spent writing/hash/closing archives.
            except BaseException as error:
                final_errors.append("terminal-manifest: " + repr(error))
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
            # Only fixed-size failure/clock metadata remains outside interruptible
            # work. Never scan/copy/hash after expiration. Originals are uploaded
            # from the exact private roots; INCOMPLETE archives are not substitutes.
            if self.budget_remaining() <= 0 or self.collection_used > 30:
                self.budget_failure = self.budget_failure or "Terminal aggregate budget exhausted"
            if self.budget_failure:
                final_errors.append(self.budget_failure)
            self.output.update(failure=failure, final_errors=final_errors, finished_at=time.time(),
                               archives=archives, budget=self.budget_receipt(),
                               gui_workflow_pass=False, production_correction_authorised=False)
            # Seal supporting metadata while the durable result is still failure.
            write_json(self.evidence / "terminal-budget.json", self.budget_receipt())
            if final_errors:
                self.output["state"] = "FINAL_GUARD_OR_COLLECTION_FAILURE"
            elif self.output["state"] == "SIXTEEN_COMBINED_PENDING_TERMINAL_GUARDS":
                self.output["state"] = "SIXTEEN_COMBINED_PASS"
            elif self.output["state"] == "DISPLAYED_SMOKE_PENDING_TERMINAL_GUARDS":
                self.output["state"] = "DISPLAYED_SMOKE"
                self.output["displayed_smoke"]["state"] = "PASS"
            # Charge the small final result write too. Overrun replaces even a
            # just-written PASS with failure before any successful return.
            try:
                write_json(self.evidence / "result.json", self.output)
                if self.budget_remaining() <= 0 or self.collection_used > 30:
                    self.budget_failure = self.budget_failure or "Final receipt exceeded aggregate budget"
                    raise TimeoutError(self.budget_failure)
            except BaseException as error:
                self.output["state"] = "FINAL_GUARD_OR_COLLECTION_FAILURE"
                write_json(self.evidence / "result.json", {"state": self.output["state"],
                           "workflow_sha": self.event_sha, "tested_game_sha": GAME_SHA,
                           "budget": self.budget_receipt(), "failure": repr(error),
                           "qualification": "Emergency failure receipt only; original private outputs remain available independently of incomplete archives. Expiry is not proof of runtime release."})
        # Only actual success in the selected mode plus all final guards succeeds.
        # A RED, partial fail-fast, setup or collection failure remains nonzero.
        return 0 if self.output["state"] in ("SIXTEEN_COMBINED_PASS", "DISPLAYED_SMOKE") else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--event-sha", required=True)
    parser.add_argument("--mode", choices=MODES, default="H5_COMBINED")
    parser.add_argument("--display-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--mesa-tool-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--vulkan-inventory-child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.mode == "VULKAN_INVENTORY" and (args.display_child or args.mesa_tool_child):
        parser.error("Inventory mode cannot enter display/Mesa-tool child paths")
    if args.vulkan_inventory_child:
        if args.mode != "VULKAN_INVENTORY" or args.display_child or args.mesa_tool_child:
            parser.error("Inventory child requires exclusive explicit VULKAN_INVENTORY mode")
        return vulkan_inventory(args)
    if args.mesa_tool_child:
        return mesa_tool_stage(args)
    if args.display_child:
        return displayed_lifetime(args)
    def interrupted(signum: int, _frame: object) -> None:
        raise InterruptedError(f"Controller received signal {signum}; retain/collect owned children")
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    controller = Controller(args)
    signal.signal(signal.SIGALRM, controller.budget_expired)
    return controller.run()


if __name__ == "__main__":
    raise SystemExit(main())


