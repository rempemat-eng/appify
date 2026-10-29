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

The manifest records pinned base/head/merge-base/tree IDs, Git change records, committed input blob IDs and SHA256s, the wrapper's and representation helper's SHA256s and Python version, command arguments, exits, timings, raw report/log hashes and relative evidence paths. `files` hashes every regular bundle file present before the manifest is written, including the index and previews. The manifest excludes its own recursive hash. Keep the manifest with its files; hashes establish byte identity, not authorship or a trusted execution environment.

## Town, kit and cast source classification (Y12-classifier/r1)

[GO6476941283](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6476941283) opened this follow-up only after PR322 was actually included in main `f51564c9783db8c9846014f3a88f1f95392f2a04`. [ASSIGN6477100506](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6477100506), slot=axiom, owns only this document, `pr_sheet.py` and its existing focused test module. It extends the existing wrapper; it changes no detector, source art, scene adapter, approval state or game rule.

The old path list could classify town JSON, W0 concept JSON and cast manifests as `not_art`, yielding a successful `no_art` bundle with no source evidence. Production source is now explicitly incomplete, even when a PNG in the same PR passes its existing raster detector. It cannot be replaced by the PNG result. The wrapper deliberately does **not** validate town geometry, concept semantics or cast contracts: malformed JSON or a missing/wrong schema marker in a known production directory still requires source review.

| Bounded source category | Repository paths                                                                                                                                                                                                                                                                                                    |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `town_plan`             | `docs/vision/research/blockout/towns/`; own `docs/codex/*-town-polish.md` descriptions                                                                                                                                                                                                                              |
| `kit_concept`           | `game/data/kit/concepts/`; requirements files named `<region>-kit.md` directly under `docs/codex/`, including new regional requirements; exact `docs/codex/painted-structure-context-plan.md` proposal                                                                                                              |
| `cast_source`           | `art/characters/`, `art/cast/`, `castwork/`, `docs/vision/characters/`, `docs/characters/`, `scripts/characters/`, `game/assets/characters/`, `game/data/cast/`, `game/data/progression/`; exact `docs/vision/{cast,world-and-cast,progression}.md`, `game/data/weapon_lines.json` and `game/actors/cast_sprite.gd` |
| `art_source`            | Existing `scripts/art/`, `game/art/`, `game/kit/`, `game/data/plans/`, `.gdshader`/`.ase` inputs; Python authoring sources under `docs/vision/research/blockout/` (including `towns55.py`, `town_plans.py`, `geo55.py`)                                                                                             |

Changed images still take the existing raster path, including ordinary PNGs under the cast directories. If either side of an image rename is a known **non-image** production source, the bundle also retains a separate `source_only` row with both source versions and exact byte copies. A passing after-image detector cannot erase the before-source review obligation, even when a malformed `.json` originally contained PNG bytes. Image-only changes normally remain on their existing raster path; direct kit representation bindings have the incomplete context handling below. Registered scene inference and its import/capture requirements are unchanged. Source-only changes have `status=source_only`, their category and an `inputs` list. Each input pins side (`before`/`after`), ref, path, Git mode/blob and SHA256, with an accessible exact-byte `.txt` copy under the bundle's `sources/` directory. These are plain source links, not executable HTML or image previews. Source copies are rehashed before finalisation and included in the bundle file manifest. Additions retain the head bytes, deletions retain merge-base bytes, and modifications/renames retain both sides. A rename out of a production directory cannot evade classification through its new filename. A symlink is recorded as the committed link bytes, never followed into external data, and keeps the evidence incomplete.

If only production sources change, the bundle has `scope=source_only`, `complete=false`, exit1. This is review evidence, not a producer failure or proof the source is defective. Mixed source/raster/scene bundles retain `scope=detector_evidence` and every real detector result, while unresolved source rows keep overall completeness false. Classification/provenance is deterministic for fixed Git objects; timestamps, actual command timings and raster-producer outputs are not claimed byte-deterministic across runs.

### Deliberately invalid test inputs

An invalid fixture is not a shipped piece and should not receive a production art verdict. Only these explicit repository namespaces are fixture evidence: `game/test/fixtures/`, `game/kit/schema/invalid/`, `scripts/review/fixtures/`, `scripts/art/kit/fixtures/`, `scripts/art/native/fixtures/` and `tests/fixtures/`. A name merely containing `fixture` or `test` is not sufficient. For example, `game/data/kit/concepts/fixtures/bad.json` remains production concept source and a PNG under `game/assets/characters/fixtures/` still requires raster evidence.

