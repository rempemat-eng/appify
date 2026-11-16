# Gameplay by region: why each place is worth visiting, and coming back to

Matt, 20 Oct 20:54: "also start to think how the game play fits into all of these areas well (incentive structures and so on)".

**Status: a proposal. Nothing here is built, and nothing changes a rule until Matt says yes.** Every item that adds a mechanic or changes an existing rule is marked **PROPOSAL** and carries an id (G1 to G17, section 4) so the decisions in section 9 can point at it. Decorative interactions stay free of rewards, costs and chores (AGENTS.md). It respects the decisions already taken: at most one way opens a day, rests run in real time when ways ship, C9 comes first (`world-unlocks.md`, PR #95), the world plan v5.3 and its region briefs (PR #96), and no new social feature without Matt's go-ahead. Numbers are **real minutes** (the game still runs at demo speed, one second for a minute: `lib/offline-rules.ts`). AGENTS.md still holds: content and mechanics come after the art, motion and HUD pass, so section 8 orders this work behind it.

It builds on, and does not repeat: `living-world-plan.md` (L2 currency and care, L3 world health, L6 people, L7 world memory), `world-unlocks.md` (#95) and the ways catalogue `lib/world-ways.ts` (#118), `world-plan.md` and `regions/*.md` (#96), `world-atlas.md`, `../companion-roadmap.md`, and Codex's `gameplay-logic.md` (draft #23: "more landscape does not require more currencies, chores or reward loops").

## 0. In short

1. **Rest stays the only engine.** Everything a region gives comes back from time away. Walking, chatting and sparring are how you find things and enjoy them, never how you farm them.
2. **Same rest, different returns.** No region pays more GRASS a minute. Regions differ in _what_ comes back: a postcard of the place, a visitor who lives there, a small find, the next chapter of a resident's story.
3. **Walk to find, rest to receive.** Walking somewhere once finds its keepsake (as today) and its rest spots. After that the companion can be sent to any found spot from the NAP sheet or the map; the player never has to walk there again (G1).
4. **Each region has one of each:** rest spots and one outing, one native visitor, three finds, one resident with a three-chapter story that changes the world for good, an outfit at its shop, a few comforts to fund, and (where the atlas puts one) a ring with a rival and a ribbon.
5. **Each region pairs with a kind of rest**, as the ways already do: the Frostline with walks, Cogsworth with focus, the isles with lying down, Neon with an evening off, the fire country with recovery, space with nights.
6. **Ways pace it.** A region's content comes online when its way opens (one a day at most). Day one is generous: in v5.3 the valley, the Brackens, the Lull plain, Lullford and Gullwick are open from the start.
7. **One currency, GRASS, with a long tail of sinks.** Comforts in the world itself (Animal Crossing's public works) give GRASS a lasting use. A night's sleep pays a flat well-rested gift rather than per minute, and rest pays in full up to a daily ceiling (G10), so long sleep is acknowledged, not farmed.
8. **No chores, no FOMO, no guilt, no paywall, no grind.** Nothing expires, nothing is seasonal-only, nothing is lost. Two small FOMO edges in today's game get softened (G14).
9. **Twelve decisions for Matt** (section 9; also `decisions.json` for the answer page).

## 1. What the game is today

Main at `9034b03` (20 Oct), plus the drafts that shape it.

### 1.1 The loop on main

1. **Hatch** a companion (`hatch`, `lib/game.ts:1176`): 20 GRASS, level 1, the starter deck, mood 80.
2. **Rest.** START a nap (`mode: 'screen_off'`, untimed) or an outing (`mode: 'mission'`, timed) from the NAP sheet or at the outing's place in the valley (`sleep`, `lib/game.ts:1541`). An optional break idea (read, rest, move, create) is recorded (`lib/companion-memories.ts`).
3. **While away,** `tick()` (`lib/game.ts:1231`) settles: 1 GRASS a minute on a nap (none during an outing, which pays at the end), mood +1 a minute, one common card per 15 minutes (`offlineCards`, `lib/cards.ts:173`), the day's record (`recordOffline`, `lib/offline-rules.ts:85`).
4. **Come back** (`wake`, `lib/game.ts:1571`): the welcome-back sheet shows minutes, GRASS, cards, a postcard (outings), a hat (Mountain Retreat), a visitor met. An outing ended early forfeits its reward but keeps every minute.
5. **Awake,** the companion is "exposed" after a 30-second care window (`status`, `lib/game.ts:121`); a friend's raid can land. Mood falls 1 per 3 seconds in the app (`lib/game.ts:1381`). In-app play is limited to 3 minutes in each 30 (`PLAY_LIMIT_MS`, `lib/offline-rules.ts:1`): after that, feeding, levelling, hats and battles pause; walking does not. A rest of 10 minutes or more resets it.

### 1.2 GRASS: sources and sinks

| Source                     | Amount                                                                                    | Where                                                        |
| -------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| A nap                      | 1 a minute                                                                                | `tick()`, `lib/game.ts:1269`                                 |
| An outing completed        | Park Patrol 20 (15 min), Book Club 60 (30 min), Mountain Retreat 150 + a hat (60 min, L2) | `missions`, `lib/game.ts:116`                                |
| A raid won / defended      | 30 % of the rival's GRASS, at least 10 / 20; three raids a day                            | `raidGrass` `lib/game.ts:1875`, `applyIncoming`, `:1706`     |
| A practice spar won        | 5, for the first three wins a day                                                         | `sparringReward`, `lib/offline-rules.ts:128`                 |
| A touch-grass-together nap | half the session's GRASS again                                                            | `resolveTogetherSession`, `lib/game.ts:587`                  |
| **Sink**                   |                                                                                           |                                                              |
| Feeding                    | 5 (+20 mood)                                                                              | `feed`, `lib/game.ts:1665`                                   |
| Levelling                  | 50 x level (L2 4-card hand, L3 Digital Sunset, then HP and damage)                        | `levelUp` `lib/game.ts:1672`, `levelPreview` `grasslings.ts` |
| Hats                       | 30, 40, 60, 150 (four in all)                                                             | `hats`, `lib/game.ts:110`                                    |
| A raid lost                | -10 attacking, -30 % defending (C9, draft #18, removes this)                              | `finishBattle`, `applyIncoming`                              |

There are four sinks, and three of them run out (hats after 280, levels slowly). GRASS has little to do once a player has their hats.

### 1.3 Collections and progression

| Thing                  | Today                                                                                                                                                                  | Where                                                   |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Visitors to befriend   | 9 (REST, ROAM, FOCUS x common, uncommon, rare); the first is guaranteed on a 10-minute rest; then 40 % on 15 min, 80 % on 60 min, rares on 2 h or 3 calm days in a row | `lib/visitors.ts:96`, `:108`                            |
| Companions             | the starter or any befriended visitor; personality adds no stats                                                                                                       | `lib/companion-profiles.ts`                             |
| Habit cards            | 9 cards, deck of up to 20 (the weakest is replaced)                                                                                                                    | `lib/cards.ts`                                          |
| Postcards              | one per completed outing (park, book, mountain)                                                                                                                        | `postcardsOf`, `lib/visitors.ts`                        |
| Keepsakes              | 17: three the hut's own, one for each place walked; placed free in the hut or garden                                                                                   | `keepsakes`, `lib/decor.ts:64`                          |
| Memories               | self-reported, from a break idea; no rewards                                                                                                                           | `lib/companion-memories.ts`                             |
| Garden growth          | six beds and three orchard trees grow with lifetime rest (full at about 18 h)                                                                                          | `lib/garden-growth.ts`                                  |
| The day and its streak | a 120-minute daily goal; one missed day a week forgiven; days in a row widen the visitor pool                                                                          | `dailyProgress`, `gardenStreak`, `lib/offline-rules.ts` |
| The map                | walked zones inked in, the rest under fog; no reward                                                                                                                   | `lib/world-map.ts`                                      |

### 1.4 The world on main

Walking is free everywhere and grants nothing but a keepsake the first time (`walkWorld`, `lib/game.ts:943`; `moveTo`, `lib/world-save.ts:76`). Every journey line runs (`travelLinks`, `lib/world-places.ts:90`). Thirty-two residents walk two-point routes and say one fixed line each (`lib/resident-routes.ts`); they grant nothing. Four regional rings (Cogsworth, Neon, the caldera, Lumen) open the same practice spar against Doomscroll Dave in front of that region (`rings`, `lib/world-places.ts:77`). The three outings start only in the valley (`missionPlaces`). The only gate is Mountain Retreat's level 2. `lib/daily-rhythm.ts` holds Rest and Focus windows but "never reads device activity or awards game rewards".

### 1.5 Decided or drafted, not on main

| What                                | State                                                                                                                                                                                                                                                                                  | Where                                        |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| C9 safe currency                    | approved; first slice drafted (raids never take GRASS)                                                                                                                                                                                                                                 | #18, `docs/codex/economy-currency-safety.md` |
| L2 earning and care                 | approved: Rest 2x, Focus 1.5x, a daily well-kept gift, raids leave the companion worn out until nursed with medicine bought with GRASS; values not set                                                                                                                                 | `living-world-plan.md`                       |
| L3 world health                     | approved: capped, reversible, visual decay from play beyond the allowance or in protected hours; repairs cost GRASS                                                                                                                                                                    | `living-world-plan.md`, C8                   |
| Ways                                | approved in principle: nine ways opened by a rest task or GRASS, one a day, GRASS refunded if the task wins, shortcuts and comforts GRASS only                                                                                                                                         | #95, catalogue #118                          |
| World plan v5.3                     | the continent, its routes, thresholds, pockets, egg spots; the ways re-sited (W3 the Millrace landslip, W4 the Shell Bar and ferry, W5 the Rift, W7 Lullford's swing span, W8 the rocket, W9 the lander)                                                                               | #96, `regions/*.md`                          |
| L6 people, C11, C21                 | approved: residents with routines by time of day, a travelling merchant with rotating stock, lines that react to world health; ambient life finite and still with reduced motion                                                                                                       | `living-world-plan.md`, #21                  |
| L7 world memory, C13                | approved: lasting story changes, chosen variants, replay; nothing decays with absence                                                                                                                                                                                                  | `living-world-plan.md`                       |
| Terrain in battle, C17              | approved: one gentle condition per field, simulated first, never harsher raids or GRASS costs                                                                                                                                                                                          | `living-world-plan.md`                       |
| Matt's World Logic answers (20 Oct) | the woodland stone circle "could have a mechanic (something magic related perhaps)"; the caldera ember shrine "needs ... some functionality"; Cogsworth spars on the plaza; Halcyon gets a padded ring; the saddle windsock serves an airship route; the mast is scenery but reachable | the answer page's `answers` collection       |

### 1.6 What this means

The regions are beautiful and logical, but they have almost no gameplay role. A player walks to Cogsworth once for its keepsake and has no reason to return; the rings all spar the same Dave; every outing starts in the valley; residents never change; GRASS runs out of uses. Ways (#95) will give a reason to _open_ each region. Nothing yet gives a reason to _come back_. That is the gap this proposal fills, without adding a second currency or anything to do every day.

## 2. What other games teach

| Game                      | What it does (sourced)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | What NapAttack takes                                                                                                                                                                         |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Stardew Valley**        | "Most crops, Foraging items, and fish are available only during their particular season or seasons", and villagers' routines change with the season ([Season](https://stardewvalleywiki.com:443/Season)). Fish depend on "the time of day, the weather, and what the current season is" and the water ([GamesRadar](https://www.gamesradar.com/stardew-valley-fish)). The Traveling Cart comes on Fridays and Sundays and its "stock changes each day" ([Traveling Cart](https://stardewvalleywiki.com/Traveling_Cart)). Community Center rooms repair the quarry bridge, the greenhouse, the minecarts and the bus; Joja does the same for money ([Vault](https://www.stardewvalleywiki.com/Vault)).                                                                                                           | Each place returns its own things; residents keep routines; repairs open the world with two routes (already #95). Not taken: seasonal-only items and calendar-day stock (FOMO).              |
| **Animal Crossing**       | Its developers wanted people to "play a little every day" and "even if it's only for 15 minutes" ([Iwata Asks, City Folk](https://iwataasks.nintendo.com/interviews/wii/accf/0/4)); time runs in sync with the real world and shops keep hours ([Iwata Asks, New Leaf](https://iwataasks.nintendo.com/interviews/3ds/animalcrossing-newleaf/0/1)). Mystery tours take a ticket to "a random deserted island" with materials, rare creatures and villagers to invite ([Nookipedia](https://www.nookipedia.com/wiki/Mystery_Island)). The museum collects and displays bugs, fish, fossils and art ([Nookipedia](https://nookipedia.com/wiki/Museum)). Bridges and inclines are built to the player's order ([iMore](https://imore.com/animal-crossing-new-horizons-how-make-new-bridges-and-inclines), via #95). | Short sessions; a collection you can see; a trip with a surprise in it; the player funds improvements to the world itself (comforts, G9). Not taken: the daily expectation.                  |
| **Pokémon**               | Badges are proof of beating a Gym Leader, needed for the League, and in most generations needed to use HMs in the overworld ([Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/badge)). Some species appear only or mostly at night ([Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Nocturnal_Pok%C3%A9mon)). In Pokémon Sleep, research areas open by registered sleep styles (Cyan Beach at 20, up to Amber Canyon at 450), and each favours types ("Many Water-type Pokémon live here") ([Serebii](https://serebii.net/pokemonsleep/researchareas.shtml)).                                                                                                                                                                                                                                          | Creatures that belong to a place (native visitors, G4); a ring per region with its own rival (G7); progress that only counts up from sleep. Not taken: badges as gates (ways do that).       |
| **Link's Awakening**      | Secret Seashells hide "underneath Grass and Rocks, underwater, or inside Treasure Chests"; 20 earn the Koholint Sword ([Zelda Wiki](https://zeldawiki.wiki/wiki/Secret_Seashell)). The trading sequence passes an item through "many characters around Koholint Island" to a final reward ([Zelda Dungeon](https://www.zeldadungeon.net/wiki/Trading_Quest)).                                                                                                                                                                                                                                                                                                                                                                                                                                                   | A story that travels between regions through their residents (the drover, Cogsworth's gear for Lullford). Not taken: rewards for secrets (world plan decision 25 keeps pockets reward-free). |
| **Eastward**              | Built round "travelling east along a railway", with "sprawling beautiful towns to discover" and "a world packed with unique and quirky characters" ([Nintendo](https://nintendo.com/us/whatsnew/how-the-developers-began-making-then-remaking-eastward)); towns hold their own pastimes (the Earth Born game, cooking, gashapon figures) and "hidden places" ([RPG Site](https://rpgsite.net/review/11744-eastward-review)).                                                                                                                                                                                                                                                                                                                                                                                    | Each town its own pastime (a landmark activity), its own people and a reason to stop on the line.                                                                                            |
| **Spiritfarer**           | The player gathers on islands to build for the spirits aboard; "you build them for others" (Nicolas Guérin, [Pocket Tactics](https://www.pockettactics.com/spiritfarer/interview)); the game "revolves around a series of quests given to Stella by the spirits" and ends in their farewell ([Wikipedia](https://en.wikipedia.org/wiki/Spiritfarer)).                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Residents' stories advanced by kindness, not chores (G6); finds given to the people who need them (G5).                                                                                      |
| **A Short Hike**          | "every path you haven't explored yet provides the promise of something new to discover"; "learning the layout of an area is kind of rewarding on its own"; the shovel and bucket are "simple things to do that reward exploration" ([Game Developer](https://www.gamedeveloper.com/disciplines/road-to-the-igf-adam-robinson-yu-s-i-a-short-hike-i-)). Golden Feathers are found, given by characters or bought, and seven reach the summit ([Wikipedia](https://en.wikipedia.org/wiki/A_Short_Hike)).                                                                                                                                                                                                                                                                                                                      | Landmarks and small delights are their own reward; one goal reachable by several routes (#95's "either route").                                                                              |
| **Finch**                 | Self-care goals give the bird strength "to adventure out of the house", and an adult bird reaches the Travel Agency to "venture beyond the forest" ([Paste](https://www.pastemagazine.com/article/finch-app-mental-health-virtual-pet-self-care)). It also rewards login streaks and "encourages users to log on every day", which can cause stress ([Internet Matters](https://www.internetmatters.org/advice/apps-and-platforms/wellbeing/finch/)).                                                                                                                                                                                                                                                                                                                                                           | The companion goes somewhere because you looked after yourself. Not taken: streak rewards and daily logins.                                                                                  |
| **Forest, Pikmin Bloom**  | Forest's tree "dies if you switch apps mid-session" ([Forest](https://forestapp.cc/llms.txt); [Wikipedia](<https://en.wikipedia.org/wiki/Forest_(application)>)). In Pikmin Bloom "the more you walk, the more your Pikmin squad will grow", and they bring "postcards of the places you visited" ([Niantic](https://indigo-pearl.prezly.com/niantic-and-nintendo-launch-pikmin-bloom-an-app-that-brings-a-little-joy-to-your-everyday-journeys-on-foot-p3jm6x)).                                                                                                                                                                                                                                                                                                                                               | Postcards of where the companion went. Not taken: loss when you look at the phone (NapAttack never spoils a rest you peek at).                                                               |
| **Dark-pattern research** | "Playing by appointment" is a temporal dark pattern ([Zagal, Björk and Lewis 2013](https://www.deceptive.design/articles/dark-patterns-in-the-design-of-games), via #95); daily-return quests are the example of temporal patterns ([Niknejad et al. 2024](https://arxiv.org/html/2412.05039v1), via #95). Autonomy, competence and relatedness support non-controlling feedback ([Ryan and Deci 2000](https://selfdeterminationtheory.org/SDT/documents/2000_RyanDeci_SDT.pdf), via `companion-roadmap.md`).                                                                                                                                                                                                                                                                                                   | No appointments, no daily quests; choice over where to rest; feedback that informs rather than presses.                                                                                      |

**Gaps.** No developer interview found here explains how Stardew or Animal Crossing tune daily return against burnout; the Animal Crossing quotes are from City Folk's and New Leaf's teams. Spiritfarer's island loop is described from Wikipedia's summary, not a developer source. Three sources (iMore, Zagal et al., Niknejad et al.) were read for #95 and not re-read today.

## 3. Principles

1. **Rest is the only engine.** Every reward in a region comes back from a rest. Walking finds things; it never earns (`living-world-plan.md`: "walking to a place is optional scenery and residents, never a shortcut to rewards").
2. **Same rest, different returns** (G2). A minute of rest is worth the same GRASS anywhere. Regions vary the postcard, the visitor, the find and the story beat, so no region is "the best one to farm".
3. **Count up, never down.** Chapters, finds, visitors, ribbons and ways only ever add. Nothing expires, wilts away in a region, or resets.
4. **Nothing to do every day.** No daily quests, no resident who needs you today, no stock that is gone tomorrow. A rest on any day, at any spot, moves things on.
5. **Nothing only in one season or at one hour.** Seasons and time of day change how a place looks and sounds, and which lines are said; every collectible can be had in every season (G15).
6. **Decorative stays decorative.** Ringing a bell, riding the funicular or soaking in the springs give nothing and cost nothing.
7. **The map paces the world; the ways pace the map.** A region's content arrives with its way, at most one a day.
8. **The companion is a friend, not a stat stick.** It guides, comments and enjoys places; personality never adds power (AGENTS.md).
9. **One currency.** GRASS stays the only currency. Finds, ribbons and chapters are collections, not money.
10. **Honest.** The game counts time between START and WAKE UP; it says so (#95, section 1).
11. **No new social feature.** Raids, pairing and touch-grass-together stay as they are (C9 aside); nothing here adds visits, gifts or leaderboards.

## 4. The mechanics this adds (each a PROPOSAL)

**G1. Rest spots. PROPOSAL (new mechanic).** Each region has one to three rest spots: a bench, a bunk, a hammock, a window seat, each a real prop with a stand. Walking to one once finds it (like a keepsake). The NAP sheet and the map then offer every found spot as where the next rest happens: "rest at the bothy". The rest itself is unchanged (same GRASS, cards, minutes, ways, garden growth). Only its returns are themed by the spot (G3 to G6). The hut's bed is the default. The three outings stay where they are as the valley's first spots. The player never has to walk back to a spot: the companion travels while the player is away, as missions do today.

**G2. Same rest, different returns. PROPOSAL (principle on G1).** No spot or region changes the GRASS a minute of rest earns.

**G3. One outing per region. PROPOSAL (extends the missions).** Each region's landmark offers one timed outing, like Park Patrol, with a length that suits its theme. New outings pay at most 2 GRASS a minute (Book Club's rate) and no more than 240 for one outing, plus a postcard of the place and a find. Early return keeps its minutes and forfeits its reward, as today. The three valley outings are unchanged.

**G4. Native visitors. PROPOSAL (content and a change to the visitor roll).** Each region adds one befriendable visitor who lives there. On a rest at that region's spots, the visitor roll may draw it (proposal: half the draws that would succeed, with today's length thresholds). The nine visitors stay the valley's and can come anywhere. Rarity is never a strength tier; personality adds no stats. Names below are placeholders.

**G5. Finds. PROPOSAL (new collection).** A rest at a region's spot brings back one small find from that region (three kinds per region). Finds sit on a curiosity shelf in the hut and in the journal. A resident may ask for their region's three (G6). Finds are never sold, never needed for a way and never lost.

**G6. Resident stories. PROPOSAL (new mechanic, uses C13 world memory).** One resident per region has a story in three chapters about the region's theme (the atlas: "every region has a resident who has lost their balance in that region's way"). Chapter 1 comes after the first rest at any of the region's spots; chapter 2 after rests there on three different days (any days, not in a row); chapter 3 after one long rest there (90 minutes or more) or after giving them the region's three finds. Each chapter is read when the companion next stops by them. Chapter 3 leaves a lasting change in the world and an outfit or keepsake. Nothing waits on a date; nothing goes back.

**G7. Ring rivals and ribbons. PROPOSAL (content; terrain after C17).** Each region's ring gets a resident rival with a deck in their region's style; the town ring keeps Dave as the tutor. The first win against each rival gives a ribbon for the journal. Practice GRASS stays 5 a win for three wins a day across all rings. A terrain condition per ring follows only after C17's simulation and Matt's look at the numbers.

**G8. Region outfits. PROPOSAL (content in the hat system).** Each region's shop or resident sells one outfit for GRASS (the atlas's list: a sailor cap, goggles, a cowboy hat, a heat visor, an LED raincoat, a tiny space helmet). Cosmetic only.

**G9. Comforts as the long tail. PROPOSAL (extends #95's comforts).** Each region has three to five comforts the player can fund with GRASS: lanterns on a path, a boat on a pond, shade sails at an oasis, a shortcut. They change the world for everyone who looks at it, never gate a place or a rest spot, and are what GRASS is for once the road is open (#95: shortcuts and comforts are GRASS only).

**G10. How rest pays. PROPOSAL (changes the earning rule and the approved L2 numbers).** Real-time rests make long sleeps huge: an eight-hour night at 1 a minute and Rest 2x is 960 GRASS, more than every hat. Proposal: (1) naps keep 1 a minute and outings their rewards, with Focus 1.5x in the Focus window as approved; (2) daytime rest (naps and outings together) pays in full up to 240 GRASS a day and a quarter beyond; (3) a night's rest (four hours or more, starting in the Rest window, or between 20:00 and 02:00 when no rhythm is set) pays one well-rested gift of 60 GRASS instead of per minute, and still counts its minutes for the garden, cards, ways and the daily goal; the gift sits outside the daily ceiling, and the approved Rest 2x is folded into it. This follows `companion-roadmap.md`: "reward respecting a chosen window with a capped cosmetic acknowledgement rather than rewarding ever-longer sleep".

**G11. The wishing stones (the woodland stone circle). PROPOSAL (new mechanic).** Matt: "could have a mechanic (something magic related perhaps)". Stand in the circle and touch one of three stones (moss, fern, lantern: REST, ROAM, FOCUS) before a rest. The stones glow, and that rest's visitor roll favours the chosen family. It gives agency to a collector without raising any odds of meeting someone at all; it costs nothing; it lasts one rest.

**G12. The ember shrine (the caldera). PROPOSAL (new mechanic).** Matt: "it also needs to have some functionality". The tempering: offer three spare cards to the embers and one card of the next rarity rises from the coals. Cards only come from rest, so this is no grind; it lets a player shape a deck the 20-card cap now shapes for them. The fire country stands for burnout; the shrine is where you let go of three things to keep one.

**G13. The companion as a guide. PROPOSAL (mild mechanic and presentation).** When a native visitor is the active companion in its home region, it points once at a secret pocket it knows (the existing "!" marker). In Neon Harbour any companion leads to the nearest quiet spot. Information only, never power.

**G14. Visitors come back. PROPOSAL (changes an existing rule).** Today an unbefriended visitor "wandered off" ten seconds after the welcome-back closes (`lib/game.ts:1236`, `:1861`), and can only come back by a fresh random draw. Proposal: a met visitor waits in the Field Journal as "met at the bothy" and returns on a later rest at that region's spots with a raised chance, so missing the tap is never a loss.

**G15. Seasons without exclusives. PROPOSAL (presentation rule on L4).** Each region's season set changes props, light, its postcard's art and its residents' lines, every year again. No visitor, find, outfit or chapter is only available in one season.

**G16. Decay at home only. PROPOSAL (scope of the approved L3).** World health decays and is repaired in the home garden only. Regions never decay while the player is away, so there is never a reason to go back and mend something far away.

**G17. The region page. PROPOSAL (presentation).** The map's region card shows tallies for what the region holds: rest spots found, visitors met and befriended, chapters read, finds, the ribbon, the way. Tally marks, no percentages, no "complete!" banner, hidden by the same switch that hides way progress (#95, section 5).

## 5. Region by region

Each region below follows the same fields. Rest spots are where the companion can be sent once found (G1); the outing is G3; the visitor G4; finds G5; the story G6; the ring G7; the outfit G8; comforts G9. Ways use v5.3's names and #95's tasks and prices (decided order, one a day).

### 5.1 The home valley and the garden

**Places.** The garden and hut (the hub), Crossroads (the square and well, the library, Moss's stall, the bakery, the green with the ring), the park and bandstand, the woodland (spring pool, stone circle, forester's yard), the riverside (millpond, mill, beehives), the halt farm (platform, engine shed, windmill), Driftwood (quay, fish market, ferry slip, lighthouse) and the Headland behind its wall.

**What you do.** Everything starts and lands here: welcome back, befriend, decorate the hut and garden with keepsakes, buy hats and levels at Moss's stall, spar Dave on the green, start the three outings.

**Why you come.** It is home, and the garden visibly grows with every rest (`garden-growth.md`).

**Why you come back.** Daily: what came back from the last rest is shown here; the companion's line; the baker's noon bell and the lighthouse at dusk (C11 routines, presentation). Weekly: the gardener's story (below) moves on with rests at home. Seasonal: the meadow, orchard and hedges in their season set (L4).

**Its own things.** Visitors: the nine existing ones live here and come anywhere. Finds: an acorn, a river pebble, a goose feather. Outfit: the four hats at Moss's stall; a sailor cap at Driftwood's chandlery. Landmark: the stone circle's wishing stones (G11). Decorative: the mill wheel, the bandstand, the lighthouse lamp. Story: the shelter that became a meeting place (C13's first approved story), told by the gardener; its last chapter builds the shelter for good. Ring: the green, Dave as the tutor (unchanged).

**Rest and time away.** Spots: the hut's bed (the default, and the night spot), the bandstand (Park Patrol), the library (Book Club), the ridge cabin (Mountain Retreat), the spring pool, the millpond bench, Driftwood's harbour wall, the Headland's tower (after W1). Intention: any; this is where the habit starts.

**Ways and shortcuts.** W1, the Headland stile: one rest of 10 minutes, or 25 GRASS; the first opening, usually on day one. Comforts: the millpond boat (60) and lanterns on the ridge trail (40), as #95.

**The companion.** At home it naps in its basket, greets visitors and says one line a day. World health (L3) is the only pressure, and it stays here (G16).

### 5.2 The Frostline and the massif

**Places.** The Col Path's switchbacks and the Col hut (threshold), the Frostline lip (W2), Fir Hollow, Snowmelt Lake in its cirque, the Snow Saddle and its bothy, the High Lookout and its scope, the High Fells along the massif to Cogsworth (tarns, cairns, a shieling, the crevasse viewpoint), the hermit's tarn (an egg spot, later).

**What you do.** Walk the high paths and look: the Lookout shows the whole land, places not yet reached among it (the benchmark's "seen before reached").

**Why you come.** The view, the bothy, and the first big walk.

**Why you come back.** Daily: the warden's kettle and the choughs (presentation). Weekly: the warden's chapters. Seasonal: snow lies lower in winter and the tarn freezes at its rim; in summer, alpine flowers (scenery).

**Its own things.** Visitor: CAIRNLET (FOCUS), a pebble that stacks itself. Finds: a cairn stone, a chough feather, a frost-polished quartz. Outfit: a bobble hat and scarf, from the bothy. Landmark: the Lookout's scope (a slow pan across the land), the echo cave (decorative). Story: the hut warden ("the bothy is always open. the kettle is always on."): chapter 1 the bothy's stove relit, chapter 2 the Col hut's lamp, chapter 3 the airship beacon by the saddle's windsock lit (Matt's answer: the windsock serves an airship route), after which the airship stop can be funded (G9). Ring: a snowy clearing by the bothy against the warden, snow as the terrain condition after C17.

**Rest and time away.** Spots: the bothy's bunk (a night spot), the Col hut bench, the tarn's shore. Outing: THE HIGH FELLS, 90 minutes, 180 GRASS, a postcard and a find. Intention: move; the region pairs with walks, and W2's task is rest in all.

**Ways and shortcuts.** W2, the ridge col: 45 minutes of rest in all, or 60 GRASS. The High Fells come down to the Cog behind W3. Comforts: the airship from Cogsworth's mast to the saddle's beacon (proposal, 150, after the warden's chapter 3 and W3), a bench at the tarn (40).

**The companion.** ROAM companions are in their element (lines only): "look how far we can see."

### 5.3 The Brackens

**Places.** A low heather ridge west of the valley with pines and gorse; the gap where the Drover's Road leaves (two bluffs, a threshold); the drove well, sheepfolds and the shepherd's hut along the road; the Heather and Fold spurs; a hermit at a fire and a buried bell (pockets); the stone ring on the ridge (an egg spot, later).

**What you do.** Walk to the gap for the first view west: the steppe, and the plume of Mount Ember far beyond. Meet the drover and his dog.

**Why you come.** It is day-one country, open from the start up to the Rift, and the first place that shows the far goal.

**Why you come back.** Daily: the drover's flock moves along the road by time of day (C11). Weekly: the drover's story. Seasonal: the heather blooms purple in late summer; gorse is yellow in spring.

**Its own things.** Visitor: GORSEHOP (ROAM). Finds: a sprig of heather, a tuft of wool, a flint. Outfit: a tam from the shepherd's hut. Landmark: the drove well (draw a bucket; decorative). Story: the drover's long walk, a story that travels (Link's Awakening's trading sequence in NapAttack's terms): chapter 1 at the shepherd's hut, chapter 2 at Drover's bridge once W5 opens, chapter 3 at Palm Spring, where the flock rests by the water for good. Ring: none (the atlas puts none here).

**Rest and time away.** Spots: the shepherd's hut step, the bench at the stile below the gap. No outing; the region is a walk. Intention: move.

**Ways and shortcuts.** None needed: open from the start up to the Rift (W5). Comforts: a mended sheepfold gate, a bench at the gap's top (40 each).

**The companion.** It points at the plume: "is that a mountain on fire? one day."

### 5.4 Cogsworth and the coal hills

**Places.** Fernhollow (a woodcutters' hamlet on the Foothill Road, open from the start), the Millrace cutting (W3), Cogsworth: the platform, the clock-tower square, workshop rows, Gasworks Hill with the airship mast (reachable by a stair or cage lift, Matt's answer), the canal with its humpback bridge, a real lock with a keeper and a crane over the narrowboat (Matt's answers), the foundry, the allotments, the terminus and pump house (W7). Coal-hill benches, spoil heaps (a loop), pit heads, charcoal camps.

**What you do.** Watch the lock fill, ride the cage lift up the mast, wind the tower clock, spar on the plaza (Matt: the ring goes, the spar is on the plaza).

**Why you come.** The first rail town; the clockmaker's story; the outing on the slow boat.

**Why you come back.** Daily: the narrowboat's place along the canal by time of day, the clock's chimes, the foundry's glow at night (presentation). Weekly: the clockmaker's chapters. Seasonal: the allotments' crops change; steam hangs longer in winter.

**Its own things.** Visitor: TICKWREN (FOCUS), a clockwork wren. Finds: a brass cog, a watch spring, a lump of coal. Outfit: goggles from the workshop rows. Landmark: the lock and the cage lift (decorative). Story: the tinkerer ("every clock in cogsworth is a minute slow. on purpose."): chapter 1 a clock that runs slow on purpose; chapter 2 the foundry casts the gear Lullford's swing span waits for (narration only: W7 still opens by its own task or GRASS); chapter 3 the tower clock gets a quiet hour in which it never chimes, for good. Ring: the plaza, against the tinkerer (a FOCUS-style deck).

**Rest and time away.** Spots: the allotments' bench (warm from the foundry's steam), the narrowboat's cabin, the clock room. Outing: THE SLOW BOAT down the canal and back, 45 minutes, 90 GRASS. Intention: create or focus; the region pairs with the Focus window (1.5x, approved), and its invitation is the CUBE family's "one small thing".

**Ways and shortcuts.** W3, the Millrace landslip: one rest of 30 minutes, or 120 GRASS; the valley train runs with it. Comforts: gas lamps along the towpath (60), the airship (with the Frostline), flower boxes on the humpback bridge (40).

**The companion.** FOCUS companions hum along with the gears. In the square the companion counts the chimes.

### 5.5 The Narrows

**Places.** The Lull's gorge through the coal hills with its rapids, the Narrows Viaduct overhead (rail only), the Cog foot where the Towpath crosses at the confluence (a threshold), a heron fishing there, the braided reach below.

**What you do.** Walk the towpath into the gorge's mouth, watch the white water, see the maglev cross the viaduct once W7 is open. Drop a stick from the towpath bridge and watch it race the other side (decorative, finite).

**Why you come.** A short, loud place between the hills and the calm plain; the turn from white water to slow.

**Why you come back.** Daily: the barges pass (presentation). Seasonal: the spring spate fills the gorge; autumn runs low and clear (scenery).

**Its own things.** Visitor: SPLASHKIT (ROAM), a small otter. Finds: a river-smoothed stone, a heron feather, the stick that won. Outfit: none of its own. Landmark: the stick race. Story: the bargee and her horse: the horse, who has pulled barges for years, learns to rest at the Cog foot (one short story; its last chapter leaves a grazing paddock by the towpath). Ring: none.

**Rest and time away.** Spots: the mooring at the Cog foot, a ledge bench above the rapids. No outing. Intention: rest beside moving water.

**Ways and shortcuts.** Inside W3 (the Towpath crosses the Cog there). The Narrows lift down to the river stays a proposal (world plan decision 29); if Matt agrees, it is a comfort (120), never a gate.

**The companion.** It flinches at the spray, then grins: "loud. but nice loud."

### 5.6 The Lull plain

**Places.** The floodplain west of the Lull in three banks: water meadows, willow carr, fields along the roads, copses and creeks; the windmill, standing stones, heron pools; the river's belt with its fresh and silted oxbows (the bell in the oxbow is an egg spot, later); the willow thicket's loop; the braided reach's gravel islands. The Lull Road, the Towpath and the Coast Path cross it.

**What you do.** The longest flat walks; the standing stones; the reeds and the herons.

**Why you come.** Open from the start, on the way to Lullford; the most open sky in the land.

**Why you come back.** Daily: mist on the meadows at dawn, haymakers by day (presentation). Weekly: the birdwatcher's chapters. Seasonal: this region changes most: spring floods the water meadows (paths stay dry, world rules), summer hay, autumn mist, a frozen oxbow in winter.

**Its own things.** Visitor: REEDLING (REST). Finds: a willow leaf, a snail shell, dried meadowsweet. Outfit: a straw hat from the farm by the windmill. Landmark: the standing stones (the companion counts them and never gets the same number; decorative). Story: an old birdwatcher counting herons: chapter 1 the count, chapter 2 the heron's nest, chapter 3 a reed hide built by the fresh oxbow for good, which becomes a new rest spot. Ring: none.

**Rest and time away.** Spots: under the willows by the oxbow, the windmill's lee, a haystack (scenery changes with the season). No outing. Intention: rest, or notice (the REST family's "notice something small").

**Ways and shortcuts.** Open from the start (west bank). Comforts: stepping stones across a creek (50), a bench at the standing stones (40).

**The companion.** REST companions doze in the hay given half a chance.

### 5.7 Lullford and Gullwick

**Places.** Lullford, the town at the Lull's lowest bridging point: the old stone bridge on its island, the toll house, the iron swing span stuck open (W7), barges waiting, market carts. Gullwick, a fishing cove west of the delta on the Coast Path, with boats on the sand.

**What you do.** Browse the market, watch the barges, talk to the toll keeper, sit on Gullwick's beach.

**Why you come.** The meeting point of the east (the Lull Road, the Towpath and the Coast Path), open from the start; the gateway to the city.

**Why you come back.** Daily: the market by day, lamps on the bridge by night (presentation). Weekly: the toll keeper's chapters, which follow W7. Seasonal: the market's goods follow the plain's season (scenery).

**Its own things.** Visitor: KNOTKIN (FOCUS), a creature made of rope. Finds: an old toll token, a barge-rope knot, a fishing float. Outfit: a boater from the market. Landmark: the market. **PROPOSAL (L6's travelling merchant, with a guard):** if a stall rotates its stock, every item comes back within seven days and nothing is only there. Story: the toll keeper and the stuck span: chapter 1 "the span's been open since spring; the gear comes from Cogsworth", chapter 2 (after W3) "the foundry's casting it", chapter 3 when W7 opens, the span swings for the barges, and the keeper hangs flower boxes. Ring: none.

**Rest and time away.** Spots: the toll house's window seat, a boat hauled up at Gullwick. Outing (after W7): DOWN THE LULL CUT by barge to the canal basin, 60 minutes, 120 GRASS. Intention: read (the window seat).

**Ways and shortcuts.** W7, Lullford's swing span: an evening rest of 2 hours, or 450 GRASS; it opens the delta and the city and runs the maglev. Comforts: flower boxes on the bridge (40), the coastal steamer from Neon to Driftwood (S3, later, decided "yes, later").

**The companion.** It waits patiently at the span: "the bridge opens when the barge is through."

### 5.8 Neon Harbour and the delta

**Places.** The delta: reed beds, mudflats, boardwalks, a reed maze, stilt huts and hides; the Lull Cut's embankment (a threshold, with a lock keeper). The city round its ria: the Falls Rock old town between two waterfalls, the market, the docks and cranes, the Heights' terraces and gardens with the funicular, the canal basin, Chapel Islet under the Harbour Bridge, the Gull Strand, Beacon Isle and its old lighthouse (the keeper's door is an egg spot, later), the new town round the maglev terminus (the boulevard, the arcade, Neon Square), the Skyport. Doomscroll Dave's home turf.

**What you do.** Walk the loud city; ride the funicular; spar Dave at the Neon court.

**Why you come.** Dave lives here, and so does the game's central story; the city's quiet places are the hardest won: the theme is finding the quiet in the loud place.

**Why you come back.** Daily: the neon flickers on at dusk and never fully goes out (atlas); the night market (presentation). Weekly: Dave's chapters. Seasonal: rain in every season, snow on the Heights in winter (scenery).

**Its own things.** Visitor: GLIMMOTH (REST), a moth that learned to sleep under neon. Finds: a ferry ticket, a reed pipe from the delta, a piece of blue sea glass from the Strand. Outfit: an LED raincoat from the arcade. Landmark: the funicular, the gallery behind the falls, the view from the Harbour Bridge (decorative). Story: **Doomscroll Dave learns to sleep.** Chapter 1: Dave scoffs at naps. Chapter 2: Dave admits he can't sleep; the companion lends him a lullaby. Chapter 3: Dave asleep on a bench in the Heights gardens, his phone face down, for good; at night his window is dark. It is the atlas's whole journey, from screens back to sleep, told by the game's villain. Dave keeps his battle role. Ring: the Neon court, Dave (as now); a ribbon for the first win.

**Rest and time away.** Spots: a bench in the Heights gardens above the noise, the chapel on its islet, the gallery behind the falls, a reed hide in the delta. Outing: AN EVENING OFF, 2 hours, 240 GRASS, best started in the evening but fine at any hour. Intention: an evening without the phone (W7's own task).

**Ways and shortcuts.** W7 opens it. The maglev runs with W7; the Heights funicular is inside the city (decided). Comforts: lanterns in the Heights gardens (60), a bench on Beacon Isle (40), the coastal steamer (later).

**The companion.** It is restless in the glare ("so bright. let's find somewhere quiet.") and leads to the nearest quiet spot (G13). The atlas's open question, whether Neon should mirror the player's late-night use, stays Matt's; this proposal does not need it.

### 5.9 The Tidebloom Isles

**Places.** The Shell Bar from the Headland by an islet (tide pools, seals, terns, the wreck: an egg spot, later), Lagoon Landing (the pier, the boathouse at the lagoon's edge with its slipway), the rainforest (the giant tree, buttress roots, footbridges), the headwaters (the crater pool, the upper fall, the rain shelter), Black-sand Cove (the basalt arm, the sea stack, the sea cave, the turtle beach).

**What you do.** Walk the island's loop; lie on the black sand; listen to the frogs.

**Why you come.** The most restful place in the game, reached by the ferry or across the bar.

**Why you come back.** Daily: frogs at dusk, the boats in and out (presentation). Weekly: the naturalist's chapters. Seasonal: turtle hatchlings in late summer (scenery that recurs every year). The tide moves on the bar but never closes the path: a tide that gated walking would be an appointment.

**Its own things.** Visitor: DEWFROG (REST), "no bigger than a fingernail". Finds: a cowrie shell, an orchid petal, black sand in a vial. Outfit: a flower crown from the landing. Landmark: the turtle beach, the sea cave's echo (decorative). Story: the naturalist ("there are frogs here no bigger than a fingernail. listen."): chapter 1 the frog count, chapter 2 the turtle nest, chapter 3 a little hide at the cove for good. Ring: none; the isles stay the quiet place.

**Rest and time away.** Spots: a hammock between palms at the landing, the rain shelter at the headwaters (rest to the sound of rain), the warm black sand. Outing: A DAY ON THE ISLE, 2 hours, 240 GRASS. Intention: rest.

**Ways and shortcuts.** W4, the Shell Bar and the ferry: an evening rest of 45 minutes, or 150 GRASS. The ferry runs with W4. Comforts: a rope swing over the lagoon (60), lanterns on the pier (40).

**The companion.** It paddles in the lagoon's shallows; REST companions fall asleep in the hammock first.

### 5.10 The Sunstone basin

**Places.** The steppe of the Rift country (sheepfolds, a barrow), the Rift gorge with Drover's bridge, the ferry at its mouth and the desert line's viaduct (W5), the scrub, Palm Spring (palms, a pool, orchards, the water-seller), Dust Gulch (one street of false fronts, the saloon, the platform and water crane, the water tower), the Lode up its mule track (the mine, ore tubs, the cart line's top), the Amber canyon (banded walls, mesas, a fossil: an egg spot, later), the salt lake, the dune sea's edge (a lone palm: an egg spot, later), a caravan camp, a rock arch.

**What you do.** The long walk west; lemonade at the saloon ("on the house for anyone off their phone"); climb a mesa by its ladder; walk down into the canyon's shade.

**Why you come.** The grand loop's first half; the oasis; the stars over the caravan camp.

**Why you come back.** Daily: the town naps at midday (residents in the shade, C11; the saloon never closes). Weekly: the trader's chapters. Seasonal: the desert blooms after the spring rains (scenery).

**Its own things.** Visitor: DUNEHOP (ROAM), a fennec. Finds: a desert rose, a cactus flower, a mule shoe. Outfit: a cowboy hat from the saloon. Landmark: the windpump over the dry well, mesa-top lookouts (decorative). Story: the trader at the oasis and the buried outlet (the atlas: the gulch's creek dried when a dune crept over the pool's outlet): chapter 1 the trader tells it, chapter 2 a caravan starts to dig, chapter 3 the creek runs again into Dust Gulch, and the windpump turns over a full well, for good. Drought of attention, restored by rest. Ring: a dusty corral against the cowhand; sand as the terrain condition after C17.

**Rest and time away.** Spots: the palm shade at Palm Spring, the caravan camp (a night spot under the stars), the saloon's porch. Outing: SIESTA at Palm Spring, 90 minutes, 180 GRASS. Intention: days away; W5's task is an hour of rest on three different days, the patience the desert teaches.

**Ways and shortcuts.** W5, the Rift: an hour of rest on three different days, or 250 GRASS; the desert line runs with it; the Lode Track is inside it. Comforts: shade sails at Palm Spring (60), the mine cart from the Lode to the forge (S1, 100, after W6).

**The companion.** ROAM companions love the canyon; everyone looks for shade.

### 5.11 The fire country

**Places.** The Cinder Rise (the reveal of Hearthold and the plume), the chasm bridge over the old flow and the crust causeway over the young one (W6), Hearthold (a walled hill town, its keep, stepped streets, the great hall, the herb garden, the library tower, the bell that still rings bedtime, the dragon that rests on the keep), the Ember forge at the caldera's lip and the ember shrine, Cinder Springs (travertine terraces and the bathhouse), Cinderwick (a black-sand cove), the dead forest with fireweed, fumaroles, a lava tube, the steam cave (an egg spot, later).

**What you do.** Cross the bridge; climb Hearthold's streets; soak in the springs; offer cards at the shrine (G12).

**Why you come.** The end of the land's road, and the deepest rests on the ground.

**Why you come back.** Daily: Hearthold's bell rings at the start of the player's Rest window (presentation; no notification); the forge glows at night until the smith's story ends. Weekly: the smith's chapters; the shrine whenever there are spare cards. Seasonal: fireweed in summer, steam thick over the springs in winter (scenery).

**Its own things.** Visitor: EMBERWISP (REST), an ember moth. Finds: an obsidian chip, a fireweed seed (the first plant back on burnt ground), a sulphur crystal. Outfit: a heat visor from the forge, a bathhouse towel from the springs. Landmark: the soak (the companion's idle in the hot pool), the ember shrine (G12). Story: the smith ("the forge cools at sunset. even fire needs a nap."), the region's burnout: chapter 1 the smith works through the night, chapter 2 after the player's long rests the smith tries the springs, chapter 3 the forge is banked at sunset for good and the smith is in the bathhouse at night. Ring: the basalt ring by the lava against the smith; heat as the terrain condition after C17.

**Rest and time away.** Spots: the bathhouse (a night spot: the inn above the pools), Hearthold's herb garden, Cinderwick's sand. Outing: A SOAK, 60 minutes, 120 GRASS. Intention: recovery; W6's task is six hours of rest in all, a long run of ordinary rests, as recovery from burnout is.

**Ways and shortcuts.** W6, the chasm bridge and the crust crossing: 6 hours of rest in all, or 350 GRASS. Comforts: the mine cart (S1, 100), lanterns on the Forge Stair (40), the Rift ferry's awning (40).

**The companion.** "it's hot. good place to rest after, though." In the springs the companion floats.

### 5.12 The Launch Cape and space

**Places.** The Launch Cape (the pad and service tower, the fuel farm, the bunker, a visitors' bench) and the rocket (W8); Halcyon Station (the airlock, hydroponics, the galley, the atrium's low-gravity ring, the sleep bay, the lounge window, a padded sparring ring by Matt's answer, the lander hatch W9); Lumen (the pad, the habitat, the ice rig, the tube corridor by Matt's answer, the dome, the moon tree, the hammock, dream pools and glow caps, the sparring crater).

**What you do.** Watch the launch, float through the station's rooms, walk down to the Dream Grove.

**Why you come.** The end of the journey and the deepest rest; the rocket and the lander are the two best journeys in the game.

**Why you come back.** Daily: the planet turns in the lounge window; Lumen's sky is always starry (presentation). Weekly: the stargazer's chapters, which take long rests. Seasonal: none (it is space); the season shows on the planet below.

**Its own things.** Visitor: LUNAPUFF (ROAM), who bounces in low gravity. Finds: a moon pebble, a scrap of star chart, a seed from the moon tree. Outfit: a tiny space helmet from the station's stores. Landmark: the lounge telescope, the low-gravity ring (decorative). Story: the stargazer ("i count the stars until one of us falls asleep") and the star chart with a gap (W9's closed state): chapter 1 the chart, chapter 2 the companion helps name a star, chapter 3 the chart is complete and hangs in the lounge for good, and the stargazer finally sleeps. Ring: Halcyon's padded ring and Lumen's crater against the stargazer; low gravity as the condition after C17.

**Rest and time away.** Spots: the sleep bay (a night spot: "a night in orbit"), the lounge window seat, Lumen's hammock under the moon tree (the long rest W9 asks for). Outing: STARGAZING at the lounge, 2 hours, 240 GRASS. Intention: nights and long rests.

**Ways and shortcuts.** W8, the rocket: an hour of rest on seven different days, or 700 GRASS (the Cape Road from the Skyport is inside W7). W9, the lander: a long rest of five hours on three different days, or 900 GRASS. The journeys are the shortcut back; nothing more is sold here except a window seat (40).

**The companion.** It floats. On Lumen it is quiet for the first time in the game, and says so: "listen. nothing."

### 5.13 The routes and the thresholds

**Places.** Fifteen routes (the Col Path, the High Fells, the Foothill Road, the Towpath, the Lull Road, the Delta Road, the Coast Path, Headland Lane, the Shell Bar, the Drover's Road, the Lode Track, the Canyon Road, the Ash Coast, Ember Way and the Forge Stair, the Cape Road), fifteen thresholds, thirty secret pockets, twenty-two obstacles with side paths, eight reserved egg spots.

**What they do in play.** Walking is free and finds things: a keepsake for each new place (as today), rest spots (G1) at the named places along the way, residents crossing at every threshold. The benchmark's ten noticeable things per screen of route are the reward of walking; none gives a reward, cost or chore (world plan 6.4, decision 25).

**Thresholds as beats.** The first time across, the companion says one line, the map inks the new region and its landmark appears (world plan 5.2). Ways stand at thresholds, so a threshold is also where a way's resident explains it.

**Pockets and egg spots.** Pockets hold a view, a bench, a resident or a story detail, and stay reward-free: no rest spot sits in a pocket, so finding one is its own reward. Egg spots are reserved and later (decided); when they are designed, this proposal recommends they stay pure delight with no reward.

**The wayfarers.** The drover, the bargee, the mule train and the carters give the routes life (C11 routines). The drover's story (5.3) is the one that walks a route.

**The companion.** It follows, notices, and once in a while suggests a pocket ("there's a path there") through the existing gentle next-place hint (C22).

## 6. Cross-cutting structure

### 6.1 The core loop

```
  put the phone down  -->  the companion rests at the spot you chose
          ^                (minutes, GRASS, cards, garden growth, way progress)
          |                                   |
          |                                   v
  choose where next   <--  come back: the postcard, a visitor, a find,
          ^                a chapter, a way opened (one a day at most)
          |                                   |
          +--- a few minutes: befriend, place, read, walk, spar, fund ---+
```

The outer loop is a week to months: ways open regions (one a day at most), each region's spots, visitor, finds and story come online, comforts and outfits give GRASS a home, and the world changes for good as stories end.

### 6.2 The session on a phone (2 to 10 minutes)

| Session                   | Length      | What happens                                                                                                                                                                                          |
| ------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The check-in              | about 2 min | Welcome back (what came back), befriend if someone waits, read a chapter if one is new, then NAP: "rest at the bothy again?" one tap away.                                                            |
| The send-off              | about 4 min | The check-in, plus placing a keepsake or find, funding a comfort or buying an outfit, picking a different found spot from the map.                                                                    |
| The wander (now and then) | 8 to 10 min | Walking into new ground (keepsakes, new rest spots, thresholds), riding a line, one spar. After 3 minutes the play budget pauses spending, not walking, and the companion suggests a rest (as today). |

Rules for every session: anything that spends happens in the first three minutes (inside the budget); "where next?" is never more than one tap away; nothing has to be done before resting; opening the app mid-rest changes nothing.

### 6.3 Currencies and sinks, with a balance sketch

**One currency, GRASS** (principle 9). The proposal adds no currency. Finds, ribbons and chapters are collections. The numbers are proposals for Matt to tune, in real minutes, with G10's earning rule.

| Sources (per day)                                | Light player                                                  | Committed player                                                                   |
| ------------------------------------------------ | ------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Their rests (from #95's two made-up players)     | one 30-minute rest on weekdays, an hour on Sunday             | a 60-minute afternoon rest and a 45-minute evening rest daily, nights on five days |
| Daytime rest GRASS (naps and outings)            | about 45 on weekdays (Book Club pays 60), about 100 on Sunday | about 165 (a region outing 120 plus a 45-minute nap), under the 240 ceiling        |
| Well-rested gift (G10)                           | none (no night rests)                                         | 60 on five nights a week                                                           |
| Practice spars and the daily well-kept gift (L2) | rarely                                                        | about 20 (values not set yet)                                                      |
| **A week**                                       | **about 325**                                                 | **about 1,600**                                                                    |
| **The first month**                              | **about 1,400**                                               | **about 6,800**                                                                    |

A heavy player chaining outings for six hours a day reaches about 360 a day with the ceiling, against about 720 without it.

| Sinks                                | Total (proposal)                                                        | Kind                     |
| ------------------------------------ | ----------------------------------------------------------------------- | ------------------------ |
| Ways by GRASS (#95)                  | 3,005 for all nine, usually avoided by tasks; refunded if the task wins | once                     |
| Levels                               | 500 to level 5; 2,250 to level 10 (50 x level)                          | open-ended               |
| Hats (today)                         | 280                                                                     | once                     |
| Region outfits (G8)                  | about 12 at 60 to 150: about 1,200                                      | once                     |
| Comforts and shortcuts (G9)          | about 4 per region at 40 to 200: about 4,000 to 5,000                   | once each; the long tail |
| Medicine (L2), repairs (L3), feeding | small and recurring; values not set                                     | recurring                |

**What it means.** A light player's first month buys a couple of levels, a few hats or outfits and a comfort or two, and opens most ways by tasks; the whole cosmetic and comfort catalogue takes about six months, with nothing lost by going slower. A committed player can fund almost everything in five or six weeks, after which GRASS simply accumulates: that is acceptable in a game about rest (there is nothing to keep up). New regions later bring new comforts. Prices for ways sit at about one and a half to two times what the task's rest earns as a nap (#95), so the task is usually quicker and GRASS is never the obvious best. **Region outings never pay above 2 GRASS a minute** (G3), so no region becomes the farm; Mountain Retreat's existing 2.5 a minute and its hat stay as they are.

### 6.4 Collections

| Collection       | Today              | Proposed                                                                               | Comes from                               | Shown in                       |
| ---------------- | ------------------ | -------------------------------------------------------------------------------------- | ---------------------------------------- | ------------------------------ |
| Visitors         | 9                  | + one native per region (11)                                                           | rests (the roll)                         | the Field Journal              |
| Postcards        | 3 (one per outing) | one per rest spot (about 30), season variants each year                                | completed outings and rests at a spot    | the journal                    |
| Keepsakes        | 17                 | one per v5.3 place (about 35)                                                          | walking somewhere first (unchanged rule) | the chest, the hut, the garden |
| Habit cards      | 9                  | unchanged; region card backs as cosmetics; new cards only after a C17-style simulation | rest, outings, the shrine (G12)          | the deck                       |
| Hats and outfits | 4                  | + 11 to 12 region outfits                                                              | GRASS                                    | the companion                  |
| Memories         | self-reported      | unchanged                                                                              | a break idea and a rest                  | the journal                    |
| Finds            | none               | 3 per region                                                                           | rests at a region's spots                | the curiosity shelf            |
| Chapters         | none               | 3 per region                                                                           | rests in that region                     | the journal; the world itself  |
| Ribbons          | none               | one per ring rival                                                                     | the first win against each               | the journal                    |
| Ways             | none on main       | 9 (#95)                                                                                | a rest task or GRASS                     | the map                        |
| Comforts         | none               | about 4 per region                                                                     | GRASS                                    | the world itself               |
| Curiosities      | reserved           | 8 egg spots, later, no reward                                                          | finding them                             | later                          |

Every collection counts up and is visible somewhere in the world (Animal Crossing's museum lesson): the hut's shelf, the journal, the companion's outfit, the regions themselves.

### 6.5 Pacing over the first weeks

The ways' pace is #95's, decided (one a day at most); this adds what each opening brings.

| When              | Light player                                                                                                                                                                                                                                                                                                                                             | Committed player                                                                                                                             |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Day 1             | Hatch; first rest of 10 minutes meets the first visitor (guaranteed) and opens **the Headland** (W1). Open to walk from the start: the valley, the Brackens to the Rift, the Lull plain, Lullford and Gullwick: about fifteen rest spots to find, three outings, and four stories to begin (the gardener, the drover, the birdwatcher, the toll keeper). | The same day one, plus a region outing on the plain or at Lullford.                                                                          |
| Days 2 to 7       | **The Frostline** (W2, day 2), **Cogsworth and the Narrows** (W3, day 3); then the ferry's evening rest or GRASS (100 of 150 by Friday). Two or three first chapters read.                                                                                                                                                                               | One a day: the Frostline, Cogsworth, the isles (W4), Sunstone (W5), Neon (W7), the fire country (W6). Most first chapters read; some second. |
| Weeks 2 to 4      | **The isles** around day 10 (GRASS), **Sunstone** on the third Sunday (day 21), **the fire country** around day 30. Second chapters in the valley and on the plain.                                                                                                                                                                                      | The rocket (W8) around day 13, Lumen (W9) around day 17. Third chapters and the first lasting world changes; most outfits bought.            |
| Month 2 and after | **Neon and the delta** (W7), then space in months 3 and 4 by GRASS or long rests; stories and comforts carry on at the player's pace.                                                                                                                                                                                                                    | The road is open; stories finish; GRASS goes to comforts; nothing more is asked.                                                             |

The first hour is the most important: hatch, a short rest, a visitor, the Headland's way, and a valley full of places with something to find. Nothing in a region is visible as "locked" except the ways themselves, which explain themselves in the world (#95).

### 6.6 Anti-patterns to avoid

| Anti-pattern         | Where it could creep in                                | In today's game?                                                                                       | Guard                                                                                                   |
| -------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| Chores               | resident requests, region upkeep, daily quests         | no                                                                                                     | stories advance by rests on any days; requests never expire; regions never decay (G16)                  |
| Fear of missing out  | rotating stock, seasonal creatures, visitors who leave | yes, mildly: a visitor "wandered off" ten seconds after the welcome-back (`lib/game.ts:1236`, `:1861`) | G14 brings them back; G15 no seasonal exclusives; rotating stock returns within seven days              |
| Appointments         | tides, market days, evening tasks, events              | no                                                                                                     | tides and markets are scenery; "an evening rest" means any evening (#95)                                |
| Guilt                | streaks, the "exposed" companion, decay                | partly: the exposed status after the care window; a lost raid takes GRASS (C9 removes it)              | streaks keep their weekly forgiveness; no line ever says "missed"; decay stays at home and capped (L3)  |
| Grind                | farming a region, sparring for GRASS, outing chains    | capped: three paid spars a day; the play budget                                                        | same GRASS a minute everywhere (G2), outings at most 2 a minute, a daily ceiling (G10)                  |
| Over-rewarding sleep | per-minute pay for nights at Rest 2x                   | not yet (demo speed); L2's Rest 2x would                                                               | G10's flat well-rested gift                                                                             |
| Loot-box randomness  | the visitor and card rolls                             | yes, random but free and only from rest                                                                | the wishing stones (G11), visitors come back (G14), the shrine (G12); nothing is ever bought with money |
| Paywalls             | skips, premium currency                                | no                                                                                                     | none, unless Matt decides otherwise (#95)                                                               |
| Social pressure      | leaderboards, visits, gifts                            | raids and pairing exist                                                                                | no new social feature here (Matt's go-ahead first)                                                      |
| Dishonest tracking   | claiming to know the phone was down                    | no                                                                                                     | the honesty line in the NAP sheet (#95)                                                                 |

## 7. What changes which rule

| Id  | Proposal                     | Kind                                          | Touches                                                           | Engine (Codex)                   | Art and screens (Claude)                             |
| --- | ---------------------------- | --------------------------------------------- | ----------------------------------------------------------------- | -------------------------------- | ---------------------------------------------------- |
| G1  | Rest spots                   | new mechanic                                  | `sleep`, the NAP sheet, the map; a new save field for found spots | `lib/rest-spots.ts`, save field  | spot props and stands (region lanes), the picker (B) |
| G2  | Same rest, different returns | principle                                     | none                                                              | a test that rates are equal      | none                                                 |
| G3  | One outing per region        | extends the missions                          | `missions`, `missionPlaces`, postcards                            | catalogue and settlement tests   | the departure card at each landmark                  |
| G4  | Native visitors              | content and a change to the roll              | `visitors`, `rollVisitor`                                         | the pool by spot, tests          | eleven visitors' sprites                             |
| G5  | Finds                        | new collection                                | settlement, the journal                                           | `lib/finds.ts`                   | 33 small sprites, the shelf                          |
| G6  | Resident stories             | new mechanic (C13)                            | residents, the journal, world variants                            | `lib/resident-stories.ts` on C13 | chapter states per region, lines                     |
| G7  | Ring rivals and ribbons      | content; terrain after C17                    | `rings`, battle opponents                                         | rival decks, ribbon save         | rivals' battle sprites                               |
| G8  | Region outfits               | content (hats)                                | `hats`                                                            | price table                      | outfit sprites per family                            |
| G9  | Comforts                     | extends #95                                   | `lib/world-ways.ts` comforts                                      | chip-in for comforts             | closed and built states                              |
| G10 | How rest pays                | **changes the earning rule** and L2's numbers | `tick()`, `wake()`, C9/L2                                         | C9's earning slice               | the welcome-back line                                |
| G11 | Wishing stones               | new mechanic                                  | the visitor roll                                                  | a family bias for one rest       | the circle's glow                                    |
| G12 | Ember shrine                 | new mechanic                                  | the deck                                                          | tempering rule and tests         | the shrine's ember beat                              |
| G13 | The companion as a guide     | mild mechanic, presentation                   | the "!" hint                                                      | a pocket hint by native visitor  | the companion's pointing pose                        |
| G14 | Visitors come back           | **changes an existing rule**                  | `waitingVisitor`, `rollVisitor`                                   | a return chance, migration       | the journal's "met at" line                          |
| G15 | Seasons without exclusives   | presentation rule (L4)                        | none                                                              | a test over catalogues           | season sets                                          |
| G16 | Decay at home only           | scope of the approved L3                      | C8                                                                | per-area scope                   | none                                                 |
| G17 | The region page              | presentation                                  | the map sheet                                                     | tallies from saves               | the card                                             |

## 8. Order of work and owners

1. **Now: nothing changes.** The art, motion and HUD pass comes first (AGENTS.md). This file is for Matt's answers (section 9).
2. **After C9, real-time rests and ways (#95) ship:** G10 with C9's earning slice (Codex), G14 (Codex), G16 folded into C8.
3. **The valley first:** G1 rest spots with the three existing outings as the first spots, G5 finds, G6 the gardener's story (on C13), G11 the wishing stones, G17 the region page. Claude A owns the catalogue (spots, finds, stories per region, like `lib/world-ways.ts`); Codex the rules and saves; Claude E the valley's spots and story states; Claude B the NAP sheet's spot picker and the journal.
4. **Each region as its way opens in the redrawn world:** its spots, outing, native visitor, finds, story and outfit, by the region's lane (E the valley, Frostline and Brackens; C Cogsworth, Lullford, Neon and the isles; D Sunstone, the fire country and space).
5. **Rings after C17:** rivals, ribbons and terrain conditions, once Matt has seen the simulated numbers.
6. **Comforts (G9) last,** as GRASS piles up and the regions are drawn.

Each step is its own PR; none ships a new rule before Matt's yes.

## 9. Decisions for Matt

The same twelve are in `decisions.json` for the answer page (Claude A's scratchpad). Recommendations in bold.

| #   | Decision                                  | Options                                                                                                                                                                  | Recommendation                                                 |
| --- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| 1   | How regions tie into rests (G1)           | found spots chosen from the NAP sheet; the companion must stand there; no rest spots (ways and keepsakes only)                                                           | **Found spots, chosen from the NAP sheet or the map**          |
| 2   | What differs between regions' rests (G2)  | flavour only (postcard, visitor, find, story), same GRASS; farther pays more; postcards only                                                                             | **Flavour only, same GRASS**                                   |
| 3   | How a night's sleep pays (G10)            | per minute at Rest 2x as approved; a taper per rest; a flat well-rested gift plus a daily ceiling; no GRASS for nights                                                   | **A flat well-rested gift for nights, a daily ceiling of 240** |
| 4   | New visitors (G4)                         | keep the nine; one native per region; three per region                                                                                                                   | **One native per region**                                      |
| 5   | Finds (G5)                                | no finds; a shelf only; a shelf and residents' requests; crafting decor from finds                                                                                       | **A shelf and residents' requests**                            |
| 6   | Residents' stories (G6)                   | lines stay decorative; three chapters by rests with lasting changes; Stardew-style bundles that open shortcuts                                                           | **Three chapters by rests, lasting changes**                   |
| 7   | Region outings (G3)                       | the three valley outings only; one per region at 2 a minute at most; outings that pay more the farther away                                                              | **One per region, 2 a minute at most**                         |
| 8   | Region rings (G7)                         | all spar Dave as now; a rival per ring and a ribbon once each, terrain after C17; rivals and ribbons with GRASS for each first win                                       | **A rival per ring, a ribbon, terrain after C17**              |
| 9   | The woodland stone circle (G11)           | decorative only (glows at night); the wishing stones (choose a family for the next rest); a moonlit rest there raises the visitor odds; befriended visitors gather there | **The wishing stones**                                         |
| 10  | The ember shrine (G12)                    | tempering (three spare cards for one of the next rarity); it heals the worn-out state for free; letting go of a card; decorative only                                    | **Tempering**                                                  |
| 11  | What GRASS is for in the regions (G8, G9) | hats stay four; an outfit per region and comforts to fund; outfits from stories only, comforts by GRASS                                                                  | **An outfit per region and comforts to fund**                  |
| 12  | Where world health decays (G16)           | every region; the home garden only; no decay at all                                                                                                                      | **The home garden only**                                       |

Two smaller ones ride along with these and need no separate answer unless Matt disagrees: visitors who were not befriended come back (G14), and no collectible is seasonal-only (G15).

## Sources

Read for this file (20 Oct 2026), except where marked "via #95" (read for `world-unlocks.md`) or "via `companion-roadmap.md`".

- Stardew Valley Wiki, Season: https://stardewvalleywiki.com:443/Season
- Stardew Valley Wiki, Traveling Cart: https://stardewvalleywiki.com/Traveling_Cart
- Stardew Valley Wiki, Vault (Community Center rooms): https://www.stardewvalleywiki.com/Vault
- GamesRadar, every Stardew Valley fish: https://www.gamesradar.com/stardew-valley-fish
- Iwata Asks, Animal Crossing: City Folk: https://iwataasks.nintendo.com/interviews/wii/accf/0/4
- Iwata Asks, Animal Crossing: New Leaf: https://iwataasks.nintendo.com/interviews/3ds/animalcrossing-newleaf/0/1
- Nookipedia, Mystery Island Tour: https://www.nookipedia.com/wiki/Mystery_Island
- Nookipedia, Museum: https://nookipedia.com/wiki/Museum
- iMore, Animal Crossing bridges and inclines (via #95): https://imore.com/animal-crossing-new-horizons-how-make-new-bridges-and-inclines
- Bulbapedia, Badge: https://bulbapedia.bulbagarden.net/wiki/badge
- Bulbapedia, Nocturnal Pokémon: https://bulbapedia.bulbagarden.net/wiki/Nocturnal_Pok%C3%A9mon
- Serebii, Pokémon Sleep research areas: https://serebii.net/pokemonsleep/researchareas.shtml
- Zelda Wiki, Secret Seashell: https://zeldawiki.wiki/wiki/Secret_Seashell
- Zelda Dungeon Wiki, Trading Quest: https://www.zeldadungeon.net/wiki/Trading_Quest
- Nintendo, how the developers began making, then remaking, Eastward: https://nintendo.com/us/whatsnew/how-the-developers-began-making-then-remaking-eastward
- RPG Site, Eastward review: https://rpgsite.net/review/11744-eastward-review
- Pocket Tactics, Spiritfarer interview (Nicolas Guérin): https://www.pockettactics.com/spiritfarer/interview
- Wikipedia, Spiritfarer: https://en.wikipedia.org/wiki/Spiritfarer
- Game Developer, Road to the IGF: Adam Robinson-Yu's A Short Hike: https://www.gamedeveloper.com/disciplines/road-to-the-igf-adam-robinson-yu-s-i-a-short-hike-i-
- Wikipedia, A Short Hike: https://en.wikipedia.org/wiki/A_Short_Hike
- Paste, Meet Finch: https://www.pastemagazine.com/article/finch-app-mental-health-virtual-pet-self-care
- Internet Matters, Finch: https://www.internetmatters.org/advice/apps-and-platforms/wellbeing/finch/
- Forest (official site summary): https://forestapp.cc/llms.txt
- Wikipedia, Forest (application) (via #95): https://en.wikipedia.org/wiki/Forest_(application)
- Niantic and Nintendo, Pikmin Bloom launch: https://indigo-pearl.prezly.com/niantic-and-nintendo-launch-pikmin-bloom-an-app-that-brings-a-little-joy-to-your-everyday-journeys-on-foot-p3jm6x
- Zagal, Björk and Lewis, Dark Patterns in the Design of Games, 2013 (via #95): https://www.deceptive.design/articles/dark-patterns-in-the-design-of-games
- Niknejad et al., Level Up or Game Over, MUM 2024 (via #95): https://arxiv.org/html/2412.05039v1
- Ryan and Deci 2000, self-determination theory (via `companion-roadmap.md`): https://selfdeterminationtheory.org/SDT/documents/2000_RyanDeci_SDT.pdf

**Gaps.** No source here measures whether any of these mechanics improves time away from the phone; the proposal is design judgement grounded in what these games do, not evidence of effect (`companion-roadmap.md` makes the same point about Finch). The balance sketch uses #95's two made-up players and today's prices; it is an inference to tune in play, not a measurement.
