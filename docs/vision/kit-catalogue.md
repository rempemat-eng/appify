# World-editor kit catalogue

W0/r2, 27 October 2026. **Concept review draft. No piece in this catalogue is approved, drawn, buildable or placeable.** Claude reviews the concepts, draws accepted designs and runs the library gate. Matt approves new material and prop designs before use. This document does not change quests, rewards, progression, combat, navigation or saves.

The useful unit is a reusable **construction family**: a material with its permitted neighbours, a bank with supported water widths, a bridge with its abutments, or a building shell with a door and stage overlays. Repeating a whole picturesque scene would make the world look copied. Repeating its well-made construction parts saves work while leaving the place itself recognisable.

## Sources and authority

| Source | Revision used | What it supplies |
| --- | --- | --- |
| `docs/world-editor.md`, schema, all 98 seeded pieces, region briefs and `game/data/plans/` | `claude-a/world-editor` / #302 at `9bfc49da6c4f593b515fbd242d38e9cfca129b5b` | Editor architecture, current material/piece inventory, placement vocabulary and zone plans |
| `docs/vision/ground-rules.md`, `eastward-edges.md`, `size-guide.md`, `scripts/review/sizes.json` | Same #302 base | Physical rules, soft-grid geometry and current density-3 dimensions |
| `docs/vision/world-and-cast.md` | #290 `claude-a/progression-2` at `debdf9495bd32966e1f1b65a67a5e6964b62b743`, blob `7d35d094cfc1b47c8ef9f7fcc8c415d70b1db7ed` | Decided circle/ring-of-falls device, cast homes and clearly labelled story proposals |
| `docs/vision/progression.md` | Same #290 head, blob `06161f8903c294b412f70c7de91fadfe8f77cd04` | Services and cosmetic/forge context; unapproved weapon lines and numerical proposals stay proposals |
| `docs/vision/vertical-slice.md`, Crossroads and Undercroft plans, quest/dialogue data | #302 base | Slice priorities and actual existing hooks, rather than invented quest IDs |
| #149 packages `6444553788`, `6448405917`; W0 claim `6451045485` | 27 October | Task boundary and handoff |

The progression documents are unmerged inputs, not permission to implement their mechanics. The circle and ring of falls are decided; the distant beam's strengths, moon-repair drawings, Saddle House proposal and individual weapon lines still need their respective decisions. Source references to Eastward shots below are the repository's recorded measurements, not new image comparisons. W0 contains no art review claim.

**Units:** one logical cell = 8 world px = 24 art px at density 3. The adult is 74 art px; the scene is 960 × 540 art px. World distances stay in world units. Current density-3 class names/ranges in `sizes.json` supersede earlier density-2 sprite sizes. Cell footprint, opaque picture extent, reserved clearance and collision are different things; do not derive a solid box from an entire tree crown or door apron.

**Height conflicts need explicit representation.** The editor prototype derives a 16-world-px earth face from two cells. The art rules also call for a 12-world-px low ledge and rock cliffs of at least 32 world px. The low ledge is 1.5 cells high and is not currently represented by that whole-cell face contract. Do not round it, stretch an existing texture or import the older world plan's uniform 32-px tier assumption. Approve an explicit height model before drawing or placing it.

**Layout conflicts stay visible.** The older Neon brief describes a 14° rotated new-town grid. Current soft-grid/ground rules require cardinal cell runs. Claude must reconcile that city composition before layout engineering; W0 grants no rotated logical grid or diagonal tile system. Likewise, older regional ramp descriptions do not override the later valley/Cogsworth stair plans. A specific quay slipway needs its own authored contract rather than reviving a general ramp rule.

## What should repeat

Use a shared family when its physical construction recurs at several sites: packed earth, a bank, a fence, a canal wall, a door landing, an ordinary bench. A new palette alone is usually a variant. A different support structure, joint pattern, silhouette, depth read or placement contract can justify another family. Frost granite, desert sandstone and columnar basalt share cliff interfaces, not one recoloured wall picture.

Keep a custom assembly when the silhouette identifies a place, stages tell its story, its function depends on named characters, or its layout hosts a unique encounter. The stone circle, Shard Lantern, village service buildings, lighthouse, great bridges, boss arenas, launch installation and observatory are assemblies of shared parts with a unique plan. Their identity is never scattered through other zones as generic decoration.

The current cast and circle device use **fourteen** folk/stones. Each stone may use the reviewed stone construction, but the circle itself is one authored site. A generic waystone repeats its carving, not the full circle.

### Reuse the current seed before adding another design

The 98 seed entries are all candidates. Reuse means *review and complete them first*, not approve them by reference.

| Existing family | Actual seed IDs | Work before broad use |
| --- | --- | --- |
| Ground | `lawn`, `path`, `cobble_road`, `worn`, `scree`, `water`, `earth_face` | Gate the current painters against the hand-painted woodland and validate each intended partner |
| Natural/built edges | The twelve entries under `game/kit/pieces/transition/` | Preserve the pair graph, upper/lower ordering, border profiles, lips and side faces; no all-pairs atlas |
| Width-specific features | `log_steps`, `log_steps_1`, `log_steps_3`; `woodland_footbridge`, `footbridge_2`, `footbridge_4`; `waterfall_1`…`waterfall_4`; `stepping_stones_1`, `stepping_stones_2` | Match actual route/channel width, rise, supports and landings; do not stretch one width into another |
| Woodland props | `woodland_oak`, `woodland_beech`, `woodland_birch`, `woodland_pine`, `woodland_willow`, bushes, brambles, stones, logs and bench | W1 completes geometry; Claude confirms crowns, role and composition. Existing collision guesses are not measured truth |
| Crossroads | Seven building seeds, bench/well/stall/lamps, anvil/grindstone, beds, fences and state rubble | Keep named building and restore identity; turn dark/lit and broken/repaired pictures into explicit state variants only after source/anchor review |

