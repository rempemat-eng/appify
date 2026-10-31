#!/usr/bin/env python3
"""One-shot working-yard receiving preparation; NO execution before lead GO.

Exact retained H2 PNGs, unmodified props.entry and render_zone.render. This file
is a task adapter, not a compositor or production adopter. Reviewed402c2cd
WNOWAIT/wait4/group collection mechanism is reused with explicit task limits.
All scientific imports and subject work occur ONLY in separately bounded children.
"""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import resource
import selectors
import shutil
import signal
import stat
import struct
import subprocess
import sys
import tarfile
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import zipfile

SEAL_DEADLINE = None  # Only active during final bounded receipt sealing.
SOURCE_SHA = "5dd3825353078b8b8e231f081714144891d98feb"
SOURCE_TREE = "120c336609b393591a662beddf45a84149e73810"
SOURCE_PARENT = "724662fa4edb4f37673856c6e78fe5f60a7fc9c1"
RECEIVER_PARENT = "3e7e6ff65dc71448d36da0932659f8b8123f043c"
ORIGINAL_RECEIVER = "1d47eec95256fccb41fcd7fa987d788bac254494"
CORRECTION_PATHS = {"scripts/review/grain_scale_receiving.py", "scripts/review/fixtures/grain_scale_yard.json",
                    ".github/workflows/grain-scale-receiving.yml"}
OWNED_PATHS = {"scripts/review/grain_scale_receiving.py", "scripts/review/fixtures/grain_scale_yard.json",
               ".github/workflows/grain-scale-receiving.yml"}
FIXTURE = "scripts/review/fixtures/grain_scale_yard.json"
INPUTS = {'.github/workflows/verify.yml': ('97a2d95b8b5d6c801ad0258cf44cbb6474a07a1e', 2165, '100644'),
 'art/house-palette.json': ('7e97a7463b3641425e667d7b7764f34510489a54', 20444, '100644'),
 'art/scenes/woodland.json': ('4ddc7ed7b91d413f897388969579b4d06a2a7486', 31704, '100644'),
 'game/assets/characters/moss/manifest.json': ('0840eda370a71247ce76a4f90f48bb4c59058704', 280584, '100644'),
 'game/assets/characters/moss/sheets/idle_S.png': ('b82e504e38d223665ba265ca0dbcc54906158e5a',
                                                   5101,
                                                   '100644'),
 'game/kit/pieces/prop/crossroads_grain_scale.json': ('b8fcacffc31a4e1d51cd6bee202b03b31a7f3554',
                                                      4215,
                                                      '100644'),
 'game/kit/pieces/structure/crossroads_smithy.json': ('205e304b0a26e5f2cabff0d77526ec699b4bd668',
                                                      5267,
                                                      '100644'),
 'game/kit/pieces/terrain/lawn.json': ('1c340e8f9387cc59e89de242e0fc500d5adad04e', 1271, '100644'),
 'game/kit/pieces/terrain/path.json': ('d7eec9d1d293ed2974c85589240c66d2b6e35a29', 1691, '100644'),
 'game/kit/pieces/terrain/worn.json': ('c21d2922c772d920630d2941caea37dc2c9b04de', 1752, '100644'),
 'game/kit/schema/piece.schema.json': ('fd61e5d29ca017e3f3796a013c86fc0afe58dc16', 25094, '100644'),
 'game/kit/terrain/decal_bankstone_0.png': ('ddf77156d3d58f20354d84ef9b7ce61f23f1dff0', 275, '100644'),
 'game/kit/terrain/decal_bankstone_1.png': ('5fdb5043422f7b5b5ec2fe8128300bb8f9c16b20', 392, '100644'),
 'game/kit/terrain/decal_bankstone_2.png': ('05fe9555da522a5f6e5343372cb097eaca99f4f1', 430, '100644'),
 'game/kit/terrain/decal_blades_0.png': ('b55bcd0317bac13b62d92c5c7c28869bb5edc75d', 92, '100644'),
 'game/kit/terrain/decal_blades_1.png': ('53241ac03be6f74b8643cc278659e85b9d8d330c', 89, '100644'),
 'game/kit/terrain/decal_blades_2.png': ('9f83cd2b210bcfe5e25fa95fbdfebe9c77511ee8', 95, '100644'),
 'game/kit/terrain/decal_pebble_0.png': ('f7b20ff8808807c6ef7b2716093eb14068453fde', 92, '100644'),
 'game/kit/terrain/decal_pebble_1.png': ('904592fcaab25c7caa641e9ad971e9cc20709cd4', 102, '100644'),
 'game/kit/terrain/decal_pebble_2.png': ('6fca74306d297fe156f61afc17e687ac7e18233d', 125, '100644'),
 'game/kit/terrain/decal_pebble_3.png': ('6079ab32f4085f56c59482bbd00ceda5e1bf40db', 125, '100644'),
 'game/kit/terrain/decal_rushes_0.png': ('6b62a84773f1ccc823f18763399239fe2467c810', 185, '100644'),
 'game/kit/terrain/decal_rushes_1.png': ('e9187e8d3d6d89ff943e196a843f11f8bfbf06d6', 192, '100644'),
 'game/kit/terrain/decal_rushes_2.png': ('f661c9f4d4e12c3fc732a8a1ad30a47739a75fb5', 207, '100644'),
 'game/kit/terrain/decal_tuft_0.png': ('7f63c07c10bcf77cf21d1a576c1e9b1d02c7fedc', 129, '100644'),
 'game/kit/terrain/decal_tuft_1.png': ('37334286da6babb496acf504a78e4cc014f0b200', 133, '100644'),
 'game/kit/terrain/decal_tuft_2.png': ('d74b3e7ee0d5318312c093cb0a5ba46839557277', 124, '100644'),
 'game/kit/terrain/decal_tuft_3.png': ('6443a0d10ac79427a474a08a38dd3cf3ddbaa78f', 127, '100644'),
 'game/kit/terrain/decal_tuft_4.png': ('584951e7acb946afec5c92c8f84f7b4e4a3c9c19', 130, '100644'),
 'game/kit/terrain/decal_tuft_5.png': ('b1cb49799015296addc07f58edee7d736ffd47a3', 135, '100644'),
 'game/kit/terrain/fill_cobble_road.png': ('139ba1e3302393b596b80d0b23aa5458fe13219d', 161706, '100644'),
 'game/kit/terrain/fill_earth_face.png': ('c2b3a544cfd7ec7ace86e80ab6d4acf2ba770a91', 12039, '100644'),
 'game/kit/terrain/fill_lawn.png': ('2da7fe642e60d366fe7b1c7db34928125d93718f', 160150, '100644'),
 'game/kit/terrain/fill_path.png': ('928c65c1f1e3d054aafd0a74133e78e602b2afd1', 121824, '100644'),
 'game/kit/terrain/fill_scree.png': ('10ad783be4b63c56401c6dff622082c8bc57a3d6', 191874, '100644'),
 'game/kit/terrain/fill_water.png': ('bae33576d7b875c455b314b51cad64f51fd8e19f', 21795, '100644'),
 'game/kit/terrain/fill_worn.png': ('928c65c1f1e3d054aafd0a74133e78e602b2afd1', 121824, '100644'),
 'game/kit/terrain/manifest.json': ('eaa4e0381bb1fba2ebf62657f7e42a7d1e6d21da', 10284, '100644'),
 'game/kit/terrain/noise.png': ('2e877679e37e07ebf459f77c6cc73c5bcfb4ef4d', 224556, '100644'),
 'game/kit/terrain/over_earth_face_over_any.png': ('7a0877194c4e24708807e856346b826cc7902bf4',
                                                   26950,
                                                   '100644'),
 'game/kit/terrain/over_lawn_over_earth_face.png': ('a3c30d6847349b6bdb2ba8e5c4eeb642daadf7ec',
                                                    25071,
                                                    '100644'),
 'game/kit/terrain/over_lawn_over_lower_tier.png': ('91385dcab2d4a001e0131d2e383f0833011a8c79',
                                                    24541,
                                                    '100644'),
 'game/kit/terrain/over_lawn_over_path.png': ('f78f169f901a1a7204569fc68f2ad182189777f9', 27186, '100644'),
 'game/kit/terrain/over_lawn_over_scree.png': ('f78f169f901a1a7204569fc68f2ad182189777f9', 27186, '100644'),
 'game/kit/terrain/over_lawn_over_water.png': ('5e5ec3ccd827c8fc258bd583f6105ad533c95630', 37711, '100644'),
 'game/kit/terrain/over_lawn_over_worn.png': ('f78f169f901a1a7204569fc68f2ad182189777f9', 27186, '100644'),
 'game/kit/terrain/over_path_over_earth_face.png': ('a3c30d6847349b6bdb2ba8e5c4eeb642daadf7ec',
                                                    25071,
                                                    '100644'),
 'game/kit/terrain/over_path_over_lower_tier.png': ('91385dcab2d4a001e0131d2e383f0833011a8c79',
                                                    24541,
                                                    '100644'),
 'game/kit/terrain/over_path_over_water.png': ('5e5ec3ccd827c8fc258bd583f6105ad533c95630', 37711, '100644'),
 'game/kit/terrain/over_water_over_earth_face.png': ('a3c30d6847349b6bdb2ba8e5c4eeb642daadf7ec',
                                                     25071,
                                                     '100644'),
 'game/kit/terrain/over_worn_over_path.png': ('9ccba9db0724d211a3a9d4d1b5116462d0928c3a', 14740, '100644'),
 'game/zones/crossroads/art/smithy.png': ('33325f45415f94bb4afcc72a19553c7d1c592951', 26700, '100644'),
 'scripts/art/biomes/woodland.json': ('6da96e5aa39b945288b2a71e826e7e6b535a7559', 8822, '100644'),
 'scripts/art/house_palette.py': ('8a816d1799abd1fc22931a2c93fbe620a14a200e', 17753, '100644'),
 'scripts/art/kit/__init__.py': ('e69de29bb2d1d6434b8b29ae775ad8c2e48c5391', 0, '100644'),
 'scripts/art/kit/build.py': ('054206b5ea00d227ae0a33075a0b0b2e0355d4b5', 18911, '100644'),
 'scripts/art/kit/compose.py': ('4435017b23a5d50ed0a5e8801abc536b84854416', 12458, '100644'),
 'scripts/art/kit/crossroads_grain_scale.py': ('e38b98d06919a04d584117bf63d38f3ae8161861', 8981, '100644'),
 'scripts/art/kit/dressing.py': ('e4b4db15f45a0f1e202012a7c8d506e6f4970c5f', 8356, '100644'),
 'scripts/art/kit/edges.py': ('28fdf16622c7a0bed0f8d427e2ed6938fc7bcd69', 23944, '100644'),
 'scripts/art/kit/fills.py': ('3cbde218f4ea757a7327887060a60dfd65138df4', 18297, '100644'),
 'scripts/art/kit/props.py': ('8fd407ff82f2964c862d5b810c67b5e004bba2a6', 5792, '100644'),
 'scripts/art/kit/relations.py': ('dd6b718b24f9f681cd5450ecbb0216e6a1ae8420', 19542, '100644'),
 'scripts/art/kit/render_zone.py': ('16da219083adad0bcdd869739e5b3e338933beda', 2237, '100644'),
 'scripts/art/kit/schema.py': ('056c1f9a30d49e203badd97624458130c79c81b2', 14148, '100644'),
 'scripts/art/kit/settlement_props.py': ('c51b9b53fb836675d305d02029c0070ae7703a1d', 8869, '100644'),
 'scripts/art/kit/surface.py': ('fb9b1688e8352350845d5669135e83cecfce8bf3', 22240, '100644'),
 'scripts/art/native/__init__.py': ('424a4a68c50941eb2550d4bcbdd8dff8fd5c37b9', 2747, '100644'),
 'scripts/art/native/accents.json': ('d612eb0e6c3eb7eedf8cf878186c26bc1aaa9486', 921, '100644'),
 'scripts/art/native/ctx.py': ('c79cfda10603fcc7092a4b879dc552c01d88f6c1', 1506, '100644'),
 'scripts/art/native/palette.py': ('7685bc30fa29bf2c6fe87cfdc4e2ecae2f908b28', 6189, '100644'),
 'scripts/art/native/softgrid.py': ('365cdd330b3a1628a1e7eca1114648262a506dab', 27518, '100644'),
 'scripts/art/native/softground.py': ('6ad07c557eefa864f1140332e382b2ef8f3101a1', 112143, '100644'),
 'scripts/art/native/terrain/__init__.py': ('955bbcf2a5172718655203a0cc8f6d08671b60ee', 2792, '100644'),
 'scripts/art/native/terrain/decals.py': ('fbbac154045fa4e1205561ad21554838c79874a4', 8622, '100644'),
 'scripts/art/native/terrain/noise.py': ('0d879d5d85126774b9df5b1b11fa81d88037cc10', 1660, '100644'),
 'scripts/art/native/terrain/scene.py': ('406f9f63e988bfb1fe8410dbffd444116d555915', 81041, '100644'),
 'scripts/art/native/terrain/sheets.py': ('1c2072d629a5c7f259b93fd303061826e255999d', 43948, '100644'),
 'scripts/art/native/terrain/tiles.py': ('e0d05e1c0ddc525a4dd952ae557353178d3a5e2f', 45209, '100644'),
 'scripts/art/native/village.py': ('78f5e5c48602242d26a52f2e0ce9dbd37610d999', 178366, '100644'),
 'scripts/art/size_guide.json': ('f30ecb3249d771e5dc6cdf6546d50400b118cf57', 45069, '100644'),
 'scripts/review/__init__.py': ('e69de29bb2d1d6434b8b29ae775ad8c2e48c5391', 0, '100644'),
 'scripts/review/ground_rules.py': ('0bfe3fff9d74f3b1ecd07afe1ff27b0940143f68', 18956, '100644'),
 'scripts/review/kit_scene.py': ('6c71732fb52cbe86e8fa723c4d09a0af4d553371', 28305, '100644'),
 'game/kit/pieces/prop/crossroads_handcart.json': ('d50ff1b2469e67333ecc47b4dd58a794a3a7c21d', 1684, '100644'),
 'game/kit/pieces/prop/crossroads_sacks.json': ('ad8a77b6d5b63e9863cde3d2ba7980fc2d2c30e8', 1625, '100644'),
 'game/zones/crossroads/art/handcart.png': ('c1016d875a02681ecfc24f624b98dc74e3caa35d', 2189, '100644'),
 'game/zones/crossroads/art/sacks_12.png': ('26f9bc05d662407557e6c152cf7fbc8c65b41871', 1122, '100644')}