Changes wholly within those fixture namespaces, including intentionally invalid PNG/SVG/JSON bytes and explicitly requested fixture asset context, have `status=test_evidence`, `category=test_fixture` and pinned input bytes. They do not invoke production raster detectors. Fixture-only bundles have `scope=test_evidence`; exit0/complete means the requested fixture **inventory** is attested, not that the tests ran, a fixture is valid, or production art passed. Nonregular or missing fixture inputs remain incomplete. Moving a fixture into a production source or image namespace loses the exemption; both sides of renames are considered. No fixture is promoted, made buildable/placeable, or granted approval by this routing.

This is still a bounded repository-path classifier, not a transitive dependency scanner or semantic approval system. New production namespaces need an explicit extension and regression controls. Ordinary code/documentation outside the listed source namespaces can retain `no_art`, which is always distinct from art approval. The HTML and manifest expose the category and source pins even where no preview or raster measurements exist.

### Regional requirements documents (Y23/r1)

[Brief6483506669](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483506669) and [ASSIGN6483527045](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483527045), slot=quill, extend the existing requirements-file namespace. The six-name list omitted the actual Frostline and Brackens reports and the reserved Cogsworth and Lull reports. A source-only CLI request could therefore report `no_art`, `complete=true`, exit0; a passing PNG could also hide the missing source obligation.

Every nonempty `<region>-kit.md` basename directly under `docs/codex/` now receives `source_only`/`kit_concept` evidence, including future regions and unusual committed filenames. Matching uses the repository path, never the prose or the region's name. Nested files such as `docs/codex/notes/lull-kit.md`, other documentation directories and suffixes such as `frostline-kit.md.backup` are outside this specific namespace. This is source classification only: malformed Markdown bytes are still retained exactly, and routing validates no kit design, schema, placement or approval state.

The existing before/after byte-copy and completeness rules apply unchanged to additions, edits, renames and deletions. Moving a requirements file to a passing PNG retains its separate before-source review obligation. Moving a fixture into this production namespace loses its exemption, while a kit-named file wholly inside an explicit fixture namespace remains test evidence. Source rows keep mixed raster bundles incomplete/exit1; their presence never grants art approval. The focused tests exercise actual temporary Git histories and the real wrapper CLI, with fixture raster producers only at the established detector boundary.

The exact `docs/codex/painted-structure-context-plan.md` test-layout proposal also receives `source_only`/`kit_concept` evidence under [Y34 GO6494933086](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6494933086). Its addition, deletion or either side of a rename retains the same source-byte obligations, incomplete status and unassessed manual review. This does not execute the proposed JSON, render a context or clear its bridge faults; physical/raster checks remain unrun, not visual PASS. The match does not include nested copies, backup suffixes, ordinary engineering reports such as `bank-edge-diagnosis.md`, or other Markdown. A copy wholly inside an explicit fixture namespace remains fixture inventory; moving it into the exact production proposal path loses that exemption.

### Kit representation context (Y25/r1)

[Brief6484223399](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6484223399) and [GO6484410205](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6484410205), slot=palette-context, add bounded metadata routing. Encoded palette codes, transition operations and shadow ramp-step masks are inputs to rendering. Their raw PNG colours cannot establish either a rendered defect or a rendered pass. Historical PR344 results are preserved; this extension does not reinterpret or approve that evidence.

The wrapper reads each relevant side's **committed** `game/kit/terrain/manifest.json` or `game/kit/props/index.json`. Direct terrain members are `materials[].fill`, `transitions[].png`, `decals{}.png`, `lut`, `noise` and `palette`. Prop `shadow.mask.png` binds a tree's shadow operations; indexed `variants{}.png` identifies physical artwork and retains the ordinary raster detector. No filename prefix grants an exemption. Kit-like names elsewhere retain ordinary detection. Inputs wholly inside existing fixture namespaces retain fixture inventory routing.

A data member has `classification=context_required` inside the asset row's `representation_inputs`, while its detector `status` remains `incomplete`, counts/exit remain null and no ordinary asset command is run. Its preview is the original encoded PNG, **not a decoded or rendered image**. Every relevant before/after side records its ref/path, owners, raw image and metadata mode/blob/SHA256, and accessible exact-byte copies. Those copies are checked again before finalisation. A rename out of the kit directories or a deletion retains its before-side obligation and provenance. Physical artwork cannot discharge a prior data-context obligation merely by receiving a new filename.

