# World atlas: the places beyond the valley

Matt, 17 Oct (20:22 and 20:23): more places ("cyber punk or steam punk, a desert/western town, lava themed, maybe out of space … a space station or another planet", "a castle or harbour like in the picture"), seamless transitions between places, and a world that feels alive. This file is the direction; the order of work is in `living-world-plan.md`. Everything here follows the world logic rules there and the art rules in `coherence-plan.md`.

## The idea that ties it together

NapAttack is about resting instead of scrolling, so the world is laid out as a journey from rest to screens and back to sleep. Near home everything is quiet, green and slow. The farther you travel, the more the places run on machines, glare and noise, until the neon city that never sleeps, home of Doomscroll Dave. Beyond it, the deepest rest: a quiet moon above the clouds. Every region has a resident who has lost their balance in that region's way, and a sparring ring where you meet them.

| Region                        | Feel                                                                                                                                                                                                                | What it stands for                        | How you reach it                                                       |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------- |
| **The Valley** (home)         | The garden, Crossroads Town, the Town Park, the Snowy Ridge, the Riverside, the Woodland                                                                                                                            | Rest, nature, slow days                   | On foot from the garden                                                |
| **Driftwood Harbour**         | The coast south of town: a fishing harbour with jetties, boats, nets, a fish market and a lighthouse that keeps the night dark for the sleepers                                                                     | The calm of a tide; the lighthouse keeper | On foot (south of town, where the Cove was planned)                    |
| **Hearthold Castle**          | A castle on the headland above the harbour: a courtyard with a well and banners, a great hall, a walled herb garden and a library tower. Its old ruler declared fixed hours for sleep; the bell still rings bedtime | Routine and keeping hours                 | On foot along the cliff path from the harbour, over a drawbridge       |
| **Cogsworth Junction**        | Steampunk: a railway town of brass, copper roofs, clock towers, pipes, steam vents and an airship mast. Everyone runs to the minute                                                                                 | Schedules and clockwork busyness          | The steam train from Crossroads Town station                           |
| **Dust Gulch**                | A western desert town: a saloon, a water tower, boardwalks, cacti, tumbleweed, a dry well, and the Desert Oasis (L8) outside town                                                                                   | Drought: a well run dry, like attention   | The train line west from Cogsworth                                     |
| **Ember Caldera**             | Lava fields under a volcano: obsidian paths, lava rivers crossed by stone bridges, forges, heat shimmer, a cooled crust where it is safe                                                                            | Burnout                                   | The old mine cart line from Dust Gulch's mine                          |
| **Neon Harbour**              | Cyberpunk: a rainy city at permanent dusk, neon signs, holo stalls, vending machines, a maglev, billboards that flicker. Doomscroll Dave's home turf                                                                | Screens and the night that never ends     | The maglev from Cogsworth (steam gives way to electric along the line) |
| **Halcyon Station and Lumen** | A space station in orbit with garden pods and a window onto the planet, then Lumen, a small quiet moon with glowing flora, slow light and low gravity                                                               | The deepest sleep, far above the noise    | The space elevator at the edge of Neon Harbour                         |

Later regions from the earlier list (tundra, sky islands, coral reef, glowshroom forest, dreamscape) fold into these where they fit: the glowshroom forest and dreamscape become Lumen's flora, the sky islands sit on the airship route from Cogsworth, the coral reef lies off Driftwood Harbour.

## World logic for the atlas

- Walking zones join only where the ground could really meet: the valley, the harbour and the castle are one walkable region.
- Distant regions are joined by a vehicle that belongs to both ends: a railway from town, the airship from Cogsworth, a mine cart into the caldera, the maglev into the city, the space elevator out of it. The station or dock is drawn in both zones.
- Each region keeps its own rules: sand and cacti only in Dust Gulch and the oasis, lava only in the caldera (it flows downhill and cools to crust at its edges), rain and neon in Neon Harbour, snow on the ridge.
- Day and night are shared everywhere, except that Neon Harbour never gets fully dark or fully bright, and Lumen's sky is always starry.

## Seamless travel

- **Within a region, no loading and no cut.** Zones sit on one grid. When the companion walks toward an edge, the neighbouring zone is already mounted beside the current one, and the camera follows across the border in one continuous scroll. Only the current zone and its neighbours are kept in memory.
- **Borders are painted together.** The generators draw each shared border from the same seed, so the road leaving the garden's south gate is the very road entering Crossroads Town, and the grass, treeline and fences run straight across. A check compares the border strips of neighbouring zones (paths line up, terrain matches or blends).
- **Between regions, the journey is the transition.** A two to four second vehicle scene: the train pulls out, the landscape scrolls past in parallax layers as it changes from meadow to brass, the train pulls in. It can be skipped, plays once, and with reduced motion it is a still frame and a short cross-fade.
- **Interrupting is always safe.** Turning back mid-walk or leaving the app mid-journey never triggers a stale arrival, a nap or a navigation (AGENTS.md).

## A world that feels alive

All of this is presentation: it never adds rewards, costs or chores, every effect is finite, stops when its screen is inactive, and shows a still frame with reduced motion.

- **Residents with routines (L6).** Each region has its people: Moss and the gardener in the valley, fishers and the lighthouse keeper at the harbour, the castle's steward, tinkerers in Cogsworth, a saloon keeper in Dust Gulch, forge workers in the caldera, street vendors in Neon Harbour, a station botanist on Halcyon. They walk short routes by time of day, greet the companion and say short lines that react to world health.
- **Animals that belong.** Butterflies, fireflies, birds and the frog in the valley; gulls and a harbour cat; ravens on the castle walls; clockwork birds in Cogsworth; lizards and a tumbleweed in Dust Gulch; ember moths in the caldera; neon moths and drones in the city; drifting spores on Lumen. Birds lift off when the companion walks close.
- **Things that move by themselves.** Smoke from chimneys, steam from vents, washing on lines, flags and banners, a windmill, boats bobbing in the harbour, water wheels, lanterns that flicker on at dusk, neon that buzzes on and off, lava that glows and crusts.
- **Weather and light per region (L4).** Rain in Neon Harbour, dust in Dust Gulch, sea mist in the harbour, snow on the ridge; warm windows at night everywhere.
- **The world remembers (L7).** Repaired things stay repaired, befriended residents stay, chosen variants stay.
- **Sound** (`sound.md`): an ambient bed per region (waves, wind, gears, the saloon piano, rain on neon), quiet by default.

## Battles and customisation per region

- **Battles:** each region has its sparring ring, its resident rival and its backdrop: a harbour jetty, the castle courtyard, a gear-floored arena, a dusty corral, a basalt ring by the lava, a neon rooftop, a zero-g dome. Gentle terrain effects (approved) are balanced by Codex first (C17); none makes raids harsher or costs GRASS.
- **Customisation:** keepsakes from each region become decor at home (a ship in a bottle, a castle banner, a brass clock, a cow skull, an obsidian lamp, a neon sign, a moon rock), and region outfits for the companion (a sailor cap, a crown of daisies, goggles, a cowboy hat, a heat visor, a raincoat with LEDs, a tiny space helmet). Which mission or visit grants which keepsake is a proposal for Matt.

## Open questions for Matt

- Should regions open by the existing level gates only, or by finishing a region's story first?
- Should Neon Harbour reflect your real phone use (brighter and louder after late-night phone use), as presentation only?
- Is Lumen the end of the journey, or should space lead on?
