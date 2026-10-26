# The game in Godot

The action RPG and village life sim (`docs/vision/game-design.md`) is built in Godot 4.7.2, in the top-level `game/` folder. The Expo app stays as it is for now; world, quest and combat work moves here. Decisions behind it (Matt, 21 to 25 Oct): desktop first, landscape only, a 960 x 540 art grid (density 3, so 320 x 180 world px) shown at exactly 2x on 1920 x 1080 and 4x on 4K, HiDPI on; LimboAI, Phantom Camera and GdUnit4 adopted; maps from the Python art kit (or Tiled with YATI later).

## Commands

Everything runs headless; no editor is needed.

```sh
export GODOT=$(bash game/tools/get_godot.sh)      # pinned 4.7.2, SHA-512 checked, self-contained mode
npm run check:godot                               # import, run the main scene 300 frames, GdUnit4 tests
$GODOT --headless --path game --import            # re-import after adding or changing art
$GODOT --path game -- --fresh --zone=woodland --spawn=stones   # play (needs a display)
```

`check:godot` (`game/tools/check.sh`) fails on any `SCRIPT ERROR` or engine `ERROR:` line, not only on the exit code, and keeps user data and editor settings in a temporary folder. It is not part of `npm run verify` (that needs no Godot); the `Godot` GitHub Actions job (`.github/workflows/godot.yml`) runs it on ready PRs and on `main` when `game/` changes. Draft PRs run no CI, so run it locally before marking a PR ready.

Game options, after `--`: `--fresh` ignores the save, `--zone=<id>` and `--spawn=<name>` choose where to start, `--shot=<png>` waits 2 s (`--wait=<s>` to change), saves the whole window 1:1 and quits; `--demo` walks the player right, down, left and up with a bow shot after each (`--quit` to end after it). For a video that keeps real time on a slow machine, use the movie maker: `DISPLAY=:96 $GODOT --path game --audio-driver Dummy --resolution 1920x1080 --write-movie out.avi --fixed-fps 30 -- --fresh --demo --quit`.

**Screenshot recipe** (the container has no display):

```sh
Xvfb :96 -screen 0 1920x1080x24 &                 # start it yourself, once
DISPLAY=:96 $GODOT --path game --audio-driver Dummy --resolution 1920x1080 --position 0,0 \
  -- --fresh --spawn=stones --shot=/path/to/woodland_1080.png
```

Use `--resolution 3840x2160` (on a matching Xvfb screen) for 4x, and an odd size such as `1600x900` to see the sharp-bilinear fallback.

## Traps (from the evaluation slice)

