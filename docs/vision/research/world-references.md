# World references: what good natural worlds look like

Research for Claude A, 20 Oct 2026. Matt (00:08): "try to capture lots of images from games i named to compare what good natural world would look like". It answers his 19 Oct 22:40 play-test (`docs/vision/art-faults.md`, "Matt's play-test"): unnatural placement, hard cut-offs between sections, fences that stop for no reason, paths that cut off, a bad waterfall, sparse woodland, trees in the sea at the border, static animals, undetailed bridges and walls. It sits beside the soft-grid study (`docs/vision/verticality.md` 4f) and `placement-paths-verticality.md`, and does not repeat them.

**The images are not in the repository.** They are other studios' art. Every shot cited here is an official screenshot: a Steam store screenshot (`path_full` from `store.steampowered.com/api/appdetails`), a studio press kit or site, or a nintendo.com store gallery. To look at them, run:

```
python3 scripts/refs/fetch_references.py
```

It reads this file, downloads exactly the image URLs cited in the source table (section 11) into `refs-cache/world/` (git-ignored), and names each file by its key, for example `refs-cache/world/eastward-13.jpg`.

**How to read it.** A key like [eastward/13] names one screenshot; section 11 maps every key to its URL and store page. Everything about the shots is **Observation**: what I saw and measured on the official images, not something a developer states. Sizes are given in NapAttack zone px, converted by character height (our adult A = 25 px, one grid cell = 8 px):

| Game | Pixel scale on a 1920 x 1080 shot | Character height (native px) | To our px |
| --- | --- | --- | --- |
| Eastward (and Octopia) | 3x | adult about 50 | x 0.5 |
| Sea of Stars | 3x | Garl about 47 | x 0.53 |
| Chained Echoes | 3x (camera zooms) | 35 to 45 | x 0.6 |
| Stardew Valley | 4x | farmer 32 | x 0.78 |
| CrossCode | 2x of 1136 x 640 | Lea about 31 | x 0.8 |
| Moonlighter | about 3x | Will about 32 | x 0.78 |
| Chef RPG | about 3x | about 37 | x 0.68 |
| TUNIC, Link's Awakening (Switch), Echoes of Wisdom, Pokémon BDSP | 3D renders | n/a | layout lessons only |

---

## 0. The ten most important lessons

1. **A forest is crown mass with an edge of trees.** Inside a wood you see overlapping crowns and no trunks; only the front row shows trunks, root flare and a foot shadow, and singles and pairs stand out in the open beyond it. The density falls off over two or three tree depths, not at a line. [eastward/08] [eastward/07] [chefrpg/09] [eastward/37]
2. **Trees grow in clumps of 3 to 7 with crowns overlapping, of mixed size and species.** Never in a row unless people planted them; Link's Awakening's mangrove rows read as a hedge maze, which is the point there and wrong for a wood. [chefrpg/09] [eastward/37] [seaofstars/12] [zelda-la/06]
3. **Every boundary ends on something.** Fences end at a building corner, a gate, a stair cheek, a lamp post, a terrain face or the frame edge; a ruined wall crumbles into loose stones. No fence or hedge stops in open grass. [eastward/17] [eastward/12] [stardew/12] [stardew/01] [crosscode/25] [chainedechoes/07]
4. **Paths are worn, not drawn.** They widen at doors and junctions, narrow between, fork as Y and T with filleted corners (never an X), are fringed by grass hanging over their edges, and end at a door, gate, stair, jetty or signpost. Bare patches spread where people stand. [stardew/03] [moonlighter/11] [chefrpg/07] [eastward/17] [seaofstars/35]
5. **A waterfall is the channel's own width, with a lip, streaks and a landing.** A notch between rock buttresses, a lit white curl over the lip, a sheet in three tones with vertical streaks of different lengths, a foam band where it lands, a plunge pool wider than the fall, wet dark rock and ferns beside it; long drops come down in tiers, each with its own pool. [seaofstars/26] [seaofstars/02] [crosscode/03] [chainedechoes/11]
6. **Every shore has three bands.** A 1 px lit foam line at the waterline, a lighter band of shallows following the shore, and a darker band in the water under any bank. Banks differ by side: a rock face on the high or outer side, sand or a shelf on the low side. [crosscode/21] [seaofstars/08] [eastward/15] [crosscode/08] [stardew/11]
7. **Open water meets sand or rock and runs off the edge of the frame.** The world's edge is open sea, a drop or a cliff, never a band of canopy. Sea stacks and islets carry their own foam ring. [seaofstars/08] [tunic/01] [crosscode/14] [eastward/39] [pokemon-bdsp/03]
8. **Height changes carry the composition, and stairs sit where paths meet them.** A low earth step with a scalloped grass lip, rocks on the lip and tall grass at its foot; a stair cut exactly where the road meets the step, flanked by a lamp or a tree; a long stair broken by landings; a ledge path guarded by a parapet of boulders. [eastward/13] [stardew/16] [chefrpg/08] [seaofstars/33] [seaofstars/12] [zelda-la/03]
9. **Props cluster where work happens, and life moves.** Churns, hay and firewood stand against barn and house walls, washing hangs in a yard between a post and the wall, goods spill in front of stalls, jars sit in twos and threes at corners. Animals stand in different poses and facings, each with its own shadow, inside the place that holds them. [eastward/17] [stardew/07] [stardew/01] [moonlighter/11] [chainedechoes/10]
10. **Made things are on the grid; grown things soften it.** Plazas, quays, walls and channels are straight with rounded corners (the soft grid), while grass invades paving in lobes, cobbles fade into single stones, weeds grow in joints and the central feature sits exactly on its axis. [eastward/15] [hyperlightdrifter/03] [crosscode/25] [moonlighter/02] [chainedechoes/16]

Contact sheets by theme (local only, not committed) were made for this study in the scratchpad's `refs-games/sheets/`; anyone can rebuild them from the fetched images.

---

## 1. Forest density, clumping and edges

**What the references show**

- [eastward/08] The station clearing is framed in two layers: background crown masses lit yellow-green on top and blue in shade, with no trunks, and a foreground canopy along the bottom edge drawn over the fence and track. Near the station, trees stand singly with trunk, root flare and a dark foot shadow.
- [eastward/07] Seen from above, the town in its valley sits inside a density gradient: closed crown masses at the top and sides, then pairs and single conifers on open ground, thinning toward the centre.
- [chefrpg/09] Autumn wood: trees in clumps of 6 to 10 with crowns overlapping and trunks hidden except in the front row; two or three single trees stand out in the open; every trunk has a dark foot shadow about 1.5 times its width. Fallen log, stump, a mushroom cluster of 6 to 8, half-buried old paving, a deer.
- [eastward/37] Conifers in clumps of 3 to 6 behind the bus, crowns overlapping, only front trunks visible; ruined concrete pillars overgrown at the wood's edge.
- [eastward/02] [eastward/22] Forest interior: giant trunks as a back wall, ferns and root flare at every trunk, tall grass in clumps of 5 to 12 tufts, sun dapple as pale blobs about 10 to 20 px (ours) on the floor, a row of young firs along the bottom edge cut by the frame.
- [moonlighter/11] Open woodland: six trees with crowns touching but trunks visible, each with a soft oval shadow.
- [seaofstars/12] [chainedechoes/11] Cypresses stand in twos at a cliff edge; under a giant tree a dense band of ferns and broadleaf undergrowth fills the front.
- [crosscode/14] A single tall fir on a cliff lip, round shrubs in pairs at its foot.
- [zelda-la/06] Counter-example: a row of identical round trees either side of a channel. It reads as a planted maze, which is what the game wants there.

