# PR pre-review sheets

`scripts/review/pr_sheet.py` puts a PR's changed PNGs beside the existing asset gate's numbers, and can include registered Godot scene captures. It is an offline evidence bundle for the Codex lead and Matt's review. It neither records catalogue verdicts nor approves art. The independent reviews and reference comparisons in [review-agents.md](../review-agents.md) still apply. Matt alone approves art/map merges under the current [handover](handover.md).

## Run it

Use a trusted, isolated, full checkout of the subject head. The tool executes that checkout's existing `scripts.review.assets` and `scripts.review.run` modules. It is not a sandbox for untrusted PR code. Install the existing review dependencies (Python, Pillow, numpy and scipy). Scene captures also need the project's Godot binary, its normal import/runtime dependencies and `Xvfb` on `PATH`; see [godot.md](../godot.md). Set `GODOT` to an installed binary to avoid the normal resolver's download path.

From a checkout containing this tool, for example:

```sh
python3 -m scripts.review.pr_sheet \
  --repo ../subject-checkout \
  --base origin/main --head HEAD \
  --out ../review-evidence/pr-sheet \
  --pr 'PR #123'
```

Here `origin/main` must be the PR's actual target ref, fetched separately before the run; the script does not fetch GitHub or establish which PR owns a commit. `--pr` is only a descriptive label. Base and head are resolved once to commit IDs, then changes use Git's three-dot semantics: the unique merge base through head. This excludes changes made only on the target branch. Run from the actual PR head for head evidence, or from a clean proposed merge checkout when reviewing the integrated result; record which one you used.

The subject's `HEAD` must match the pinned head and tracked files must be clean. Assume-unchanged and skip-worktree entries are rejected; Git replacement objects are ignored. Source guards run around producers. If a producer changes tracked source or moves `HEAD`, the bundle stays incomplete and the tool preserves that checkout for inspection. It never resets it. Ignored imports, installed dependencies and untracked files are not attested by the Git tree; use a controlled checkout and environment.

The output must be new or empty, outside Git metadata. Existing evidence is neither reused nor deleted. Open `index.html` and retain the whole directory with `manifest.json`, previews, reports, logs and scene images.

Add scene or asset context explicitly:

```sh
python3 -m scripts.review.pr_sheet \
  --repo ../subject-checkout --base origin/main --head HEAD \
  --out ../review-evidence/undercroft-sheet \
  --scene undercroft --spawn start \
  --asset game/zones/woodland/art/forest_bench.png
```

`--scene`, `--spawn` and `--asset` are repeatable. Scenes must be registered IDs from `game/data/zones.json`; a changed `.tscn` infers a scene only when its exact path matches a registered target. A PNG change alone does not infer every zone that uses it. Without `--spawn`, each requested scene must supply evidence for every declared spawn. Explicit spawns must be declared by that scene. Arbitrary scene/plan overrides are unsupported. The producer's `zone` spawn/composite filename collision is reported as incomplete because a distinct rendered capture cannot be established.

`--asset` adds a committed PNG as context, marked `requested`; it does not turn an unchanged asset into a Git change. Changed PNGs are selected automatically. The original NUL-delimited Git change records retain additions, modifications, renames and removals, including unusual filenames. A removed PNG gets its merge-base preview, without a head detector pass. Other image formats, linked/nonregular images and recognised art source-only changes remain visible and keep the bundle incomplete. Other code changes are listed without an art rating. This is a bounded classifier, not proof that every art dependency has been discovered; choose relevant scenes and context yourself.

## Read the evidence

The asset command uses the existing public `--no-sheet` option: all detector findings, counts and detail-bar measurements remain unchanged, while this page displays the byte-identical committed preview beside them. The legacy contact/style-reference sheet is not generated (`gate_sheet` is null for assets). No kit-reference cache is generated, no `--record` is used and no catalogue verdict is written. Perform the required scale, sibling and reference comparisons separately.

Scene evidence includes an observed Godot import preflight, raw rendered captures for the requested spawns, the scene composite and the producer's boxed/grid pictures. Missing captures, unsafe evidence paths, malformed reports, mismatched input hashes, stale reports, inconsistent finding counts, logged engine errors and command failures cannot become passes. Timeouts retain logs and stop the owned producer process group. These checks validate the evidence the producer exposes; they cannot certify errors or process results that the existing producer suppresses. Captures are rendered desktop evidence, not native/device testing, gameplay coverage or a manual visual verdict.

Counts are the producer's reported finding **occurrences**. Scene findings also appear on the zone composite and may therefore be counted twice by that producer. The sheet preserves this convention; it does not add asset and scene numbers into a total of unique faults. Blocker/fault/polish counts and detector passes are leads for the independent reviewers, never art approval. `manual_review` always remains `not_assessed`.

The manifest records pinned base/head/merge-base/tree IDs, Git change records, committed input blob IDs and SHA256s, the wrapper's SHA256 and Python version, command arguments, exits, timings, raw report/log hashes and relative evidence paths. `files` hashes every regular bundle file present before the manifest is written, including the index and previews. The manifest excludes its own recursive hash. Keep the manifest with its files; hashes establish byte identity, not authorship or a trusted execution environment.

## Town, kit and cast source classification (Y12-classifier/r1)

[GO6476941283](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6476941283) opened this follow-up only after PR322 was actually included in main `f51564c9783db8c9846014f3a88f1f95392f2a04`. [ASSIGN6477100506](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6477100506), slot=axiom, owns only this document, `pr_sheet.py` and its existing focused test module. It extends the existing wrapper; it changes no detector, source art, scene adapter, approval state or game rule.