## Biome packs: shared construction and custom places

Counts below are **planning estimates of distinct designs**, including materials/edges/features/props, not placement counts, PNG counts or promises. Many shared families appear in more than one row, so the rows must not be summed into a production total. A family can have several width, geology or stage drawings. Reuse existing reviewed seeds before commissioning its estimated additions.

| Region | Shared kit and why it repeats | Custom assemblies and why they stay unique | Initial pack estimate |
| --- | --- | --- | --- |
| Valley, woodland and Crossroads | Lush/dry lawn, canopy litter, packed earth, worn clearings, bank/fall/bridge/steps, oaks/birches, drystone wall, fence, bench, lamps, well, crops, domestic roof/wall/door parts. These recur in glades, farm boundaries and settlement lots | The woodland circle and hatch; forester's yard; Crossroads' terraced plan, Shard Lantern, Hale's smithy, Morel's apothecary, library, bakery and Fern cottage; Driftwood lighthouse and Headland landmark. Named services and first homecoming must remain recognisable | Start with all applicable seed families; about 10–18 additions, plus 8–12 custom assemblies across the wider valley |
| Frostline and massif | Thin snow/deep-drift boundary, exposed granite, ice shore, conifer, cairn, rope post, cold stone stair and bothy construction. Repeated exposed trails use the same safety/readability contract | Ridge col and its gate, summit lookout, Rime Wyrm lake approach; Saddle House only if the cast-fit proposal is approved. Distinct skyline and encounter geometry | 18–26 shared designs; 4–6 custom assemblies |
| Brackens | Heather/peat/grass transition, drovers' track, drystone fold, gate, trough, wind-bent shrub and marker. Repeated grazing infrastructure and moor shelves | The named drove-road junctions, lone stone ring and Iona-related site, pending story owner's precise brief. The stone ring is not a second copy of the woodland's central circle | 12–18 shared designs, with Frostline/valley reuse; 3–5 custom assemblies |
| Sunstone basin | Dry earth/scrub/sand/salt, sandstone cliffs, oasis bank and irrigation, sun-bleached timber, cactus/acacia, railhead hardware. Shared across dry approaches and settlements | Palm Spring's stopped spring/drill composition, Dust Gulch's sheriff/railhead silhouette, the Rift viaduct, the Lode and Amber canyon fossil. Infrastructure joints repeat; these locations do not | 22–30 shared designs; 5–8 custom assemblies |
| Fire country | Ash, basalt crust, lava channel boundaries, cooled rock, steam-vent surrounds, masonry stair and ironwork. Repeated volcanic geology and fortified construction | Hearthold, its two bridges and great forge; dragon/crater arena and Mount Ember steam cave. Unique supports and battle space need custom plans | 16–24 shared designs plus common cliffs; 4–7 custom assemblies |
| Tidebloom Isles and coast | Sand/wet sand/black sand, sea/shallow/reef edge, palms, tropical understory, rope/net/bollard, quay/slipway and boardwalk. Repeated shore construction; tide-pool geometry differs from a river | Lagoon Landing, Shell Bar wreck, naturalist/salvage base, Beacon Isle lighthouse and volcanic cove/boss site. A shipwreck is a readable whole hull, not scattered identical crates | 22–32 shared designs plus valley/water reuse; 5–8 custom assemblies |
| Cogsworth, coal hills, Narrows and Fernhollow | Brick/setts/slag, engineered canal, rail bed/crossing, retaining wall, gantry, pipes, coal heaps, workshop/clutter families. Rail/steam construction repeats with purpose and continuity | Foundry, station/junction, locks and major bridges, Company seam, Narrows crossing and Fernhollow composition. Larger machines need real space and supports | 24–34 shared designs; 6–9 custom assemblies |
| Lull, Lullford and Gullwick | River/mud/reed bank, towpath, mooring, barge hardware, sluice and waterside masonry. Reuse the river/coast packs; do not invent another generic water fill | Lullford swing bridge and its operating envelope; oxbow bell; specific riverside mill/port fronts. The mover's service location remains authored | 8–14 additions beyond industrial/coastal packs; 3–5 custom assemblies |
| Neon Harbour, Heights, delta and Launch Cape | Concrete, brick, metal deck, kerb/drain, conduit, facade signs, service platforms, quay edge and salt-marsh shelves. Repeated Company infrastructure has common joints and power sources | Harbour skyline, maglev terminal, courier district landmark, launch pad/service tower/fuel farm/bunker and rocket. The rocket replaces the retired space elevator; do not reintroduce its ribbon | 20–30 additions beyond industry/coast; 6–9 custom assemblies |
| Halcyon | Pressure-hull panels, hatch/airlock, cable run, service bay, docking collars, handrails and window surrounds. Shared orbital construction uses one consistent pressure boundary | Station ring and silhouette, drilling core, lander bay. Rook stays an astronaut; his proposed redesign is not settled. No new zero-gravity traversal rule follows from this pack | 12–18 shared designs; 3–4 custom assemblies |
| Lumen | Regolith, fractured crater rim, glass/stone threshold, ancient light fittings and observatory components. Share the circle's glass vocabulary, not every building shape | Observatory, its connection to the circle, crack's-heart chamber and lander pad. These close the story's spatial relationship | 10–16 shared designs; 3–5 custom assemblies |
| Undercroft-style dungeons | Flag floor, damp/chipped sibling, wall/cap/corner, pillar stump, root intrusion, grille, doorway and stair sockets. Repeated rooms require modular joints and legible collision | The actual three-room Undercroft and Thornback chamber; Cairn's wall niche and great-shard site. Boss arenas are unique layouts with proven movement/line-of-sight, not a generic circular floor decal | 14–20 shared designs; 3–5 custom room/arena assemblies per dungeon theme |