**Rules for NapAttack**

1. Draw a wood in three depths. **Interior:** overlapping crown masses, no trunks, two palettes (lit top, cool shade), varied crown sizes (28 to 44 px). **Edge row:** individual trees with trunk, root flare and a foot shadow (an ellipse about 1.5 trunk widths, offset down-right). **Outliers:** singles and pairs 16 to 48 px out from the edge, and saplings and bushes in between.
2. Clump trees in groups of 3 to 7, crowns overlapping by a third to a half, heights varying by up to 30 % within a clump, at least two species per clump in mixed woodland. Never a straight line or column of more than three trunks unless it is an orchard, an avenue or a hedgerow that people planted.
3. Crown cover targets (share of the area under crowns): deep forest 70 % or more; woodland 45 to 60 %; open woodland or parkland 15 to 25 %. Fir Hollow ("a sheltered bowl of old firs") is woodland, so 45 to 60 %, about 35 to 45 trees on a 320 x 576 zone (fault A2 asks for about 40).
4. The forest floor reaches beyond the crowns: a band of litter, shade and moss 20 to 40 px into the meadow, grass tufts in clumps of 5 to 12 at every trunk foot and at the edge, ferns, a log or a stump every 60 to 100 px of edge.
5. Put a foreground canopy (dark, cool, drawn in `fore.png` over everything) along a zone's south edge where it is wooded, as Eastward does. It frames the scene and hides the border.
6. Light the clearing with pale dapple blobs (2 to 3 per 100 px square), never one perfect lighter ellipse (fault 04).

## 2. Ledges, cliffs, side faces and stairs

**What the references show**

- [eastward/13] A low earth step crosses the farm: a grass lip with scallops, tufts and three or four grey rocks sitting on it; a dark earth face about 12 px (ours, half an adult); a timber stair of four treads about 32 px wide cut in exactly where the farm road meets the step, a lamp post and a conifer at its head; the step turns an inner corner by the trees.
- [stardew/12] Snow cliffs: faces of rounded cobbles in one cold ramp, constant height along a run (about 1.3 farmer, so about 32 px ours), a snow lip that wobbles 1 to 3 px; a lower step with no face, only a 2 px blue crease, meanders across the snow.
- [stardew/16] An earth cliff with plants growing out of the face, a lumpy foot line with fallen pebbles below, and a timber stair cut into it just over one farmer wide.
- [eastward/01] City levels: retaining walls with a lit coping band, bollards along the edge, a straight stair between buildings and a second stair running sideways down the face of a wall.
- [eastward/05] A terrace edge at night: a cobbled earth face lit by the lamp above, a ramp running down along the face.
- [crosscode/03] [crosscode/14] Terraces step down in two or three levels with faces about one character tall; tall faces are vertical ribs of light and dark; every top carries a grass lip and bushes.
- [seaofstars/33] A ledge path cut diagonally along a cliff face as short steps, its outer edge a row of rounded rock blocks lit on top: a natural parapet.
- [seaofstars/12] A plateau ringed along its drop by boulders of two sizes with lit tops; a ladder stair down the face with two posts at its head.
- [zelda-la/03] A walled plateau: the coping turns corners with corner blocks and stops either side of the stair cut, so the wall ends for a reason.
- [tunic/01] A straight stair runs along the cliff face down to the beach; the grass drips over the rim and an earth stratum shows on the face top.
- [chefrpg/08] Stair flights of four to six treads broken by round landings between rope-wrapped posts, lamps at the foot and the landing.

**Rules for NapAttack** (these refine `verticality.md` 4f, they do not replace it)

1. A low step is 12 or 16 px (Eastward's farm step converts to 12); a tier is 32 or 40 px (Stardew's cliff converts to about 32). Keep one height all round a plateau.
2. Every lip carries life: scallops 1 to 3 px, tufts overhanging, a rock or two sitting on the lip every 40 to 80 px, and tall grass at the foot. Faces carry roots, plants or fallen pebbles at the foot.
3. Put stairs where a path meets a step, never in the middle of nowhere, and mark the head with a lamp, a post pair or a tree. Stair cut 32 to 48 px wide; a flight longer than six treads gets a landing 8 to 12 px deep.
4. A drop that people walk beside gets a parapet: a row of boulders (two sizes, 10 to 22 px, lit tops) on rock, a coping and bollards on built walls, a rail on decks. Coping and parapet stop at a stair cheek or turn a corner with a corner block.
5. A stair may run along a face (sideways), not only into it; use it where the face is long and the path runs parallel.
6. The edge of the world, where it is land, is a drop or a cliff seen from above (as [crosscode/14]), not a wall of trees.

## 3. Rivers, banks, waterfalls and ponds

**What the references show**

- [seaofstars/26] The river runs between rock banks and pours over a straight lip as a sheet exactly the channel width; a bright white curl at the lip with spray specks breaking off; the sheet in three blues with long vertical white streaks of different lengths; dark wet rock, vines and leaves beside it; 1 px light ripple lines along both banks.
- [seaofstars/02] A waterfall down a coastal cliff in three tiers, each landing in a round pool with a white foam ring before it spills again.
- [crosscode/03] Two waterfalls fall straight down south faces, each as wide as its channel, with a white foam band where they land; the plunge pool is wider than the fall, lily pads in clumps of 3 to 5.
- [chainedechoes/11] A waterfall pours through a notch between two rock buttresses; the pool is rimmed by flat stones on the low bank and stacked rock on the high bank; reeds with seed heads in one clump in the shallows; roots spill into the water.
- [crosscode/08] The river bends in 45 degree runs; the high bank is a rock face under a grass lip, the low bank a sandy shelf.
- [crosscode/10] An island with an earth face all round meeting the water with a dark wet band; lily pads in clusters of 5 to 8.
- [eastward/15] Swamp channels with straight sides and stepped right-angle corners rounded by 1 to 2 px (ours); every bank has a lit lip and a dark band on the water below it; reeds in clumps of 3 to 6 standing in the water with a white ripple at each stem; lily pads in overlapping clusters of 5 to 10, frogs on them; entry by a jetty between two posts with a lamp.
- [eastward/17] [eastward/37] Pond edges: a chain of rounded stones along the waterline (4 to 8 px ours), doubled at a bend, a mossy boulder pile at one corner, reed clumps between, and a stake-and-board revetment where a farmyard meets the water.
- [stardew/14] An irregular pond of straight-ish runs with rounded corners, a sand beach ring with set stones round half the rim, a darker mud band 2 to 4 px just inside the waterline, a few lily pads together.
- [stardew/11] A river with a sand strip between water and grass, pebbles on it, a 1 px foam line at the water's edge.
- [seaofstars/15] Depth in three bands seen from above: lighter shallows near the shore, a dark channel, submerged rocks as dark silhouettes, fish shadows.

