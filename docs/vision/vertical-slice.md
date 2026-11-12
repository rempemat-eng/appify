# The vertical slice: the first 60 to 90 minutes (25 Oct)

The prologue as one playable stretch, beat by beat, for the Godot build (`docs/godot.md`). It follows `game-design.md` (sections 7, 8 and 12.2, on `claude-a/game-design-v2`) and Matt's round-2 answers: the Starfall story (the cracked moon's shards turn creatures wild; they are **freed, not killed**), Glint as the one currency, storm-broken Crossroads as the village you restore with your hut on a terrace above the square, raids that come from earned attention and can be postponed twice, and a defeat that keeps your gear and drops a fifth of the Glint earned since you were last home as a cache you can pick up again. The player is **Bramble** (the older ranger in Codex's fourteen) with the Mossling as familiar.

What is built now (this PR) is the village and quest half: the chain below as quest and dialogue data, Crossroads and the Undercroft as plans and blockout scenes, and the restore step. Combat, the woodland's enemy types and the Thornback belong to Codex (`game/combat/**`, `game/enemies/**`); the blockout uses the existing `actors/enemy.tscn` as a stand-in so the chain plays end to end.

**Numbers.** Every Glint amount, cost and minute below is a **placeholder** to tune in play-tests; none is balanced. Scrap and region materials (10.1) are not in the save yet, so costs are Glint only for now.

## Beat by beat

| # | Beat | Where | Who | What the player does | Reward | What changes in the village | Minutes |
| - | ---- | ----- | --- | -------------------- | ------ | --------------------------- | ------- |
| 1 | Arrival | the valley woodland, by the old path (`woodland:start`) | Bramble, the Mossling | Wakes after the starfall night; learns to move, roll and swing on the way to the stones | none | none yet; the crack in the night sky is visible | 3 to 5 |
| 2 | Thorns by the stones (in game) | the stone circle and the meadow east of it | the weathered sign | Reads the sign, frees the three shardstruck mosslings, reads it again | **40 Glint** | none | 8 to 12 |
| 3 | Meeting the first villager | the woodland's east path | **Hale**, the smith (NPC, placeholder name) | Finds Hale, lost since the storm; she asks to walk back with you (*The road home* starts) | none | none | 2 |
| 4 | Crossroads, broken | the garden walk, your terrace, the square | **Moss** at the stall; **Morel** outside his torn herbalist's | Walks in along the garden walk past your scorched beds, down the gate stair to the square; talks to Moss, who lists what the storm took | **10 Glint** | the broken state: rubble round a choked well, slates across the smithy door, the bakery cold, the library roof torn, a smoking crater in the park, the shard lantern dark; only the stall open | 5 to 8 |
| 5 | The first restored service: **the forge** | the old smithy, east of the square | Hale | *The cold forge*: pays 30 Glint at the "restore here" mark by the smithy door; Hale lights the forge and gives the first upgrade | the forge (tier 1: upgrade and salvage); one free upgrade (placeholder) | rubble and boards gone from the smithy; the forge glows; Hale moves from the square to her anvil; the hatch under the stone circle is unbarred | 4 to 6 |
| 6 | The Undercroft and the Thornback | the hatch by the stone circle, then three rooms and the chamber under it | the Thornback; Cairn asleep in the wall (a look, no more) | *Under the stones*: frees the shardstruck in three rooms (Codex's grunt, lunger, shooter and swarmer), then the Thornback; takes the great shard | **60 Glint** on return; loot from the rooms (the valley family, Common to Rare; Codex) | none until the shard comes home | 20 to 30 |
| 7 | The first homecoming change | the square, then the Ferns' cottage | Moss, Hale, **Ada Fern** (placeholder villager) | Sets the shard in the lantern; *Home again*: clears the Ferns' door (20 Glint), welcomes Ada home, plants two beds | **25 Glint**, two packets of valley seed | the lantern lit; the well clear; the crater stops smoking; the Ferns' cottage open; your beds dug over; a new note on the board | 8 to 12 |
| 8 | The first prepared raid: **the first night** | the square: one lane (the halt road), two pads | Hale, Moss; the shardstruck drawn by the lit lantern | Announced on the next return home; "ring the bell" on the prepare screen (untimed, both pads prefilled with Hale's hurdle barricade); three waves | a modest Glint purse; the bell tower offered for stage 1 | brief repairs only (boards on a window, a cart on its side), cleared on the next visit | 10 to 15 |

Total: about 60 to 90 minutes, matching 12.2's test (45 to 70 for a strong player).

### Notes on each beat

1. **Arrival.** No tutorial text. The path from `start` funnels past the sign, so the first "!" the player sees is the sign's (8.3: show, do not explain). The Mossling follows a step behind.
2. **The sign quest** is already in the game (`woodland_stones`). It is the slice's first fight and pays what the forge needs, so the money loop is felt before it is explained. "Freed" in the text, not "killed": the mosslings run back into the trees.
3. **Hale** stands on the east path, so a player who runs east first meets her before the sign. That is fine: her lines point back to the sign's pouch if the Glint is short. She hides once *The road home* starts, as if she walked on ahead.
4. **Broken Crossroads.** The entry is the garden walk on the terrace (the woodland's east door), so the player passes the hut and its beds first and sees the square from above before walking down the gate stair: the home is shown before the town. Moss is the town's voice (the stall is the one thing open). Morel, the alchemist from Codex's fourteen, stands outside the herbalist's he will reopen in act 1 as the apothecary; in the slice he only foreshadows (his tonics, the fever in the mosslings).
5. **Forge, not apothecary.** Reasons: (a) 12.2's test asks the player to upgrade a weapon, and gear is Bramble's first loop (fight, loot, upgrade); (b) the smith is the prologue's mover in 8.2 and 7.4 ("a smith from Crossroads (forge)"); (c) the apothecary brews from crops, which the slice only plants at its end, and 8.2 ties it to the circle's act-1 beat (the gardener's daughter, or Morel); (d) the forge's defence kind, the hurdle barricade, is what fills the first night's two pads. The apothecary is the first restore of act 1. The restore is paid at a "restore here" mark on the building, instantly, with no timer (7.3).
6. **The Undercroft** is three rooms and the chamber in a row under the stone circle, reached by the hatch Hale unbars. Defeat here follows Matt's rule: the player keeps all gear, and a fifth of the Glint earned since last home drops as a cache at the spot, picked up again on the next run. The Thornback, a boar in a bramble shell, is freed: when its health runs out the bramble shell cracks and falls away and it lies down calm beside the shard. Cairn is a granite figure half sunk in the chamber wall; looking at him after the shard is taken makes his eye slits glow once. He stands up in act 1.
7. **The homecoming.** Walking the shard home is the slice's emotional beat: the lantern lights, the well clears and the crater stops smoking (7.10, the village reacts to the story). The villager quest (*Home again*) is 12.2's "one villager" quest and repairs a second building in front of the player. Its seeds are the two beds 12.2 asks for; they grow by outings, not by clock.
8. **The first night.** The lit lantern is the attention the raid comes from. It is announced when the player next comes home, can be postponed twice, and then begins the next time the player walks into town; the prepare screen is never timed. Losing costs nothing but brief repairs. **Built 12 Nov** (below, "The first night as built"), after Codex's enemies, on the plan's lane and the existing woodland creatures.

## The quest chain (data)

All in the existing schema (`game/data/quests/*.json`, `game/data/dialogue/*.json`). Events: `talk:<speaker>`, `camp:<camp>`, `enter:<zone>`, and the new `restore:<id>`.

| Quest | Kind | Starts on | Steps | Rewards |
| ----- | ---- | --------- | ----- | ------- |
| `woodland_stones` *Thorns by the stones* | main | `talk:stone_sign` | `camp:meadow`; `talk:stone_sign` | 40 Glint |
| `road_to_crossroads` *The road home* | main | `talk:hale` | `enter:crossroads` (or already visited); `talk:moss` | 10 Glint; `met_moss` |
| `cold_forge` *The cold forge* | main | `talk:hale` once the road is done | `restore:forge` (or already restored); `talk:hale` | `forge_open`, `undercroft_open` |
| `under_the_stones` *Under the stones* | main | `talk:hale` once the forge is done (the same talk) | `enter:undercroft`; `camp:undercroft_rooms`; `camp:thornback`; `talk:circle_shard` (sets `shard_taken:woodland`); `talk:shard_lantern` (sets `shard_home:woodland`) | 60 Glint; `thornback_freed` |
| `home_again` *Home again* | village | `talk:moss` once the shard is home | `restore:fern_cottage`; `talk:ada_fern` | 25 Glint; `fern_home`, `seeds:valley` |

Glint over the chain: 40 + 10 - 30 + 60 - 20 + 25 = 85 from the quests and restores, plus 31 from the fights since 11 Nov (2 for each of the three mosslings, 3 for each of the Undercroft's five creatures, 10 for the Thornback, each paid once for the life of the save): 116 at the end of *Home again*, and 76 after the apothecary's 40 in act 1's first quest. Going down leaves a fifth of the Glint carried, rounded down, as a cache where the player fell; it stays until it is picked up, a second defeat adds a second cache, and both are in the save (`game/core/glint_cache.gd`, `game/data/balance/glint.json`). The story model plays every order with the worst defeats in it: the forge, the Ferns' door and the apothecary stay affordable.

**Schema extensions** (tested in `game/test/test_slice.gd`): conditions gain `restored`, `not_restored` and `glint_at_least`; a door takes `only_if` (a condition), and so does the new `Conditional` node; entering a zone sets `visited:<zone>`. The save gains `village.restored` (id to tier); older saves load as broken.

## Crossroads as data

`game/data/plans/crossroads.json`, in world px local to the zone (640 x 560; `origin_on_canvas` 5976, 3248 puts the square where `art/regions/valley.json` has it, 6176, 3448). It reuses the region plan's keys (`id`, `box`, `tiers` with outlines, `faces`, `routes`, `stairs`, `places`) and adds what a playable zone needs: `buildings` (rect, door, stage, restore), `lots` (the burnt lots for stage 2 and 3), `props`, `people`, `things`, `restore_sites`, `spawns`, `doors`, `raid_pads` (two for the first night, four more for stage 1) and `raid_lanes`. One plan holds every state: any item with `if` shows only while its condition holds, and `stages` names them (broken, forge, homecoming) for tests and tools. `game/data/plans/undercroft.json` has the same shape, with `camps`.

`python3 game/tools/gen_blockout.py` writes `game/zones/<id>/<id>.tscn` from a plan: flat placeholder rectangles, walls, interactables, restore sites, camps, doors, spawns and raid pad markers, with conditional items wrapped in `Conditional` nodes. Crossroads is now drawn (25 Oct): `python3 game/tools/gen_village.py crossroads` renders the plan with the kit's village module (buildings drawn once, the storm's damage an overlay each restore removes) and writes the scene with the same node names (docs/godot.md).

## Play it

```sh
$GODOT --path game -- --fresh                      # woodland, the sign quest, Hale on the east path
$GODOT --path game -- --fresh --zone=crossroads    # straight to the broken square
```

The loop: woodland, the east door to Crossroads' terrace, the square, the smithy's mark, back west to the woodland, the hatch by the stones, the Undercroft, back to the lantern.

## Play the current slice by hand (2 Nov)

This is a **source-derived checklist, not a completed manual playtest**, for
main `bf85f174`. Claude's accepted endpoint is **Home again**: the woodland
shard home, Ada welcomed and Cairn's existing statue answer observed. Full circle
waking remains gated. The older beat table above is the wider design, not a
claim that every beat is currently playable.

Use a display and a separately isolated, disposable Godot user-data profile
before launching the woodland at `start` with `--fresh`, as in
[the Godot instructions](../godot.md#commands). Do not use a normal player
profile: `--fresh` skips loading, but `game.gd` still autosaves on zone and
quest changes; portable mode can also override XDG isolation. Do not use
`--stage`, `--at`, `--camp` or `--bossfight` to skip this route.

Current controls: WASD/arrows move, mouse aims, left click fires Bramble's bow,
Space rolls, E interacts; E/Enter advances dialogue (first finishes the text,
then advances/closes it). Finish each conversation before moving on. The old
melee-combo helper is not bound to the attack action.

- [ ] Start in the woodland. Approach the weathered sign and read it.
- [ ] Free the three enemies in the meadow camp through normal combat, then
  read the sign again: *Thorns by the stones* completes, with 46 Glint (the sign's 40 and 2 a mossling).
- [ ] Talk to Hale on the east path, then walk through the east door to
  Crossroads. Talk to Moss: *The road home* completes, with 56 Glint total.
- [ ] Talk to Hale in the square. Use the smithy's Restore mark (30 Glint),
  finish its dialogue, then talk to Hale at the forge. *The cold forge*
  completes; the Undercroft hatch opens. Expected balance: 26 Glint.
- [ ] Walk back through Crossroads' woodland door, then enter the hatch by the
  stones. Do not use a zone/spawn jump to bypass either door.
- [ ] Traverse the Undercroft and free its five room-camp enemies. Step onto the
  seal plate, then approach and pull the lever: the seal opens. Neither a
  console flag nor a script-emitted area signal counts as manual completion.
- [ ] Free the Thornback through normal combat, take the revealed great shard,
  and look at Cairn's statue: its answer mentions a glow; Cairn does not join.
- [ ] Walk out to the woodland, return to Crossroads and interact with the shard
  lantern. *Under the stones* completes and the village enters homecoming.
- [ ] Talk to Moss, restore the Ferns' cottage (20 Glint), finish the dialogue,
  then welcome Ada. *Home again* completes; expected balance is 116 Glint (85 from quests and restores, 31 from the nine creatures; less whatever lies in a cache not yet picked up) with
  `fern_home`, `seeds:valley` and `shard_home:woodland` set by normal consumers.
- [ ] Stop here and record the last completed beat plus any obstructed
  approach, failed prompt, dialogue, fight or transition. Do not grant flags
  or teleport to turn a blocked manual run into a pass.

### What the script proves, and what remains blocked or unplayed

The merged [scene-consumer scenario](../../game/test/test_slice.gd)
(`test_reachable_slice_through_home_again_uses_scene_consumers`) completes the
quest chain, but calls interactables directly, closes dialogue automatically
because no dialogue box is attached, emits body-entry signals for all five door
crossings and the plate, and supplies lethal hits to all nine enemies. Walking,
collision/proximity, aiming, surviving the fights and using the visible dialogue
box therefore remain **unplayed at each corresponding checklist step**. The
source provides normal input/area consumers for them; this is not evidence that
they require scripting, nor proof that no physical blocker exists.

**Beyond this endpoint, the full circle cannot currently be reached through
the registered scenes.** [The zone registry](../../game/data/zones.json) contains
only woodland, Crossroads and Undercroft. Frostline, ice caves, Brackens and the
barrow routes needed for the other two shards are absent. The woodland also
does not place the later `circle_stones`/`cairn` interactions or
`circle_trial` camp described in [Act 1](../story/act1.md#what-other-lanes-need-to-place).
The scenario explicitly leaves those shards absent and `circle_awake` false.
Do not substitute its earlier state-seeding tests for a manual route.
Planting two beds and a first weapon upgrade in the older beat table are
outside the accepted scenario's completion evidence. The first-night raid has
its own route and suite (below).

Source references: [input bindings](../../game/core/inputs.gd),
[player input](../../game/actors/player.gd),
[dialogue UI](../../game/ui/dialogue_box.gd),
[door consumer](../../game/world/door.gd),
[plate](../../game/world/pressure_plate.gd),
[lever](../../game/world/seal_lever.gd) and
[restore consumer](../../game/world/restore_site.gd).

## The first night as built (12 Nov)

Beat 8 plays in Crossroads after *Home again*. `data/raids/first_night.json` holds it, `core/raids.gd` keeps
it in the save and `world/raid_night.gd` plays it (docs/godot.md, "Raids"). Every number is a placeholder.

1. **Attention.** The lit lantern (`shard_home:woodland`) draws the shardstruck. The raid is announced only
   after *Home again* is done, so beat 8 follows beat 7.
2. **Announced on the next walk into town.** This means walking into Crossroads from another zone. A load
   or getting up after a defeat does not count, so an older save is never ambushed. The announcement is the
   prepare screen itself. It is untimed and the player stands still behind it. It names the halt road and
   shows the lane, with both pads holding Hale's hurdle barricade. Its buttons are "Ring the bell" and
   "Not tonight (n left)". A pad tap cycles between the hurdle and empty, and the layout is remembered.
3. **Postponed twice.** "Not tonight" puts it off until the next walk in. After two, the next walk in
   brings the screen without "Not tonight". Moss mentions the camp while it is put off. Quitting on the
   screen brings it back on the next start.
4. **Three waves, one lane, two pads.** The waves come down the halt road and use the woodland's
   creature roles: two boarlets; then a boarlet, a toad and a boarlet; then a mossback, a boarlet and the
   horned elite. They march to the lantern and batter a standing hurdle, or the lantern itself, with
   their own tells. A creature turns on the player when the player is near and nothing solid is between
   them. The toad spits over a hurdle. Nobody targets Hale, Moss or any villager. Creatures are freed with
   the camps' look and pay no fight Glint. Both pads are in the raid's own data: `pad_halt_street` in the
   street between the bakery and the herbalist's, and `pad_street_mouth` where the street opens on the
   square. Each hurdle spans the street wall to wall, so nothing walks round it. The lane is the plan's
   `halt_road` to the square's edge, then the raid's own points round the north of the well to the
   lantern's west side (the plan's last leg ran through the well). A raider strikes the lantern only
   from beside its post.
5. **Win.** A purse of 30 Glint is paid once and `first_night_won` is set. The hurdles and the lantern's
   bar clear away. The bell tower is offered as a restore (`bell_tower`, 50 Glint, act 1's id and price):
   its mark stands before the library's door from then on, and Hale points to it. Its picture (the
   cupola) comes with stage 1, so paying it changes no picture yet.
6. **Loss.** The night is lost when the lantern falls or the player goes down; a card says so, on
   getting up for the second. Defeat keeps the usual cache rule. Nothing is taken. Brief repairs show (boards on the smithy's window, a cart on its side)
   until the next walk in, which clears them and offers the night again with both postponements back.
   Walking out mid-night leaves it due. Quitting mid-night brings the screen back, from wave 1.

Placeholders (art follow-ups): the hurdle, the lantern's health bar, the two repairs and the screen's lane
map use the blockout's flat colours. There is no bell or horn sound yet.

`test/test_raids.gd` holds the rules. `game/tools/routes/first_night.txt` plays the end of the slice with
real input, from a save made just after *Home again* through the announcement, both postponements, a quit
on the screen, the three waves and the win, to Hale's offer.

## Open for Matt

1. The forge first (reasons in beat 5), with the apothecary as act 1's first restore.
2. The smith is a new villager, Hale, rather than one of the fourteen; Morel (the alchemist) appears in the slice only as a neighbour who joins in act 1.
3. Restores are paid at a "restore here" mark on the building itself, not at the hut's workbench (7.3 allows either).
4. The first night stays in the slice but is built last, after Codex's enemies; it moves to M2 if the slice runs long.
5. The placeholder purse: 40, 10, 60 and 25 Glint in, 30 and 20 out.
6. The first night (12 Nov), to confirm: the announcement waits for *Home again* to be done; the
   announcement and the prepare screen are one screen; a lost night is offered again on the next walk in
   with both postponements back; going down during the night loses it; walking out mid-night leaves it
   due. Where the pads go: both are now in the raid's data, in the street between the bakery and the
   herbalist's (`pad_halt_street`) and at its mouth (`pad_street_mouth`), each closing it wall to wall.
   The plan's first-night pads stand in the open square (`pad_halt_gate`, where a hurdle can be walked
   round) and on the harbour road (`pad_harbour_gate`, which no wave walks); move the plan's pads to
   match, or the raid's. The raid's lane also leaves the plan's last leg, which runs through the well.
   The purse is 30 Glint, and the bell tower is offered at act 1's price of 50, payable at once though
   its cupola is not drawn yet.
