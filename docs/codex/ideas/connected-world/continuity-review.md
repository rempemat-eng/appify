# Route continuity review

Status: abstract design logic checked; marked landscape corrections and the final named ferry piers visually inspected on 18 October 2026. Suitable for a **draft design handoff**, not production terrain approval. No claim that graph checks validate landscape pixels or actual game collision grids. The final landscape is `world-concept.png`; the exact segment/transport contracts and logical map take precedence when Claude draws detailed terrain.

## What went wrong

The original illustration used the vocabulary of paths and railways without consistently drawing their physical endpoints. The graph correctly named services, but that did not make the pixels correct. Matt identified conventional rail changing into a path, a missing Cogsworth station connection, unsupported-looking crossings, stray volcanic track and ambiguous access to small props. These are render defects, not permission to add transport edges.

The validation boundary is now explicit: the logical sheet is generated from the contracts; the landscape is separately inspected against it. A graph pass is not a visual release gate. Future art must be reviewed at each approach/platform, not only at whole-map scale.

The last pass was reviewed for the continuous Cogsworth through-track, separate maglev platform and Skyport terminus, the removed upper Caldera spur, the dry stepped ridge terrace, supported river/coastal footbridges, removed isolated desert/sea-stack buildings, and the named Driftwood Ferry / Lagoon Ferry piers. These are visible conceptual corrections, not measured terrain or pathfinder evidence. Terrain-local bridge dimensions, actual underpasses, bank collision cells and platform standing points remain Claude's later greybox checks.

## Marked locations and required outcome

| Location                           | Required physical interpretation                                                                                                                         |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cogsworth west / waterfall railway | Continuous conventional rails on supported deck into a through-platform and onward to Dust Gulch. No dirt-path substitute or track ending at facade.     |
| Cogsworth interchange              | Conventional train and blue maglev platforms are separate, joined by a dry pedestrian forecourt.                                                         |
| Skyport                            | Maglev enters a same-height boarding platform and terminates at a buffer; pedestrian promenade does not become guideway.                                 |
| Caldera                            | One mine-cart terminal on solid basalt with buffers. Remove the unrelated upper looping spur; no platform on molten lava.                                |
| Upper river foot crossing          | Water underneath a supported deck; dry approaches on both banks, downstream fall below the crossing.                                                     |
| Ridge cliff approach               | Continuous switchback on a real terrace. It is part of the Garden–Ridge approach, not an extra Ridge–Riverside seam or a vertical-face shortcut.         |
| Garden / Riverside crossing        | Dry path on both landings, no prop blocking the abutment, no walking onto river water.                                                                   |
| Driftwood / Headland crossing      | Supported pedestrian bridge joins both dry coast paths; slope/steps finish on land, not sea.                                                             |
| Isolated desert hut / ruin group   | Remove from this footprint rather than inventing extra destinations and routes to justify spare assets.                                                  |
| Sea stack below Hearthold          | Natural scenery only: remove a building/door/path implying an inaccessible visitable place.                                                              |
| Proposed sea link                  | Both endpoints are named reachable piers in Driftwood and Lagoon Landing; intermediate route stays over open water. No lighthouse or black-sand landing. |

## Logical release checks

- Every ordinary walk edge has one owner, reciprocal ports, cell-aligned width, consistent lateral arrival and a visible closed boundary outside its span. No diagonal corner escape.
- Frostline's loop starts beyond the existing cabin approach; the existing mountain mission remains at Ridge. The shared Fir Hollow–Woodland scarp is closed.
- Tidebloom's loop is continuous on one main island. Outer reef/islets are scenery, not stepping stones or new collection goals.
- Conventional railway: Valley Halt–Cogsworth–Dust Gulch, with a through-platform at Cogsworth and buffers at the two ends.
- Mine-cart line: separate Gulch bay–Caldera; no castle track. Maglev: separate Cogsworth platform–Skyport.
- Six current service edges remain exactly covered; the island boat candidate is separately proposed, not a current service or new runtime rule.
- Existing return, Quiet view, mission settlement, currency, rewards and save data are untouched. Final terrain and a real versioned migration remain separate integration work.

## Still required before live use

Actual generated dry/support/water/rail/elevation masks, every bridge landing and platform connection, route component flood fill, art-scale-to-screen framing, stop-ID adapter, lossless save/read/write/reload migration, interruption and Back/Home behaviour, and browser/native validation. A static rendering or synthetic grid does not provide these.