**Rules for NapAttack**

1. **Waterfall kit** (answers A1): the stream bends into a notch between two rock blocks; the fall is exactly the channel width (stream 16 to 24 px, river 40 px or more); a lit white curl 3 to 5 px over the lip; the sheet in three tones with vertical streaks of 3 to 4 lengths that scroll down in two or three frames; a foam band 3 to 4 px at the foot, spray as dithered white specks; a plunge pool 8 px wider each side and an outflow; wet dark rock with ferns either side. A drop taller than about 48 px comes down in two or three tiers, each with a pool and foam ring.
2. **Banks** by side: on the outer bend or high side a rock or earth face 8 to 16 px under a grass lip; on the inner or low side a sand or gravel shelf 8 to 20 px wide with pebbles. Both get a 1 px lit foam line at the waterline and a 2 to 3 px dark band on the water under a face. Decide one treatment per river and keep it across zones (fault B12).
3. **Ponds**: soft-grid outline (straight runs, rounded corners), never an ellipse; a rim of stones in a chain on part of the shore, a boulder pile at one corner, mud band 2 to 3 px inside the waterline, reeds in clumps of 3 to 6 on the shallow side with a ripple at each stem, lily pads in clusters of 5 to 10 off-centre.
4. **Depth**: three tones (shallows, mid, deep) following the banks, with darker silhouettes of submerged stones.
5. **Motion** (A8): ripple lines along banks, foam at falls and stems, all as a finite loop per zone and off under reduced motion.

## 4. Coasts, beaches, harbours and bridges

**What the references show**

- [crosscode/21] Water in three depth bands: pale turquoise shallows along shore and as a sandbar, mid blue, dark blue deep. Rock islets have a lit top, a south face, a 1 to 2 px white foam line at the waterline and a soft darker halo 8 to 16 px round them. The beach meets the sea with a white foam line and a translucent wash.
- [seaofstars/08] Every rock that meets the sea has a foam line and a band of shallows; the sea runs off the frame on all sides; a small island is a rock column ringed by bushes and its own foam ring.
- [seaofstars/02] A sand beach fans out where the path meets the sea, then a timber jetty on piles; houses pack a ledge above a quay of planks.
- [eastward/39] A sand plateau with a soft-grid outline and a lit rim; a short sea wall with tetrapods piled against it; a stair down through the wall to a timber deck with handrails; gulls standing, walking and flying (the flying shadow offset below).
- [tunic/01] [pokemon-bdsp/03] The beach is a wide apron between the cliff or lawn and the sea (about 3 to 4 adults); the sea touches sand or rock only; boulders on the sand stand singly or in a cluster of three at the cliff foot.
- [seaofstars/38] [seaofstars/24] A harbour boardwalk on thick round piles wrapped with rope, a lit front beam, lattice skirting, a post-and-rail fence on the edge, a ramp down; barrels in twos and threes, jars by doors; lantern strings between posts.
- [stardew/09] Plank piers (planks across the pier with staggered joints, a darker shadow strip on the water beside them); every boat moored alongside a pier; buoys with lamps; coiled rope and crates by the shop.
- [chainedechoes/16] A canal between quays of dressed stone; mooring bollards in a row; cargo crates of 2 or 3 sizes overlapping; weeds in the paving joints.
- [seaofstars/05] A fallen tree bridges a gorge: the root plate sits on the far bank, the crown end on the near bank, a lit walking band with bark grain and moss along the edges, bushes growing out of it.
- [eastward/30] A rope bridge: planks of slightly different lengths, two rope hand-lines sagging between posts, knots at each post, anchor posts set in grass and reeds at each end; the deck has a lit top edge and a darker front face.

**Rules for NapAttack**

1. Coast bands from land to sea: dry sand (with drift line of weed and shells), wet sand (darker), a 1 px foam line, a translucent wash 2 to 4 px, shallows 8 to 15 px, then mid and deep water. Rocks in the sea carry a foam ring and a faint second ring 3 to 5 px out.
2. A beach is at least 3 adults (75 px) deep where people use it; lighthouses, cottages and chairs sit on the dry upper beach or on rock, never at the waterline.
3. Where the valley meets the sea at its edge, it is open sea running off the frame, with a rocky point or a cliff as the last land. Forest stops at least one tree depth short of any shore with a hedge, a bank or a strip of grass between (answers A3).
4. Jetties end at a boat, a ladder or a fishing spot; boats lie alongside a jetty or quay. Piles every 16 to 24 px, rope-wrapped at the top; planks 4 to 5 px across the pier with staggered joints; a dark shadow strip on the water beside the deck.
5. **Bridges** (answers "undetailed bridges"): a deck with a lit top edge, a darker front face and planks of uneven length; posts at each end set into the bank with reeds and stones at their feet; rails or rope hand-lines that sag between posts every 48 to 64 px; stone bridges with a coping, voussoirs and a cutwater facing upstream. The ends always land on dry ground on a path.

## 5. Paths and wear

**What the references show**

- [stardew/03] Earth paths are bands with soft edges where grass overhangs by 1 to 3 px; they fork as Y and T with a filleted corner about the path's width; a signpost stands at the fork; a worn paddock is a big rounded rectangle of bare earth inside its fence.
- [moonlighter/11] A wide earth path with a tufted fringe of grass blades hanging over it, turning in rounded right angles.
- [crosscode/25] A cobble path of loose rounded stones with grass between them, thinning at its edges into scattered single stones; a narrow beaten track meanders through the garden gate.
- [chefrpg/07] A stone path widens into an apron at the door and narrows as it leaves; slabs go missing and grass pushes in at its edges; worn sandy patches with a darker rim.
- [eastward/12] Oval stepping stones, decreasing in size, from a hut door to the road; the road is packed earth with darker worn wheel tracks.
- [eastward/04] [chainedechoes/10] At a market the ground is worn bare between stall rows; grass survives in islands only where nobody walks.
- [seaofstars/35] A pale lane with grass pushing in from both sides in irregular lobes, so its width varies along its length.
- [seaofstars/07] [zelda-eow/05] Worn patches are blobby with tufted edges, following the traffic between a tent door and the path.
- [hyperlightdrifter/03] Grass invades a paved plaza in large soft lobes from the sides and in small patches at slab joints; the paving's straight outline survives under it.
- [chainedechoes/07] A path of cobbles fading into dirt and then grass, with bare patches beside it.
- [crosscode/08] A wide sandy clearing that narrows into a lane between grass lobes.

**Rules for NapAttack**

