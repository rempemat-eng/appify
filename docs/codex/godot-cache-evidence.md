# MyGame Godot cache: observed hosted evidence

Y13-warm-evidence/r1 · slot=ci-map · evidence inspected 28 October 2026.
[Claim](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6478940444),
[brief](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6475912728),
[GO](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6476941283).

## Finding

No warm restore was observed in the four successful cache-enabled jobs below.
The strongest matched pair is PR339 and its subsequent main push: identical
full Git tree, archive key, import key, runner image version and 182 clean
Godot cases, but **both archive and import restores missed in both jobs**.
Their elapsed times therefore cannot measure a cache speedup. A cache save
is evidence of publication, not evidence that a later job restored it.

This is an engineering evidence report. It changes no workflow, helper,
cache, engine pin, package, artwork or game rule. Download-cache correctness
(PR327) and import-cache correctness (PR328) already have their own validation;
this report does not repeat those suites or promote whole-Y13 acceptance.

## Pinned implementation

Audited main commit: `f51564c9783db8c9846014f3a88f1f95392f2a04`.
Full tree: `5b2474488191a5e19792c579941a416f7a564b2a`.

| Existing path                        | Git blob at audited main                   | Role                                                |
| ------------------------------------ | ------------------------------------------ | --------------------------------------------------- |
| `.github/workflows/godot.yml`        | `7ab1d4100e76e6f77859d9893ece6da414b33bd1` | Cache ordering, exact keys and unconditional checks |
| `game/tools/get_godot.sh`            | `8614f900d39d426cae1385450b0f215bbebd9a22` | Verify archive, freshly extract executable          |
| `game/tools/check.sh`                | `adb61590a9881440b4a6820019749537ea5c7cad` | Import, fresh-userdata main300, every GdUnit suite  |
| `scripts/godot-import-cache.py`      | `a2c2d3a83dc67ca082b576f2d28ac19f8ee33f5a` | Exact source/platform/engine key                    |
| `scripts/godot-import-cache.test.py` | `d5268cacca2cdb26b349e71ed8b8fdd5c8612ac3` | Key and workflow regression controls                |

The existing getter pins Godot 4.7.2 Linux x86_64 and SHA-512
`9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65`.
Its successful step verifies this digest using quiet sha512sum, then freshly
extracts. These logs do not print an independent executable-byte digest or
checksum success message; successful execution of the pinned fail-closed
getter is the evidence. The archive key contains the getter hash, not a
printed measurement of downloaded bytes.

Archive key A, identical in all four jobs:

```text
godot-archive-v1-Linux-X64-7210f4d5f5cc515f4bcb5d8a964772002bf513925cf4ebb3ede501b976de3c3a
```

Import key I, identical in the PR339/main pair:

```text
godot-import-v1-f6b93728b58bf0ab3c5584b75924c6c862a1894d68a8039dbc57f8c67bb33b2e
```

Import key P, PR328 only:

```text
godot-import-v1-44fd4b84bda005601ed1a94dfeeb2c55237b84852265714bb5b8554d3b452576
```

## Actual jobs and checkout provenance

All four runs are attempt 1 and completed successfully. Actual job logs,
rather than the PR head label alone, identify the checkout.

