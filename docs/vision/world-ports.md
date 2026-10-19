# Where places meet

Matt, 18 Oct 22:21: "really make sure that the world comes to life as Codex mapped it out and you don't just piece together old work". This file is the checklist against Codex's connected-world design (PR #23: `docs/codex/ideas/connected-world/`, `topology.json`, `biome-extensions.json`, `gameplay-logic.md`). Where this file and the PR disagree, the PR's intent wins unless a line below says why not.

## The rule

**Changed 19 Oct (Matt: "there do not need to be boundaries everywhere, only where they need to be for gameplay purposes").** Neighbouring places are open land: meadow runs into meadow, desert into desert. A border closes only where the world itself would stop you: a cliff or height change, water, lava, the garden's fence, castle walls. Where one does, it is a real feature drawn by the zone (a scarp, rock shoulders, a fence), never a band painted on the seam. Codex's spans stay as the place where the way through a closed border goes.

- `frames.PORTS` gives each shared edge its state: `OPEN` (open land), a span (closed by the land except there) or closed. They are exported as `zonePorts` in `lib/zone-maps.ts`.
- The build fails if a state is broken (`frames.check`), and so does `lib/region-walk.test.ts`.
- See `art-faults.md` for the rest of what Matt found on 19 Oct.

## Every seam

| Seam                  | Codex span | Now       | What closes it                                                   |
| --------------------- | ---------- | --------- | ---------------------------------------------------------------- |
| woodland/garden       | 412–468    | open land | nothing: open land                                               |
| garden/riverside      | 192–248    | open land | nothing: open land                                               |
| ridge/garden          | 176–232    | 196–216   | the garden's treeline, open at its trail                         |
| garden/town           | 136–192    | 144–176   | the garden's fence and gate                                      |
| woodland/halt         | 120–184    | open land | nothing: open land                                               |
| halt/town             | 268–324    | open land | nothing: open land                                               |
| riverside/park        | 136–192    | open land | nothing: open land                                               |
| town/park             | 272–328    | open land | nothing: open land                                               |
| town/harbour          | 136–192    | open land | nothing: open land                                               |
| park/headland         | 112–168    | open land | nothing: open land                                               |
| harbour/headland      | 88–144     | open land | nothing: open land                                               |
| hollow/ridge          | 320–376    | open land | nothing: open land                                               |
| hollow/woodland       | closed     | closed    | the escarpment                                                   |
| snowmelt/hollow       | 144–200    | open land | open below the scarp, which is the step up                       |
| snowmelt/saddle       | 248–304    | open land | the saddle's flank closes the rest                               |
| saddle/ridge          | 176–232    | 176–232   | the rock shoulders                                               |
| summit/saddle         | 120–168    | 116–172   | the steep ground below the lookout                               |
| junction/canal        | 128–192    | open land | nothing: open land                                               |
| neon/skyport          | 164–220    | open land | nothing: open land                                               |
| oasis/gulch           | 496–552    | 496–552   | dune ridges, open at the oasis track                             |
| gulch/scorch          | 204–268    | 356–412   | dunes frame (owner to review)                                    |
| hearthold/scorch      | (no seam)  | 140–188   | ash frame (owner to review)                                      |
| caldera/hearthold     | (no seam)  | 104–152   | basalt frame (owner to review)                                   |
| caldera/springs       | 264–320    | 264–320   | basalt frame (owner to review)                                   |
| rainforest/headwaters | 224–280    | 224–280   | the escarpment and the gorge's rim; the switchback up the recess |
| rainforest/landing    | 128–184    | 128–184   | the escarpment; the broad stair                                  |
| headwaters/cove       | 192–248    | 192–248   | the escarpment; the first stair of the descent                   |
| landing/cove          | 352–408    | open land | nothing: both at sea level, the land runs on                     |

Sunstone Reach is one walking region (Codex's concept map draws it as one land), but it keeps Claude's arrangement that `gameplay-logic.md` asks for: the walk through the Scorched Pass to Hearthold's long south bridge, the postern to the caldera, the mine cart from Dust Gulch to the caldera.

## Still to match Codex's geography

These need redrawing, not only closing:

1. **Tidebloom Isles** (redrawn by Claude C, 18 Oct: I1 the shape and water, I2 the heights, I3 the detail pass; I4 against art-faults.md, 19 Oct). The island is drawn whole in island coordinates (`isle_zones.island()`) and cut per zone. Coast, lagoon, mangroves, the stream valley, the black-sand cove, the outer islets and the reef follow Codex's section 10. The tiers are basalt escarpments along the zone borders: Landing 0, Rainforest 1, Headwaters 2, Cove 0, with a terrace (tier 1) between the Headwaters and the Cove. The ways through are a broad stair (landing/rainforest), a switchback beside the waterfall gorge (rainforest/headwaters), and two stairs round the east shoulder (headwaters, terrace, cove). Footbridges cross the river on dry abutments above the falls' lip. No frame bands: the escarpments and the gorge's rim close the three height seams, and the landing and the cove run into each other as open land.
2. **Frostline Highlands.** Redrawn 18 Oct as one landscape in the valley's coordinates (`frost_zones.py`). Fir Hollow is a sheltered fir bowl with snow patches growing up the slope, closed by the escarpment above the Woodland. Snowmelt Lake is a cirque. Its outflow crosses under the shore path's footbridge, runs south through the hollow, falls over the escarpment and feeds the Woodland's spring, the garden's stream. That route differs from Codex's (via the ridge); the water reaches the valley river either way. The Saddle is a broad treeless shoulder with a switchback through stepped rock shoulders to the cabin. The Lookout is a flagged terrace at the end of a short broad path. Steep ground is drawn as rock buttresses and gullies, plainly not walkable.
3. **The valley's water.** The river rises below the ridge, crosses the garden's lower terrace, turns south through Riverside and the Park and reaches the sea at Driftwood's estuary. Today the Riverside river runs off east and the Park has a pond.
4. **Driftwood's ferry pier.** It should be a named pier with the boat moored, linked to the harbour lane (play-test finding 15).
