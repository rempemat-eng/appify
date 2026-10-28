# Settlement-life source identities

X3-reference-checker/r1, slot=rivet. Extends the existing checker from PR330 at
`5832e1e384048d2ad598570537de62e731e14eaf`, after editor-data's explicit two-file release6468657415.
The original Gullwick town and packet documentation stay with editor-data. No town layout or life data is changed.

The original command and `check(plan, source)` keep their pinned Gullwick default: commit
`911edac6173ebf4398bcbf54b6171e4e68e62e13`, blob `3c238e470f2da19082227a0a56580b4d1ca2810c`.
A new town or source revision needs all three independently selected CLI arguments:

```sh
python -m scripts.settlement_life.check /tmp/canalside-packet.json \
  --source /tmp/canalside-source.json \
  --source-commit 4984438d09b5fe1333d3e6ea6e6ee82be2bdc908 \
  --source-blob 0cd85fc6468007579e8f5a7ad54bccc8cbc6cc18 \
  --source-path docs/vision/research/blockout/towns/canalside.json
```

The paths in `/tmp` are placeholders for files supplied by the receiving owner; this step does not author a
Canalside packet. Obtain the source with `git show <commit>:<repository-path>` after fetching that exact commit.
The CLI verifies the raw Git blob hash, that the selected object is a commit, and that its repository path maps to
that blob. It never takes the expected identity from the packet. Missing Git objects fail with an explicit request
to fetch them; the checker has no fallback pin or automatic source refresh. Full lowercase SHAs and a canonical
`docs/vision/research/blockout/towns/<id>.json` path are required.

A packet's `life_planning` must name matching `source_commit`, `source_blob` and, for explicit pins, `source_path`.
All non-life fields must still equal the selected source, including new `landmarks`, `counts_as` and counting notes.
In particular, copying new identity labels onto the original Gullwick packet does not carry the newer layout
metadata into it and fails. Integrating the newer source with a life block is a receiving-owner action, not an
exemption from the no-drift check. Counting rules themselves remain the existing town checker's responsibility.

The pure API accepts `check(plan, source, source_pin=SourcePin(commit, blob, path))`; callers must independently
verify/trust their parsed source. `verify_source(raw_bytes, pin)` performs the CLI's byte/Git verification.
The API checks the source town ID and unique place IDs as well as the original references. Source identity is
provenance, not town-plan, art, role, timing or gameplay approval.

Every existing planning boundary remains: one provisional representative per authored occupied building, original
role/district, placeholder names, deferred workplaces/headcounts/animals/props, proposal status and runtime disabled.
Morning/day/evening/night remain ordering placeholders. Day refers only to the home's authored frontage; the other
phases refer to home. These are the original packet assumptions, not production routine or clock rules.

## Validation and limits

`python -m unittest scripts.settlement_life.test_check -v` retains all five original methods and adds current
Canalside/Gullwick source fixtures at `4984438d`, synthesized only inside tests. It checks valid explicit pins,
actual CLI exits0/1/2, exact bytes and commit/path/blob disagreement, incomplete/noncanonical pins, metadata/role/
layout/approval refusals, duplicate places and malformed JSON. Temporary paths contain spaces; both input files
must remain byte-identical. Duplicate JSON keys, non-JSON numeric constants and invalid UTF-8 are malformed inputs.
The new dedicated workflow runs these focused controls, fetching only the two exact source snapshots and the existing
draft/ready policy. It does not edit shared package scripts or bypass ordinary verification/art checks.

This remains an offline planning validator. It does not author another town's population, provide pathfinding,
validate rendered density, activate routines or prove device/native runtime behavior. No Godot/runtime code changed.
Claude A reviews the source identity contract and integrates after the original packet; later town owners choose
explicit authored inputs and preserve their metadata and life blocks during generator refreshes.
