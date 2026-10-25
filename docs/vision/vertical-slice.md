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
8. **The first night.** The lit lantern is the attention the raid comes from. It is announced when the player next comes home, can be postponed twice, and then begins the next time the player walks into town; the prepare screen is never timed. Losing costs nothing but brief repairs. **It is built last**, once Codex's enemies and the familiar's save land, and it moves to M2 if the slice runs long (12.2 allows this). The plan already holds its lane and two pads.

## The quest chain (data)

All in the existing schema (`game/data/quests/*.json`, `game/data/dialogue/*.json`). Events: `talk:<speaker>`, `camp:<camp>`, `enter:<zone>`, and the new `restore:<id>`.

| Quest | Kind | Starts on | Steps | Rewards |
| ----- | ---- | --------- | ----- | ------- |
| `woodland_stones` *Thorns by the stones* | main | `talk:stone_sign` | `camp:meadow`; `talk:stone_sign` | 40 Glint |
| `road_to_crossroads` *The road home* | main | `talk:hale` | `enter:crossroads` (or already visited); `talk:moss` | 10 Glint; `met_moss` |
| `cold_forge` *The cold forge* | main | `talk:hale` once the road is done | `restore:forge` (or already restored); `talk:hale` | `forge_open`, `undercroft_open` |
| `under_the_stones` *Under the stones* | main | `talk:hale` once the forge is done (the same talk) | `enter:undercroft`; `camp:undercroft_rooms`; `camp:thornback`; `talk:circle_shard` (sets `shard_taken:woodland`); `talk:shard_lantern` (sets `shard_home:woodland`) | 60 Glint; `thornback_freed` |
| `home_again` *Home again* | village | `talk:moss` once the shard is home | `restore:fern_cottage`; `talk:ada_fern` | 25 Glint; `fern_home`, `seeds:valley` |

Glint over the chain: 40 + 10 - 30 + 60 - 20 + 25 = 85 at the end, enough for a first upgrade at the forge (upgrade prices are Codex's).

**Schema extensions** (tested in `game/test/test_slice.gd`): conditions gain `restored`, `not_restored` and `glint_at_least`; a door takes `only_if` (a condition), and so does the new `Conditional` node; entering a zone sets `visited:<zone>`. The save gains `village.restored` (id to tier); older saves load as broken.

## Crossroads as data

`game/data/plans/crossroads.json`, in world px local to the zone (640 x 560; `origin_on_canvas` 5976, 3248 puts the square where `art/regions/valley.json` has it, 6176, 3448). It reuses the region plan's keys (`id`, `box`, `tiers` with outlines, `faces`, `routes`, `stairs`, `places`) and adds what a playable zone needs: `buildings` (rect, door, stage, restore), `lots` (the burnt lots for stage 2 and 3), `props`, `people`, `things`, `restore_sites`, `spawns`, `doors`, `raid_pads` (two for the first night, four more for stage 1) and `raid_lanes`. One plan holds every state: any item with `if` shows only while its condition holds, and `stages` names them (broken, forge, homecoming) for tests and tools. `game/data/plans/undercroft.json` has the same shape, with `camps`.

`python3 game/tools/gen_blockout.py` writes `game/zones/<id>/<id>.tscn` from a plan: flat placeholder rectangles, walls, interactables, restore sites, camps, doors, spawns and raid pad markers, with conditional items wrapped in `Conditional` nodes. When the kit draws Crossroads, its base scene replaces the rectangles and the node names stay.

## Play it

```sh
$GODOT --path game -- --fresh                      # woodland, the sign quest, Hale on the east path
$GODOT --path game -- --fresh --zone=crossroads    # straight to the broken square
```

The loop: woodland, the east door to Crossroads' terrace, the square, the smithy's mark, back west to the woodland, the hatch by the stones, the Undercroft, back to the lantern.

## Open for Matt

1. The forge first (reasons in beat 5), with the apothecary as act 1's first restore.
2. The smith is a new villager, Hale, rather than one of the fourteen; Morel (the alchemist) appears in the slice only as a neighbour who joins in act 1.
3. Restores are paid at a "restore here" mark on the building itself, not at the hut's workbench (7.3 allows either).
4. The first night stays in the slice but is built last, after Codex's enemies; it moves to M2 if the slice runs long.
5. The placeholder purse: 40, 10, 60 and 25 Glint in, 30 and 20 out.
