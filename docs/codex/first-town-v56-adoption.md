# First-town v56 adoption review

Y38/r1, 29 October 2026. Sole claim [6497649552](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6497649552), under [lead dispatch6496505337](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6496505337). Report base is main `b1dbceafc77d51358eae503f8f57bac617055fbe`. This document supplies source records for Y35; it changes no town or producer.

The ten added building records and explicitly carried district, open-use and site metadata match the existing `PROPOSED_ADOPTIONS` packets. The exporter recomputes derived fields; this does not establish whole-proposal JSON reproduction. **None of the packets is selected by the default v56 producer**. Keep them as explicit proposals until the newly generated baseline, real ground and access have been reconciled. Copying their JSON over generated output would bypass that work.

## Source snapshots

Short source names below refer to these immutable heads.

| Source | Actual commit | Role |
| --- | --- | --- |
| 303 | `4984438d09b5fe1333d3e6ea6e6ee82be2bdc908` | Historical v55 map and town baselines |
| 334 | `4669140421d7d8c69482fc90b78fea0a50d1d4bc` | Cinderwick proposal |
| 335 | `59f3722d1b39050cc81709fa5933d4c9c093ee98` | Hearthold proposal |
| 336 | `9276174000e47858e92a25803e606fb9dea1fc87` | Launch Cape proposal |
| 355 | `7afe9efdb3340bd5bb350176c182db4aa0421ebe` | Prospective stable seeds and retained adoption interface |
| 381 | `3e4ab55920e8cecd384ba468bd819565bb3947d9` | Frozen Y35 prospective v56 producer; generation still queued at source-freeze6497218483 |

The baseline JSON blobs on355 and381 still equal303. The proposal JSONs preserve all **51 original building records**, with ten additions across the three towns. Their additions exactly equal the packet records in381 `towns55.py`. “Preserved” here compares those committed JSONs; it does not establish that a fresh CRC32-seeded generation reproduces303's baseline.

| Town | Baseline records / counted | Proposal records / counted | Target | Counting facts |
| --- | --- | --- | --- | --- |
| Cinderwick | 13 / 13 | 17 / 15 | 14–22 | Two cottages add 2; two net sheds add 0. |
| Hearthold | 32 / 28 | 35 / 31 | 30–45 | Three additions add 3; four inherited landmarks remain excluded. |
| Launch Cape | 6 / 3 | 9 / 6 | 4–8 | Three additions add 3; inherited hangar b001 and warehouses b003/b006 remain excluded. |

Use `counts_as` for these totals. Launch Cape's three excluded records still have `counted:true`, so counting that flag alone yields the wrong total. Cinderwick's sheds have `counted:false, counts_as:0`; they are additional records, not additional counted buildings.

## Exact addition records

Coordinates are continent cells, eight world pixels per cell. Footprints and plots are `[x,y,width,height]`; doors are `[x,y]`. Each source `rect_px` is the footprint multiplied by 8. No coordinates below are proposed relocations or proven v56 positions.

| Stable proposal ID | Type / form | Footprint cells | Door / faces | Private plot cells | counts_as |
| --- | --- | --- | --- | --- | --- |
| `cinderwick-b014` | cottage / cottage | `[301,719,8,6]` | `[305,725]` / `cinderwick-s02` | yard `[301,717,8,2]` | 1 |
| `cinderwick-b015` | cottage / cottage | `[306,727,7,5]` | `[305,729]` / `cinderwick-s02` | yard `[306,725,7,2]` | 1 |
| `cinderwick-b016` | barn / shed | `[300,736,4,3]` | `[302,735]` / `cinderwick-s01` | absent | 0 |
| `cinderwick-b017` | barn / shed | `[306,736,4,3]` | `[308,735]` / `cinderwick-s01` | absent | 0 |
| `hearthold-b033` | house / house | `[253,706,10,6]` | `[263,708]` / `hearthold-s09` | yard `[251,706,2,6]` | 1 |
| `hearthold-b034` | cottage / cottage | `[254,698,9,6]` | `[263,700]` / `hearthold-s09` | yard `[252,698,2,6]` | 1 |
| `hearthold-b035` | workshop / workshop | `[343,690,11,7]` | `[345,689]` / `hearthold-s06` | yard `[343,697,11,2]` | 1 |
| `launch-cape-b007` | cottage / cottage | `[1494,727,8,6]` | `[1502,729]` / `launch-cape-a1` | garden `[1492,727,2,6]` | 1 |
| `launch-cape-b008` | cottage / cottage | `[1510,729,8,6]` | `[1509,731]` / `launch-cape-a1` | garden `[1518,729,2,6]` | 1 |
| `launch-cape-b009` | workshop / workshop | `[1509,737,13,7]` | `[1508,739]` / `launch-cape-a1` | yard `[1522,737,2,7]` | 1 |

