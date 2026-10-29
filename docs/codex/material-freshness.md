# Material producer freshness (Y26/r1)

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
