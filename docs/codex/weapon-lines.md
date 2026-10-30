# Y2: proposed weapon lines, detached from live combat

`WeaponLines` is a read-only `RefCounted` resolver. Its table is a proposal, **not an approved balance or art specification**. It neither applies mechanics nor grants an evolution. Claude A owns review and live integration; C60's approved canonical values are unavailable here. Y3 owns payment/respec transactions and Y1 records tiers only after the caller's approved transaction.

## Pinned authority and extraction

Y2 in `docs/vision/development-plan.md` asks for the current weapon table as data and runtime. The table's authority is PR #290 at commit `debdf9495bd32966e1f1b65a67a5e6964b62b743`, including `docs/vision/world-and-cast.md`: the weapon table is explicitly unapproved and all balance values are placeholders. That document is absent from this task's main base. This task does not replace main's progression catalogue or its fourteen authored folk files.

`game/data/weapon_lines.json` copies each complete `.weapon` object from those fourteen pinned folk files without changing its fields, names, forms, requirements, mechanics, or existing art descriptions. It contains 56 stages, including repeated forms with different mechanics. The wrapper records the source commit, catalogue blob, individual source path/blob and SHA-256 of each canonical weapon object. It sets `approved=false` and `mechanics_applied=false` and retains the proposal/placeholder label.

From the repository root:

```sh
python3 scripts/progression/weapon_lines.py --write
python3 scripts/progression/weapon_lines.py --check
python3 scripts/progression/weapon_lines.py --check-stored
```

`--write` reads the pinned Git objects, validates the extraction and replaces the output through a temporary file. `--check` reconstructs and compares the complete parsed table with those source objects; it fails if they are unavailable. Supply the pinned PR commit/objects before running these two commands. No network request is made by the script itself; Git's existing partial-clone configuration may retrieve missing blobs.

`--check-stored` works without Git or the original PR objects. It validates proposal flags, source metadata, fourteen unique records, stage structure and stored content fingerprints. This detects accidental/stale edits; a fingerprint alone does not authenticate upstream authorship. The source-backed `--check` supplies that comparison. Checks never rewrite their input. `--path PATH` selects an alternate output/input.

Canonical fingerprint encoding is Python JSON with sorted keys, compact separators, UTF-8, unescaped Unicode and non-finite numbers refused. Integers remain integers in the stored extraction. Re-encoding through a float-only JSON reader can change fingerprints; do not regenerate the table that way. The GdUnit suite additionally pins the committed table's whole-file SHA-256 and exercises the offline command, so the existing Godot gate covers extraction drift without new package scripts or CI configuration.

## Runtime interface

Load the bundled JSON into a dictionary and call `configure(document)`. Configuration copies accepted metadata and replaces the previous catalogue only after validation succeeds. It validates the used shape, proposal flags, source identifier/hash syntax, fourteen unique lines and four stages at levels 1, 8, 16 and 24. It accepts whole JSON numbers. It does not recompute canonical fingerprints or authenticate source blobs; the extraction checks above do that.

- `status()` returns the proposal label, source and `preview_only=true`, `approved=false`, `mechanics_applied=false`.
- `folk_ids()` lists the configured folk; `line(id)` returns a detached raw weapon object (or an empty dictionary). Use `status()` alongside raw line metadata when presenting it.
- `at_tier(id, tier)` resolves an explicit stage, retaining proposal flags and source provenance. Unknown IDs or invalid tiers return `ok=false` with a reason.
- `current(projection, id)` accepts the caller's detached `{progression: {level}, folk: {id: {weapon_tier}}}` projection. It requires an already joined folk and a recorded tier consistent with the shared level. A level-30 folk recorded at tier 1 still resolves tier 1. Other projection fields are neither interpreted nor modified.
- `compare(id, from_tier, to_tier)` returns detached stages and flags for changed form and mechanics dictionaries. It does not interpret modifiers or calculate damage.

All returned arrays/dictionaries are detached. Invalid projections, non-finite/fractional/boolean tiers, unjoined folk and above-level records are read-only refusals. No autoload, project configuration, Player, SaveGame, ability, UI, animation, payment, authored progression or art file changes are included. No live gameplay, device, visual, approved balance, forge transaction or combined Y integration acceptance is claimed.