### Cinderwick334

All four additions belong to `cinderwick-d-the-quay`. The cottages' exact purpose is “a detached fishing cottage”; their occupants field is “a fisher's household”. Both sheds have purpose “a net shed by the boatyard” and occupants “work storage only; resident roles deferred to X3”. These strings provide no named people, household sizes or routines.

The associated adoption deltas are:

- `buildings_counted=15`, `fronts=17`; add `size_table_px.shed=[[32,48],[24,40]]`.
- `site.authored="existing generated layout with Y15 Cinderwick-only authored additions (issue149 comment6471345306)"`.
- The Quay's declaration becomes “the existing stone quay with detached fishing cottages, net sheds and a working boatyard”; membership is b014–b017, `mix={"cottage":2,"barn":0}`, function “docks and transport with homes”. Preserve the literal type/contribution mix; do not silently turn it into a count of shed forms.
- Add `cinderwick-o01`, “the boatyard work apron”, kind `yard`, cells `[294,736,6,5]`.
- Add `cinderwick-o02`, “the boatyard net-shed frontage”, kind `yard`, cells `[300,736,11,3]`.

The two yard rectangles cover 63 cells together; the two shed footprints occupy 24 of those cells, leaving 39 open. The frontage rectangle includes the sheds. This source representation is not a second building overlap and should not be rewritten as 63 cells of clear working space.

Exactly seven top-level fields differ from303: `buildings_counted, site, districts, size_table_px, fronts, buildings, open_uses`. Original streets, arrivals, terrain and life data are unchanged. The retained historical report records 10 streets, 2 arrivals and 1 dead end; it is not prospective v56 access evidence.

### Hearthold335

b033/b034 join `hearthold-d-ash-lane`; b035 joins `hearthold-d-smiths-row`. Purposes are respectively “a detached lower-town house”, “a detached lower-town cottage”, and “a craft workshop; specific trade not yet authored”. The home occupants field explicitly leaves individuals and routines unauthored; the workshop likewise leaves individual workers and routines unauthored. Do not assign a trade or a resident from these descriptions.

Associated deltas:

- `buildings_counted=31`, `fronts=35`.
- Extent `footprint_px`: `[1996,5096,2776,5800]` → `[1996,5096,2832,5800]`.
- `game_layout.screens`: `[2.4,3.9]` → `[2.6,3.9]`.
- Append the new IDs to those two district memberships. Ash Lane mix becomes `{"house":4,"cottage":3,"workshop":1}`; Smiths' Row becomes `{"shop":1,"workshop":6,"house":2,"cottage":2,"townhouse":1}`.

Exactly six top-level fields differ: `buildings_counted, footprint_px, districts, fronts, buildings, game_layout`. The castle wall, gate and sealed postern, size table, original roads/arrivals, open uses, terrain and life arrays are unchanged. The historical report's 18 streets, 3 arrivals and 5 dead ends remain separate from the additions. [Review6476348901](https://github.com/rempemat-eng/appify/pull/335#issuecomment-6476348901) retains the eastern workshop's slope, retaining and access review.

### Launch Cape336

b007/b008 join new district `launch-cape-d-staff-homes`; b009 joins `launch-cape-d-the-works`. Purposes are “a detached staff cottage” and “a staff settlement workshop”. Their occupants fields explicitly leave individual residents/workers and routines unauthored.

Associated deltas:

