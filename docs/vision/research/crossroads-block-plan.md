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