## Materials, edge partners and widths

This is a sparse **adjacency graph**. Paint only edges that the plans actually need. A new material is incomplete until every permitted meeting has a reviewed transition and every forbidden meeting fails validation. Three materials at a corner need a compatible ordered composition test; adding another fill is not enough.

| Ground/water family | Variants within the family | Width classes and edge treatment | Gate before use |
| --- | --- | --- | --- |
| Lawn and earth routes | Lush/dry/shaded ground; calm packed earth versus visibly cobbled road are separate existing materials; ruts are directional dressing | Side path 2 cells, main route 3, wide road 4+; 1-cell paths are lab/feature exceptions, not the default main route. Width changes use a taper and a named junction | Lawn–path, lawn–worn, lawn–scree, route–bank, route–face and route–built landing |
| Moor/fen/forest floor | Heather patch, peat shelf, root/litter understory; dampness stays within the local palette | Patches are cell unions; plants are organic silhouettes. Do not make a one-cell wet/dry checkerboard | Peat–water, peat–path, heather–grass; roots cannot silently turn a route into a solid collider |
| Snow and ice | Settled cover, wind-scoured exposure, compact trail, drift edge; ice is a distinct visible support/hazard decision | Trail width 2/3 cells; drift feet may dress a rim but cannot narrow an approved passage below its tested width | Snow–rock, snow–trail, snow–ice shoreline; terrain support and water depth are explicit |
| Sand/scrub/salt | Dune body, oasis damp band, salt crust; wind marks belong to local direction, not repeated zebra tiles | Shelf/canyon plan on cells; dry channels end in a declared sink; desert oasis uses width classes rather than a tiny recoloured river | Sand–earth, sand–sandstone, sand–wet bank; salt/sand transitions are regional, not all-pairs |
| Ash/basalt/lava | Cool ash, coherent crust, hot seam, active channel; basalt column cliff is a distinct face construction | Lava rill/channel/basin widths with their own edge/crust treatment; one hazard envelope authoritative for picture and collision | Cool–hot support boundary, crust–channel, vent–source; no unapproved damage values or bridge immunity |
| Constructed ground | Brick/setts, concrete, rail ballast, timber deck, metal deck | Route widths tied to destination; kerbs and drains change elevation visibly; rails require their own continuous gauge | Paving–soil, kerb–street, deck–water, rail–street crossing, hull–hatch |
| Inland water | Rill 1 cell, stream 2/3, river 4+, lake/open pool; still/flowing class must be explicit | Narrow rills use smaller rounding; every fall/bridge/stepping-stone piece matches channel width and bank tier. Pool geometry is not a widened straight channel | True source/outlet; downhill flow; north-bank face, east/west edge walls, south lip, shallow and deep treatments |
| Marine/estuarine water | Sheltered harbour, open sea, brackish reach, tidal shallows/tide pool | Share palette/shore operations, but use distinct depth, flow and shore dressing; waterline follows shore, not a row of repeated foam icons | Wet/dry shoreline envelope, mooring depth, pier support and no stranded spawn/door in any approved visual stage |
| Regolith and dungeon floor | Crater dust, compacted pad, fractured glass; flags/damp/chipped floor | Dust and floor patterns remain below prop detail scale. Rim/wall heights are measured, not inferred from a dark colour | Rim–floor, pad–dust, floor–wall, door–landing, glass–stone; no floor colour doubles as a collision mask |

Every family uses upper-left lighting, material-specific ramps, readable top/side/foot planes and source-bound shadows. Wells/barrels remain round; trees retain organic crowns; rocks have individual silhouettes. The soft grid governs terrain boundaries and placement, not a rule to square every prop. See `eastward-edges.md` 7–8 and “What the soft grid governs”. The hand-painted woodland's paths, water and crown shadows remain the minimum visual bar, even where the live preview is simpler than the baked result.

Two overlapping intake briefs have been consolidated before commissioning: sandstone/basalt faces are regional variants of `shared_rock_cliff`; the coastal and Lull/delta brackish-water briefs are one `nature_estuary_water` family. Basalt jointing follows the local geology (columns versus broken flow fronts), not a conflicting instruction to draw either stripes everywhere or plates everywhere. Water connects through the whole source/outlet network; every channel cell does not have to sit directly next to the sea.

## Proposed checks for additional biomes

These are **test specifications**, not implemented checks and not new gameplay. Names in this table are proposed diagnostics. W5/W6 and Claude agree metadata and messages before code. All fixtures must run in Python and Godot against the same exported cells and object state; no palette-colour guesses.

