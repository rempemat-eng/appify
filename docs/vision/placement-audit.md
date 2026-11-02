# Placement audit (Claude A, 2 Nov)

Matt, 2 Nov: "think deeply about parts of the game like fences. where would they be? what would they
fence in?" Every prop and structure in `game/kit/pieces` has been checked against
[placement-logic.md](placement-logic.md): what it is for (**purpose**), where it may stand (**requires**,
**forbids**, read by `scripts/art/kit/relations.py` on every kit zone in `check:kit`), and whether its
drawing fits that purpose. The table is generated from `scripts/art/kit/placement_audit.py`, which also
writes each piece's `placement.purpose`, requires and forbids; `--check` (in `check:kit`) fails when a
piece has no purpose or drifts from the table. Terrain materials and transitions are ground, not
placed objects, and are not listed.

Verdicts: **fine** (fits), **fixed** (its data or a placement was corrected in this audit), **redraw**
(the drawing does not fit its purpose: the art queue), **missing** (cannot be placed sensibly until a
companion piece exists).

Totals: 64 fine, 18 fixed, 4 redraw, 1 missing.

## Placements fixed in the kit zones

- `woodland_kit`: the footbridge's two `rules.requires` faults (a walkable piece now stands on its
  deck's cells, so the bridge stands on the water it spans with the path meeting it at both banks);
  the willow's trunk off the east path; a bush off the cascade's face; the stone ring's east stone
  clear of the north-south path; with the woodland's solid boxes restored, a holly inside the zone's
  west edge, a bramble clear of an oak, a boulder clear of the oak by the pool; the north path ends
  in trodden ground at the glade instead of stopping dead in the lawn; the waterfall's top.
- `kitlab_widths`: the stepping stones' path relation (their deck carries their landing stones).
- `kitlab`, `kitlab_tiers`: nothing out of place (a lab's bench, oak, stump and boulders beside its
  routes).

## Missing pieces

- **Animals** (hens, sheep, a cow or a horse) and **pen boundaries** (hurdles, a chicken run, a
  paddock rail with a gate): without them a trough or hay has nothing to serve. The Crossroads
  slice's painters (#421) are the starting point.
- **Fence corners and gates**, and a **front-garden picket**: see `crossroads_fence`.
- **A signpost for junctions** (a waystone stands in for now) and **a coop / field shelter**.

## Table

