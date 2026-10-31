# Crossroads block-and-plot proposal

**Proposed A/B/C reconciliation plus partial measured Mill End / D, E and G unfitted / not adopted / not approved.** One proposed town structure for Matt to review, following [the layout study](https://chatgpt.com/library?file_id=libfile_b30bed8af740819199558691c451d410&account_id=personal). This is the seventeenth- to early nineteenth-century market/mill town, not Hearthold's medieval castle borough. It retains the current house style, soft grid, game rules and building-size requirements.

The preferred plan is a **compact market widening with connected mixed fronts, deep plots and service backs**, then a lower mill/grain quarter and two distinct goods approaches. New groups complete streets and corners around the existing gameplay core. They do not extend the rejected pattern of isolated rectangles across broad grass.

The companion [JSON](crossroads-block-plan.json) is a human-review proposal sidecar. It is not a runtime schema, adopted town plan, new validator or instruction to the producer.

[Lead amendment6533453453](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6533453453) repairs an inventory omission: retain the original forty records and add one separately labelled candidate representation of the already-authored mill programme in block F. The candidate total is **41**, within Matt's large-town range of 30–45. The previous exact-forty hold was lead accounting, not a new decision for Matt. No mill identity, geometry or terrain placement is adopted here.

## Retained facts and limits

This proposal starts from PR381 source `3818de444d24c95c50daedd6e547a78bd0436551`, after the workflow-only handoff. The preceding Granary extension remains **only a placement diagnostic**. Its requirement to preserve the failed layout's first nineteen positions belongs to that engineering experiment; it does not make those nineteen positions an approved masterplan. Here, records 1–7 remain measured gameplay anchors; records 8–40 retain their block/plot assignments. The measured A/B/C sidecar section below now supplies candidate coordinates for seven of them; other D–G and mill geometry stays null.

The durable R6 actual capture is from `87ea22a4be342e3b8009b1c9b922c2fb7db56711`; `capture.json` SHA256 is `ba68fc26d029ed85e53b4ad69feb426cf9a88ec5ea61a10d180d822be0cc5b7a`. Unchanged replay later reproduced all 15 comparisons, 49 arrays and 168 support records. That verifies the failed input, not this proposal. Its producer stopped with 19 records and IDs20–23 queued; later24–40 were not attempted.

| Fact established by saved JSON/source | Constraint on this proposal |
|---|---|
| Actual cell is 8 world px; global shape is 896 × 1568 cells. Captured consumer box is `[5632,2944,7424,4608]` px. | These bounds describe evidence coverage, not a permitted town footprint or guaranteed dry land. No new plot is declared feasible. |
| Existing gameplay zone spans `[5976,3248,6616,3808]` px. Its square is `[6176,3448,240,176]`, green `[6016,3656,168,136]`, crater `[6448,3688,72,48]` as `[x,y,w,h]`. | Keep destinations, entrances, training green and shard-crater programme. Do not use them as spare packing land or change story state. |
| The seven zone buildings have actual inherited positions and `zone_door` authority. | Preserve these anchors/doors. Their missing `form` property is real schema; use the existing registry/export authority, never fabricate it. |
| Actual Sleepwater polyline bends north/east of the core: selected centre points include `(6680,3520)`, `(6680,3616)`, `(6471,3904)` and `(6296.879,4094.489)`. | The lower river crosses the diagnostic's intended Mill End. A centreline is not a bank width, bridge proof or dry-plot mask. No bank/river is filled here. |
| Named actual routes include Valley lanes north/west/east/south/to the Lull Road and Foothill Road. Fixed zone routes include `garden_walk`, `halt_road`, `harbour_road`, `green_lane`. | Retain garden, halt, coast/valley and eastward arrivals and their identities. Exact bridge-cell joins and any new service alignment remain UNKNOWN until terrain fitting. |
| The source authors a halt yard at `[5840,4304,6080,4368]`, but execution failed before `t.yard`; captured `outskirts` is empty. | This is an unreached authored intention, not an observed usable yard. The actual station/rail global footprint was not captured. Do not assert a measured platform position. |

Native water/barrier/grade/overlap, door/access/frontage, route and exporter checks remain in force. Plot extents, depths, widths, banks, levels, crossings and the final native export window remain **UNKNOWN**. The diagram and study cannot supply them.

## One street structure

**Primary public route:** the retained garden/north arrival leads to the market widening; the southward Mill Street/valley route then continues toward the coast. The west halt approach and east harbour/Foothill/Lull approaches meet this centre. Keep their route destinations and existing closed-slice/story gates. The diagram does not open the halt or create a new traversal mechanic.

Make the existing square read as a widening along that connected route, with its well and civic/trade fronts visible. Avoid a new giant empty rectangle. The market's west side retains library, bakery and herbalist; its east side retains smithy, Fern cottage and green connections. New shop/house corners close gaps and turn the approach streets, with purposeful passages rather than a detached building in every grass patch.

**Secondary public links:** a market-west passage reaches West Lane and its garden edge; an Eastgate passage reveals the inn court; a Mill Street passage reaches the grain court and a suitable bank view. The explicit first loop is market widening → market-west passage → West Lane rear/service lane → halt approach → market widening. It returns to the town-side public approach, before the existing closed halt/slice gate, rather than ending in a private plot or passing through a closed gate. The exact gate line is not captured here and must be checked before fitting that return. Other passages may remain short destinations. Connect them to named streets where feasible. Their alignments must later avoid private plot backs, the training space, yard work faces and unsupported river crossings. No assumed new bridge is part of this proposal.

**Goods movement:** keep the halt loading approach, inn coach entrance and mill/grain delivery court distinct. A back/service lane on the halt side serves market rear courts; the eastern approach serves the inns; the lower street serves grain handling. Cart access should be visually understandable without making the well or every domestic court a loading apron. This is a spatial brief, not vehicle simulation or a new numerical clearance rule.

## Blocks and plot depth

Every plot has a street front, a service/household back, and an edge. Short frontage groups should enclose public space while still admitting real side passages. Grouped fronts do not automatically mean shared collision or permission to enable Neon's continuous-frontage checker settings for Crossroads.

| Block | Existing logical records | Front / back / edge |
|---|---|---|
| **A — Market west** | 002,004,005,035,037 (5) | Library/bakery/herbalist plus two shops form short civic/trade fronts on the widening and west approach. A rear court and halt-side back lane handle stores/deliveries; gardens follow behind. |
| **B — Market east** | 006,007,013,022,033 (5) | Smithy, Fern cottage, a shop and two houses define the harbour approach and green connection. The smithy has a working rear distinct from domestic courts; the green/crater stays open. |
| **C — Garden and north terrace** | 001,003,010,011 (4) | Retain your hut and north terrace; two additional records give the approach an inhabited edge. Garden backs stay quieter than the goods streets. Do not surround the garden with service paving. |
| **D — West Lane** | 008,009,024,025,026,027 (6) | Two row-house records make short grouped fronts, then cottage/house plots turn and taper toward the woodland. A connected rear lane reaches courts and long gardens. No blind backland house with no public entrance. |
| **E — Eastgate** | 030,031,032,034,036 (5) | Both existing inn forms remain: record031 fronts the principal coach/service court, record030 has a separate smaller inn court, and connected house/cottage fronts. Their entrances belong to the east approach, not to the rail yard. |
| **F — Mill End** | 012,014,015,016,017,018,019,020,021,023 (10 retained), plus separate candidate F11 (1) | Short house/cottage groups enclose Mill Street's junctions. Side passages reach plot courts and grain handling; candidate F11 represents the existing mill programme, with identity and geometry unresolved. Garden/farm backs soften the outer edge. The river and productive court determine fit, not a long default row. |
| **G — Halt Road fringe** | 028,029,038,039,040 (5) | A small inhabited approach with long garden/work plots leads toward the halt-related working area. Rail loading is a separate destination, with fields beyond; it is not automatically an inn stable yard. |

**Front → court/work area → garden** is a relationship, not three equal bands. Deeper plots can differ in length and combine narrow passages, paved working edges, trees, vegetable ground and household space. The outer boundary should follow real plot backs and productive land; avoid an abrupt rectangle of painted town ground.

### Conceptual relationship diagram — UNSCALED

Arrows show proposed connections, not measured direction, building polygons, travel rules or approved crossings. Letter groups refer to the block table, unchanged forty-record ledger and separate candidate mill addition.

```mermaid
flowchart TB
    N["C: retained garden / north approach"] --> M["Market widening + well"]
    H["G: halt approach / closed state retained"] --> M
    M --> E["E: Eastgate inn fronts"]
    M --> F["F: Mill Street and lower junction"]
    M --- A["A + D: short west fronts"]
    M --- B["B: trades / green-side fronts"]
    A --> R["Rear service lane + plot courts"]
    R --> V["Deep gardens / woodland fringe"]
    R -->|"town-side return; gate stays closed"| H
    B --> S["Smith working back / domestic courts"]
    E --> C["Coach court / east service entrance"]
    F --> G["Grain court / candidate mill F11"]
    G --- W["Sleepwater bank / working face UNKNOWN"]
    H --- Y["Separate halt loading / rail fit UNKNOWN"]
```

## Mill, courts, viewpoints and useful open space

A mill town needs a visible **water → mill/work face → grain handling → cart approach** relationship. Reserve that relationship below the market, using the real Sleepwater rather than a decorative pond. The handling court should be reached from Mill Street; a public bank passage/view can expose the water and work without crossing the loading face. Bank grade, hydraulic reach, candidate building identity and its exact placement remain unresolved.

**Inventory omission repaired at proposal level:** none of the retained forty records has form `mill`, but original Crossroads already authored one mill. At source3818de, `towns55.py:855–866` describes the large 30–45 market/mill town; line895 authors one mill cluster. Lines2249–2260 then show `lay_feedback` removing legacy Crossroads and substituting the replacement inventory, which omitted that programme. Its legacy cluster seed is an authored intention, not a measured building location.

The separate **F11 candidate mill** restores that existing programme without changing any of the original forty records. Record006 remains the old smithy. The sidecar keeps `count=40` for the unchanged retained ledger, `candidate_count=41` for the proposed total, and exactly one entry in `proposed_additions`; this entry has a proposal identifier, not an adopted logical building ID. There is no new occupant, job or gameplay rule.

**Identity and fit still unresolved:** the candidate mill's logical ID, legacy identity mapping, footprint, geometry, foot, door, location and plot dimensions are `null`; bank/working-face/head-and-tail reach and native fit are UNKNOWN. Main's historical web Riverside already has a `mill` object, `water_mill` sprite and `mill` stand (`scripts/art/valley_zones.py:1239–1466`), but those local coordinates do not establish placement on this continent. Resolve and deduplicate the single existing mill identity against legacy/native plans before adoption; do not create a second mill or silently convert the smithy. This revision repairs the proposed programme inventory; it does not prove a physical mill location.

The inventory also contains no dedicated stable/granary form; open service/storage courts can be proposed, but additional counted stable/granary buildings must not appear silently.

At Eastgate, the coach court is behind an inn frontage, with an entrance from the approach, working edges, room for the existing catalogue's equipment where later accepted, and a quiet public route past it. At the halt, a loading yard explains goods movement and a productive town edge. These two spaces have different reasons to exist. Their native fit is unproved.

Keep these spaces deliberately open: the well's circulation and market stopping space; training green and crater park; quiet garden approach; each separately legible work court; useful riverbank/viewing ground; gardens and fields at plot ends. Avoid treating every open patch as another house slot. View sequences should reveal the well/library from the northern approach, the market corner from the halt side, the inn court from Eastgate, and water/work from Mill Street; exact sightlines at the playing camera remain to be tested.

## Forty-record ledger

This is the unchanged source ledger of forty records, not forty placed or inhabited buildings. The separate mill candidate below makes the proposed total41, inside Matt's large-town target of 30–45. All forty existing logical IDs occur once; no candidate is inserted into or substituted for this ledger. Footprints below are retained source dimensions, **not plot dimensions or new placement coordinates**. Row-house bay data remains exact in the sidecar; its bays do not increase the forty-record count. Occupants, home/work semantics and routines are not authored here.

| Existing ID | Existing identity/form; source footprint | Proposed plot | Assignment |
|---|---|---|---|
| `crossroads-b001` | Your hut; 80 × 40 px | C01 | Your hut; identity retained |
| `crossroads-b002` | Library (roof torn); 96 × 40 px | A01 | Library (roof torn); identity retained |
| `crossroads-b003` | North terrace cottages; 96 × 40 px | C02 | North terrace cottages; identity retained |
| `crossroads-b004` | Bakery (cold); 72 × 48 px | A02 | Bakery (cold); identity retained |
| `crossroads-b005` | Herbalist's (apothecary, stage 1); 72 × 48 px | A03 | Herbalist's (apothecary, stage 1); identity retained |
| `crossroads-b006` | The old smithy; 88 × 56 px | B01 | The old smithy; identity retained |
| `crossroads-b007` | The Ferns' cottage; 72 × 48 px | B02 | The Ferns' cottage; identity retained |
| `crossroads-b008` | row_house; 80 × 24 px | D01 | Grouped market-west approach frontage; both original bays retained |
| `crossroads-b009` | row_house; 112 × 48 px | D02 | Turn West Lane court with a second grouped frontage; both bays retained |
| `crossroads-b010` | cottage; 48 × 72 px | C03 | Frame the garden-to-market arrival without occupying the quiet garden |
| `crossroads-b011` | house; 56 × 88 px | C04 | Turn the north terrace approach toward the square |
| `crossroads-b012` | cottage; 48 × 64 px | F01 | Define the upper Mill End junction frontage |
| `crossroads-b013` | shop; 48 × 88 px | B03 | Connect the market to the trades-side passage with a shop front |
| `crossroads-b014` | cottage; 40 × 72 px | F02 | Continue a short Mill Street frontage group |
| `crossroads-b015` | house; 64 × 96 px | F03 | Turn the Mill End street-to-court corner |
| `crossroads-b016` | cottage; 48 × 56 px | F04 | Face the street beside the grain-court approach |
| `crossroads-b017` | house; 56 × 88 px | F05 | Define the lower Mill Street junction |
| `crossroads-b018` | cottage; 40 × 64 px | F06 | Connect a small court frontage to garden backs |
| `crossroads-b019` | cottage; 64 × 40 px | F07 | Enclose the public-facing side of a lower plot court |
| `crossroads-b020` | cottage; 64 × 48 px | F08 | Turn the passage into the lower plot group |
| `crossroads-b021` | cottage; 64 × 40 px | F09 | Front a garden-edge lane within Mill End |
| `crossroads-b022` | house; 88 × 48 px | B04 | Give the harbour approach a connected house front |
| `crossroads-b023` | cottage; 72 × 40 px | F10 | End a short Mill End frontage at productive plots |
| `crossroads-b024` | cottage; 40 × 72 px | D03 | Front a West Lane court with a deep garden behind |
| `crossroads-b025` | house; 56 × 96 px | D04 | Turn the west market/service-lane entrance corner |
| `crossroads-b026` | cottage; 40 × 56 px | D05 | Continue the West Lane plot frontage toward woodland |
| `crossroads-b027` | cottage; 40 × 64 px | D06 | End the grouped West Lane frontage before garden plots |
| `crossroads-b028` | house; 56 × 96 px | G01 | Mark the halt approach corner facing the market link |
| `crossroads-b029` | cottage; 48 × 72 px | G02 | Front a deep garden plot on Halt Road |
| `crossroads-b030` | inn; 72 × 128 px | E01 | Secondary inn frontage with its own smaller service court |
| `crossroads-b031` | inn; 128 × 72 px | E02 | Principal coach-inn wide frontage with the main coach/service court behind |
| `crossroads-b032` | house; 48 × 88 px | E03 | Connect the inn frontages with a house-form plot |
| `crossroads-b033` | house; 96 × 56 px | B05 | Turn the market-east corner with a house-form frontage |
| `crossroads-b034` | cottage; 72 × 48 px | E04 | Turn the Eastgate court approach with a cottage-form plot |
| `crossroads-b035` | shop; 64 × 56 px | A04 | Close the west approach corner with an existing shop form |
| `crossroads-b036` | cottage; 80 × 48 px | E05 | Extend an inhabited Eastgate approach with a garden-backed plot |
| `crossroads-b037` | shop; 48 × 64 px | A05 | Define the market-widening edge with the second added shop form |
| `crossroads-b038` | cottage; 56 × 48 px | G03 | Join the short Halt Road frontage group |
| `crossroads-b039` | cottage; 64 × 48 px | G04 | Turn the halt-side group toward garden plots |
| `crossroads-b040` | cottage; 56 × 40 px | G05 | End the halt-side frontage at the productive fringe |

## Separate proposed addition: the existing mill programme

| Proposal | Count / block | Relationship | Identity and geometry |
|---|---|---|---|
| `crossroads-mill-candidate` | 1 / F11 in Mill End; candidate town total41 | Sleepwater working face → mill → grain handling → Mill Street goods approach | Proposed representation only. Logical ID, legacy identity mapping, geometry, coordinates, footprint, plot dimensions, foot, door and location are `null`; orientation unassigned and terrain/water reach UNKNOWN. |

All forty retained records, their source forms/footprints/bays, seven measured gameplay anchors and old smithy remain unchanged. F11 is a plot label in an unscaled proposal, not a measured polygon or an extra adopted mill.


## Measured market-quarter candidate — partial fit

This first flat plan measures **A/B/C only** against the real saved BEFORE crop, retaining all seven native anchor rectangles and doors. Fourteen records are shown: seven anchors and seven candidate buildings. D/E/F/G and the separate mill remain unplaced. The original forty-record ledger and candidate total41 are unchanged. The sidecar's `measured_market_fit` section is proposal evidence, not a runtime schema or adoption packet.

The west approach gains two south-facing shops, a24px public lane into the square, and a16px passage between them to a rear service lane. Garden backs follow the protected woodland edge. North homes face the existing garden walk and a quiet16px spur, with side gardens; they do not turn the garden into a loading yard. An east shop faces the native harbour road, and a house turns the northern arrival. A dashed alternative house closes the south-east market return. The native market, green, crater and garden stair stay recognisable and open.

| Candidate | World rectangle x,y,w,h | Door | Actual footprint evidence / disposition |
|---|---|---|---|
| `crossroads-b010` / C03 | `[6184, 3232, 48, 72]` | `[6208, 3304]` | barrier0, keepout0, literalpath0; tiers[3, 3]; MEASURED_DRY_CANDIDATE_NATIVE_FIT_UNPROVEN |
| `crossroads-b011` / C04 | `[6352, 3240, 56, 88]` | `[6384, 3328]` | barrier0, keepout0, literalpath0; tiers[3, 3]; MEASURED_DRY_CANDIDATE_NATIVE_FIT_UNPROVEN |
| `crossroads-b013` / B03 | `[6552, 3472, 48, 88]` | `[6576, 3560]` | barrier0, keepout0, literalpath1; tiers[3, 4]; CONDITIONAL_LITERAL_PATH_CONFLICT |
| `crossroads-b022` / B04 | `[6320, 3640, 88, 48]` | `[6368, 3640]` | barrier3, keepout2, literalpath0; tiers[3, 3]; CONDITIONAL_BARRIER_KEEPOUT_CONFLICT |
| `crossroads-b033` / B05 | `[6528, 3336, 96, 56]` | `[6576, 3392]` | barrier0, keepout0, literalpath0; tiers[4, 5]; MEASURED_DRY_CANDIDATE_NATIVE_FIT_UNPROVEN |
| `crossroads-b035` / A04 | `[6096, 3408, 64, 56]` | `[6128, 3464]` | barrier0, keepout0, literalpath0; tiers[3, 3]; MEASURED_DRY_CANDIDATE_NATIVE_FIT_UNPROVEN |
| `crossroads-b037` / A05 | `[6032, 3400, 48, 64]` | `[6056, 3464]` | barrier0, keepout0, literalpath0; tiers[3, 4]; MEASURED_DRY_CANDIDATE_NATIVE_FIT_UNPROVEN |

All fourteen footprint rectangles are pairwise disjoint, and original ordered dimensions are retained. Rectangles/area boundaries use8px world cells; inherited bakery/herbalist doors at x6148 are kept exactly. Cell masks and one-cell halos are recorded separately for every record. Five new footprints have no literal path, barrier, keepout, street or taken conflict. That is a useful measured offer, **not native acceptance**: inherited overview building paint still needs identity reconciliation, two candidates require coherent terracing, native floor/collider/door checks are unrun, and nominal route width/door contacts need later checking.

**The two east/return candidates remain conditional.** Shop013 was deliberately moved8px south to front the native harbour street edge, reducing six literal-path cells to one; the remaining cell is not ignored because `street` happens to be false. House022 was moved from the narrow Lull-side strip to a south-east market return. Its new footprint contains3barrier/2keepout cells, so it is drawn dashed rather than accepted. No density packing, footprint shrinking, terrain filling or manual-placement bypass was used to turn these into passes.

**Existing native/macro conflicts also remain visible.** Ferns cottage007 intersects43 of54 macro keepout cells,9barrier cells and5crater-mask cells, including four shardglass and one scorch cell. Its native rectangle ends3664; the native crater rectangle starts3688,24px lower. The explicit macro crater centre is6484,3712, bowl radius36 (`geo53.py44–47,130–174`), with a broader90px protection disc (`geo55.py847–848`). Separately, saved macro north/west centrelines cut the fixed hut/herbalist footprints despite the native garden/halt routes. Fixed anchors are not moved to conceal those mismatches.

The **unapplied reconciliation proposal** is to fit the procedural crater rim/scorch/protection coherently around the unchanged native cottage, crater bowl/centre/story and park approach, and align local macro arrivals with the existing native garden/stair and halt-road axes while preserving outer route joins and the closed halt. This requires actual ground, masks, tiers, route widths, doors and access to agree. It is not permission to punch holes in keepouts or erase paths. No such change has been applied; the flat plan overlays candidates on the original terrain, with conflicts highlighted.

The north house's first candidate hit six protected north-disc cells; shifting it32px south makes it face the quiet spur and leaves its final footprint/halo clear. The initial west garden band touched13protected woodland-edge cells, so its boundary stops8px farther south. These deliberate design revisions and earlier measurements are retained in the evidence packet; protected cells were not cleared.

The next scope is one coherent terrain/route reconciliation and native authoring test for this market quarter, followed by the two conditional frontages. It must preserve all seven anchors, names and story states and cannot use `Town.free`'s manual grade/barrier bypass as acceptance. Cap40/expected40 in the frozen producer remain unchanged; later adoption of the legitimate41-building candidate must reconcile them explicitly. No D–G/mill fit, whole-world generation, native placement/export/checker, camera/art/Y12/Ready/merge or Matt approval is claimed.

GO6533855827 / ASSIGN6533865862 / ACK6533866313. Actual cropped stdlib probes remained below64MiB/30seconds/4MiB, with unchanged source input hashes. The accompanying actual-cell flat SVG is the reviewable geometry offer; it is not finished game art.


## Current reconciliation offer — actual BEFORE versus proposed copied crop

The previous partial frame above is retained as evidence. The current candidate is the sidecar's `market_reconciliation` section: **one coherent A/B/C ground, road, park and frontage proposal**, evaluated only on a private copy of the actual208×224crop. The actual BEFORE archive is unchanged. This is a geometry offer for review, not native placement, finished art or a corrected whole world.

The two formerly conditional B plots now belong to a connected street structure. Shop013 keeps its south door directly on the north edge of harbour road. House022 moves to `[6520,3592,88,48]` across that road, making an opposing domestic frontage and a16px side close beside Ferns. Its north-facing facade is a required future asset variant, **not demonstrated existing art**. House011 moves8px east to `[6360,3240,56,88]`; the24px north approach can then pass east of the fixed hut on dry ground. The woodland garden walk bends below the hut instead of using the creek-cut western slot. Source IDs, ordered dimensions and all seven fixed rectangles/doors remain unchanged.

Five named local road legs use deliberate routes to exact old in-crop join points, retaining every subsequent original point. West traffic follows the existing halt-road axis along the green's western edge, joining the old road before its existing creek crossing. East/Lull arrivals share harbour road and a bank street before branching to the old crossings. The south leg follows the market perimeter. All avoid the native conditional well rectangle `[6254,3552,20,16]`; no well state or reward rule changes. The fixed garden stair remains on the native axis. D/E/F/G and the mill are not fitted by these local joins.

The park is reshaped **as a whole feature**. Crater centre6484,3712, nominal horizontal bowl radius36 and homeward story/bearing remain. The vertical bowl projection deliberately changes from source0.86×36=30.96 to the native-authored24px half-height. The proposed side rim has radii56×24, and the homeward scorch is shortened from129.6 to32px within that park. A declared park polygon replaces the old90px protection disc; the original woodland/north/east/circle protections remain. This is an explicit terrain projection change, not a claim that old contours/pixels are unchanged and not a house-shaped keepout hole. The **unchanged one-cell barrier dilation is recomputed from the complete proposed physical hazards**. The16px Ferns front path then clears that guard while retaining its original door and crater centre/story.

Two declared16px terraced aprons join the new B house foundations to surrounding grades. The first copied proposal left two slopes above0.016; those measurements remain in the packet. The revision changes the planned ground/aprons rather than weakening the threshold. Original native tier/stair source bytes are untouched; these are macro terrace proposals, not a proven native floor conversion.

| Measured copied-crop result | Actual result and limit |
|---|---|
| Fourteen footprints | All0water/nonbuildable/barrier/keepout/street/other occupancy; each uniform macro tier; maximum slope0.013223 against unchanged0.016. |
| Their one-cell halos | All0water/barrier/keepout/other occupancy. Frontage streets and some mixed-tier aprons remain intentionally present; halos are not claimed street-free or uniform. |
| Door links | All14 adjacent door links reach the native square in a limited four-neighbour explicit-street diagnostic, with the well conservatively reserved. Native navigation/collision/interaction checks remain unrun. |
| Changed road prefixes | All five0newwater/barrier/keepout/building intersections. No creek was filled and no new bridge invented. |
| Retained road tails | Exact old points retained.22North keepout cells,7Lull keepout cells and existing bridge-abutment guard cells remain unresolved; no whole-route pass follows. |
| Actual inputs and outside patch | All6 input hashes unchanged. All49 typed channel bytes outside `[5920,3184,6800,3840)` match their original hashes. All river masks, land and closed-state fields remain exact. |
| Proposed copy |4,589 distinct cells differ inside the declared support; affected-cell CSV and per-channel before/after/outside hashes are retained. The proposal changes ground, crater, barriers, keepouts, terraces, streets and occupancy coherently. |

The earlier negative offers are preserved: six protected cells under the first northern house; protected woodland garden-edge cells; the two copied-foundation slope residuals; and the later two-creek-cell north approach. The final north route uses the opposite side of the hut instead of adding a bridge or erasing drainage. No coordinate search, density packing, footprint shrink, manual-placement bypass or production generator change was used.

Review the actual-before/proposed-copy comparison for the street enclosure, back courts, gardens, arrival sequence and park edge. The next executable scope is explicit producer/native-plan adoption of the reviewed geometry, followed by the existing validators and editor use. It still needs original route-tail/portal/bridge authority, native floor and collider checks, facade variants and art review. The frozen producer's40count remains unchanged until deliberate adoption of the legitimate41-building town candidate. No Matt permission is needed for this authorised proposal iteration; final art/map merge approval remains Matt's on the PR.

GO6534840357 / ASSIGN6534876710 / ACK6534877050. The final copied probe exited0 in1.937seconds/peak53,985,280bytes under oneCPU/256MiB/60seconds/output8MiB. It never imported project code, invoked an engine/packer/painter, changed the original capture or wrote production terrain.

## Review and next scope

The concrete choice is the seven-block arrangement above: a connected market core, west rear-service plots, Eastgate coach courts, a lower water/work quarter and a productive halt fringe, retaining the seven gameplay anchors. The omitted mill programme now has one explicit candidate representation, authorised as routine inventory repair by lead6533453453. Its identity mapping and physical fit remain unresolved. Exact plots/crossings/rail fit are later measured work, not requests for physics exceptions. Matt's applicable review of the town composition and explicit PR approval before any art/map merge remain required.

After lead/Matt reviews this structure, a separately scoped terrain-fitting step can draw actual frontage/plot boundaries against saved masks and the full route context, adjusting suitable land only where explicitly authorised. It must keep the river's meaningful upstream/downstream joins, valid crossings, existing gameplay zone and named destinations. If the required support leaves the current captured bounds, report the missing area rather than make UNKNOWN ground buildable.

Then use the existing native placement/export/checker on the newly scoped plan, accounting for all forty original IDs, the single deduplicated mill candidate, original inherited doors, terrain, fronts/rears, service yards and routes. That physical result would still not approve the composition or art. One representative street and working-court vignette at the actual character/play-camera scale should establish construction, material, contact-shadow and circulation quality before kit expansion or whole-town claims.

No production producer/helper/checker/terrain/workflow or generated game-art image was changed. This step created the two proposal documents, outside-Git copied-crop comparison evidence, and a flat SVG/PNG presentation using the existing Sharp renderer. No packing, project test, scientific import, controller, engine, game-art rendering, world generation, job, Ready, merge or art approval occurred. PR381's original failure, unchanged replay and diagnostic PNG remain preserved; the existing Granary candidate is not offered as a finished Crossroads.

### Evidence references

- [Mill inventory amendment6533453453](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6533453453), [repair claim6533485058](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6533485058) and [separate ACK6533489951](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6533489951).
- [Matt layout direction6526956297](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6526956297), [study handoff6527386266](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6527386266), [two-file scope6527523659](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6527523659).
- [Workflow-only source handoff6527830649](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6527830649); exact producer inventory blob `f23c793baf4a3b937a223c2a9fd2ac2786442f94` at parent3818de.
- [Actual unchanged replay/failed-state result6525128251](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6525128251). Input `before.npz` SHA256 `95574230bb4474fa3a931ba6167fa521d609107ae79fff3f7e7022e327d7d527`; zone JSON SHA256 `cee996a1d28ce4e3523eca541522aae3e05c61c59252496b7aa9eeb334487dec`. These hashes identify evidence; they do not certify this proposed geometry.


## Mill End: ten measured homes and a conditional mill offer

This extension fits one district, **F**, against the retained r3 private copy. The completed A/B/C offer remains unchanged. The new geometry is in `mill_end_fit`; the original forty-record ledger and separate mill entry are still factual source records, with their unresolved adoption fields untouched. These are proposed structures and plots on a copied macro crop, not houses placed in the native game.

The real drainage determines the choice. The initial upper cottage site cut three river cells, and the first mill halo reached water and its physical guard. The dry west-bank alternative still contained 25 literal path cells on the existing south-road approach, so it was not promoted as a working mill. The current proposal uses the **east bank below the confluence**: the mill faces west toward Sleepwater, its goods entrance faces east into a distinct grain court, and a short Grain Close separates this working group from the domestic street. No new crossing is assumed. Mill Street reaches the existing Lull-road endpoint on the same bank; the completed south road, original route polylines and all captured water/bridge cells remain unchanged.

At the upper approach, two cottages and two opposing houses/cottages form a short street rather than a field of detached markers. The street then bends toward the mill and continues as a domestic lane, with varied but aligned fronts, side access, rear gardens and retained woodland at the outer edge. The grain court has a separate handling face and an approach from the street; the real river remains visible behind the mill. Existing fields and woodland are cleared only in the declared plots, gardens and circulation support. All heights, tiers, slopes, barriers, crater and protection masks retain the r3 values: there is no broad dry-floor replacement or individual keepout hole in this offer.

| Plot / original record | Proposed rectangle `[x,y,w,h]`, world px | Required door face | Measured disposition |
|---|---|---|---|
| F01 / 012 | `[6656, 3856, 48, 64]` | south | Footprint and one-cell halo clear in copied macro data; native floor/art fit unverified. |
| F02 / 014 | `[6728, 3848, 40, 72]` | south | Footprint and one-cell halo clear in copied macro data; native floor/art fit unverified. |
| F03 / 015 | `[6560, 3968, 64, 96]` | north | Footprint and one-cell halo clear in copied macro data; native floor/art fit unverified. |
| F04 / 016 | `[6656, 3968, 48, 56]` | north | Footprint and one-cell halo clear in copied macro data; native floor/art fit unverified. |
| F05 / 017 | `[6520, 4080, 56, 88]` | west | Footprint and one-cell halo clear in copied macro data; native floor/art fit unverified. |
| F06 / 018 | `[6424, 4000, 40, 64]` | east | Footprint and one-cell halo clear in copied macro data; native floor/art fit unverified. |
| F07 / 019 | `[6520, 4208, 64, 40]` | west | Footprint and one-cell halo clear in copied macro data; native floor/art fit unverified. |
| F08 / 020 | `[6392, 4240, 64, 48]` | east | Footprint and one-cell halo clear in copied macro data; native floor/art fit unverified. |
| F09 / 021 | `[6520, 4280, 64, 40]` | west | Footprint and one-cell halo clear in copied macro data; native floor/art fit unverified. |
| F10 / 023 | `[6344, 4048, 72, 40]` | south | Footprint and one-cell halo clear in copied macro data; native floor/art fit unverified. |
| F11 / separate mill candidate | `[6344, 4128, 96, 64]` | east | Conditional: 2 approach-street cells inside footprint; 16–24 px bank gap is not hydraulic proof. |

The ten homes have **zero water, nonbuildable, barrier, keepout, street or other-occupancy cells in their footprints**. Their one-cell halos have zero water/barrier/keepout/other occupancy, while frontage streets intentionally enter some halos. Captured footprint tier spread is at most one, matching the unchanged macro placement rule; maximum slope is **0.004832** against the unchanged 0.016 threshold. Upper plots retain hillside grades (F01 tiers 5–6, F02 tiers 6–7); this is not proof of a native level floor, stair, collider or accessible threshold. No height or slope was edited to make a numerical pass.

**F11 is still conditional.** Its proposed 96×64 footprint falls within the existing mill form's 80–104×56–72 range, and its revised footprint/halo are dry and barrier/keepout-clear. However, the rounded cap of the separately proposed goods-approach band paints **two street cells inside the east face**. Only 94 of 96 footprint cells were stamped in the copied proposal; those two cells remain visible as a conflict. The next bounded correction should end that spur outside the face and measure it again, without altering the footprint, river or physical masks. The candidate is not signed off from dry geometry alone.

Eight literal river-bank sections give a **16–24px gap** from water to the proposed west working face. That is measured proximity, not a proven wheel, head race, tail race, hydraulic fall or usable native river edge. A drawing/asset agent must demonstrate the required mill working-face and facade variant, with identity deduplication against the already-authored single mill, before adoption. The mill's original logical ID, legacy identity mapping and geometry fields remain null; candidate geometry is separate. Existing assets are not assumed to face arbitrary directions for any new home or mill.

The new Mill Street band contains **three existing keepout cells at its outer join**. Those cells stay protected; no route-width pass follows. The limited four-neighbour proposed-street graph still connects all eleven door-adjacent sets to the mill court and Square, but this does not establish native collision, cart clearance, full-width legality or a portal connection. The previously retained 22 North / 7 Lull keepout cells and bridge-bank guards also remain unchanged. A later scope must resolve actual approach/portal authority rather than treating graph reach as permission to erase protections.

The copied extension changes **1,442 distinct cells in five channels**: ground appearance, streets, route occupancy, building occupancy and used flags. All 49 typed channels outside the new support `[6288,3744,6824,4368)` match the r3 baseline; all49 outside the union with the prior A/B/C support match the original captured BEFORE. Every captured literal water and bridge cell retains all 49 values. The fourteen A/B/C footprint/halo sets, their rects/doors, park, green, square, stair, well and all36 existing route polylines remain exact. All six original input hashes and the r3 archive hash are unchanged.

Three bounded attempts are retained: the rejected river/halo sites; an early `KeyError` caused by using the wrong existing JSON record key; and the complete copied proposal. The third exited 0 in 2.152 seconds with peak 66,768,896 bytes. The code error was corrected once within the stated three-attempt budget; there was no fourth probe. This is a partial result, with the mill endpoint, water-work reach and outer protection limit still visible. No producer, native plan, gameplay, actual terrain, art asset or whole-world build was changed.

GO6535477628 / ASSIGN6535521160 / ACK6535521524. The new source is a genuine descendant of 4e16a9ca. D/E/G remain unfitted; the old producer cap 40 / check 40 and all unadopted 41-building accounting remain unchanged. Final map/art merge approval still belongs to Matt on the PR.



## Mill End correction: street bands checked against actual protections

This is a narrow correction to the preceding partial offer. The historical partial data and figures remain unchanged; the latest local geometry is in `mill_end_correction`. All ten homes, the mill rectangle and door, the completed A/B/C fourteen rectangles/doors, original 40-record ledger and separate mill identity fields stay unchanged. Nothing is adopted into the production terrain or native game.

The mill goods approach now ends at `[6456,4160]`, rather than on the east wall at `[6440,4160]`. Its24px round cap ends at x6444; the separate 16px worker/door link still reaches the threshold at x6440. The two former street intrusions at `[6432,4152]` and `[6432,4160]` can therefore be stamped as building cells without clearing a guard or changing any terrain grade. The complete proposed mill now has **96 of 96 occupied cells**, zero footprint street/water/nonbuildable/barrier/keepout/other occupancy, and a dry, guard-clear one-cell halo. Frontage street remains intentionally present in that halo; this is not a claim that every halo is street-free.

The first branch attempt used an earlier real Lull-approach point and appeared clear from the 110px east-disc arithmetic. The actual copied mask still gave **five protected cells**: the mask includes crater/trail protection as well as discs. That failed route offer and its complete copied data are preserved. The second offer branches from an actual retained Lull Road point (index 3), east and south of the protected trail. It does not change the old approach endpoint or clear protected cells, and it invents no bridge. The final route coordinates and measured mask counts are below. Existing full source polylines and old tails remain unchanged.

**Mill Street:** 32px band, points `[[6824.0027316369915, 3778.2971906108255], [6784, 3808], [6784, 3944], [6528, 3944], [6488, 4000], [6488, 4328]]`. Actual copied band: 0 water, 0 barrier, 0 keepout and 0 building cells.

**Mill working court approach:** 24px band, points `[[6488, 4160], [6456, 4160]]`. Actual copied band: 0 water, 0 barrier, 0 keepout and 0 building cells.


All eleven F footprints and halos have now been measured on the final private copy, preserving captured grades and the unchanged 0.016 slope limit. All eleven door-adjacent links reach the mill court in the limited four-neighbour proposed-street graph, but **zero reach Square** in that same graph of explicitly painted streets. The new branch meets a real retained Lull Road point beyond the protected trail; the intervening named road is not represented by this painted street component. No connector was added to force this result green. Existing literal road identity is source evidence, not proof of a complete native or full-width connection to Square. This does not demonstrate native pathfinding, a level floor, a facade variant, vehicle clearance or an approved portal. The full older 22 North / 7 Lull protected tail cells and bridge-bank guards remain a separate limitation; clearing the revised F branch does not clear the entire outer road.

The mill's **16–24px measured bank gap remains proximity only**. Hydraulic fall, wheel/race/head/tail reach, legacy identity deduplication and asset working-face/facade authorability remain UNKNOWN. No extra mill identity, occupant, job, mechanic, watercourse or crossing was added. The original mill source entry retains its null identity and geometry fields; the measured candidate remains separate.

The final correction changes **38 distinct cells** inside two declared support boxes `[[6712, 3736, 6848, 3824], [6424, 4136, 6464, 4184]]`. All 49 typed payloads outside those boxes match the frozen F-partial proposal; outside the union of all declared supports they match actual captured BEFORE. All 24 previously clear A/B/C and F-home footprint/halo sets retain all 49 values, as do water/bridge cells and the protected native features. Heights, tiers, slopes, river/land/closed fields, crater, barrier and keepout masks are unchanged. The six source inputs, r3 archive and F-partial archive remain exact.

Two bounded correction attempts were used, retaining the first actual-mask failure. The final probe exited 0 in 2.222 seconds / peak 74235904 bytes. There was no third correction attempt, project import, engine/world job, production edit or unchanged A/B/C regeneration. D/E/G remain unfitted. Source GO6535910901 / ASSIGN6535926108 / ACK6535926395; the new source is a genuine child of 08ebbab5. Native/game/art/full-gate acceptance and Matt's explicit art/map approval on the PR remain outstanding.



## West Lane D: grouped fronts, service passages and garden backs

The new `west_lane_D_fit` section adds **six original records**, preserving the frozen corrected copy 303ca038 and all 25 previously measured A/B/C/F plots. This is a proposed district on the captured macro crop, not an adopted native layout. The earlier evidence sections remain unchanged. No F-road connector or native/editor-plan repin is part of this step.

West Lane continues the existing 24px market-west public lane as one short town street. Its northern fronts end at y3464; three opposing cottages begin at y3512. The resulting **48px frontage-to-frontage gap** contains the same 24px traffic lane and the offered thresholds. Two attached-front records keep their original two-bay divisions rather than becoming unrelated cottages. The tall corner house turns the market/service entrance, linking the new frontage to the existing A-quarter grain.

Separate 16px service closes connect the rear plots and side passages. These are foot/service access offers, not vehicle-clearance proof. The northern back lane stays south of the protected woodland boundary y3344. Its eastern return uses the corridor x6016–6032, between the new corner house and the retained A buildings/garden; it joins the existing rear lane without repainting it. Southern gardens extend 64–80px behind the cottage backs, then meet a shared rear close. The corner house has a small rear court rather than a falsely oversized garden. All captured grades and physical/protection masks remain unchanged.

| Source plot / record | Candidate rectangle `[x,y,w,h]`, world px | Threshold offer | Disposition |
|---|---|---|---|
| D01 / 008 | `[5736, 3440, 80, 24]` | south; `[[5760, 3464], [5800, 3464]]` | Footprint and halo macro-clear; exact asset/bay thresholds unverified. |
| D02 / 009 | `[5832, 3416, 112, 48]` | south; `[[5864, 3464], [5920, 3464]]` | Footprint and halo macro-clear; exact asset/bay thresholds unverified. |
| D03 / 024 | `[5792, 3512, 40, 72]` | north; `[[5812, 3512]]` | Footprint and halo macro-clear; north facade required / unverified. |
| D04 / 025 | `[5960, 3368, 56, 96]` | south; `[[5988, 3464]]` | Footprint and halo macro-clear; exact asset/bay thresholds unverified. |
| D05 / 026 | `[5848, 3512, 40, 56]` | north; `[[5868, 3512]]` | Footprint and halo macro-clear; north facade required / unverified. |
| D06 / 027 | `[5904, 3512, 40, 64]` | north; `[[5924, 3512]]` | Footprint and halo macro-clear; north facade required / unverified. |

The row-house records 008 and 009 retain their exact source forms, footprints and bay data: 6+4 cells and 8+6 cells, including storeys and roof choices. Two proposed bay thresholds per record yield **eight offered thresholds across six records**. They do not add logical building records, households, occupants, jobs or routines. The original forty-record ledger and separate mill entry remain unchanged, with candidate total 41 and all original unresolved geometry/identity fields still null.

All six footprints have zero water, nonbuildable, barrier, keepout, street or other-occupancy cells and are completely stamped in the copied candidate. Every footprint retains its captured uniform macro tier 3 or 4; maximum slope is **0.001599**, against the unchanged 0.016 limit. Their one-cell halos are dry and guard/other-occupancy-clear; frontage streets and some mixed tiers intentionally remain in halos. All fifteen proposed public/service/passage/door bands have zero water/barrier/keepout/building intersections. All eight threshold links reach Square in the limited four-neighbour graph of painted streets, with the conditional well conservatively reserved.

The closed halt gate `[5976,3528,8,40]`, its conservative one-cell planning reserve, future workshop lot `[6000,3568,64,64]` and green `[6016,3656,168,136]` retain all 49 values, with zero new structure/route intersections. The new public street returns to the town-side market lane above the closed portal; no halt arrival or station permission is inferred. All prior 25 plot footprints and halos, earlier A/B/C garden/service areas and native story features stay byte-exact. No watercourse is filled, bridge invented, native gate opened, grade flattened or threshold weakened.

**Art/native limits:** current native art source supports south-facing doors. The three opposing cottage north facades are required but unverified future variants. Door/bay placement, occlusion, native floors, colliders, pathfinding, interactions, portals, character-scale art and the current editor plan still require actual authoring and acceptance. This frozen capture-based proof is not automatically current-native compatibility. Existing F local/outer-road limitations remain untouched: the earlier zero-Square diagnostic describes painted-street coverage, not proof that the native world is disconnected. Named roads, placement keepout and legacy coarse walking masks are not interchangeable permissions.

The district changes **1,080 distinct cells in four channels** inside `[5704,3344,6056,3680)`. All 49 typed payloads outside this support match the frozen 303ca038 copy; outside the accumulated support union they match original captured BEFORE. Water and bridge cells retain all 49 values, as do river/land/closed, height, tier, slope, crater, barrier and keepout channels. All six original input hashes and the frozen base archive remain unchanged; all 36 existing source route polylines are preserved.

The first bounded attempt stopped at the old public-lane byte guard because route bookkeeping would have changed an existing painted street. That code and error are retained. The second keeps existing streets entirely unchanged and moves the northern service return to x6024, avoiding the old A garden band. It exited 0 in 2.004 seconds with peak 67,391,488 bytes; there was no third probe, F rerun or world/engine/project import. Static source/accounting/null/history/AST/XML/whitespace checks are separate from native/full-project/art acceptance. E/G remain unfitted and need separate assignments. No production adoption, Ready, merge or Matt approval is claimed.

GO6536330070 / ASSIGN6536511906 / ACK6536512087. The source is a genuine child of b39fb6b8 and changes only the two existing proposal documents. Final art/map merge approval still belongs to Matt on the PR.



## Eastgate and Halt Road: the complete 41-record candidate, with one grade conflict

The new `eastgate_halt_EG_fit` section completes the **geometry offer for 40 original records plus one separate restored mill**, without adopting any of them into the native game. All 31 earlier A/B/C/D/F footprints, halos, gardens, courts and source sections remain unchanged. Nine of the ten new E/G footprints are macro-clear. **E05 / crossroads-b036 remains unoccupied**: its captured tiers 9–11 span two steps, exceeding the unchanged permitted spread of one. Its slope 0.006221 is below 0.016 and its literal ground/physical guards are clear; that does not waive the tier conflict. Overall accounting is 40 macro-clear footprints and one conditional plot, not 41 accepted/native placements.

Eastgate now places two inns on the south side of Market Lane, opposite three smaller frontage offers. The principal wide-front inn has a distinct 128×104 rear coach court, reached by a 32px side drive. The secondary portrait-plan inn has a separate 40×56 rear service court on the dry side of the protected feature, reached from the shared rear service lane rather than through the inn. The inns are 8px apart; that gap is not called a 16px passage. Both inn north facades and service/work faces are required but unverified. Coach turning, grades, gates and native floors remain unproved even though the courts are dry/guard-clear and retain captured tiers 9–10.

The first eastern offer put the portrait inn on 96 literal path cells, spread the principal inn across tiers 9–11 and met unrelated occupancy in its far-eastern service loops. Those negatives remain. The final offer moves onto the already measured lower plateau and avoids the real Fern Lane and occupied far-eastern ground. Three north-side dwellings face south toward the public street. Ordinary `BUILDABLE` includes unprotected `trail`; the final uses that unchanged source rule while still rejecting `path`, registered streets, occupancy, guards and excessive tier/slope spread. No named regional centreline crosses the revised E footprints by independent source check; this is not proof of every unnamed/native path permission.

Halt Road is an inhabited productive fringe, not an invented station. Its five homes face a short32px approach connected to an exact retained western regional point. Smaller rear work plots and longer garden backs taper around the existing roads and drainage. All five G records and the entire declared G support retain the first successful offer's 49 typed values exactly; they were not repainted during the final E measurement. The intended loading yard `[5840,4304,240,64]` was never reached in the failed original capture. It is reserved as an intention, not drawn as an existing rail/platform, inn court or open arrival. No measured rail/platform polygon exists, so rail clearance and station/portal authority remain UNKNOWN.

| Plot / record | Candidate `[x,y,w,h]`, world px | Required face | Actual copied disposition |
|---|---|---|---|
| E01 / 030 | `[6896, 3432, 72, 128]` | north | Macro footprint and halo clear; native/asset acceptance unverified. |
| E02 / 031 | `[6976, 3456, 128, 72]` | north | Macro footprint and halo clear; native/asset acceptance unverified. |
| E03 / 032 | `[6992, 3312, 48, 88]` | south | Macro footprint and halo clear; native/asset acceptance unverified. |
| E04 / 034 | `[7056, 3352, 72, 48]` | south | Macro footprint and halo clear; native/asset acceptance unverified. |
| E05 / 036 | `[6896, 3352, 80, 48]` | south | UNSTAMPED: tiers 9–11/spread2; no grade waiver. |
| G01 / 028 | `[5992, 3944, 56, 96]` | west | Macro footprint and halo clear; native/asset acceptance unverified. |
| G02 / 029 | `[5992, 4064, 48, 72]` | west | Macro footprint and halo clear; native/asset acceptance unverified. |
| G03 / 038 | `[5888, 4048, 56, 48]` | east | Macro footprint and halo clear; native/asset acceptance unverified. |
| G04 / 039 | `[5880, 4120, 64, 48]` | east | Macro footprint and halo clear; native/asset acceptance unverified. |
| G05 / 040 | `[5992, 4160, 56, 40]` | west | Macro footprint and halo clear; native/asset acceptance unverified. |

All 18 E/G public/service/threshold bands have zero water, barrier, keepout or building cuts. All ten offered thresholds connect locally; the five E threshold offers reach Square in the painted-street graph, while G's five are outside that painted component. This is coverage evidence, not native-disconnection proof or a substitute for the real retained roads and their bridge/gate authority. Earlier F/outer-road, mill identity/hydraulic and facade limitations remain unchanged.

A **bounded UNAPPLIED terrace-study option** surrounds E05 at `[6888,3344,96,64]`. It would investigate one continuous plot/frontage terrace, protecting neighbouring plots, physical masks and water, then remeasure the ordinary tier/slope/door/native rules. Target native level and earthwork quantities are UNKNOWN. No height, tier, slope or physical/protection mask was changed in this offer, and no terrain result or new rule is claimed.

The final copy changes 2,117 distinct cells inside the declared E/G supports. Per-channel counts/outside-support proofs are in the sidecar and actual report. All 49 typed values outside E/G match frozen D489e; outside the accumulated support union they match original captured BEFORE. All 31 earlier plot/halo sets, prior A/B/C/D/F areas, native story/closed-halt reserves, planned loading area, water/bridge cells and six original input hashes remain exact. All 36 original route polylines remain unchanged. Original 40 records, bays/forms/dimensions, single mill/count 41 and all original null identity/geometry fields remain deep unchanged; no residents, jobs or extra homes are inferred.

**Execution and artifact history:** invocation 1 measured the first conflicts and exited 0. Its completed-size accounting implies a 1,442,295-byte NPZ, but the retained original later contained only 1,088,864 bytes, 29 complete local ZIP members and no central directory: 353,431 bytes are absent. The cause is UNKNOWN. Invocation 2 failed before measurement when opening that incomplete archive. Independent byte reconstruction from frozen D489e plus the recorded CSV matched all 49 payload/outside hashes. Recovery-only GO6537123683 then authorised a NEW RECOVERED container; its typed data is exact, while original ZIP byte identity is not claimed. Both the incomplete original and the recovered container are retained.

After root inspection, GO6537155067 expressly authorised one final E-only measurement of the prepared revision. Its atomic closed output was collected at exit0 in 3.288 seconds, peak 75,112,448 bytes, with 10,954 log bytes and no truncation. After actual collection, all 49 CRC/shape/dtype/raw/NPY/outside hashes and per-file closed size/SHA matched. Original inputs and successful G data remain exact. There was no further fit or redesign after the residual E05 conflict. A timing/yield explanation for the earlier archive loss is unproved and is not presented as a cause.

This is one labelled complete-town candidate on a private captured crop, **not a corrected production continent overview, 21-town report, native/editor compatibility, art approval or playable integration**. Static source/accounting/null/history/AST/XML/whitespace checks are separate from required full-project, art, native and visual gates. Producer cap 40 / check 40 is unchanged until separately scoped adoption of the 41-record programme. Matt's explicit art/map OK on the PR remains required before merge.

GO6536825931 / ASSIGN6536841341 / ACK6536841532; recovery-only6537123683 / ACK6537136426; final E6537155067 / ACK6537164795. Source is a genuine sole child of 60c08da3; only the two existing proposal documents change.



## Native-driven whole-town revision r2 — UNMEASURED source contract

GO6537559340 / ASSIGN6537575560 / ACK6537577661; genuine a96 descendant. This section supersedes the earlier rectangle/entrance **offers**, retaining every original record, the separate mill, every old diagnostic section and its raw outcomes as history. It does not transfer the earlier 40 macro-clear results to changed geometry. No fitting, crop mutation, painting, native import, test, engine or generation ran. The accompanying static SVG is a flat source schematic, without sampled terrain or accepted native art.

The all41 native audit (6537486605, native407 feb37c31) identified19 non-south offers and11 narrow-cottage cases (22-record union),14 generic classes unresolved and34 new records unbound. Current ordinary houses show a south wall only. The corrected arrangement therefore uses40 ordinary south-entry offers plus a deliberately unbound south public entrance intent for the custom mill. The mill's west water-working face remains separate; no second mill, hydraulic acceptance or historical ID is invented.

The seven captured anchors and logical doors remain exact, together with story approaches, garden stairs, the green, well, closed halt/guard, future workshop, crater centre/horizontal bowl radius and all original save identities. Actual407 herbalist floor/door are8px farther south than this frozen capture; that adoption difference is now explicit rather than silently moving the anchor. North terrace's extra rendered south door and smithy/Ferns2px logical-to-drawn offsets remain unresolved review items.

West Lane now has a real northern terrace frontage and a southern public court. Three widened cottages enter from their south courts, connected around the western edge, leaving the closed halt untouched. Productive allotments beyond the court are labelled as allotments rather than imaginary back-door access. The narrow8px interval between D05/D06 is not a passage; both reach the southern public court. The old x6000 west-route descent conflicted with the reserved future workshop and closed-halt guard, so the proposed local west approach detours via West Lane and west of those features while retaining its exact old regional join. No guard is cleared. The row-house records remain whole assemblies: D01's floor depth changes24→48 while the original mixed roof/storey bay programme stays historical and intact. Native units only split paint/window ownership; they do not implement mixed roof materials or a second-storey assembly.

Mill End uses one street, an upper court, grain court and stepped lower courts. Narrow cottages gain actual64px floors; detached house proposals also receive wider physical plots without being relabelled as cottage scale classes. The single mill's public approach moves to its south loading court. Its custom facade, exact native assembly, hydraulics and bank acceptance remain unknown. No new water crossing is proposed.

Both inns now present visible south fronts to distinct courts. E01 receives a112px physical front and E02 retains128px; these are class-specific frontage offers, not drawn height/storey/opaque approval. A40px interval between inn floors provides a real side access court (24px proposed route), replacing reliance on an8px gap. The coach drive connects those courts to the existing east arrival. E05 stays conditional and unoccupied: captured tiers9–11 exceed the unchanged ordinary spread limit. Its terrace-study target native level remains UNKNOWN.

The Halt Road group enters from south-facing courts off the inhabited approach and keeps productive plots toward the river fringe. The real regional join is retained as source intent, without claiming a rail/platform polygon, open halt, native Square connection or transport permission.

The default cottage structural slate span is3×(floor width+6) at density3. A64px floor gives210artpx of structural roof and216px canvas, with no blank-padding credit. This is an unexecuted source calculation; opaque bbox, height, doors, detail, collision, occlusion and full art gates remain unproved. Generic house/shop/inn/mill uses still lack legitimate exact bbox classes. Candidate shell parameters are actionable inputs to existing village.building→houses.building, not approved bindings.

### All41 original-versus-revised physical contracts

Every rectangle is[x,y,w,depth] in worldpx; every row is UNMEASURED. The historical column preserves the source dimensions and the exact earlier candidate floor. All proposed public fronts are south. Mill entry support is still unbound; other ordinary shells support the projection but do not yet have approved pieces.

| Plot | Historical floor / prior offer | Revised floor | South threshold offer | Native binding / open gap |
| --- | --- | --- | --- | --- |
| C01 | [80, 40] / [6256, 3272, 80, 40] | [6256, 3272, 80, 40] | [[6296, 3312]] | hut |
| A01 | [96, 40] / [6176, 3408, 96, 40] | [6176, 3408, 96, 40] | [[6224, 3448]] | library |
| C02 | [96, 40] / [6320, 3408, 96, 40] | [6320, 3408, 96, 40] | [[6392, 3448]] | north_cottages |
| A02 | [72, 48] / [6088, 3488, 72, 48] | [6088, 3488, 72, 48] | [[6148, 3536]] | bakery |
| A03 | [72, 48] / [6088, 3576, 72, 48] | [6088, 3576, 72, 48] | [[6148, 3624]] | herbalist |
| B01 | [88, 56] / [6432, 3472, 88, 56] | [6432, 3472, 88, 56] | [[6464, 3528]] | smithy |
| B02 | [72, 48] / [6432, 3616, 72, 48] | [6432, 3616, 72, 48] | [[6448, 3664]] | fern_cottage |
| D01 | [80, 24] / [5736, 3440, 80, 24] | [5736, 3416, 80, 48] | [[5760, 3464], [5800, 3464]] | whole terrace; mixed assembly unknown |
| D02 | [112, 48] / [5832, 3416, 112, 48] | [5832, 3416, 112, 48] | [[5864, 3464], [5920, 3464]] | whole terrace; mixed assembly unknown |
| C03 | [48, 72] / [6184, 3232, 48, 72] | [6176, 3232, 64, 72] | [[6208, 3304]] | cottage shell; piece unknown |
| C04 | [56, 88] / [6360, 3240, 56, 88] | [6360, 3240, 72, 88] | [[6396, 3328]] | house shell/class unknown |
| F01 | [48, 64] / [6656, 3856, 48, 64] | [6616, 3856, 64, 64] | [[6648, 3920]] | cottage shell; piece unknown |
| B03 | [48, 88] / [6552, 3472, 48, 88] | [6552, 3472, 64, 88] | [[6584, 3560]] | shop shell/class unknown |
| F02 | [40, 72] / [6728, 3848, 40, 72] | [6696, 3848, 64, 72] | [[6728, 3920]] | cottage shell; piece unknown |
| F03 | [64, 96] / [6560, 3968, 64, 96] | [6560, 3968, 72, 96] | [[6596, 4064]] | house shell/class unknown |
| F04 | [48, 56] / [6656, 3968, 48, 56] | [6656, 3968, 64, 56] | [[6688, 4024]] | cottage shell; piece unknown |
| F05 | [56, 88] / [6520, 4080, 56, 88] | [6520, 4112, 72, 88] | [[6556, 4200]] | house shell/class unknown |
| F06 | [40, 64] / [6424, 4000, 40, 64] | [6392, 3976, 64, 64] | [[6424, 4040]] | cottage shell; piece unknown |
| F07 | [64, 40] / [6520, 4208, 64, 40] | [6520, 4256, 64, 40] | [[6552, 4296]] | cottage shell; piece unknown |
| F08 | [64, 48] / [6392, 4240, 64, 48] | [6392, 4280, 64, 48] | [[6424, 4328]] | cottage shell; piece unknown |
| F09 | [64, 40] / [6520, 4280, 64, 40] | [6520, 4352, 64, 40] | [[6552, 4392]] | cottage shell; piece unknown |
| B04 | [88, 48] / [6520, 3592, 88, 48] | [6520, 3592, 88, 48] | [[6564, 3640]] | house shell/class unknown |
| F10 | [72, 40] / [6344, 4048, 72, 40] | [6344, 4048, 72, 40] | [[6380, 4088]] | cottage shell; piece unknown |
| D03 | [40, 72] / [5792, 3512, 40, 72] | [5704, 3512, 64, 72] | [[5736, 3584]] | cottage shell; piece unknown |
| D04 | [56, 96] / [5960, 3368, 56, 96] | [5952, 3368, 64, 96] | [[5984, 3464]] | house shell/class unknown |
| D05 | [40, 56] / [5848, 3512, 40, 56] | [5792, 3512, 64, 56] | [[5824, 3568]] | cottage shell; piece unknown |
| D06 | [40, 64] / [5904, 3512, 40, 64] | [5864, 3512, 64, 64] | [[5896, 3576]] | cottage shell; piece unknown |
| G01 | [56, 96] / [5992, 3944, 56, 96] | [6000, 3944, 72, 96] | [[6036, 4040]] | house shell/class unknown |
| G02 | [48, 72] / [5992, 4064, 48, 72] | [6000, 4080, 64, 72] | [[6032, 4152]] | cottage shell; piece unknown |
| E01 | [72, 128] / [6896, 3432, 72, 128] | [6888, 3448, 112, 96] | [[6944, 3544]] | inn shell/class unknown |
| E02 | [128, 72] / [6976, 3456, 128, 72] | [7040, 3448, 128, 72] | [[7104, 3520]] | inn shell/class unknown |
| E03 | [48, 88] / [6992, 3312, 48, 88] | [6992, 3312, 72, 88] | [[7028, 3400]] | house shell/class unknown |
| B05 | [96, 56] / [6528, 3336, 96, 56] | [6528, 3336, 96, 56] | [[6576, 3392]] | house shell/class unknown |
| E04 | [72, 48] / [7056, 3352, 72, 48] | [7080, 3352, 72, 48] | [[7116, 3400]] | cottage shell; piece unknown |
| A04 | [64, 56] / [6096, 3408, 64, 56] | [6096, 3408, 64, 56] | [[6128, 3464]] | shop shell/class unknown |
| E05 | [80, 48] / [6896, 3352, 80, 48] | [6896, 3352, 80, 48] | [[6936, 3400]] | cottage shell; piece unknown |
| A05 | [48, 64] / [6032, 3400, 48, 64] | [6024, 3400, 64, 64] | [[6056, 3464]] | shop shell/class unknown |
| G03 | [56, 48] / [5888, 4048, 56, 48] | [5864, 4048, 64, 48] | [[5896, 4096]] | cottage shell; piece unknown |
| G04 | [64, 48] / [5880, 4120, 64, 48] | [5864, 4152, 64, 48] | [[5896, 4200]] | cottage shell; piece unknown |
| G05 | [56, 40] / [5992, 4160, 56, 40] | [6000, 4200, 64, 40] | [[6032, 4240]] | cottage shell; piece unknown |
| F11 | None / [6344, 4128, 96, 64] | [6344, 4128, 96, 64] | [[6392, 4192]] | mill shell/class unknown |

### Terrain and native adoption still required

The JSON declares the exact proposed local route points, court/plot bounds, threshold approaches and protected features. Proposed western clearing, lower mill edge, eastern coach drive and Halt Road court changes are UNAPPLIED earthwork/route operations; their native target levels are NULL. This pass loaded no crop arrays and altered no ground, mask, guard, height, water or bridge byte. It does not punch keepout holes or waive ordinary acceptance.

The current407 native box remains[5976,3248,640,560]. Thirty older candidate floors lay outside or crossed it; the revised floor union and revised outside count are recorded explicitly. Extending or splitting zones, preserving cross-zone routes and save identities, binding all34 new records, class-specific inn/terrace/mill contracts and measuring one coherent complete correction are later adoption work. Producer cap40/check40 remain unchanged. This is still a41-record programme, not a claim of41 complete homes/residents/jobs.

Repository changes remain only these two existing proposal documents. All prior measurements apply to their precise historical inputs. Private source arithmetic and the labelled static schematic support review only; no successful native placement, actual asset/detail gate, whole-world21-town report, Ready status or Matt approval follows.

## Native visible-approach reconciliation (r3, source proposal)

The actual Q2 native cottages show all four doors clearly. Their complete 42 x 96 door regions retain all 4,032 isolated-body pixels each. The problem is the walking space projected below two doors: the lower cottage's roof/chimney hides much of G02's apron and court, and G04's chimney partly hides G03's court. These are visual findings, not a claim that doors are hidden or that a physics check failed.

Evidence is the [actual Q2 native scene](https://chatgpt.com/library?file_id=libfile_efbdb66f20508191803385ce2b7e94a1&account_id=personal), run41193179535/job124513954596 on native40918588 and receiver40645f934. The native PNG is397344B/SHA256392071bff2444516dd023a8eaab17db2cfb4b717db1a1e4a5862a910db30cf08. Its original coordinates, pixels and receipts remain unchanged. GO6542378669 / ASSIGN6542382538 / ACK6542382710 authorise only this bounded two-document proposal.

The existing size guide keeps a 32 x 16 world-px door apron (four by two cells). Actual source-alpha masks, ordered as foreground sprites, cover the following nominal bands. Each counted scene pixel matches an opaque foreground sprite; transparent canvas and ground shadows are excluded. The percentages describe the observed projection and set no new acceptance threshold.

| Plot | Other-house coverage of 32 x 16 apron | Coverage of declared 24px court band | Actual door region |
|---|---:|---:|---|
| G02 | 3585/4608 pixels, 77.8% | 9662/17884, 54.0% | all4032 pixels intact |
| G03 | 101/4608, 2.2% | 4726/19612, 24.1% | all4032 pixels intact |
| G04 | 0/4608 | 0/19612 | all4032 pixels intact |
| G05 | 0/4608 | 0/17884 | all4032 pixels intact |

G02's door-to-court centreline has38/49 native samples covered; its court-to-spine centreline has107/193. G03's door centreline is clear, while29/217 court-centre samples are covered by the foreground chimney. The sampled central32px Halt spine has no house coverage. Readability and playable walking/collision validation remain separate.

### Bounded next placement offer

Only G04 and G05 move. Their physical forms, dimensions, material looks, south doors, IDs and counts remain the same. All39 unlisted floors, including G02/G03, inherit r2 unchanged.

| Plot | Historical738/Q2 floor | New proposed floor | New south threshold | Movement |
|---|---|---|---|---|
| G04 / crossroads-b039 | [5864,4152,64,48] | [5864,4184,64,48] | [5896,4232] | south32worldpx |
| G05 / crossroads-b040 | [6000,4200,64,40] | [6056,4192,64,40] | [6088,4232] | east56, north8worldpx |

The two24px court halves now meet the unchanged Halt spine at[5968,4248]: west to[5896,4248], east to[6088,4248]. Their16px threshold spurs are[5896,4240] to[5896,4248] and[6088,4240] to[6088,4248]. This is one aligned cross-lane instead of adjacent staggered turns. Every other70 local route offer and the original36 source global routes remain untouched; no station, rail opening, portal or new shortcut is inferred.

G05 would intersect the old productive-back proposal. Move that proposed area from[6088,4080,64,208] to[6128,4080,64,208], leaving8worldpx beside G05's new east edge6120. The moved area avoids all41 floors, all74 local route bands and the other8 candidate areas, as well as the known protected green/well/workshop/closed-halt rectangles. Its east edge6192 exceeds the historical Halt study's6152: a later UNAPPLIED study offer must extend40px east, from[5848,3928,304,360] to[5848,3928,344,360]. The target terrain level remains NULL. No ground or playable-zone growth occurs here.

### Analytical result and limits

Translating the existing actual alpha masks numerically by G04[0,96] and G05[168,-24] art pixels predicts zero foreign-sprite coverage on all four prescribed aprons and all four declared court bands. This is **ANALYTICAL ONLY**: no new PNG, native composition, terrain fit or physics result exists. The same960 x1008 diagnostic can contain the revised four cottage sprites, but its world east edge6144 cannot show the whole productive area ending6192.

Source-only rectangle/full-width capsule checks find all41 floors disjoint and all74 local route bands clear of floor interiors; threshold tangency is allowed. Moved floors and the productive area avoid the known protected bounds. The seven captured story anchors, green, well, workshop, closed halt, source global routes, water/bridges/river/masks/grades and save IDs remain unchanged. These checks do not establish actual terrain/grade/bank/hazard or full global-route clearance. The historical floor union remains[5704,3232,1464,1160].

The appended JSON field native_visible_approaches_r3 overrides only these two records, four local route offers and one area for the next SOURCE PROPOSAL. All historical738/Q2 data stays bound to its old geometry. All moved ground remains UNMEASURED; prior E/G terrain results do not transfer. The four diagnostic native pieces remain candidates, and the remaining classes/terrace/mill/zone/binding/E05 and approval gaps persist. No new households/jobs/rules, size exception, renderer/cutaway direction,409/406 edit or live adoption follows. Producer cap40/check40, medium14–22/large30–45 and41-record accounting are unchanged.

Next: root and independent source review, then a separate exact native context recomposition and ordinary real-terrain validation. KEEP/catalogue/Y12/detail/full gates/whole-world21-town/Matt approval and Ready/merge remain outstanding.


## Doorstep contact r4: use the renderer's rectangular cells

Matt asks for the path to reach the house. Q3 kept the doors and courts clear, but did not prove earth-to-threshold contact. The earlier radius-cap reasoning was wrong for this native route path.

GO6546904382 / ASSIGN6546924380 / separate ACK6546928147. This source-only overlay changes the **nominal width of just the four G02-G05 threshold spurs from16 to24 worldpx**, keeping their points and every floor/door in place. It changes no painter, terrain, other route, reserve, count or earlier JSON section.

Exact source409a25 town._ground converts nominal width with n=max(1,round((width-8)/8)); softgrid.cells_route lays rectangular cell slices. Width16 becomes one8px cell, with floor snapping and no cap north of the first row. Each old spur starts at doorY+8, so its entire two-cell strip is already inside its court and leaves the doorstep row unpainted. All four door centres lie on cell lines, while that odd-width strip sits to their right.

Width24 becomes **two cells**, snapped to cell lines with one cell either side. Keeping the existing start at doorY+8 now makes the slice start at doorY and span doorX-8 to doorX+8: a centred16px unsmoothed core. Each spur adds the two missing threshold-row cells and shares four cells with its existing court. These are exact half-open rectangular slices, not a24px circular corridor.

| Spur | Existing points, worldpx | Proposed nominal width | Derived unsmoothed core [x,y,w,h] |
| --- | --- | ---: | --- |
| G02 | [[6032, 4160], [6032, 4168]] |24| [6024, 4152, 16, 24] |
| G03 | [[5896, 4104], [5896, 4112]] |24| [5888, 4096, 16, 24] |
| G04 | [[5896, 4240], [5896, 4248]] |24| [5888, 4232, 16, 24] |
| G05 | [[6088, 4240], [6088, 4248]] |24| [6080, 4232, 16, 24] |

The four derived strips touch their own floor only at its southern boundary and have zero positive-area overlap with all41 proposed floors. The other five diagnostic routes and all70 other town routes remain exact. Original40 plus the separate mill/candidate41 accounting, producer cap/check40, seven anchors, source history and all oldr2/r3 results remain unchanged.

A nominal24 route treated as a radius12 capsule would extend4worldpx into its own floor, unlike the native two-cell rectangle. This overlay does not pass or redefine that physical-route check. Later adapters and terrain validation must reconcile the nominal native width and actual physical core explicitly; they must not suppress a capsule conflict or credit an unchanged physics pass.

This is **source arithmetic, not a new rendered contact or terrain pass**. The renderer unions cells before unchanged soft-grid rounding, seeded1.5-3artpx displacement, cleanup and ground painting. Those steps can alter edge pixels, so a later exact combined native image must demonstrate continuous earth at all four thresholds with the courts still visible. No native module, array, mask, renderer, terrain fit, collision test or engine was executed for this overlay.

The appended native_visible_approaches_r4 field overrides only these four nominal widths after r3. The later native fixture must consume it explicitly, together with reviewed painter corrections and an honest updated receiving closure. Actual continent water/bank/grade validation and playable zone extent, physical door operation, detail/Y12/full gates and Matt's PR approval remain open.