| Proposed check | Required metadata and exact refusal | Passing / failing fixture |
| --- | --- | --- |
| `rules.snow_support` | Every snow/drift cell has solid underlying support at the same tier; drifts may overhang visually but do not grant navigation | Drift beside a trail / drift visually bridging a cliff gap without a deck |
| `rules.drift_clearance` | Compute the walkable width after drift footprints and verify the route's declared minimum across each cross-section | Two-cell trail retained / drift consumes one of its two cells |
| `rules.ice_boundary` | Ice over water requires an explicit approved support state; visual frost alone cannot flip water to walkable | Decorative ice border outside route / spawn placed on water made pale by its texture |
| `rules.lava_source_end` | A hot flow has a declared vent/upstream seam and downhill termination at a basin, drop or zone port; its cells cannot run uphill | Vent → channel → caldera / orphan hot stripe ending in a cool floor |
| `rules.hot_crossing` | A crossing of blocked hot cells has a reviewed deck at the correct tier with supported landings and safe access on both sides | Authored chasm bridge / path painted over lava. Hazard damage remains gameplay-owner data |
| `rules.tidal_envelope` | If a site has tide states, union all blocked-water/unsafe cells and verify doors, fixed spawns and persistent escape route remain reachable in every state | Pier landing above all authored waterlines / cottage door flooded in one state. No real-time tide mechanic is added |
| `rules.rail_continuity` | Rail endpoints match position, gauge, tier and tangent at every join and zone boundary; track enters only a matching turnout or buffer/terminal | Continuous line through station / one-cell gauge shift at a seam |
| `rules.rail_crossing` | Route and track intersection requires a declared crossing; sleepers, gates and props leave the verified walking corridor open | Flush level crossing / ordinary road with a rail collider across it |
| `rules.operating_envelope` | Swing bridge, crane or service arm declares swept footprint per stage; no persistent spawn, door apron or required route lies in an unsafe envelope | Clear bridge sweep with tested closed/open access / mooring bollard inside the span's arc |
| `rules.canal_level` | Water meets the engineered bank at one tier per pound; a different level uses a real lock/drop and matched gate geometry | Two lock pounds with a gate chamber / uphill canal between equal-looking paving tiles |
| `rules.sign_mount` | Sign has a real wall/post bracket and a declared facade/power anchor where lit; its projection misses doorways, overhead clearance and route sightlines | Bracketed sign above a shop / floating neon word across a door. No automatic glow or timed animation |
| `rules.pressure_boundary` | Hull, hatch and window connect to continuous station enclosure; outside space is non-walkable absent an approved traversal mode | Closed ring corridor to an airlock / corridor floor painted across the void |
| `rules.vacuum_effects` | Exterior-vacuum volumes cannot contain open liquid-water decoration, rain, chimney smoke or wind-blown foliage; interior plants/water belong to a declared pressure volume | Tree and hydroponics inside a sealed dome / outdoor lunar rain or an exposed moon tree |
| `rules.utility_support` | Pipe/hose ends join a visible source, receiver or cap; valves have a reachable operating position; stacked cargo has supported, non-overlapping bearing footprints and correct depth order | Pump-to-trough hose and two declared supported containers / floating pipe end or unsupported upper container |
| `rules.crater_bearing` | For a homeward-scorch proposal, the authored world-space bearing points toward the valley within a reviewer-approved tolerance; local screen orientation is insufficient | Regional crater streak correctly transformed / identical east-pointing scorch in every region |
| `rules.sky_anchor` | Distant moon/beam layers have no collider or ground role, render behind the horizon, and use an authored view bearing/occlusion mask | Beam behind the far ridge / beam crosses a nearby roof or appears in a closed cellar |
| `rules.dungeon_socket` | Wall caps, corners, doors and stairs join without leaks; footprint blocks only solid wall, while each intended exit connects to its declared spawn/route | Modular room with a reachable doorway / picture of open door over a solid wall cell |
| `rules.stage_binding` | Stage switch updates appearance, footprint, interaction and existing quest condition together; an overlay cannot leave a ghost collider or stale door | Forge rubble and its collider removed together / invisible boards still block the restored smithy |

Keep existing rules unchanged: benches beside/facing routes; lamps at edges/corners/entrances; hearth-only fire; source-bound smoke; non-overlapping stones unless explicitly stacked; no clutter on route centres or in water; doors and stairs with reachable landings. Custom scenery must pass these too. An editor “custom” flag is not a validator bypass.

## Build order

| Rank | Deliverable for Claude | Why now / acceptance before the next batch |
| --- | --- | --- |
| 0 | Resolve concept-state intake and catalogue review; choose a small initial subset | No IDs, painters or world placements allocated from a speculative catalogue |
| 1 / P0 | Gate current woodland lawn/path/water/earth face, matching edges, log steps, footbridge, fall and tree shadows | Reaches Matt's preferred hand-painted bar in actual width/edge contexts; all negative placements refused |
| 2 / P0 | Complete existing woodland props and Crossroads source-derived pieces; circle/hatch, forge, Shard Lantern, well, hut/route landings and state overlays | Supports the actual first loop: woodland → village → forge → Undercroft → lantern. Keep quest/restore hooks and named anchors |
| 3 / P0 | Undercroft wall/floor/door/stair family and unique Thornback chamber | Small closed pack proves physical sockets, collision, exit reachability and custom arena composition |
| 4 / P1 | Act-1 branches: Frostline snow/rock/ice boundary and cold structures; Brackens heather/peat/drover pack; Driftwood shore/lighthouse | Extends the first region with distinct geography instead of commissioning every late-game biome |
| 5 / P2 | Cogsworth rail/canal/brick pack, Lull river infrastructure and Tidebloom shore/forest pack | Establishes reusable transport, engineered water and coast contracts before city/space variants |
| 6 / P2 | Sunstone dry/salt/oasis and fire-country basalt/hot-water/lava packs | Needs additional source/end, heat-crossing and cliff support checks; unique landmarks reviewed separately |
| 7 / P3 | Neon/Launch Cape, then Halcyon/Lumen | Reuses industry/coast where physically appropriate; pressure/void and ancient observatory construction stay distinct |

Priorities identify when a concept should be reviewed, not permission to skip its gate. Freeze a family only after a lab combines its ordinary use, awkward corners, width changes, tier ends, three-material junctions and illegal placements. A change to a shared family then requires regeneration and review of every dependent zone; unique compositions should store their dependencies so that review scope is inspectable.

## Data contract and schema dependency

Concept files live under `game/data/kit/concepts/`, outside `game/kit/pieces/`. They use the existing piece-schema vocabulary, preserve `approval.state: "concept"`, contain no PNG paths/painters/material IDs, and are not inputs to the current build. The concept namespace is not the final runtime namespace. Reuse or merge a proposal into the seed identity when reviewed rather than minting a second instance of the same bench.