1. A path is a corridor of wear: 12 to 24 px wide for a footpath, widening by half at doors, gates, stairs and junctions, narrowing between. Grass overhangs its edges by 1 to 3 px in tufts; its width varies by up to 30 % along its length.
2. Junctions are Y or T with a fillet of the path's width; no X crossings (fault E4). A signpost or a lamp marks a fork that matters.
3. Paths end at something: a door (with an apron), a gate, a stair, a jetty, a bench facing a view, a signpost. A path never runs into water, a fence or the back of a prop.
4. Paving degrades toward its edges: cobbles thin into single stones, slabs go missing, weeds grow in joints. Bare earth patches are blobby, with a darker 1 px rim, where people stand: at doors, gates, wells, benches, troughs.
5. Stepping stones (3 to 5, decreasing) connect a door to a path across a lawn.

## 6. Fences, walls and gates

**What the references show**

- [stardew/12] A post-and-rail fence turns 90 degrees at a corner post and its free end stops against the cliff face.
- [stardew/20] Dry-stone walls enclose beds and leave a gap with a small timber gate; walls turn corners with a corner block and end at the house or at a bed.
- [stardew/01] An iron fence encloses the farmyard, turns corners at posts and leaves a gate gap flanked by flower tubs; its free end runs into the coop wall.
- [stardew/07] The hedge lines the inside of the log fence; beehives stand in a row along the fence.
- [eastward/17] The pipe-rail fence runs from the barn corner and stops at a lamp post with a sign where the track enters.
- [eastward/08] The chain-link fence along the track stops exactly at the level crossing, with barrier posts and signals at the break.
- [eastward/13] A low lattice fence with a gate on the path line, ending at the forest.
- [eastward/12] A bamboo fence starts at the house corner and runs to the frame behind a tree; a picket fence closes a small garden.
- [crosscode/25] A brick wall with stone coping runs from the house corner, steps up into an arched gateway with piers on the path line, and ends at a lamp post.
- [zelda-la/03] The coping stops either side of the stair cut.
- [chainedechoes/07] An old enclosure wall breaks down into scattered stones at its ends: a ruin ending, not a cut.
- [tunic/07] Stone walls end in broken stubs among bushes.

**Rules for NapAttack**

1. Every fence, wall and hedge **encloses something** (a yard, a paddock, a garden, a bed, a track) and **every end lands on something**: a building corner, a gate post, a corner post where it turns, a stair cheek, a terrain face, a lamp or sign post, water, or the zone edge where the neighbour continues it. A ruined wall may end in a scatter of fallen stones. Lint: a fence end that touches none of these is a fault (answers "fences that just stop", B9, E7).
2. Gates sit on the path line, between two heavier posts, with something marking them (tubs, lamps, braziers, a sign).
3. Corners turn at corner posts or blocks; long runs get a heavier post every 32 to 48 px.
4. Tall grass and weeds at every fence and wall foot; hedges sit inside or along fences, 10 to 14 px tall with a shaded front face, never a 7 px flat band.
5. Dry-stone walls: stones about 4 x 2.5 px of 3 sizes, a lit top course, darker lower courses, moss in the joints, a corner block at turns (answers "stone walls lacking detail").

## 7. Fields, farms, yards and animals

**What the references show**

- [eastward/13] Raised beds with rounded timber frames, crops of mixed heights overflowing their cells, a scarecrow inside a bed, milk churns and hay bales against the barn wall, a bell on a frame with a bird on it, squirrels on a lamp.
- [eastward/17] Pigs and cows wander a fenced yard in different poses and facings, each with its own soft shadow; bare earth fans out from the barn doors; four churns clustered at the barn wall, hay stacked behind.
- [eastward/12] A front-yard kit by the door: bench, lantern post, mailbox on a post, flower pot, rocks; a vegetable bed with a rounded frame.
- [eastward/10] Tomato rows tied to bamboo hoops; small rock groups at wall feet and bed corners; a pair of stone lanterns flanking the door path.
- [stardew/07] The well stands at the junction of the yard path and the field; crops in small blocks with a tilled border and walkable gaps; firewood stacked under the eave; a mailbox where the path meets the yard; a rain barrel and a chest by the porch.
- [stardew/01] Barn and coop sit on a big worn earth yard with pebbles and tufts; cows, a goat, a chicken and a duck spread across it, each in a different pose.
- [stardew/13] Trellis crops in rows between posts; a dry-stone pen holds chickens; kegs in a row on a paved pad.
- [stardew/11] Barrels either side of the smithy door, a crate and tools leaning on the wall, a flagstone apron in front of the door only.
- [moonlighter/11] A washing line runs between a post and the barn corner in the house's own yard, beside the path, never across it; crates stacked two or three high by the shop.
- [chefrpg/09] A deer at the wood's edge; mushrooms in one cluster; a fallen log and stumps.
- [chainedechoes/10] An ox stands by a cart at the market's edge; water tubs, crates and a cage between stalls.
- [chainedechoes/07] Monkeys sit in a loose group in the meadow.

**Rules for NapAttack**

1. Work props stand **against** something: churns, hay, firewood, barrels and tools against a wall, under an eave or beside a door; goods in front of a stall. Groups of 2 or 3, never a lone item in open grass (answers E8).
2. A yard is bare earth worn in a fan from the main door, with tufts and pebbles; a front door gets an apron and a small kit (bench, lamp, mailbox, pot).
3. Crops grow in blocks or rows people set out, with a tilled border and walkable gaps between blocks; crops vary in height within a block.
4. Washing hangs in a yard behind or beside its house, between a post and the wall or between two posts, sagging, with a basket below, in the sun (answers "where clothes would be hung", B8 and E10).
5. Animals are always inside the place that holds them (fold, yard, pond, wood edge), each in its own pose and facing, with its own contact shadow; a group of animals is loose, never a grid. They idle and wander within their area (answers A9).
6. Rows are allowed only for things people line up: crops, trellises, beehives along a fence, kegs on a pad, bollards on a quay.

## 8. Villages, plazas, wells and streets

**What the references show**

- [moonlighter/02] A paved plaza with a raised kerb (lit top edge) and rounded corners; a radial paving ring round the central feature, which sits exactly at the plaza's centre; benches set along the edge facing inward; trees planted in the paving with moss at their feet; barrels at the edge.
- [hyperlightdrifter/03] The central mosaic lies on the axis of the door and the bridge; two basins flank the bridge symmetrically; tents with jars at their doors on the grass beside the paving.
- [seaofstars/35] Flat roofs with lit parapets; crocks and barrels grouped at house corners; a lamp on a bracket at a corner.
- [crosscode/15] A canal with a dressed-stone quay wall and a slim rail; ivy climbing the timber frames; a planter of three shrubs under a window; market stalls with striped awnings in a row against a wall; cobbles on the house apron, large flags in the street.
- [crosscode/17] Snow drifts banked against wall feet, cleared cobbles along the door-to-door route, bunting sagging between buildings and down a stair, jars in threes.
- [chainedechoes/16] [chainedechoes/10] Quays with bollards and stacked crates; stalls in two rows facing a lane; a puddle that reflects the people in it.
- [eastward/16] Kerbs with a lit top edge, tactile paving at the crossing, lantern strings sagging between posts, vending machines in pairs against the shop front.
- [eastward/04] Market stalls in two loose rows facing a worn lane, a gate arch at the entrance, rugs laid flat in perspective.
- [eastward/01] Three walking heights joined by stairs; utility poles; chain-link panels ending at walls.
- [stardew/09] The night market is strung with lanterns and every boat is moored to a pier.
- [tunic/07] A well stands on open ground beside the path with a winch post.

