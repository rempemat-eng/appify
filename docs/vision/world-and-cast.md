# The world and its cast: what holds it together (26 Oct)

Matt, 26 Oct 12:04: "think critically how all these different characters can fit into the game and its world (... the world should feel like many isolated parts but there should be some sort of overarching theme or thing that holds it together)".

**Status.** Claude A's proposal. It builds on the decided points and contradicts none of them: the Starfall, Glint, storm-broken Crossroads as the village you restore, the familiar who backs you with boosts, fourteen playable folk, village raids, the shared level and the skill tree. Sources: `game-design.md` (PR #223), `world-plan.md`, `world-atlas.md`, `regions/`, `vertical-slice.md`, `docs/story/act1.md`, `progression.md`, the castwork cast and Codex's kits (#261). The weapon lines are in `progression.md` and `game/data/progression/`. Every number is a placeholder.

## For Matt (one page)

**The unifying device: the stone circle and the ring of falls.** The stone circle in the woodland is older than every town. It was built to hold the moon's light. On the Starfall night it called the shards, and they fell in a **ring round it**: one great shard in every region, each crater's glassy scorch streaking back toward the valley. So the world is many isolated places with one centre, and the player feels that centre everywhere:

- **The cracked moon hangs in every sky.** Its crack closes a little with each stone lit.
- **The beam.** Once the circle wakes (act 1), a pale pillar of light stands over the valley at night. It shows on every region's skyline and brightens with each shard brought home.
- **Every crater points home.** Each region's crater has the same violet-and-gold shard glass, and the scorch runs toward the valley.
- **The waystones are the circle's kin.** They are chips of the circle carried out long ago, which is why fast travel runs between them.
- **The world map.** The circle sits at the centre, with the craters in a ring that light as you clear them. The line from each crater home is drawn when its shard reaches the lantern.
- **One shape to every region's story:** free what the shard twisted, carry the great shard home, and a new folk lights a stone.
- **Three faces you meet everywhere:**
  - **Moss**, who rides the trains and stocks each region's goods;
  - **the Company's buyer**, who is always one step ahead, buying shards;
  - **your familiar**, who points to the shard in every region.

The theme in one line: **the circle keeps the moon's light for everyone; the Company sells it.**

**Cast fit: problems and fixes.**

1. **Rook** is a generic astronaut. He joins only in act 4, and his place, Halcyon, belongs to the villain. **Fix:** make him **the Launch Cape's pad rigger**: ground crew who built the rocket the Company took. He wears a flight-line coverall and a flip-up welding visor in place of the pressure suit and space helmet. His thruster pack is a rocket test rig and his turrets are pad survey drones. He joins at the end of act 3, when the rocket is fuelled (W8), and flies you up. His kit is unchanged; his body art is redrawn.
2. **Tam** is a bald warrior monk in saffron, in a highland country of bothies. **Fix:** the Frostline gets **the Saddle House**, a small cliff monastery whose order has kept the col and the bothy open for generations. The saffron is there to be seen against snow, as a rescue order would wear it. The hut warden is the order's last elder.
3. **The spread of technology** (knights, cowboys, steam, neon, rockets) reads as random. **Fix:** technology follows the rail and the shards:
   - Cogsworth's railway carried steam outward.
   - Places the rail never reached kept older ways: Hearthold behind its lava, the Frostline order, the Isles' sail.
   - Only the Company leapt ahead, on bought shard light: Neon Harbour's neon and Halcyon's rockets.
4. **Pendle**, a robot in a western town, needs a reason to be there. **Fix:** Cogsworth's works built him as the desert line's marshal. When the Rift cut the line, Dust Gulch kept him as its sheriff.
5. **Brine**, a copper-helmet diver on a natural island, needs a reason too. **Fix:** he is the naturalist's salvage diver, working the reef wrecks off the Shell Bar. His gear comes from Driftwood's trade.
6. **Act 3 is crowded** (Mirra, Pendle, Ashe, Nix and Rook join). This is acceptable, because act 3 is the longest. One fallback is to let Pendle ride in early on the desert line's first train.

**Weapon lines and trees** (details in `progression.md`). Tiers open at levels 8, 16 and 24, and Hale forges them cheaply. Each tree has three branches: **kinds** (one loaded at a time), the **weapon** branch (forms and its signature move) and **craft**. *New clips* marks the one form change per folk that needs new clip tables. The other steps are rig parts on the existing clips.

| Folk | Level 1 | Level 8 | Level 16 | Level 24 | Tree: kinds; weapon; craft |
| --- | --- | --- | --- | --- | --- |
| **Bramble** | Yew bow | Hedge crossbow *(new clips)* | Repeating crossbow | Starfall repeater | **Bolts** (barbed heads, fire heads, shard heads); **Volley** (Twin shot to Three-bolt spread); **Woodcraft** |
| **Iona** | Ash spear | Winged spear | Storm glaive *(new clips)* | Starfall lance | **Storm** (static, gale, rain); **Lance** (Gale step to Gale step II); **Gust** |
| **Pendle** | Trail revolver | Sunhammer | Twin Sunhammers *(new clips)* | Six Suns | **Rounds** (hot-loaded, silver, lodestone); **Gunslinger** (Ricochet to Ricochet II); **Marksman** |
| **Cairn** | Bare stone | Banded fists | Boulder gauntlets | Moonvein gauntlets | **Stones** (river stone, mossball, flint); **Fists** (Stonebreak to Stonebreak II); **Bedrock** |
| **Morel** | Field kit | Bandolier | Flask mortar *(new clips)* | Starglass mortar | **Reagents** (glue, frost salt, quicklime); **Volley** (Pair to Cluster); **Remedies** |
| **Velvet** | Naval sabre | Cutlass | Moth sabre and dark lens *(new clips)* | Moonlit sabre | **Lights** (white light, amber light, moth dust); **Blade** (Moth's waltz to Moth's waltz II); **Shadow** |
| **Tam** | Plain wraps | Iron wraps | Frost gauntlets | Moonbead gauntlets | **Stances** (crane, ox, glacier); **Ridge** (Twin ridge to Three ridges); **Stillness** |
| **Mirra** | Turquoise bands | Wave bands | Spring orb | Starspring orb | **Waters** (spring water, brine, hot spring); **Currents** (Undertow to Fountain); **Curtain** |
| **Brine** | Dock harpoon | Sheathed harpoon | Pressure cannon *(new clips)* | Abyssal cannon | **Heads** (barbed head, eel head, buoy head); **Winch** (Anchor line to Snap line); **Brace** |
| **Ashe** | Knight's sword | Ember longsword | Wyrmfang | Starforged fang | **Flames** (ember, smoke, white fire); **Blade** (Crescent to Twin crescent); **Plate** |
| **Clack** | Works launcher | Plated launcher | Twin-tube launcher *(new clips)* | Starnose launcher | **Rockets** (cluster, incendiary, concussion); **Salvo** (Hot loader to Hot loader II); **Shield** |
| **Nix** | Courier arm | Finned arm | Split-lens arm | Pearl arm | **Pulses** (needle, arc, scatter); **Ghost** (Flashbreak to Flashbreak II); **Shield** |
| **Rook** | Salvage carbine | Shrouded carbine | Twin-barrel rifle | Launch-gold rifle | **Cells** (amber cell, flare cell, mag cell); **Jets** (Air shot to Air shot II); **Rig** |
| **Mote** | Observatory core | Dropped hooks | Orrery | Little moon | **Glass** (clear glass, violet glass, mirror glass); **Gravity** (Starfall to Starfall II); **Panes** |

**Decisions for you** (recommendation in bold):

1. **The device.** **The stone circle and the ring of falls, with the beam, the craters pointing home, the waystones as the circle's kin and the map built round it.** Or keep the train lines as the only link.
2. **Rook.** **Rework him as the Launch Cape's pad rigger**, joining at the rocket (act 3's end). His kit is kept; his body art is redrawn. Or keep the orbital salvager on Halcyon.
3. **Tam.** **The Saddle House order, with Tam a bald warrior monk in saffron.** Or drop the monastic dress for highland clothes.
4. **Weapon lines.** **Approve the table, and build Bramble's crossbow and Pendle's twin guns first.** These are the two lines you described, and they test both kinds of form change (a new weapon, and a second weapon).
5. **Kinds as a loadout.** **One kind loaded at a time, set at a waystone or the hut.** Or a quick switch in a fight, which would need a fifth button.

