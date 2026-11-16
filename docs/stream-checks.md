# Stream checks: the inner loop, the final head and the pre-audit list

A stream builds on a draft PR, an independent auditor reviews it, and the final head passes the whole chain before it is marked ready (`AGENTS.md`, "Verify the exact result"). This page is about the time in between: which checks a change needs while it is still being worked on, how a check survives a restarted container, and what a stream looks at itself before it asks for an audit. Nothing here replaces or shortens a check. The final head still passes `npm run verify`, `npm run check:art-repro`, `npm run check:godot` and, when `game/` changed, every route, and hosted CI still runs everything on the ready PR.

## One command

```sh
export GODOT=/path/to/Godot_v4.7.2-stable_linux.x86_64   # docs/godot.md
export STREAM_LOCK=/tmp/claude-0/heavy.lock              # where heavy work is serial; leave unset elsewhere

npm run stream:checks                # the inner loop: what this diff needs
npm run stream:checks -- --final     # the whole chain, for the head that is marked ready
npm run stream:checks -- --plan      # only say what would run
npm run stream:checks -- --stop      # end this worktree's running chain and only what it started
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

A failed step's log is kept: before the result is written, `<step>.log` and a route's output folder (its `log.txt` and `fail.png`) are moved to `<step>.fail-<n>.log` and `<step>.fail-<n>/` beside it, the record points at them, and the `FAIL` and `EARLIER` lines print both paths. A rerun writes a new `<step>.log` and loses nothing. A pass keeps the plain name. If a move fails, the record keeps the original path. Every run ends with a `kept failures` line giving the number of kept logs and route folders and their size, so a cache that grows is visible; delete old `<tree>/` folders by hand.

Run one chain per worktree at a time. Two chains in one worktree share its results file, its logs and its `runner.pid`.

After a restarted container, run the same command again: at most the step that was running is lost. In a handoff, quote the summary lines as they are, with the mode, the `Left to --final` line, any `EARLIER` lines and `reused, finished <time>` where it says so: a reused line is the same finished invocation on the same tree, not a new run.

## Stopping a run

`npm run stream:checks -- --stop` ends the chain that this worktree's runner recorded in `.cache/stream-checks/runner.pid` and the processes it started (the step, its lock wait, its Godot and its Xvfb), and nothing else. The runner records its pid, that pid's start time (field 22 of `/proc/<pid>/stat`) and its working directory. Before it sends anything, `--stop` checks that the pid still has that start time, is a `node`, and that its script argument, resolved against its own working directory, is this worktree's `scripts/stream-checks.cjs` (npm starts it with a relative path). A pid the system has since given to another process, an editor with the script open and another worktree's runner are left alone; a record that fails the check is reported as stale and removed. It sends SIGTERM to the chain's processes (children first, the runner last), waits up to 10 s, names any that are still running, sends SIGKILL only to those, and then lists which exited and which did not. It reads `/proc`, so it works on Linux only. The stopped step has no result, or a FAIL, and runs again on the next start. Never stop a run with `pkill`, `killall` or a `pgrep` pattern: on a shared machine the same names belong to other streams (lessons, rule 1).

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

Every item below is something an auditor found on #482, #483, #498 or #499 that the stream could have found first. Each round costs hours; these cost minutes.

1. **Play a new or changed route three times.** `npm run playtest:repeat -- <route>`. "It passed" means three of three on this head. #483's route passed once for the stream and failed two of three for the auditor.
2. **Say what the pilot hides.** `fight`, `defend` and `down` play well and arrive when they arrive. For each one a route uses, add one plain passage without it (`goto`, `aim`, `click`, `wait`) and an `expect` on the state at the moment the beat depends on, not only on the outcome (#483: `expect defences 2` at the first battering showed that the first hurdle fell before anyone could reach it).
3. **Play the ways to fail.** Lose once, go down once, quit and come back in the middle, walk away, walk round the thing you built. Each needs a route of a few lines; keep the ones that found something.
4. **Open your own pictures.** Look at every `shot` of the route at 3x before you cite it. The hurdle in an open square was in the stream's own `03_first_wave.png`.
5. **Read test for art.** At 1x, on its real ground, beside Bramble: what does it read as at a glance? Name it in the PR. The silhouette alone must say what the object is, in the material's own palette ramp (lessons, rule 4).
6. **Things that block or lead get a test.** A barrier: no creature-sized free cell beside it. A lane or path: no point inside a solid, and a whole body fits along it. Reach is measured from where the thing stands, not from its talk area.
7. **List every flag and state you added:** who sets it, who clears it, what a load, a quit in the middle and a second visit do to it, and which test or route line shows each. Put the table in the PR body.
8. **Words match the screen.** Each card, tracker line and prompt against the picture taken while it shows, in every layout the player can make (empty pads, lost night, after a win).
9. **Numbers come from a log.** A count in a comment, a doc or the PR body ("6 of 6", "never", "always") names the log it came from; say "in most runs" when that is what the log says. Name every run that failed or ended without a result, even one you think was the machine.
10. **Claims come from measurements.** Each claim in a commit or the PR body about pixels, numbers or behaviour names the measurement or log it came from. Describe what you measured, not what you meant to make (lessons, rule 3).
11. **Protected paths.** `npm run stream:checks -- --plan` is quick, and the chain's first step fails when the diff touches `.github/`, `game/world/loop_fx.gd`, `game/world/door.gd`, `game/export_presets.cfg` or `game/actors/player.gd` (`--allow=<path>` when your brief gives you one of them).
12. **Hand over the results, not a claim.** Give the auditor the summary lines of `npm run stream:checks -- --final` for the pushed head (or of the inner loop, quoted with its mode and its `Left to --final` line, when the final chain has not run yet) and the path of `.cache/stream-checks/`. The results file is a plain file that anyone can edit. It is a guide for the auditor: it tells them what the stream says passed, so they can decide what to spend the lock on (new routes, the ways to fail, the pictures, and a sample of the stream's claims). It is not the auditor's own run, and an auditor does not cite it as one.

## Lessons from 13 to 16 Nov

Each rule comes from a PR where a stream lost a round or broke another stream's work.

1. **Stop only your own processes.** Never kill by a broad name match (`pkill node`, `pkill -f playtest`). Use `npm run stream:checks -- --stop`. Otherwise stop only processes from a pid file of your own, or whose script path or working directory is exactly your worktree (match `<path>/` including the slash: `/x/wt` is a prefix of `/x/wt2`). (#491: a broad match killed another stream's runner.)
2. **A failed step's log is evidence.** Keep it before any rerun. The runner now moves it to `<step>.fail-<n>.log` itself (above); a log you write by hand needs the same. (#492: a Frostline route failure could not be diagnosed after its rerun.)
3. **Describe only what you measured.** A commit or PR claim about pixels, numbers or behaviour comes from a measurement or a log. (#499: the independent art audit of #499 found three claims in one commit that the pixels did not bear out.)
4. **Read test before handing art over.** At 1x, on its real ground, beside Bramble, ask "what does this read as at a glance?" and name it. First drafts read as an upright crate (#498 cart), a stone ball and then snow (#499 dome, drawn with the snow ramp for lead) and a T or a cross (#499 vane). Use the material's own palette ramp (lead is not snow), and check that the silhouette alone says what the object is. (#498, #499: found by their independent art audits.)
5. **Brief and PR state the read, not only the mechanism.** Say what the player should see. Hale's walk-off (#495) took four rounds because each fix met the geometry but not the read. Feet distance is not body overlap. A test starts from the state play actually produces (Hale turned to talk, not her rest pose).
6. **Runtime art still faces the gate.** Plan an art PR in the gate's order: PNGs and pending records, then verdicts, then the scene write, then `--final`. Never bypass or switch off the gate, even in a one-off script. (#498, #499)
7. **Audit every picture the change touches.** When an art PR changes a picture another object already uses (a baked shadow moved out of `ground.png`, an existing prop hidden), those pictures are in the audit from the start. (#498)
8. **Check file overlap before starting.** Two open PRs on the same file (`play_driver.gd`, `docs/godot.md`, `pause_menu.gd`) cost a merge and a full rerun each. Compare `git diff --name-only` of the open PRs with your plan before you start, and sequence the streams or merge main in early. (#492, #494)
9. **Carry main's workflows before landing.** A PR branch must contain main's current `.github/` changes, or the hosted run uses the old ones. Merge main, while the PR is still a draft, when `.github/` changed since the branch's base. (#496 hit the old 30-minute playtest limit.)
10. **Review every scene after a new zone.** Run `npm run review:scene` on main as a health check after any zone is added. (#500: `brackens_lab` broke the scene review, unnoticed, for every zone for days.)
11. **`detail.bar` on a thin or partly covered sprite is a lead.** The auditor measures it by hand (for example, the coverage of the patches it averages); by itself it is neither a pass nor a fault. A coverage-normalised measure is proposed as Codex task Z3 and needs Claude A's yes before it changes the gate. (#498, #499)
