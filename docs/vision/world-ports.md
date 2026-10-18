# Where places meet

Matt, 18 Oct 22:21: "really make sure that the world comes to life as Codex mapped it out and you don't just piece together old work". This file is the checklist against Codex's connected-world design (PR #23: `docs/codex/ideas/connected-world/`, `topology.json`, `biome-extensions.json`, `gameplay-logic.md`). Where this file and the PR disagree, the PR's intent wins unless a line below says why not.

## The rule

Two places that touch are joined only at a declared port, about 48–64 art px wide. Every other stretch of the shared edge is closed by something you can see: a hedge, a park wall, a belt of trees, rock shoulders, dune ridges, basalt. Both zones draw their half of that boundary from world coordinates, so it reads as one hedge across the seam. Water may run across a closed seam; it never opens it.

- Ports live in `scripts/art/frames.py` (`PORTS`) and are exported as `zonePorts` in `lib/zone-maps.ts`.
- The build fails if a port is shut or an edge is open outside its port (`frames.check`). `lib/region-walk.test.ts` checks the same on the stitched region walk.
- The garden's own side is closed in `lib/region-walk.ts`. Its drawn hedge belongs to `garden.py` (Claude B's lane).

## Every seam

| Seam                  | Codex span | Built span | Frame               | Status                                                                    |
| --------------------- | ---------- | ---------- | ------------------- | ------------------------------------------------------------------------- |
| woodland/garden       | 412–468    | 412–468    | tree belt           | matches; garden side's drawn frame is Claude B's                          |
| garden/riverside      | 192–248    | 192–248    | willows             | matches; garden side's drawn frame is Claude B's                          |
| ridge/garden          | 176–232    | 196–216    | trees               | narrower: the garden's trail through its treeline is 16 px. Widen with B. |
| garden/town           | 136–192    | 144–176    | hedge               | the existing garden gate; narrower                                        |
| woodland/halt         | 120–184    | 120–184    | hedge, gateposts    | matches                                                                   |
| halt/town             | 268–324    | 268–324    | hedge, gateposts    | matches                                                                   |
| riverside/park        | 136–192    | 136–192    | willows             | matches                                                                   |
| town/park             | 272–328    | 276–328    | park wall           | matches                                                                   |
| town/harbour          | 136–192    | 136–192    | retaining wall      | matches                                                                   |
| park/headland         | 112–168    | 112–168    | hedge               | matches                                                                   |
| harbour/headland      | 88–144     | 88–144     | rock shoulder       | matches                                                                   |
| hollow/ridge          | 320–376    | 320–376    | fir belt            | matches; the meadow trail west from the ridge's main trail                |
| hollow/woodland       | closed     | closed     | escarpment          | matches                                                                   |
| snowmelt/hollow       | 144–200    | 144–200    | snowy rocks         | matches; the switchback through the scarp                                 |
| snowmelt/saddle       | 248–304    | 248–304    | snowy rocks         | matches; the shore path, over the outflow's footbridge                    |
| saddle/ridge          | 176–232    | 176–232    | rock shoulders      | matches; the switchback down past the cabin's east end                    |
| summit/saddle         | 120–168    | 120–168    | steep snow and rock | matches                                                                   |
| junction/canal        | 128–192    | 128–192    | parapet             | matches                                                                   |
| neon/skyport          | 164–220    | 164–220    | quay wall           | matches                                                                   |
| oasis/gulch           | 496–552    | 296–352    | dune ridges         | kept: the oasis road meets Dust Gulch's main street at mid-height         |
| gulch/scorch          | 204–268    | 356–412    | dune ridges         | kept: the road to the lava bridge leaves the gulch's south yard           |
| scorch/hearthold      | (no seam)  | 140–188    | ash rocks           | Claude's two-bridge Hearthold, which Codex's `gameplay-logic.md` keeps    |
| caldera/hearthold     | (no seam)  | 104–152    | basalt              | the postern, as above                                                     |
| caldera/springs       | 264–320    | 264–320    | basalt              | matches                                                                   |
| rainforest/headwaters | 224–280    | 120–168    | jungle              | **interim**: moves with the isles redraw                                  |
| rainforest/landing    | 128–184    | 172–228    | jungle              | **interim**: redraw                                                       |
| headwaters/cove       | 192–248    | 192–248    | jungle              | matches                                                                   |
| landing/cove          | 352–408    | 352–408    | jungle              | matches                                                                   |

Sunstone Reach is one walking region (Codex's concept map draws it as one land), but it keeps Claude's arrangement that `gameplay-logic.md` asks for: the walk through the Scorched Pass to Hearthold's long south bridge, the postern to the caldera, the mine cart from Dust Gulch to the caldera.

## Still to match Codex's geography

These need redrawing, not only closing:

1. **Tidebloom Isles.** One island in open sea with an organic coast. Lagoon Landing is a sheltered lagoon with a mangrove fringe and the ferry pier. The Rainforest is a stream valley. The Headwaters are an upland, tier 2, with a waterfall gorge; the path skirts the falls. Black-sand Cove is an exposed basalt coast reached by a two-tier terraced descent. Fresh water drains Headwaters → Rainforest → Lagoon, apart from the path. Outer islets and reef are scenery. Today the island is a rectangle of turf.
2. **Frostline Highlands.** Redrawn 18 Oct as one landscape in the valley's coordinates (`frost_zones.py`). Fir Hollow is a sheltered fir bowl with snow patches growing up the slope, closed by the escarpment above the Woodland. Snowmelt Lake is a cirque. Its outflow crosses under the shore path's footbridge, runs south through the hollow, falls over the escarpment and feeds the Woodland's spring, the garden's stream. That route differs from Codex's (via the ridge); the water reaches the valley river either way. The Saddle is a broad treeless shoulder with a switchback through stepped rock shoulders to the cabin. The Lookout is a flagged terrace at the end of a short broad path. Steep ground is drawn as rock buttresses and gullies, plainly not walkable.
3. **The valley's water.** The river rises below the ridge, crosses the garden's lower terrace, turns south through Riverside and the Park and reaches the sea at Driftwood's estuary. Today the Riverside river runs off east and the Park has a pond.
4. **Driftwood's ferry pier.** It should be a named pier with the boat moored, linked to the harbour lane (play-test finding 15).
