# Where places meet

Matt, 18 Oct 22:21: "really make sure that the world comes to life as Codex mapped it out and you don't just piece together old work". This file is the checklist against Codex's connected-world design (PR #23: `docs/codex/ideas/connected-world/`, `topology.json`, `biome-extensions.json`, `gameplay-logic.md`). Where this file and the PR disagree, the PR's intent wins unless a line below says why not.

## The rule

Two places that touch are joined only at a declared port, about 48–64 art px wide. Every other stretch of the shared edge is closed by something you can see: a hedge, a park wall, a belt of trees, rock shoulders, dune ridges, basalt. Both zones draw their half of that boundary from world coordinates, so it reads as one hedge across the seam. Water may run across a closed seam; it never opens it.

- Ports live in `scripts/art/frames.py` (`PORTS`) and are exported as `zonePorts` in `lib/zone-maps.ts`.
- The build fails if a port is shut or an edge is open outside its port (`frames.check`). `lib/region-walk.test.ts` checks the same on the stitched region walk.
- The garden's own side is closed in `lib/region-walk.ts`. Its drawn hedge belongs to `garden.py` (Claude B's lane).

## Every seam

| Seam                  | Codex span | Built span | Frame            | Status                                                                       |
| --------------------- | ---------- | ---------- | ---------------- | ---------------------------------------------------------------------------- |
| woodland/garden       | 412–468    | 412–468    | tree belt        | matches; garden side's drawn frame is Claude B's                             |
| garden/riverside      | 192–248    | 192–248    | willows          | matches; garden side's drawn frame is Claude B's                             |
| ridge/garden          | 176–232    | 196–216    | trees            | narrower: the garden's trail through its treeline is 16 px. Widen with B.    |
| garden/town           | 136–192    | 144–176    | hedge            | the existing garden gate; narrower                                           |
| woodland/halt         | 120–184    | 120–184    | hedge, gateposts | matches                                                                      |
| halt/town             | 268–324    | 268–324    | hedge, gateposts | matches                                                                      |
| riverside/park        | 136–192    | 136–192    | willows          | matches                                                                      |
| town/park             | 272–328    | 276–328    | park wall        | matches                                                                      |
| town/harbour          | 136–192    | 136–192    | retaining wall   | matches                                                                      |
| park/headland         | 112–168    | 112–168    | hedge            | matches                                                                      |
| harbour/headland      | 88–144     | 88–144     | rock shoulder    | matches                                                                      |
| hollow/ridge          | 320–376    | 144–200    | firs             | **interim**: moves with the Frostline redraw                                 |
| hollow/woodland       | closed     | closed     | escarpment       | matches                                                                      |
| snowmelt/hollow       | 144–200    | 120–148    | snowy rocks      | **interim**: redraw                                                          |
| snowmelt/saddle       | 248–304    | 404–436    | snowy rocks      | **interim**: redraw (with the footbridge over the lake's outflow)            |
| saddle/ridge          | 176–232    | 172–196    | snowy rocks      | **interim**: redraw                                                          |
| summit/saddle         | 120–168    | 140–164    | snowy rocks      | **interim**: redraw                                                          |
| junction/canal        | 128–192    | 128–192    | parapet          | matches                                                                      |
| neon/skyport          | 164–220    | 164–220    | quay wall        | matches                                                                      |
| oasis/gulch           | 496–552    | 296–352    | dune ridges      | kept: the oasis road meets Dust Gulch's main street at mid-height            |
| gulch/scorch          | 204–268    | 356–412    | dune ridges      | kept: the road to the lava bridge leaves the gulch's south yard              |
| scorch/hearthold      | (no seam)  | 140–188    | ash rocks        | Claude's two-bridge Hearthold, which Codex's `gameplay-logic.md` keeps       |
| caldera/hearthold     | (no seam)  | 104–152    | basalt           | the postern, as above                                                        |
| caldera/springs       | 264–320    | 264–320    | basalt           | matches                                                                      |
| rainforest/headwaters | 224–280    | 224–280    | jungle           | matches: the switchback up the escarpment beside the waterfall gorge         |
| rainforest/landing    | 128–184    | 128–184    | jungle           | matches: the broad stair at the escarpment, the river's cascade west of it   |
| headwaters/cove       | 192–248    | 192–248    | basalt           | matches: the first stair of the terraced descent (the second is in the cove) |
| landing/cove          | 352–408    | 352–408    | basalt           | matches: the shore path round the basalt headland                            |

Sunstone Reach is one walking region (Codex's concept map draws it as one land), but it keeps Claude's arrangement that `gameplay-logic.md` asks for: the walk through the Scorched Pass to Hearthold's long south bridge, the postern to the caldera, the mine cart from Dust Gulch to the caldera.

## Still to match Codex's geography

These need redrawing, not only closing:

1. **Tidebloom Isles** (redrawn by Claude C, 18 Oct: I1 the shape and water, I2 the heights; I3, the detail pass, is still to come). The island is drawn whole in island coordinates (`isle_zones.island()`) and cut per zone. Coast, lagoon, mangroves, the stream valley, the black-sand cove, the outer islets and the reef follow Codex's section 10. The tiers are basalt escarpments along the zone borders: Landing 0, Rainforest 1, Headwaters 2, Cove 0, with a terrace (tier 1) between the Headwaters and the Cove. The ways through are a broad stair (landing/rainforest), a switchback beside the waterfall gorge (rainforest/headwaters), and two stairs round the east shoulder (headwaters, terrace, cove). Footbridges cross the river on dry abutments above the falls' lip. The landing/cove border is the basalt headland.
2. **Frostline Highlands.**
   - Fir Hollow is sheltered firs with patchy snow, closed above the woodland by an escarpment.
   - Snowmelt Lake is a cirque. Its outflow stream is crossed by a footbridge at the saddle port and drains through the hollow and the ridge toward the valley river.
   - The Saddle is a broad treeless shoulder with a switchback down to the cabin.
   - High Lookout is a short, broad terminal spur.
   - The snowline follows height. Today the snow places are flat white fields with tile seams (play-test 18 Oct, findings 4 and 5).
3. **The valley's water.** The river rises below the ridge, crosses the garden's lower terrace, turns south through Riverside and the Park and reaches the sea at Driftwood's estuary. Today the Riverside river runs off east and the Park has a pond.
4. **Driftwood's ferry pier.** It should be a named pier with the boat moored, linked to the harbour lane (play-test finding 15).