## 1. The critique: what holds the world together today

- **The old glue is gone.** The world atlas tied the regions by a theme of rest and screens: quiet near home, glare in the neon city, sleep on the moon. Matt removed rest on 21 Oct, so that line no longer explains anything.
- **The Starfall explains each region's trouble, but not why they belong to one world.** As written, each region has its own shard, boss and folk, and the regions only touch by train.
- **The cast is strong one by one but scattered as a set**: a medieval knight, a cowboy robot, a cyborg and an astronaut need a rule for why they share a continent.
- **What already works**: the regions' geography explains itself (world-plan 4), each region looks like its own place (world-atlas: "not reskins"), the nine ways tie the story to the land, and the fourteen stones tie the cast to the circle. The device below builds on these and adds nothing that must be taken back.

## 2. The device in full

**Lore.** The circle was raised by people who watched the moon. Its twin is the observatory on Lumen, which Mote keeps. When the Company's drill cracked the moon, the circle pulled the falling shards toward itself, and they landed in a ring. The storm that came with them broke the nine ways, so each region was cut off from the others. Bringing the shards home closes the ring: the moon mends when all fourteen stones are lit and every great shard is back (game-design 8.1).

**How the player feels it in every region.**

| Channel | In every region | How it grows |
| --- | --- | --- |
| Sky | the cracked moon; at night, the circle's beam on the skyline toward the valley | the crack narrows and the beam brightens with each stone and shard |
| Ground | the shard crater, in the same violet-gold glass, its scorch pointing home; shardstruck ground round it | the crater cools and greens after the shard leaves |
| Waystones | a small standing stone with the circle's carving | each waystone lights when its region's shard is home |
| The familiar | points to the region's great shard and the elites' weak points | the familiar's bond grows over the whole journey |
| People | Moss on the train with the region's goods; the Company's buyer a step ahead; a villager who moves to Crossroads | Crossroads gains one feature from each region (game-design 7.4) |
| Story | free the shard's guardian, carry the shard home, a folk lights a stone | the circle's light rises in the village and over the map |
| Map | the circle in the middle, the ring of craters, the lines home | a full ring and fourteen lit stones at the end |
| Raids | the shards in the lantern draw raiders to Crossroads | each region adds its own raiders (game-design 7.6) |