- **A `SCRIPT ERROR` does not stop a run.** Godot logs it and carries on, and still exits 0. Always scan the log (check.sh does). `--quit-after <frames>` ends a run; `get_tree().quit()` from a script is the other way out.
- **No `-d` for headless test runs.** With the debugger on, a parse error drops into Godot's interactive `debug>` prompt and the run hangs; `--remote-debug` to a closed port now logs errors of its own. check.sh runs GdUnit4 without either.
- **Godot writes to `~/.config/godot` and `~/.local/share/godot`** whenever it runs. Use self-contained mode (an empty `_sc_` file beside the binary; `get_godot.sh` adds it) or point `XDG_CONFIG_HOME` and `XDG_DATA_HOME` somewhere disposable, as check.sh does. The game's own `user://` is `~/.local/share/napattack` (`config/custom_user_dir_name`).
- **Node paths into an instanced scene** (`NodePath` exports such as a camera's follow target) only resolve when the instance has editable children, and break silently when the inner scene changes. Bind them in code (`pcam.follow_target = player` in `game.gd`) or use groups (`get_first_node_in_group("player")`).
- **Headless frames are unthrottled.** In tests, wait on `get_tree().physics_frame`, not process frames, before checking anything physics does (areas, movement, timers on physics).
- **Hand-written `.tscn` files** are fine (the generator writes them) but use `format=3` and string ids; the editor adds `uid=` on save. Commit the `.uid` and `.import` files Godot creates; never commit `game/.godot/`.
- **A missing autoload is a compile error** in scripts run with `-s` (they compile before autoloads exist): reach autoloads through the tree, or run a scene.

## Folder layout

```
game/
  project.godot          960 x 540, Compatibility renderer, nearest filtering, 2D pixel snapping, HiDPI on
  main.tscn              Main (main/pixel_screen.gd) > Screen (SubViewportContainer) > World (SubViewport) > Game
  main/                  pixel_screen.gd (scale rule) and sharp_bilinear.gdshader (the non-integer fallback)
  game.tscn, game.gd     ZoneRoot, the Camera2D with PhantomCameraHost, the PhantomCamera2D, the UI layer
  core/                  autoloads: inputs.gd (Inputs), save_game.gd (SaveGame), quests.gd (Quests),
                         dialogue.gd (Dialogue), zones.gd (Zones), village.gd (Village)
  actors/                player.gd/.tscn, enemy.gd/.tscn (LimboAI state machine)
  world/                 zone.gd, door.gd, interactable.gd, restore_site.gd, conditional.gd, camp.gd, flow_anim.gd
  ui/                    hud.gd, dialogue_box.gd
  data/                  zones.json, quests/*.json, dialogue/*.json, plans/*.json (zone plans: Crossroads, the Undercroft)
  zones/<id>/            art/*.png, kit.json, walk.txt, <id>_base.tscn (generated), <id>.tscn (authored)
  art/placeholder/       player, mossling and sign stand-ins (tools/gen_placeholders.py)
  test/                  GdUnit4 suites and fixtures
  tools/                 gen_zone.py, gen_blockout.py, gen_village.py, gen_placeholders.py, check.sh, get_godot.sh, fetch_limboai_release.sh
  addons/                vendored plugins (below)
```

**The screen.** The world renders into a 960 x 540 SubViewport. `pixel_screen.gd` scales it to the largest size that fits with the aspect kept: a whole number shows with plain nearest filtering (2x at 1080p, 4x at 4K), anything else with the sharp-bilinear shader, so odd windows fill instead of showing wide black bars. The save's `settings.pixel_scale = "whole"` forces whole scales with bars. Project stretch is off because this node does the scaling. The HUD and dialogue box draw inside the art grid for now.

**Units.** One world px is 3 texels. Gameplay constants are written in world px times `DENSITY` (`50.0 * DENSITY`), so they read like the design doc.

## Plugins (vendored, pinned)

| Plugin | Version | Source | Licence | In repo |
| --- | --- | --- | --- | --- |
| LimboAI (GDExtension) | v1.8.1, build for Godot 4.6+ | `limbonaut/limboai` release `limboai+v1.8.1.gdextension-4.6.zip`, SHA-256 `0910411f…5f0e` | MIT (`addons/limboai/LICENSE.md`) | 24 MB |
| Phantom Camera | 0.11.0.3 | `ramokz/phantom-camera` | MIT | 1.3 MB |
| GdUnit4 | 6.2.2 | `godot-gdunit-labs/gdUnit4` (no bundled self-tests) | MIT | 3.0 MB |

Phantom Camera's updater is off (`phantom_camera/updater/updater_mode=0` in `project.godot`, the addon's own setting). Left on, its editor plugin asks GitHub for releases whenever the project is imported, and a rate-limit reply raised a `SCRIPT ERROR` in `update_button.gd` that failed `check:godot` at random. Update the addon by hand when needed.

LimboAI is trimmed to the platforms we ship: the editor (debug) libraries for Linux x86_64, Windows x86_64 and macOS (universal), and the web build without threads (debug and release). Android, iOS, Linux arm64, 32-bit Windows and threaded web builds are left out (over 50 MB). The desktop release libraries (about 12 MB) are only needed for release exports: `bash game/tools/fetch_limboai_release.sh` fetches the pinned zip, checks it and copies them in (git-ignored). `addons/limboai/bin/limboai.gdextension` lists exactly these.

Dialogic 2 was evaluated and **not adopted yet**: it adds 11 MB and its own input action, its default binds Space and left click (our roll and attack), and the sample quest needs only a speaker, lines and a quest-state condition. `core/dialogue.gd` plus `ui/dialogue_box.gd` do that in about 150 lines. Revisit when branching conversations, portraits or voiced lines arrive.

