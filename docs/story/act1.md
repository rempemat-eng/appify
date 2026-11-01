# Act 1 after the slice: the Frostline, the Brackens and the circle waking

Claude K (story), 25 Oct. The assignment is to-all-assignments-1025, "K: act 1 after the slice: quests and dialogue as JSON". This act follows `docs/vision/vertical-slice.md` and the Starfall arc in game-design v2 §7.2 and §8.2 (`claude-a/game-design-v2`).

The data is in two places:

- **Quests:** `game/data/quests/a1_*.json`, 15 quests.
- **Dialogue:** `game/data/dialogue/frostline.json`, `brackens.json` and `a1_valley.json`.

`game/test/story/test_act1.gd` runs the whole act through `Quests.notify` and checks the data against itself. All Glint amounts and costs are **placeholders** to tune in play.

## The chain

The act opens once the slice ends (`home_again` done). Its three strands run side by side, and the circle waits for all three great shards.

| Quest | Kind | Starts | What you do | Pays |
| --- | --- | --- | --- | --- |
| Bread for the Col hut | main (Frostline ch 1) | `talk:moss` | free the shard crows at the ridge col (`camp:col_crows`, opens **W2**); climb to the Frostline; take Moss's loaf to the hut warden | 30 |
| The ring is shut | main (ch 2) | `talk:hut_warden` | free the ibex on the High Fells (`fells_ibex`) | 40 |
| Under the snout | main | `talk:hut_warden` | ask the ice-cutter; the ice caves (`ice_caves`), its rooms, **the Rime Wyrm**; help Tam out; take the shard; set it in the lantern | 60 |
| A cup by the stove | resident (ch 3) | `talk:hut_warden` | Tam by the stove: **Tam joins** | 20 |
| A ring of our own | village | `talk:hut_warden` | restore the green's ring as the training yard (the bothy keeper's) | – |
| The scattered flock | main (Brackens ch 1) | `talk:drover` | free the flock by the gap (`gap_flock`) | 30 |
| The shepherd's dog | side | `talk:shepherd` | calm the dog on the road (`stray_dog`) | 20 |
| The cut rope | main (ch 2) | `talk:drover` | the drove well; the barrow (`the_barrow`), its rooms, **Old Fang**; the shard to the lantern | 60 |
| The road west | resident (ch 3) | `talk:drover` | free the old ram on the Heather spur (`spur_tor`): **Iona joins**; the drover's niece moves in | 30 |
| The torn roof | village | `talk:morel` | restore the herbalist's as the apothecary: **Morel joins** | – |
| The choked well | village | `talk:moss` | clear the well; Moss mentions the Company's buyer | 15 |
| The dark lighthouse | main | `talk:velvet` | Driftwood's quay (`driftwood_quay`); light the lamp: **Velvet joins** | 30 |
| The circle wakes | main | `talk:shard_lantern` with three shards home | take the light to the stones; the circle's trial (`circle_trial`): **Cairn joins** | 50 |
| The wolf moon | main (act 1's story siege) | `talk:hale` | rebuild the bell cupola, ring it, hold the lantern (`wolf_moon`) | 60 |
| The Millrace landslip | main | `talk:moss` | rebuild the halt's platform; free the landslip (`millrace_slip`, opens **W3**) | 40, `act1_done` |

Five folk join in Act 1: Morel and Velvet (the two starters not chosen; game-design §8.2), Tam, Iona and Cairn. The resident stories move on by quests and fights, never by rest. The hut warden's three chapters are the bread, the ring and the cup. The drover's are the flock, the rope and the road west.

## What other lanes need to place

These are listed for their owners; I made no edits to their files.

- **Claude A, Crossroads** (`game/data/plans/crossroads.json`):
  - restore ids with the costs the mark lines quote: `apothecary` 40, `well` 20, `training_yard` 40, `bell_tower` 50, `halt` 60;
  - Velvet standing on the square (speaker `velvet`);
  - the bell (`bell_tower`);
  - the `wolf_moon` siege camp.
- **Claude A, the woodland:** the `circle_stones` interactable, `cairn` and the `circle_trial` arena.
- **Claude F**, from #262 (`frostline.json`, `brackens.json`):
  - camp ids `fells_ibex`, `gap_flock`, `stray_dog` and `spur_tor`, as drawn;
  - new camps: `col_crows` (the ridge col, W2's fight), `ice_caves_rooms` and `rime_wyrm`, `barrow_rooms` and `old_fang`;
  - speakers `hut_warden`, `ice_cutter`, `forager`, `tam`, `frost_shard`, `drover`, `shepherd`, `iona`, `drove_well`, `barrow_shard` and `hermit` at #262's quest spots;
  - **two names differ:** game-design §8.2 names the bosses the Rime Wyrm and Old Fang, while #262 has an ibex ram and a badger sow as the dungeon keepers. The quests follow the design. Please align, or tell me to change them.
- **Claude E:** Driftwood's quay camp `driftwood_quay` and the `lighthouse_lamp`, plus the `millrace_slip` camp at the cutting.

## For Matt

1. **Homes for Codex's fourteen.** The proposal is on #149: Iona on the Brackens, Clack in Cogsworth, Brine on the Isles, Pendle in Dust Gulch (his sheet says no clock motif), Rook on Halcyon and Mote on Lumen, with the Lull a mover only. Act 1 uses Morel, Velvet, Tam, Iona and Cairn.
2. **The engine change.** `core/dialogue.gd` now gives a speaker who appears in several files all their entries, ordered by an optional `priority`. This lets act files add lines to the slice's people without editing the slice's files. Claude A owns `core/`, so it is flagged for Claude A's yes.
