# The progression spine: what opens when, from the first launch to the moon

Claude K (the story and progression stream), 21 Oct. **A proposal:** nothing here is in the game or changes a rule until Matt decides ([choices-for-matt.md](choices-for-matt.md)). The data is [art/story/progression.json](../../art/story/progression.json) and [art/story/stories.json](../../art/story/stories.json), typed by [lib/progression.ts](../../lib/progression.ts) and checked by `npm run check:progression` (the spine against Claude G's route graph, the ways catalogue and the cast, the stories against Matt's rules, and the pacing page against the economy sim). Real minutes and Dream Dust throughout.

It gathers what is already decided or proposed (Matt's decisions on #95, the world plan v5.3, `cast.md`, #143 and #146) into one ordered spine, adds the resident stories, and checks the pace with the C33 economy sim's three resters ([pacing.md](pacing.md)).

## The spine in one picture

```
first launch: hatch a Grassling, choose Bramble, Puffcap or Velvet (stones 1 to 3)
  |  first rest (10 min): the first visitor, the Headland stile (W1), the gardener's chapter 1
  v
open from the start: the home valley, the Brackens, the Lull plain with Lullford and Gullwick
  |  one way a day at most, each by a rest task or by Dream Dust
  |-- W2 the ridge col ---------------> the Frostline        (the hut warden -> Tam)
  |-- W3 the Millrace landslip -------> Cogsworth            (the tinkerer -> Pendle)
  |-- W4 the Shell Bar and ferry -----> the Tidebloom Isles  (the naturalist -> Tuff)
  |-- W5 the Rift [Brackens ch 2] ----> the Sunstone basin   (the oasis trader -> Mirra)
  |     '-- W6 the chasm bridge [Sunstone ch 3] -> the fire country (the smith -> Ashe)
  '-- W7 Lullford's span [Cogsworth ch 2] -> Neon Harbour    (Dave -> Nix)
        '-- W8 the rocket [Neon ch 3] ----> Halcyon Station  (the sleep-bay keeper -> Bunk)
              '-- W9 the lander [Halcyon ch 3] -> Lumen      (the stargazer -> Mote: the moon is full)
the valley, the Brackens and the Lull have their own stories from day one:
  the gardener -> Cairn, the drover -> Tally, the bargee -> Puddle
```

Square brackets are the proposed **story links**: the way comes in reach only once that story reaches that chapter, so each region's story opens the road onward (choices, item 2). Everything else on the road is #95 as Matt approved it in principle, re-sited on the v5.3 map.

## The rules it runs on

**Ways** (decided by Matt on 20 Oct unless marked): a way opens by its rest task or by Dream Dust chipped in; Dust chipped in comes back if the task wins; at most one way opens a calendar day; a paid way opens at the end of the next rest of 10 minutes or more (open, #95 question 3); rests are split at midnight; an evening rest starts between 18:00 and midnight (open, #95 question 7). Lines and areas make the road; shortcuts and comforts are Dust only and never stand between the player and a place.

**Rest spots** (#143 G1, a proposal this spine depends on): each region has three or four, found by walking past once. From then on the NAP sheet offers them as where the next rest happens and the companion goes there while the player is away; nobody walks back. Every spot pays the same Dust a minute.

**Chapters** (proposed here): chapter 1 with the first rest at any of the region's spots; chapters 2 and 3 each with one more rest there that ends on a later day than the previous chapter or is a long rest (90 minutes, a night counts); one chapter per rest; at most one new chapter a day in all. Nothing waits on a date, nothing expires, nothing is lost. Chapter 3 leaves a lasting change in the world and the apprentice joins at once.

**Why one chapter a day.** Without it the sim's Regular rester reads all eleven stories in three weeks, a new region every day and each story over in three days; with it, every welcome-back carries at most one story beat and the journey lasts five to six weeks for a daily rester however much they rest (the heavy rester is no faster than the regular one, which is the point: rest more and nothing races ahead). It matches the decided "one way a day" and costs nobody anything.

## The first launch, in order

| Step                          | What happens                                                                                                                                                                                   | Companion                                                                                   |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Hatch                         | Hatch a Grassling (it keeps the type) and choose one of three valley folk; their stone in the circle lights                                                                                    | "hello. i'm small, but i'm very good at naps."                                              |
| First walk                    | The garden and the hut; the hut's bed is the first rest spot, and the valley's spots are found by walking past them                                                                            | "the bed's ours. want to see the village?"                                                  |
| First rest (10 min suggested) | The first visitor (guaranteed, as today), W1's task met so the Headland stile is mended, the gardener's chapter 1                                                                              | "while you were away, the shepherd mended the stile. and that stone moved. i'm sure of it." |
| The first week                | One way a day at most: the Frostline and Cogsworth usually on days 2 and 3; the Brackens and the Lull stories run alongside; Cairn, the first apprentice, joins on day 3 for all three resters | "the high path is clear. no rush. it'll still be there."                                    |

Day one is generous on purpose: three regions, about fifteen rest spots, four stories to begin and the first apprentice within days.

## The ways on the v5.3 map

| Way | What and where                                                                | Task (or Dust)                                | Opens                                                 | Story link (proposal) |
| --- | ----------------------------------------------------------------------------- | --------------------------------------------- | ----------------------------------------------------- | --------------------- |
| W1  | the Headland stile (threshold `headland-stile`)                               | one rest of 10 min (25)                       | the Headland tip                                      | none                  |
| W2  | the ridge col at the Frostline lip (`frostline-lip`)                          | 45 min of rest in all (60)                    | the Frostline                                         | none                  |
| W3  | the Millrace landslip (`millrace-cutting`); the valley train runs with it     | one rest of 30 min (120)                      | Cogsworth, its three gates, the Narrows               | none                  |
| W4  | the Shell Bar and the Driftwood ferry (`shell-bar`)                           | an evening rest of 45 min (150)               | the Tidebloom Isles                                   | none                  |
| W5  | the Rift: Drover's bridge, the Rift ferry, the desert line (`drovers-bridge`) | an hour of rest on 3 different days (250)     | Palm Spring, Dust Gulch, the Lode                     | the Brackens, ch 2    |
| W6  | the chasm bridge and the crust causeway (`chasm-bridge`); after W5            | 6 h of rest in all (350)                      | Hearthold, the Ember forge, Cinderwick                | Sunstone, ch 3        |
| W7  | Lullford's swing span (`lullford-bridge`); the maglev runs with it; after W3  | an evening rest of 2 h (450)                  | the delta, Neon Harbour, the Skyport, the Launch Cape | Cogsworth, ch 2       |
| W8  | the rocket at the Launch Cape; after W7                                       | an hour of rest on 7 different days (700)     | Halcyon Station                                       | Neon, ch 3            |
| W9  | Halcyon's lander; after W8                                                    | a long rest of 5 h, on 3 different days (900) | Lumen                                                 | Halcyon, ch 3         |

The stops each way adds match Claude G's `routeGates` in `lib/world-routes.ts` exactly (checked). Why each link: the drover tells how the spring flood took Drover's bridge's deck and the ferry's rope; with the creek running again the masons of Dust Gulch stop hauling water and mend the chasm bridge; once the tinkerer stops re-timing every pour, the foundry casts the gear Lullford's span has waited for; the night Dave sleeps the city dims and the Cape's crew fuels the rocket; with the keeper resting, the botanist readies the lander.

**For Claude A (`lib/world-ways.ts`):** the catalogue still uses pre-v5 names and sites for four ways: W3 `valley-train` (now the Millrace landslip, the train opening with it), W5 `desert-line` (now the Rift; the desert line runs from the valley halt, and it no longer needs W3), W8 `elevator` (now the rocket at the Launch Cape) and W9 `shuttle` (now Halcyon's lander). The spine keeps the catalogue ids as `catalogueId` so nothing breaks; renaming them is a catalogue change for its owner.

## Regions, rest spots and stories

| Region (opens)                       | Rest spots                                                                                                                                           | Resident, story, apprentice                              | Ring rival                      | Region plan                      |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ------------------------------- | -------------------------------- |
| the home valley (start)              | the hut's bed (default), the spring pool, the millpond bench, the bandstand, the library, the ridge cabin, the harbour wall, the Headland tower (W1) | the gardener, "the weeds will keep", Cairn               | Dave, as the tutor on the green | Claude E                         |
| the Brackens (start)                 | the shepherd's hut step, the drove well, the bench below the gap                                                                                     | the drover, "forty-two in the fold", Tally               | none                            | `art/regions/brackens.json` (F)  |
| the Lull, Lullford, Gullwick (start) | Lullford's quay, the willows by the oxbow, a boat at Gullwick                                                                                        | the bargee, "the river runs downhill on its own", Puddle | none                            | `lull-delta.json` (I, #177)      |
| the Frostline (W2)                   | the bothy's bunk, the Col hut bench, the tarn shore                                                                                                  | the hut warden, "the kettle is always on", Tam           | the hut warden                  | `art/regions/frostline.json` (F) |
| Cogsworth (W3)                       | the allotments' bench, the narrowboat's cabin, the clock room                                                                                        | the tinkerer, "a minute slow", Pendle                    | the tinkerer, on the plaza      | `cogsworth.json` (H, #184)       |
| the Tidebloom Isles (W4)             | a hammock at Lagoon Landing, the rain shelter, the black sand                                                                                        | the naturalist, "an inch a year", Tuff                   | none (the quiet place)          | Claude C                         |
| the Sunstone basin (W5)              | the palm shade, the caravan camp, the saloon's porch                                                                                                 | the oasis trader, "the creek remembers", Mirra           | the cowhand, in the corral      | Claude D                         |
| the fire country (W6)                | the bathhouse, Hearthold's herb garden, Cinderwick's sand                                                                                            | the smith, "banked at sunset", Ashe                      | the smith, by the lava          | Claude D                         |
| Neon Harbour (W7)                    | a reed hide, the gallery behind the falls, a bench in the Heights gardens, the chapel                                                                | Doomscroll Dave, "route complete", Nix                   | Dave, at the Neon court         | `neon.json` (I, #177)            |
| Halcyon Station (W8)                 | the sleep bay, the galley, the lounge window seat                                                                                                    | the sleep-bay keeper, "everyone else's pillows", Bunk    | the station botanist            | Claude D                         |
| Lumen (W9)                           | the habitat bunk, the dream pools, the hammock under the moon tree                                                                                   | the stargazer, "the gap in the chart", Mote              | the stargazer, in the crater    | Claude D                         |

The stories themselves, how they were drafted and graded, and what each leaves changed in the world: [stories.md](stories.md). Stories never need a ring win; a rival's invitation is optional.

## The fourteen folk

Night 1 to 3 the starters (Bramble, Puffcap, Velvet). The first pick sticks; `cast.md` says the other two join later through the stone circle, and the spine proposes when: as Cairn wakes at the end of the gardener's story, the circle calls them both (usually day 3; choices, item 4); then Tally (4), Tam (5), Puddle (6), Cairn (7, the half moon), Pendle (8), Mirra (9), Ashe (10), Tuff (11), Nix (12), Bunk (13) and Mote (14, the full moon). The number is a label, never a gate: each joins when their story ends, in whatever order the player rests.

## Outings, the home and comforts

- **Outings:** the three valley outings stay as they are; one per region (#143 G3) at its own rest spot, never above 2 Dust a minute or 240 an outing. Lullford's barge outing waits for W7.
- **The home** (#146, in its Dust-only form): the hearth's six levels and the house's four tiers as nine steps, each paid in Dust when queued and finished by that many minutes of rest. #146's ten materials are left out (choices, item 9).
- **Comforts and shortcuts** (#95 S1 to S4 and #143 G9): nineteen, 40 to 150 Dust, each after its region's way; the airship from Cogsworth's mast also waits for the warden's story. They never gate a place or a rest spot.

## Pacing, in short

From [pacing.md](pacing.md) (G10 earning, story links on):

| Rester (economy sim)                     | Rest a week      | Cogsworth | Neon Harbour | Lumen        | Folk at day 30 | Moon full    |
| ---------------------------------------- | ---------------- | --------- | ------------ | ------------ | -------------- | ------------ |
| Light (chips spare Dust into ways)       | 6 rests, 3.5 h   | day 3     | day 24       | day 56       | 11             | day 59       |
| Regular (typical; nights 3 times a week) | 17 rests, 32.8 h | day 3     | day 16       | day 32 to 39 | 12 to 13       | day 35 to 42 |
| Committed (heavy)                        | 19 rests, 52.3 h | day 3     | day 16       | day 37 to 38 | 12             | day 40 to 41 |

- **Everyone gets a generous first week:** five folk by day 7 and three or four regions.
- **More rest does not race ahead:** the heavy rester finishes no sooner than the regular one, because one way and one chapter a day set the pace once rests are plentiful.
- **The light rester is not left behind:** without evening rests the Isles, Neon and space open by Dust, and the whole journey ends in about two months. If they spend their Dust on the home instead, they keep ten folk and five regions by day 90 and can turn to the ways at any time; nothing is lost by waiting.
- **G10 against L2:** under L2 (every night minute at Rest 2x) the regular rester earns 96,395 Dust in 26 weeks and the heavy one 184,760, against 26,195 and 57,519 under G10, and Dust stops meaning anything; G10 keeps the road's prices meaningful (choices, item 5).
- The home base takes the regular rester about six weeks and the light one about eleven, in parallel with the road.

## Hand-offs

Unlock tables and story beats go to the lanes as data, not prose ([handoffs.md](handoffs.md)): to Claude L (mechanics: ways, chapters, spots, outings, the earning rule), to Claude M (interface: the NAP sheet's spot picker, the welcome-back beat, the journal, the circle of fourteen stones) and to the map lanes (each region's rest spots, chapter places and world changes, by region plan file).
