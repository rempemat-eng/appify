# Physics in the Godot game

How bodies collide, where solids come from, what is drawn in front of what and what a shot meets, in the three playable zones (woodland, Crossroads, the Undercroft). Written 10 Nov 2026 from the code and from play. `game/test/test_physics_model.gd` holds every rule below that a machine can check. Units are texels (Godot units); one world px is 3 texels.

## Layers

| Bit | Value | Name | On it |
| --- | --- | --- | --- |
| 1 | 1 | walls | every solid: terrain, zone edges, buildings, props, the posts of people and signs |
| 2 | 2 | player | the player's body |
| 3 | 4 | enemy | enemies and the boss, while alive |
| 4 | 8 | interact | talk and read areas |
| 5 | 16 | low | set together with bit 1 (value 17): a solid that stops feet and that a shot flies over |

Bits 1 to 4 are named in `game/project.godot`. Bit 5 is not named there yet (the file is shared; the name is a label only).

## Who is on what

| Kind | Node | Layer | Mask | Shape | Set in |
| --- | --- | --- | --- | --- | --- |
| Player | CharacterBody2D, floating | 2 | 1 | circle r 9 at (0, -4) | `actors/player.tscn` |
| Player's melee hit box | Area2D | 0 | 4 | circle r 22, on only during a swing | `actors/player.tscn` |
| Mossling | CharacterBody2D | 4 | 1 | circle r 10 at (0, -8) | `actors/enemy.tscn` |
| Camp creature | CharacterBody2D | 4 | 1 | circle r 12 | `enemies/slice_enemy.gd` |
| Thornback | CharacterBody2D | 4 | 1 | circle at (0, -18) | `bosses/thornback.gd` |
| A dead enemy | | 0 | | | set to 0 on death, so nothing meets it |
| Solid | StaticBody2D | 1 | 0 | rectangles (a post: circle r 5) | the zone generators |
| Low solid | StaticBody2D | 17 | 0 | rectangles | the zone generators |
| Talk or read area | Area2D (`Interactable`, `RestoreSite`, `SealLever`) | 8 | 2 | circle r 30 | `world/interactable.gd` |
| Door | Area2D (`Door`) | 0 | 2 | rectangle | `world/door.gd` |
| Pressure plate | Area2D (`PressurePlate`) | 0 | 2 | rectangle | `world/pressure_plate.gd` |
| Arrow | Area2D (`Arrow`) | 0 | 1 and 4 | circle r 4 | `actors/arrow.gd` |
| Thorn (boss) | Area2D | 0 | 1 and 2 | circle r 9 | `bosses/thorn.gd` |
| Camp creature's shot | a ray each step | | 1 and 2 | | `enemies/projectile.gd` |

Nothing collides with the interact layer; it exists so a talk area is findable. Actors do not collide with each other: the player and enemies only mask walls. Enemies find the player through the group `player`, damage is dealt by distance checks in their own scripts.

## Where solids come from

A solid is never drawn by hand in a scene. Each zone's generator writes them, and `game/tools/gen_physics.py` holds what the generators share.

| Zone | Generator | Terrain | Objects |
| --- | --- | --- | --- |
| woodland | `gen_zone.py` writes `woodland_base.tscn` | `walk.txt`: 12 texel cells, `#` blocked, merged into rectangles (`Base/Walls/c<i>`). `low.txt` marks the blocked cells that are water (`Base/LowWalls/l<i>`). Four edge walls stand outside the picture (`edge_n`, `edge_s`, `edge_w`, `edge_e`). | one rectangle per object (`s_<id>`) from the kit library: `game/kit/pieces/prop/woodland_<kind>.json`, `geometry.collision`, world px from the foot |
| Crossroads | `gen_village.py` writes `crossroads.tscn` | the plan's box edges, `faces` and building rectangles (`Walls/Edge*`, `Face_*`, `Building_*`) | the plan's box (`kit.json` `solid`), except where the kit library holds a box reviewed against the art or the object is an approved woodland picture: then the library's box stands |
| Undercroft | `gen_undercroft.py` writes `undercroft.tscn` | the plan's box edges and wall blocks (`Walls/Edge*`, `Wall_*`) | the plan's box (`kit.json` `solid`) |

A solid inside a `Conditional` (the choked well, the dark lantern, the sealed slab) comes and goes with its picture, because a hidden Conditional disables its children.

Two rules hold for every object solid:

1. **It fits what is drawn.** Its width is the drawn base: for a tree the trunk above the root flare, for anything else the texels drawn in the rows the solid covers. More than 8 texels wider or narrower is a fault. Until 10 Nov the woodland's mask blocked each picture's whole width at its feet (180 texels under the willow's 30 texel trunk).
2. **The same picture has the same solid everywhere.** The kit library is the one place a picture's box is written, so the playable zones and the kit zones cannot disagree.

`walk.txt` is the terrain only: the ground nobody can stand on (water, cliff faces, the rock bank). Objects are not in it. The review tools (`scripts/review/scene.py`) read the same file as their walk mask.

Zones built by the world editor (`kitlab`, `woodland_kit`) derive one walls body from the same piece boxes in `world/terrain/walk.gd`. They do not know low solids yet.

## Low solids

A solid is low when its picture stands less than 64 texels above its foot (`gen_physics.LOW_RISE`: the shoulder of a 74 texel person). A piece can say so itself (`geometry.height_px`, or `gameplay.blocks_shots` false), and terrain is low where `low.txt` says so. Low today: the woodland's stream and pool, stumps, the bench, logs, brambles, bushes and the two short standing stones (the broken one and the low ones); Crossroads' benches, tubs, barrels, sacks, woodpiles, troughs, rubble, the boulder and bushes; the Undercroft's rubble, roots, urn and pulled lever. Never low: walls, wall faces, buildings, zone edges, trunks, hollies, the tall standing stones, the broken pillars, the sealed slab (`test_what_must_stop_a_shot_is_never_low`).

Why: an arrow leaves the bow 21 to 70 texels above the ground and is drawn that high, so over a bench or a stream it is seen flying on. Stopped there it vanished in mid air. Measured on the woodland camp, 12 % of the lines from a standing point within range to a mossling cross only low solids.

## Arrows and other shots

- The arrow's node is on the ground under the drawn arrow. It stops at a solid or an enemy and ignores a low solid (`Arrow.is_low`).
- It starts at the bow's tip. If a solid that stops shots lies between the archer's feet and the tip, it starts at the feet instead, so a wall the archer leans on is never skipped (the sealed slab). The way is tested as wide as the arrow (`Arrow.walled_off`: three lines and the body's place at the tip), so an arrow never starts touching a corner.
- The archer is handed to `setup`, or else is the body in the group `player` among the arrow's own siblings nearest the tip. `player.gd` adds the arrow to its own parent, so that is the shooter.
- Enemy shots (`enemies/projectile.gd`, `bosses/thorn.gd`) and the camp shooter's line of sight still stop at low solids. Those files were reserved when this was written; the change is one `Arrow.is_low(collider)` test in each.

## Draw order

Everything in a zone is one y-sort: the zone root, the base, `Objects` or `Props`, `Actors`, each `Camp` and each `Conditional` are y-sorted, so their children sort together by y. A node sorts by the y of its nearest ancestor that sits in a y-sorted parent (a villager by its talk area, a tree by itself).

| z | What |
| --- | --- |
| -10 | the ground picture |
| -9 | moving water, floor plates, cast shadows that come and go |
| -8 | wall torches (the Undercroft), flat things nobody is blocked by: beds, debris (Crossroads) |
| -1 | the woodland's hatch |
| 0 | everything y-sorted: scenery, people, enemies, the player |
| 1 | chimney smoke, an enemy's tells |
| 50 | the faint copy of a hidden actor (below) |

A y-sorted picture's origin is on its drawn feet, its lowest opaque row, within 2 texels (`test_every_sorted_picture_sorts_by_its_drawn_feet`). The generators move the origin there and keep every texel in place (`gen_physics.on_feet`). A thing that lies flat and blocks nobody is not y-sorted at all: sorted by its far edge it would cover whoever walks over it.

## Actors behind tall things

`world/occlusion.gd`, added to every zone by `world/zone.gd`. It builds art-style.md rule 11 ("The companion stays readable") as the app does: when one picture drawn in front hides at least 40 % of an actor's body, a copy of the actor at 42 % opacity is drawn over the scenery.

- Who: the player and enemies (the groups `player` and `enemy`). Villagers and signs stand still, so a hidden one is a placement fault to fix in the scene, not to paper over.
- What hides: a scenery `Sprite2D` at z 0 or above that is drawn after the actor. The share is measured on the picture's alpha at 5 x 10 points over the opaque box of the actor's drawing; the most that any one picture covers counts. A low fence across the feet never reaches 40 %.
- Cost: an actor is measured when it has moved a texel, or every 0.25 s, against the pictures registered in its 192 texel grid cell. A picture's alpha is read once, the first time something stands behind it.
- Motion: it fades in over 0.18 s and out over 0.12 s; under reduced motion both happen at once. It stops with the tree when the game is paused, and its nodes go with the zone.

## Checks

| Check | Holds |
| --- | --- |
| `game/test/test_physics_model.gd` | layers and masks of every body and area in the three zones; no way off a zone; woodland solids no wider than what is drawn; Crossroads' reviewed boxes; y-sort origins on drawn feet; flat things under people |
| `game/test/test_occlusion.gd` | the 40 % rule and its branches, the fade, reduced motion, the terrace road and the willow |
| `game/test/test_arrow_physics.gd`, `test_arrow_walls.gd` | the start check, low solids, the archer |

After changing a plan, a piece's box or a walk mask, regenerate and run `npm run check:godot`:

```sh
python3 game/tools/gen_zone.py woodland
python3 game/tools/gen_village.py crossroads --no-render
python3 game/tools/gen_undercroft.py --no-render
python3 -m scripts.art.kit.props        # after a piece's box changed, then scripts.art.kit.bake for the kit zones that use it
```
