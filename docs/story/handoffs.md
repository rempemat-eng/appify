# Hand-offs from the progression spine

Claude K, 21 Oct. Data for the other streams, drawn from [art/story/progression.json](../../art/story/progression.json) and [art/story/stories.json](../../art/story/stories.json); read those through [lib/progression.ts](../../lib/progression.ts) rather than copying numbers. Everything is a proposal until Matt answers [choices-for-matt.md](choices-for-matt.md); build behind a switch, change no rule before then.

## For Claude L (mechanics)

### The unlock table

| Way | Catalogue id   | In reach after | Story link (proposal) | Task                                    | Dust | Opens regions | Opens stops                                                                                                      |
| --- | -------------- | -------------- | --------------------- | --------------------------------------- | ---: | ------------- | ---------------------------------------------------------------------------------------------------------------- |
| W1  | `headland`     | start          | –                     | one rest of 10 min                      |   25 | –             | headland-tip                                                                                                     |
| W2  | `ridge-col`    | start          | –                     | 45 min of rest in all                   |   60 | frostline     | frostline                                                                                                        |
| W3  | `valley-train` | start          | –                     | one rest of 30 min                      |  120 | cogsworth     | cogsworth, cogsworth-north, cogsworth-west, cogsworth-east                                                       |
| W4  | `ferry`        | start          | –                     | an evening rest of 45 min               |  150 | isles         | lagoon-landing                                                                                                   |
| W5  | `desert-line`  | start          | brackens ch 2         | an hour of rest on 3 different days     |  250 | sunstone      | dust-gulch, palm-spring, the-lode                                                                                |
| W6  | `chasm-bridge` | W5             | sunstone ch 3         | 6 h of rest in all                      |  350 | fire          | hearthold, ember-forge, cinderwick                                                                               |
| W7  | `maglev`       | W3             | cogsworth ch 2        | an evening rest of 2 h                  |  450 | neon          | lull-east-bank, neon-market, neon-docks, neon-heights, neon-quay, gull-strand, beacon-isle, skyport, launch-cape |
| W8  | `elevator`     | W7             | neon ch 3             | an hour of rest on 7 different days     |  700 | halcyon       | –                                                                                                                |
| W9  | `shuttle`      | W8             | halcyon ch 3          | a long rest of 5 h, on 3 different days |  900 | lumen         | –                                                                                                                |

Rules (`rules` in the JSON): one way a calendar day; a paid way opens at the end of the next rest of 10 minutes or more; Dust refunded if the task wins; rests split at midnight; an evening rest starts 18:00 to midnight; a storyLink way comes in reach only once its story has reached that chapter.

### Chapters, folk and spots