- `buildings_counted=6`, `fronts=9`; cottage size range is added.
- Extent: `[11856,5928,12240,6515]` → `[11856,5816,12240,6515]`; `game_layout.screens` changes `[1.2,3.3]` → `[1.2,3.9]`.
- The staff-homes district has centre `[12048,5848]`, the two cottage IDs, `mix={"cottage":2}`, function “homes”, and declaration “two detached staff cottages with gardens at the northern entrance, away from the pad”.
- The works gains b009 and its workshop mix rises from 2 to 3.

Exactly seven top-level fields differ: `buildings_counted, footprint_px, districts, size_table_px, fronts, buildings, game_layout`. Streets/arrival, terrain, site, ground, landmarks and life data are unchanged. The inherited pad district's function “homes”, `site.dry=false`, aggregate `tiers=[-1,7]` and `levelled_footprints=4` do not establish any new addition's use, wetness or tier. The historical report records 3 streets, 1 arrival and 0 dead ends.

## Door and terrain evidence

The following values come from literal committed town RLE rows and bounded arithmetic on declared street polylines. They are neither a real-raw-ground adoption run nor runtime navigation.

| Addition | Literal footprint symbols | Door distance to its named street band, Chebyshev cells |
| --- | --- | --- |
| Cinderwick b014 | 8 land `.`,40 green `g` | 0; Quay Lane s02 |
| Cinderwick b015 | 3 `.`,29 `g`,3 route `r` | 0; Quay Lane s02 |
| Cinderwick b016/b017 | 12 `.` each | 0; Strand s01 |
| Hearthold b033/b034 | 60 /54 `.` | 1 each; Well Lane s09 |
| Hearthold b035 | 76 `.`,1 `g` | 0; Smiths' Row s06 |
| Launch Cape b007/b008/b009 | 48 /48 /91 `g` | 1 /2 /3; Pad Road a1 |

None of these footprints contains literal exported water `~` or barrier `#`. Cape's plots contain 12/12/14 green cells; its doors are green. This does not identify the full raw buildable kind, mask or tier. Hearthold's two Well Lane doors are adjacent to the band, not directly on it; their nearest band column is264.

The historical checker uses a three-cell Chebyshev proximity rule. The producer's `_authored_access` is stricter in other ways: an exterior-ring door, one unambiguous named street, Euclidean distance ≤3.01 and an unobstructed approach over real passability/barrier data. Cape's source-derived Euclidean distances are √2,√8,3 cells. Proximity alone does not prove the approach.