DEPENDENCIES = {"Pillow":"12.3.0", "numpy":"2.5.3", "scipy":"1.18.1"}
FILENAMES = ("crossroads_grain_scale_ready.png", "crossroads_grain_scale_loaded.png")
H2_ARTIFACT_ID = 13012081883
H2_RUN_ID = 41128868097
H2_RECEIVER_SHA = "3e7e6ff65dc71448d36da0932659f8b8123f043c"
H2_SOURCE_SHA = "5dd3825353078b8b8e231f081714144891d98feb"
H2_ZIP_BYTES = 3776131
H2_ZIP_SHA256 = "609f3772d3a63eda72df6f7e174134530268f6c3fcb11857433779fe96b8ae9b"
H2_PNGS = {
    FILENAMES[0]: (2837, "beea15bd36e20c9a4887dd721bfbf6febd313658aa278f206e5062eb4b0f3d1c"),
    FILENAMES[1]: (3199, "967c74e5bc753357abf3d8cfecc7d6593291632af1ae36659fbde8bae1ba0199"),
}
GOODS = ("game/kit/pieces/prop/crossroads_handcart.json", "game/kit/pieces/prop/crossroads_sacks.json")
GRAIN = "game/kit/pieces/prop/crossroads_grain_scale.json"
SMITHY = "game/kit/pieces/structure/crossroads_smithy.json"
OWNED_LIMIT = 1024 * 1024**2  # full duty, separately includes all source/work/deps/evidence
FREE_RESERVE = 256 * 1024**2
DEPENDENCY_LIMIT = 384 * 1024**2
EVIDENCE_LIMIT = 64 * 1024**2
LOG_LIMIT = 4 * 1024**2
ERROR_PATTERN = re.compile(r"Traceback \(most recent call last\):|^ERROR:|SCRIPT ERROR:|MemoryError|ModuleNotFoundError", re.M)

