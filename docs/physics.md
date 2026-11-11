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

All five are named in `game/project.godot` (`[layer_names]`); `test_world_fixes.gd` holds the names.

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
| Talk or read area | Area2D (`Interactable`, `RestoreSite`, `SealLever`, `RestSpot`) | 8 | 2 | circle r 30 (the shard lantern in Crossroads: r 22) | `world/interactable.gd` |
| Door | Area2D (`Door`) | 0 | 2 | rectangle | `world/door.gd` |
| Pressure plate | Area2D (`PressurePlate`) | 0 | 2 | rectangle: the drawn slab moved up 4 texels (where the body's centre is) and 7 in from each side, so feet anywhere on the slab press it, its corners included, and feet 3 texels or more off it do not | `world/pressure_plate.gd` |
| Arrow | Area2D (`Arrow`) | 0 | 1 and 4 | circle r 4 | `actors/arrow.gd` |
| Thorn (boss) | Area2D | 0 | 1 and 2 | circle r 9 | `bosses/thorn.gd` |
| Camp creature's shot | a ray each step | | 1 and 2 | | `enemies/projectile.gd` |

Nothing collides with the interact layer; it exists so a talk area is findable. Actors do not collide with each other: the player and enemies only mask walls. Enemies find the player through the group `player`. Damage: the mossling, the camp's rusher, shield and elite and the Thornback's charge and slam deal it by distance checks in their own scripts; the Thornback's thorn deals it when its area overlaps the player; the camp shooter's shot when its ray meets the player.

## Where solids come from

The generators write the solids, with one exception: the 5 texel posts of the stone sign and of Hale in the hand-written `woodland.tscn`. Nothing else is drawn by hand, and `game/tools/gen_physics.py` holds what the generators share.

| Zone | Generator | Terrain | Objects |
| --- | --- | --- | --- |
| woodland | `gen_zone.py` writes `woodland_base.tscn` | `walk.txt`: 12 texel cells, `#` blocked, merged into rectangles (`Base/Walls/c<i>`). `low.txt` marks the blocked cells that are water (`Base/LowWalls/l<i>`). Four edge walls stand outside the picture (`edge_n`, `edge_s`, `edge_w`, `edge_e`). | one rectangle per object (`s_<id>`) from the kit library: `game/kit/pieces/prop/woodland_<kind>.json`, `geometry.collision`, world px from the foot |
| Crossroads | `gen_village.py` writes `crossroads.tscn` | the plan's box edges, `faces` and building rectangles (`Walls/Edge*`, `Face_*`, `Building_*`) | the plan's box (`kit.json` `solid`), except where the kit library holds a box reviewed against the art or the object is an approved woodland picture: then the library's box stands. The notice board and the waystone get the texels drawn in their lowest 12 rows |
| Undercroft | `gen_undercroft.py` writes `undercroft.tscn` | the plan's box edges and wall blocks (`Walls/Edge*`, `Wall_*`) | the plan's box (`kit.json` `solid`), which is the prop's own `box` in the plan where that one was measured on the picture (the hall's roots, the two broken pillars, the seal room's rubble; `scripts/art/native/undercroft.py` writes it there). `size` stays as it is: the painter shapes the picture and its contact shadow from it |

A solid inside a `Conditional` (the choked well, the dark lantern, the sealed slab) comes and goes with its picture, because a hidden Conditional disables its children.

Two rules hold for every object solid:

1. **It is not wider than what is drawn.** A solid may not reach more than 8 texels past the texels drawn in the rows it covers, and may not be narrower than a third of them (`test_a_woodland_solid_is_no_wider_than_what_is_drawn`, every woodland object). An invisible block is the fault that rule is for: until 10 Nov the woodland's mask blocked each picture's whole width at its feet (180 texels under the willow's 30 texel trunk). Narrower is right where the drawing spreads at ground level and feet may step there: a trunk blocks its stem, not its root flare (oak 30 on a 41 texel stem and 64 of roots, stump 36 in 69), a bramble its mass and not its cane sprays (90 in 120), the handcart its bed and not its shafts (66 in 88), the choked well its ring (60 in 93). The test is the woodland's. Crossroads has pinned sizes for the boxes that changed (`test_crossroads_solids_follow_the_reviewed_boxes`); the Undercroft's four measured boxes are held by `test_the_undercroft_roots_and_pillars_block_what_is_drawn` (no more than 8 texels of bare floor inside a box, no narrower than three fifths of what is drawn in its rows, and a broken pillar's box at least 80 % of its plinth as drawn); its other rubble, roots and the urn keep the plan's box and have no fit test.
3. **No slot a body just fits.** A prop stands against its wall, nearer to it than a body (18 texels), or at least 24 texels clear (`test_no_undercroft_solid_leaves_a_body_wide_slot`, the Undercroft). Until 11 Nov the hall's roots and the seal room's rubble each left exactly 18.

Crossroads' retaining faces end on the drawn wall's foot: the garden walk's and the terrace's are one wall and share one south edge (`test_the_garden_walk_and_the_terrace_share_one_wall_foot`).
2. **The same picture has the same solid everywhere.** The kit library is the one place a picture's box is written, so the playable zones and the kit zones cannot disagree.

`walk.txt` is the terrain only: the ground nobody can stand on (water, cliff faces, the rock bank). Objects are not in it. The review tools (`scripts/review/scene.py`) read the same file as their walk mask.

Zones built by the world editor (`kitlab`, `woodland_kit`) derive one walls body from the same piece boxes in `world/terrain/walk.gd`. They do not know low solids yet. A piece scene (`game/kit/props/*.tscn`, written by `scripts/art/kit/props.py`) carries a `Solid` only when its record says `gameplay.blocks_move`, so a zone built from the scenes blocks what the walk mask blocks.

## Low solids

A solid is low when its picture stands less than 64 texels above its foot (`gen_physics.LOW_RISE`: the shoulder of a 74 texel person), and terrain is low where `low.txt` says so. A piece's own word wins over its height (`gen_physics.is_low`):

- `gameplay.blocks_shots` false: low, whatever its height.
- `gameplay.blocks_shots` true and marked as authored (`audit.overrides` has `"blocks_shots"`): never low. Solid rock at chest height stops an arrow; a bush of the same height does not. A `true` without the mark is only the seeder's default and decides nothing.
- `geometry.height_px`: the height to judge by, in place of the picture's.

Low today:

| Zone | Low |
| --- | --- |
| woodland | the stream above the fall and the pool and river below it; stumps, the bench, logs, brambles, bushes |
| Crossroads | bushes, flower tubs, woodpiles, sacks, benches, barrels, the coal heap, the trough, the boulder (45), the anvil, the knee-high rubble (square rubble a, fern rubble) |
| Undercroft | rubble, roots, the urn, the pulled lever |

Never low: walls, wall faces, buildings, zone edges, the fall's face, trunks, saplings, hollies, every standing stone (the two short kinds, 56 texels, by their records), Crossroads' chest-high stone rubble (smithy rubble 56, square rubble b 57, by their records), the wells, lanterns, crates, the broken pillars, the sealed slab. `test_what_must_stop_a_shot_is_never_low` holds this for terrain, edges, faces, buildings, posts and the slab by node name; `test_the_woodland_is_split_into_walls_and_low_walls` pins the woodland's low kinds exactly and its stones; `test_every_woodland_thing_that_stands_tall_has_a_solid` holds everything 64 texels or taller; `test_crossroads_solids_follow_the_reviewed_boxes` pins the rubble piles, a bench and the hollow oak. The other Crossroads and Undercroft props are classed by the rule and not pinned one by one.

Why: an arrow is drawn 29 to 33 texels above the ground when shot south, about 46 when shot east or west and 61 to 67 when shot north. Over water it is always seen flying on. Over a prop 47 to 61 texels tall it is drawn across the prop's upper part on south, east and west shots, which reads as passing over a low thing; stopped there it vanished in mid air. Rock is the exception by art direction: an arrow that crosses a chest-high stone looks wrong, so stone says so in its record.

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

A y-sorted picture's origin is on its drawn feet, its lowest opaque row, within 2 texels (`test_every_sorted_picture_sorts_by_its_drawn_feet`). Where the kit's foot is further off than that, the generators move the origin there and keep every texel in place (`gen_physics.on_feet`). A thing that lies flat and blocks nobody is not y-sorted at all: sorted by its far edge it would cover whoever walks over it.

## Actors behind tall things

`world/occlusion.gd`, added to every zone by `world/zone.gd`. It builds art-style.md rule 11 ("The companion stays readable") as the app does: when one picture drawn in front hides at least 40 % of an actor's body, a copy of the actor at 42 % opacity is drawn over the scenery.

- Who: the player and enemies (the groups `player` and `enemy`). Villagers and signs stand still, so a hidden one is a placement fault to fix in the scene, not to paper over.
- What hides: a scenery `Sprite2D` at z 0 or above that is drawn after the actor. The share is the body's own: of the opaque texels of the actor's drawing (every second one each way, about 550 for Bramble) how many lie under an opaque texel of the picture; the most that any one picture covers counts. At the willow's edge it reads 45, 42 and 39 % where the true shares are 45.6, 42.2 and 39.5 % (`test_forty_percent_means_forty_percent_of_the_body`). A low fence across the feet never reaches 40 %. Scenery may be scaled, flipped or turned.
- Cost: an actor is measured when it has moved a texel, or every 0.25 s, against the pictures registered in its 192 texel grid cell. A first pass over 50 of the points settles it when the share is clearly under 25 % or over 55 %; only near the line are all points read. A picture's alpha is read once, the first time something stands behind it.
- Motion: it fades in over 0.18 s and out over 0.12 s; under reduced motion both happen at once. It stops with the tree when the game is paused, and its nodes go with the zone.

## Checks

| Check | Holds |
| --- | --- |
| `game/test/test_physics_model.gd` | layers and masks of every body and area in the three zones; no villager hidden behind scenery; a solid 6 texels outside each edge at 40 points a side (a sample, not a proof: a gap between two points would pass); woodland solids no wider than what is drawn; Crossroads' reviewed boxes; y-sort origins on drawn feet; flat things under people |
| `game/test/test_occlusion.gd` | the 40 % rule and its branches, the fade, reduced motion, the terrace road and the willow |
| `game/test/test_arrow_physics.gd`, `test_arrow_walls.gd` | the start check, low solids, the archer |
| `game/test/test_world_fixes.gd` | the Undercroft's measured boxes and slots, Crossroads' wall foot, the plate off the walk to the lever, arrival spawns clear of their doors (32 texels: more than the walk covers in the 0.4 s a door takes to arm), the layer names |

After changing a plan, a piece's box or a walk mask, regenerate and run `npm run check:godot`:

```sh
python3 game/tools/gen_zone.py woodland
python3 game/tools/gen_village.py crossroads --no-render
python3 game/tools/gen_undercroft.py --no-render
python3 -m scripts.art.kit.props        # after a piece's box changed, then scripts.art.kit.bake for the kit zones that use it
```