Cinderwick-b015 contains route-coded cells `(312,730), (311,731), (312,731)`. `terrain_rows` collapses raw route kinds to `r`; an `r` cell is not by itself proof of a road-placement fault. [Qualification6476573830](https://github.com/rempemat-eng/appify/pull/334#issuecomment-6476573830) withdraws that earlier inference. The diagnostic regeneration had14 baseline records against committed13, with an unrecorded process hash seed. Do not relocate b015 or clear its ground on that evidence.

An independent source audit also decoded303's exported tier grid, blob `f176bd254ec43349bb34d3cb553252c4a20d80ad`, raw SHA256 `fbeaddf7157f5f9522d51a59c0b66d44132e872f0d5a79a3034a00645f9010ae`: all seven Cinderwick/Hearthold additions, their five private plots, seven doors and two boatyard rectangles occupy exported tier 6. That establishes the stored historical tier values only. Original raw `K, taken, street, barrier, keepout, tiers_pre` and its historical seed are unavailable; neither historical retaining feasibility nor new v56 terrain follows from the export.

For Cape,575px/503px are nearest cottage/workshop edge distances to point `(12085,6455)`, not pad/apron boundary clearances. README303's770px statement needs reconciliation. Current `geo55.py` calculates `buffer_px_to_nearest_house` from **Halcyon Row building centres only**; it would omit proposed Cape cottages. These are different metrics and populations, with no approved clearance threshold.

## Explicit producer adoption for Y35

The existing fixture contract compares exact additions and retained buildings, districts, counts/fronts/extent/size/screens for Hearthold and Cape. Cinderwick retains a conservative route-as-road refusal control. It does not assert equality of the whole exported object to each proposal JSON. Source: [381 test_town_generator_adoption.py](https://github.com/rempemat-eng/appify/blob/3e4ab55920e8cecd384ba468bd819565bb3947d9/scripts/review/test_town_generator_adoption.py), blob `60b65900b6781887ec55fd433939721a62da67aa`. These tests were inspected, not executed for Y38.

355 already provides `Town.adopt`, `PROPOSED_ADOPTIONS`, `lay_all(..., authored=None)`, `hearthold(..., authored=None)` and `launch_cape(..., authored=None)`. Reuse that interface. Its packets pin the exact proposal and baseline commit/blob/path, geometry, purpose, district and contribution; synthetic interface tests are not actual-ground acceptance.

381's actual path is:

1. `geo55.v55_paint` selects `lay_feedback(T,X)` only for v56, otherwise `lay_all(T,X)`.
2. `lay_feedback` invokes `lay_all(T,X)` without an authored selection.
3. `geo55` separately invokes `launch_cape(T,X)` without a selection.

Thus all three proposals remain OFF. `lay_feedback` currently has no `authored` parameter; a later authorised adoption must deliberately carry selections through that path. Committed town JSON is output, not a generator input.

Before selecting any packet, the owning producer task must establish:

- The fresh prospective baseline's complete inventory, ordinal/layout IDs, count contributions, district and street identities. CRC32 fixes future determinism; it cannot recover303's old seed or guarantee its records. Export identity precedence is `layout_id`, then `authored_id`, then ordinal `bNNN`; fixed proposed IDs can collide with a changed baseline.
- For every full footprint and private plot in the table, actual terrain bounds/window, buildable kind, reservations, existing uses, street/barrier/keepout masks and required uniform footprint tier. `Town.adopt` fails on blocked/clipped uses and does not author a terrain-tier change.
- Exact door and street approach on that real ground. Do not widen the existing threshold to obtain adoption.
- Cinderwick's working apron/frontage and shed storage, Hearthold's eastern-workshop ground/retaining relationship, and Cape's staff plots, real pad/apron boundary and nearest-house metric. Whether any terrain adjustment is needed remains an output of that review, not a licence to level whole rectangles blindly.
- Complete re-export of IDs, metadata, contributions, districts, extent, screen/size metadata and associated open uses, preserving the old records only where fresh source actually supports that equivalence.

381 includes378's checker blob `f330fa94673a9d2cea5de49e971f5b6eefe7be08`: full positive whole-cell geometry/bounds, literal water/barrier and mutual-footprint checks occur before the `from_zone_plan` skip. Zone-owned road/door authority remains separate. Y35 refreshes terrain rows from final raw ground and requires all 21 retained town IDs. Its Crossroads 40 / Neon 72 assertions are not first-town proposal count assertions. New `towns-v56`/all-town findings must retain actual failures; diagnostic images do not waive them.

## Source index and delivery boundary

Primary town paths are `docs/vision/research/blockout/towns/<id>.json`.

| Pin | Commit / exact path | Git blob |
| --- | --- | --- |
| Cinderwick proposal | [334 JSON](https://github.com/rempemat-eng/appify/blob/4669140421d7d8c69482fc90b78fea0a50d1d4bc/docs/vision/research/blockout/towns/cinderwick.json) | `9cacbd0833c090c5365d3a9afea84a15ac9c5977` |
| Cinderwick baseline | [303 JSON](https://github.com/rempemat-eng/appify/blob/4984438d09b5fe1333d3e6ea6e6ee82be2bdc908/docs/vision/research/blockout/towns/cinderwick.json) | `b1a6b82b71ba055bf6dc351f81a58766775bf1c4` |
| Hearthold proposal | [335 JSON](https://github.com/rempemat-eng/appify/blob/59f3722d1b39050cc81709fa5933d4c9c093ee98/docs/vision/research/blockout/towns/hearthold.json) | `51fad9db44e2a9be22d2bbb5b007249ae9ecebce` |
| Hearthold baseline | [303 JSON](https://github.com/rempemat-eng/appify/blob/4984438d09b5fe1333d3e6ea6e6ee82be2bdc908/docs/vision/research/blockout/towns/hearthold.json) | `f19a9108cf07a3b8140ba136c04149a8c0ddd31d` |
| Cape proposal | [336 JSON](https://github.com/rempemat-eng/appify/blob/9276174000e47858e92a25803e606fb9dea1fc87/docs/vision/research/blockout/towns/launch-cape.json) | `9aab428f54a898b2c19049857bc092fe39d6e009` |
| Cape baseline | [303 JSON](https://github.com/rempemat-eng/appify/blob/4984438d09b5fe1333d3e6ea6e6ee82be2bdc908/docs/vision/research/blockout/towns/launch-cape.json) | `06faf55d311d78016966c977bedcc7598348b817` |
| Adoption packets355 | [355 towns55.py](https://github.com/rempemat-eng/appify/blob/7afe9efdb3340bd5bb350176c182db4aa0421ebe/docs/vision/research/blockout/towns55.py) | `3cea8b5d316bd6122c836d048a4d5df5dfef885f` |
| Default producer355 | [355 geo55.py](https://github.com/rempemat-eng/appify/blob/7afe9efdb3340bd5bb350176c182db4aa0421ebe/docs/vision/research/blockout/geo55.py) | `20013f98a13b939bdc2ae3789ec92f4b5030db53` |
| Exporter355 | [355 town_plans.py](https://github.com/rempemat-eng/appify/blob/7afe9efdb3340bd5bb350176c182db4aa0421ebe/docs/vision/research/blockout/town_plans.py) | `02e563eb95d1329214bfccef4890a7a498d019be` |
| Current packets/factories | [381 towns55.py](https://github.com/rempemat-eng/appify/blob/3e4ab55920e8cecd384ba468bd819565bb3947d9/docs/vision/research/blockout/towns55.py) | `a227b0714d3c0c28048689fc37de7864faa38de4` |
| Current producer/reporting | [381 geo55.py](https://github.com/rempemat-eng/appify/blob/3e4ab55920e8cecd384ba468bd819565bb3947d9/docs/vision/research/blockout/geo55.py) | `4e198d81f178b6530c714dd39d6f9078d2b11354` |
| Current exporter | [381 town_plans.py](https://github.com/rempemat-eng/appify/blob/3e4ab55920e8cecd384ba468bd819565bb3947d9/docs/vision/research/blockout/town_plans.py) | `f643cdd362d7d81e81f3d9d5eb462d78271d4ebb` |
| Current physical checker | [381 town_plan.py](https://github.com/rempemat-eng/appify/blob/3e4ab55920e8cecd384ba468bd819565bb3947d9/scripts/review/town_plan.py) | `f330fa94673a9d2cea5de49e971f5b6eefe7be08` |
| Adoption contract | [381 town-generator-adoption.md](https://github.com/rempemat-eng/appify/blob/3e4ab55920e8cecd384ba468bd819565bb3947d9/docs/codex/town-generator-adoption.md) | `68dbd747afe868677a200d88791cdedebdc8fcfa` |
| Seed boundary | [355 map-reproduction-contract.md](https://github.com/rempemat-eng/appify/blob/7afe9efdb3340bd5bb350176c182db4aa0421ebe/docs/codex/map-reproduction-contract.md) | `a669c61c001f70cca2c9468af2e3c19cdd8bb3eb` |
| Y35 scope | [381 map-feedback-v56.md](https://github.com/rempemat-eng/appify/blob/3e4ab55920e8cecd384ba468bd819565bb3947d9/docs/codex/map-feedback-v56.md) | `5ce4e246ef32c6dbe5b1dc00e2f82095b5b3681d` |

This review used exact source/blob checks, JSON comparisons, packet AST inspection, literal RLE decoding and bounded street arithmetic, with disjoint peer source audits. No generator, renderer, engine or new full verify/art suite ran. Old proposal checks remain historical; their filtered hosted workflows are NOT RUN, not passes. The336 Y12 [supplement6495050797](https://github.com/rempemat-eng/appify/pull/336#issuecomment-6495050797) remains exit1/incomplete with unsupported SVG, not visual acceptance.

The next executable action is lead review of these source records, followed by a separately allocated real Y35 generation/adoption step on a declared exact source. New full validation and applicable Y12/Matt approvals remain queued; this report grants no adoption, terrain placement or art approval.
