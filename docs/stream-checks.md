# Stream checks: the inner loop, the final head and the pre-audit list

A stream builds on a draft PR, an independent auditor reviews it, and the final head passes the whole chain before it is marked ready (`AGENTS.md`, "Verify the exact result"). This page is about the time in between: which checks a change needs while it is still being worked on, how a check survives a restarted container, and what a stream looks at itself before it asks for an audit. Nothing here replaces or shortens a check. The final head still passes `npm run verify`, `npm run check:art-repro`, `npm run check:godot` and, when `game/` changed, every route, and hosted CI still runs everything on the ready PR.

## One command

```sh
export GODOT=/path/to/Godot_v4.7.2-stable_linux.x86_64   # docs/godot.md
export STREAM_LOCK=/tmp/claude-0/heavy.lock              # where heavy work is serial; leave unset elsewhere

npm run stream:checks                # the inner loop: what this diff needs
npm run stream:checks -- --final     # the whole chain, for the head that is marked ready
npm run stream:checks -- --plan      # only say what would run
npm run playtest:repeat -- first_night            # one route three times in a row
npm run playtest:repeat -- main --repeat=5
npm run playtest:repeat -- fight_by_door --fast   # a quick look in fixed step: never a counted run (below)
```

`scripts/stream-checks.cjs` compares the working tree with its merge base on `origin/main` (`--base=<ref>` for another) and picks the checks from the changed paths. It starts from the path filters of the hosted workflows in `.github/workflows/` and adds the files those filters miss, so the local choice is never looser than the hosted one. Paths are compared without rename detection: a moved file counts as its old path removed and its new path added.

**The inner loop is less than hosted CI and less than `--final`.** After a change to game code or to the play driver it plays no route unless a route file itself changed, while hosted Godot playtest plays every route; `verify:game` leaves out nine steps and the exports; `check:art-repro` runs only when an art input changed. The last lines of every run say which mode ran (`inner mode`, `routes mode`, `final mode`) and name what is left to `--final`. Only a `final mode` summary for the pushed head covers the whole chain.

| Changed                                                           | Inner loop                                                                  | `--final`                                                                                       |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| only `docs/` and `*.md`, none of the files below                  | nothing selected (the summary says so; no check ran)                        | `check:godot`, `verify`, `check:art-repro`                                                      |
| `game/` (with or without docs)                                    | `check:godot`, `verify:game`, each new or changed route three times         | `check:godot`, `verify`, `check:art-repro`, every route once, new or changed routes three times |
| `scripts/art/`, `scripts/review/`, `scripts/progression/`, `art/` | `check:godot`, `verify`, `check:art-repro`                                  | the same                                                                                        |
| anything else                                                     | `verify`, plus `check:art-repro` and changed routes where the filters match | `check:godot`, `verify`, `check:art-repro`, and with `game/` changed the routes as above        |

`--final` always runs `check:godot`, `verify` and `check:art-repro`, whatever changed, and every route when anything under `game/` changed. The additions to the hosted filters:

- **`check:godot` outside `game/`.** Its tests pin the sha256 of `scripts/art/kit/build.py`, `compose.py`, `dressing.py`, `edges.py`, `scripts/art/house_palette.py`, `scripts/art/native/palette.py`, `accents.json` and `art/house-palette.json` (`game/test/test_terrain.gd`), and run `scripts.review.kit_scene` and `scripts/progression/weapon_lines.py`. The hosted Godot filter lists none of these, so hosted CI does not run it for them: the local run is the only one before main.
- **`check:art-repro` under `docs/` and `game/`.** The generators read `docs/vision/research/blockout/` and `game/data/sun.json`, and write `docs/vision/regions/route-meets.md`, `docs/vision/cliff-core/` and `docs/vision/icon-sheet*.png`, which the check compares. A change to any of them asks for `verify` and `check:art-repro`.
- **`verify` under `docs/`.** Steps of `check` open `docs/vision/asset-ledger.md`, `prop-logic.md`, `placement-audit.md` and `docs/vision/regions/sunstone-basin-fire-country.md`. A change to one asks for the full `verify`, and `verify:game` refuses it.

These lists come from reading the generators and tests on 14 Nov 2026 (`ART_DOCS_INPUTS`, `VERIFY_DOCS_INPUTS` and `GODOT_OUTSIDE_INPUTS` in the script). A generator that starts to read another file under `docs/` needs its path added there.

A filter that cannot be read counts as a match, so a gap adds a check and never drops one.

Every step runs under `STREAM_LOCK` on its own (the lock is free between steps, and the wait is timed apart from the run). A route gets a display of its own: `playtest.sh` starts an Xvfb for it and stops it afterwards, so no shared Xvfb has to stay alive. Set `STREAM_KEEP_DISPLAY=1` to play on the `DISPLAY` you already have.

Exit code 0 means every step passed, 1 means a step failed (the chain stops there; `--keep-going` runs the rest), 3 means the `--budget=<seconds>` ran out before every step had started, 2 is a usage error or a machine that cannot give a valid result: the runner stops at once when its Node major is not the one hosted Verify uses (`verify` fails on another one only after minutes), and when the plan has an art or kit check and `python3` would write other PNG bytes than hosted CI (next section). `--repeat` takes a whole number of 1 or more; anything else is a usage error. When the diff selects no check, the summary says "nothing selected for this diff, so no check ran" in place of a count; `protected-paths` is a path comparison and is never counted as a passed check.

