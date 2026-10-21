# Placement logic, realistic paths and verticality for NapAttack

Research for NapAttack's zone generators (320x576 px zones, 4 px walk cells, so 80x144 cells per zone, three-quarter view, light from the upper left). Written 19 Oct 2026.

How to read this. Claims about games, algorithms and papers carry a source URL. Where no credible source was found, the text says **(observation, unsourced)** or **(inference)**. Numbers marked "starting point" are my proposals to tune in play, not sourced values. This report builds on `docs/vision/world-rules.md` and `docs/research/2d-world-design.md` in the repo. Those already define terrain classes, placement types and lint checks 1 to 20, so this report adds what they lack: how to *test* each rule on the data, a path generator, and a two-level walk model.

---

## 0. What the sources say, in short

- **Placement**
  - Good placement comes from rules that a generator enforces, not from hand-fixing.
  - Stardew Valley shows the pattern exactly. A fruit tree "must be planted in the center of a clear 3x3 ground area" that is "free of objects, flooring/paths, and terrain features" (https://stardewvalleywiki.com/Fruit_Trees).
  - Bad North's WFC generator gives each tile "its navigability" and "wouldn't place the house tiles if it wasn't navigable". It restarts an island that cannot satisfy its constraints (https://www.gamedeveloper.com/game-platforms/how-townscaper-works-a-story-four-games-in-the-making).
- **Paths**
  - The standard recipe is a least-cost search over a terrain cost field, then smoothing, then carving the corridor into the terrain (Galin et al. 2010, https://perso.liris.cnrs.fr/egalin/Articles/2010-roads.pdf).
  - A steepness cost that grows faster than linearly makes paths wind and switchback naturally (https://www.gamedeveloper.com/programming/creating-natural-paths-on-terrains-using-pathfinding).
  - Hierarchies are built top-down, with minor roads reusing major ones (Galin et al. 2011, https://www.cs.purdue.edu/homes/bbenes/papers/Galin11CGF.pdf).
  - Junctions come from snapping and pruning rules (Parish and Müller 2001, https://cgl.ethz.ch/Downloads/Publications/Papers/2001/p_Par01.pdf).
  - Real footpaths form by reinforcement, as a compromise between directness and comfort (Helbing et al., https://ar5iv.labs.arxiv.org/html/cond-mat/9805158).
- **Verticality**
  - Top-down 2D handles height with discrete layers or levels. Each level has its own ground or collision, and explicit connectors change the level: stairs, ledges, jump panels, trigger rows.
  - Draw order is a y-sort within a level, with levels drawn in order.
  - The best modern examples show the lower level *under* the upper one instead of cutting to a closed room. Nintendo did this deliberately in A Link Between Worlds (https://iwataasks.nintendo.com/interviews/3ds/a-link-between-worlds/0/4).

---

## 1. Placement logic: rules and how to test them

### 1.1 Data the checks need

All of these exist or nearly exist in the repo (`zoneTerrain`, `zonePlacement`, the walk grid and the prop lists in `scripts/art/world_lint.py`).

- `terrain[y][x]`: the class per 4 px cell (`~ - , ^ . = # * ! B R`).
- `tier[y][x]`: the integer elevation tier per cell. This is **new**. It is needed for the level-ground, slope and stair checks.
- `walk[level][y][x]`: walkable per level. Today there is one level. Section 3 adds a deck level.
- Prop list: `key, x, y, w, h, placement, foot cells`. **New optional fields**:
  - `facing` (N/E/S/W or a target class)
  - `door` (cell offset of a door)
  - `encloses` (for fences)
  - `kind` (tree/plant/furniture/sign/actor/animal)
  - `species` (for vegetation rules)
  - `height_px` (for shadows and scale)
- `nodes`: exits, doors, plazas, jetties, benches, stalls, each with an importance.
- A path graph: the skeleton of the `=` mask, with each segment's grade.

### 1.2 The checklist

For each rule: the rule, then the source or rationale, then the automatic test. "Foot cells" are the cells under a prop's base or trunk, not its canopy, as in `_foot_cells` in the lint.

**A. Footing and support**

1. **Footing matches placement type.** Ground props stand on ground, floor or the region's surface. Floating props sit on water. Supported props sit over water or a gap and show drawn supports. Wet props stand on bank or beach.
   - Source: Solarus, an ALttP-style engine, gives every tile a ground type and queries "ground per point and per layer". Its types include `deep_water`, `shallow_water`, `hole`, `ladder` and `lava` (https://docs.solarus-games.org/lua-api/map/). Pokémon's Castelia pier design note: "Since it is pier, it is floating on the sea" (https://siliconera.com/excerpts-from-pokemon-black-whites-castelia-city-design-documents/).
   - Test (exists as check 1): `set(terrain[c] for c in foot_cells) ⊆ ALLOWED[placement]`.
2. **Supported structures have supports.** Check that a jetty, deck, bridge or balcony has a support every N cells.
   - Test: for each `supported` prop, sample its span every N cells along its long axis (starting point: N = 8 cells = 32 px). Require a pier, post or abutment sprite whose foot cell lies on a bearing class (ground, bank, rock) or is a declared pile in water. Both ends must touch a bearing class.
3. **Nothing hangs in air.** Overhead props (bunting, cables, signs on brackets) must have both anchor points on a post, wall or building.
   - Test: each `overhead` prop declares `anchors=[(x,y),...]`. Each anchor must lie inside a prop of kind post, wall or building, or inside a `B` cell.
4. **Heavy things stand on level ground.** Buildings, wells, stalls and wagons must not straddle a tier change, a path or water.
   - Test: `len(set(tier[c] for c in footprint)) == 1`, and the footprint shares no cell with `{=, ~, -, ^, !}`. Allow an exemption only if a `plinth` or `terrace` prop covers the low side.
5. **No one stands in water.** People and non-swimming animals must not stand in water. Swimmers and waders must be in water.
   - Test: an actor's foot cell is never in `{~, -}` unless the actor's kind is in `{duck, swan, fish, boat, wader}`. A wader may be on `-` only. This is the existing `stand-in-water` check, extended to residents' route waypoints.

**B. Paths, doors and gates stay clear**

6. **No plant, rock or furniture in the walking band.** Matt: "neither should trees be in a path".
   - Test (exists as `plant-on-path`): first erode the path mask by 0 cells for grade 3 and by 1 cell for grades 1 and 2, so a verge lamp may touch the edge. Then any foot cell of kind tree, bush, rock, stump, crop or furniture inside the eroded mask fails. A canopy may overhang. A trunk may not.
7. **Minimum path width by grade.** Measure the width with a distance transform on the path mask. Along each skeleton pixel, `width = 2 × dist`. Fail if more than 10% of a segment is below its grade's minimum.
   - Starting points, which keep the 44 screen-px tap rule at scale 4, where 11 native px is about 3 cells:
     - grade 1 road: 8 to 12 cells (32 to 48 px)
     - grade 2 lane: 5 to 7 cells
     - grade 3 footpath: 3 to 4 cells
     - trail or desire line: 2 to 3 cells, drawn as worn grass, with walkability coming from the ground anyway
   - Also fail if a segment's width varies by more than about ±35%. That would read as a puddle, not a path.
8. **Doors open onto standing space.** Check a door apron: the 3x3-cell rectangle (12x12 px, starting point) directly in front of the door (south of it in three-quarter view, unless the door faces sideways).
   - Every apron cell must be walkable at the door's level.
   - The apron shares no cell with a prop footprint.
   - The apron is connected by BFS over `walk` to a zone exit.
   - This is the existing `door-shut-in` check, plus the BFS. Stardew's building data supports the idea of "clear space in front" as data: buildings carry flags such as `FadeWhenBehind` and `DrawShadow` (https://forums.stardewvalley.net/threads/mod-to-turn-off-transparency-of-farm-buildings.30012/latest).
9. **Gates sit in fences, and fences enclose something.**
   - Test (a), gate: the cells left and right of a gate (or above and below, for a side gate) belong to fence, hedge or wall props. A path skeleton passes through the gate's opening.
   - Test (b), fence ends: rasterise all fence, hedge and wall props into a barrier mask. Every barrier polyline end must touch a post, a corner, a building, a cliff, water or the zone border. A fence that ends in open grass fails.
   - Test (c), enclosure: flood-fill the non-barrier cells, treating barrier, water, cliff and building as walls. Each fenced region that is neither the outside nor a fully open area must contain at least one prop of kind in `ENCLOSABLE` (animal, crop, garden bed, well, washing line, yard prop) and have at least one gate.
   - Townscaper has the same rule: "unless you build an entirely enclosed area, there's no way to place the garden pieces at all" (https://www.gamedeveloper.com/game-platforms/how-townscaper-works-a-story-four-games-in-the-making).
10. **Everything interactive is reachable.**
    - Test: run a multi-source BFS from all zone exits over `walk` (per level, through connectors once section 3 exists). Every door apron, interactive prop standing point, bridge end, stair end and exit must be reached. All exits must be mutually reachable.
    - Bad North asks the same question: "how do you ensure there's always a path from the beach to the houses?" (same Townscaper source).

**C. Purpose and orientation**

11. **Things face what they are for.**
    - Test: a prop with `facing=D` casts a ray of length r from its front in direction D, and the ray must hit the target class:
      - bench: path, plaza or a view (water, cliff edge), r = 3 cells
      - fisher: water, r = 3
      - vendor and stall: path or plaza, r = 2
      - market counter: plaza, r = 2
      - grave and statue: path, r = 4
      - mailbox and sign: path, r = 2
    - Rationale: environmental storytelling. Props should let the player infer "who put it there, what for" (Smith and Worch, GDC 2010, https://gdcvault.com/play/1012647/What-Happened-Here-Environmental). The specific ray test is my inference.
12. **Signs at junctions, gates and exits.**
    - Test: skeletonise the path mask and find skeleton nodes of degree 3 or more (junctions) and the cells where a path crosses an exit or gate. Each sign must lie within 4 cells of one of these.
    - Soft check: each grade-1 junction should have a sign or lamp within 4 cells. Lamps are already restricted to grade 1, gates and doors (check 13).
    - Rationale: Lynch's nodes and landmarks. A 2025 study found landmarks and edges clearly apply to game worlds (https://cs.wellesley.edu/~pmwh/mvmap/papers/open_world_elements/open_world_elements.html).

**D. Light, shadow and scale**

13. **Shadows fall down-right, and length tracks height.**
    - Test per sprite: find the pixels in the shadow palette indices. Their centroid relative to the footprint centre must have `dx ≥ 0` and `dy ≥ 0`.
    - Shadow extent divided by `height_px` must stay within ±25% of the region median (starting point).
    - Also check lit edges: the mean luminance of the top-left outline must be at least the mean of the bottom-right outline.
    - This automates check 17. The upper-left light is the house rule (AGENTS.md).
14. **One scale.**
    - Test: keep a table of reference sizes per kind, for example door height, bench length, cottage width in doors, tree height relative to eaves. Fail any sprite whose bounding box falls outside its kind's range.
    - Also fail if a door is shorter than the companion's sprite height plus 2 px.
    - Rationale: in the slanted three-quarter view, Nintendo "purposefully tilted the objects back so you could see Link and the others' faces and bodies". The look is a consistent fudge, applied the same way to everything (https://iwataasks.nintendo.com/interviews/3ds/a-link-between-worlds/0/3).

**E. Living things**

15. **Vegetation by moisture and light.**
    - Compute `moisture = f(distance to fresh water)`, following Red Blob: "moisture is the distance to fresh water"; biome comes from elevation and moisture via a Whittaker-style table (http://www-cs-students.stanford.edu/~amitp/game-programming/polygon-map-generation/; https://www.redblobgames.com/maps/terrain-from-noise/#biomes).
    - Compute `shade` as cells under tree crowns, plus a band north of buildings and cliffs. In upper-left light, shade falls down-right, but tall objects also shade the ground behind them.
    - Each species gets ranges `{moisture: [a,b], shade: [c,d], tier: [e,f], classes: {...}}`. Test each plant's foot cell against its species range. Examples: reeds need distance to still water ≤ 2 cells. Ferns need shade above 0.5. Pines need a high tier.
    - Plant distributions should reflect "the interactions of plants with each other and with their environment" (Deussen et al., SIGGRAPH 98, https://algorithmicbotany.org/papers/ecosys.sig98.html).
16. **Spacing (no clumped duplicates, no grid look).**
    - Test: for each pair of same-kind props, `distance ≥ r_kind`. Fruit-tree analogue: Stardew enforces at least two tiles between fruit trees' clear areas (https://stardewvalleywiki.com/Fruit_Trees).
    - For generation, use Poisson disc or a jittered grid. Red Blob: "I recommend using Poisson Disc or a jittered grid instead of high frequency Simplex/Perlin noise", with radius varying by biome for density (https://www.redblobgames.com/maps/terrain-from-noise/#trees).
17. **Animals where they belong.**
    - Test: grazing animals' foot cells lie inside an enclosure region from rule 9c, or on the ground class of a declared pasture. They are never on a path of grade 1 or 2, a roof or water.

**F. Water and crossings**

18. **Bridges at narrow points, ending on paths.**
    - Test: for each bridge, compute the water body's crossing width along the bridge axis at offsets of ±10 cells. Fail if the bridge span is more than 1.3 × the minimum nearby width.
    - Both bridge ends must touch a path cell, and that path must reach a node (check 5).
    - Source: road generators give bridges their own cost, so the least-cost route picks short spans. In Galin et al., bridge cost depends on bridge height, slope and "the depth of water crossed" (https://perso.liris.cnrs.fr/egalin/Articles/2010-roads.pdf).
    - In Parish and Müller, only highways may cross an illegal area "up to a specified length", and that crossing becomes "a bridge, or two tunnel entrances". Streets instead prune or rotate to stay legal (https://cgl.ethz.ch/Downloads/Publications/Papers/2001/p_Par01.pdf).

**G. Height**

19. **Height changes only at a drawn connector.**
    - Test: for each pair of 4-adjacent walkable cells, if `tier` differs, the pair must lie on a stair, ramp, ladder or slope cell. Cells adjacent across a cliff `^` may not both be walkable.
    - Every stair has a path cell at both ends, and those paths reach nodes (check 8).
20. **One-way drops are deliberate.**
    - A ledge you can jump down but not climb is a classic Pokémon device. Players "jump over ledges and land on the other side, but may not climb back up", often as shortcuts back to earlier areas (https://bulbapedia.bulbagarden.net/wiki/Ledge).
    - Test: a one-way edge `(a→b)` requires `tier[a] = tier[b] + 1`, an arrow-readable ledge sprite, and a two-way route from b back to a somewhere else in the region (no soft-lock).

**H. Overrides**

21. **Overrides need a reason.** This exists as check 18. Keep the Bad North rule: hard constraints fail, soft constraints may be relaxed, and a generator that cannot satisfy hard constraints should **restart with a new seed**, not ship (Townscaper source above).

---

## 2. Paths that look real

### 2.1 How real paths form (and what generators copy)

- **Desire lines are a compromise.** In Helbing's trail model, "at the beginning, pedestrians take the direct ways to their respective destinations". Later they reuse trails "since this is more comfortable than to clear new ways".
  - The final network is conjectured to be "the shortest one which is compatible with a certain accepted relative detour".
  - Trails "begin to bundle, especially where different trails meet or intersect". Nodes are either straight crossings or places where two trails "smoothly merge into one trail" (https://ar5iv.labs.arxiv.org/html/cond-mat/9805158).
  - Pedestrian systems become a "minimal detour system" (https://ar5iv.labs.arxiv.org/html/cond-mat/9806097).
  - **Implication**: Y-shaped merges for footpaths, T-junctions where a lane meets a road, few true crossroads.
- **Desire-path simulation as a generator.**
  - Cogmind (Grid Sage Games) plots "a path between every point and every other point". It weights each path by the average importance of its two endpoints. It caps connection range and detour length, then fuzzes each path by adding "half its value to adjacent non-path tiles" so worn areas are soft-edged. Overlapping routes accumulate value (https://www.moddb.com/news/desire-paths-for-a-robot-world).
  - An academic version: Procedural Location of Roads Using Desire Paths (CEIG 2019) generates many optimal paths under different cost functions and turns them into walkability and habitability maps for placing roads and buildings (https://diglib.eg.org/handle/10.2312/ceig20191199).
- **Shortest path over a cost field.**
  - Red Blob: movement costs make Dijkstra and A* route around expensive terrain: "walking through water cost 10 times as much as walking through grass". A* is optimal "as long as the heuristic does not overestimate distances" (https://www.redblobgames.com/pathfinding/a-star/introduction.html).
- **Slope cost, winding and switchbacks.**
  - Rune Johansen (runevision) found that a linear height penalty only stopped paths going up and down. The fix: "penalize steep slopes more than linearly, for example by squaring it".
  - He recommends power 2 with a multiplier of 3 to 15 depending on how straight or winding the path should be.
  - He uses 16 neighbour directions instead of 8 to avoid "very small-scale zig-zags" (https://www.gamedeveloper.com/programming/creating-natural-paths-on-terrains-using-pathfinding).
  - Switchbacks emerge on their own when the slope cost dominates **(inference from that article's results)**.
- **Road generation papers.**
  - Galin et al. 2010 define the cost as a sum of transfer functions of slope, curvature, water depth and vegetation density. Each function returns infinity above a threshold, which makes that ground impassable.
  - They search on a grid with a k-neighbourhood mask of segments to points (i,j) in [−k,k]² with gcd(i,j)=1. k=1 gives 8 directions (45°), k=2 gives 16 (26.5°), and they use k=5.
  - Bridges and tunnels are long edges in separate masks.
  - The path is then fitted with clothoids and the terrain is graded inside a corridor: vegetation inside it is removed, and heights blend between the road profile and the terrain (https://perso.liris.cnrs.fr/egalin/Articles/2010-roads.pdf).
  - Galin et al. 2011 build hierarchies top-down (highways, then major, then minor). They add a cost that discourages new roads near existing ones, and minor roads "should reuse the existing major road network as much as possible". Where routes run close, Steiner points become "intersections and interchanges", and a merged road takes the higher type (https://www.cs.purdue.edu/homes/bbenes/papers/Galin11CGF.pdf).
- **Junction rules (Parish and Müller 2001).**
  - When a new segment ends in water or a park, the generator first tries "Prune the segment length", then "Rotate the segment within a maximal angle until it is completely inside the legal area". The rotation is how roads come to follow coastlines.
  - On intersecting another segment, "the road is pruned and a crossing is generated".
  - Within a distance of an existing crossing, the road is extended "to reach the crossing". After a crossing is created, the road stops growing.
  - Their San Francisco pattern makes roads follow the lowest elevation, with short steep connectors between height levels (https://cgl.ethz.ch/Downloads/Publications/Papers/2001/p_Par01.pdf).
- **Following contours.**
  - Red Blob's polygon map generator draws roads along contour lines: "Where the contour level changes, there's a road". They are drawn as splines from edge midpoint to midpoint (http://www-cs-students.stanford.edu/~amitp/game-programming/polygon-map-generation/).
- **Ugly grid paths and smoothing.**
  - On grids "there can be more than one shortest path of the same length".
  - Red Blob lists the fixes: any-angle search (Theta*), "string pulling", nudging tie costs, and alternating neighbour order on a checkerboard (https://www.redblobgames.com/pathfinding/a-star/implementation.html#troubleshooting-ugly-path).
  - Chaikin corner cutting replaces each segment P_i P_{i+1} with points at 1/4 and 3/4 along it. Repeating it converges to a quadratic B-spline (https://www.cs.unc.edu/%7Edm/UNC/COMP258/LECTURES/Chaikins-Algorithm.pdf).
  - For road-like curves, circular arcs and biarcs are an option (https://www.redblobgames.com/articles/curved-paths/).
- **Natural edges.**
  - Red Blob's noisy edges use recursive midpoint displacement inside a quadrilateral, so a boundary wanders but stays in bounds. They use 2^levels segments and an amplitude of 0.25 to 0.5 (https://www.redblobgames.com/maps/noisy-edges/).
  - The same idea gives path verges that wobble by about a cell without breaking width rules.
- **Hand-made game examples.**
  - Pokémon routes use one-way ledges to make shortcuts back to earlier areas and to gate later ones (https://bulbapedia.bulbagarden.net/wiki/Ledge).
  - Hoenn's Seaside Cycling Road is a raised track "extending over the sea and the grassy road beneath". It is a graded road (bikes only) stacked over a footpath grade (https://bulbapedia.bulbagarden.net/wiki/Hoenn_Route_110).
  - In A Link to the Past's overworld, walls are "impenetrable mountain ridges, stands of trees, or riverbanks". Two tunnels connect chunks that would otherwise be inaccessible (https://www.gamedeveloper.com/disciplines/overworld-overload-an-analysis-of-link-to-the-past-s-light-world-part-2).
  - Stardew treats flooring and paths as a placement class that blocks tree planting (https://stardewvalleywiki.com/Fruit_Trees).

### 2.2 A path generator for NapAttack (implementable in `zones.py`)

This runs in pass 2 ("structure") of world-rules section 6, after terrain and tiers exist.

**Inputs**
- `terrain`, `tier` (or a fine `height` field)
- canopy and trunk masks
- building footprints with door aprons
- `nodes` with importance. Starting points: exits 10, main plaza 8, doors 5, jetty, bridge or stall 4, bench or viewpoint 2.
- the zone's frame. Exits are fixed points on the border, shared with the neighbour zone.

**Step 1: cost field per cell** (starting points)

```
base:    ground 1.0, sand/snow 1.4, bank 1.6, shallow water 12 (ford only),
         under canopy 1.3, within 1 cell of a building wall 2.0, zone-edge band 1.5
blocked: deep water, cliff, lava, building, tree trunk, rock  -> infinity
reuse:   existing path cells x0.35 (grade 1), x0.5 (grade 2)   [Galin 2011 reuse]
slope:   + (m * dh/dx)^2 with m = 3..15                         [runevision]
tier step without stair: infinity; a stair cell costs 4 (people avoid stairs a little)
```

**Step 2: neighbourhood**
- Use the 16-direction mask (Galin k=2, runevision). Integrate the cost along each long edge by sampling the cells it crosses.
- This removes 45° staircase artefacts at the 4 px cell scale.

**Step 3: grades, top-down** (Galin 2011)
1. **Grade 1**: A* between each pair of exits and the main node, choosing a minimum spanning set plus one extra edge so the zone has a loop where it fits. Rasterise at width 8 to 12 cells.
2. **Grade 2**: for each door, jetty, stall and bridge end, run Dijkstra *from the destination* with the existing path cells as targets. The search stops at the first network cell, so a branch meets the network at a near-right angle on its own and forms a **T**.
   - Apply Parish and Müller snapping. If the meeting point is within 4 cells of an existing junction, extend to that junction instead of making a new one.
3. **Grade 3 / desire lines**: Cogmind-style all-pairs between nodes within range, weighted by mean importance. Accumulate a `traffic` count per cell.
   - Cells where traffic reaches about 2× the median become a footpath (3 to 4 cells).
   - Cells above about 1× become worn grass only, with no path class, so they stay walkable ground.
   - Footpaths that meet at a shallow angle merge into one before the node: the Helbing **Y**.
4. **Bridges**: allow special long edges across water (Galin's bridge mask) of length up to `L_max`, with starting points 12 cells for a footbridge and 24 for a road bridge. Cost = `c0 + 3 × length`.
   - Because cost rises with span, A* picks the narrow point.
   - Only grades 1 and 2 may bridge. Grade 3 detours or uses stepping stones at a ford, following the Parish and Müller rule that only highways cross.

**Step 4: smooth**
- String-pull: remove a vertex if the straight segment between its neighbours stays inside cells of cost below 1.5× the original.
- Run Chaikin twice, then re-check that every smoothed sample is on an allowed cell. If one is not, keep the unsmoothed vertex there.
- Grade 1 may use biarcs for long curves.

**Step 5: shape junctions**
- At a T, add a fillet of 1 to 2 cells on each inside corner, so the corner is worn.
- At a Y, taper the minor path's width to the merge point.
- Forbid a degree-4 node unless it lies inside a plaza `#`. Otherwise offset one branch by 4 or more cells to make two staggered Ts.
- **(Inference)** The staggered T follows from the T and Y forms the sources show (Helbing, Galin, Parish and Müller). None of them states a rule against crossroads.

**Step 6: edges, verges and wear**
- Path width wobbles ±1 cell using noisy-edge midpoint displacement at amplitude 0.25 (Red Blob).
- Add a 1 to 2 cell verge band of worn grass, with intensity = traffic.
- Puddles go in local minima of `height` on the path. Mud goes where the path crosses moisture above 0.7.
- Galin et al. 2010 grade a corridor beyond the road surface and remove vegetation inside it. The pixel-art equivalent: no tall plants within the verge, and short grass and flowers only at its outer edge.

**Step 7: terminate properly**
- Every path end is a node (check 6). A path end not at a node is pruned back to the last junction.
- Every exit has a path through it, matched in width with the neighbour zone's path at the same border cell (check 10).

**Step 8: lint, and restart on hard failure**
- If a zone's hard checks fail after generation, reseed the stochastic steps (desire-line fuzz, noisy edges) up to N times before reporting. This is Bad North's restart rule.

---

## 3. Verticality in top-down 2D

### 3.1 How the reference games show and play height

**Zelda, the 2D games**
- *A Link to the Past* dungeons already treat space "as a building with verticality". You "drop down from the exact right spot on floor five" to reach a chest on floor four, and push blocks down holes to the floor below (GMTK, Boss Keys transcript: https://amara.org/subtitles/eYhYYN1TyE9U/en-gb/1/download/The%20Legend%20of%20Zelda%20A%20Link%20to%20the%20Pasts%20dungeon%20design%20%20Boss%20Keys.en-gb.srt).
- But on ALttP, Iwata says: "When you went up stairs, you just entered a closed room."
- For *A Link Between Worlds* (top-down again), Aonuma: "when you go up a floor this time, the lower levels overlap underneath". Hitting a jump platform sends Link "to the floor above", and "it automatically switches to the upper floor" (https://iwataasks.nintendo.com/interviews/3ds/a-link-between-worlds/0/4).
- Aonuma also said ALBW "made the difference in height of different objects clearer", and that in ALttP "it was harder to make that difference clear" (https://zeldauniverse.net/2013/10/06/aonuma-his-responsibilities-the-3d-effect-in-a-link-between-worlds-and-more/).
- **Lesson**: show the lower level beneath the upper one (darkened, partly visible) rather than cutting away. Shading has to do the stereoscopic depth's job on a phone.
- On the view itself: "A true top-down view actually has lots of problems … So you have to fake it", and they "purposefully tilted the objects back" (https://iwataasks.nintendo.com/interviews/3ds/a-link-between-worlds/0/3).

**Layers in ALttP-style engines**
- Solarus (an engine built to recreate ALttP-style games) stacks layers. "There is always a layer 0, and maps can add additional layers above or below 0". Each layer has its own ground, queried with `map:get_ground(x, y, layer)`. The layer system is what lets a hero walk "above or under" a bridge (https://docs.solarus-games.org/lua-api/map/).
- Inner stairs "go from a layer to another layer on the same map". They must sit on the lower of the two layers, and the engine changes the hero's layer automatically (https://docs.solarus-games.org/lua-api/map-entities/stairs/).
- In the Solarus forum, the engine's author describes layer-change sensors. He warns that sensors "should not overlap each other, otherwise you would have an infinite loop". At a transition, "The invisible tile is on the higher layer of both, it is walkable so that the hero does not fall" (https://forum.solarus-games.org/en/index.php/topic,346.0.html).

**Bridges over and under (RPG Maker's official method)**
- Place a row of trigger events at each bridge end, one setting the bridge switch OFF and the other ON, with a **neutral row between them** so walking back and forth always passes a trigger.
- The bridge has two states: "above character" plus pass-through (you walk under it), or normal passability (you walk on it).
- Set the switch correctly on map entry.
- Caveat: other events "can't pass below a bridge while characters are on the upper layer" (https://rpgmakerweb.com/blog/making-multi-level-bridge-tiles).
- **Lesson**: give each actor its *own* level instead of a global switch, which avoids that caveat for NPCs.

**Pokémon**
- Ledges are one-way: you "may not climb back up" (https://bulbapedia.bulbagarden.net/wiki/Ledge).
- Stacked roads: the Seaside Cycling Road runs over the old road, which "was kept underneath". New Mauville's entrance is reached by Surf "underneath the cycling road". Entry to the upper deck goes through gatehouses at both ends (https://bulbapedia.bulbagarden.net/wiki/Hoenn_Route_110).
- Fortree City's residents "live in treehouses and get around by a system of rope bridges that hang in the treetops" (https://bulbapedia.bulbagarden.net/wiki/Fortree_City).
- **Lesson**: the upper level is entered at a few clear connectors (gatehouses, ladders), and the lower level stays playable underneath.

**CrossCode**
- Radical Fish: CrossCode is three-dimensional so the player can move across layers at different heights. "The jump height in CrossCode is fairly low", and jumps mainly serve to change height.
- They chose **auto jump**: height matters, but precise jumping does not.
- They also report that a tech-demo level stacking platforms at different heights was overly complex. Future areas would use more distinct colours to mark heights (https://www.radicalfishgames.com/?p=1168).
- Jump panels "help you reach a higher altitude quickly" and can be used by enemies too (https://www.moddb.com/news/devlog-67-wiki-caves-and-weird-trees).
- **Lessons**: limit the number of levels visible at once; give each height a distinct palette; let height changes happen automatically at connectors.
- I found no credible developer source on how Rookie Harbor or Basin Keep are composed.

**Sea of Stars**
- Sabotage built "dense and multitiered" levels and broke from "restrictive grid-based movement". Animator Savannah Perron noted that in games you can slay a dragon but not hop over a fallen tree, so the team wanted traversal that "would feel more seamless".
- Thierry Boulanger: "There's a little verticality in the level design". Coral Cascades has the party "jumping, swimming and shimmying across ledges" (https://mobilesyrup.com/2023/09/11/sea-of-stars-level-design-sabotage-studio-thierry-boulanger-interview/).
- **Lesson**: contextual climb, jump and drop points at ledges, without free jumping. That fits NapAttack's tap-to-walk.

**Eastward**
- Pixpil's Feng Ye: "We also utilise smart placing and orientation of the sprite to make it look like 3D". The lighting "is basically general deferred shading, which enables our designer to put more lights into the level" (https://www.redbull.com/my-en/eastward-interview).
- The world began from a sketch of "a weird monster dormitory building resembling Hong Kong's Kowloon Walled City" (https://www.gamedeveloper.com/disciplines/road-to-the-igf-pixpil-s-i-eastward-i-; also https://nintendo.com/us/whatsnew/how-the-developers-began-making-then-remaking-eastward).
- I found no credible developer source on New Dam City's walk layering.
- **(Observation, unsourced)** Its streets read as stacked because building fronts are tall, layered facades with walkways and stairs drawn on them, while most walking stays on a few clearly lit planes.

**Tunic**
- Tunic uses an "isometric orthographic projection". Because "vertical lines line up perfectly … it makes it easy to hide things", for example a path behind a waterfall (https://blog.unity.com/games/smoke-mirrors-and-scrolling-textures-behind-the-scenes-of-tunic).
- **Lesson**: in an orthographic three-quarter view, whatever is directly behind a tall facade is hidden by default. That is useful for secrets, and harmful for anything the player must find or tap.

**Hyper Light Drifter, Chained Echoes, Chef RPG, Cainos packs**
- I found no credible source on how these handle levels.
- Preston says HLD's 480x270 resolution "forces you to think and design within tight constraints" (https://www.gamedeveloper.com/design/road-to-the-igf-heart-machine-s-i-hyper-light-drifter-i-).
- The Cainos "Pixel Art Top Down - Basic" page notes only that an update added "stairs of west and east direction" and "Seperated shadow sprites" (https://cainos.itch.io/pixel-art-top-down-basic). Its in-package layer and stair scripts are not documented on the public page.

### 3.2 Draw order and occlusion

- **Y-sort within a level.** Put each object's origin at its feet. Objects lower on screen draw later: "The higher on the screen, the farther away and therefore lower the render order" (https://kidscancode.org/godot_recipes/4.x/2d/using_ysort/index.html).
- Unity's equivalent is a custom sort axis plus a sprite sort point at the pivot. Sorting Layers set priority first and Order in Layer second, and a Sorting Group sorts a multi-part object as one unit (https://docs.unity3d.com/2019.4/Documentation/Manual/2DSorting.html).
- **Levels draw in order.** Everything on level 0 draws before level 1's surface, as in Solarus' stacked layers and Unity Sorting Layers. Supports such as columns and stair stringers sort with level 0 by their foot y.
- **Fade what hides the player.** Stardew buildings "turn transparent when I move slightly behind them", controlled per building by a `FadeWhenBehind` data field (https://forums.stardewvalley.net/threads/mod-to-turn-off-transparency-of-farm-buildings.30012/latest). NapAttack already has a `Ghost` outline for the companion when hidden (world-rules section 2a).

### 3.3 What this means for a city with skybridges and stacked streets on a phone

**(Inference, drawing on the sources above.)**

1. **Two walk levels per zone, not more.** Use a ground street (L0) and a deck (L1: skybridges, terraces, elevated walkways). CrossCode's experience says stacked heights get confusing fast, and a 320x576 zone has little room to show three planes. Put rooftops as a third level only in a separate zone or interior.
2. **Show L0 under L1.** The ALBW principle: skybridges should be narrow (starting point: 6 to 8 cells deep including the front face) so the street below stays readable. Darken L0 under a deck by one palette step, the deck's cast shadow falling down-right. Draw railings so the deck reads as a deck.
3. **Few, obvious connectors.** Use stairs, a lift or a gatehouse at each end of a deck system, like Pokémon's cycling-road gatehouses. Each L1 component should have two or more connectors where it fits, so a loop exists.
4. **Distinct materials per level.** Example: L0 cobbles with warm lamps, L1 timber or steel decking with a lighter tone. This follows CrossCode's "more distinct colors to mark heights".
5. **Facades are the vertical axis.** In three-quarter view, a building's height takes up screen y. A tall facade directly south of a street hides that street. Keep tall buildings on the *north* side of walkable streets where possible, and keep south-side buildings low or cut away (fading roofs). Under-deck tunnels on L0 should be short (starting point: 10 cells or fewer) so the companion is rarely hidden.
6. **Auto level change, no jumping.** Walking onto a stair changes level, as with Solarus inner stairs and CrossCode's auto jump. A lift is a tappable action, never an automatic trigger, so an interrupted walk cannot fire it (AGENTS.md).

---

## 4. Recommendations for NapAttack

### 4.1 Lint additions, in order of value

The lint already has footing, floating/supported, path ends, borders, `plant-on-path` and `door-shut-in`. Add these:

1. **reach**: BFS from exits over all levels and connectors. Fail on any unreachable door apron, interactive standing point, bridge end, stair end or exit (rules 8 and 10). This covers checks 5, 7 and 11.
2. **path-width**: a distance-transform width per grade, plus a variance cap (rule 7).
3. **junction-shape**: skeleton nodes of degree 4 or more outside plazas fail. Branches meeting at less than 25° within 6 cells of a node are flagged as slivers (section 2.2, step 5).
4. **tier-step**: walkable neighbours with different tiers must be on stair, ramp or ladder cells. Buildings must sit on a single tier (rules 4 and 19).
5. **bridge-narrow**: span at most 1.3 × the local minimum crossing width, and both ends on a path (rule 18).
6. **fence-encloses / gate-in-fence**: barrier ends terminate properly; enclosed regions contain an enclosable prop and a gate (rule 9).
7. **facing**: a ray test for benches, fishers, vendors, signs and statues (rule 11).
8. **sign-at-junction**: signs within 4 cells of a junction, gate or exit (rule 12).
9. **shadow-dir / shadow-length**: shadow centroid down-right; length tracks `height_px` (rule 13).
10. **veg-niche**: species ranges over moisture, shade and tier fields (rule 15).
11. **spacing**: a per-kind minimum distance (rule 16).
12. **deck-support / deck-reach / deck-occlusion**: see section 4.3.

### 4.2 The path generator

Implement section 2.2 as a `paths.py` module that the zone generators call in pass 2. It takes `terrain, tier, nodes, exits, cost_overrides` and returns `path_cells_by_grade, junctions, traffic`.

Defaults:
- 16-direction A*
- slope cost `(6·dh)^2`
- reuse discount 0.35 / 0.5
- Dijkstra-to-network for grade 2
- Cogmind-style traffic for grade 3
- bridge edges for grades 1 and 2 only
- string-pull, then Chaikin ×2
- noisy verges at amplitude 0.25
- reseed up to 5 times on a hard lint failure

Write `traffic` out so the wear pass (section 6, "derived detail") can draw worn grass, verges and puddles from it.

### 4.3 Two-level walk design (ground L0 and deck L1)

**Data**
- `walk[0]` and `walk[1]`, each an 80x144 grid with RLE as today.
- `deck_height_px[c]` for L1 cells. Starting point: a constant 24 or 32 px per zone.
- Store L1 in **ground coordinates**, meaning where the deck's footprint is on the ground. Draw it at `screen_y = ground_y − deck_height`. Sorting and shadows stay consistent this way, and the occlusion test is exact: a deck cell hides the L0 cells `deck_height/4` rows above its footprint on screen.
- `connectors`: a list of `{kind: stair|ramp|lift|ladder, cells_L0: [...], cells_L1: [...], dir}`.

**Movement**
- Pathfinding runs on nodes `(level, cell)`. Edges stay within one level, except at connector pairs.
  - A stair is a strip of cells, starting point 6 to 8 cells for a 24 to 32 px rise. Walking along it interpolates the companion's draw offset from 0 to `deck_height`.
  - The level flips at the top and bottom cells.
  - Use one neutral middle cell, like RPG Maker's neutral row, so oscillating taps cannot flicker the level.
  - Stairs sit on the lower level, as in Solarus.
- A **lift** is a tappable prop with a standing cell on each level. Only an arrival from a completed walk triggers it, never a stale one (AGENTS.md: interrupted walks must not trigger stale navigation).
- A **ladder** is a connector that is 1 cell wide and slower.
- One-way **drops** from L1 to L0 are allowed only with a two-way route back (rule 20).
- The saved state stores `level` with the companion's position.
- Residents and visitors carry their own level, so no global switch is needed.

**Collision**
- L1 deck edges are blocked except at connectors. Railings are drawn on every non-connector edge.
- On L0, columns, piers and building fronts block. The rest of the space under the deck stays walkable.

**Tap resolution**
- A screen tap maps to a candidate cell on each level. Prefer L1 if a deck surface is drawn at that pixel. Otherwise use L0.
- If an L0 prop is fully covered by the deck on screen, it is not tappable, and the lint forbids interactive props there.

**Draw order**
1. L0 ground
2. L0 props, actors and deck supports, y-sorted by foot y
3. The deck's cast shadow on L0, offset down-right
4. Deck front faces and railings
5. Deck surface
6. L1 props and actors, y-sorted
7. Overhead (cables, bunting, signs on brackets)
8. Roofs and anything flagged `fade_when_behind`

**Occlusion**
- When the companion on L0 is under a deck, or behind a building whose base y is greater than the companion's foot y while their sprites overlap:
  - fade the occluder to about 55% alpha inside a soft circle of radius 20 px around the companion (Stardew `FadeWhenBehind`), *and*
  - keep the `Ghost` outline.
- Use a finite fade (about 150 ms in and out). Under reduced motion, switch instantly.

**Readability**
- Darken L0 one palette step under any deck.
- Give each level its own material palette (CrossCode).
- At most two levels per zone.
- Keep L0 tunnels under decks short.
- Put tall facades north of the street they serve.
- Let the lower street show beneath the skybridges (ALBW).

**Lint for levels**
- **deck-support**: each L1 cell lies within 8 cells of a column, pier or building (rule 2).
- **deck-reach**: each L1 component has one or more connectors (two or more preferred), and all connector ends are reachable (rule 10).
- **connector-apron**: the 2x2 cells at each connector end are walkable and prop-free.
- **deck-occlusion**: no interactive L0 prop or door apron is fully covered by L1 on screen.
- **deck-edge**: every L1 boundary cell without a connector has a railing prop.
- **tier-consistency**: a deck landing at a building is a doorway on that building's upper floor (world-rules 2a: "a skybridge landing in a doorway at both ends").

---

## 5. Gaps and blocked sources

- No credible developer source was found on the internal layering of Eastward's New Dam City, Sea of Stars' towns, CrossCode's Rookie Harbor or Basin Keep, Hyper Light Drifter's cliffs, Chained Echoes' maps, Chef RPG, or the Cainos packs' stair and layer scripts. Statements about those are labelled as observation or omitted.
- The Porymap manual on Gen 3 Pokémon collision and elevation (https://huderlem.github.io/porymap/manual/editing-map-collisions.html) was blocked by the fetch tool and not read. It is the best technical source on how Pokémon encodes walk-under bridges and elevation per metatile, and worth reading by hand.
- All numeric thresholds above (widths, radii, ratios, deck heights) are starting points to tune in play-tests, not sourced values.
- None of this was tested on a phone. It is design research only.