| Run / job                                                                                                                                                                                     | Event and actual checkout                                | Full checkout tree                         | Observed cache result                                            |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ------------------------------------------ | ---------------------------------------------------------------- |
| [PR327 run40664242375](https://github.com/rempemat-eng/appify/actions/runs/40664242375) / [job122734592830](https://github.com/rempemat-eng/appify/actions/runs/40664242375/job/122734592830) | pull_request; `9391fc0d8f25f23d693d7b26abdaee7319c8651d` | `a61db7608f902eaeef955df9e01fe66521a882fb` | A MISS, then SAVE; import cache not implemented in this checkout |
| [PR328 run40681373076](https://github.com/rempemat-eng/appify/actions/runs/40681373076) / [job122792619296](https://github.com/rempemat-eng/appify/actions/runs/40681373076/job/122792619296) | pull_request; `d8f8c04a6392c48f9450d8045092c19b5fef3560` | `b99c97fb04040d3c7caf172ef47d24c3dfb10146` | A MISS then SAVE; P MISS then SAVE                               |
| [PR339 run40739842866](https://github.com/rempemat-eng/appify/actions/runs/40739842866) / [job122998149729](https://github.com/rempemat-eng/appify/actions/runs/40739842866/job/122998149729) | pull_request; `efc237b85cc2ff06ee492a2c8fa1d58f6e0c454c` | `5b2474488191a5e19792c579941a416f7a564b2a` | A MISS then SAVE; I MISS then SAVE                               |
| [Main run40742389521](https://github.com/rempemat-eng/appify/actions/runs/40742389521) / [job123007129182](https://github.com/rempemat-eng/appify/actions/runs/40742389521/job/123007129182)  | push; `f51564c9783db8c9846014f3a88f1f95392f2a04`         | `5b2474488191a5e19792c579941a416f7a564b2a` | A MISS then SAVE; I MISS then SAVE                               |

The Git data API independently confirms PR339 checkout parents
`d7352886989d0d6e53ea59b63039de23d719e4fc` and
`f51564c9783db8c9846014f3a88f1f95392f2a04`, with the exact main tree above.
PR328 checkout parents are `121f0f00e4cb42b9e7c4e6b638bf700399be3d00`
and `126737394880110f062a9cf6fd025a25df874aa5`; PR327 parents are
`1e8ce2d8290c5be63bb70bceb7d9a42bcb30a96c` and
`121f0f00e4cb42b9e7c4e6b638bf700399be3d00`.

All jobs advertise Linux/X64 keys, Ubuntu24.04.5 and runner2.338.0. PR327/328
use runner image20261012.334.1; PR339/main use image20261025.353.1.
The older jobs also have different source/test inventories. They are context,
not a controlled performance pair. The same-key misses across different
events/refs do not by themselves diagnose a cache implementation defect or
prove why a restore missed.

## Observed durations and unconditional results

UTC on 28 October. Durations below are differences between job-step API
timestamps, reported to whole seconds. They include shell/step overhead,
not isolated download, checksum, extraction or import CPU measurements.

| Run   | Getter start–finish | Getter | Full import/main/tests start–finish | Full check | Clean cases |
| ----- | ------------------- | ------ | ----------------------------------- | ---------- | ----------- |
| PR327 | 09:26:35–09:26:37   | 2s     | 09:26:37–09:27:49                   | 72s        | 81          |
| PR328 | 11:37:27–11:37:29   | 2s     | 11:37:30–11:38:41                   | 71s        | 81          |
| PR339 | 17:52:51–17:52:53   | 2s     | 17:52:55–17:54:15                   | 80s        | 182         |
| main  | 18:09:33–18:09:34   | 1s     | 18:09:36–18:10:51                   | 75s        | 182         |

Each raw log records `ok   import`, `ok   run main scene for 300 frames`,
the clean case total (zero errors/failures/flaky/skips/orphans),
`ok   GdUnit4 tests` and `check:godot passed`.
The cache-enabled workflow also actually runs its 12 getter controls and,
where present, import-key/workflow controls before cache restore.
No check result is restored from cache. Derived imports save only after
the full command succeeds; a later hit would still execute the same command.

The five-second full-check difference between PR339 and main is ordinary
observed elapsed-time variation between two cold runs. It is not a measured
benefit. Their overall job durations additionally include substantially
different checkout time, so whole-job timing would be even less informative.

## Retrieval coverage, exclusions and next evidence

Inspected the newest 400 repository workflow-run records across four 100-row
pages, through the 27 October evening records, and fetched the actual logs for
all six successful Godot jobs in that window from PR327's first cache
publication onwards. Four use cache-enabled workflows and are tabulated
above. PR329 run40683511357 and PR341 run40744743648 use older editor/main
ancestry whose actual step lists have no cache restore; their passing
81/87-case results are not warm-cache evidence. Draft skips and older
pre-cache jobs are excluded. This is a bounded historical inventory, not a
claim that every run in repository history was inspected.

Further instrumentation is **not required yet**: current logs already expose
exact keys, miss/hit, save outcomes, checkout provenance, runner image,
step timestamps and final check totals. Next, inspect a naturally triggered
successful Godot job with unchanged relevant inputs after the main cache
save. Require an actual restore/hit for the exact key, comparable platform
and source, and the complete unconditional checks before making any
warm/cold timing statement. If no comparable warm run occurs, keep speed
and network savings unmeasured. Do not dispatch or push source just to
manufacture a benchmark; no cache-scope diagnosis or instrumentation change
is authorised by this report.

Source-only report checks do not prove native/device performance, visual
quality, gameplay acceptance, approved art or the whole Y13 programme.
Existing cache-action Node deprecation warnings remain in the raw logs.