Claude A's [27 October decision](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6454566919) grants W0 the one-line addition of `concept` to the schema's approval enum. That addition is included here. Its semantic validator still requires a runtime `terrain` or `transition` block for those kinds. Inventing a stable numeric material ID, a painter function or an asset path to make a pre-art idea pass would hide work that has not been done. These runtime blocks are therefore deliberately deferred; dimensions in concept geometry are proposed allocation targets, never measured art/collision. Other optional keys are left absent when not settled.

The remaining upstream request is [#149 comment 6451056103](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6451056103): keep concepts **non-buildable and non-placeable**, including in labs, and apply drawn-piece runtime-block requirements after concept review. The strict concept check still fails on the deferred runtime blocks. **Do not rename concept to candidate, weaken an approval test, or claim a full schema pass.** The PR stays draft. W0 changes only the granted schema enum; the semantic validator, library loader and editor remain with their owners. W3's separate placement refusal is recorded in [its handoff](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6454010263).

Within the closed schema, review-only descriptors that lack a dedicated field are carried in `audit.todo`: scope/shared-versus-custom, priority, purpose, visual brief, dimensions/widths, source and implementation decisions. This is a temporary authoring convention; W1 can propose structured fields/versioning with Claude. `audit.size_class` is an existing density-3 class or null with a sizing decision explained. `story` carries real source hooks or plain-language proposed hooks; no fictional quest, scene or reward IDs are installed. Relation targets such as a named hearth/socket are proposals until W5 resolves them against actual metadata. Unknown targets must fail, never become an automatic legal placement.

### Promotion after review

1. Claude accepts a concept or records changes; merge duplicate proposals into an existing seed family.
2. Schema/metadata owner assigns stable runtime IDs, concrete terrain/transition blocks and understood relation targets. The artist supplies real anchors, opaque extents, solid footprint/overhang separation and final collision. Every hook resolves to actual gameplay data, or remains a clearly unbound note.
3. Draw/bake the candidate. Compare at the 74-art-px character scale with the repository's reference shots and the hand-painted woodland; inspect silhouette, planes, material grain, lighting, shadows and seams.
4. Run schema, Python/Godot relation and round-trip tests, walk/collision checks, visual parity, asset/scene reviews and independent art review. Record the exact inputs and outputs.
5. Obtain the library/Matt approval required by `world-editor.md`, then make the piece available to production placement. No catalogue estimate grants that approval.

## Validation and handoff

The final PR records exact tested head, commands and failures. The default schema check covers the existing live library, **not this concept directory**. Existing library/kit tests demonstrate isolation and detect regressions in the unchanged kit; they do not validate speculative placements, future drawings, schema promotion or gameplay.

No art was created, no scene was changed, and no Godot/phone/visual play-test is claimed. Full `npm run verify` and `check:art-repro` remain readiness checks if this draft is later promoted under the repository policy. Schema compatibility and the art/design decisions above remain outstanding even if every structural catalogue check passes.

Reproduce the distinction between a healthy live library and the deliberately blocked concept intake:

```sh
python3 -m scripts.art.kit.schema
python3 -m unittest scripts.art.kit.test_kit
python3 -m scripts.art.kit.schema game/data/kit/concepts/*.json
```

With the enum addition the last command is expected to exit 1 for **exactly** the deliberately absent runtime blocks on the 22 terrain and 8 transition concepts; any other diagnostic is a failure to correct. All 129 records pass the structural schema. The combined catalogue audit also checks unique IDs/file stems, namespace isolation, metadata completeness, real class keys and no asset/painter/material allocation. This is a diagnostic audit, not a substitute for the future strict-schema pass.

Final source-level checks for this W0 draft: 98/98 live pieces pass their schema; the existing kit suite runs 18 tests, with 17 passing and one optional `jsonschema` parity test skipped because that package is absent. The kit reports seven materials/twelve transitions and current baked grounds. Existing unclosed-file `ResourceWarning`s are visible in that suite. The new concept audit has no unexpected diagnostics. No approved-piece gate, invalid fixture or source implementation was changed to obtain these outcomes.

## Concept index

129 review records: 97 shared construction families and 32 custom site/assembly briefs, with 332 variant briefs. A record is not necessarily one future PNG or runtime piece. The namespaces group this review, not distinct runtime libraries. Each linked JSON contains the purpose, visual brief, allowed/denied contexts, relations, clearance, orientations, stage notes, function/story hooks, size basis and unresolved implementation decisions.

### Cross-region contracts and story motifs

| Concept | Kind | Scope | Priority | Variant briefs |
| --- | --- | --- | --- | ---: |
| [Bridge abutments and landing pair](../../game/data/kit/concepts/shared_bridge_abutment.json) | structure | shared | P0 | 2 |
| [Storm damage overlay family](../../game/data/kit/concepts/shared_building_damage.json) | decal | shared | P0 | 3 |
| [Distant circle-beam sky layer](../../game/data/kit/concepts/shared_circle_beam_sky.json) | effect | shared | P1 | 3 |
| [Cracked moon sky layer](../../game/data/kit/concepts/shared_cracked_moon_sky.json) | effect | shared | P1 | 3 |
| [Homeward shard-scorch dressing](../../game/data/kit/concepts/shared_crater_scorch.json) | decal | shared | P1 | 3 |
| [Door landing and route socket](../../game/data/kit/concepts/shared_door_landing.json) | structure | shared | P0 | 3 |
| [Hearth and fire socket](../../game/data/kit/concepts/shared_hearth_socket.json) | structure | shared | P0 | 3 |
| [Low earth ledge face](../../game/data/kit/concepts/shared_low_earth_ledge.json) | tier | shared | P1 | 3 |
| [Rock cliff face family](../../game/data/kit/concepts/shared_rock_cliff.json) | tier | shared | P1 | 4 |
| [Crossroads Shard Lantern](../../game/data/kit/concepts/shared_shard_lantern.json) | prop | custom | P0 | 2 |
| [Source-bound smoke](../../game/data/kit/concepts/shared_smoke_at_source.json) | effect | shared | P0 | 2 |
| [Woodland stone circle assembly](../../game/data/kit/concepts/shared_stone_circle.json) | structure | custom | P0 | 2 |
| [Circle-carved waystone](../../game/data/kit/concepts/shared_waystone.json) | prop | shared | P0 | 2 |

### Valley, woodland, Crossroads, Frostline, Brackens and coast

| Concept | Kind | Scope | Priority | Variant briefs |
| --- | --- | --- | --- | ---: |
| [Highland conifers and wind-cut trees](../../game/data/kit/concepts/nature_alpine_conifers.json) | prop | shared | P1 | 4 |
| [Alpine turf](../../game/data/kit/concepts/nature_alpine_turf.json) | terrain | shared | P1 | 3 |
| [Shingle and tidal rock shelf](../../game/data/kit/concepts/nature_beach_shingle.json) | terrain | shared | P2 | 3 |
| [Bothy and shepherd hut family](../../game/data/kit/concepts/nature_bothy_shell.json) | structure | shared | P1 | 3 |
| [Brackens ridge stone ring](../../game/data/kit/concepts/nature_brackens_stone_ring.json) | structure | custom | P1 | 1 |
| [Coastal sand](../../game/data/kit/concepts/nature_coastal_sand.json) | terrain | shared | P2 | 3 |
| [Morel's apothecary facade](../../game/data/kit/concepts/nature_crossroads_apothecary.json) | structure | custom | P1 | 2 |
| [Hale's old smithy](../../game/data/kit/concepts/nature_crossroads_smithy.json) | structure | custom | P0 | 2 |
| [Driftwood lighthouse and lantern room](../../game/data/kit/concepts/nature_driftwood_lighthouse.json) | structure | custom | P1 | 2 |
| [Estuary, brackish channel and sheltered lagoon water](../../game/data/kit/concepts/nature_estuary_water.json) | water | shared | P2 | 5 |
| [Farm border and gate modules](../../game/data/kit/concepts/nature_field_border.json) | structure | shared | P1 | 3 |
| [Field and orchard edge dressing](../../game/data/kit/concepts/nature_field_dressing.json) | decal | shared | P1 | 3 |
| [Temperate forest floor](../../game/data/kit/concepts/nature_forest_floor.json) | terrain | shared | P0 | 3 |
| [Snowmelt Lake headwall composition](../../game/data/kit/concepts/nature_frostline_tarn_headwall.json) | structure | custom | P1 | 2 |
| [Glacier and lake ice family](../../game/data/kit/concepts/nature_glacier_ice.json) | terrain | shared | P2 | 3 |
| [Heath to meadow transition](../../game/data/kit/concepts/nature_heath_meadow_margin.json) | transition | shared | P1 | 3 |
| [Heath and peat floor](../../game/data/kit/concepts/nature_heath_peat.json) | terrain | shared | P1 | 3 |
| [Heather and gorse boundary clumps](../../game/data/kit/concepts/nature_heather_gorse.json) | prop | shared | P1 | 3 |
| [Pier and landing modules](../../game/data/kit/concepts/nature_island_pier.json) | structure | shared | P2 | 3 |
| [Woodland litter and root-edge decals](../../game/data/kit/concepts/nature_leaf_litter.json) | decal | shared | P0 | 3 |
| [Meadow sward family](../../game/data/kit/concepts/nature_meadow_sward.json) | terrain | shared | P0 | 3 |
| [Rainforest floor](../../game/data/kit/concepts/nature_rainforest_floor.json) | terrain | shared | P2 | 3 |
| [Rainforest crown and understorey family](../../game/data/kit/concepts/nature_rainforest_plants.json) | prop | shared | P2 | 4 |
| [Saddle House site study](../../game/data/kit/concepts/nature_saddle_house.json) | structure | custom | P2 | 1 |
| [Shell Bar wreck composition](../../game/data/kit/concepts/nature_shell_bar_wreck.json) | structure | custom | P2 | 1 |
| [Shore wrack and driftwood dressing](../../game/data/kit/concepts/nature_shore_wrack.json) | decal | shared | P2 | 3 |
| [Snow drift and cornice dressing](../../game/data/kit/concepts/nature_snow_drift.json) | decal | shared | P1 | 3 |
| [Snow to exposed rock transition](../../game/data/kit/concepts/nature_snow_rock_margin.json) | transition | shared | P1 | 3 |
| [Settled snow and windpack](../../game/data/kit/concepts/nature_snow_shelf.json) | terrain | shared | P1 | 3 |
| [Temperate tree family expansion](../../game/data/kit/concepts/nature_temperate_trees.json) | prop | shared | P0 | 5 |
| [Tidal pools and shallow sea pockets](../../game/data/kit/concepts/nature_tidal_pool.json) | water | shared | P2 | 3 |
| [Tidebloom giant tree landmark](../../game/data/kit/concepts/nature_tidebloom_giant_tree.json) | structure | custom | P2 | 2 |
| [Field and bed soil](../../game/data/kit/concepts/nature_tilled_soil.json) | terrain | shared | P0 | 3 |
| [Upland water family](../../game/data/kit/concepts/nature_upland_water.json) | water | shared | P0 | 5 |
| [Sleepwater mill and wheel assembly](../../game/data/kit/concepts/nature_valley_mill.json) | structure | custom | P1 | 2 |
| [Village and coastal cottage construction family](../../game/data/kit/concepts/nature_village_cottage.json) | structure | shared | P1 | 4 |
| [Wet to dry beach transition](../../game/data/kit/concepts/nature_wet_dry_beach.json) | transition | shared | P2 | 3 |
| [Woodland floor to meadow margin](../../game/data/kit/concepts/nature_wood_margin.json) | transition | shared | P0 | 3 |

### Cogsworth, river belt, Neon Harbour and Launch Cape

| Concept | Kind | Scope | Priority | Variant briefs |
| --- | --- | --- | --- | ---: |
| [Reed-channel boardwalk family](../../game/data/kit/concepts/industry_boardwalk.json) | structure | shared | P2 | 3 |
| [Mooring bollard and cleat](../../game/data/kit/concepts/industry_bollard.json) | prop | shared | P2 | 3 |
| [Built canal water class](../../game/data/kit/concepts/industry_canal_water.json) | water | shared | P2 | 3 |
| [Cargo container and stack family](../../game/data/kit/concepts/industry_cargo_container.json) | prop | shared | P3 | 3 |
| [Waterside cargo-hoist family](../../game/data/kit/concepts/industry_cargo_hoist.json) | structure | shared | P2 | 3 |
| [Coal and shale spoil surface](../../game/data/kit/concepts/industry_coal_spoil.json) | terrain | shared | P2 | 3 |
| [Cogsworth clock-tower composition](../../game/data/kit/concepts/industry_cogsworth_clock_tower.json) | structure | custom | P2 | 1 |
| [Gasworks Hill gasholder composition](../../game/data/kit/concepts/industry_cogsworth_gasholder.json) | structure | custom | P2 | 1 |
| [Concrete service-apron surface](../../game/data/kit/concepts/industry_concrete_apron.json) | terrain | shared | P3 | 3 |
| [Deep Seam pit-head composition](../../game/data/kit/concepts/industry_deep_seam_headframe.json) | structure | custom | P2 | 1 |
| [Eel trap and keeper bundle](../../game/data/kit/concepts/industry_eel_trap.json) | prop | shared | P2 | 2 |
| [Estuarine silt and exposed mudflat](../../game/data/kit/concepts/industry_estuarine_silt.json) | terrain | shared | P2 | 3 |
| [Falls Rock and paired falls composition](../../game/data/kit/concepts/industry_falls_rock.json) | structure | custom | P3 | 1 |
| [Fish-market stall family](../../game/data/kit/concepts/industry_fish_stall.json) | structure | shared | P2 | 3 |
| [Harbour Bridge and Chapel Islet composition](../../game/data/kit/concepts/industry_harbour_bridge.json) | structure | custom | P3 | 1 |
| [Heights funicular station and track composition](../../game/data/kit/concepts/industry_heights_funicular.json) | structure | custom | P3 | 2 |
| [Launch Cape pad and rocket support composition](../../game/data/kit/concepts/industry_launch_cape_pad.json) | structure | custom | P3 | 1 |
| [Canal lock-gate assembly](../../game/data/kit/concepts/industry_lock_gate.json) | structure | shared | P2 | 2 |
| [Lullford stone arches and swing span](../../game/data/kit/concepts/industry_lullford_swing_bridge.json) | structure | custom | P2 | 2 |
| [Brick and stone retaining-wall tier family](../../game/data/kit/concepts/industry_masonry_retaining.json) | tier | shared | P2 | 3 |
| [Cogsworth Millrace wheel composition](../../game/data/kit/concepts/industry_millrace_wheel.json) | structure | custom | P2 | 1 |
| [Airship mooring-mast family](../../game/data/kit/concepts/industry_mooring_mast.json) | structure | shared | P2 | 2 |
| [Narrows Viaduct composition](../../game/data/kit/concepts/industry_narrows_viaduct.json) | structure | custom | P2 | 1 |
| [Company-city sign and bracket family](../../game/data/kit/concepts/industry_neon_sign.json) | prop | shared | P3 | 3 |
| [Fishing-net drying rack](../../game/data/kit/concepts/industry_net_rack.json) | prop | shared | P2 | 3 |
| [Station-platform kerb](../../game/data/kit/concepts/industry_platform_kerb.json) | tier | shared | P2 | 2 |
| [Masonry quay and canal-bank transition](../../game/data/kit/concepts/industry_quay_edge.json) | transition | shared | P2 | 3 |
| [Quay railing and access opening](../../game/data/kit/concepts/industry_quay_railing.json) | prop | shared | P2 | 3 |
| [Rail ballast bed](../../game/data/kit/concepts/industry_rail_bed.json) | terrain | shared | P2 | 2 |
| [Pedestrian rail-crossing deck](../../game/data/kit/concepts/industry_rail_crossing.json) | structure | shared | P2 | 2 |
| [Rail run, junction and buffer modules](../../game/data/kit/concepts/industry_rail_run.json) | structure | shared | P2 | 4 |
| [Fernhollow sawpit assembly](../../game/data/kit/concepts/industry_sawpit.json) | structure | shared | P2 | 2 |
| [Exposed service pipe and valve family](../../game/data/kit/concepts/industry_service_pipe.json) | prop | shared | P2 | 3 |
| [Industrial setts and flag infills](../../game/data/kit/concepts/industry_setts.json) | terrain | shared | P2 | 3 |
| [Silt and reed-bank transition](../../game/data/kit/concepts/industry_silt_shore.json) | transition | shared | P2 | 3 |
| [Skyport terminal composition](../../game/data/kit/concepts/industry_skyport_terminal.json) | structure | custom | P3 | 1 |
| [Soot, coal-dust and runoff decals](../../game/data/kit/concepts/industry_soot_stain.json) | decal | shared | P2 | 3 |
| [Old-town terrace frontage family](../../game/data/kit/concepts/industry_terrace_frontage.json) | structure | shared | P2 | 3 |
| [Brick workshop frontage modules](../../game/data/kit/concepts/industry_workshop_frontage.json) | structure | shared | P2 | 3 |

### Sunstone, fire country, orbital/lunar and dungeon packs

| Concept | Kind | Scope | Priority | Variant briefs |
| --- | --- | --- | --- | ---: |
| [Sunstone adobe dwelling kit](../../game/data/kit/concepts/frontier_adobe_dwelling.json) | structure | shared | P2 | 3 |
| [Pressure airlock with paired thresholds](../../game/data/kit/concepts/frontier_airlock.json) | structure | shared | P3 | 2 |
| [Basalt–lava heat rim](../../game/data/kit/concepts/frontier_basalt_heat_rim.json) | transition | shared | P2 | 3 |
| [Cairn’s sleeping alcove](../../game/data/kit/concepts/frontier_cairn_alcove.json) | prop | custom | P0 | 2 |
| [Hearthold’s chasm bridge](../../game/data/kit/concepts/frontier_chasm_bridge.json) | structure | custom | P2 | 2 |
| [Halcyon’s shard-drill assembly](../../game/data/kit/concepts/frontier_company_drill.json) | structure | custom | P3 | 2 |
| [Cooled basalt paving and natural crust](../../game/data/kit/concepts/frontier_cooled_basalt.json) | terrain | shared | P2 | 3 |
| [Desert cactus family](../../game/data/kit/concepts/frontier_desert_cactus.json) | prop | shared | P2 | 3 |
| [Dry sand and travelled desert ground](../../game/data/kit/concepts/frontier_dry_sand.json) | terrain | shared | P2 | 3 |
| [Ancient doorway and stair collar](../../game/data/kit/concepts/frontier_dungeon_arch.json) | structure | shared | P0 | 2 |
| [Undercroft floor slabs](../../game/data/kit/concepts/frontier_dungeon_floor.json) | terrain | shared | P0 | 3 |
| [Undercroft wall bay and corner](../../game/data/kit/concepts/frontier_dungeon_wall.json) | structure | shared | P0 | 3 |
| [The Ember forge at the caldera lip](../../game/data/kit/concepts/frontier_ember_forge.json) | structure | custom | P2 | 2 |
| [Dust Gulch false-front shop family](../../game/data/kit/concepts/frontier_false_front.json) | structure | shared | P2 | 3 |
| [Hydroponic rack](../../game/data/kit/concepts/frontier_hydroponic_rack.json) | prop | shared | P3 | 3 |
| [Shadow-crater ice rig](../../game/data/kit/concepts/frontier_ice_rig.json) | prop | shared | P3 | 2 |
| [Active lava channel and cooling margin](../../game/data/kit/concepts/frontier_lava_run.json) | water | shared | P2 | 3 |
| [Lumen’s observatory, the circle’s twin](../../game/data/kit/concepts/frontier_lumen_observatory.json) | structure | custom | P3 | 2 |
| [Lumen’s lander pad](../../game/data/kit/concepts/frontier_lunar_landing_pad.json) | structure | custom | P3 | 2 |
| [Lunar crater rim and cut face](../../game/data/kit/concepts/frontier_lunar_rim.json) | tier | shared | P3 | 3 |
| [Supported mine-mouth family](../../game/data/kit/concepts/frontier_mine_portal.json) | structure | shared | P2 | 2 |
| [Lumen’s moon tree within the pressure dome](../../game/data/kit/concepts/frontier_moon_tree.json) | prop | custom | P3 | 2 |
| [Oasis spring pool and irrigation channel](../../game/data/kit/concepts/frontier_oasis_channel.json) | water | shared | P2 | 3 |
| [Palm Spring’s resurfacing springhead](../../game/data/kit/concepts/frontier_palm_spring_head.json) | prop | custom | P2 | 2 |
| [Station pressure bulkhead and window bay](../../game/data/kit/concepts/frontier_pressure_bulkhead.json) | structure | shared | P3 | 3 |
| [Pressure-tube span and landing](../../game/data/kit/concepts/frontier_pressure_tube.json) | structure | shared | P3 | 3 |
| [Lunar regolith and compacted pad approach](../../game/data/kit/concepts/frontier_regolith.json) | terrain | shared | P3 | 3 |
| [Regolith-covered habitat shell](../../game/data/kit/concepts/frontier_regolith_habitat.json) | structure | shared | P3 | 2 |
| [Salt-lake crust](../../game/data/kit/concepts/frontier_salt_crust.json) | terrain | shared | P2 | 2 |
| [Sand–scrub and gravel-fan transition](../../game/data/kit/concepts/frontier_sand_scrub_edge.json) | transition | shared | P2 | 2 |
| [Undercroft seal lever](../../game/data/kit/concepts/frontier_seal_lever.json) | prop | shared | P0 | 2 |
| [Undercroft seal pressure plate](../../game/data/kit/concepts/frontier_seal_plate.json) | prop | shared | P0 | 2 |
| [Undercroft’s sinking seal slab](../../game/data/kit/concepts/frontier_sealed_slab.json) | structure | custom | P0 | 2 |
| [Solar-array rack](../../game/data/kit/concepts/frontier_solar_array.json) | prop | shared | P3 | 2 |
| [Pressure-station deck and service grating](../../game/data/kit/concepts/frontier_station_deck.json) | terrain | shared | P3 | 3 |
| [Thornback chamber composition](../../game/data/kit/concepts/frontier_thornback_chamber.json) | structure | custom | P0 | 2 |
| [Vault-root intrusion and floor spread](../../game/data/kit/concepts/frontier_vault_roots.json) | decal | shared | P0 | 2 |
| [Volcanic ash and black-sand surface family](../../game/data/kit/concepts/frontier_volcanic_ash.json) | terrain | shared | P2 | 3 |
| [Windpump at well or trough](../../game/data/kit/concepts/frontier_windpump.json) | prop | shared | P2 | 2 |
