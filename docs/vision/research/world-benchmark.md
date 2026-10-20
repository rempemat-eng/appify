# World benchmark for NapAttack v5.2: density, boundaries, transitions, obstacles

For the map agents (first written for the world plan's v5.2; its checklist, section 5, is for every lane). Research of 20 Oct (Matt, 15:50: transitions "perfect", "a decent amount of things in each of the major biomes", world boundaries "excellent", "obstacles ... and little paths", "compare with other games").

**Units.** One NapAttack screen = 320 x 576 art px = 12.8 x 23 adults (A = 25 px) = about 294 A². Walk speed 40 px/s, so a screen is 8 s across and 14.4 s down. Conversions used below (one person = one tile in the 16 px games; Stardew's farmer is two tiles tall):

| Game                      | Screen                    | Person      | One NapAttack screen equals |
| ------------------------- | ------------------------- | ----------- | --------------------------- |
| A Link to the Past (SNES) | 256 x 224                 | about 24 px | about 3 ALTTP screens       |
| Link's Awakening (GB)     | 160 x 128 play area       | 16 px       | about 3.7 LA screens        |
| Pokémon Gen 3 (GBA)       | 240 x 160 (15 x 10 tiles) | 1 tile      | about 2 GBA screens         |
| Stardew Valley            | tiles of 16 px            | 2 tiles     | 294 A² = 1,176 tiles        |

The reference images (VGMaps: the ALTTP Light World, Link's Awakening's Koholint in GB and DX, Minish Cap's Hyrule, and Emerald's Routes 104, 110, 111, 113, 119 and 120) are not in the repository; Claude A keeps them in its scratchpad (`bench/`). The Sources list gives each one's address.

## 1. Content density

### 1.1 What the references put in an area (measured)

| Game, area                 | Size                                                                                           | Contents                                                                                                                                                                                                                                                                                          | Per NapAttack screen                                                                                               |
| -------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| ALTTP Light World          | 8 x 8 map squares of 512 px = 4096 px a side (TCRF; VGMaps image); about 100 NapAttack screens | about 15 named regions (Lost Woods, Kakariko, castle, Death Mountain, Zora's River, Eastern Palace, Lake Hylia, swamp, desert...); 24 Pieces of Heart across both worlds; walls are "impenetrable mountain ridges, stands of trees, or riverbanks"; "Of 256 mini-chunks only 6 cannot be reached" | 1 named region per about 7 screens, each packed with houses, caves, bushes, rocks; rewards sparse (0.1 per screen) |
| Link's Awakening, Koholint | 16 x 16 screens of 160 x 128 (2560 x 2048 image); about 70 NapAttack screens                   | about 20 named districts (approximate); 26 Secret Seashells and 12 Pieces of Heart (GB); 50 and 32 in the 2019 remake                                                                                                                                                                             | 1 district per about 3.5 screens; secrets 0.55 per screen (GB), 1.2 (remake)                                       |
| Pokémon Emerald, Route 119 | 40 x 140 tiles (VGMaps), about 19 NapAttack screens                                            | 21 visible items, 6 hidden, 17 trainers; Weather Institute, 2 Secret Base spots, 3 bridges (one very long), waterfalls, long-grass field, a hill climbed by "several flights of stairs"                                                                                                           | about 2.3 things a screen, plus a landmark every 2 to 3 screens                                                    |
| Emerald, Route 113         | 100 x 20 tiles, about 7 screens                                                                | 10 visible items, 5 hidden, 6 to 10 trainers; the Glass Workshop; ash on every tile                                                                                                                                                                                                               | about 3.5 things a screen                                                                                          |
| Emerald, Route 111 desert  | inside a 40 x 140 tile route                                                                   | 5 visible items, 9 hidden; 5 (RS) or 9 (E) trainer sets; Mirage Tower, Desert Ruins, fossils                                                                                                                                                                                                      | hidden items outnumber visible ones in the harshest biome                                                          |
| Stardew, The Mountain      | 135 x 41 tiles (5,535 tiles; wiki), about 4.7 NapAttack screens                                | Carpenter's Shop and house, Linus' tent, a treehouse, the Mines, the Adventurer's Guild, the Quarry behind a broken bridge, a central lake with legendary fish; 3 gated passages (earthquake pass, boulder, hidden passage); forage 0.5 a night on 4% of tiles                                    | 1.3 landmarks a screen; 0.6 gates a screen                                                                         |
| Stardew, Secret Woods      | 1,920 tiles, about 1.6 screens                                                                 | behind a Large Log; 6 Large Stumps, a statue (Old Master Cannoli), a pond with a unique fish                                                                                                                                                                                                      | a secret pocket holds 3 kinds of thing                                                                             |
| CrossCode, Autumn's Rise   | 27 rooms                                                                                       | 29 chests, 5 landmarks (teleporters), 4 traders, 9 quests, 4 puzzle mechanics                                                                                                                                                                                                                     | about 1 container per room, 1 landmark per 5 rooms                                                                 |
| Sword/Shield, Wild Area    | 18 subareas                                                                                    | 99 Pokémon Dens (5.5 per subarea), weather set per subarea, named lakes, bluffs, a stone arch, a stone circle                                                                                                                                                                                     | every subarea has a name, a landform and its own weather                                                           |

What fills the areas, by kind: landmarks (towers, ruins, a lake, a big tree), residents (trainers, a hermit's tent, a hut), resource spots (stumps, forage tiles, fishing), small puzzles (switches, a boulder), secrets (hidden items, seashells under rocks, a statue in a hidden wood), viewpoints, and lore. Sea of Stars' rule: "when you turn over a stone there should be something under it" (Boulanger); it "feels like a game where it's all these small pockets". Hyper Light Drifter: each major section has its own population, terrain, geography and traces of culture, and "sometimes it will just be some dead bodies and ruins, and there will be some mystery to it" (Diefenbach). Chained Echoes fills its world maps "with tons of little details" (Linda).

### 1.2 Targets for NapAttack (per 320 x 576 screen of walked ground)

NapAttack's secrets and decorations give no rewards, costs or chores, so the references' item density becomes noticing density: things to look at, residents to meet and places to sit, at the same rate.

| Screen type           | Landmark (a named silhouette)                                    | Interactable (tap target: resident, sign, bench, door, existing play object) | Decorative with a story (no tap: a cart with a broken wheel, a cairn, tracks, a mended fence) | Ambient life |
| --------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ------------ |
| Route                 | 0.5 to 1 (one every 1 to 2 screens, seen from the screen before) | 2 to 3                                                                       | 3 to 5                                                                                        | 1 to 2       |
| Biome core (off-town) | 0.5 to 1                                                         | 2 to 4                                                                       | 4 to 6                                                                                        | 2            |
| Settlement            | 1 to 2                                                           | 6 to 10                                                                      | 6 to 10                                                                                       | 2 to 3       |

The plan's "something every 5 s" is 200 px, so about 3 noticeable things per screen height; the table meets it. Per major region (8 to 25 screens): at least 3 named places plus 1 per 6 screens (LA's rate is 1 per 3.5); at least 3 secret pockets, about 1 per 5 screens (above the plan's "1 to 3", in line with LA and Stardew); 1 resident camp or hut outside a town (Linus' tent); 1 viewpoint; 1 ruin or story site; 2 kinds of wildlife found only there; 1 water feature.

## 2. World boundaries

### 2.1 How the references end the world (observed on the VGMaps images unless cited)

- **ALTTP.** Cliff rims on west, south and east, Death Mountain's massif across the north (reached only "through a tunnel"), and the Lost Woods' solid canopy in the north-west. The rims are stacked two or three deep with ledge bands between and turn at 45 degrees. The outermost line can run straight for two or three screens (the desert's west wall), but the inner rims jog every 3 to 8 tiles, so the eye reads the broken inner edge, not the straight outer one. Lake Hylia is held by cliffs on its far side.
- **Link's Awakening.** The Tal Tal range is a band one to two screens deep across the whole north, with the Wind Fish's egg on top as the one landmark that is always above you; beyond it the map shows sky and sea. South and east end in beach and sea (Toronbo Shores, Martha's Bay); the desert sits in the south-east corner between cliffs and sea.
- **Pokémon Gen 3.** Tree walls 2 to 6 tiles deep with bulging canopies and ragged inner edges, rock walls, and water. Routes are corridors 10 to 25 tiles wide inside maps 40 tiles wide (Routes 104, 110, 111, 119, 120). Past the map edge the engine repeats a small border block of trees or water, so the land never ends on screen (engine detail from the pret decompilation, not re-checked here). The desert of Route 111 is a basin walled by cliffs, and its sandstorm is the boundary: the desert "cannot be traversed without the Go-Goggles".
- **Sword/Shield Wild Area.** City walls (Motostoke's, Hammerlocke's), bluffs, lakes and a dividing river; an island in Lake Axewell (Axew's Eye) is visible but out of reach until the Rotom Bike.
- **Stardew.** Each map ends in a canopy of trees or cliffs; exits are few (the Mountain starts with two) and the gated ones are physical things being cleared: bridge debris (spring 5), an earthquake pass (summer 3), a boulder, a Large Log needing a Steel Axe, a broken Quarry bridge. The Forest Farm is framed by a border of trees and foliage.
- **Sea of Stars** keeps a separate world map (the camera "zooms out for world traversal"); inside areas the edges are cliffs you climb, jump and swim along. **Tunic** hides edges and treasure behind the fixed camera: "you can slip around a corner and sort of hide from the camera", and fading trees failed because "the solidity of the world was compromised". **Eastward, Moonlighter, Chained Echoes:** no credible source on their edges found in this pass.

### 2.2 Excellent versus cheap

Cheap: an invisible wall; one row of identical trees; a straight cut longer than a screen; a border one tile deep; scenery beyond the edge that looks reachable but is not explained; content placed past the edge (the Fallout 3 complaint in the gamedev.net thread). Excellent: the border has depth (two or three strata), a material reason, a jog at walking scale, at least one thing seen beyond it, and a promise that is kept (Axew's Eye, ALTTP's desert ledges reached later from the Dark World).

### 2.3 Techniques per border type (for NapAttack's edges)

| Border                          | Strata from the walked side out                                                         | Beyond                                      | Break-up and promise                                                                               |
| ------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Sea cliffs (south coast)        | turf lip, then 96 to 192 px face, then boulders and surf                                | the isles, a sail, a far headland           | coves every 1 to 2 screens; one stair down to a beach; a sea stack you cannot reach                |
| Mountain range (north massif)   | scree and lone pines, then a 64 px rock face, then snowfields and a second face         | glaciers and peaks to the top edge          | a gorge where a river comes out with no path; a hut or cairn at the last reachable spot            |
| Dense forest (east, old forest) | brambles and fallen logs, then trunks of 3 or more species and sizes, then solid canopy | darker canopy fading into haze              | canopy bulges every 2 to 4 trees; a deer trail that ends in a clearing (a pocket)                  |
| Desert (west, dune sea)         | scrub islands, then a dune crest, then open dunes                                       | dune ridges running off the edge, heat haze | a dry riverbed fading into the sand; a buried ruin top; wind (Route 111's sandstorm) as the reason |
| Marsh (east, moss fens)         | reeds and boardwalk end, then pools, then bog                                           | meres catching the sky                      | a broken boardwalk (the "you'll come back" sight without a promise to keep); a heron               |
| Wide river                      | water meadow, then bank, then water 3 A or more wide                                    | the far bank with something on it           | bridges and fords only where a route needs them; the far bank's landmark                           |
| Chasm (Rift)                    | rim stones, then the drop drawn as two or three bands                                   | the far rim, the viaduct                    | a rope bridge or ferry at the threshold; a ledge path visible on the far wall                      |

## 3. Transitions between biomes

- **Neutral buffer.** Link's Awakening puts a screen of shared base tiles between any two screens with different custom tilesets, "a kind of memory airlock" (setsideb, from the disassembly). The technical reason became a design one: one screen of shared ground between two characters.
- **Fade with a cause.** Route 113: "what appears to be snow begins to fall as the grassy landscape gives way to a dust-covered one"; the ash stops where the long grass ends near Fallarbor. One material spreads from a source and thins with distance.
- **Walls with a gap.** Route 111 enters the desert through a cliff gap after a Rock Smash blockade on the south; Route 119 steps up by waterfalls and stairs. ALTTP's Death Mountain is a cave threshold; its open south row "clear across" from the desert to Lake Hylia is the corridor that ties biomes together.
- **Weather and sound.** Route 119 rains three days of four; the Wild Area sets weather per subarea; Hyper Light Drifter changes music by place (birdsong by water, discord in a facility); Sea of Stars has night versions of its music.
- **Hide, then reveal.** Breath of the Wild's CEDEC talk (Fujibayashi, Yonezu): obstacles are triangles you go "over or around", and they "hide exciting surprises". Tunic's camera "control[s] when you get these bigger vista views, and when you would see a certain landmark".

What to copy: every transition has a source the change radiates from (volcano, glacier, river, sea), a buffer of at least one screen where both palettes and prop sets mix, a threshold object (bridge, gap, stair, cave, gate), a crest or bend that hides the next region until the threshold, and a weather or ambience change at it.

## 4. Obstacles and little paths

**Vocabulary in the references.** Boulders and wooden posts (ALTTP, item gates), bushes and tall grass, stumps and logs (Stardew), a rock blockade (Route 111), rivers and waterfalls with stairs beside them, narrow bridges and a maze of bridges (Route 119), a muddy slope (Route 119), sand pits and dunes (Route 111), a long bridge over a valley, ponds and long grass mazes (Route 120), ledges.

**Ledges and NapAttack's "no one-way ledges".** Pokémon's ledges are "one-way obstacles", "often used to provide shortcuts to return from a later area to an earlier one". Alternatives that keep the shortcut and stay two-way: a stair cut in the face (34 px or wider) that is hidden from the start of the route and obvious from the end; a ramp along the face at 1 in 3; a ladder; stepping stones (the Acro Bike's stones up a ledge in Hoenn); a gate or stile latched on the far side that opens once and stays open (Tunic's soft gates; the plan's "once open, open for good"); a ferry or lift.

**Side paths and dead ends.** Pokémon puts items on or near ledges so that players take a longer or more hidden route. NapAttack cannot reward, so a dead end must end in a view, a resident, a bench or a story detail; a dead end with nothing is a fault. Tunic: a passage you missed is reached later from the other end, and understood then.

**Route shape.** Pokémon: a corridor 10 to 25 tiles wide that zigzags round tree blocks and ponds inside a fixed-width map. Zelda: open rooms with exits on several sides and walls made of ridges, trees and banks. NapAttack's portrait screen suits the corridor along north-south with Zelda rooms as the pockets east and west.

## 5. Checklist for the v5.2 block-out (each item measurable)

**Density**

1. Each route screen (320 x 576) has 2 to 3 interactables and 3 to 5 story props; each settlement screen 6 to 10 of each.
2. No stretch of walked path longer than 200 px (5 s) without something to notice.
3. Every 1 to 2 screens of route has a landmark, visible from the screen before.
4. Each major biome has at least 3 named places plus 1 per 6 screens, at least 3 secret pockets (about 1 per 5 screens), 1 viewpoint, 1 camp or hut, 1 ruin or story site, 2 local wildlife kinds, 1 water feature.
5. No secret or decoration gives a reward, cost or chore.

**Boundaries** 6. Zero invisible walls: every blocking cell has a drawn physical reason. 7. Every outer border is at least 64 px deep in two or three strata. 8. No straight border line longer than 96 px without a jog of 8 px or more, a bulge, an outlier or a change of material; a straighter outer line is allowed only with a broken inner layer within 64 px (ALTTP). 9. No more than 3 identical props in a row; tree walls mix 3 or more species and sizes. 10. Every screen-length of border shows something beyond (a peak, a ridge, haze, an isle, a far rim). 11. Each region shows at least one visible-but-unreached place, and every promise of that kind is reachable later by a way or a loop.

**Transitions** 12. Every region change on a route has a mixing band of at least one screen height (576 px), a threshold object, and at least 3 elements crossing the line each way. 13. The next region's landmark is hidden until a crest, bend or threshold, then seen at least 1 screen before arrival. 14. Ambience and music cross-fade at the threshold over at least 3 s (120 px). 15. Each change has a source it radiates from (river, volcano, glacier, sea, city).

**Obstacles and paths** 16. The main path bends or meets an obstacle every 200 to 300 px; no straight run longer than 240 px. 17. Path width varies between 24 and 64 px; side paths at least 1 per 2 screens. 18. Each region has at least one loop; every area two ways in except deliberate pockets. 19. Every dead end longer than 80 px ends in a view, resident, bench or story detail. 20. No one-way drops: every shortcut is a two-way stair, ramp, ladder, stepping stones or a far-side latch that stays open. 21. Every tier change uses a stair (34 px or wider) or a ramp; obstacles leave touch targets of 44 screen px.

## 6. What to copy from whom

- **ALTTP:** layered cliff rims with 45 degree turns; walls made of ridges, trees and banks; almost everything reachable; one open corridor tying the biomes.
- **Link's Awakening:** a buffer screen between biomes; one landmark (the egg) visible above the whole map; a secret every few screens.
- **Minish Cap:** a dense town at the hub ringed by distinct regions (VGMaps map).
- **Pokémon Gen 3:** ragged tree walls 2 to 6 tiles deep; a route rhythm of items, residents and a landmark; weather and ash as transitions; the sandstorm as a desert border.
- **Sword/Shield Wild Area:** named subareas with their own weather; a visible island promised for later.
- **Stardew:** borders and gates as physical things being mended; few exits; secret woods behind a log.
- **Sea of Stars:** small pockets; "turn over a stone" density; hopping over fallen trees instead of being stopped by them.
- **Tunic:** firm, not hard, gates; the camera times the reveal; shortcuts understood from the far end.
- **Hyper Light Drifter:** each section with its own people, terrain and traces of culture; sound changes by place.
- **CrossCode:** about one find per room and a landmark every five.
- **Eastward:** towns "packed with unique and quirky characters" (Zhou).
- **Breath of the Wild (contrast):** triangles that hide and reveal.

**Not reached in this pass:** kemenaran's Link's Awakening overworld write-up and Bulbapedia's Route 104 (permission timed out); Stardew wiki's Cindersap Forest page; Bulbapedia's image archive (403); Zelda Wiki's Link's Awakening (Switch) page (fetch error); no official overworld maps for Eastward, Sea of Stars, Chained Echoes, CrossCode or Moonlighter; no credible source on Moonlighter's world design.

## Sources

- Game Developer, Overworld Overload, ALTTP Light World part 2: https://www.gamedeveloper.com/disciplines/overworld-overload-an-analysis-of-link-to-the-past-s-light-world-part-2
- TCRF, ALTTP maps: https://tcrf.net/Development:The_Legend_of_Zelda:_A_Link_to_the_Past/Maps
- VGMaps, ALTTP Light World: https://www.vgmaps.com/Atlas/SuperNES/LegendOfZelda-ALinkToThePast-LightWorld.png
- VGMaps, Link's Awakening DX Koholint: https://www.vgmaps.com/Atlas/GB-GBC/LegendOfZelda-Link'sAwakeningDX-Koholint.png
- VGMaps, GBA atlas (Minish Cap Hyrule, Emerald routes): https://www.vgmaps.com/Atlas/GBA/index.htm
- Set Side B, hidden structure of Link's Awakening's overworld: https://setsideb.com/?p=133
- Zelda Wiki (Fandom), Piece of Heart: https://zelda.fandom.com/wiki/Piece_of_Heart
- Zelda Wiki, Secret Seashell: https://zeldawiki.wiki/wiki/Secret_Seashell
- Bulbapedia, Hoenn Route 119: https://bulbapedia.bulbagarden.net/wiki/Hoenn_Route_119
- Bulbapedia, Hoenn Route 111: https://bulbapedia.bulbagarden.net/wiki/Hoenn_Route_111
- Bulbapedia, Hoenn Route 113: https://bulbapedia.bulbagarden.net/wiki/Hoenn_Route_113
- Bulbapedia, Ledge: https://bulbapedia.bulbagarden.net/wiki/Ledge
- Bulbapedia, Wild Area: https://bulbapedia.bulbagarden.net/wiki/Wild_Area
- Stardew Valley Wiki, The Mountain: https://wiki.stardewvalley.net/The_Mountain
- Stardew Valley Wiki, Secret Woods: https://wiki.stardewvalley.net/Secret_Woods
- Stardew Valley Wiki, Farm Maps: https://stardewvalleywiki.com/Farm_Maps
- MobileSyrup, Sea of Stars level design (Boulanger): https://mobilesyrup.com/2023/09/11/sea-of-stars-level-design-sabotage-studio-thierry-boulanger-interview/
- Nintendo Life, the influences of Sea of Stars: https://www.nintendolife.com/features/from-chrono-trigger-to-super-mario-rpg-the-varied-influences-of-sea-of-stars
- Game Developer, Tunic interview: https://www.gamedeveloper.com/design/designing-content-for-no-one-an-interview-with-the-team-behind-tunic
- Kill Screen, Hyper Light Drifter's wordless world: https://killscreen.com/building-wordless-world-hyper-light-drifter
- RPGFan, Matthias Linda on Chained Echoes: https://www.rpgfan.com/feature/interview-with-matthias-linda-on-chained-echoes/
- CrossCode Wiki, Autumn's Rise: https://crosscode.fandom.com/wiki/Autumn%27s_Rise
- Nintendo, making Eastward (Tommo Zhou): https://www.nintendo.com/us/whatsnew/how-the-developers-began-making-then-remaking-eastward
- Source Gaming, Breath of the Wild's triangles (CEDEC): https://sourcegaming.info/2017/11/25/holism-breath-of-the-wilds-golden-triangles/
- GameDev.net, map borders in an open world game (forum, low weight): https://gamedev.net/forums/topic/659628-map-borders-in-an-open-world-game
