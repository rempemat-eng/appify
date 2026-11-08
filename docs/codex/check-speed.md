# Verification speed (C35/r1)

`npm run verify` runs the complete canonical `package.json` check list in a bounded pool (two jobs by default), then exports web and iOS in order. `npm run check` and `npm run verify:serial` retain the serial path. Unsupported check-list syntax fails explicitly instead of omitting a step. Exports do not start after a failed check; the other scheduled checks finish and report their failures.

## Art reproducibility

Each generator group receives its own disposable tracked-source copy, Git index and preview directory. Garden and zones run in that order in the same copy because the world canvas reads garden ground and walk data. Journey and rocket also stay together. Other groups run independently, with no shared output tree. Each group compares all tracked bytes and checks for unexpected generated files. Formatting and sprite validation always run, including on a cache hit. Generator, formatter, sprite, subprocess and snapshot failures remain failures.

A local certificate under `.cache/art-repro` permits skipping generators only after a complete successful run with identical inputs. Its SHA-256 key includes every tracked file's path, current bytes, length and executable mode; all installed Node tools/dependencies; npm/npx and Git executables; the Python executable, shared interpreter library and standard library (excluding site-package roots); the actually imported PIL, numpy and scipy package directories, versions and adjacent wheel libraries; Node/platform versions; and the environment, including density inputs. It does not recursively scan unrelated Python search paths or unrelated site packages. Source and tool fingerprints are checked again at the end of certificate-based checks. Missing or corrupt certificates regenerate. Failed or interrupted runs do not publish a certificate. Certificates store no generated artwork and cannot restore files over a checkout.

Dangling tool symlinks contribute their target string and missing-target state to the fingerprint; creating the target invalidates it. If permissions or probing prevent a complete initial tool fingerprint, the check reports that the cache is unavailable and performs full cold regeneration without reading or publishing a certificate. Actual regeneration failures still fail. The regression fixtures include an unrelated fake sys.path directory with a dangling lldb link, a dangling link inside an imported package, package/native-library mutations and a forced unreadable-tool fallback. This corrects review 6326993286; earlier timings below remain historical until the refreshed source is measured.

The key is deliberately conservative: any tracked source, output, configuration or documentation change invalidates every generator. It avoids guessing which shared art input a generator might read. Only identical checks receive the warm shortcut; this is not a per-region incremental builder. The fingerprint scanner reuses one read buffer for installed tool files.

```sh
npm run check:art-repro -- --cold
npm run check:art-repro -- --serial
ART_REPRO_JOBS=1 npm run check:art-repro -- --cold
VERIFY_JOBS=1 npm run verify
```

`--serial` is the original ordered regeneration guard in one disposable copy. `--cold` runs every isolated group without reading or publishing a certificate, avoiding installed-tool scanning. A normal cache miss scans tools before and after regeneration to seed a reusable certificate. Cache files are local and are not committed or restored by CI. With `CI=true`, the CLI always takes the full cold path, so fresh CI checkouts do not pay certificate overhead. `ART_REPRO_JOBS` and `VERIFY_JOBS` accept 1–32; neither changes the check list or production app.

## Current-main integration

Main subsequently added `world_routes.py`, `lib/world-routes.ts`, `check:world-routes` and `check:region-plans`. All are preserved. The scheduler derives singleton groups from the canonical generator manifest, with explicit garden→zones and journey→rocket pairs, so another appended generator cannot disappear from a separate hard-coded schedule. Route-output drift and failed-route-generator fixtures are included. The versioned measurements below precede this upstream addition; exact integrated-head validation is recorded on the linked PR checkpoint.

## Measured reference