**Rules for NapAttack**

1. A plaza takes its shape from the buildings and streets round it: straight kerbs (lit top edge) with rounded corners, never an ellipse (answers E1).
2. Its feature (well, fountain, statue) sits exactly at the centre of the open floor or on the axis of the main door; the paving ring is centred on the feature's basin.
3. Benches stand along the plaza edge or a path, facing the feature or a view (answers E3).
4. Goods and containers group at corners and doors in 2s and 3s; lantern strings and bunting sag between posts; ivy and planters soften walls; weeds grow in joints.
5. Pave by grade: one material for the main street through the square, a different one for aprons; lay slabs in region coordinates so they continue across zones (answers A7 and E2).
6. The well (answers A12): dressed stones with chipped corners and moss, a roof or winch on two posts, rope and bucket, a worn ring of setts and a blobby bare patch at its foot.

## 9. Lighting and palette

- [eastward/08] [eastward/22] Crowns are lit warm yellow-green on top and cool blue in shade; sun shafts and dapple fall on the floor; the foreground canopy is the darkest and coolest layer.
- [eastward/05] [seaofstars/24] At night, warm lamp pools on the ground, everything else in cool blue shade; lamps sit where people gather.
- [eastward/17] A sun shaft lights the worn yard at the barn door.
- **Rule:** keep the upper-left light and the material ramps; add a cool shade hue to every crown and face, a warm lit hue to every top; at night light only where a lamp stands, so lamps must stand at doors, stairs, jetties and junctions.

## 10. How each of Matt's faults is answered

| Matt's fault (22:40, and `art-faults.md`) | What the references do | Shots |
| --- | --- | --- |
| Props in positions that look unnatural (E8, E10, E11) | Work props stand against walls and doors in groups of 2 or 3; nothing stands alone in open grass | [eastward/17] [stardew/07] [stardew/11] [moonlighter/11] |
| Hard cut-offs between sections (A4 to A7) | One ground with biome bands that blend; density gradients at forest edges; paving that continues; grass lobes into paving | [eastward/07] [eastward/08] [hyperlightdrifter/03] [seaofstars/35] |
| Unrealistically large benches (B1) | Benches are about 1.3 to 1.5 adults long with the seat at knee height (32 px for us, as verticality.md 5), set along an edge facing a feature or a view | [moonlighter/02] [eastward/12] |
| Fences that just stop (B9, E7) | Every end lands on a building, gate, post, stair, face, lamp or edge; ruins crumble | [eastward/17] [eastward/08] [stardew/12] [stardew/01] [crosscode/25] [chainedechoes/07] |
| The well not in the centre (E1, A12) | The feature sits at the plaza centre or at a junction; the paving ring is centred on it | [moonlighter/02] [hyperlightdrifter/03] [stardew/07] |
| Paths cutting off (B10, E4) | Paths fork as Y and T and end at doors, gates, stairs and jetties | [stardew/03] [chefrpg/07] [crosscode/25] [eastward/12] |
| Stone path on one side but not the other (B12, E2) | One bank treatment per river, chosen by side (rock on the high side, shelf on the low side); paving by grade | [crosscode/08] [stardew/11] [crosscode/15] |
| Water should flow (A8) | Streaked falls, ripple lines on banks, foam rings at stems and rocks | [seaofstars/26] [crosscode/03] [eastward/15] |
| Bridges lacking detail | Uneven planks, lit deck edge and dark front, sagging hand-lines, posts set in reeds, root plate on the bank | [eastward/30] [seaofstars/05] [seaofstars/38] |
| Stone walls lacking detail | Stones of 3 sizes, lit top course, darker lower courses, corner blocks, moss, ruin ends | [stardew/20] [chainedechoes/07] [crosscode/25] |
| Animals lacking detail and not moving (A9, B3) | Varied poses and facings, own shadows, inside their fold or yard; gulls walk and fly | [eastward/17] [stardew/01] [eastward/39] [chefrpg/09] |
| Where clothes are hung (B8, E10) | In the house's own yard, between a post and the wall, beside the path | [moonlighter/11] |
| TERRIBLE WATERFALL (A1) | Notch, lit curl, streaked three-tone sheet of the channel's width, foam band, plunge pool, tiers | [seaofstars/26] [seaofstars/02] [crosscode/03] [chainedechoes/11] |
| Fir Hollow needs more trees (A2) | Clumps of 3 to 7, crowns overlapping, front row with trunks, 45 to 60 % crown cover | [chefrpg/09] [eastward/37] [eastward/02] |
| Trees as a world border in the water (A3, fault 13) | Sea meets sand or rock and runs off the frame; forest stops short of shore | [seaofstars/08] [tunic/01] [crosscode/21] [eastward/39] |
| Forest edge as a wall of scales (A11, fault 07) | Crown masses inside, a front row of individual trees, outliers, a litter band, a foreground canopy | [eastward/08] [eastward/07] [chefrpg/09] |
| Hedges lacking detail (E6, E7) | Hedges with height and a shaded face inside a fence, ending at posts | [stardew/07] [eastward/13] |
| Ponds as perfect ellipses (B11, fault 15) | Soft-grid outline, stone chain, boulder pile, mud band, reed clumps | [stardew/14] [eastward/17] [eastward/37] [eastward/15] |

## 11. Sources

Every image below is an official screenshot from the store or the studio named. Steam URLs are each screenshot's `path_full` from `https://store.steampowered.com/api/appdetails?appids=<id>`. App ids: Eastward 977880, Eastward: Octopia 2305370, Stardew Valley 413150, Sea of Stars 1244090, Chained Echoes 1229240, Chained Echoes: Ashes of Elrant 3350260, CrossCode 368340, CrossCode: A New Home 1517030, Moonlighter 606150, Hyper Light Drifter 257850, TUNIC 553420, Chef RPG 1796790. Press kits: https://eastwardgame.com/media/, https://sabotagestudio.com/presskits/sea-of-stars/, https://www.stardewvalley.net/press/. Nintendo galleries: the nintendo.com store page named in the table.

