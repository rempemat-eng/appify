# PR pre-review sheets

`scripts/review/pr_sheet.py` puts a PR's changed PNGs beside the existing asset gate's numbers, and can include registered Godot scene captures. It is an offline evidence bundle for Claude A's review. It neither records catalogue verdicts nor approves art. The independent reviews and reference comparisons in [review-agents.md](../review-agents.md) still apply.

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

| Exit | Meaning |
| --- | --- |
| `0` | Every selected detector row passes with usable evidence, or the explicit `no_art` scope has nothing to rate. A `no_art` result is not an art detector pass. |
| `1` | A bundle was written with failing, unsupported, removed, missing or incomplete evidence. Inspect row errors and raw logs. |
| `2` | A preflight/argument/command failure prevented normal completion. Existing output may be partial; use a fresh directory for a new run. |

`complete` means the selected detector evidence is complete **and passing**. It remains false for a well-formed report containing blocker/fault findings. It does not mean the PR, the whole game, style direction or all scene dependencies are approved.

## Checks

```sh
python3 -m unittest scripts.review.test_pr_sheet
npm run check:review
npm run verify
npm run check:art-repro
```

The PR-sheet tests use real temporary Git histories and fixture command producers to exercise orchestration, provenance and failure handling. They do not substitute for the existing detectors' tests or a real supported producer smoke. Run `npm run check:godot` when scene/runtime work is relevant, and retain exact tested-head results and practical limitations in the PR handoff.