# Opt-in subject is separate from the frozen H3 source/receiver ancestry above.
ACTIVE_RECEIVER_PARENT = "c302b3380f99091e30ef6e7dc2b18f6118a268f3"
ART_SOURCE_SHA = "d948ac57134ab092e91c8ab9ccc5d62593f064dd"
ART_SOURCE_TREE = "d52322bc21b10ba9d4a6cab4bb1d45f6d79ebf87"
ART_SOURCE_PARENT = "eee6036dd1d96a6c63c6a25a6ca33a0ccf56d77e"
ART_SOURCE_CHANGES = {
    "scripts/art/native/village.py": ("100644", "f4c5b8393beb8332403a0760bbedc635f4b35adb"),
    "docs/codex/crossroads-grain-scale-review.md": ("100644", "578406e211fe54d9961afce5bc63d63f750029e9"),
}
MODE_PATHS = {"scripts/review/grain_scale_receiving.py", ".github/workflows/grain-scale-receiving.yml"}
TWO_GOODS_INPUTS = {'.github/workflows/verify.yml': ('97a2d95b8b5d6c801ad0258cf44cbb6474a07a1e', 2165, '100644'),
 'art/house-palette.json': ('7e97a7463b3641425e667d7b7764f34510489a54', 20444, '100644'),
 'game/zones/crossroads/art/handcart.png': ('c1016d875a02681ecfc24f624b98dc74e3caa35d', 2189, '100644'),
 'game/zones/crossroads/art/sacks_12.png': ('26f9bc05d662407557e6c152cf7fbc8c65b41871', 1122, '100644'),
 'scripts/art/house_palette.py': ('8a816d1799abd1fc22931a2c93fbe620a14a200e', 17753, '100644'),
 'scripts/art/native/__init__.py': ('424a4a68c50941eb2550d4bcbdd8dff8fd5c37b9', 2747, '100644'),
 'scripts/art/native/accents.json': ('d612eb0e6c3eb7eedf8cf878186c26bc1aaa9486', 921, '100644'),
 'scripts/art/native/ctx.py': ('c79cfda10603fcc7092a4b879dc552c01d88f6c1', 1506, '100644'),
 'scripts/art/native/palette.py': ('7685bc30fa29bf2c6fe87cfdc4e2ecae2f908b28', 6189, '100644'),
 'scripts/art/native/village.py': ('f4c5b8393beb8332403a0760bbedc635f4b35adb', 185603, '100644')}
TWO_GOODS_FILES = ("handcart.png", "sacks_12.png")
TWO_GOODS_PRESENTATION = set(TWO_GOODS_FILES) | {"two-goods-before-after-2x.png"}

def digest(path: Path, kind: str = "sha256") -> str:
    h = hashlib.new(kind)
    with path.open("rb") as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b""):
            if SEAL_DEADLINE is not None and time.monotonic() > SEAL_DEADLINE:
                raise RuntimeError("Final sealing deadline during bounded hash chunk")
            h.update(data)
    return h.hexdigest()

def blob(path: Path) -> str:
    h = hashlib.sha1(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b""):
            if SEAL_DEADLINE is not None and time.monotonic() > SEAL_DEADLINE:
                raise RuntimeError("Final sealing deadline during bounded hash chunk")
            h.update(data)
    return h.hexdigest()

def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")

