# C61 woodland enemies

Assignment: Claude A #149 comment 6396530638, r1. Base c21814f.

Instantiate `res://enemies/woodland_camp.tscn` under a zone's Actors node. It is deliberately not inserted into Claude's woodland scene. Four placeholder actors share one encounter pool: triangular rusher, round shooter with a barrel, rectangular shield bearer, large horned elite. Replace these programmatic stand-ins when authored regional art is available.

The LimboAI HSM runs idle → approach → windup → attack → recover. Any active state cancels to leash when either combatant leaves the 140 world-pixel home radius, or the target disappears. All state timing uses delta seconds. Normal tells are 0.95 s, the elite 0.65 s. Direction locks on commitment. Ground lane/ring/wedge marks and growing overhead marks provide shape cues without blinking.

The cap is shared across pools, including overlapping camps and isolated actors. Two reservations cover wind-up, contact, projectile lifetime and recovery. Waiting enemies circle or keep distance. Death, removal, cancellation and leash return reservations. A shooter checks viewport visibility and solid-cover line of sight before commitment; its finite ray-tested projectile stops on solid cover/player and travels at 80 world px/s, below the roll's nominal 100. Shield front halves integer damage (rounded up), back is open, and recovery opens the front too.

Integration boundaries: existing Player `take_damage` and enemy `take_hit` interfaces, collision layers 1 solid / 2 player / 4 enemies; existing Camp `died` signal and quest/save behaviour. This scene inherits current Camp's persistently cleared semantics, rather than introducing region-refresh/save rules. Claude must resolve that existing foundation/design difference during integration. No new rewards, equipment, save schema, difficulty option or main-scene wiring. Combat balance remains placeholder scale matching the foundation's 5-HP player, not Appendix B's level formula.

The GdUnit suites under `game/test/enemies` exercise actual HSM transitions, release timing for all four roles, shared commitments, target-loss and leash cancellation, shield direction, projectile reservation and death cleanup. Headless checks do not establish visual quality or gamepad feel. Run `npm run check:godot` and `npm run verify` before readiness; full art reproduction is also required by AGENTS.md. Validation status belongs in the PR/checkpoint.

## Looks (Claude A, enemy cast)

The placeholder shapes are replaced by drawn woodland creatures from the castwork (`castwork/src/boarlet.py`, `toad.py`, `tortoise.py`, `thornback.py`, `den.py`; tables in `anim_<id>.py`), imported with `tools/import_cast.py` into `assets/characters/<id>/`; the den, clumps and seed are strips in `assets/enemies/`. Each creature has the Starfall shard lodged in it (story: shards turned them wild; they are freed, not killed).

| role | creature | tell in the pose | ground tell |
| --- | --- | --- | --- |
| rusher | boarlet | head drops, rump up, paws twice with dust, quivers | lane |
| shooter | bramble toad | rises on its front legs, sac swells, a glint gathers at its lips (sighting) | narrow wedge |
| shield | mossback tortoise | head drawn in, front reared off the ground | ring (the stomp) |
| elite | thornback (1.35x boar, two shards, bramble back) | the boarlet's, deeper and shorter (0.65 s) | lane |

Wiring adds nodes and never edits `slice_enemy.gd`: `woodland_camp.tscn` has a `CreatureDresser` child that gives every `SliceEnemy` entering the camp a `CreatureLook` child. The look hides the placeholder `_draw` with `self_modulate` (children are unaffected), maps state to clip (idle, approach/leash → move, windup → telegraph stretched to `windup_time()`, attack, recover → stagger, a hit → hurt, or a flash during a tell or charge), draws the contact shadow and the ground tell in the one reserved colour (it fills as the tell runs and brightens once, solidly, for the last fifth; no blinking), and dresses the shooter's shot as a thorn seed. On `died` a `FreedCreature` plays `freed` (the shard pops out, it shakes itself) and walks off and fades (finite; under reduced motion it calms in place). The den and clumps sit in the camp's parent, because a cleared camp frees its children; they show calm once the camp is cleared. `--camp` (game.gd) sets the camp north of the player to see it.