## Systems

- **Input** (`core/inputs.gd`): the 11.5 map in code. WASD or arrows and the left stick move; the mouse or right stick aims; left click or X attacks; right click or right trigger is ranged (bound, not built); Space or A rolls; Q or right bumper special; F or left trigger familiar; R or left bumper tonic; E or Y interact; Esc or Start pauses; M map; Tab gear. Dialogue advances on E, Enter, A or Y, never Space or click.
- **Player** (`actors/player.gd`): run 50 world px/s; a 0.42 s roll invulnerable for its first 0.26 s, two charges each back after 1.2 s; a three-swing combo with a heavier finisher; hit-stop of 4, 4 and 7 frames (halved under reduced motion); mercy frames after a hit; no naps at 0 HP (the player gets up at the zone's start). The body is Bramble from the redrawn cast (below): facing from movement or aim, clips by state (idle, walk, the bow shot on left click, dodge for the roll, hit, defeat before getting up), walking at the manifest's `walk_speed`. The melee combo stays in code for the billhook but is not bound.
- **Enemy** (`actors/enemy.gd`): the evaluation's LimboAI state machine (idle, chase, a 0.5 s telegraphed wind-up, lunge, recover, leash home), now dying at 0 HP and reporting to its camp.
- **Camera** (`game.gd`): a PhantomCamera2D following the player with damping, pixel snapping, the zone's bounds as limits, aim look-ahead up to 48 world px past a 16 px dead zone (11.2), and a 1 world px shake on hits (off under reduced motion).
- **Save** (`core/save_game.gd`): one versioned JSON document, `user://save_0.json`, written to a temporary file and renamed. `data` holds zone, spawn, Glint, flags, quests, player and settings. When a field changes shape, bump `VERSION` and add a step to `_migrate`. The game autosaves when a quest moves and when the zone changes.
- **Zones** (`core/zones.gd`, `world/zone.gd`, `world/door.gd`): `data/zones.json` maps ids to scenes. `Zones.go_to(id, spawn)` swaps the zone, moves the one player into its `Actors` at the spawn marker and records it in the save. A door to a zone not in the table is refused with a warning (Crossroads' west road to Valley Halt waits for act 1). A door's `only_if` condition keeps it shut until it holds (the Undercroft's hatch). Entering a zone sets the flag `visited:<zone>`.
- **Quests** (`core/quests.gd`): JSON in `data/quests/`. The world reports plain events (`talk:<speaker>`, `camp:<camp>`, `enter:<zone>`); a quest starts on its `start.on` event, each step completes on its `on` event (if its `if` condition holds) or at once when its `done_if` already holds; rewards pay Glint and set flags. Conditions (`flags`, `not_flags`, `done`, `active`, `not_started`, `step`) are shared with dialogue. Quests never expire and never run on a clock (8.3).
- **Dialogue** (`core/dialogue.gd`, `ui/dialogue_box.gd`): JSON in `data/dialogue/`, per speaker a name and entries; the first entry whose condition holds is shown, then `talk:<speaker>` goes to the quests. An `Interactable` (`world/interactable.gd`) shows a "!" while a quest waits on it.
- **Village** (`core/village.gd`, `world/restore_site.gd`, `world/conditional.gd`): zone plans in `data/plans/` list `restores` (cost in Glint, optional condition) and `stages`. A `RestoreSite` ("restore here") pays and restores instantly, records the tier in `SaveGame.data.village.restored` and reports `restore:<id>`. A `Conditional` node shows and enables its children only while its condition holds, so one scene holds the broken and the restored town. Conditions also take `restored`, `not_restored` and `glint_at_least`.
- **Camps** (`world/camp.gd`): a node whose child enemies count as one fight; clearing it sets `camp_cleared:<id>` and reports `camp:<id>`; a cleared camp stays empty.

The vertical slice's chain (`docs/vision/vertical-slice.md`): *The road home*, *The cold forge*, *Under the stones* and *Home again*, through the woodland, Crossroads and the Undercroft. The Undercroft is a blockout: `python3 game/tools/gen_blockout.py` writes `zones/<id>/<id>.tscn` from `data/plans/<id>.json` (placeholder rectangles; regenerate, do not edit). **Crossroads is drawn** (25 Oct): `python3 game/tools/gen_village.py crossroads` renders its plan with the kit (`scripts/art/native/village.py` draws the buildings, their storm damage as separate overlays and the props; `town.py` paints the ground and writes `zones/crossroads/art/` and `kit.json`), then writes `crossroads.tscn` with the blockout's node names: the ground picture, `Walls` (edges, faces, footprints, solid dressing), `Props` (every building, prop and dressing piece y-sorted with the actors by its feet; a damage overlay sits in `If_<building>_damage`, shown until its restore, and the plan's conditional props keep `If_<id>`), `Actors`, `BuildingDoors`, `Spawns` (`square` for screenshots), `RaidPads` and `Doors`. The plan's `art` section holds each building's look, the walls, paving, puddles and the dressing with reasons; `--preview DIR` writes the whole zone per stage. Re-import (`$GODOT --headless --path game --import`) after regenerating, and `npm run check:kit` checks the pictures (house colours, lone pixels, staleness against the kit and plan). gen_blockout skips plans with `art`.

The sample quest, **Thorns by the stones** (`data/quests/woodland_stones.json`): read the sign by the stone circle, clear the three mosslings in the meadow east of it, read the sign again for 40 Glint.

## The cast

The characters are drawn and animated by Claude A's procedural rig outside the repo (the castwork: one pose-driven build per character, renders S, N, E and W from the same pose, 17 clips, timings fitted to Codex's studio). `python3 game/tools/import_cast.py <castwork>/out bramble` copies one character into `game/assets/characters/<id>/`: a strip per clip and facing (`sheets/<clip>_<F>.png`, 160 x 144 cells, foot pivot (80, 136)), `frames.tres` (animations `<clip>_<F>` as AtlasTexture regions) and `manifest.json` (per-drawing durations, release frames and times, anchors such as `arrow_tip` and `hand_R` in pixels from the foot pivot, `walk_speed`). It checks each frame's size and sha256 against the manifest.

`actors/cast_sprite.gd` (`CastSprite`, an AnimatedSprite2D) loads a character and keeps time from the manifest itself, so gameplay can ask which drawing is showing and where its anchors are; `CastSprite.facing_for(v, current)` picks the nearest of eight facings (S, SE, E, NE, N, NW, W, SW) with 10 degrees of hysteresis round the current one (animation contract v2, castwork CONTRACT.md); a character whose manifest has only S, N, E and W shows a diagonal as the profile on its side (`resolve_facing`, the manifest's `facing_fallback`). Bramble and Velvet are the v2 pilots (eight facings, 12-drawing walks, more drawings with anticipation and follow-through in their actions, walk speed 78.1 px/s); the other twelve stay on four facings until Matt approves. A v2 manifest also lists `idle_fidgets`: after 4 s of idle the sprite plays one (Bramble checks his bowstring, scratches his beard or counts his arrows) and returns to idle, and any other clip cancels it. The player spawns its arrow (`actors/arrow.gd`) on the primary's `release_frame`, at that drawing's `arrow_tip` (or the drawing before, once the arrow has left the bow), flying along the aim; `test/test_cast.gd` checks the facing choice (eight facings, hysteresis, the four-facing fallback), the release frame and position in all eight facings and at an off-facing angle (the arrow flies along the exact aim from the nearest facing's `arrow_tip`), the idle fidget, the walk speed, the dodge and hit clips and that defeat plays before `downed`.

All fourteen are imported (`python3 game/tools/import_cast.py <castwork>/out`, 26 MB). **Character select (debug):** keys 1 to 0 pick Bramble, Iona, Pendle, Cairn, Morel, Velvet, Tam, Mirra, Brine and Ashe, and Shift+1 to 4 pick Clack, Nix, Rook and Mote (`Player.CAST`; the label at the bottom left names the current one). Bramble keeps his wired bow shot; the others play idle, walk, primary (no projectile or effect yet), dodge, hit and defeat until the ability runner lands. `--lineup` stands the whole cast in a row, and `--cycle` turns the player into each one in turn (walk, primary, walk back), and `--character=<id>` starts as that one.

Scale: the cast is drawn at the 960 x 540 grid's own scale (Bramble 74 texels tall), and its walk speed is in texels a second (Bramble 68, the speed at which his planted foot does not slide). That is slower than the design's 50 world px (150 texels) run; a faster run needs a run cycle with a longer stride, not a faster walk.

## Village folk and village effects

Hale (the smith), Moss (the stall keeper) and Ada Fern are drawn in the cast's style in the castwork (`src/folk.py` and one module each) with four clips: idle, walk, talk (a small gesture loop) and work (Hale hammering at her anvil, Moss moving apples from her basket, Ada sweeping), and imported like the cast (`import_cast.py <castwork>/out hale moss ada`). In a zone, `world/villager.gd` (`Villager`, a CastSprite) plays a person's work loop or idle facing `facing_at_rest`, and turns to the player and talks while the player is within 40 world px; the quest triggers stay on the parent Interactable. gen_village maps plan speakers to characters (`CAST`) and reads `face` and `work` from each plan person; Hale also stands on the woodland's east path.

The lit forge's fire and the smithy chimney's smoke are looping strips (`python3 game/tools/gen_village_fx.py` writes `zones/crossroads/art/fx/`), played by `world/loop_fx.gd`: only while on screen, and held on one drawing under reduced motion. gen_village swaps the kit's static `forge_fire` for the strip (`LOOPS`) and puts the smoke on the smithy's chimney pot while the forge is restored (`SMOKE`).

Screenshot options: `--stage=<id>` puts the save in a plan stage (`--zone=crossroads --stage=homecoming`), and `--at=x,y` stands the player at a world point.

## How lanes add a region (zone)

1. Render the zone with the kit at density 3 and import it: `python3 game/tools/gen_zone.py <zone> --render <kit checkout> --walk <kit checkout>/lib/zone-maps.ts`. It runs `python3 -m scripts.art.native.zone --zone <zone> --density 3` in the kit checkout, copies the pictures to `game/zones/<zone>/art/`, keeps the kit's boxes in `kit.json` and the walk mask in `walk.txt`, and writes `<zone>_base.tscn`: ground and water below everything, the objects y-sorted with their feet as origins, the blocked walk cells as merged collision rectangles, and the named stands as markers. Without `--render`, it rebuilds the base scene from what is already in the folder.
2. Make `<zone>.tscn` by hand (copy `zones/woodland/woodland.tscn`): a `Zone` root, the base instanced as `Base`, a y-sorted `Actors` node for people, signs and camps, `Spawns` markers (one named `start`), and `Doors`. Never edit the base scene; regenerate it.
3. Add the zone to `data/zones.json` and point the neighbours' doors at it.
4. Run `npm run check:godot` and take a 1920 x 1080 screenshot with the recipe above.

The woodland came from `origin/claude-a/woodland-2x` (PR #222's kit: `scripts/art/native/zone.py` already takes `--density`; at 3 it stores pictures at 1 image px per texel instead of the app's 2x2-doubled ones, so nothing in the kit had to change). Its walk mask and stands are the 1x zone's own from that branch's `lib/zone-maps.ts`. Zones from the world canvas (256 px tiles) or from Tiled with YATI will need their own importer writing the same base-scene shape.

## How lanes add a quest

1. Write `data/quests/<id>.json` (copy `woodland_stones.json`): `start.on`, the `steps` with their `on` events and optional `if` and `done_if` conditions, `rewards` in Glint and flags.
2. Give the people in it lines in `data/dialogue/<region>.json`, most specific entry first and an unconditional one last.
3. Place what the events need: an `Interactable` with the speaker id, a `Camp` with the camp id, a door into the zone for `enter:<zone>`.
4. Add a GdUnit test that drives it with `Quests.notify` (see `test/test_quests.gd`), and run `npm run check:godot`.