- **Chapter rule:** chapter 1 with the first rest (any length) at any of the region's spots; chapters 2 and 3 each with one more rest there that ends on a later calendar day than the previous chapter, or is 90 minutes or more; one chapter per rest; at most one new chapter a day across all stories. Kept for ever; shown at the next welcome-back.
- **Folk:** one chosen starter at the first launch; the other two when the valley story ends (with Cairn); each apprentice when their story's chapter 3 arrives. Nothing costs Dust or needs a fight.
- **Rest spots:** found by walking past once (like keepsakes); then offered on the NAP sheet. Same Dust a minute everywhere (G2). Which spot a rest happens at decides only which story it moves.
- **Outings** (proposals): THE HIGH FELLS at the Col hut bench, 90 min, 180 Dust; THE SLOW BOAT at the narrowboat's cabin, 45 min, 90 Dust; A DAY ON THE ISLE at a hammock at Lagoon Landing, 120 min, 240 Dust; SIESTA at the palm shade at Palm Spring, 90 min, 180 Dust; A SOAK at the bathhouse at Cinder Springs, 60 min, 120 Dust; DOWN THE LULL CUT at Lullford's quay and mooring, 60 min, 120 Dust; AN EVENING OFF at a bench in the Heights gardens, 120 min, 240 Dust; STARGAZING at the lounge window seat, 120 min, 240 Dust.
- **The earning rule:** the spine's pacing assumes G10 (choices, item 5). `docs/story/pacing.md` regenerates with `npm run sim:progression` whenever `scripts/economy-inputs.ts` changes, and `npm run check` fails if it is stale.
- **Save shape, when it comes** (Codex's): found spots `string[]`; chapters `Record<storyId, { n: 1|2|3; at: number }[]>`; folk joined `Record<folkId, number>`; the last chapter's calendar day. All additive and optional, like `ways` in #95.

## For Claude M (interface)

| Moment                 | What the screen shows                                                                                                                       | Data                                      |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| The NAP sheet          | "rest at …": the found spots, the hut's bed first; one quiet line naming the story the rest would move ("the warden has news"), never a nag | `regions[].spots`, chapter state          |
| Welcome back           | At most one way and one chapter: the chapter's `beat` text, its title and the region; a joined folk as its own row                          | `stories[].chapters[].beat`, `join.joins` |
| The journal            | Each story's chapters so far, re-readable, with their lines as speech bubbles; a ribbon row for rivals                                      | `stories[]`                               |
| The circle of fourteen | The select screen: fourteen stones round a moon in `night` order, unmet folk dark with a hint at their home ("someone waits at the bothy")  | `folk[]`                                  |
| A way's card           | Name, the task in words (`taskWords`), a tally meter and a Dust meter; a story link reads as the resident's line, not a lock                | `ways[]`                                  |

Copy is lowercase in speech and uppercase only in labels; lines fit 90 characters. Touch targets 44 px; nothing hover-only.

## For the map lanes: each region's rest spots and story places

Each chapter's lasting change is presentation only and at most one small new prop or pose. Put the rest spots on open, reachable ground with a stand in front (they become NAP-sheet destinations), and keep them out of secret pockets.

### The home valley: Claude E, its plan file (not yet started)

- **Rest spots:** the hut's bed (night); the spring pool in the woodland; the millpond bench; the bandstand in the park (Park Patrol); the library (Book Club); the ridge cabin (Mountain Retreat) (night); Driftwood's harbour wall; the Headland's lookout tower.
- **Story:** the gardener, "the weeds will keep"; apprentice Cairn.
  - Chapter 1 at the hut's bed: no change yet.
  - Chapter 2 at the millpond bench: a kettle hangs on a hook in the shelter by the green, and neighbours gather there when it rains.
  - Chapter 3 at the bandstand in the park (Park Patrol): the gardener's trowel hangs on a hook in the shelter by the green, which is now a meeting place with a lantern; at dusk she sits there, not in the beds.
- **To draw:** a kettle on a hook in the shelter by the green; the gardener seated on the bandstand step, hat slipped (pose); the trowel on a hook and a lit lantern in the shelter; Cairn's empty place in the circle: a ring of pale grass.
- **Ring:** the green in Crossroads, rival Doomscroll Dave, as the tutor (unchanged).

### The Brackens: Claude F, `art/regions/brackens.json`

- **Rest spots:** the shepherd's hut step (night); the drove well; the bench below the Brackens gap.
- **Story:** the drover, "forty-two in the fold"; apprentice Tally.
  - Chapter 1 at the shepherd's hut step: no change yet.
  - Chapter 2 at the drove well: the drover's dog dozes in the shade of the drove well, belly up.
  - Chapter 3 at the bench below the Brackens gap: at dusk the sheepfold by the road holds the whole flock behind a shut gate, and the drover sits on the bench below the gap with his boots beside him.
- **To draw:** the drover's dog asleep belly-up by the drove well; the sheepfold with the flock inside and the gate shut; the drover seated on the bench below the gap, boots off beside him.

### The Lull plain, Lullford and Gullwick: Claude I, `art/regions/lull-delta.json` (PR #177)

- **Rest spots:** Lullford's quay and mooring; the willows by the oxbow; a boat hauled up at Gullwick (night). The Gullwick boat lives in `art/regions/gullwick.json` (#177).
- **Story:** the bargee, "the river runs downhill on its own"; apprentice Puddle.
  - Chapter 1 at Lullford's quay and mooring: no change yet.
  - Chapter 2 at the willows by the oxbow: clover grazes under the willows by the oxbow with the barge moored beside her, rope slack.
  - Chapter 3 at a boat hauled up at Gullwick: clover dozes in the meadow behind Lullford quay, her harness hung on the mooring post, and the barge drifts down with the tide.
- **To draw:** clover grazing under the oxbow willows, barge moored with a slack rope; clover at rest in the meadow behind Lullford quay; the harness hung over the mooring post.

### The Frostline: Claude F, `art/regions/frostline.json`

- **Rest spots:** the bothy's bunk (night); the Col hut bench; the tarn shore at Snowmelt Lake.
- **Story:** the hut warden, "the kettle is always on"; apprentice Tam.
  - Chapter 1 at the bothy's bunk: no change yet.
  - Chapter 2 at the Col hut bench: a second dented mug stays on the Col hut bench, upside down to keep the snow out.
  - Chapter 3 at the tarn shore at Snowmelt Lake: the warden sits on the bench by the bothy door at dusk with her mug, and a chair has been brought out beside the stove.
- **To draw:** a dented mug upside down on the Col hut bench; the warden seated on the tarn shore rock (one seated pose); the warden seated on the bench by the bothy door, mug in hand.
- **Ring:** a snowy clearing by the bothy, rival the hut warden.

### Cogsworth, the coal hills and the Narrows: Claude H, `art/regions/cogsworth.json` (PR #184)

- **Rest spots:** the allotments' bench, warm from the foundry; the narrowboat's cabin (night); the clock room.
- **Story:** the tinkerer, "a minute slow"; apprentice Pendle.
  - Chapter 1 at the allotments' bench, warm from the foundry: no change yet.
  - Chapter 2 at the narrowboat's cabin: the narrowboat's cabin clock stands open with its hands taken off and set on the shelf beside it.
  - Chapter 3 at the clock room: the tower's sunset chime rings a minute after the station clock's (sound only), and the tinkerer naps in a chair by the clock room window at dusk.
- **To draw:** the narrowboat's open cabin clock with its hands on a shelf; a chair by the clock room window with the tinkerer asleep in it (pose); the sunset chime a minute late (a sound cue for lane M, no art).
- **Ring:** the plaza, rival the tinkerer.

### The Tidebloom Isles: Claude C, its plan file (not yet started)

- **Rest spots:** a hammock at Lagoon Landing (night); the rain shelter at the headwaters; the black sand of the cove.
- **Story:** the naturalist, "an inch a year"; apprentice Tuff.
  - Chapter 1 at a hammock at Lagoon Landing: no change yet.
  - Chapter 2 at the rain shelter at the headwaters: the naturalist's notebook hangs open to dry on the rain shelter's rail, pages fanned.
  - Chapter 3 at the black sand of the cove: the naturalist lies on the black sand by a smooth dent where the boulder used to sit, notebook shut, pencil behind her ear.
- **To draw:** the naturalist's notebook fanned on the rain shelter rail; a smooth boulder-shaped dent in the cove's black sand; the naturalist lying on the sand, pencil behind her ear.

### The Sunstone basin: Claude D, its plan file (not yet started)

- **Rest spots:** the palm shade at Palm Spring; the caravan camp under the stars (night); the saloon's porch.
- **Story:** the oasis trader, "the creek remembers"; apprentice Mirra.
  - Chapter 1 at the palm shade at Palm Spring: no change yet.
  - Chapter 2 at the caravan camp under the stars: the trader's awning is rolled up at dusk, with a moon pictogram hung on its pole.
  - Chapter 3 at the saloon's porch: a thin creek runs again down the gulch's old dry bed past the saloon, and the trader sits on the porch at dusk with a glass of water.
- **To draw:** the trader's awning rolled up with a moon pictogram on its pole; water frames in the gulch's dry creek bed and a gap in the drift at the outlet; the trader seated on the saloon porch with a glass (pose).
- **Ring:** the dusty corral in Dust Gulch, rival the cowhand.

### The fire country: Claude D, its plan file (not yet started)

- **Rest spots:** the bathhouse at Cinder Springs (night); Hearthold's herb garden; Cinderwick's sand.
- **Story:** the smith, "banked at sunset"; apprentice Ashe.
  - Chapter 1 at the bathhouse at Cinder Springs: no change yet.
  - Chapter 2 at Hearthold's herb garden: after the bedtime bell, the Ember forge's door is pulled half shut and its glow dims for the night.
  - Chapter 3 at Cinderwick's sand: at sunset the Ember forge is banked: door shut, embers low, the hammer hung up, and the smith rests at Cinderwick or on the forge bench.
- **To draw:** the Ember forge with its door half shut and the glow dimmed; the forge banked: door shut, low ember glow, hammer on a hook; the smith asleep on Cinderwick's black sand.
- **Ring:** the basalt ring by the lava, rival the smith.

### Neon Harbour and the delta: Claude I, `art/regions/neon.json` (PR #177)

- **Rest spots:** a reed hide in the delta; the gallery behind the falls; a bench in the Heights gardens; the chapel on Chapel Islet (night).
- **Story:** Doomscroll Dave, "route complete"; apprentice Nix.
  - Chapter 1 at a reed hide in the delta: no change yet.
  - Chapter 2 at the gallery behind the falls: one billboard in the market now shows a slow moon glyph after midnight instead of an advert.
  - Chapter 3 at a bench in the Heights gardens: Dave sleeps on the bench in the Heights gardens for good, under the blanket, phone face down beside him.
- **To draw:** one market billboard frame showing a moon glyph; Dave lying on the Heights garden bench under a blanket; a phone face down beside the bench.
- **Ring:** the Neon court, rival Doomscroll Dave.

### Halcyon Station: Claude D, its plan file (not yet started)

- **Rest spots:** the sleep bay (night); the galley; the lounge window seat.
- **Story:** the sleep-bay keeper, "everyone else's pillows"; apprentice Bunk.
  - Chapter 1 at the sleep bay: no change yet.
  - Chapter 2 at the galley: a second magnetic mug stays clipped to the galley's round table, with the keeper's name on it.
  - Chapter 3 at the lounge window seat: the keeper sleeps in a sleeping bag strapped by the lounge window seat, and the sleep bay lamps stay dimmed.
- **To draw:** a second magnetic mug clipped to the galley table; a sleeping bag strapped by the lounge window seat with the keeper in it.
- **Ring:** the padded ring, rival the station botanist.

### Lumen: Claude D, its plan file (not yet started)

- **Rest spots:** the habitat bunk (night); the dream pools; the hammock under the moon tree (night).
- **Story:** the stargazer, "the gap in the chart"; apprentice Mote.
  - Chapter 1 at the habitat bunk: no change yet.
  - Chapter 2 at the dream pools: the stargazer's chart is pinned up in the habitat with a tiny nightcap drawn in the gap.
  - Chapter 3 at the hammock under the moon tree: the stargazer sleeps in the hammock under the moon tree with her chart rolled up beside it, and the last crystal spire round the Dream Grove glows.
- **To draw:** the star chart pinned up in the habitat with a nightcap doodle in its gap; the stargazer asleep in the hammock, chart rolled beside it; the fourteenth crystal spire lit.
- **Ring:** the sparring crater, rival the stargazer.
