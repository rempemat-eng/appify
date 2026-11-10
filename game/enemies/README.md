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

## Home, waking and reach (10 Nov, the combat stream)

The same rules hold for the mossling (`actors/enemy.gd`) and for these creatures (`slice_enemy.gd`). The first three are Matt's of 10 Nov; the rest follow from them or fix faults found in play.

| Rule | Mossling | Creature |
| --- | --- | --- |
| No healing on the walk home; full health after 3 s at home (`HOME_HEAL_TIME`) | yes | yes (they never healed before) |
| A hit wakes an idle enemy when the archer is within 330 px (`wake_radius`, `WAKE`) | yes | yes, and the archer must be inside its leash |
| Its idle camp mates in earshot wake with it, if the archer stands on ground they keep to | within 165 px | within 300 px |
| It can only be hurt by someone it can come for (`can_come_for`); otherwise the arrow glances off (`glance.gd`: a pale chevron for 0.22 s, one still drawing) | on its ground (300 px leash + 51 px reach from home) and, asleep or walking home, within 330 px | inside its leash (420 px from home) and, asleep or walking home, within 330 px |
| A hit on the walk home by someone it can come for turns it round | yes | yes |
| Woken by a shot it keeps coming for 3 s even past its lose radius (`PROVOKED_TIME`) | yes | not needed (no lose radius) |
| The chase and the walk home go round solids (`steer.gd`) | yes | yes |
| A walk home that takes longer than twice the straight walk plus 3 s is given up: the enemy is put at home (a 0.3 s fade in, none under reduced motion) | yes | yes |
| No noticing by nearness for 2.5 s after a zone becomes ready (`ARRIVAL_GRACE`; a hit still wakes it) | yes | yes |

What "wakes" means against the leash: a woken enemy chases as before and turns for home at its leash limit. An archer who stands where the leash cannot bring it within striking distance cannot hurt it, whether it is asleep, coming or walking home, so there is no place from which an enemy at its leash limit can be shot down. `steer.gd` is wall following, not path finding: it gets an enemy round a bench, a stump or a door jamb; across a room with no straight way it may circle, and then the given-up walk ends it.

`test/enemies/test_enemy_rules.gd` holds each rule (the movement ones on real physics steps); every one fails when its rule is taken out.
