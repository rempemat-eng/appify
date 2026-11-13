# Stream checks: the inner loop, the final head and the pre-audit list

A stream builds on a draft PR, an independent auditor reviews it, and the final head passes the whole chain before it is marked ready (`AGENTS.md`, "Verify the exact result"). This page is about the time in between: which checks a change needs while it is still being worked on, how a check survives a restarted container, and what a stream looks at itself before it asks for an audit. Nothing here replaces or shortens a check. The final head still passes `npm run verify`, `npm run check:art-repro`, `npm run check:godot` and every route, and hosted CI still runs everything on the ready PR.

## One command

```sh
export GODOT=/path/to/Godot_v4.7.2-stable_linux.x86_64   # docs/godot.md
export STREAM_LOCK=/tmp/claude-0/heavy.lock              # where heavy work is serial; leave unset elsewhere

npm run stream:checks                # the inner loop: what this diff needs
npm run stream:checks -- --final     # the whole chain, for the head that is marked ready
npm run stream:checks -- --plan      # only say what would run
npm run playtest:repeat -- first_night            # one route three times in a row
npm run playtest:repeat -- main --repeat=5
```

`scripts/stream-checks.cjs` compares the working tree with its merge base on `origin/main` (`--base=<ref>` for another) and picks the checks from the changed paths, using the path filters of the hosted workflows in `.github/workflows/`, so the inner loop asks for what hosted CI will ask for:

| Changed                        | Inner loop                                                                                        | `--final`                                                                                        |
| ------------------------------ | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| only `docs/` and `*.md`        | nothing heavy                                                                                     | `verify`, `check:art-repro`                                                                      |
| `game/` (with or without docs) | `check:godot`, `verify:game`, each new or changed route three times                               | `check:godot`, `verify`, `check:art-repro`, every route once, new or changed routes three times  |
| anything else                  | `verify`, plus `check:art-repro`, `check:godot` and changed routes where the hosted filters match | `verify`, `check:art-repro`, and with `game/` changed also `check:godot` and the routes as above |

A filter that cannot be read counts as a match, so a gap adds a check and never drops one. `game/data/sun.json` also asks for `check:art-repro`, because the golden scenes read it.

Every step runs under `STREAM_LOCK` on its own (the lock is free between steps, and the wait is timed apart from the run). A route gets a display of its own: `playtest.sh` starts an Xvfb for it and stops it afterwards, so no shared Xvfb has to stay alive. Set `STREAM_KEEP_DISPLAY=1` to play on the `DISPLAY` you already have.

Exit code 0 means every step passed, 1 means a step failed (the chain stops there; `--keep-going` runs the rest), 3 means the `--budget=<seconds>` ran out before every step had started, 2 is a usage error or the wrong Node: the runner stops at once when its Node major is not the one hosted Verify uses, because `verify` fails on another one only after minutes.

## Results survive a restart

Each step's result is appended to `.cache/stream-checks/results.jsonl` (git-ignored) the moment the step ends: its name, the tree hash of the working files, the head, the Node major version and `GODOT`, the exit code, the seconds it ran and waited, and its log under `.cache/stream-checks/<tree>/`. On the next start, a step that already finished with exit 0 **on the same tree with the same toolchain** is listed as `reused` and not run again. A step that was cut off has no result and runs again; so does a failed one. Any edit changes the tree hash, so nothing is carried from one source to another, and an edit made while a step runs fails that step and stops the chain: do not edit the worktree while it checks. `--fresh` trusts no record.

After a restarted container, run the same command again: at most the step that was running is lost. In a handoff, quote the summary lines as they are, with `reused, finished <time>` where it says so: a reused line is the same finished invocation on the same tree, not a new run.

## `npm run verify:game`

`verify` has 42 checks and two exports. File tracing on 13 Nov 2026 showed that only `check:review`, `check:kit` and `check:quests` read anything under `game/`; the type check and lint only list its folders. `verify:game` runs the steps of `check` except nine app-only ones of 5 s or more (`APP_ONLY` in the script: the type check, lint, `check:core`, `check:world-canvas`, `check:world-walk`, `check:world`, `check:clusters`, `check:world-audit`, `check:check-speed`) and the two exports: about 5 min in place of 12 to 13 with one job. A check that is added to `check` later is part of `verify:game` until somebody traces it and lists it.

It refuses, with exit 2, any diff that changes more than `game/`, `docs/` and `*.md`, or that adds a script file under `game/`. It is for the rounds before the final head. It is not a pass of `verify`.

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
10. **Hand over the results, not a claim.** Give the auditor the summary lines of `npm run stream:checks` for the pushed head and the path of `.cache/stream-checks/`. An auditor in another worktree at the same tree can read what passed and spend the lock on what only an auditor does: new routes, the ways to fail, the pictures.