| Key | Game | Image |
| --- | --- | --- |
| chainedechoes/07 | Chained Echoes (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1229240/ss_48db751b344de859c2fc1a4b3bc0dae74e341989.1920x1080.jpg?t=1788522273 |
| chainedechoes/10 | Chained Echoes (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1229240/ss_a683aed9b1e2500b3aa7bb5f3d5d7a58f744dca8.1920x1080.jpg?t=1788522273 |
| chainedechoes/11 | Chained Echoes (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1229240/ss_4b3a9335a15584143b657593522954595cd59e2d.1920x1080.jpg?t=1788522273 |
| chainedechoes/16 | Chained Echoes: Ashes of Elrant (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/3350260/ss_d5290911adce3be6a2026295ac1bc9c90f78c5e4.1920x1080.jpg?t=1754586032 |
| chefrpg/07 | Chef RPG (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1796790/ss_a7919db771c21a757c2f32b22b5686eba0afcee0.1920x1080.jpg?t=1787346270 |
| chefrpg/08 | Chef RPG (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1796790/ss_0f0d961567c3eec213daefa246168a79b78bb7c1.1920x1080.jpg?t=1787346270 |
| chefrpg/09 | Chef RPG (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1796790/ss_691edcdd73121d2130aa8daf14839eece95756e0.1920x1080.jpg?t=1787346270 |
| crosscode/03 | CrossCode (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/368340/ss_4a517a0780eaca5fa87c98ba5d1095812f415378.1920x1080.jpg?t=1788522282 |
| crosscode/08 | CrossCode (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/368340/ss_df77c06e713d76f8245016177b54a7456b11c0a0.1920x1080.jpg?t=1788522282 |
| crosscode/10 | CrossCode (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/368340/ss_e9c77a57c0be0e86416319b22331e48118c84020.1920x1080.jpg?t=1788522282 |
| crosscode/14 | CrossCode (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/368340/ss_6a96ff676c98dc81905a550733086aa911cc9e6a.1920x1080.jpg?t=1788522282 |
| crosscode/15 | CrossCode (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/368340/ss_4d1c860d8afea533b14a9a353831461c0df1071d.1920x1080.jpg?t=1788522282 |
| crosscode/17 | CrossCode (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/368340/ss_c89e7de11d225926fa53fb9984fb287c3a2eb8be.1920x1080.jpg?t=1788522282 |
| crosscode/21 | CrossCode: A New Home (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1517030/ss_b0683222285e64efee92e3a1e4ec71670c8d6f55.1920x1080.jpg?t=1651242585 |
| crosscode/25 | CrossCode: A New Home (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1517030/ss_b896e0c2f17a0bf98743476a18702a2121fbd932.1920x1080.jpg?t=1651242585 |
| eastward/01 | Eastward (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_5d50545b49db3a8502666b4195d2fabd0e31a29d.1920x1080.jpg?t=1782290198 |
| eastward/02 | Eastward (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_b3512f7576dbdd1e35dd3fb27a04f29174efb00d.1920x1080.jpg?t=1782290198 |
| eastward/04 | Eastward (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_ddd76431b1df70e234494c92370e2391680c98ef.1920x1080.jpg?t=1782290198 |
| eastward/05 | Eastward (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_fc97f011126b32f77cbb66a9dc59e22cc353c2b8.1920x1080.jpg?t=1782290198 |
| eastward/07 | Eastward (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_c9a1045cf8d4c65cf0bdf38c4b5de7c9a05a0fb9.1920x1080.jpg?t=1782290198 |
| eastward/08 | Eastward (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_bf8d65929d363f1b62f632d934eda94ef5188049.1920x1080.jpg?t=1782290198 |
| eastward/10 | Eastward (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_29d7dd0891c88b08d699556ed62fcc37f1aea47f.1920x1080.jpg?t=1782290198 |
| eastward/12 | Eastward: Octopia (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2305370/ss_c3e35bbd8e25af924b3b9cbf087f1f0c77dcf68a.1920x1080.jpg?t=1770113484 |
| eastward/13 | Eastward: Octopia (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2305370/ss_f5788b1d4ade71e0cdb1e0110debfad3b32ca51c.1920x1080.jpg?t=1770113484 |
| eastward/15 | Eastward: Octopia (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2305370/ss_c73bb91589b4ec73ba204ce2fbb402ce849cdc60.1920x1080.jpg?t=1770113484 |
| eastward/16 | Eastward: Octopia (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2305370/ss_6251ef76241411ab5659482fc644a215ffe4ddcf.1920x1080.jpg?t=1770113484 |
| eastward/17 | Eastward: Octopia (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2305370/ss_95e7b57126bf6395b4bbe0adabf1b633c20e5245.1920x1080.jpg?t=1770113484 |
| eastward/22 | Eastward (eastwardgame.com/media) | https://eastwardgame.com/wp-content/uploads/2023/10/eastward-features-2.jpg |
| eastward/30 | Eastward: Octopia (eastwardgame.com/media) | https://eastwardgame.com/wp-content/uploads/2024/06/Octopia-10_Bridge.jpg |
| eastward/37 | Eastward: Octopia (eastwardgame.com/media) | https://eastwardgame.com/wp-content/uploads/2024/06/Octopia-7_Fishing.jpg |
| eastward/39 | Eastward: Octopia (eastwardgame.com/media) | https://eastwardgame.com/wp-content/uploads/2024/06/Octopia-9_Beach.jpg |
| hyperlightdrifter/03 | Hyper Light Drifter (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/257850/ss_37ad0b207c867078e87cf8a185fe3c66b0bdd490.1920x1080.jpg?t=1762899660 |
| moonlighter/02 | Moonlighter (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/606150/ss_af36aa1ca2e534a999938cff0eb04409668f5b10.1920x1080.jpg?t=1790860598 |
| moonlighter/11 | Moonlighter (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/606150/ss_cdf8ac351f6e7c441e3b9b4e07d44833b3c926cd.1920x1080.jpg?t=1790860598 |
| pokemon-bdsp/03 | Pokémon Brilliant Diamond (nintendo.com/us/store/products/pokemon-brilliant-diamond-switch/) | https://assets.nintendo.com/image/upload/f_jpg/q_auto/store/software/switch/70010000039950/080d47d081a28d427e2cb3f4fe420a22c548caba89a169b1b68df38eedff9431 |
| seaofstars/02 | Sea of Stars (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_c250a7fd789b3cbab5ca8e99e3530cf933656ad1.1920x1080.jpg?t=1780931183 |
| seaofstars/05 | Sea of Stars (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_e7ac3a6e5ebe5f4561fc46d116c33678cf4ba811.1920x1080.jpg?t=1780931183 |
| seaofstars/07 | Sea of Stars (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/3fe79321f425c071dc91de0f54bcbea94cd91558/ss_3fe79321f425c071dc91de0f54bcbea94cd91558.1920x1080.jpg?t=1780931183 |
| seaofstars/08 | Sea of Stars (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_3444baf45a5dc2b27d0c7d385dbcad7e4b121791.1920x1080.jpg?t=1780931183 |
| seaofstars/12 | Sea of Stars (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_6c1428488a9c2aeecea2afe5f5e906be488b4dc0.1920x1080.jpg?t=1780931183 |
| seaofstars/15 | Sea of Stars (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_2f011be3599c238ff5d240bdb2bb2879e27271f1.1920x1080.jpg?t=1780931183 |
| seaofstars/24 | Sea of Stars (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_b1e28ca1b57123358ae4e0857e69eb313a54504d.1920x1080.jpg?t=1780931183 |
| seaofstars/26 | Sea of Stars (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_dd8fbf1f96e8a67b57e854f12ff9f48d55f5ca73.1920x1080.jpg?t=1780931183 |
| seaofstars/33 | Sea of Stars (Sabotage press kit) | https://sabotagestudio.com/wp-content/uploads/2022/03/Traversal-4-launch.png |
| seaofstars/35 | Sea of Stars (Sabotage press kit) | https://sabotagestudio.com/wp-content/uploads/2022/03/Traversal-7-launch.png |
| seaofstars/38 | Sea of Stars (Sabotage press kit) | https://sabotagestudio.com/wp-content/uploads/2022/03/World-12-launch.png |
| stardew/01 | Stardew Valley (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_b887651a93b0525739049eb4194f633de2df75be.1920x1080.jpg?t=1786554168 |
| stardew/03 | Stardew Valley (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_4fa0866709ede3753fdf2745349b528d5e8c4054.1920x1080.jpg?t=1786554168 |
| stardew/07 | Stardew Valley (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_a3ddf22cda3bd722df77dbdd58dbec393906b654.1920x1080.jpg?t=1786554168 |
| stardew/09 | Stardew Valley (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_64d942a86eb527ac817f30cc04406796860a6fc1.1920x1080.jpg?t=1786554168 |
| stardew/11 | Stardew Valley (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_5e327e4cfc49d8137f8014e728eae3c0e6be2dca.1920x1080.jpg?t=1786554168 |
| stardew/12 | Stardew Valley (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_980472fb4f4860639155880938b6ec292a0648c4.1920x1080.jpg?t=1786554168 |
| stardew/13 | Stardew Valley (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_f79d2066dfaf32bbe87868d36db4845f771eddbd.1920x1080.jpg?t=1786554168 |
| stardew/14 | Stardew Valley (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_4ff3fe6e9555052aaa076866407b0ba68fe73132.1920x1080.jpg?t=1786554168 |
| stardew/16 | Stardew Valley (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_f6f4c727570d753b2b5d8da6af4e0c38fe489059.1920x1080.jpg?t=1786554168 |
| stardew/20 | Stardew Valley (press kit) | https://www.stardewvalley.net/presskit/Stardew%20Valley/images/Multiplayer_Screenshot2.png |
| tunic/01 | TUNIC (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/553420/ss_9c0184ba83022786f74f4a70ebae5c47d2a3c35c.1920x1080.jpg?t=1783359656 |
| tunic/07 | TUNIC (Steam) | https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/553420/ss_260662fe9276ed7ffdd95c07891fb4dc0e6a0b6b.1920x1080.jpg?t=1783359656 |
| zelda-eow/05 | The Legend of Zelda: Echoes of Wisdom (nintendo.com/us/store/products/the-legend-of-zelda-echoes-of-wisdom-switch/) | https://assets.nintendo.com/image/upload/f_jpg/q_auto/store/software/switch/70010000084618/d92da089452a88aa37e69662589f047cae8de2294cc3583da3d43ba429fde85e |
| zelda-la/03 | The Legend of Zelda: Link's Awakening (nintendo.com/us/store/products/the-legend-of-zelda-links-awakening-switch/) | https://assets.nintendo.com/image/upload/f_jpg/q_auto/store/software/switch/70010000020033/e1b9dea18517d21f8ab3fcb0c1aa5a28331ca33da11c354e681d79a013fadfb4 |
| zelda-la/06 | The Legend of Zelda: Link's Awakening (nintendo.com/us/store/products/the-legend-of-zelda-links-awakening-switch/) | https://assets.nintendo.com/image/upload/f_jpg/q_auto/store/software/switch/70010000020033/0e3ab53cea0d73bc7ad270654406efd1dd11c3bf1ac4c8977b32aa410108b179 |

<!-- Link definitions: each [key] in the text links to its official image. -->

[chainedechoes/07]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1229240/ss_48db751b344de859c2fc1a4b3bc0dae74e341989.1920x1080.jpg?t=1788522273
[chainedechoes/10]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1229240/ss_a683aed9b1e2500b3aa7bb5f3d5d7a58f744dca8.1920x1080.jpg?t=1788522273
[chainedechoes/11]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1229240/ss_4b3a9335a15584143b657593522954595cd59e2d.1920x1080.jpg?t=1788522273
[chainedechoes/16]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/3350260/ss_d5290911adce3be6a2026295ac1bc9c90f78c5e4.1920x1080.jpg?t=1754586032
[chefrpg/07]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1796790/ss_a7919db771c21a757c2f32b22b5686eba0afcee0.1920x1080.jpg?t=1787346270
[chefrpg/08]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1796790/ss_0f0d961567c3eec213daefa246168a79b78bb7c1.1920x1080.jpg?t=1787346270
[chefrpg/09]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1796790/ss_691edcdd73121d2130aa8daf14839eece95756e0.1920x1080.jpg?t=1787346270
[crosscode/03]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/368340/ss_4a517a0780eaca5fa87c98ba5d1095812f415378.1920x1080.jpg?t=1788522282
[crosscode/08]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/368340/ss_df77c06e713d76f8245016177b54a7456b11c0a0.1920x1080.jpg?t=1788522282
[crosscode/10]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/368340/ss_e9c77a57c0be0e86416319b22331e48118c84020.1920x1080.jpg?t=1788522282
[crosscode/14]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/368340/ss_6a96ff676c98dc81905a550733086aa911cc9e6a.1920x1080.jpg?t=1788522282
[crosscode/15]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/368340/ss_4d1c860d8afea533b14a9a353831461c0df1071d.1920x1080.jpg?t=1788522282
[crosscode/17]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/368340/ss_c89e7de11d225926fa53fb9984fb287c3a2eb8be.1920x1080.jpg?t=1788522282
[crosscode/21]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1517030/ss_b0683222285e64efee92e3a1e4ec71670c8d6f55.1920x1080.jpg?t=1651242585
[crosscode/25]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1517030/ss_b896e0c2f17a0bf98743476a18702a2121fbd932.1920x1080.jpg?t=1651242585
[eastward/01]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_5d50545b49db3a8502666b4195d2fabd0e31a29d.1920x1080.jpg?t=1782290198
[eastward/02]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_b3512f7576dbdd1e35dd3fb27a04f29174efb00d.1920x1080.jpg?t=1782290198
[eastward/04]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_ddd76431b1df70e234494c92370e2391680c98ef.1920x1080.jpg?t=1782290198
[eastward/05]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_fc97f011126b32f77cbb66a9dc59e22cc353c2b8.1920x1080.jpg?t=1782290198
[eastward/07]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_c9a1045cf8d4c65cf0bdf38c4b5de7c9a05a0fb9.1920x1080.jpg?t=1782290198
[eastward/08]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_bf8d65929d363f1b62f632d934eda94ef5188049.1920x1080.jpg?t=1782290198
[eastward/10]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/977880/ss_29d7dd0891c88b08d699556ed62fcc37f1aea47f.1920x1080.jpg?t=1782290198
[eastward/12]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2305370/ss_c3e35bbd8e25af924b3b9cbf087f1f0c77dcf68a.1920x1080.jpg?t=1770113484
[eastward/13]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2305370/ss_f5788b1d4ade71e0cdb1e0110debfad3b32ca51c.1920x1080.jpg?t=1770113484
[eastward/15]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2305370/ss_c73bb91589b4ec73ba204ce2fbb402ce849cdc60.1920x1080.jpg?t=1770113484
[eastward/16]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2305370/ss_6251ef76241411ab5659482fc644a215ffe4ddcf.1920x1080.jpg?t=1770113484
[eastward/17]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2305370/ss_95e7b57126bf6395b4bbe0adabf1b633c20e5245.1920x1080.jpg?t=1770113484
[eastward/22]: https://eastwardgame.com/wp-content/uploads/2023/10/eastward-features-2.jpg
[eastward/30]: https://eastwardgame.com/wp-content/uploads/2024/06/Octopia-10_Bridge.jpg
[eastward/37]: https://eastwardgame.com/wp-content/uploads/2024/06/Octopia-7_Fishing.jpg
[eastward/39]: https://eastwardgame.com/wp-content/uploads/2024/06/Octopia-9_Beach.jpg
[hyperlightdrifter/03]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/257850/ss_37ad0b207c867078e87cf8a185fe3c66b0bdd490.1920x1080.jpg?t=1762899660
[moonlighter/02]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/606150/ss_af36aa1ca2e534a999938cff0eb04409668f5b10.1920x1080.jpg?t=1790860598
[moonlighter/11]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/606150/ss_cdf8ac351f6e7c441e3b9b4e07d44833b3c926cd.1920x1080.jpg?t=1790860598
[pokemon-bdsp/03]: https://assets.nintendo.com/image/upload/f_jpg/q_auto/store/software/switch/70010000039950/080d47d081a28d427e2cb3f4fe420a22c548caba89a169b1b68df38eedff9431
[seaofstars/02]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_c250a7fd789b3cbab5ca8e99e3530cf933656ad1.1920x1080.jpg?t=1780931183
[seaofstars/05]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_e7ac3a6e5ebe5f4561fc46d116c33678cf4ba811.1920x1080.jpg?t=1780931183
[seaofstars/07]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/3fe79321f425c071dc91de0f54bcbea94cd91558/ss_3fe79321f425c071dc91de0f54bcbea94cd91558.1920x1080.jpg?t=1780931183
[seaofstars/08]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_3444baf45a5dc2b27d0c7d385dbcad7e4b121791.1920x1080.jpg?t=1780931183
[seaofstars/12]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_6c1428488a9c2aeecea2afe5f5e906be488b4dc0.1920x1080.jpg?t=1780931183
[seaofstars/15]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_2f011be3599c238ff5d240bdb2bb2879e27271f1.1920x1080.jpg?t=1780931183
[seaofstars/24]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_b1e28ca1b57123358ae4e0857e69eb313a54504d.1920x1080.jpg?t=1780931183
[seaofstars/26]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1244090/ss_dd8fbf1f96e8a67b57e854f12ff9f48d55f5ca73.1920x1080.jpg?t=1780931183
[seaofstars/33]: https://sabotagestudio.com/wp-content/uploads/2022/03/Traversal-4-launch.png
[seaofstars/35]: https://sabotagestudio.com/wp-content/uploads/2022/03/Traversal-7-launch.png
[seaofstars/38]: https://sabotagestudio.com/wp-content/uploads/2022/03/World-12-launch.png
[stardew/01]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_b887651a93b0525739049eb4194f633de2df75be.1920x1080.jpg?t=1786554168
[stardew/03]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_4fa0866709ede3753fdf2745349b528d5e8c4054.1920x1080.jpg?t=1786554168
[stardew/07]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_a3ddf22cda3bd722df77dbdd58dbec393906b654.1920x1080.jpg?t=1786554168
[stardew/09]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_64d942a86eb527ac817f30cc04406796860a6fc1.1920x1080.jpg?t=1786554168
[stardew/11]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_5e327e4cfc49d8137f8014e728eae3c0e6be2dca.1920x1080.jpg?t=1786554168
[stardew/12]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_980472fb4f4860639155880938b6ec292a0648c4.1920x1080.jpg?t=1786554168
[stardew/13]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_f79d2066dfaf32bbe87868d36db4845f771eddbd.1920x1080.jpg?t=1786554168
[stardew/14]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_4ff3fe6e9555052aaa076866407b0ba68fe73132.1920x1080.jpg?t=1786554168
[stardew/16]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/413150/ss_f6f4c727570d753b2b5d8da6af4e0c38fe489059.1920x1080.jpg?t=1786554168
[stardew/20]: https://www.stardewvalley.net/presskit/Stardew%20Valley/images/Multiplayer_Screenshot2.png
[tunic/01]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/553420/ss_9c0184ba83022786f74f4a70ebae5c47d2a3c35c.1920x1080.jpg?t=1783359656
[tunic/07]: https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/553420/ss_260662fe9276ed7ffdd95c07891fb4dc0e6a0b6b.1920x1080.jpg?t=1783359656
[zelda-eow/05]: https://assets.nintendo.com/image/upload/f_jpg/q_auto/store/software/switch/70010000084618/d92da089452a88aa37e69662589f047cae8de2294cc3583da3d43ba429fde85e
[zelda-la/03]: https://assets.nintendo.com/image/upload/f_jpg/q_auto/store/software/switch/70010000020033/e1b9dea18517d21f8ab3fcb0c1aa5a28331ca33da11c354e681d79a013fadfb4
[zelda-la/06]: https://assets.nintendo.com/image/upload/f_jpg/q_auto/store/software/switch/70010000020033/0e3ab53cea0d73bc7ad270654406efd1dd11c3bf1ac4c8977b32aa410108b179

## 12. Gaps

- **A Link to the Past and The Minish Cap:** no official screenshots were reachable. They have no current nintendo.com store pages with a gallery (the 3DS pages return no images, the Wii U pages 404; they are now only in Nintendo Switch Online). Echoes of Wisdom, drawn in the Link's Awakening remake's style, stands in for the top-down Zelda look.
- **Pokémon and Animal Crossing:** the nintendo.com galleries were looked at (Brilliant Diamond and Shining Pearl, Mystery Dungeon Rescue Team DX, Animal Crossing: New Horizons). Only one Brilliant Diamond beach shot was kept; the rest are battles, interiors, menus or close-ups. These are 3D renders, so they teach layout, not pixel technique.
- **3D games** (TUNIC, the Switch Zelda games, Pokémon): used only for layout (where stairs, walls and beaches go), never for pixel sizes.
- **Moonlighter's and Chef RPG's own sites** did not answer; Hyper Light Drifter's and TUNIC's sites offer no extra gameplay shots, so only their Steam shots are used.
- Pixel sizes are measured on screenshots and converted by character height; treat them as plus or minus 2 px.
- Store screenshots are marketing images: some carry dialogue boxes, HUDs or cinematic bars, and they show each game at its best. That is what we want to match.