The table records the first fully validated implementation checkpoint, [`e9e645e`](https://github.com/rempemat-eng/appify/commit/e9e645e87ed10f17625c3f5a81eae0a5db149bc8), against main [`f88298f`](https://github.com/rempemat-eng/appify/commit/f88298fab4123f9a801151f58530f5b1619ec383). A subsequent change reuses the tool-hash read buffer and adds fresh-input/source-change fixtures. Exact final heads, updated measurements and CI outcomes are maintained in the [PR checkpoint](https://github.com/rempemat-eng/appify/pull/185#issuecomment-6314882656).

| Command / condition                                                                    | Baseline (s) | Measured checkpoint (s) |
| -------------------------------------------------------------------------------------- | -----------: | ----------------------: |
| Full art regeneration; no certificate or generator caches                              |      285.618 |                 277.796 |
| Full verify, including web/iOS exports; warm build caches                              |      217.523 |                 190.349 |
| Local art certificate population; full regeneration plus tool scans                    |            — |                 327.158 |
| Repeated identical art check; valid certificate, formatting and sprites still executed |            — |                  48.575 |

Cold art is only slightly faster in this sample: the garden/world-canvas group dominates. Warm verification took about 12% less wall time in this pair, despite including the new orchestration/cache fixtures. The warm art check took about 83% less time than baseline full regeneration. The initial certificate costs more than cold regeneration; reuse is worthwhile only when inputs stay identical. No cold-CI cache benefit is claimed.

An initial baseline verify with colder build caches took 362.237 seconds. It is excluded from the headline comparison because the changed build reused Metro caches. The serial control was repeated with warm builds. These are single wall-clock observations on a shared host, not statistical estimates or guarantees; a short fixture check finished near the start of the serial control. Reproduce with several pairs for tighter estimates. No repository assets, generated data or art-generator inputs changed between the compared versions.

## Reproduce

Both versions used Node 24.19.0, Python 3.12.14, Pillow 12.3.0, NumPy 2.3.5 and the same installed Node dependencies. Each measured command inherited CPU affinity restricted to exactly CPUs 0 and 1. The host quota permits more CPUs, so affinity, rather than the host core count, imposed the two-CPU limit. Benchmark commands ran sequentially with the same environment. Art snapshots exclude generator caches. Warm-build verification ran after both exports had already succeeded; web/iOS exports stay ordered because they share Expo/Metro state.

From each checkout, for example:

```sh
taskset -c 0,1 env TZ=UTC PYTHONDONTWRITEBYTECODE=1 \
  WORLD_AUDIT_NO_IMAGES=1 NPM_CONFIG_UPDATE_NOTIFIER=false \
  python3 -c 'import os,subprocess,time; assert len(os.sched_getaffinity(0)) == 2; t=time.monotonic(); r=subprocess.run(["npm","run","verify"]); print("seconds",time.monotonic()-t); raise SystemExit(r.returncode)'
```

Use the same wrapper with `npm run check:art-repro -- --cold` for cold regeneration, then two ordinary `npm run check:art-repro` invocations for certificate population and warm reuse. Keep the environment and tracked source unchanged between the latter two. CI uses NumPy 2.5.3; the local timing environment above uses 2.3.5. Matching hosted results at the final PR head are recorded on the PR.

## Regression coverage and limits

- The original 2,913 guard assertions are retained and extended for newly integrated generators: checkout/index isolation, current unstaged tracked bytes, inherited Git context, output drift/deletions/additions, generator/formatter/sprite failures and cleanup.
- Real subprocess fixtures compare ordered-cold, parallel-cold and warm byte/mode digests; require every generator exactly once; exercise fresh garden data reaching zones; reject source changes during checks; invalidate on source/configuration/tool/density changes; and verify corrupt-certificate fallback and equivalent failure detection.
- Installed-tool traversal fixtures change imported Python packages and their wheel libraries, the standard library, formatter binaries, npm/Git bytes and executable modes. Unrelated package changes leave the fingerprint unchanged. They exercise the production traversal rather than merely changing a claimed version label.
- Runner fixtures verify bounded concurrency, the entire canonical command list, spawn failures/timeouts/output limits, later checks after failure, and ordered exports after successful checks only.

Both full regeneration guards reproduced the unchanged committed artwork without drift. Isolated groups never combine changed artwork into the caller's checkout. No rules, rewards, saves, art-generator source, generated files, renderer, dependencies, lockfile or asset/audit gate policy changes. These are command/source checks, not browser gameplay, native frame timing, process-memory, phone-runtime or visual-quality measurements.