**What it costs.** Most of it uses things already planned: the craters, the lantern, the waystones, the map, Moss and the Company. It adds three things. The **beam and the moon's crack** are sky layers shared by every region, a set of five crack states and a beam drawn at three strengths. The **crater's scorch direction** is a parameter in each region's crater piece. Each waystone gets **the circle's carving**.

## 3. The regions: why each is isolated

Technology follows the rail and the shards (fit problem 3). The tech column is what the place runs on.

| Region (act) | Cut off by | Culture | Tech | What the Starfall did | Folk |
| --- | --- | --- | --- | --- | --- |
| The valley and woodland (prologue, 1) | the Headland's wall, the Millrace landslip (W1, W3) | a market town and its farms; Driftwood's fishers | hand tools, the mill, the halt | thorns over the circle; Crossroads burnt; the forge cold | Bramble, Morel, Velvet, Cairn |
| The Frostline (1) | the ridge col (W2); the massif | the Saddle House's monks, the hut warden, ice-cutters | rope, stone and kettle | shard crows over the col; the Rime Wyrm under the lake | Tam |
| The Brackens (1) | the moor's bluffs and the Rift (W5 to the west) | drovers and the moor wardens, lancers who guard the drove roads | horse, crook and lance | shard wolves scatter the flock | Iona |
| Cogsworth and the coal hills (2) | the Cog's gorge; the Narrows | foundry and railway people | steam, brass, black-powder rockets | automata run wild on shard power; the Company fences a seam | Clack |
| The Lull (2) | the river; Lullford's swing bridge (W7) | bargees and millers | barge and sluice | smugglers on the river | none (a mover) |
| The Tidebloom Isles (2) | the sea; the Shell Bar and the ferry (W4) | the naturalist, fishers, divers off the wrecks | sail; Driftwood's diving gear | the volcano's shard wakes the basalt | Brine |
| The Sunstone basin (3) | the Rift's viaduct (W5); the desert | oasis keepers and a railhead town | windpumps and the desert line; Pendle is Cogsworth-made | the Company's drill stops the spring | Mirra, Pendle |
| The fire country (3) | the lava flows and the chasm bridge (W6) | Hearthold's knights, the Ember forge | forge and sword; cut off for generations | the dragon shardstruck; the Company presses the forge | Ashe |
| Neon Harbour and the Launch Cape (3) | the maglev and the Lull (W7) | the Company's city; couriers and fixers | shard-powered neon, the maglev, rockets | the Company's power, bought with shards | Nix, Rook (proposed) |
| Halcyon Station (4) | orbit (W8) | the Company's drilling platform | shard drills | the drill itself | none |
| Lumen (4) | the lander (W9) | the observatory, the circle's twin | old glass and light | the crack's heart | Mote |

