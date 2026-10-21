# Verification speed (C35/r1)

This change preserves the canonical `package.json` check list and all existing gates. `npm run verify` runs those checks in a bounded pool (two jobs by default), then exports web and iOS in order. `npm run check` and `npm run verify:serial` retain the serial path. Unsupported check-list syntax fails explicitly instead of omitting a step. Exports do not start after a failed check; all other scheduled checks finish and report their failures.

## Art reproducibility

`npm run check:art-repro` gives each generator group its own disposable tracked-source copy, Git index and preview directory. Garden and zones run in that order in the same copy because the world canvas reads garden ground and walk data. Journey and rocket also stay together. Other groups run independently, with no shared output tree. Each group compares all tracked bytes and checks for unexpected generated files. The final formatting and sprite checks always run, including on a cache hit. Generator, formatter, sprite, subprocess and snapshot failures remain failures.

A local certificate under `.cache/art-repro` permits skipping generators only after a complete successful run with identical inputs. Its SHA-256 key includes every tracked file's path, current bytes and executable mode; all installed Node tools/dependencies; npm/npx and Git executables; the Python executable, shared interpreter library and every existing Python search-path tree (including installed packages); Node/platform versions; and the effective environment, including density inputs. Source and tool fingerprints are checked again at the end. Missing/corrupt certificates regenerate. Failed or interrupted runs do not publish a certificate. Certificates store no generated artwork and cannot restore files over a checkout.

The dependency key is deliberately conservative: any tracked source, output, configuration or documentation change invalidates every generator. It avoids guessing which shared art input a generator might read. Only identical checks receive the warm shortcut; this is not a per-region incremental art builder. The complete cold path ignores certificates:

```sh
npm run check:art-repro -- --cold
npm run check:art-repro -- --serial
ART_REPRO_JOBS=1 npm run check:art-repro -- --cold
VERIFY_JOBS=1 npm run verify
```

`--serial` is the original ordered regeneration guard in one disposable copy. `--cold` runs the isolated groups without reading or publishing a certificate, so it avoids scanning installed tools. A normal cache miss performs that scan before and after regeneration to seed a reusable certificate. `ART_REPRO_JOBS` and `VERIFY_JOBS` accept 1–32; neither changes the check list or production app. Cache files are local and are not committed or restored by CI. With `CI=true`, the CLI always takes the forced cold path, avoiding certificate overhead on fresh CI checkouts.

## Evidence at the implementation checkpoint

- The original 2,913 guard assertions pass unchanged: checkout/index isolation, current unstaged tracked bytes, inherited Git context, output drift/deletions/additions, generator/formatter/sprite failures and cleanup.
- Real subprocess fixtures verify ordered-cold, parallel-cold and warm byte/mode digest equality; all entry points exactly once; complete input/tool/density invalidation; corrupt-certificate fallback; and equivalent detection of output changes, deletion, new files and process failures.
- Orchestration fixtures verify bounded concurrency, the entire canonical command list, output limits, spawn failures/timeouts, preservation of later checks after failure, and ordered exports after successful checks only.
- A preliminary full art regeneration on the pinned baseline reproduced all 12 generators. Its timing overlapped a failed verification attempt against in-progress source changes, so it is excluded from performance evidence.

Full clean baseline/changed-source runs and two-CPU timing are being collected. This checkpoint is a draft implementation, not a completed C35 handoff. It has not been marked ready, and no hosted CI or device-runtime result is claimed.

## Reproduce the timings

The baseline is main `f88298fab4123f9a801151f58530f5b1619ec383`. Both versions use Node 24.19.0, Python 3.12.14, Pillow 12.3.0, NumPy 2.3.5 and the same installed Node dependencies. Benchmarks set process affinity to exactly CPUs 0 and 1; descendants inherit that restriction. The host CPU quota permits more CPUs, so affinity, rather than the host core count, is the actual two-CPU limit. Runs are sequential, with `TZ=UTC`, `PYTHONDONTWRITEBYTECODE=1`, `WORLD_AUDIT_NO_IMAGES=1` and the npm update notifier disabled.

The local NumPy version differs from CI's pinned 2.5.3. Matching hosted verification remains required. These are command timings, not gameplay, native frame-time, device memory or visual-quality measurements. No rules, rewards, saves, art generator source, generated files, renderer or asset/audit gate policy changes.
