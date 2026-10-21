# World rules (v2): what the world means, and what follows from it

Matt, 18 Oct: "create some sort of protocol / system to spot visual and especially logical bugs in the world … really hone in on game fundamentals and logic and what follows in terms of world building and detail." And 20 Oct 10:58: "continue working on the logic of everything (improve the rules of the world as you build). the world should feel expansive with natural looking boundaries and no abrupt cuts".

This is the rulebook for every region generator and prop module, and for the checks that guard them. v1 (18 Oct) set the semantic layer, placement types, physics, graded paths, corridors and the bug protocol. v2 folds in what has been decided since and makes every rule checkable:

- the soft 8 px grid and side faces (`verticality.md` 4f, decided 19 Oct; `research/soft-grid.md`);
- the scale (an adult is 25 px; `verticality.md` 5) and every size in [size-guide.md](size-guide.md);
- region canvases instead of 320 x 576 zones, and the sizing of places (`world-plan.md`, decisions 1 to 7, 20 Oct);
- the prop contract and clusters (`prop-logic.md`);
- each setting's own forms and the house look at Eastward's level of detail (`art-style.md`, 20 Oct 10:15; `house-style.md`, draft PR #121: Matt approved the bottom row of its style sheet as the target for each setting at 11:20, and agreed that the moon is grey to brown-grey regolith with nearly black shadows and nothing on it is built of brick or stone);
- the continent (`world-plan.md` v3, 20 Oct, recommended and not yet decided): one world canvas, eight walkable routes, trains as shortcuts, a rocket to space, natural boundaries and wide transitions;
- the ways that open the world (`world-unlocks.md`, decided; `lib/world-ways.ts`);
- natural boundaries and no abrupt cuts (new here, section 9).

Each rule ends with the check that guards it in brackets. **Strict** means it fails the build today; **report** means a tool prints it but the build passes; **proposed** means a check is designed in a named doc but not built; **review** means only an eye catches it (the stitched region render, a line-up or the scheduled world review). The table at the end lists every check, its tool and its status. Numbers are starting points to tune in play; a size given here is the size guide's, which wins on any number.

## 1. Every pixel has a meaning

Before any art, each region is built as a **semantic layer**: every 4 px walk cell belongs to exactly one terrain class, and props, the walk grid, tap routing and decoration all read that layer. The generator records it (`zoneTerrain` in `lib/zone-maps.ts`, run-length encoded like the walk grid).

| Class                        | Code | Walk | What may stand on it                                                                   | Must border                                | Details derived from it                                             |
| ---------------------------- | ---- | ---- | -------------------------------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------- |
| Deep water                   | `~`  | no   | only **floating** props or **supported** structures (jetty, bridge, mill wheel, piles) | bank, beach, quay or bluff; never lawn     | dark band under the near bank, glints, bob on floaters              |
| Shallow water                | `-`  | no¹  | reeds, stepping stones, wading birds                                                   | deep water on one side, bank on the other  | reeds where still shallows meet a bank, ripples round stones        |
| Bank / beach                 | `,`  | yes  | wet-tolerant props (hauled-up boats, nets, driftwood, deck chairs on dry sand)         | water on one side                          | wet band, foam line                                                 |
| Face / bluff                 | `^`  | no   | nothing (roots, strata and murals are part of the face)                                | a top tier and a bottom tier               | lit lip, side bands, cast shadow down and right                     |
| Ground                       | `.`  | yes  | most ground props of the region                                                        | anything, through a band (section 9)       | darker under canopy, worn where traffic flows                       |
| Path                         | `=`  | yes  | nothing in the walking band; lamps, signs, benches beside it                           | a node at each end                         | lamps on grade-1 paths only, wear, puddles in hollows               |
| Floor / plaza                | `#`  | yes  | stalls, benches, wells, statues                                                        | paths that lead to it                      | worn centre, drains                                                 |
| Snow / sand / ash / regolith | `*`  | yes  | that region's props only                                                               | the next class on its gradient (section 9) | footprints (snow), ripples (sand), cinders (ash), tracks (regolith) |
| Lava                         | `!`  | no   | only stone bridges and supported structures                                            | a crust or ash band, never vegetation      | glow, crust at the edges; flows downhill from a vent                |
| Building                     | `B`  | no   | its own sprite                                                                         | a door facing reachable open ground        | window glow at night, smoke if a hearth is inside                   |
| Rail                         | `R`  | no²  | trains, buffers, signals                                                               | a platform at a station                    | sleepers, ballast                                                   |
| Frame                        | ` `  | no   | the sea, mountains, old forest, dunes, the void past the moon's horizon (section 9)    | the walkable land, through a band          | detail at its edge, calmer further out                              |

¹ Walkable only over a drawn ford or stepping stones. ² Crossable only at a level crossing.

1.1 Every walk cell has one class, and the classes agree with the walk grid (water, lava, faces and buildings are blocked). [world_lint classify, strict; `check:world-logic` (Codex C23), proposed]

1.2 **Being water** means three things at once: nobody stands there; anything drawn there floats or stands on drawn supports; and the water belongs to a network with a source upstream and a sink downstream (section 7). [world_lint `ground-on-water`, `stand-in-water`; source and sink, proposed]

## 2. The grid (soft grid, decided 19 Oct)

2.1 **Snap the structure, not the texture.** Every rim, side, stair, bank, path edge, wall, fence and built prop foot sits on an 8 px line. Roughness stays within 4 px of it. [terrace `rim-on-grid`, report (#90); `grid-edges` at least 80 % on the grid, `edge-jitter`, `prop-snap`, proposed (soft-grid 6.5)]

2.2 **No visible grid.** No ground texture repeats on an 8 or 16 px period. [`no-tile-repeat`, proposed]

2.3 **Straight runs and soft corners.** A straight run is at least 2 cells; corners round by one cell; a diagonal is a staircase of runs of two or more cells, never a single-cell zigzag. [`min-run`, proposed; terrace builds it this way]

2.4 **Ground shapes are rounded rectangles**, never ellipses: ponds, plazas, fields, paddocks. Built round things stay round (a well, a fountain basin, a bandstand, a stone circle, a lander pad), on a square footprint. [`no-ellipse`, proposed]

2.5 **What stays free:** trees, bushes, rocks, flowers, tufts, leaves, litter, puddles, wear, shadows, and the water line inside grid-led banks (2 px of wobble). Their base cell still checks against paths, faces, stairs and aprons. [world_lint `plant-on-path`, report]

## 3. Height

3.1 **Tiers are ground; decks are levels.** If anything walks under it, it is a deck (`two-level-walk.md`); if not, it is a tier drawn higher on screen. [review]

3.2 **Four face heights.** A face between walkable tiers is 12 or 16 (a low step: porch, boardwalk, platform), 32 (a ledge: valley, isles, west, garden yard) or 40 (city, mesa); nothing between 17 and 23; one height all round a plateau. Frame cliffs and mountains that are not walked may be taller, built as stacked tiers with ledges every 32 to 40. [terrace `face-height`, report (#90); `plateau-height`, proposed]

3.3 **On screen:** at most two full tiers and one low step; faces at most a quarter of the view's height. [review]

3.4 **Only the south face is a face.** West and east sides are 5 px bands (lit on the west, darkest tones on the east), the east side casts a constant 8 px shadow down and to the right, a north edge is a crease and the lip. Outer corners wrap, inner corners crease, and every side band ends on ground. Buildings and props show their west or east walls the same way, narrower than the front, never as a second front. [`side-width`, `side-light`, `shadow-constant`, `face-parts`, proposed; terrace draws them (#90)]

3.5 **Height changes only at a way between levels**: a stair, a ramp, a tunnel mouth, a ladder, a lift, or a fall for water. No one-way hops down low steps for now (plan decision 11). [terrace `tier-step`, report (#90)]

3.6 **Stairs sit where a path meets a face**, at least 34 open (40 standard, 48 with cheeks), with landings 8 deep clear of props at both ends, each reaching a path to a node; flights over six treads get a mid landing; the head is marked by a lamp, a post pair or a tree. [terrace `stair-width`, `stair-ends`, report (#90); `cut-on-grid`, proposed]

3.7 **Every built rim people walk beside has a railing, parapet or coping**, open over stairs; natural banks are exempt; a ledge path gets boulders or a rail. Railings are props sorted by foot, so they cover a walker's feet. [`rail-at-edge`, proposed]

3.8 **Nothing important hides behind a lower tier.** No stand, door apron or tap target on an upper tier lies under a lower-tier sprite, and no walkable upper ground is hidden for more than 40 px of depth. [`upper-hidden`, proposed]

## 4. Scale (decided 19 to 20 Oct)

4.1 **Everything is sized from a 25 px adult**, by [size-guide.md](size-guide.md): doors 32 x 14, storeys 32, shop storeys 44, counters 13, benches 32, lamps 56, crates 11, trees about 90. A prop off the guide is redrawn in its generator (taller walls, a bigger door, a lower counter), never stretched or squashed as a bitmap. [`size_check.py`, report (this file's PR); `prop-scale` for doors and storeys, proposed (`verticality.md` 5)]

4.2 **Fewer storeys, not squashed ones.** A city building has three to six storeys of 32 over a 44 shop storey; only a few landmark towers rise over a north edge where the ground behind is empty. [`size_check.py`, report]

4.3 **Things people touch are true size; buildings are compressed; landscape most** (size guide 1). A small animal may be drawn up to twice true size but never over half an adult. [`size_check.py`, report]

4.4 **The zoom stays at 12 adults across** (`ART_ACROSS` 300; plan decision 1). [`check:core` pixel-scale test, strict]

4.5 **Touch targets** are at least 44 screen px: a hit box of at least 34 x 34 art px at the prop's foot, apart from other hit boxes at standing distance. Scale fixes never shrink a hit area. [`check:garden` for the garden, strict; elsewhere proposed]

## 5. Setting, style and light

5.1 **One light, one view.** Light from the upper left everywhere (also at night, also on the moon); the three-quarter view; every prop shows its top and its front. [`style_lint.py` west minus east light, report (#121); review]

5.2 **One house look, each setting's own forms** (`house-style.md` 9). The bottom row of the house style sheet is the approved target for each setting (Matt, 20 Oct 11:20). What a setting may change: forms, materials, up to three accent families, ambient shadow depth, dressing. What never changes: the ramp rule, the outline (one pixel, the family's edge tone, the lit break), the hard terminator, shading by parts and clusters, shadows thrown down and to the right, the detail bar and no speckle. [`style_lint.py`, report (#121)]

5.3 **Materials come from the place.** The valley and the isles: dry stone, thatch, slate, hedgerows, clean and bright. Cogsworth: true brick in stretcher bond, cast iron, rivets, glass roofs, soot, steam. Sunstone Reach: sun-bleached timber, false fronts, adobe, corrugated iron, dust; Hearthold dressed stone; the fire country basalt, ash and glowing seams. Neon Harbour: concrete, glass, signage, cables, wet reflections. Halcyon and Lumen: plates with seams, hatches, radiators, antennas, footings; **nothing up there is brick, stone or timber**, and the moon's ground is grey to brown-grey regolith, airless (no violet in its shade), with cast shadows three tones down to nearly black (decided 20 Oct). [`style_lint.py` families, report; review]

5.4 **Eastward's level of detail is required.** Every surface drawn or redrawn reaches 90 % of the Eastward reference for its kind (tones, shapes and dressing per 16 x 16 patch at the same character height) and is no noisier; the PR says what it compared. [`detail_bar.py`, report (#90); review by Claude A before merging art]

5.5 **Every detail makes sense for its object** (Matt, 20 Oct 10:15 and 11:20: "dont get lazy with detail in the future, make sure the detail makes sense and looks right"): what it is, why it is there and how it is built. Bricks lie in a bond, boards are nailed at joints, moss grows in damp low joints, soot settles under eaves, snow drifts on the windward side, a lit window is lit from inside, a doorway exists only where something meets it, banners hang where they read whole, posts and beams run unbroken. A detail added only to raise a count is not allowed, and a surface that passes the bar but reads wrong at game scale goes back. [review: by eye beside a reference of the same thing at the same character height, at 3x and 1x, by day and at night]

5.6 **Readable on a phone.** Detail in clusters of two or more pixels; walkable ground calmer and lighter than what stands on it; tones 0 and 5 only on things that stand up; dither only for an atmospheric fade at a place's edge. [`style_lint.py` lone pixels and dither, report]

5.7 **Props carry no time of day.** A prop is drawn alone in the one light, with its cast shadow as its own shape, so it works on any ground and under the night tint; light sources declare their glow (`zoneWindows`, lamp pools). [review]

## 6. Props

6.1 **Every prop has a placement type** declared in its own module: `ground`, `wet`, `floating`, `supported`, `edge` or `overhead` (`PLACEMENT`; anything unlisted is `ground`). A ground prop on water or lava, a floating prop on land, or a supported structure with no drawn support is a bug. [world_lint `ground-on-water`, `ground-on-lava`, `floating-on-land`, strict]

6.2 **The prop contract** (`prop-logic.md` 2): a prop is placed only when its owner, its job, its way in (a reachable stand on the same tier), its footing and its neighbours can all be named. Nature answers "nature" and grows where it can live. [`prop-owner`, proposed; "why is this here" pass, review]

6.3 **Clusters, not scatter.** Each place of work has an anchor and its work's three points within 2 to 6 cells; 3 to 9 small props in groups of two or three, against walls and edges, one personal object per cluster; clusters of different owners at least 4 cells apart unless they share a wall. [`prop-owner`, proposed; review]

6.4 **Stores stand against something**: crates, barrels, sacks, firewood and churns within 1 cell of a wall, a stall, a cart or each other. [`store-against`, proposed]

6.5 **Footprints live on the grid** (size guide 1): a built prop declares its footprint in cells, its anchor on the foot line, its collision mask and its apron; the footprint lies on one tier, off faces, stairs, landings and lips, 1 cell back from a lip. [terrace `one_tier()`, report (#90); `prop-snap`, `prop-footprint`, proposed]

6.6 **Aprons and bands stay clear**: a door's 4 x 2 cells (a cart door's 6 x 3) on its tier with a path or worn ground leading away; a stall's customer band; a bench's front; a path's walking band; stairs, landings and a gate's line. A door never faces a wall, water, a face or a prop. [world_lint `door-shut-in`, report; `apron-clear`, proposed]

6.7 **No rows of identical props**, except what people line up (crop rows, fence posts, bollards, lamps along a street, hives along a fence, kegs on a pad), and even those vary. Neighbouring buildings never share material, roof and storeys all at once. [`prop-row`, proposed; the facade composer builds it in]

6.8 **Vehicles stand where they are used**: on rails, at a mooring, on a road or the yard road, or beside the door they serve, shafts down; never on a pavement, a plaza or a lawn. [`vehicle-on-route`, proposed]

6.9 **Nothing floats or hangs from nothing.** A sign hangs from its bracket, bunting from two posts, wires from drawn anchors; a deck lands in a doorway or on a stair and is within reach of a support. [`deck-support`, `deck-reach`, proposed (`two-level-walk.md`); review]

6.10 **Decorative interactions add no rewards, costs or chores** (AGENTS.md). Secret pockets hold a view, a resident or a story detail, never a keepsake (plan decision 10). [review]

## 7. Water

7.1 **Every water body has a source and a sink** (a spring, a fall, a culvert or snowmelt upstream; a larger water, the sea or a declared exit downstream), and flow never runs uphill. [proposed; the valley's network is drawn this way]

7.2 **Water changes tier only at a fall**: straight down the face, as wide as its channel, white at the lip, into a plunge pool 8 wider each side, a drop over 48 in tiers. Never a diagonal band over a slope. [`fall-vertical`, proposed]

7.3 **Still water is level** and sits in a hollow: a pond's rim is one height all round. [review]

7.4 **Banks by side**: a face under a grass lip on the high or outer side, a shelf of sand or gravel on the low side; a foam line at the waterline and a dark band under any face. One treatment per river, carried along its whole length. [review]

7.5 **Crossings** are bridges, fords or stepping stones at a narrow point; a bridge spans exactly the water and both ends land on a path that reaches a node. Jetties end at a boat, a ladder or a fishing spot. [proposed]

7.6 **Water is sized to what uses it** (size guide 7): a river reads as a barrier at 40 or more; a lagoon or basin where boats move is at least three boat lengths across; a beach people use is at least 75 deep. [review]

## 8. Paths and places

8.1 **Paths come in grades.** Grade 1 joins the exits and the main node and is the only lit path at night; grade 2 branches end at a door, bench, jetty, bridge, gate or stall; grade 3 is a worn desire line. Widths from the size guide (16, 24, 32 and up). [review; lamps, proposed]

8.2 **Every path ends at something**: a node, a door, a gate, a stair, a jetty, a bench facing a view, a signpost. A path into open grass is a dead end; a path into a frame is a wall. [world_lint `path-to-nowhere`, strict]

8.3 **Paths are orthogonal runs** on the grid, turning with rounded corners of 8 to 12, changing direction in dog-legs, meeting as T or Y junctions with a fillet (never an X), widening by half at doors and junctions. Trees, bushes, rocks, stumps and crops stand beside paths, never in them. [world_lint `plant-on-path`, report; review]

8.4 **An area is a small Lynch map**: one character, one landmark in its north third seen from the area before, one node of at least 48 x 48 kept mostly empty, a frame of edges that belong there, two to four vignettes. Something at the companion's scale every 5 s of walking (about 190 px). [review]

8.5 **Regions have loops and two ways in**: every region of four areas or more has a walking loop; every area and every region has two ways in except deliberate pockets. Plan v3 gives the continent four loops (valley, Canal Road, Cogsworth, Hill Path; valley, Eastern Road, Neon, Coast Path; Cogsworth, Drover's Road, Sunstone, Ember Pass; Driftwood, ferry, the isles, Shell Bar). [proposed (`check:world-routes`, Codex C27); measured on the block-outs (`stats.json`)]

8.6 **Places are sized from people** (size guide 8): a cottage plot 128 x 176, a village square 240 x 176, a farm 384 x 288, a harbour 544 x 352, a city block 208 x 272; everyday places within about 15 s of the hut's door. [review against the block-outs]

8.7 **Routes are places** (plan v3 4): a route between regions is 8 to 40 s of walking with a landmark every 5 to 10 s, a rest about halfway and a reason to exist (who uses it). Trains, the ferry and the maglev are shortcuts over routes, never the only way to a place on the continent. [proposed: a walk from the hut reaches every region on foot with all ways open]

8.8 **Density: busy cores, quiet edges.** Props are densest at doorsteps, stalls and quays, single props 4 to 6 cells out, then only nature. Streets of touching facades have a passage at least 12 wide every 120 to 200 of frontage, or the land behind is declared closed. [`row-closure`, proposed]

## 9. Boundaries: natural, never cut

The world should feel expansive, with natural boundaries and no abrupt cuts.

9.1 **No seams.** Regions are canvases, not 320 x 576 zones (plan decision 2, decided); plan v3 recommends one world canvas for the whole continent, authored in chunks (regions and routes), with Halcyon, Lumen and the hut's inside as canvases of their own. Until the new build lands, a canvas is cut into zones and everything that reaches a zone border carries on in the neighbour on the same line and width (roads, water, faces, rails, fences, hedges, treelines, ground tone). [world_lint `seam-water`, `seam-path`, `seam-tone`, `seam-lava`, strict; `tier-seam`, proposed]

9.2 **Ground changes over wide bands.** Classes meet only along the allowed-contact list: snow to alpine meadow to grass; sand to scrub to grass; lava to crust to ash to fireweed to scrub; deep water to shallows to bank to ground; regolith to dust to the habitat's apron. Each step is at least 96 px across (plan v3's steps are 120 to 370) with its edge in lobes of 16 to 48, never a straight line; unlike grounds are at least 192 apart; a whole change of biome between regions takes 700 to 1200 along its route; nothing green grows within 64 of lava. [allowed contacts, proposed (`check:world-logic`); band widths, proposed]

9.3 **Settlements sit inside their own ground**, at least a screen (300 px) from hostile ground (lava, open ice, the volcano's flank). Matt, 20 Oct: the gulch "should be entirely in the desert and the lava somewhere else". [proposed]

9.4 **Districts change at nodes, not at lines.** A change of character happens at a gate, a bridge, a square or a corridor, inside a stretch of shared character. [review]

9.5 **Corridors, not tubes.** Where districts meet, a corridor of 120 to 200 px: the walkable width 40 to 72 varying by about a third, one side open to the view for half its length, one bend, one pause (a bench, a signpost, a stile), the next landmark visible before it ends, ground and edge props blending the two. [review]

9.6 **Every boundary ends on something.** Fences, walls and hedges enclose something; each end lands on a building corner, a gate post, a corner post, a stair cheek, a face, a lamp or sign post, water, or the canvas edge where the land carries on; a ruined wall ends in fallen stones. A gate sits on the path line between heavier posts. [`fence-end`, proposed (world-references 6)]

9.7 **Forests have edges, not walls**: an interior of overlapping crowns, a front row of single trees with trunks and shadows, outliers 16 to 48 out, a floor band 20 to 40 into the meadow; trees in clumps of 3 to 7 of mixed size and species; forest stops at least one tree depth short of any shore. [review; PR #102 draws the scenery this way]

9.8 **The world's edge is sea, mountains or wilds**, never a straight cut, never canopy standing in water. Plan v3: the Northern Range closes the north (peaks drawn as frame, the volcano's black flank in the west), badlands and the sea the west, the sea the south, old forest and the sea beyond the Launch Cape the east. The sea runs to the canvas edge, deepening in bands, its last land a rocky point or a cliff with foam; mountains rise in stacked faces; wilds are frame with detail at their edge. The frame is at least 150 px deep to the east and west and 240 to the north and south, so a walker at the edge still sees the world go on. [review; frame depth, proposed]

9.9 **Views to distant land.** From every coast, land shows across the water within a screen (an island, a headland, the far shore); far landmarks show as far-scale silhouettes where a sightline allows (plan v3 5: the city's glow from the High Lookout, the gasholder and airship over the Brackens from the halt, the maglev's viaduct and the rocket from Driftwood, Dave's tower from the Eastern Road, the desert from the Ember Pass). They are drawn calmer and cooler than the near ground, are scenery only and are never tap targets. [review]

9.10 **No dead holes.** Every frame cell is drawn as something (sea, slope, canopy, void past the moon's horizon); nothing shows the canvas background. [stitched region render, review]

## 10. Living things and time

10.1 **Plants grow where they can live**: by moisture, light and soil. Reeds at still water, ferns in shade, cacti in sand, nothing green on lava or regolith (the moon tree grows inside its dome); alpine plants and pines thin with height. [region-only props, proposed; review]

10.2 **Animals stay in the place that holds them** (fold, yard, pond, wood's edge), each in its own pose and facing with a contact shadow, a group loose, never a grid. People face what they do. Life off the planet needs a pressurised habitat. [review]

10.3 **Motion anticipates, acts and settles**, is finite, is still under reduced motion and stops when its screen is inactive; at most a handful of live elements per screen; an interrupted walk never triggers a stale arrival or nap. [`check:app-active`, `check:home-lifecycle`, harness, strict for what they cover]

10.4 **The world shows time** through wear, repairs and half-finished work, and through scenery-only changes on the shared clock (lamps lit at dusk, washing on dry days, boats out in the morning), each a variant of the same footprint. [review]

## 11. The ways that open the world

11.1 **Ways are things being mended at chokepoints** (`world-unlocks.md`, decided): nine on the road (W1 to W9), each a barrier on cells with a stand on its near side; once open, open for good. Plan v3 puts each on a route (a landslip in the Millrace gorge, the Dry Wash bridge, the swing bridge, an unfuelled rocket instead of the space elevator) and opens a route and its line together. [`check:world-ways` catalogue, report (#118); `check:ways` rules (Codex C29 to C32), proposed]

11.2 **With every way closed, nothing behind it is reachable**: a flood fill from the garden and every open stop reaches no gated ground; the heart of the valley is never gated. [`check:world-ways`, report (#118), moving to cells with the region canvases]

11.3 **A barrier is drawn** (a fallen pine, a broken stile, a sand-caked wagon), believable in its place, and its open state is drawn too. [review]

## 12. Overrides and the bug protocol

12.1 **Overrides are declared.** A rule broken on purpose (the lighthouse on a rock in deep water) is listed with the zone, the object, the rule and the reason (`OVERRIDES` in `world_lint.py`). An override with no reason fails, and an override that no longer exempts anything is reported for deletion. [world_lint, strict]

12.2 **Two families of bug**, named so reviews are specific. _Visual:_ seams, palette jumps, shadows against the light, z-order errors, scale mismatches, cut-off sprites, dark holes. _Logical:_ physical impossibilities (a ground prop on water, water with no source, lava uphill), access impossibilities (an unreachable door, a bridge to nowhere, a tap target with no stand), purposeless objects (a gate in no fence, a path ending in grass, a lamp on an unlit lane), causal contradictions (a dry well beside a full trough, a hearth with no chimney, snow outside the peaks), wrong scale (a door shorter than a resident, a bench as tall as a person).

12.3 **Four stages, every time a region changes:**

1. **Lint** in the build and `npm run verify`: `world_lint.py` at the end of every `zones.py` build, plus the report tools below.
2. **Stitched region render**: `LINT_OUT=<folder> python3 scripts/art/zones.py` writes `world-lint.txt` and each region drawn whole with findings boxed, reviewed for water, roads, fences, tone and what you see from each entry edge.
3. **"Why is this here" and line-up pass**: every prop answers who, what for and how you reach it; every new or redrawn prop stands at 3x beside a resident and beside the Eastward reference.
4. **Play-test** (AGENTS.md): normal and reduced motion, day and night, interrupted walks, overlapping props, every corridor walked, every prop near water tapped.

## The checks

Tools: **world_lint** is `scripts/art/world_lint.py` (on main, run by every zones build); **terrace** is `terrace.check()` and `one_tier()` in `scripts/art/terrace.py` (draft PR #90); **detail_bar** is `scripts/art/detail_bar.py` (draft PR #90); **style_lint** is `scripts/art/style_lint.py` (draft PR #121, report only by design until the house-style migration ends); **size_check** is `scripts/art/size_check.py` (this guide's PR, report only); **world-ways** is `lib/world-ways.test.ts` as `npm run check:world-ways` (draft PR #118); Codex checks are named by their queue number in `coherence-plan.md`.

| Rule          | What is checked                                                              | Tool and check                                                              | Status today                         |
| ------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------ |
| 1.1           | each walk cell has one class that agrees with the walk grid                  | world_lint classify; `check:world-logic` (C23)                              | strict (lint); proposed (C23, #37)   |
| 1.2, 6.1      | no ground prop on water or lava, no floating prop on land                    | world_lint `ground-on-water`, `ground-on-lava`, `floating-on-land`          | strict                               |
| 1.2           | no stand in water or lava                                                    | world_lint `stand-in-water`                                                 | report                               |
| 2.1           | rims and sides on grid rows and columns                                      | terrace `rim-on-grid`                                                       | report (#90)                         |
| 2.1           | at least 80 % of boundary samples on the grid; edges within 4 px             | `grid-edges`, `edge-jitter`                                                 | proposed (soft-grid 6.5)             |
| 2.2           | no 8 or 16 px texture period                                                 | `no-tile-repeat`                                                            | proposed                             |
| 2.3           | runs at least 16 px                                                          | `min-run`                                                                   | proposed                             |
| 2.4           | no elliptical ground shapes                                                  | `no-ellipse`                                                                | proposed                             |
| 2.5, 8.3      | no plant in a path                                                           | world_lint `plant-on-path`                                                  | report                               |
| 3.2           | face heights 12, 16, 32 or 40; one height a plateau                          | terrace `face-height`; `plateau-height`                                     | report (#90); proposed               |
| 3.4           | side bands 4 to 6, lit west, dark east, 8 px shadows, complete face parts    | `side-width`, `side-light`, `shadow-constant`, `face-parts`                 | proposed                             |
| 3.5           | tiers change only at stairs or ramps                                         | terrace `tier-step`                                                         | report (#90)                         |
| 3.6           | stairs at least 34 open, landings open and reaching a node, cut on the grid  | terrace `stair-width`, `stair-ends`, `reach`; `cut-on-grid`                 | report (#90); proposed               |
| 3.7           | railings on built rims                                                       | `rail-at-edge`                                                              | proposed                             |
| 3.8           | nothing important hidden by a lower tier                                     | `upper-hidden`                                                              | proposed                             |
| 4.1 to 4.3    | sprite heights and widths within their kind's range                          | size_check                                                                  | report (this PR)                     |
| 4.1           | door and storey heights                                                      | `prop-scale` (world_lint, `KIND`, `DOOR_RECTS`, `STOREYS`)                  | proposed (`verticality.md` 5)        |
| 4.4           | the zoom (`ART_ACROSS` 300)                                                  | `lib/pixel-scale.test.ts` in `check:core`                                   | strict                               |
| 4.5           | touch targets 44 screen px, apart at standing distance                       | `check:garden` (garden); check 12 elsewhere                                 | strict (garden); proposed            |
| 5.1, 5.2, 5.6 | upper-left light, palette, outline, lone pixels, dither                      | style_lint                                                                  | report (#121)                        |
| 5.3           | setting materials (no brick or stone on the moon)                            | style_lint families; review                                                 | report (#121); review                |
| 5.4           | Eastward's detail per 16 px patch                                            | detail_bar                                                                  | report (#90); Claude A's review gate |
| 5.5, 5.7      | the drawing makes sense; no baked time of day                                | review                                                                      | review                               |
| 6.2, 6.3      | owner, job, way in; clusters                                                 | `prop-owner`                                                                | proposed (prop-logic 9)              |
| 6.4           | stores against something                                                     | `store-against`                                                             | proposed                             |
| 6.5           | footprints on the grid and on one tier                                       | terrace `one_tier()`; `prop-snap`, `prop-footprint`                         | report (#90); proposed               |
| 6.6           | door faces open ground; aprons and bands clear                               | world_lint `door-shut-in`; `apron-clear`                                    | report; proposed                     |
| 6.7           | no rows of identical props                                                   | `prop-row`                                                                  | proposed                             |
| 6.8           | vehicles on routes                                                           | `vehicle-on-route`                                                          | proposed                             |
| 6.9           | decks supported and reached                                                  | `deck-support`, `deck-reach`                                                | proposed (`two-level-walk.md`)       |
| 6.10, 11.3    | no rewards for decoration; barriers drawn                                    | review                                                                      | review                               |
| 7.1           | source and sink, no uphill flow                                              | water network check                                                         | proposed                             |
| 7.2           | falls straight down, as wide as the channel                                  | `fall-vertical`                                                             | proposed                             |
| 7.5           | bridges span water, ends land on paths                                       | bridge check                                                                | proposed                             |
| 8.2           | every path ends at a node                                                    | world_lint `path-to-nowhere`                                                | strict                               |
| 8.5           | loops and two ways into each area                                            | `check:world-routes` (C27, #43)                                             | proposed                             |
| 8.7           | every region reached on foot over routes with all ways open                  | route walk on the block-outs (`stats.json`), then on the real grid          | proposed (plan v3)                   |
| 8.8           | passages through street walls                                                | `row-closure`                                                               | proposed (`verticality.md` 4b)       |
| 9.1           | borders continue across zone seams                                           | world_lint `seam-water`, `seam-path`, `seam-tone`, `seam-lava`; `tier-seam` | strict; proposed                     |
| 9.2, 9.3      | allowed contacts, band widths, settlements away from hostile ground          | contact check (C23); band check                                             | proposed                             |
| 9.6           | every fence and wall end lands on something                                  | `fence-end`                                                                 | proposed                             |
| 9.8, 9.10     | frame depth; no dead holes at the canvas edge                                | stitched render; frame check                                                | review; proposed                     |
| 10.3          | motion finite, reduced-motion safe, stopped when inactive; no stale arrivals | `check:app-active`, `check:home-lifecycle`, harness                         | strict for what they cover           |
| 11.1, 11.2    | ways catalogue; nothing behind a closed way reachable                        | world-ways; `check:ways` (C29 to C32)                                       | report (#118); proposed              |
| 12.1          | every override has a reason and still exempts something                      | world_lint overrides                                                        | strict                               |
| All           | everything else in this file                                                 | the stitched region render, line-ups, the scheduled world review (lane R)   | review                               |

**What still needs a check most** (in order of how often reviews find it): fence ends (9.6), band widths and allowed contacts (9.2), aprons (6.6, from report to strict), `prop-scale` doors and storeys (4.1), the water network (7.1), `grid-edges` (2.1). Claude A builds them in `world_lint.py` as reports first, then strict per region as each owner clears it, as the regions went strict on 18 Oct.