Hosted workflows with no local counterpart, with or without `--final`: `kit-build-check` (`python3 -m unittest scripts.art.kit.test_build_check`), `kit-concept-validation` (`scripts.art.kit.test_concept_schema`), `kit-scene-intake` (`scripts.review.test_kit_scene_intake`), the two tests at the start of `godot.yml` (`game/tools/test_get_godot.py`, `scripts/godot-import-cache.test.py`), `native-readiness` (expo-doctor and a prebuild), `screens`, and the `engineering-validation` and `editor-*-validation` workflows. None of them is part of `check`. Run the unittest ones by hand when your diff matches their path filters, and read the hosted result of each on the ready PR.

## The Python the art checks need

`check:kit` and `check:review` (inside `verify` and `verify:game`) and `check:art-repro` compare freshly written PNGs with the committed ones byte for byte. The pixels depend on Pillow, numpy and scipy; the bytes also depend on the zlib that Pillow loads. Pillow's wheel does not carry a zlib of its own: it takes the machine's `libz.so.1`. Hosted CI (Ubuntu) has the original zlib, and the committed PNGs are its output. Some sandbox images put zlib-ng first in the loader's path, and some also patch their system Pillow to write PNGs at another compression level. On such a machine identical pixels come out as other bytes, and `python3 -m scripts.art.kit.build --check` reports `stale or missing` on an unchanged `main`. That is the machine, not the change, and a PNG written there must never be committed.

The runner checks this before any plan with `verify`, `verify:game` or `check:art-repro`: it asks `python3`, and `$PYTHON` when that is set (`check:art-repro` and three Godot tests start it in place of `python3`), for the zlib Pillow reports (`PIL.features.version('zlib')`) and stops with exit 2 when there is no Pillow or the zlib is zlib-ng. It warns when Pillow, numpy or scipy differ from the versions hosted Verify pins. To get a Python that passes:

1. Make a venv with the wheels hosted CI pins (the `pip install` line in `.github/workflows/verify.yml`: Pillow, numpy and scipy with exact versions) on the Python minor it uses. Unmodified wheels from PyPI, not the image's own packages.
2. Find the distribution's original zlib (on Ubuntu and Debian `/lib/x86_64-linux-gnu/libz.so.1`; `ldconfig -p | grep libz` lists what is there, and the one to avoid has `zlib-ng` in the name it links to).
3. Put a small `python3` launcher first on `PATH` that sets `LD_PRELOAD` to that file and then starts the venv's Python. `LD_PRELOAD` is inherited by the Pythons that the checks start themselves. `LD_LIBRARY_PATH` is not enough where the Python binary has an rpath of its own.
4. Check it on an unchanged `main`: `python3 -c "from PIL import features; print(features.version('zlib'))"` prints a plain version such as `1.3`, and `python3 -m scripts.art.kit.build --check` ends with `up to date`. Only then are local art results worth anything.

The Python, Pillow, numpy, scipy and zlib versions (of `python3`, and of `$PYTHON` when set) are part of the key a result is kept under (below), so a result made with one Python is never reused with another.

## Results survive a restart

Each step's result is appended to `.cache/stream-checks/results.jsonl` (git-ignored) the moment the step ends: its name, the tree hash of the working files, the head, the toolchain (the full Node version, the Python, Pillow, numpy and scipy versions, the zlib Pillow reports and the sha256 of the Godot binary), the exit code, the seconds it ran and waited, and its log under `.cache/stream-checks/<tree>/`. On the next start, a step whose **newest** finished result **on the same tree with the same toolchain** is exit 0 is listed as `reused` and not run again. A step that was cut off has no result and runs again; so does a failed one, and a pass from before a failure is never reused: the newest result decides.

A route's runs stand or fall together. A failure of any run of a route on a tree voids every run of that route before it, so `#1`, `#2` and `#3` all play again and the three passes that count are in a row after the last failure. A route that fails one time in two cannot reach three of three by being started again. Every earlier failure of a step on the same tree stays in the output as an `EARLIER` line and in the summary count ("1 earlier failure on this tree"), however many passes follow it. Quote those lines too. Any edit changes the tree hash, so nothing is carried from one source to another, and an edit made while a step runs fails that step and stops the chain: do not edit the worktree while it checks. `--fresh` trusts no record.

After a restarted container, run the same command again: at most the step that was running is lost. In a handoff, quote the summary lines as they are, with the mode, the `Left to --final` line, any `EARLIER` lines and `reused, finished <time>` where it says so: a reused line is the same finished invocation on the same tree, not a new run.

## `npm run verify:game`

