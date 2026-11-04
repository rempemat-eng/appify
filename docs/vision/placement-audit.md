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

Totals: 150 fine, 28 fixed.

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

- ~~Animals and pen boundaries~~ (3 Nov): hens, sheep, a hen ark, a field shelter and fence cells in
  wattle and picket that close loops (`scripts/art/kit/farm.py`, `fences.py`; the loops and what they
  hold are checked by `enclosures.py`). Still missing: a cow, a horse and a paddock rail.
- ~~A signpost for junctions~~ (3 Nov): fingerposts, one per set of arms (`commons_fingerpost_*`);
  their arms must point along the routes that leave the junction (`placement.points`): the routes crossing a band 3 to 5 cells out from the post on each side.

## Placement logic beyond relations (3 Nov)

`placement_audit.check_plan` (in `--check`, over every kit zone and the village-green study) reads
four fields relations cannot express: **needs** (a tag some piece `provides` within N cells, e.g. a
woodpile needs a hearth; `side: yard` means behind the provider, so washing never hangs before the
front door), **faces** (from the piece's `facing`, a cone N cells deep must hold a feature, a view,
water or lower ground), **avoid** (`wild_woods`: three or more trees within 4 cells and no home
within 8) and **points** (a signpost's arms equal the sides on which routes leave it, read 3 to 5 cells
out, so a two-cell lane counts once; three ways or more make a junction).

## Doors, paths, gates and where fences meet buildings (4 Nov)

Matt's review of the farm study ("the placement of the fence, doors and pathways does not align"):
`thresholds.py`, run by `check_plan`, so the editor's live overlay and Validate read it too. Doors
are each building's `geometry.doors` (the opening between the frame posts, texels from the foot).
**door_path**: a path leaving a door starts centred on the opening (within a texel) and runs
straight out a cell before it bends; a door whose centre is off the half-cell grid can never have a
path of whole cells centred on it, so `houses.building` draws every door and the forge's mouth on
that grid (`houses.doors_on_grid`; the fern cottage's door and the smithy's mouth moved 2 world px
east, their frame post and boards with them). **door_clear**: nothing stands in a door's threshold and swing. **gate_path**: a gate
or a stile is centred on the path through it (a north-south run's cells centre on row lines, so its
path is an even number of cells wide). **path_through_fence**: a path crosses a boundary only at a
gate or a stile. **fence_wall**: a boundary meets a building at a front corner or along its wall
foot, its end post beside the wall, never drawn in front of the façade; a front garden is enclosed
from the house's front corners. The editor snaps a path painted from a door onto the door's centre
line and a gate onto the path crossing its run.

## Table