def reuse_h2(root: Path, work: Path, evidence: Path) -> int:
    """Task-specific bounded urllib/ZIP intake, adapted from the existing receiver.

    Only authenticated GitHub metadata/redirect uses the token; the signed blob
    request has no Authorization header. Never print tokens, signed URLs or raw
    network exception strings. Originals/partial bytes stay in this job's duty.
    """
    token = os.environ.pop("GRAIN_ARTIFACT_TOKEN", "")
    if not token:
        raise RuntimeError("Read-Actions token required for exact H2 artifact; no repaint fallback")
    if work != root / "work" or evidence != root / "evidence":
        raise RuntimeError("H2 intake requires the existing private duty paths")
    archive = evidence / "h2-original.zip"
    art = work / "game/kit/props/art"
    if archive.exists() or art.exists():
        raise RuntimeError("Fresh H2 intake destinations required; retain earlier evidence")
    started, received = time.monotonic(), 0
    receipt = {"artifact_id": H2_ARTIFACT_ID, "run_id": H2_RUN_ID,
               "receiver_sha": H2_RECEIVER_SHA, "source_sha": H2_SOURCE_SHA,
               "expected_bytes": H2_ZIP_BYTES, "expected_sha256": H2_ZIP_SHA256}
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    api = f"https://api.github.com/repos/rempemat-eng/appify/actions/artifacts/{H2_ARTIFACT_ID}"
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    try:
        try:
            with opener.open(urllib.request.Request(api, headers=headers), timeout=10) as response:
                raw = response.read(65537)
            if len(raw) > 65536:
                raise RuntimeError("H2 artifact metadata exceeds64KiB")
            (evidence / "h2-artifact-metadata.json").write_bytes(raw)
            meta = json.loads(raw)
            if not isinstance(meta, dict):
                raise RuntimeError("H2 artifact metadata must be an object")
            if (meta.get("id") != H2_ARTIFACT_ID or meta.get("expired") is not False
                    or meta.get("size_in_bytes") != H2_ZIP_BYTES
                    or meta.get("digest") != "sha256:" + H2_ZIP_SHA256
                    or meta.get("name") != f"mygame-grain-scale-{H2_RECEIVER_SHA}-{H2_RUN_ID}-1"
                    or meta.get("workflow_run", {}).get("id") != H2_RUN_ID
                    or meta.get("workflow_run", {}).get("head_sha") != H2_RECEIVER_SHA):
                raise RuntimeError("H2 artifact identity/run/receiver/size/expiry mismatch")
            # Deliberately do not forward the API token through the cross-host redirect.
            try:
                response = opener.open(urllib.request.Request(api + "/zip", headers=headers), timeout=10)
            except urllib.error.HTTPError as error:
                if error.code != 302:
                    raise RuntimeError("H2 archive endpoint did not provide its expected redirect") from None
                location = error.headers.get("Location", "")
                error.close()
                url = urllib.parse.urlsplit(location)
                host = url.hostname or ""
                if (url.scheme != "https" or url.username or url.password or url.fragment
                        or url.port not in (None, 443)
                        or not (host.endswith(".blob.core.windows.net") or host.endswith(".actions.githubusercontent.com"))):
                    raise RuntimeError("H2 archive redirect destination refused")
                response = opener.open(urllib.request.Request(location), timeout=10)
            else:
                response.close()
                raise RuntimeError("Unexpected H2 archive response; no alternate acquisition")
            with response, archive.open("xb") as output:
                for chunk in iter(lambda: response.read(65536), b""):
                    if received + len(chunk) > H2_ZIP_BYTES or time.monotonic() - started > 30:
                        raise RuntimeError("H2 archive exact-byte/30s acquisition bound exceeded")
                    output.write(chunk)
                    received += len(chunk)
            # The enclosing unchanged phase monitor enforces duty/RSS/log/deadline.
        except (urllib.error.URLError, OSError, ValueError) as error:
            raise RuntimeError("H2 artifact acquisition failed: " + type(error).__name__) from None
        if received != H2_ZIP_BYTES or digest(archive) != H2_ZIP_SHA256:
            raise RuntimeError("Original H2 archive bytes/hash differ; no repaint fallback")
        art.mkdir(parents=True, mode=0o700)
        selected = {"work/game/kit/props/art/" + n: n for n in FILENAMES}
        files, expanded = {}, 0
        with zipfile.ZipFile(archive) as packed:
            members = packed.infolist()
            if not 1 <= len(members) <= 128 or len({x.filename for x in members}) != len(members):
                raise RuntimeError("H2 ZIP duplicate/member-count refusal")
            for member in members:
                path = PurePosixPath(member.filename)
                mode = member.external_attr >> 16
                if (not member.filename or "\\" in member.filename or path.is_absolute()
                        or member.orig_filename != member.filename
                        or any(p in ("", ".", "..") for p in member.filename.rstrip("/").split("/"))
                        or str(path) != member.filename.rstrip("/") or member.flag_bits & 1
                        or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)):
                    raise RuntimeError("Unsafe H2 ZIP path/type/encryption")
                if ((stat.S_IFMT(mode) == stat.S_IFDIR and not member.is_dir())
                        or (stat.S_IFMT(mode) == stat.S_IFREG and member.is_dir())):
                    raise RuntimeError("H2 ZIP file/directory type mismatch")
                expanded += member.file_size
                if expanded > 16 * 1024**2 or member.file_size < 0:
                    raise RuntimeError("H2 ZIP expanded-size bound exceeded")
                if member.is_dir():
                    if member.filename in selected or member.file_size:
                        raise RuntimeError("H2 PNG member is not a physical file")
                    continue
                name = selected.get(member.filename)
                if name and member.file_size != H2_PNGS[name][0]:
                    raise RuntimeError("H2 PNG member declared size differs")
                h, count, data = hashlib.sha256(), 0, bytearray()
                with packed.open(member) as source:
                    for chunk in iter(lambda: source.read(65536), b""):
                        count += len(chunk)
                        if count > member.file_size or time.monotonic() - started > 30:
                            raise RuntimeError("H2 ZIP byte/deadline bound exceeded")
                        h.update(chunk)
                        if name: data.extend(chunk)
                if count != member.file_size:
                    raise RuntimeError("H2 ZIP truncated member")
                if name:
                    if (count, h.hexdigest()) != H2_PNGS[name]:
                        raise RuntimeError("H2 original PNG hash differs")
                    if (data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR"
                            or struct.unpack(">II", data[16:24]) != (168, 144)):
                        raise RuntimeError("H2 PNG header differs")
                    with (art / name).open("xb") as dest: dest.write(data)
                    files[name] = {"bytes": count, "sha256": h.hexdigest(),
                                   "size_px": [168,144], "foot_art": [84,132]}
        if set(files) != set(FILENAMES) or set(art.iterdir()) != {art / n for n in FILENAMES}:
            raise RuntimeError("Both exact H2 PNG members required, no substitution")
        write_json(evidence / "reuse-result.json", {"state":"PASS", "draw_invocations":0,
            "files":files, "provenance":receipt, "all_zip_members_crc_read":len(members),
            "qualification":"Exact old H2 bytes reused; no new draw/reproduction/detail approval"})
        return 0
    finally:
        primary_error = sys.exc_info()[0]
        try:
            receipt.update(received_bytes=received, elapsed_s=time.monotonic()-started,
                           retained_bytes=archive.stat().st_size if archive.exists() else 0,
                           retained_sha256=digest(archive) if archive.exists() else None)
            write_json(evidence / "h2-acquisition.json", receipt)
        except BaseException as error:
            if primary_error is None: raise
            print("H2 acquisition receipt incomplete: " + type(error).__name__, file=sys.stderr)

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
                            timeout=(min(30, max(0.01, SEAL_DEADLINE - time.monotonic()))
                                     if SEAL_DEADLINE is not None else 30), env=env, check=False)
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
    def __init__(self, args):
        self.source = args.source.resolve(strict=True)
        self.candidate = args.candidate.resolve(strict=True)
        self.root = args.root.resolve(strict=True)
        self.work = self.root / "work"
        self.evidence = self.root / "evidence"
        self.event_sha = args.event_sha
        self.receiving_mode = args.receiving_mode
        self.two_goods = self.receiving_mode == "TWO_GOODS"
        self.inputs = TWO_GOODS_INPUTS if self.two_goods else INPUTS
        self.subject_sha = ART_SOURCE_SHA if self.two_goods else SOURCE_SHA
        self.subject_tree = ART_SOURCE_TREE if self.two_goods else SOURCE_TREE
        self.goods_before = None
        self.artifact_token = os.environ.pop("GRAIN_ARTIFACT_TOKEN", "")
        self.phases = {n: {"state": "NOTRUN"} for n in (("dependencies", "versions", "two_goods") if self.two_goods else ("dependencies", "versions", "reuse", "composition"))}
        self.output = {"state": "SETUP_FAILED", "workflow_sha": self.event_sha,
                       "source_sha": self.subject_sha, "source_tree": self.subject_tree, "receiving_mode": self.receiving_mode, "phases": self.phases,
                       "qualification": "Synthetic CANDIDATE only; no terrain/layout/library/art/Matt acceptance."}
        self.before = None
        self.candidate_before = None
        self.deps_before = None
        self.fixture_before = None
        self.reuse_before = None
        self.owned_roots = (self.root, self.source, self.candidate)

    def capacity(self):
        used = 0
        # Only private mutable staging/output entries may disappear during writes.
        def onerror(error):
            if isinstance(error, FileNotFoundError) and error.filename and Path(error.filename).is_relative_to(self.root):
                return
            raise error
        for root in self.owned_roots:
            for base, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
                for name in dirs + files:
                    p = Path(base) / name
                    try:
                        st = p.lstat()
                    except FileNotFoundError as error:
                        onerror(error)
                        continue
                    if stat.S_ISLNK(st.st_mode):
                        raise RuntimeError(f"Unsupported symlink in duty: {p}")
                    used += st.st_blocks * 512
        free = min(shutil.disk_usage(p).free for p in self.owned_roots)
        limits = [(self.root / "dependencies", DEPENDENCY_LIMIT), (self.evidence, EVIDENCE_LIMIT),
                  (self.work / "game/kit/props/art", 8 * 1024**2),
                  (self.root / "presentation", (8 if self.two_goods else 16) * 1024**2)]
        for folder, limit in limits:
            if folder.exists():
                actual = 0
                for p in folder.rglob("*"):
                    try:
                        if p.is_file(): actual += p.stat().st_size
                    except FileNotFoundError as error:
                        onerror(error)
                if actual > limit:
                    raise RuntimeError(f"Duty sub-budget exceeded: {folder.name}: {actual}>{limit}")
        value = {"owned_allocated_bytes": used, "free_bytes": free}
        if used > OWNED_LIMIT or free < FREE_RESERVE:
            raise RuntimeError(f"Duty/reserve exhausted: {value}")
        return value

    def inputs_snapshot(self, root):
        rows = {}
        for name, (sha, size, mode) in self.inputs.items():
            p = root / name
            st = p.lstat()
            if (not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_size != size
                    or blob(p) != sha or bool(st.st_mode & 0o111) != (mode == "100755")):
                raise RuntimeError(f"Pinned physical input differs: {name}")
            rows[name] = {"blob": sha, "bytes": size, "mode": mode, "sha256": digest(p)}
        return rows

    def candidate_snapshot(self):
        rows = {}
        expected = tree(self.candidate)
        for name in sorted(OWNED_PATHS):
            p = self.candidate / name
            st = p.lstat()
            if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or expected.get(name) != ("100644", blob(p)):
                raise RuntimeError("Receiving source differs from immutable event")
            rows[name] = {"blob": blob(p), "sha256": digest(p), "bytes": st.st_size}
        return rows

    def setup(self):
        if (os.environ.get("GITHUB_REPOSITORY") != "rempemat-eng/appify"
                or os.environ.get("GITHUB_REF") != "refs/heads/codex/grain-scale-receiving-run"
                or os.environ.get("GITHUB_RUN_ATTEMPT") != "1"):
            raise RuntimeError("Requires separately lead-allocated exact pushref/attempt1")
        if sys.platform != "linux" or platform.machine() not in ("x86_64", "AMD64") or sys.version_info[:2] != (3, 12):
            raise RuntimeError("Pinned Linux x86_64 CPython3.12 required")
        if not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal"):
            raise RuntimeError("Identity-safe adopted-child collection unavailable")
        if self.event_sha != os.environ.get("GITHUB_SHA") or not re.fullmatch(r"[0-9a-f]{40}", self.event_sha):
            raise RuntimeError("Event pin differs")
        ws = Path(os.environ["GITHUB_WORKSPACE"]).resolve(strict=True)
        if self.source != ws / "source" or self.candidate != ws / "runner":
            raise RuntimeError("Requires two fresh task-specific checkouts")
        if self.root != Path(os.environ["RUNNER_TEMP"]).resolve(strict=True) / "grain-scale":
            raise RuntimeError("Wrong private duty root")
        if set(self.root.iterdir()) != {self.evidence} or set(self.evidence.iterdir()) != {
                self.evidence / "bootstrap.json", self.evidence / "controller.log"}:
            raise RuntimeError("Evidence/duty root nonempty; do not overwrite")
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
        if git(self.source, "rev-parse", "HEAD").decode().strip() != self.subject_sha:
            raise RuntimeError("403 source head differs")
        if git(self.source, "rev-parse", "HEAD^{tree}").decode().strip() != self.subject_tree:
            raise RuntimeError("403 source tree differs")
        if git(self.candidate, "rev-parse", "HEAD").decode().strip() != self.event_sha:
            raise RuntimeError("Candidate head differs")
        headers = git(self.candidate, "cat-file", "commit", "HEAD").decode().split("\n\n", 1)[0]
        if [x[7:] for x in headers.splitlines() if x.startswith("parent ")] != [ACTIVE_RECEIVER_PARENT]:
            raise RuntimeError("Mode extension must retain the exact sole c302 receiver parent")
        active_headers = git(self.candidate, "cat-file", "commit", ACTIVE_RECEIVER_PARENT).decode().split("\n\n", 1)[0]
        if [x[7:] for x in active_headers.splitlines() if x.startswith("parent ")] != [RECEIVER_PARENT]:
            raise RuntimeError("Frozen H3 receiver must retain genuine3e7 parent")
        parent_headers = git(self.candidate, "cat-file", "commit", RECEIVER_PARENT).decode().split("\n\n", 1)[0]
        if [x[7:] for x in parent_headers.splitlines() if x.startswith("parent ")] != [ORIGINAL_RECEIVER]:
            raise RuntimeError("H2 receiver must retain genuine1d47 parent")
        original_headers = git(self.candidate, "cat-file", "commit", ORIGINAL_RECEIVER).decode().split("\n\n", 1)[0]
        if [x[7:] for x in original_headers.splitlines() if x.startswith("parent ")] != [SOURCE_SHA]:
            raise RuntimeError("Original receiver must retain genuine403 parent")
        source_headers = git(self.source, "cat-file", "commit", SOURCE_SHA).decode().split("\n\n", 1)[0]
        if [x[7:] for x in source_headers.splitlines() if x.startswith("parent ")] != [SOURCE_PARENT]:
            raise RuntimeError("Frozen403 must retain genuine377 parent")
        src, runner = tree(self.source, SOURCE_SHA), tree(self.candidate)
        if git(self.source, "rev-parse", SOURCE_SHA + "^{tree}").decode().strip() != SOURCE_TREE:
            raise RuntimeError("Original5dd source baseline differs")
        if self.two_goods:
            art_headers = git(self.source, "cat-file", "commit", ART_SOURCE_SHA).decode().split("\n\n", 1)[0]
            art_parent_headers = git(self.source, "cat-file", "commit", ART_SOURCE_PARENT).decode().split("\n\n", 1)[0]
            if ([x[7:] for x in art_headers.splitlines() if x.startswith("parent ")] != [ART_SOURCE_PARENT]
                    or [x[7:] for x in art_parent_headers.splitlines() if x.startswith("parent ")] != [SOURCE_SHA]):
                raise RuntimeError("Separate subject d948->eee->5dd ancestry differs")
            art_tree = tree(self.source)
            changed = {p for p in src.keys() | art_tree.keys() if src.get(p) != art_tree.get(p)}
            if changed != set(ART_SOURCE_CHANGES) or any(art_tree[p] != v for p,v in ART_SOURCE_CHANGES.items()):
                raise RuntimeError("Only reviewed native source and review MD may differ from5dd")
            self.output["art_subject_history"] = {"headers":art_headers,"parent_headers":art_parent_headers,
                "baseline_sha":SOURCE_SHA,"changed":sorted(changed),"not_receiver_ancestor":True}
        active_tree = tree(self.candidate, ACTIVE_RECEIVER_PARENT)
        mode_delta = {p for p in active_tree.keys() | runner.keys() if active_tree.get(p) != runner.get(p)}
        if mode_delta != MODE_PATHS:
            raise RuntimeError("Only two existing mode-extension receiver files may change")
        previous = tree(self.candidate, RECEIVER_PARENT)
        correction_delta = {p for p in previous.keys() | runner.keys() if previous.get(p) != runner.get(p)}
        if correction_delta != CORRECTION_PATHS:
            raise RuntimeError("Only the three existing working-yard receiving paths may change")
        delta = {p for p in src.keys() | runner.keys() if src.get(p) != runner.get(p)}
        if delta != OWNED_PATHS or any(p in src for p in OWNED_PATHS):
            raise RuntimeError("Exactly three NEW receiving files only")
        for root in (self.source, self.candidate):
            gd = Path(git(root, "rev-parse", "--absolute-git-dir").decode().strip())
            if (gd / "objects/info/alternates").exists():
                raise RuntimeError("Source/candidate borrows objects")
        self.index = Path(git(self.source, "rev-parse", "--absolute-git-dir").decode().strip()) / "index"
        self.before = {"inputs": self.inputs_snapshot(self.source), "index_sha256": digest(self.index)}
        self.candidate_before = self.candidate_snapshot()
        write_json(self.evidence / "source-before.json", self.before)
        write_json(self.evidence / "candidate.json", {"head": self.event_sha,
            "tree": git(self.candidate, "rev-parse", "HEAD^{tree}").decode().strip(),
            "headers": headers, "active_headers": active_headers, "mode_delta":sorted(mode_delta), "parent_headers": parent_headers, "original_headers": original_headers,
            "receiver_parent": RECEIVER_PARENT,
            "correction_delta": sorted(correction_delta), "source_headers": source_headers, "delta": sorted(delta),
            "receiving": self.candidate_before})
        for name in OWNED_PATHS:
            shutil.copyfile(self.candidate / name, self.evidence / Path(name).name)
        self.work.mkdir(mode=0o700)
        deadline = time.monotonic() + 30
        with tarfile.open(self.evidence / "immutable-inputs.tar.gz", "x:gz") as archive:
            for name in self.inputs:
                if time.monotonic() > deadline:
                    raise RuntimeError("Physical source staging30s exhausted; partial archive retained")
                p = self.work / name
                p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(self.source / name, p)
                p.chmod(0o755 if INPUTS[name][2] == "100755" else 0o644)
                archive.add(p, arcname=name, recursive=False)
                self.capacity()
        if self.inputs_snapshot(self.work) != self.before["inputs"]:
            raise RuntimeError("Physical work copies differ")
        if not self.two_goods:
            # Copy fixture only into the isolated work tree, outside registered zones.
            f = self.work / FIXTURE
            f.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.candidate / FIXTURE, f)
            if blob(f) != self.candidate_before[FIXTURE]["blob"]:
                raise RuntimeError("Private fixture copy differs from immutable receiving source")
            self.fixture_before = digest(f)
        (self.root / "presentation").mkdir(mode=0o700)
        roots = {k: self.root / k for k in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "TMPDIR")}
        for p in roots.values(): p.mkdir(mode=0o700)
        self.env = {**os.environ, **{k: str(v) for k,v in roots.items()},
                    "PYTHONDONTWRITEBYTECODE":"1", "PYTHONNOUSERSITE":"1",
                    "PYTHONPATH":os.pathsep.join((str(self.root / "dependencies"), str(self.work))),
                    "OPENBLAS_NUM_THREADS":"1", "OMP_NUM_THREADS":"1", "MKL_NUM_THREADS":"1",
                    "GRAIN_RECEIVING_CHILD":self.event_sha, "GRAIN_DUTY_ROOT":str(self.root)}
        self.env["GRAIN_RECEIVING_MODE"] = self.receiving_mode
        if not self.two_goods:
            self.env["GRAIN_FIXTURE_BLOB"] = self.candidate_before[FIXTURE]["blob"]
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "No actual orphan collection")
        write_json(self.evidence / "plan.json", {"fit":"UNMEASURED; no automatic increase", "one_cpu":True,
            "receiving_mode":self.receiving_mode,"source_files":len(self.inputs), "source_bytes":sum(v[1] for v in self.inputs.values()),
            "limits":{"duty_bytes":OWNED_LIMIT,"dependency_stage_bytes":DEPENDENCY_LIMIT,
                "evidence_bytes":EVIDENCE_LIMIT,"reserve_bytes":FREE_RESERVE,
                "reuse_s":30,"reuse_sampled_group_rss":256*1024**2,"reused_png_output":8*1024**2,
                "composition_s":120,"composition_sampled_group_rss":512*1024**2,
                "two_goods_s":30,"two_goods_sampled_group_rss":256*1024**2,
                "presentation_output":(8 if self.two_goods else 16)*1024**2,"phase_log":LOG_LIMIT,
                "collection_per_phase_s":12,"per_process_AS":2*1024**3,"job_outer_minutes":15},
            "import_initialisers":("TWO_GOODS imports only native village/ctx/palette/house_palette; no town/terrain initialisers." if self.two_goods else "Unmodified build/terrain imports paint native face/snow/grass/path sheets in memory. Included in future composition120s/512MiB; exact future GO must explicitly accept this dependency work. No code executed during source preparation."),
            "terrain_inputs":("NONE: only two frozen old PNGs for inspection." if self.two_goods else "Complete unmodified manifest and all39 PNG read paths; not a selected-fill approximation."),
            "rss_qualification":"Sampled /proc aggregate group RSS,50ms select loop; actual maximum monitor gap recorded. Any observed excess fails.",
            "acceptance":"Synthetic receiving diagnostic only; no Crossroads layout/physics/art/EW detail/Matt approval."})
        self.capacity()

    def require_phase(self, name, result):
        text = diagnostic_text(self.evidence / (name + ".log"))
        if (result.get("exit") != 0 or result.get("state") != "COLLECTED"
                or ERROR_PATTERN.search(text) or orphan_diagnostics(text)):
            raise RuntimeError(f"{name} prerequisite/collection failed; retain actual first error")

    def dependency_snapshot(self):
        rows = {}
        base = self.root / "dependencies"
        for p in sorted(base.rglob("*")):
            if p.is_symlink(): raise RuntimeError("Unsupported dependency symlink")
            if p.is_file():
                if p.stat().st_nlink != 1: raise RuntimeError("Shared dependency file")
                rows[str(p.relative_to(base))] = {"bytes":p.stat().st_size,"sha256":digest(p)}
        if not rows: raise RuntimeError("Empty private dependency stage")
        return rows

    def install_dependencies(self):
        target = self.root / "dependencies"
        target.mkdir(mode=0o700)
        text = (self.source / ".github/workflows/verify.yml").read_text()
        if any(f"{n}=={v}" not in text for n,v in DEPENDENCIES.items()):
            raise RuntimeError("Pinned main-compatible scientific convention differs")
        command = [sys.executable,"-I","-B","-m","pip","install","--disable-pip-version-check",
            "--no-input","--no-cache-dir","--no-compile","--only-binary=:all:","--no-deps",
            "--target",str(target),*[n+"=="+v for n,v in DEPENDENCIES.items()]]
        self.require_phase("dependencies",self.phase("dependencies",command,120,512*1024**2))
        command = [sys.executable,"-B",str(self.candidate / "scripts/review/grain_scale_receiving.py"),
                   "--mode","versions","--root",str(self.root)]
        self.require_phase("versions",self.phase("versions",command,20,256*1024**2))
        versions = json.loads((self.evidence / "scientific-versions.json").read_text())
        for n,v in DEPENDENCIES.items():
            row = versions["packages"][n]
            if row["version"] != v or not Path(row["file"]).resolve(strict=True).is_relative_to(target):
                raise RuntimeError("Scientific version/location substituted")
        self.deps_before = self.dependency_snapshot()
        write_json(self.evidence / "dependencies-before.json",self.deps_before)

    def run(self):
        global SEAL_DEADLINE
        failure = None
        final_errors = []
        try:
            self.setup()
            self.install_dependencies()
            controller = self.candidate / "scripts/review/grain_scale_receiving.py"
            for name, seconds, rss in ((("two_goods",30,256*1024**2),) if self.two_goods else (("reuse",30,256*1024**2),("composition",120,512*1024**2))):
                command = [sys.executable,"-B",str(controller),"--mode",name,"--root",str(self.root)]
                if name == "reuse": self.env["GRAIN_ARTIFACT_TOKEN"] = self.artifact_token
                try:
                    self.require_phase(name,self.phase(name,command,seconds,rss))
                finally:
                    self.env.pop("GRAIN_ARTIFACT_TOKEN", None)
                    self.artifact_token = ""
                result = json.loads((self.evidence / (name+"-result.json")).read_text())
                if result.get("state") != "PASS":
                    raise RuntimeError(f"{name} output/canary incomplete")
                if name == "reuse": self.reuse_before = result
                if name == "two_goods": self.goods_before = result
            self.output["state"] = "DIAGNOSTIC_EXECUTION_COMPLETE_PENDING_FINAL_GUARDS"
        except BaseException as error:
            failure = {"type":type(error).__name__,"message":str(error),"traceback":traceback.format_exc()}
            self.output["state"] = "PREREQUISITE_OR_RECEIVING_FAILURE"
        finally:
            # Durable non-green state BEFORE guards/packaging. Artifacts remain
            # available as original task-owned roots even if packaging times out.
            self.output.update(failure=failure,final_errors=final_errors,finished_at=time.time())
            write_json(self.evidence / "result.json",self.output)
            seal_started = time.monotonic()
            seal_deadline = seal_started + 30
            SEAL_DEADLINE = seal_deadline
            def seal_check():
                if time.monotonic() > seal_deadline:
                    raise RuntimeError("Final guard/receipt sealing30s exhausted; originals retained")
            for label, action in (
                ("candidate", lambda: self.candidate_snapshot() == self.candidate_before),
                ("source", lambda: {"inputs":self.inputs_snapshot(self.source),"index_sha256":digest(self.index)} == self.before),
                ("work-inputs", lambda: self.inputs_snapshot(self.work) == self.before["inputs"]),
                ("work-fixture", lambda: digest(self.work / FIXTURE) == self.fixture_before),
                ("h2-reuse", lambda: digest(self.evidence / "h2-original.zip") == H2_ZIP_SHA256
                    and (self.evidence / "h2-original.zip").stat().st_size == H2_ZIP_BYTES
                    and set((self.work / "game/kit/props/art").iterdir()) == {
                        self.work / "game/kit/props/art" / n for n in FILENAMES}
                    and all(stat.S_ISREG((self.work / "game/kit/props/art" / n).lstat().st_mode)
                        and (self.work / "game/kit/props/art" / n).lstat().st_nlink == 1
                        and (self.work / "game/kit/props/art" / n).stat().st_size == H2_PNGS[n][0]
                        and digest(self.work / "game/kit/props/art" / n) == H2_PNGS[n][1]
                        for n in FILENAMES)),
                ("dependencies", lambda: self.dependency_snapshot() == self.deps_before),
                *(((("two-goods", lambda: self.goods_snapshot() == self.goods_before["presentation"]),)
                    if self.two_goods else ()))):
                try:
                    seal_check()
                    if (label == "candidate" and self.candidate_before is None) or (label in ("source","work-inputs") and self.before is None) or (label == "dependencies" and self.deps_before is None):
                        self.output[label+"_guard"] = "NOTRUN; setup not complete"
                        continue
                    if label == "work-fixture" and self.fixture_before is None:
                        self.output[label+"_guard"] = "NOTRUN; setup not complete"
                        continue
                    if label == "two-goods" and self.goods_before is None:
                        self.output[label+"_guard"] = "NOTRUN; draw not complete"
                        continue
                    if label == "h2-reuse" and self.reuse_before is None:
                        self.output[label+"_guard"] = "NOTRUN; reuse not complete"
                        continue
                    if not action(): raise RuntimeError(label+" bytes/index changed")
                    seal_check()
                    self.output[label+"_guard"] = "PASS"
                except BaseException as error:
                    final_errors.append(label+": "+repr(error))
            try:
                seal_check();self.output["final_capacity"] = self.capacity();seal_check()
            except BaseException as error:
                final_errors.append("capacity: "+repr(error))
            try:
                manifest = {}
                for folder in (self.evidence,self.root / "presentation",self.work / "game/kit/props/art"):
                    if folder.exists():
                        for p in sorted(folder.rglob("*")):
                            seal_check()
                            if p.is_file() and not p.is_symlink() and p.name not in ("evidence-manifest.json","result.json","controller.log","controller.exit","workflow-disposition.json"):
                                manifest[str(p.relative_to(self.root))] = {"bytes":p.stat().st_size,"sha256":digest(p)}
                write_json(self.evidence / "evidence-manifest.json",{"files":manifest,
                    "terminal_exclusions":["result.json","controller.log","controller.exit","workflow-disposition.json"],
                    "qualification":"These terminal mutable receipts are retained directly and covered by provider artifact digest; not stale pre-final hashes."})
                seal_check()
            except BaseException as error:
                final_errors.append("manifest incomplete: "+repr(error))
            if time.monotonic() > seal_deadline:
                final_errors.append("Terminal sealing30s budget exceeded; receipt is non-green")
            SEAL_DEADLINE = None  # mandatory small failure/terminal receipt can still be written
            if failure or final_errors:
                self.output["state"] = "RECEIVING_FAILED_OR_FINAL_GUARD_INCOMPLETE"
            elif self.output["state"] == "DIAGNOSTIC_EXECUTION_COMPLETE_PENDING_FINAL_GUARDS":
                self.output["state"] = "TWO_GOODS_ARTIFACTS_COMPLETE_NOT_ART_APPROVAL" if self.two_goods else "SYNTHETIC_WORKING_YARD_COMPLETE_NOT_ART_APPROVAL"
            self.output.update(final_errors=final_errors,seal_elapsed_s=time.monotonic()-seal_started,
                               finished_at=time.time(),art_approved=False,layout_approved=False)
            write_json(self.evidence / "result.json",self.output)
        return 0 if self.output["state"] in ("TWO_GOODS_ARTIFACTS_COMPLETE_NOT_ART_APPROVAL", "SYNTHETIC_WORKING_YARD_COMPLETE_NOT_ART_APPROVAL") else 1

    def goods_snapshot(self):
        out = self.root / "presentation"
        if set(p.name for p in out.iterdir()) != TWO_GOODS_PRESENTATION:
            raise RuntimeError("Exactly two subjects and one labelled inspection strip required")
        rows = {}
        for p in sorted(out.iterdir()):
            st = p.lstat()
            if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
                raise RuntimeError("Nonphysical two-goods presentation")
            rows[p.name] = {"bytes":st.st_size,"sha256":digest(p)}
        if sum(v["bytes"] for v in rows.values()) > 8*1024**2:
            raise RuntimeError("Two-goods8MiB output bound exceeded")
        return rows

    def phase(self, name: str, command: list[str], seconds: int, rss_limit: int) -> dict:
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
                resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
                resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024**2, 64 * 1024**2))
            process = subprocess.Popen(command, cwd=self.work, env=self.env, start_new_session=True,
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
                    if rss > rss_limit:
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


def draw_two_goods(root: Path, work: Path, evidence: Path) -> int:
    """One native API pass over the two reviewed forms; no town/terrain/compositor."""
    out = root / "presentation"
    if set(out.iterdir()) or "scripts.art.native.village" in sys.modules:
        raise RuntimeError("Fresh output directory and unimported density context required")
    from scripts.art.native import ctx
    ctx.configure(3.0)
    from scripts.art.native import village as V
    from PIL import Image, ImageDraw, ImageFont
    for module_name in ("scripts.art.native", "scripts.art.native.ctx", "scripts.art.native.village",
                        "scripts.art.native.palette", "house_palette"):
        module = sys.modules[module_name]
        if not Path(module.__file__).resolve(strict=True).is_relative_to(work):
            raise RuntimeError("Native module substituted: " + module_name)
    deps = root / "dependencies"
    versions = {}
    for name, module_name in (("Pillow", "PIL"), ("numpy", "numpy"), ("scipy", "scipy")):
        module = sys.modules[module_name]
        versions[name] = {"version":module.__version__, "file":module.__file__}
        if module.__version__ != DEPENDENCIES[name] or not Path(module.__file__).resolve(strict=True).is_relative_to(deps):
            raise RuntimeError("Actual drawing dependency/version substituted")
    subjects = {}
    images = []
    for name, kind, w, h, seed, size, foot in (
            ("handcart.png", "cart", 22, 8, 157, (114,84), (57,80)),
            ("sacks_12.png", "sacks", 14, 8, 112, (60,66), (30,62))):
        pic = V.prop(kind,w,h,seed=seed,hd=True)
        if (pic.W,pic.H) != size or (pic.ax,pic.ay) != foot:
            raise RuntimeError("Native canvas/foot contract differs: " + name)
        image = pic.rgba()
        if image.mode != "RGBA" or image.size != size:
            raise RuntimeError("Native RGBA contract differs")
        image.save(out / name, optimize=True)
        with Image.open(out / name) as check:
            check.verify()
        with Image.open(out / name) as check:
            check.load()
            if check.mode != "RGBA" or check.size != size or check.tobytes() != image.tobytes():
                raise RuntimeError("Saved PNG differs from native drawing")
        alpha = image.getchannel("A")
        bounds = alpha.getbbox()
        if not bounds:
            raise RuntimeError("Empty native subject")
        colours = image.getcolors(maxcolors=size[0]*size[1])
        subjects[name] = {"kind":kind,"seed":seed,"canvas":list(size),"foot":list(foot),
            "mode":"RGBA","alpha_bbox":list(bounds),"alpha_pixels":sum(alpha.histogram()[1:]),
            "nontransparent_colours":len({rgba for _count,rgba in colours if rgba[3]}),
            "bytes":(out/name).stat().st_size,"sha256":digest(out/name)}
        images.append(image)
    # One inspection artifact only: four unmodified old/new subjects at integer2x.
    strip = Image.new("RGBA",(800,256),(24,25,30,255))
    draw = ImageDraw.Draw(strip)
    font = ImageFont.load_default(size=10)
    captions = ["CANDIDATE / native pixels at integer2x / source " + ART_SOURCE_SHA,
                "Python " + platform.python_version() + " / Pillow " + versions["Pillow"]["version"]
                + " / NumPy " + versions["numpy"]["version"] + " / SciPy " + versions["scipy"]["version"],
                "OLD / NEW only. No EW detail score, Y12, production or Matt approval."]
    for caption,y in zip(captions,(2,16,240)):
        box = draw.textbbox((0,0),caption,font=font)
        if box[2]-box[0] > 784:
            raise RuntimeError("Candidate caption exceeds inspection width")
        draw.text((8,y),caption,font=font,fill=(235,233,226,255))
    for i,(name,x) in enumerate(zip(TWO_GOODS_FILES,(8,500))):
        with Image.open(work / "game/zones/crossroads/art" / name) as old:
            old.load()
            if old.size != images[i].size:
                raise RuntimeError("Frozen old native dimensions differ")
            old = old.convert("RGBA")
            strip.alpha_composite(old.resize((old.width*2,old.height*2),Image.Resampling.NEAREST),(x,60))
        nx = x + (252 if i == 0 else 140)
        image = images[i]
        strip.alpha_composite(image.resize((image.width*2,image.height*2),Image.Resampling.NEAREST),(nx,60))
        draw.text((x,38),"OLD "+name,font=font,fill=(235,233,226,255))
        draw.text((nx,38),"NEW "+name,font=font,fill=(235,233,226,255))
    strip.save(out / "two-goods-before-after-2x.png")
    presentation = {p.name:{"bytes":p.stat().st_size,"sha256":digest(p)} for p in out.iterdir()}
    if set(presentation) != TWO_GOODS_PRESENTATION or sum(v["bytes"] for v in presentation.values()) > 8*1024**2:
        raise RuntimeError("Two subject PNGs plus one inspection strip/8MiB required")
    write_json(evidence / "two_goods-result.json",{"state":"PASS","source_sha":ART_SOURCE_SHA,
        "source_tree":ART_SOURCE_TREE,"draw_invocations":1,"native_prop_calls":2,
        "grain_draw_invocations":0,"composition_invocations":0,"subjects":subjects,
        "presentation":presentation,"actual_scientific_versions":versions,"python":sys.version,
        "qualification":"Two candidate native artifacts only. VIEW still required; colour/alpha counts are not detail scores. Same-kind/native-period/adult EW comparison/Y12/Matt approval remain open."})
    return 0


def child(mode, root):
    root = root.resolve(strict=True)
    if (str(root) != os.environ.get("GRAIN_DUTY_ROOT")
            or os.environ.get("GITHUB_REF") != "refs/heads/codex/grain-scale-receiving-run"
            or os.environ.get("GITHUB_RUN_ATTEMPT") != "1"
            or os.environ.get("GRAIN_RECEIVING_CHILD") != os.environ.get("GITHUB_SHA")):
        raise RuntimeError("Child requires exact owned outer preflight/ref/attempt")
    work = root / "work"
    evidence = root / "evidence"
    receiving_mode = os.environ.get("GRAIN_RECEIVING_MODE", "WORKING_YARD")
    if receiving_mode not in ("WORKING_YARD", "TWO_GOODS"):
        raise RuntimeError("Unknown receiving mode")
    two_goods = receiving_mode == "TWO_GOODS"
    if not two_goods and blob(work / FIXTURE) != os.environ.get("GRAIN_FIXTURE_BLOB"):
        raise RuntimeError("Child fixture bytes differ BEFORE any receiving use")
    for name, (sha, size, _mode) in (TWO_GOODS_INPUTS if two_goods else INPUTS).items():
        p = work / name
        if not p.is_file() or p.is_symlink() or p.stat().st_nlink != 1 or p.stat().st_size != size or blob(p) != sha:
            raise RuntimeError("Child source bytes differ: "+name)
    if mode == "versions":
        import PIL, numpy, scipy
        value = {"python":sys.version,"packages":{n:{"version":m.__version__,"file":m.__file__}
                 for n,m in zip(("Pillow","numpy","scipy"),(PIL,numpy,scipy))}}
        write_json(evidence / "scientific-versions.json",value)
        return 0
    if two_goods:
        if mode != "two_goods":
            raise RuntimeError("TWO_GOODS never enters H3 reuse/composition")
        return draw_two_goods(root, work, evidence)
    if mode == "two_goods":
        raise RuntimeError("Two-goods child requires explicit outer mode")
    if mode == "reuse":
        return reuse_h2(root, work, evidence)
    # No subject imports occur before outer preflight and private exact dependency stage.
    from PIL import Image, ImageDraw, ImageFont
    from scripts.art.kit import schema
    config = json.loads((work / FIXTURE).read_text())
    grain = json.loads((work / GRAIN).read_text())
    smithy = json.loads((work / SMITHY).read_text())
    goods = [json.loads((work / path).read_text()) for path in GOODS]
    pieces = [grain,smithy,*goods]
    for piece in pieces:
        errors = schema.errors(piece,schema.load_schema())
        if errors or piece["approval"]["state"] != "candidate":
            raise RuntimeError("Source schema/status mismatch: "+str(errors))
    if grain["function"] != {} or grain["geometry"]["foot"] != [84,132] or grain["geometry"]["size_px"] != [168,144]:
        raise RuntimeError("Grain candidate metadata/anchor changed")
    if [(v["id"],v["png"],v["foot"]) for v in grain["variants"]] != [
            ("ready","res://kit/props/art/"+FILENAMES[0],[84,132]),
            ("loaded","res://kit/props/art/"+FILENAMES[1],[84,132])]:
        raise RuntimeError("Two authored states changed")
    art = work / "game/kit/props/art"
    if mode != "composition":
        raise RuntimeError("Unknown receiving phase")
    reused = json.loads((evidence / "reuse-result.json").read_text())
    if (reused.get("state") != "PASS" or reused.get("draw_invocations") != 0
            or reused.get("provenance", {}).get("artifact_id") != H2_ARTIFACT_ID):
        raise RuntimeError("Missing exact H2 reuse receipt; no painter fallback")
    for name in FILENAMES:
        if (digest(art / name) != H2_PNGS[name][1]
                or reused["files"][name]["sha256"] != H2_PNGS[name][1]
                or (art / name).stat().st_size != H2_PNGS[name][0]):
            raise RuntimeError("Exact reused H2 PNG changed BEFORE composition")
    plan = config["plan"]
    if (plan["zone"] != "grain_scale_diagnostic" or not plan["lab"] or plan["ship"] or plan["bake"]
            or plan.get("coordinate_space") != "texels" or len(plan["rows"]) !=22
            or any(len(row)!=40 or set(row)-set(plan["legend"]) for row in plan["rows"])):
        raise RuntimeError("Synthetic fixture/coordinate/glyph contract differs")
    expected = [("existing_smithy","crossroads_smithy","smithy",[240,360]),
                ("grain_candidate","crossroads_grain_scale","loaded",[552,384]),
                ("yard_handcart","crossroads_handcart","handcart",[696,312]),
                ("yard_grain_storage","crossroads_sacks","sacks_12",[432,384])]
    if [(p["id"],p["piece"],p["variant"],p["at"]) for p in plan["pieces"]] != expected:
        raise RuntimeError("Named fixture instances/positions differ; no silent variant fallback")
    from scripts.art.kit import props
    compiled = {p["id"]:props.entry(p) for p in pieces}
    if (compiled[grain["id"]]["shadow"] != {"size":[48,9],"dir":[6,3]}
            or compiled[grain["id"]]["collision"] != [-48,-24,96,24]
            or compiled[smithy["id"]]["shadow"] is not None):
        raise RuntimeError("Actual compiler shadow/collision contract differs")
    for p in pieces:
        if any(compiled[p["id"]][k] != p.get(k,{}) for k in ("function","story")):
            raise RuntimeError("Compiler lost authored function/story metadata")
        if compiled[p["id"]]["footprint"] != p["geometry"]["footprint"]:
            raise RuntimeError("Compiler footprint differs from source")
    for piece in goods:
        if (piece.get("function") != {} or piece["rendering"]["cast_shadow"] != {"shape":"baked"}
                or compiled[piece["id"]]["shadow"] is not None):
            raise RuntimeError("Goods function/shadow/status must not be promoted")
    for entry in plan["pieces"]:
        if entry["id"].startswith("yard_") and any(v % 24 for v in entry["at"]):
            raise RuntimeError("Whole-cell goods feet required; preserve sack half-X caveat")
        rect = compiled[entry["piece"]]["collision"]
        if rect:
            x,y,w,h = rect
            x,y = x+entry["at"][0], y+entry["at"][1]
            for band in config["diagnostic_access_bands"]:
                bx,by,bw,bh = band["rect_art"]
                if max(x,bx) < min(x+w,bx+bw) and max(y,by) < min(y+h,by+bh):
                    raise RuntimeError("Candidate collider obstructs authored diagnostic access band: "+band["id"])
    idx = work / "game/kit/props/index.json"
    zone = work / "game/kit/zones/grain_scale_diagnostic.json"
    if idx.exists() or zone.exists():
        raise RuntimeError("Private generated index/zone must not overwrite source")
    idx.parent.mkdir(parents=True,exist_ok=True);zone.parent.mkdir(parents=True,exist_ok=True)
    write_json(idx,compiled);write_json(zone,plan)
    # No shared ROOT/index monkeypatch, full props.build, bake or world generator.
    from scripts.review import kit_scene
    library = {p["id"]:p for p in pieces}
    # Use the complete ACTUAL metadata registry: surface:rock is a declared
    # grain alternative, even though this fixture places only lawn/worn/path.
    # Omitting scree would fabricate an unknown-ground refusal in the adapter.
    materials = {m["id"]:m for m in json.loads((work / "game/kit/terrain/manifest.json").read_text())["materials"]}
    findings = kit_scene.check_zone(plan,library=library,materials=materials)
    write_json(evidence / "physical-findings.json",findings)
    # Candidates stay visible and unapproved; physical faults refuse rendering.
    if any(f.get("severity") == "fault" for f in findings):
        raise RuntimeError("Actual private receiving physical canary refused; no repair/promotion")
    # These UNMODIFIED imports initialise native terrain sheets in memory; known
    # dependency work is counted within this ONE composition phase120s/512MiB.
    from scripts.art.kit import render_zone
    image = render_zone.render(plan["zone"],sprites=True)  # EXACTLY ONE composition
    if image.size != (960,528):
        raise RuntimeError("Reference renderer dimensions differ")
    moss = config["moss"]
    manifest = json.loads((work / moss["manifest"]).read_text())
    frame = manifest["clips"]["idle"]["facings"]["S"]["frames"][3]
    if (manifest["frame_size"] != [160,144] or manifest["foot_pivot"] != [80,136]
            or manifest["body_height_target"] !=72 or frame["region"] != [480,0,160,144]
            or frame["packed_bounds"] != [62,63,100,137]
            or frame["sha256"] != "80442f02c5d46a4eec9703122db28f6f06c46d3cb24c199bcfdc89e7916c5a37"):
        raise RuntimeError("Moss source frame identity changed")
    with Image.open(work / moss["sheet"]) as sheet:
        sheet.load()
        sprite = sheet.convert("RGBA").crop((480,0,640,144))
    if list(sprite.getbbox() or ()) != [62,63,100,137]:
        raise RuntimeError("Actual Moss crop differs from pinned packed bounds")
    # Worker feet are SOUTH of the bench, so overlay order is explicit; no
    # fake actor renderer, actor shadow, interaction or gameplay is introduced.
    image.alpha_composite(sprite,(552-80,432-136))
    native = Image.new("RGBA",(960,540),(20,22,23,255));native.alpha_composite(image,(0,0))
    draw = ImageDraw.Draw(native)
    font = ImageFont.load_default(size=10)
    box = draw.textbbox((0,0),config["qualification"],font=font)
    if box[2]-box[0] > 952 or box[3]-box[1] > 12:
        raise RuntimeError("Candidate caption does not fit reserved footer; do not crop it")
    draw.text((4-box[0],528+(12-(box[3]-box[1]))//2-box[1]),config["qualification"],font=font,fill=(230,230,225,255))
    out = root / "presentation"
    native.save(out / "grain-scale-candidate-native.png")
    native.resize((1920,1080),Image.Resampling.NEAREST).save(out / "grain-scale-candidate-2x.png")
    outputs = {p.name:{"bytes":p.stat().st_size,"sha256":digest(p)} for p in out.iterdir() if p.is_file()}
    write_json(evidence / "composition-result.json",{"state":"PASS","composition_invocations":1,
        "outputs":outputs,"fixture":config,"private_index":compiled,"physical_findings":findings,
        "grain_reuse":reused,"new_painter_invocations":0,
        "Moss":{"actual_alpha_bbox":[62,63,100,137],"packed_height":74,"target":72,
                "crop":[480,0,160,144],"foot_art":[80,136],"placed_foot":[552,432]},
        "shadow_qualification":"Actual compose.shadows for grain [48,9]/[6,3]; smithy raster/baked metadata preserved; no additional character/contact-AO pass invented.",
        "acceptance":"Synthetic candidate diagnostic execution only. EW sameheight/detail/Y12/physics wholeworld/layout/Matt acceptance remain open."})
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",choices=("outer","versions","reuse","composition","two_goods"),default="outer")
    parser.add_argument("--receiving-mode",choices=("WORKING_YARD","TWO_GOODS"),default="WORKING_YARD")
    parser.add_argument("--source",type=Path)
    parser.add_argument("--candidate",type=Path)
    parser.add_argument("--root",required=True,type=Path)
    parser.add_argument("--event-sha")
    args = parser.parse_args()
    if args.mode != "outer":
        return child(args.mode,args.root)
    if not args.source or not args.candidate or not args.event_sha:
        parser.error("outer requires --source --candidate --event-sha")
    def interrupted(signum,_frame):
        raise InterruptedError(f"Controller received{signum}; collect owned children/partials")
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGHUP,interrupted)
    return Controller(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
