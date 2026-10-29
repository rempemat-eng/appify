# Material producer freshness (Y26/r2)

The existing `python3 -m scripts.art.kit.build --check` now checks the outputs
that its early return previously omitted. Claim: [6484771364](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6484771364),
lead scope: [6484700169](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6484700169).
Source starts at the frozen editor proposal `b1b066d9`; that ancestry remains
unapproved. This engineering proposal does not promote the editor or its pieces.

The fill/transition recipe-hash and existence checks remain first. If they pass,
check mode uses the **same auxiliary writer as normal generation** in an external
temporary directory and compares every file it produces byte for byte. That set
currently contains `lut.png`, `palette.png`, `materials.tres`, `tiers.png`,
`tiers.tres`, `noise.png`, every producer-returned `decal_<id>.png`, and
`manifest.json`. It is derived from the writer's actual output directory, so decal
names are not a fixed test-only list. A missing or different auxiliary output
returns 1 with its filename; the subject is never repaired. A missing output
directory is refused without creating it. Normal and `--all` generation retain
their existing recipes, output encoding and incremental/force behavior.

The committed manifest's input hashes are recipe identities, not independent
hashes of output bytes. Existing fill/transition checks still attest their recorded
recipe hashes and presence; this change does not add a full repaint comparison for
those cached images. Unreferenced historical files are not deleted. No metadata,
schema, material palette, mask, threshold or committed image/reference is changed.

`python3 -m unittest scripts.art.kit.test_build_check` calls the real argument
parser and build orchestration with a tiny temporary material/transition library,
bounded painter/decal fixtures and the real auxiliary writer. Controls cover clean
checks; missing and changed outputs; manifest drift; stale material/transition
inputs; changed auxiliary inputs and dynamic decals; absent directories; and
normal/force byte-preserving generation. Read-only assertions include file and
directory inventories, bytes, modes and modification timestamps. These fixture
controls are not production-art or rendered-material acceptance. The dedicated
workflow persists them without editing shared package/test lists.

Initial controls reproduced the old false success and missing-directory write.
Final focused results belong in the PR checkpoint. Full `npm run verify` with
zero lint, ordinary `check:art-repro` and actual hosted checks require a separate
lead allocation. Do not rerun completed editor validation or dispatch a benchmark.
Freshness does not discharge decoded/composed-material, scene, dock, visual,
placement or device obligations. Applicable editor/kit merges still require
`needs-matt-review` and Matt's explicit OK on the PR.

## External temporary parent (r2)

[Lead source scope6486164458](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6486164458)
requires check mode to refuse a temporary directory inside the subject. Before
loading recipes or asking `tempfile` to create anything, the checker resolves the
first nonempty `TMPDIR`, `TEMP` or `TMP`, otherwise the cached `tempfile.tempdir`.
A parent equal to or below the checkout root or output root, including a symlink
alias, is refused with exit1. A configured but missing parent is refused without
fallback or directory creation. With no configured/cached parent, the checker
uses the first existing `/tmp`, `/var/tmp` or `/usr/tmp`; it never falls back to
the working directory. Platforms without those defaults must configure an
existing external parent. This selection is specific to check mode; ordinary and
force generation are unchanged. The validated parent is passed explicitly to
`TemporaryDirectory`, so its default write-probing selector is never called.

Controls invoke the real `main(["--check"])` with temporary subject data and
copied source bytes: all three environment variables at the checkout root,
output root and a nonexistent output descendant; an unsafe cached parent; a
symlink alias; a valid external sibling sharing the subject's name prefix; a
missing external parent; and unavailable defaults. They assert subject inventory,
bytes, modes and modification times, plus refusal before temporary creation and
no default selector calls. Existing13 producer controls remain configured.

Changing build.py invalidates its whole-file W7 fixture provenance. Do not patch
that hash by hand: freeze the final source, then wait for a separate proof
allocation to run the documented fixture generator in an external checkout.
Only if all five PNG bytes and decoded RGBA, all other52 input hashes and all
other reference metadata agree may the owner import the generated build.py hash.
No PNG rebaseline or waived freshness assertion is authorised. That proof and
new-source full Godot/kit/verify/ordinary-art validation are still pending.