| Piece | Purpose | Role | Requires | Forbids | Verdict | Why, and what was done |
|---|---|---|---|---|---|---|
| `commons_bench` | rest | seat | - | on route; on water | **fine** | Facing a feature, a view, water or the land falling away (faces, 6 cells). |
| `commons_cart` | store | cart | at_edge route 1 | on route; on water | **fine** | At a road's edge, off the way. |
| `commons_chopping_block` | work | chopping_block | - | on route; on water | **fine** | Near a hearth (needs hearth 6), by the woodpile. |
| `commons_fingerpost_esw` | guide | signpost | - | on route; on water | **fine** | At a junction whose routes leave E-S-W (points). |
| `commons_fingerpost_nes` | guide | signpost | - | on route; on water | **fine** | At a junction whose routes leave N-E-S (points). |
| `commons_fingerpost_nesw` | guide | signpost | - | on route; on water | **fine** | At a junction whose routes leave N-E-S-W (points). |
| `commons_fingerpost_new` | guide | signpost | - | on route; on water | **fine** | At a junction whose routes leave N-E-W (points). |
| `commons_fingerpost_nsw` | guide | signpost | - | on route; on water | **fine** | At a junction whose routes leave N-S-W (points). |
| `commons_notice_board` | guide | marker | at_edge route 1 | on route; on water | **fine** | At a route's edge where people pass; never in wild woods. |
| `commons_pump` | water | centrepiece | near house 8 | on route; on water | **fine** | On a green near homes; a feature benches face. |
| `commons_shrine` | mark | marker | at_edge route 1 | on route; on water | **fine** | At the wayside; a feature to face. |
| `commons_stall_cloth` | work | stall | at_edge route 1 | on route; on water | **fine** | As the produce stall. |
| `commons_stall_produce` | work | stall | at_edge route 1 | on route; on water | **fine** | At a route's edge on the green or square, beside its pair. |
| `commons_washing_line` | work | washing_line | - | on route; on water | **fine** | In a house's back yard (needs home 4, yard side); never in wild woods. |
| `commons_woodpile` | store | store | - | on route; on water | **fine** | Against a house with a chimney (needs hearth 4). |
| `crossroads_anvil` | work | workplace | near forge 3 | on route | **fine** | Beside the forge. |
| `crossroads_bakery` | live | house | - | on route; on water | **fine** | A shop-home on the square; its door onto a route. |
| `crossroads_barrel` | store | store | within house 2 | on route | **fine** | By a door or a shop, never loose on a lawn. |
| `crossroads_beds_dug` | grow | garden | - | on route; on water | **fixed** | Redrawn (3 Nov, scripts/art/kit/farm.py): three soil ridges with a crop on each (cabbage, leek, lettuce; carrot, cabbage, beans) in a dug patch with a rough spade edge, no boards. Holds crops for a kitchen garden's wattle (placement.enclosure). |
| `crossroads_beds_scorched` | grow | garden | - | on route; on water | **fixed** | Redrawn with the beds (3 Nov): the same ridges burnt, crops black stubs in ash, green coming back. |
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
| `crossroads_fence` | contain | boundary | - | on route; on water | **fixed** | Retired (3 Nov): one straight post-and-rail segment could not close an enclosure. Replaced by the modular fence cells `fence_wattle_*` and `fence_picket_*` (scripts/art/kit/fences.py): straights, corners, Ts, a cross, end posts and a gate three cells wide, which close loops (enclosures.py). |
| `crossroads_fern_cottage` | live | house | - | on route; on water | **fine** | A cottage on a lane. |
| `crossroads_fern_rubble` | aftermath | clutter | - | on water | **fine** | Storm debris: only in the broken stage, under its condition (rules.stage_debris); clears as the village is restored. |
| `crossroads_flower_tub` | care | planter | within house 1 | on route | **fine** | By a door. |
| `crossroads_grindstone` | work | workplace | near forge 3 | on route | **fine** | In the smithy's yard. |
| `crossroads_handcart` | store | cart | at_edge route | on route | **fine** | At a road's edge by a shop or the market. |
| `crossroads_hay` | feed | feed | near stock 6 | on route | **fixed** | Redrawn (3 Nov): three tied bales stacked, and a heap forked out loose; placed by the animals it feeds. |
| `crossroads_herbalist` | live | house | - | on route; on water | **fine** | A shop-home. |
| `crossroads_hut` | live | house | - | on route; on water | **fine** | The companion's hut. |
| `crossroads_kit_lantern` | light | light | at_edge route 1 | on route; not_near centrepiece | **fixed** | Along streets, at junctions and gates. Props sweep (3 Nov): never on a well. |
| `crossroads_lantern_dark` | light | light | at_edge route 1 | on route; not_near centrepiece | **fixed** | As the lantern, unlit (story). |
| `crossroads_lantern_lit` | light | light | at_edge route 1 | on route; not_near centrepiece | **fixed** | As the lantern; its solid box is the plinth (was 22 world px deep up the post). |
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
| `crossroads_trough` | feed | trough | near stock 4; within boundary 4 | on route | **fixed** | The kit now has animals (`farm_sheep*`, `farm_hen_*`, role stock) and pens (the fence cells): it stands inside a fold with its flock (placement.enclosure: what sheep and horses need). |
| `crossroads_waystone` | guide | marker | at_corner route 2 | - | **fixed** | At a junction, pointing down real routes. Props sweep (3 Nov): at_corner route (was at_edge, which a straight path also met). |
| `crossroads_well` | water | centrepiece | near house 8 | on route; not_near water | **fixed** | Central to the square. Props sweep (3 Nov): requires homes within 8 cells, forbids a river within 6. |
| `crossroads_well_choked` | water | centrepiece | - | on route | **fine** | The storm-broken well (story stage). |
| `crossroads_woodpile` | store | store | within house 2 | on route | **fine** | Against a gable wall or under the eaves; never away from a hearth. |
| `farm_calf` | live | stock | within trough 14; within boundary 5 | on route; on water | **fine** | As the cow, near her. |
| `farm_churns` | store | churns | near gate 3 | on route; on water | **fine** | By a yard or paddock gate, where the cart stops. |
| `farm_coop` | live | coop | within boundary 2; near stock 4 | on route; on water | **fine** | In the run's back corner against its fence; the hens about it. |
| `farm_cow` | live | stock | within trough 14; within boundary 8 | on route; on water | **fine** | In a paddock of 10 cells or more with water and a field shelter. |
| `farm_feed_sacks` | store | sacks | near stock 8 | on route; on water | **fine** | By the stock they feed, at a shelter or coop. |
| `farm_goat` | live | stock | within shelter 8; within boundary 5 | on route; on water | **fine** | In a pen of 4 to 8 cells with a shelter and water. |
| `farm_goat_b` | live | stock | within shelter 8; within boundary 5 | on route; on water | **fine** | As the goat. |
| `farm_hen_brown` | live | stock | within coop 4; within boundary 3 | on route; on water | **fine** | As the white hen. |
| `farm_hen_speckled` | live | stock | within coop 4; within boundary 3 | on route; on water | **fine** | As the white hen. |
| `farm_hen_white` | live | stock | within coop 4; within boundary 3 | on route; on water | **fine** | In a chicken run of 3 to 4 cells, near its coop. |
| `farm_horse` | live | stock | within trough 14; within boundary 8 | on route; on water | **fine** | In a paddock of 10 cells or more with water and a field shelter. |
| `farm_muck_heap` | store | muck_heap | near stock 10 | on route; on water | **fine** | Beside the pens it is mucked out of, away from the house door. |
| `farm_pig` | live | stock | within wallow 6; within boundary 5 | on route; on water | **fine** | In the run before its sty, with a wallow and a trough. |
| `farm_scarecrow` | grow | scarecrow | within garden 3 | on route; on water | **fine** | In the crops, never on the path. |
| `farm_sheep` | live | stock | within trough 9; within boundary 5 | on route; on water | **fine** | In a fold of 6 to 10 cells with its trough and shelter. |
| `farm_sheep_graze` | live | stock | within trough 9; within boundary 5 | on route; on water | **fine** | As the sheep. |
| `farm_sheep_lie` | live | stock | within trough 9; within boundary 5 | on route; on water | **fine** | As the sheep. |
| `farm_shelter` | live | shelter | within boundary 2; near stock 8 | on route; on water | **fine** | Its back to the fold's hurdles, its open side away from the weather. |
| `farm_sty` | live | sty | near stock 6 | on route; on water | **fine** | The north wall of its pigs' run, its door and trough facing into it. |
| `farm_wallow` | live | wallow | within boundary 5 | on route; on water | **fine** | In the pigs' run, off the trodden way. |
| `farm_water_butt` | water | water_butt | adjacent house 1 | on route; on water | **fine** | Against a building, under its downpipe. |
| `farm_wheelbarrow` | work | barrow | near muck_heap 4 | on route; on water | **fine** | By the muck heap or the beds it serves. |
| `fence_picket_e` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms e): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_es` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms es): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_esw` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms esw): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_ew` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms ew): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_gate_ew` | mark | gate | on route | - | **fine** | A picket gate three cells wide, on the path its owner walks (requires on route). |
| `fence_picket_gate_ns` | mark | gate | on route | - | **fine** | A picket gate three cells wide, on the path its owner walks (requires on route). |
| `fence_picket_n` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms n): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_ne` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms ne): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_nes` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms nes): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_nesw` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms nesw): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_new` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms new): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_ns` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms ns): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_nsw` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms nsw): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_nw` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms nw): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_s` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms s): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_sw` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms sw): closes a loop with its neighbours (enclosures.py). |
| `fence_picket_w` | mark | boundary | - | on route; on water | **fine** | A picket fence cell (arms w): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_e` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms e): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_es` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms es): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_esw` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms esw): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_ew` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms ew): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_gate_ew` | contain | gate | on route | - | **fine** | A rail gate three cells wide, on the path its owner walks (requires on route). |
| `fence_rail_gate_ns` | contain | gate | on route | - | **fine** | A rail gate three cells wide, on the path its owner walks (requires on route). |
| `fence_rail_n` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms n): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_ne` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms ne): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_nes` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms nes): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_nesw` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms nesw): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_new` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms new): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_ns` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms ns): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_nsw` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms nsw): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_nw` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms nw): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_s` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms s): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_stile_ew` | contain | stile | on route | - | **fine** | Where a footpath crosses a paddock's rails: people over, stock in. |
| `fence_rail_stile_ns` | contain | stile | on route | - | **fine** | As the stile along x. |
| `fence_rail_sw` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms sw): closes a loop with its neighbours (enclosures.py). |
| `fence_rail_w` | contain | boundary | - | on route; on water | **fine** | A rail fence cell (arms w): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_e` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms e): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_es` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms es): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_esw` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms esw): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_ew` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms ew): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_gate_ew` | contain | gate | on route | - | **fine** | A wattle gate three cells wide, on the path its owner walks (requires on route). |
| `fence_wattle_gate_ns` | contain | gate | on route | - | **fine** | A wattle gate three cells wide, on the path its owner walks (requires on route). |
| `fence_wattle_n` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms n): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_ne` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms ne): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_nes` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms nes): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_nesw` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms nesw): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_new` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms new): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_ns` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms ns): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_nsw` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms nsw): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_nw` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms nw): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_s` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms s): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_sw` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms sw): closes a loop with its neighbours (enclosures.py). |
| `fence_wattle_w` | contain | boundary | - | on route; on water | **fine** | A wattle fence cell (arms w): closes a loop with its neighbours (enclosures.py). |
| `footbridge_2` | cross | bridge | on water; adjacent route 1 | - | **fine** | Exactly where a route meets a two-cell stream, the route's width. |
| `footbridge_4` | cross | bridge | on water; adjacent route 1 | - | **fine** | As footbridge_2, over four cells. |
| `garden_flower_border` | care | planter | within boundary 3; near house 6 | on route; on water | **fine** | In a front garden, beside the door path. |
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