Missing, malformed, duplicate-key, unsafe-path, ambiguous or unbound metadata remains `unresolved` and incomplete. This is a direct binding check, not the full piece schema or a transitive dependency scanner. Indirect texture references, including the tier palette reached through a `.tres` file, are not interpreted. Unknown PNGs in the terrain or kit-prop-art directories remain incomplete rather than receiving an unsupported representation verdict. Linked metadata is retained as committed link bytes and never followed. Known indexed physical sprites keep their existing detector and findings.

**Freshness is `not_assessed` for every binding.** The terrain recipe hashes are input hashes, and the prop index has no output-byte hash. Committed metadata does not independently establish that generated PNGs are current. This step neither executes generators nor decodes pictures, evaluates material quality or creates an acceptance gate. A resolved binding still requires producer/output freshness evidence, decoded/composed-material or owner-shadow scene review, the applicable library gates and reference comparison, independent review and Matt's approval. Even passing scene rows cannot turn the outstanding context row into `complete=true`.

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

## Optional managed launch mode (Y47, source preparation only)

GO6503275523 / ASSIGN6503377386 adds a controller-owned broker and adapters for
the existing Y12 launch graph. This section and the new controls are **source
preparation, not observed process isolation or successful Y12 evidence**. No
helper import, pidfd probe, fake producer, engine, display or project test has
run under this source-only allocation.

An external controller can explicitly create one `owned_broker.Broker` facade in a
new private directory and use its `environment()` with `owned_launch.run()`.
The top-level PR-sheet Python must itself be launched through that client; an
independently started producer is not retrospectively registered. Supply an
absolute, reviewed tool-source import root in `PYTHONPATH`, invoke Python with
`-P -B -m scripts.review.pr_sheet`, and supply the already allocated `GODOT`
and authenticated `DISPLAY`. Creating the broker, importing these helpers or
running that command requires a separate exact runtime allocation.

The explicit mode is requested by any `MYGAME_OWNED_SOCKET`,
`MYGAME_OWNED_TOKEN` or `MYGAME_OWNED_PARENT` key. Incomplete credentials,
unavailable pidfd operations, a broken channel or a cancelled allocation fail
closed. There is no local subprocess fallback. Ordinary mode keeps its existing
launch and error behavior. No automatic acquisition or Xvfb startup is permitted
in managed mode. The controller remains responsible for the approved copied
engine, private roots, source guards, display and external resource policy.

Audited registered edges are the top producer, PR-sheet `_git`, asset/import
and scene `_command` producers, and the scene runner's `_godot_command`.
Managed child Python producers use `-I -B` and the reviewed absolute client
bootstrap. It binds `core.REPO` to the subject before importing assets/run and
their scene/construct/scale dependencies; derived scene/game/catalogue paths
and Godot cwd therefore refer to that subject. Actual rewritten argv remains
in each command record. The subject working directory must not silently load
an older, unadapted runner from frozen375. Static inspection found no additional
process-launch site. Detector reference `eastward_bands.json` and the imported
`scripts.art.native.palette` code still belong to the reviewed TOOL tree; they
are not relocated by `core.REPO`. Any later real-sheet allocation must attest
those tool-reference bytes separately alongside the subject paths. The tiny
routing controls do not establish actual detector reference parity.
Git helpers, engine/native forks and arbitrary other
subprocess calls are **unregistered descendants**, not contained or measured
by this change. A caller supplying the authentication token is trusted; this is
an accounting protocol, not a sandbox against malicious authenticated clients.

The facade starts only a fixed reviewed `-I -S -B` service interpreter, with a minimal
bootstrap environment. Controllers cannot pass callbacks or modules to that service.
The service is the actual parent of managed targets; the facade is their grandparent.
An owner pipe cancels and collects targets on controller exit. Before even the service
spawn, the facade refuses ignored SIGCHLD, SA_NOCLDWAIT and unsupported signal ABIs.
The supported policy is deliberately limited to Linux x86_64 glibc (152-byte sigaction,
flags at offset136); other platforms refuse before spawning. The fresh service installs
and verifies default/non-auto-reaping SIGCHLD before its threads or target creation,
then rechecks it before every target spawn. Only its reviewed per-PID raw wait routine
reaps targets, under a per-process wait lock. No controller/native waiter can reap these
grandchildren. Popen poll/wait is never used as kernel-wait evidence; ECHILD records
failed accounting and retains the job instead of synthesising success. This is a trusted
accounting boundary, not protection against malicious same-user process interference.