The old path list could classify town JSON, W0 concept JSON and cast manifests as `not_art`, yielding a successful `no_art` bundle with no source evidence. Production source is now explicitly incomplete, even when a PNG in the same PR passes its existing raster detector. It cannot be replaced by the PNG result. The wrapper deliberately does **not** validate town geometry, concept semantics or cast contracts: malformed JSON or a missing/wrong schema marker in a known production directory still requires source review.

| Bounded source category | Repository paths                                                                                                                                                                                                                                                                                                    |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `town_plan`             | `docs/vision/research/blockout/towns/`; own `docs/codex/*-town-polish.md` descriptions                                                                                                                                                                                                                              |
| `kit_concept`           | `game/data/kit/concepts/`; the six exact `docs/codex/{crossroads,coast-city,sunstone,fire-country,tidebloom,highgarth}-kit.md` requirements documents                                                                                                                                                               |
| `cast_source`           | `art/characters/`, `art/cast/`, `castwork/`, `docs/vision/characters/`, `docs/characters/`, `scripts/characters/`, `game/assets/characters/`, `game/data/cast/`, `game/data/progression/`; exact `docs/vision/{cast,world-and-cast,progression}.md`, `game/data/weapon_lines.json` and `game/actors/cast_sprite.gd` |
| `art_source`            | Existing `scripts/art/`, `game/art/`, `game/kit/`, `game/data/plans/`, `.gdshader`/`.ase` inputs; Python authoring sources under `docs/vision/research/blockout/` (including `towns55.py`, `town_plans.py`, `geo55.py`)                                                                                             |

Changed images still take the existing raster path, including ordinary PNGs under the cast directories. If either side of an image rename is a known **non-image** production source, the bundle also retains a separate `source_only` row with both source versions and exact byte copies. A passing after-image detector cannot erase the before-source review obligation, even when a malformed `.json` originally contained PNG bytes. Image-only changes remain on their existing raster path. Registered scene inference and its import/capture requirements are unchanged. Source-only changes have `status=source_only`, their category and an `inputs` list. Each input pins side (`before`/`after`), ref, path, Git mode/blob and SHA256, with an accessible exact-byte `.txt` copy under the bundle's `sources/` directory. These are plain source links, not executable HTML or image previews. Source copies are rehashed before finalisation and included in the bundle file manifest. Additions retain the head bytes, deletions retain merge-base bytes, and modifications/renames retain both sides. A rename out of a production directory cannot evade classification through its new filename. A symlink is recorded as the committed link bytes, never followed into external data, and keeps the evidence incomplete.

If only production sources change, the bundle has `scope=source_only`, `complete=false`, exit1. This is review evidence, not a producer failure or proof the source is defective. Mixed source/raster/scene bundles retain `scope=detector_evidence` and every real detector result, while unresolved source rows keep overall completeness false. Classification/provenance is deterministic for fixed Git objects; timestamps, actual command timings and raster-producer outputs are not claimed byte-deterministic across runs.

### Deliberately invalid test inputs

An invalid fixture is not a shipped piece and should not receive a production art verdict. Only these explicit repository namespaces are fixture evidence: `game/test/fixtures/`, `game/kit/schema/invalid/`, `scripts/review/fixtures/`, `scripts/art/kit/fixtures/`, `scripts/art/native/fixtures/` and `tests/fixtures/`. A name merely containing `fixture` or `test` is not sufficient. For example, `game/data/kit/concepts/fixtures/bad.json` remains production concept source and a PNG under `game/assets/characters/fixtures/` still requires raster evidence.

Changes wholly within those fixture namespaces, including intentionally invalid PNG/SVG/JSON bytes and explicitly requested fixture asset context, have `status=test_evidence`, `category=test_fixture` and pinned input bytes. They do not invoke production raster detectors. Fixture-only bundles have `scope=test_evidence`; exit0/complete means the requested fixture **inventory** is attested, not that the tests ran, a fixture is valid, or production art passed. Nonregular or missing fixture inputs remain incomplete. Moving a fixture into a production source or image namespace loses the exemption; both sides of renames are considered. No fixture is promoted, made buildable/placeable, or granted approval by this routing.

This is still a bounded repository-path classifier, not a transitive dependency scanner or semantic approval system. New production namespaces need an explicit extension and regression controls. Ordinary code/documentation outside the listed source namespaces can retain `no_art`, which is always distinct from art approval. The HTML and manifest expose the category and source pins even where no preview or raster measurements exist.

| Exit | Meaning                                                                                                                                                                              |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `0`  | Every selected detector row passes with usable evidence, or explicit `no_art`/`test_evidence` has no production art to rate. Fixture inventory is not a test or production-art pass. |
| `1`  | A bundle was written with failing, unsupported, removed, missing or incomplete evidence. Inspect row errors and raw logs.                                                            |
| `2`  | A preflight/argument/command failure prevented normal completion. Existing output may be partial; use a fresh directory for a new run.                                               |

`complete` means the selected detector evidence is complete **and passing**. It remains false for a well-formed report containing blocker/fault findings. It does not mean the PR, the whole game, style direction or all scene dependencies are approved.

For source-only inputs, completeness remains false until appropriate separately produced review evidence exists. For fixture-only inputs it attests the inventory and regular committed bytes, not test execution. No new override/auto-approval flag can turn these classifications into production acceptance.

## Checks

```sh
python3 -m unittest scripts.review.test_pr_sheet
npm run check:review
npm run verify
npm run check:art-repro
```

The PR-sheet tests use real temporary Git histories and fixture command producers to exercise orchestration, provenance and failure handling. They do not substitute for the existing detectors' tests or a real supported producer smoke. Run `npm run check:godot` when scene/runtime work is relevant, and retain exact tested-head results and practical limitations in the PR handoff.
