# C61 woodland enemies

Assignment: Claude A #149 comment 6396530638, r1. Base c21814f.

Instantiate `res://enemies/woodland_camp.tscn` under a zone's Actors node. It is deliberately not inserted into Claude's woodland scene. Four placeholder actors share one encounter pool: triangular rusher, round shooter with a barrel, rectangular shield bearer, large horned elite. Replace these programmatic stand-ins when authored regional art is available.

The LimboAI HSM runs idle → approach → windup → attack → recover. Any active state cancels to leash when either combatant leaves the 140 world-pixel home radius, or the target disappears. All state timing uses delta seconds. Normal tells are 0.95 s, the elite 0.65 s. Direction locks on commitment. Ground lane/ring/wedge marks and growing overhead marks provide shape cues without blinking.

The cap is shared across pools, including overlapping camps and isolated actors. Two reservations cover wind-up, contact, projectile lifetime and recovery. Waiting enemies circle or keep distance. Death, removal, cancellation and leash return reservations. A shooter checks viewport visibility and solid-cover line of sight before commitment; its finite ray-tested projectile stops on solid cover/player (since 11 Nov it flies over low solids, and the shooter sees over them, as the player's arrow does) and travels at 80 world px/s, below the roll's nominal 100. Shield front halves integer damage (rounded up), back is open, and recovery opens the front too.

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

## Home, waking and reach (10 and 11 Nov, the combat stream)

The rules below hold for the mossling (`actors/enemy.gd`) and for these creatures (`slice_enemy.gd`) unless a column says otherwise. The first three are Matt's of 10 Nov. Each row names the test in `test/enemies/test_enemy_rules.gd` that holds it; a row marked "played" was also seen with real input (PR #468).

| Rule | Mossling | Creature | Held by |
| --- | --- | --- | --- |
| No healing on the walk home; full health 3 s after it is home (`HOME_HEAL_TIME`) | yes | yes (they never healed before) | `..._does_not_heal_on_the_walk_home...`, `test_a_creature_is_whole_three_seconds...`, the numbers test; played for the mossling only |
| A hit wakes an idle enemy when the archer is within 330 px | yes | yes, and the archer must be inside its 420 px leash | `test_a_hit_wakes_an_idle_mossling...`, `test_a_hit_wakes_an_idle_creature...`; played |
| Its idle camp mates in earshot wake with it, if the archer stands on ground they keep to | within 165 px | within 300 px | the same two, and `test_a_camp_mate_whose_ground_the_archer_is_not_on_stays_asleep`; played |
| Asleep, coming or walking home, it is only hurt by an archer it can come for (`can_come_for`); otherwise the arrow glances off (`glance.gd`: a short metal spark and the word "clink" for 0.4 s, the spark standing still under reduced motion; every glance calls `Glance.clink(at)`, the one sound hook, empty until the sound work fills `Glance.on_clink`) | on its ground (300 px leash + 51 px reach from home) and, asleep or walking home, within 330 px | inside its leash and, asleep or walking home, within 330 px | `test_an_arrow_from_beyond_330_glances...`, `..._at_its_leash_limit_is_not_a_target...`, the creature's wake test; played |
| While it winds up, lunges or recovers it can always be hurt | yes | its committed wind-up and strike finish even across its leash (Matt, 11 Nov); the recovery after them goes home | `test_a_mossling_that_winds_up_lunges_or_recovers_can_always_be_hurt`, `test_a_committed_tell_finishes_across_the_leash...` (test_slice_enemies.gd); played |
| It strikes only along a clear line: a low solid between (a bramble, a root, rubble: arrows cross it) is walked round, and a chase that gains nothing is given up as usual (Matt, 11 Nov) | yes | the rusher, shield and elite (the toad shoots over it) | `test_a_mossling_walks_round_a_low_solid...`, `test_a_rusher_walks_round_a_low_solid_too`, `test_in_the_woodland_the_camp_gets_round_the_bramble...`; played |
| Health | 5 (3 until 11 Nov, Matt: a lone mossling shot from 300 px now arrives); fight Glint stays 2 | as before (4, 8, 12) | `test_a_mossling_has_five_health` |
| A hit on the walk home by an archer it can come for turns it round | yes | yes | the leash-limit test, `test_a_creature_hit_on_its_walk_home...` |
| Woken by a shot it keeps coming for 3 s even past its lose radius (`PROVOKED_TIME`) | yes | no lose radius | `..._keeps_coming_when_the_arrow_knocks_it_past_330`; played |
| Woken by a shot it runs in 1.6 times as fast until its first wind-up (`RUN_IN`; a proposal of 11 Nov) | yes | the rusher only | `test_woken_by_a_shot_it_runs_in_faster...`; played |
| It steers round a solid on the walk home and in the chase (`steer.gd`, and `wall_min_slide_angle = 0`): with a goal, the hand whose end of the solid is the shorter way round (felt with short rays along it) | yes | yes | the two `..._walks_home_round_a_solid...` tests, `test_the_chase_goes_round_a_solid...`; the walk home played |
| A walk home longer than twice the straight walk plus 3 s is given up: it is put at home | with a 0.3 s fade in, none under reduced motion | no fade | the two `..._cannot_get_home_gives_up...` tests, the fade test; never seen in a zone |
| A chase that gets no nearer its target for 2.5 s is given up: it walks home, and on that walk a shot neither turns it round nor hurts it. At home it answers a shot at once | yes | yes | `test_a_chase_that_gains_no_ground...`, `test_the_real_pocket_at_610_1570...`, `test_a_creature_whose_approach_gains_no_ground...`; played |
| No noticing by nearness for 2.5 s after a zone becomes ready (`ARRIVAL_GRACE`; a hit still wakes it) | yes | yes | the two grace tests; played |

What is not so, so nobody reads more into the table. Each of these was played and is open (numbers in PR #468):

- **A lone mossling or rusher woken from about 300 px is freed before it arrives.** Three or four arrows take less time than its run, also at the faster run-in.
- **A creature can be beaten at its leash line** by stepping out when it comes and back in to shoot: it turns for home the step the player is outside.
- **A melee enemy cannot answer over a low solid.** The player's arrows cross a bramble, a root or a rubble heap (`docs/physics.md`); a mossling or a creature winds up and lunges into it. Standing behind one, the woodland camp, the hall's rusher and the corridor's pair can be freed without a heart lost. The toad's seed and its sight do cross low solids, as the Thornback's thorns and charge do.
- **The pocket at (610, 1570) in the woodland.** Shot from (600, 1720) the mosslings run into it, give the chase up after 2.5 s, walk home and come again at the next shot; while they stand in the pocket arrows reach them. The cure is in the solids there, not in these rules.
- `steer.gd` is wall following, not path finding. It gets an enemy round a bench, a stump or a door jamb. Where it circles instead, the given-up chase or the given-up walk ends it.
- The glance mark is the same pale chevron whatever the reason (out of reach, walking home, the Thornback from outside its arena).