| Piece | Purpose | Role | Requires | Forbids | Verdict | Why, and what was done |
|---|---|---|---|---|---|---|
| `crossroads_anvil` | work | workplace | near forge 3 | on route | **fine** | Beside the forge. |
| `crossroads_bakery` | live | house | - | on route; on water | **fine** | A shop-home on the square; its door onto a route. |
| `crossroads_barrel` | store | store | within house 2 | on route | **fine** | By a door or a shop, never loose on a lawn. |
| `crossroads_beds_dug` | grow | garden | - | on route; on water | **redraw** | Four boarded boxes on bare earth that read as crates (Matt's Crossroads review); redraw as soil beds with crops in a dug patch, inside a garden boundary. |
| `crossroads_beds_scorched` | grow | garden | - | on route; on water | **redraw** | The burnt stage of the beds: redraw with them. |
| `crossroads_bench` | rest | seat | adjacent route_edge 2 | on route; on water | **fine** | Beside a route, facing it. |
| `crossroads_boulder` | mark | rock | - | not_overlap rock; on route | **fine** | Field stones at the village edge. |
| `crossroads_bush` | grow | shrub | - | on route; on water | **fine** | Hedges and garden shrubs. |
| `crossroads_bush_nonblocking` | grow | shrub | - | on route; on water | **fine** | Low shrubs the companion walks through. |
| `crossroads_coal` | store | store | near forge 2 | on route | **fine** | Heaped by the forge. |
| `crossroads_crater_smoke` | aftermath | clutter | - | on water | **fine** | Storm debris: only in the broken stage, under its condition (rules.stage_debris); clears as the village is restored. |
| `crossroads_crates` | store | store | within house 2 | on route | **fine** | As the barrel. |
| `crossroads_debris_a` | aftermath | clutter | - | on water | **fine** | Storm debris: only in the broken stage, under its condition (rules.stage_debris); clears as the village is restored. |
| `crossroads_debris_b` | aftermath | clutter | - | on water | **fine** | Storm debris: only in the broken stage, under its condition (rules.stage_debris); clears as the village is restored. |
| `crossroads_debris_c` | aftermath | clutter | - | on water | **fine** | Storm debris: only in the broken stage, under its condition (rules.stage_debris); clears as the village is restored. |
| `crossroads_debris_d` | aftermath | clutter | - | on water | **fine** | Storm debris: only in the broken stage, under its condition (rules.stage_debris); clears as the village is restored. |
| `crossroads_fence` | contain | boundary | - | on route; on water | **redraw** | One straight post-and-rail segment with no corner post, side run or gate, so it cannot close an enclosure (rules.fences). Redraw as runs along x and y with corner posts and a gate, in the styles placement-logic gives (wattle, hurdle, picket, rail); the Crossroads slice's painters are the model. |
| `crossroads_fern_cottage` | live | house | - | on route; on water | **fine** | A cottage on a lane. |
| `crossroads_fern_rubble` | aftermath | clutter | - | on water | **fine** | Storm debris: only in the broken stage, under its condition (rules.stage_debris); clears as the village is restored. |
| `crossroads_flower_tub` | care | planter | within house 1 | on route | **fine** | By a door. |
| `crossroads_grindstone` | work | workplace | near forge 3 | on route | **fine** | In the smithy's yard. |
| `crossroads_handcart` | store | cart | at_edge route | on route | **fine** | At a road's edge by a shop or the market. |
| `crossroads_hay` | feed | feed | within pen 1 | on route | **redraw** | Reads as pale slabs, not loose or baled hay; and like the trough it needs a pen. Redraw (the slice's hay heap is the model). |
| `crossroads_herbalist` | live | house | - | on route; on water | **fine** | A shop-home. |
| `crossroads_hut` | live | house | - | on route; on water | **fine** | The companion's hut. |
| `crossroads_kit_lantern` | light | light | at_edge route 1 | on route | **fine** | Along streets, at junctions and gates. |
| `crossroads_lantern_dark` | light | light | at_edge route 1 | on route | **fine** | As the lantern, unlit (story). |
| `crossroads_lantern_lit` | light | light | at_edge route 1 | on route | **fine** | As the lantern. |
| `crossroads_library` | live | house | - | on route; on water | **fine** | A public building on the square. |
| `crossroads_north_cottages` | live | house | - | on route; on water | **fine** | A terrace on the north lane. |
| `crossroads_notice_board` | guide | marker | at_edge route 1 | on route | **fine** | On the square, at a route's edge. |
| `crossroads_oak` | grow | tree | - | on route; on water | **fine** | The square's tree. |
| `crossroads_sacks` | store | store | within house 2 | on route | **fine** | As the barrel. |
| `crossroads_smithy` | work | forge | - | on route; on water | **fine** | The forge: the hearth anvil, coal and grindstone gather round. |
| `crossroads_smithy_rubble` | aftermath | clutter | - | on water | **fine** | Storm debris: only in the broken stage, under its condition (rules.stage_debris); clears as the village is restored. |
| `crossroads_square_puddles` | aftermath | clutter | - | on water | **fine** | Storm debris: only in the broken stage, under its condition (rules.stage_debris); clears as the village is restored. |
| `crossroads_square_rubble_a` | aftermath | clutter | - | on water | **fine** | Storm debris: only in the broken stage, under its condition (rules.stage_debris); clears as the village is restored. |
| `crossroads_square_rubble_b` | aftermath | clutter | - | on water | **fine** | Storm debris: only in the broken stage, under its condition (rules.stage_debris); clears as the village is restored. |
| `crossroads_stall` | work | stall | at_edge route | on route | **fine** | In rows on the square with aisles; its front to the route. |
| `crossroads_trough` | feed | trough | within pen 0 | on route | **missing** | A trough needs animals and a pen; the kit has neither yet (no animal pieces, no pen boundary). |
| `crossroads_waystone` | guide | marker | at_edge route 2 | - | **fine** | At a junction; points down real routes. |
| `crossroads_well` | water | centrepiece | - | on route | **fine** | Central to the square. |
| `crossroads_well_choked` | water | centrepiece | - | on route | **fine** | The storm-broken well (story stage). |
| `crossroads_woodpile` | store | store | within house 2 | on route | **fine** | Against a gable wall or under the eaves; never away from a hearth. |
| `footbridge_2` | cross | bridge | on water; adjacent route 1 | - | **fine** | Exactly where a route meets a two-cell stream, the route's width. |
| `footbridge_4` | cross | bridge | on water; adjacent route 1 | - | **fine** | As footbridge_2, over four cells. |
| `log_steps` | climb | stair | on face | - | **fine** | Where a route climbs a face; on the face, a route at head and foot. |
| `log_steps_1` | climb | stair | on face | - | **fine** | As log_steps. |
| `log_steps_3` | climb | stair | on face | - | **fine** | As log_steps. |
| `stepping_stones_1` | cross | bridge | on water; within route 1 | - | **fixed** | A footpath over a rill; its deck includes its landing stones, so the path meets it within a cell (was "adjacent", which no landing can satisfy). |
| `stepping_stones_2` | cross | bridge | on water; within route 1 | - | **fixed** | As stepping_stones_1, over a stream. |
| `waterfall_1` | flow | waterfall | on face; under water | - | **fixed** | Water crossing a rim: the sheet starts at the rim, the channel's width, foam on the pool only (2 Nov). |
| `waterfall_1_tall` | flow | waterfall | on face; under water | - | **fixed** | Water crossing a rim: the sheet starts at the rim, the channel's width, foam on the pool only (2 Nov). |
| `waterfall_2` | flow | waterfall | on face; under water | - | **fixed** | Water crossing a rim: the sheet starts at the rim, the channel's width, foam on the pool only (2 Nov). |
| `waterfall_2_tall` | flow | waterfall | on face; under water | - | **fixed** | Water crossing a rim: the sheet starts at the rim, the channel's width, foam on the pool only (2 Nov). |
| `waterfall_3` | flow | waterfall | on face; under water | - | **fixed** | Water crossing a rim: the sheet starts at the rim, the channel's width, foam on the pool only (2 Nov). |
| `waterfall_3_tall` | flow | waterfall | on face; under water | - | **fixed** | Water crossing a rim: the sheet starts at the rim, the channel's width, foam on the pool only (2 Nov). |
| `waterfall_4` | flow | waterfall | on face; under water | - | **fixed** | Water crossing a rim: the sheet starts at the rim, the channel's width, foam on the pool only (2 Nov). |
| `waterfall_4_tall` | flow | waterfall | on face; under water | - | **fixed** | Water crossing a rim: the sheet starts at the rim, the channel's width, foam on the pool only (2 Nov). |
| `woodland_beech` | grow | tree | - | on route; on water | **fine** | As the oak. |
| `woodland_birch` | grow | tree | - | on route; on water | **fine** | As the oak. |
| `woodland_boulder` | mark | rock | - | not_overlap rock; on route | **fixed** | Talus under the escarpment and bank stones; one overlapped an oak's trunk and was moved clear (2 Nov). |
| `woodland_bramble` | grow | shrub | - | on route; on water | **fine** | Thickets at the wood's edge; blocks the way like a hedge. |
| `woodland_bramble_b` | grow | shrub | - | on route; on water | **fixed** | One overlapped an oak's trunk; moved clear (2 Nov). |
| `woodland_bush` | grow | shrub | - | on route; on water | **fine** | Understorey under and between trees, at path margins. |
| `woodland_bush_b` | grow | shrub | - | on route; on water | **fixed** | One stood on the cascade's face; moved onto the raised ground (2 Nov). |
| `woodland_bush_c` | grow | shrub | - | on route; on water | **fine** | As the bush. |
| `woodland_footbridge` | cross | bridge | on water; adjacent route 1 | - | **fixed** | Its two rules.requires faults: a walkable piece now stands on its deck's cells, the water it spans (relations._deck_cells). |
| `woodland_forest_bench` | rest | seat | adjacent route_edge 2 | on route; on water | **fine** | Beside the path, facing it, at the stone ring's view. |
| `woodland_hollow_tree` | grow | tree | - | on route; on water | **fine** | A landmark tree; a creature's home in story. |
| `woodland_holly` | grow | shrub | - | on route; on water | **fine** | Understorey. |
| `woodland_holly_b` | grow | shrub | - | on route; on water | **fixed** | One crossed the zone's west edge once its solid box was restored; moved inside (2 Nov). |
| `woodland_lintel` | mark | ruin | within marker 2 | on route | **fine** | Fallen among the ring's stones. |
| `woodland_mossy_log` | rest | log | - | on route; on water | **fine** | A fallen trunk lying along the ground, a seat in a clearing. |
| `woodland_oak` | grow | tree | - | on route; on water | **fine** | Woodland and field-edge tree; never on a path or in water. Trunk box authored (2 Nov). |
| `woodland_pine` | grow | tree | - | on route; on water | **fixed** | As the oak; one's trunk stood on the rill's bank and moved a cell west (2 Nov). |
| `woodland_sapling` | grow | tree | - | on route; on water | **fine** | Young growth at a wood's edge or in a clearing. |
| `woodland_standing_stone` | mark | marker | within marker 4 | on route | **fine** | A stone of the ring. |
| `woodland_standing_stone_b` | mark | marker | within marker 4 | on route | **fine** | A stone of the ring. |
| `woodland_standing_stone_broken` | mark | marker | within marker 4 | on route | **fine** | A stone of the ring, broken. |
| `woodland_standing_stone_lean` | mark | marker | within marker 4 | on route | **fine** | A stone of the ring, leaning. |
| `woodland_standing_stone_low` | mark | marker | within marker 4 | on route | **fixed** | A stone of the ring; the east one stood on the north-south path's edge and moved a half cell clear (2 Nov). |
| `woodland_standing_stone_runes` | mark | marker | within marker 4 | on route | **fine** | The ring's rune stone. |
| `woodland_stone_sign` | guide | marker | at_edge route | on route | **fine** | A way-marker at a path; not placed yet. |
| `woodland_stone_top` | mark | ruin | within marker 3 | on route | **fine** | Fallen beside the ring. |
| `woodland_stump` | mark | stump | - | on route; on water | **fine** | Where a tree was felled: near paths and clearings, with mushrooms at its foot. |
| `woodland_willow` | grow | tree | within water 4 | on route; on water | **fixed** | Willows grow by water: requires water within 4 cells. It stood far from any water with its trunk on the east path; moved to the river's south bank (2 Nov). |