`verify` has 43 checks and two exports. File tracing on 13 Nov 2026 showed that only `check:review`, `check:kit` and `check:quests` read anything under `game/` (and since the game has sound, `check:sound-repro`, which compares `game/audio` with what `scripts/audio/game_sounds.py` writes); the type check and lint only list its folders. `verify:game` runs the steps of `check` except nine app-only ones of 5 s or more (`APP_ONLY` in the script: the type check, lint, `check:core`, `check:world-canvas`, `check:world-walk`, `check:world`, `check:clusters`, `check:world-audit`, `check:check-speed`) and the two exports: about 5 min in place of 12 to 13 with one job. A check that is added to `check` later is part of `verify:game` until somebody traces it and lists it.

It refuses, with exit 2, any diff that changes more than `game/`, `docs/` and `*.md`, or that adds a script file under `game/`. It also refuses a diff that touches one of the files under `docs/` that a check reads (the lists above). `--base=<ref>` works here as in the runner, and the runner hands its own `--base` on. It is for the rounds before the final head. It is not a pass of `verify`.

## The fast playtest (`--fast`): a quick look, never a result

`npm run playtest:repeat -- <route> --fast` plays a route once with Godot's `--fixed-fps 60 --disable-render-loop`: a fixed step and no drawing, about ten times faster than real time. It is off unless asked for, exists only for `playtest:repeat` (which itself refuses `--final`: naming routes is never the final chain), and is refused with `--final`, in the inner loop and together with `--repeat`. Its steps have ids of their own (`route-fast:<name>#1`), a cache key of their own, and `FAST` on every result line, so a fast pass is never reused or counted as a real run.

- **Fast runs are deterministic.** The same tree gives the same log every time. Three fast runs are one sample: they say nothing about flakiness, which is what the three repeats are for. That is why `--fast` plays once.
- **It can hide timing bugs.** On a loaded machine the real game gets late inputs, uneven frame times and several physics steps in one frame; in fixed step none of that happens. In the audit of #489 a fight that put the player down once in both real runs never did in fixed step, and ended in half the time. Code that waits on drawn frames or on the wall clock (effects that start when they come on screen, the dialogue box's frame guard, the hurt blink) behaves differently too.
- **No pictures.** `shot` waits for a drawn frame and fast mode draws none, so a route with a `shot` line is refused in fast mode. Making pictures work needs a change under `game/tools/`, which this tooling does not make. Never cite a picture or a result from a fast run in a PR or to an auditor. For the same reason a fast route that fails cannot take its `fail.png`: it waits for a frame that is never drawn and ends only at the time limit, which fast steps set to 180 s (in place of 900), and its last message is lost. It still ends as `FAIL`; play it without `--fast` to see why.

Use it to find out quickly whether a route's steps still line up after an edit. Then play the route for real: the three counted repeats, `--final`, hosted CI and an auditor never use it.

## Before you ask for an audit

Every item below is something an auditor found on #482 or #483 that the stream could have found first. Each round costs hours; these cost minutes.

1. **Play a new or changed route three times.** `npm run playtest:repeat -- <route>`. "It passed" means three of three on this head. #483's route passed once for the stream and failed two of three for the auditor.
2. **Say what the pilot hides.** `fight`, `defend` and `down` play well and arrive when they arrive. For each one a route uses, add one plain passage without it (`goto`, `aim`, `click`, `wait`) and an `expect` on the state at the moment the beat depends on, not only on the outcome (#483: `expect defences 2` at the first battering showed that the first hurdle fell before anyone could reach it).
3. **Play the ways to fail.** Lose once, go down once, quit and come back in the middle, walk away, walk round the thing you built. Each needs a route of a few lines; keep the ones that found something.
4. **Open your own pictures.** Look at every `shot` of the route at 3x before you cite it. The hurdle in an open square was in the stream's own `03_first_wave.png`.
5. **Things that block or lead get a test.** A barrier: no creature-sized free cell beside it. A lane or path: no point inside a solid, and a whole body fits along it. Reach is measured from where the thing stands, not from its talk area.
6. **List every flag and state you added:** who sets it, who clears it, what a load, a quit in the middle and a second visit do to it, and which test or route line shows each. Put the table in the PR body.
7. **Words match the screen.** Each card, tracker line and prompt against the picture taken while it shows, in every layout the player can make (empty pads, lost night, after a win).
8. **Numbers come from a log.** A count in a comment, a doc or the PR body ("6 of 6", "never", "always") names the log it came from; say "in most runs" when that is what the log says. Name every run that failed or ended without a result, even one you think was the machine.
9. **Protected paths.** `npm run stream:checks -- --plan` is quick, and the chain's first step fails when the diff touches `.github/`, `game/world/loop_fx.gd`, `game/world/door.gd`, `game/export_presets.cfg` or `game/actors/player.gd` (`--allow=<path>` when your brief gives you one of them).
10. **Hand over the results, not a claim.** Give the auditor the summary lines of `npm run stream:checks -- --final` for the pushed head (or of the inner loop, quoted with its mode and its `Left to --final` line, when the final chain has not run yet) and the path of `.cache/stream-checks/`. The results file is a plain file that anyone can edit. It is a guide for the auditor: it tells them what the stream says passed, so they can decide what to spend the lock on (new routes, the ways to fail, the pictures, and a sample of the stream's claims). It is not the auditor's own run, and an auditor does not cite it as one.