## 4. The cast: where each folk belongs

| Folk | Home | Why there | What the Starfall did to them | Why they join | Fit |
| --- | --- | --- | --- | --- | --- |
| Bramble | the woodland's forester's yard | he keeps the valley's paths | thorns over the circle he guards | it is his valley | good |
| Morel | the herbalist's on the square | the town's chemist | his shop torn open; the shardstruck fever | the apothecary reopens (act 1) | good |
| Velvet | Driftwood's lighthouse | she keeps the harbour light | the lamp dark, ships lost on shards in the bay | the light is lit again (act 1) | good |
| Cairn | the stone circle | a stone of the circle that woke | the shards woke him | the circle's trial (act 1) | good: the device's own child |
| Tam | the Saddle House, the Frostline | his order keeps the col | the Rime Wyrm; the col closed | the bothy reopens; he follows the shards | fixed by the Saddle House |
| Iona | the Brackens, a moor warden | her riders guard the drove roads | shard wolves | the flock home, the road west open | good once the moor wardens are named |
| Clack | Cogsworth's foundry | he made the railway's signal rockets | the automata run wild; the Company fences the seam | the foundry freed; the first guns | good |
| Brine | the Isles (Lagoon Landing's boathouse) | the naturalist's salvage diver | the basalt wakes, the reef closes | the cove freed | fixed by the salvage trade |
| Mirra | Palm Spring | the oasis's diviner | the Company's drill stops the spring | the spring flows again | good |
| Pendle | Dust Gulch | Cogsworth-built marshal of the desert line, now the town's sheriff | the line cut; the town dry | the drill stopped; the line open | fixed by the marshal story |
| Ashe | Hearthold | a knight of the castle | the dragon shardstruck; the forge pressed | the dragon freed; she carries its fang | good |
| Nix | Neon Harbour | a courier whose arm is Company work | the Company's power, bought with shards | turns on the Company | good |
| Rook | the Launch Cape (proposed) | the pad rigger who built the rocket | the Company took his rocket | fuels it and flies you up | fixed by the rework |
| Mote | Lumen's observatory | the circle's twin keeper | the crack's heart | the fourteenth stone; the full moon | good: the device's other end |

**Recurring faces.** Moss travels the lines with each region's goods (her stall widens as the ways open). The Company's buyer is in every region just before you, buying shards (game-design 8.1 foreshadows him in act 1). Hale's forge turns each region's material into the folk's next weapon tier. Each region's mover brings one feature to Crossroads.

## 5. Weapon lines in brief

Each line keeps the folk's identity and its four actions. The full art and rig notes are in `progression.md` section 5 and the folk's JSON.

- **Seven form changes need new clip tables**: Bramble's crossbow, Iona's glaive, Pendle's twin guns, Morel's mortar, Velvet's beam lantern, Brine's cannon and Clack's twin tubes.
- **The other steps are parts on the existing clips**: Cairn's gauntlets, Tam's ice gauntlets, Ashe's Wyrmfang (one-handed, so the helm stays under her arm), Nix's split lens, and Rook's twin barrel. Mirra's spring orb and Mote's orrery are effect sprites anchored to the hand and the core, so their hands and bodies stay as drawn.
- **Readable at 74 px**: each tier changes the silhouette by at least 3 px or adds one new 2 x 2 px colour cluster, and sizes are relative to the tier-1 drawing.

## 6. Conflicts (raised on #149)

- **The form changes** need the runner to swap the primary's projectile and hit parameters per tier: count, spread, capacity and alternating hands. The kit files stay canonical.
- **Loadout kinds** add an effect to hits.
- **Seventeen nodes** change a count or rule in a kit or powered form and are flagged `touches_canonical`.
- **Rook's rework** changes art only. His kit, including the Orbital Rig turrets, is unchanged.