For each registered launch the service broker is the actual parent. A trusted Python
gate receives only a minimal trusted bootstrap environment. Target argv and
environment, including dynamic-loader variables, are read as bounded JSON and
applied only at target exec after the broker opens and records the child's
pidfd. Registration refusal closes the gate and waits for the trusted helper;
no target code should run. Cancellation closes unreleased gates, signals only
retained pidfds and refuses later launches. No numeric PID/PGID signalling or
`/proc` discovery fallback is present in the managed helpers. Actual wait
results and logical parent links remain in the controller's broker receipts;
a JSON numeric PID alone is not proof. A failed wait/signal or surviving handler
keeps collection failed, rather than declaring cleanup complete.

Request frames have an absolute2s deadline including header and payload; progress does
not reset it. Accepted channels are tracked before handlers start and shutdown on
cancellation, including incomplete prelaunch frames. Exit shares one8s collection
deadline across all handlers. Captured text follows subprocess default encoding,
errors-only text selection and CRLF/CR universal-newline translation.

One allocation is bounded to32 concurrent channels,4096 accepted connections
and4096 logical request identities; duplicate IDs are refused. Requests are at
most512KiB, captured stdout plus stderr at most4MiB per job, replies at most9MiB
and each target timeout at most3600s. Output overflow cancels and fails. Timeout
uses a bounded3s post-cancel drain and5s direct-child wait; inherited pipes held
by an unregistered descendant can therefore yield explicit incomplete-output
failure. The client allows10s protocol/collection overhead. These are channel
and per-job bounds, **not global RSS, descendant cleanup or full-Y12 proof**.
Native-descendant cancellation requires a separately reviewed execution boundary.

### Prepared focused-control allocation request (NOT allocated)

The proposed first run uses one CPU,180s outer wall time,512MiB observed memory,
8MiB outer text and64MiB total new private output. Refuse an unsupported pidfd
environment rather than skipping methods. Use only a new controller/test/temp
root; no original editor/source/index/profile mutation or cleanup, real engine,
display, art, project assets, Node, dependency installation/copy or full gates.
Require a reviewed outer collector with actual exits, logs, source hashes and
owned-child collection before execution. Exact final file hashes belong in the
source handoff; this document does not embed a circular self-hash.

First authorisation would cover exactly22 methods in
`OwnedLaunchControls`, then separately approved import prerequisites and six
methods in `OwnedAdapterControls`. The adapter module imports the existing
review/Pillow/NumPy stack; that private import layout and available dependencies
must be explicitly approved before invocation. No full-source hydration is
implied. The existing PR-sheet suite and all ordinary full gates remain separate.

The controls exercise real fake producer -> scene runner -> engine nesting,
actual parent/wait/argv/environment/streams/status, simulated unavailable Python
`/proc` reads (not a kernel namespace proof), immediate exit, failed exec,
registration refusal before target execution, gate/nested cancellation, timeout,
broken channel, duplicate/late requests, output overflow, ordinary detector
exit1, engine-error text at exit0, acquisition/display/stripped-credential refusal,
and reviewed-tool routing with subject-derived scene/asset paths and fake-engine
cwd despite hostile subject modules (tiny tool fixtures, not detector coverage). One waited native
grandchild deliberately demonstrates the unregistered-descendant limit.

All28 controls are **UNRUN** (22 broker/client plus six adapter methods).
The superseded nineteen-method source-only plan remains historical, not executed.
Additional controls cover ignored SIGCHLD, SA_NOCLDWAIT, unsupported ABI, forbidden
in-process service authority, lost actual wait, slow frame absolute deadline and
partial-frame cancellation, repeated-cancel control replies and rejection of a
pending logical parent before any actual/kernel wait. Test-only isolated service bootstraps inject faults; the
production facade accepts no injection or callback parameter. AST parsing, a static review or later fake-process
success cannot establish real Godot/display containment, memory measurement,
render freshness, visual quality, source-sheet completeness, device behavior or
Matt's approval. Source379/E9/E10 and editor375 retain their separate validation
and inherited acceptance holds; no Ready or merge follows this preparation.
