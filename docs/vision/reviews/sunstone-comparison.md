# Sunstone Reach beside comparable places

Claude D, 19 Oct 2026 (task S3 in `coherence-plan.md`). Matt asked for this on 18 Oct: "occasionally compare with similar games if the current world makes sense and looks good". This note sets Sunstone Reach (Dust Gulch, the oasis, the Scorched Pass, Hearthold, the caldera and Cinder Springs) beside three well-documented places in other games: a desert you reach by vehicle, a hot-spring town under a volcano, and a mining town above lava. Each comparison gives what reads better there, what we changed because of it, and what we deliberately keep different.

Sources are limited to developer talks, official sites and community wikis that cite the games. I have not played these games for this note, so claims about them stay at the level the sources support.

## 1. Stardew Valley's Calico Desert: arriving by vehicle in a desert

What the wiki records ([Stardew Valley Wiki, "The Desert"](https://stardewvalleywiki.com/The_Desert)):

- The desert lies far from the home valley and is reached only by the repaired bus. The bus is there whenever you arrive, so the way home is always in sight.
- A few landmarks are spread across one screen-sized map:
  - Sandy's Oasis shop in the south-west.
  - A sand-dragon skeleton on a hill north of the shop.
  - Three pillars in the north-east.
  - The Desert Trader's tent in the east.
  - The Skull Cavern mine entrance in the north-west corner.
  - A pond beside the mine, and a smaller pond on the south edge.
- The original trees are palms.

What reads better there:

- **Every landmark has one job and its own corner.** The shop, the trader, the mine and the ponds never compete for the same spot.
- **The vehicle that brought you is part of the scene.** It is not an icon.

What we changed:

- Dust Gulch already strings its town along one street from the railway (saloon, store, water tower, corral).
- S1 gave the mine and its cart line their own corner. The mine is a mouth cut into the mesa's face. Its narrow-gauge bay sits beside the platform, with a dry forecourt between the two.
- The main line ends at a buffer you can see, so the train that brought you has a visible end, like the bus.

What we keep different:

- Our oasis is a separate place west of the town, with the caravan camp at the end of the street. It is not a shop in the town. It explains why the town exists (the creek was the pool's overflow until a dune crept over the outlet), which a cosy game can afford to show in the landscape rather than in text.

## 2. Pokémon Ruby, Sapphire and Emerald: Mt. Chimney and Lavaridge Town

What the wiki records ([Bulbapedia, "Mt. Chimney"](https://bulbapedia.bulbagarden.net/wiki/Mt._Chimney); [Bulbapedia, "Lavaridge Town"](https://bulbapedia.bulbagarden.net/wiki/Lavaridge_Town)):

- **Two ways up.** A cable car climbs the volcano's side to a terminal at the peak. Jagged Pass descends the south side on foot, with ledges and ash-covered grass, back to Route 112. From there a path leads west to Lavaridge Town.
- **The crater is the summit's one feature.**
- **Ash falls downwind.** The volcano's soot rains on Route 113 to the north, leaving the grass and trees coated.
- **The town's water is its own.** Lavaridge sits at the volcano's southern foot and is known for its hot springs. The wiki's explanation: "The magma in the active volcano causes veins of water nearby to well up as hot springs."

What reads better there:

- **The two approaches are clearly different in kind**: a ride up, a walk down. Each ends at a named place.
- **The hot springs are explained as groundwater heated by the volcano, not as lava.** Their water comes from their own source.

What we changed:

- S1 made Cinder Springs follow the same logic. The lava branch that ran into the springs is gone. The springs' water wells up at the top terrace and runs off the bottom one as a steaming stream, down the volcano's flank. No blue pool receives molten rock, which is Codex's rule as well.
- Our two approaches to Hearthold already match Pokémon's two kinds of route, and S1 made the ride's end physical:
  - the walk through the Scorched Pass to the long south bridge;
  - the mine cart from Dust Gulch to the caldera and the postern.
    The cart line now ends at a buffer on a basalt landing. Paths lead from it to the bridge, the forge and the ring.

What we keep different:

- We do not grey the scrub with ash fall downwind. Our Scorched Pass instead makes the change gradual on the ground: the gulch's sand gives out into a scrub belt and then ash along a wandering line about 100 px wide, and the lava keeps a collar of ash and cooled crust, so sand never meets molten rock.

## 3. The Legend of Zelda: Breath of the Wild: Goron City and the Eldin approach

What the sources record ([Zelda Wiki, "Goron City"](https://zeldawiki.wiki/wiki/Goron_City)):

- Goron City lies west of Death Mountain in Eldin Canyon. A marker at the road reads "Welcome to Goron City."
- Bridges give "safe passage over a pool of Lava below the City", and the Mountain Road runs through the city to the Abandoned North Mine.
- The city's industry is the Goron Group Mining Company.

What the developers said about laying out such approaches comes from Nintendo's CEDEC 2017 talk, as reported by [GIGAZINE (4 Oct 2017)](https://gigazine.net/gsc_news/en/20171004-breath-of-the-wild-design-secret):

- **Triangles at three scales.** Large ones are landmarks, medium ones shield landmarks and routes, small ones vary the pace.
- **Gradual reveal.** Terrain hides a destination until the player is close; one example is the chain "hill, then bridge structure, then tower".
- **Pull by size and purpose.** Objects pull the player toward them in proportion to their size and purpose.

What reads better there:

- **A lava town is safe because its bridges and roads are made, solid and obvious, and the danger stays below them.**
- **The approach reveals the destination in stages.**

What we changed:

- **Hearthold's danger stays outside.** The castle has a curtain wall all round its isle, broken only by the gate and the postern, so no paving runs out to the moat (play-test finding 14). Both bridges keep their parapets.
- **The lava is one course you can follow:** from the crater lake, down the caldera, round the castle rock and out through the Scorched Pass into a crusted basin, with no light line at the tile joins.
- **Hearthold now looks made, at the density Matt set** (19 Oct, a stone tower with a timber storey):
  - coursed stone with every block its own tone;
  - slate roofs in single tiles;
  - an oak porch, a timber belfry and hoardings on beam ends.
- **The Scorched Pass's road reveals its destination in stages.** Each step pulls the eye to the next, the way the talk describes:
  - the small bridge over the drain;
  - a lantern at each bend, each throwing a warm pool on the ash;
  - the castle's banners at the long bridge;
  - the gatehouse.

What we keep different:

- No heat meter, no damage, no gear to cross. Lava is scenery and a barrier only (AGENTS.md: decorative things add no rules).

## Still to do from this comparison

- **World edges** (`art-faults.md`, rule 10). The empty cells in Sunstone's grid (north of the gulch and the oasis, east of Hearthold) should be real scenery you cannot walk on: a mesa country, the volcano's flank. Today they are filler around the walkable zones. In the browser (19 Oct, local export at 360 and 402 px) the cell north of Dust Gulch shows the volcano's basalt flank (`components/atlas-walk.tsx` picks `zoneBeyondAsh` for column 0 at row -1). Desert or mesa country belongs there: the row -1 test would become row -2.
- **Dust Gulch's buildings and the caldera's forge** should get the same material kit as Hearthold (`castle_props.masonry`, `slates`; boards with grain for the false fronts). The forge has it since S7 (19 Oct): a slate roof with verges, a dressed stone stack, coursed walls sooted round the furnace, an arch of voussoirs and an oak lean-to over the anvil, the quench trough and a tool rack. The false fronts already have grained boards; their tin roofs and boardwalks are the next candidates.
