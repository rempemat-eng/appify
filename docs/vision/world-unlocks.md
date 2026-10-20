# World unlocks: opening the world through time away and GRASS

Matt, 20 Oct 01:05: "i want players to progressively unlock more of the world through tasks that ask the user to not use their phone or via in game currency etc."

**Status: a proposal for Matt to review.** Nothing here is built. This file designs the mechanism and its economy. Where each gate stands in the redrawn world is `world-plan.md` (written alongside this); the ways listed below are drawn from today's world and get matched to that plan's gates when it lands. Once Matt approves, this replaces two earlier lines: "Gates are soft and use rules that exist … any new kind of gate waits for Matt" (`living-world-plan.md`) and "no fares, waiting schedules or travel unlocks" (Codex's connected-world proposal, draft #23).

This is a new game rule, not an art or HUD pass. It is kept in its own module, its own save field and its own store actions so it can be reviewed, tested and switched off on its own (AGENTS.md: decorative interactions stay free, existing rules stay unchanged).

## What the game has today (main at `9175f1e`)

**One currency, GRASS** (`player.grass`; a new companion starts with 20).

| Earned by                                   | How much                                                                                           | Where                                             |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| An untimed nap (`mode: 'screen_off'`)       | 1 per minute of the nap                                                                            | `tick()` in `lib/game.ts`                         |
| An outing (mission) completed               | Park Patrol 20 (15 min), Book Club 60 (30 min), Mountain Retreat 150 (60 min, level 2, plus a hat) | `missions` and `tick()`                           |
| A raid defended / won / a practice spar won | 20 / 30 % of the rival's GRASS (at least 10) / 5, three a day                                      | `applyIncoming`, `finishBattle`, `sparringReward` |
| A touch-grass-together session              | half the partner's session GRASS as a bonus                                                        | `pollTogether`                                    |

**Spent on:** feeding (5), levelling up (50 × level), hats (30 to 150). **Lost:** a lost raid still takes GRASS (C9, the safe-currency change, is a parked draft, #18), which matters below.

**Signals of time away.** All of them come from the player's own START and WAKE UP:

- A nap or outing records wall-clock time from START to WAKE UP (or the outing's end) into `player.offline_seconds`, and per calendar day into `rules.days[day].offline`, split at midnight (`recordOffline` in `lib/offline-rules.ts`). An early return keeps every minute; it only forfeits the outing's reward.
- Each day has a goal of 120 minutes (`dailyProgress`); `gardenStreak` forgives one missed day a week; `consecutiveOfflineDays` (days in a row at the goal) widens the visitor pool.
- Garden growth (`lib/garden-growth.ts`) and a common card every 15 minutes come from lifetime rest.
- In-app play is limited to 3 minutes in each 30 (`PLAY_LIMIT_MS`, `accountPlay`).
- `lib/app-active.ts` and `startGame()` know whether NapAttack itself is in the foreground (React Native `AppState`; on the web, `document.visibilityState`). Nothing reads that during a nap: opening the app mid-nap changes nothing.
- `lib/daily-rhythm.ts` holds planned Rest and Focus windows, but says of itself: "Planning only: this module never reads device activity or awards game rewards."

**The clock runs at demo speed.** "Offline MIN are existing demo seconds" (`lib/offline-rules.ts`): one real second counts as one minute, so Park Patrol takes 15 real seconds and the daily goal 2 real minutes. `docs/break-experience.md` names "a reliable real-duration session mode" as the next substantial work. Every number in this file is in **real minutes** (open question 1).

**What is gated today.** Almost nothing. Walking is free everywhere (`lib/region-walk.ts`), every journey line runs (`travelLinks` in `lib/world-places.ts`), and the only gate is the Mountain Retreat outing at level 2 (a mission rule, not a walking one). The world map inks in walked zones and shows the rest under fog (`components/world-map.tsx`); `lib/world-map.ts` calls itself "a schematic, not a navigator or an unlock/reward system".

**What the save stores.** `world` (`region`, `x`, `y`, `visited` zones, `layout`), `mapSeen`, `decor`, `hutLook`, `rules` (the per-day record), `recentBreaks` (the last 20 receipts) and the `player` row (synced to the backend's `players` table). The save keeps unknown fields it does not recognise (`retainUnknown` in `lib/save-data.ts`), so an additive optional field is backward compatible without a version bump.

## What other games and apps teach

- **Count up, never down.** Pokémon Sleep opens each new research area once the player has registered a number of sleep styles (Cyan Beach at 20, Taupe Hollow at 70, up to Amber Canyon at 450), which only grows with nights tracked ([Serebii](https://serebii.net/pokemonsleep/researchareas.shtml)). Finch's bird grows as the player checks in, and once it is grown the Travel Agency lets it venture beyond its forest ([Paste](https://www.pastemagazine.com/article/finch-app-mental-health-virtual-pet-self-care)).
- **Don't punish leaving.** Forest's tree "withers if the user opens another application before the timer ends", a loss-aversion design ([Wikipedia](<https://en.wikipedia.org/wiki/Forest_(application)>)). Habitica takes health for missed Dailies, and death costs a level, all gold and a piece of equipment ([Habitica Wiki](https://habitica.fandom.com/wiki/Death)). Both work for some people, and both are the guilt NapAttack rules out.
- **No appointments.** Zagal, Björk and Lewis named "playing by appointment" among the temporal dark patterns ([Dark Patterns in the Design of Games, 2013](https://www.deceptive.design/articles/dark-patterns-in-the-design-of-games)); Niknejad et al. define temporal patterns as "strategies prolonging or shortening certain interaction sequences against players' expectations", with daily-return quests as the example ([Level Up or Game Over, MUM 2024](https://arxiv.org/html/2412.05039v1)).
- **Be modest about what a phone tool can prove.** A systematic review of digital self-control tools finds their real effectiveness "still poorly understood" and asks for long-term evaluation and ethics ([Monge Roffarello and De Russis, ACM TOCHI 2023](https://iris.polito.it/handle/11583/2972709)).
- **Let the system that knows, tell the game.** Pokémon GO's Adventure Sync counts walking in the background through Apple Health and Google Fit instead of requiring the app open ([The Next Web](https://thenextweb.com/news/pokemon-go-step-tracking-offline-adventure-sync)). For phone use, the equivalents are Apple's Screen Time frameworks, which need Family Controls authorisation and let an extension watch schedules and events without launching the app ([Apple](https://developer.apple.com/documentation/screentimeapidocumentation.md)), and Android's usage access, a permission the user grants in Settings ([UsageStatsManager](https://developer.android.com/reference/android/app/usage/UsageStatsManager)).
- **Gates are places and repairs, with two ways through.** Stardew Valley's bus to the desert is fixed either by finishing the Community Center's Vault bundles or by paying Joja 40,000g ([Stardew Valley Wiki](https://stardewvalleywiki.com/Bus_Stop)); the other rooms mend the quarry bridge, the greenhouse and the minecarts ([Bundles](https://stardewvalleywiki.com/Bundles)). Animal Crossing: New Horizons grows the island with the player's projects: the ladder arrives with the house-building project and opens the upper tiers ([Nookipedia](https://nookipedia.com/wiki/Ladder)), and later bridges and inclines are built to order ([iMore](https://imore.com/animal-crossing-new-horizons-how-make-new-bridges-and-inclines)).
- **Obstacles you can read.** Pokémon's HMs turned trees, water and boulders into gates opened by badges ([Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/HM)). Sea of Stars went the other way: Thierry Boulanger did not want a fallen tree that "I can't just hop over", and the grappling hook "only further open[s] up navigation" ([MobileSyrup](https://mobilesyrup.com/2023/09/11/sea-of-stars-level-design-sabotage-studio-thierry-boulanger-interview/)). The lesson for us: a gate must be a believable thing the world is mending, not an arbitrary wall.

## 1. Principles

1. **Cosy and never shaming.** The world opens because the player rested, not because they were told to. No line, colour or sound says "missed", "failed", "lost" or "hurry". Progress bars are tally marks that fill; nothing counts down.
2. **No loss, ever.** A way, once open, never closes. Progress toward a way never decays or expires. GRASS put toward a way is kept by that way and comes back if the task opens it first. Missing a day, breaking a streak or ending a rest early costs nothing; an early return keeps every minute.
3. **No appointments.** No daily quests, no timed windows to catch, no expiring offers, no notification asking the player back. The "evening" tasks below ask for a kind of rest, on any evening, whenever.
4. **Honest about what the game can know.** The game counts the time between START and WAKE UP. It cannot see the phone. It says so, plainly, where tasks are offered (see "What the game can and cannot know" below).
5. **Works offline.** Every rule runs on the device from the save. Nothing needs the server.
6. **Nothing bought with real money** unless Matt decides otherwise. No ads, no premium currency, no skip.
7. **Reduced effort for accessibility.** Every way has both routes, so someone who cannot do a long or evening rest can always open it with GRASS. A "gentle pace" setting halves every task and price (open question 6). Nothing needs speed, precision or reading under time pressure.
8. **Rest is the only input.** Walking, battles and play never move a way forward directly. GRASS does, and GRASS comes mostly from rest.
9. **The world explains itself.** A closed way is a believable thing being mended (a fallen tree, a train with a cold boiler, a ferry on the slip). Its people say what it needs. No padlocks, no level numbers on the map.
10. **Separate and reviewable.** One module, one save field, a handful of store actions, its own tests. Existing rules (missions, level gates, raids, the play budget) are untouched.

### What the game can and cannot know

| Platform                          | It can know                                                                                                                                                                                                                                                                                 | It cannot know                                                                                   |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Web (today)                       | When the player pressed START and WAKE UP; whether the NapAttack tab was visible; the device clock                                                                                                                                                                                          | Other tabs, other apps, other devices; whether the phone was picked up; whether the player slept |
| Native, no special permission     | The same, through `AppState` (NapAttack in the foreground or not)                                                                                                                                                                                                                           | The same                                                                                         |
| iOS with Screen Time (later)      | With Family Controls authorisation (an entitlement Apple must grant, `docs/native-readiness.md`), an extension can be told when usage of chosen apps crosses a threshold during a schedule; as we understand the frameworks, the app does not read raw usage itself (to confirm in a spike) | Anything the player did not authorise; anything off the device                                   |
| Android with usage access (later) | With the usage-access permission granted in Settings, screen-on and screen-off events and which app was in front                                                                                                                                                                            | Anything off the device                                                                          |

So today a **rest** means "the companion was napping or out on an outing, by the player's own START and WAKE UP". It is an honour system with a clock. The game should say so once, in the nap sheet's small print: "the game can't see your phone. it counts the time your companion rests." Opening NapAttack during a rest to peek does not stop or spoil it (as today). A changed device clock would inflate a rest; the game already trusts the clock and keeps doing so (single player, nothing to gain against anyone).

When native screen-time data arrives, it stays optional and never becomes a requirement: a web player and a player who declines the permission open the same ways at the same pace (open question 9).

## 2. The mechanism

### 2.1 Unlock units: ways

A **way** is one thing in the world that opens more of it. Four kinds:

| Kind         | What it opens                                                                              | How it is closed in the world                                      |
| ------------ | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| **Line**     | A journey service to a region (a train, the ferry, the maglev, a lift)                     | The vehicle is out of service at its stop; the line is not offered |
| **Area**     | Zones within a region beyond a natural barrier                                             | A drawn barrier across the only way in (the walk grid follows it)  |
| **Shortcut** | A quicker way between places you can already reach on foot                                 | Out of service; you walk instead                                   |
| **Comfort**  | Presentation in places you can already reach (lanterns on a trail, a boat on the millpond) | Not there yet                                                      |

Lines and areas make up **the road**, the ordered list of ways that open the world. Shortcuts and comforts are optional extras bought with GRASS; they never stand between the player and a place.

The home valley's heart is always open from the first minute: the garden and the hut, Crossroads Town, the Town Park, the Woodland, the Riverside, the Snowy Ridge with its cabin, Valley Halt and Driftwood Harbour. That is eight places to walk on day one.

### 2.2 Rest: the one measure

Every task is measured in **rest**: a nap or an outing, from START to WAKE UP or the outing's end, in real minutes. The record is the one the game already keeps (`offline_seconds` and `rules.days`), read at the moment a rest ends. Days are local calendar days and a rest is split at midnight, as `recordOffline` does. A rest of under 10 minutes still counts its minutes (the same 10-minute line the care window uses only matters for when paid work finishes, below).

A way is **in reach** once the way before it physically is open (the desert line needs the valley train; the four valley ways are in reach from the start). Only rest after a way came in reach counts toward it. All ways in reach progress together from the same rest; the player does not have to choose.

### 2.3 The two routes, and how they combine

Every way on the road can be opened by **either** route. Progress on both is kept.

**Route 1: a task of time away.** Each way names one kind of rest:

| Task kind        | Wording in the game                       | Met when                                                                                         |
| ---------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------ |
| A rest in one go | "one rest of 30 min"                      | A single rest of at least N minutes                                                              |
| Rest in all      | "45 min of rest in all"                   | Rest since the way came in reach adds up to N minutes                                            |
| Days away        | "an hour of rest on 3 different days"     | N calendar days (not in a row, any days) each with at least 60 minutes of rest                   |
| An evening rest  | "an evening rest of 45 min"               | A single rest of at least N minutes that starts between 18:00 and midnight                       |
| A long rest      | "a long rest of 5 h, on 3 different days" | N rests of at least 5 hours, ending on different days (a night counts; so does a long afternoon) |

**Route 2: GRASS.** Each way has a price. The player can **chip in** any amount at the way (its card) or on the map; the way holds it, and the meter shows it. GRASS held by a way is safe: no raid, decay or anything else touches it. If the task opens the way first, everything chipped in comes back to the wallet with a line from the companion.

**Opening.** A way opens at the end of a rest, so the world always changes while the player was away:

- When a rest meets a way's task, the way opens as that rest ends.
- When a way is paid in full, it opens at the end of the player's next rest of at least 10 minutes ("let's rest and they'll finish it"). Paying never opens a way while the player watches the screen, so GRASS cannot become a tap-to-unlock loop.
- **At most one way opens per calendar day.** If two are ready, the earlier one on the road opens and the other waits for the next rest on another day. Nothing is lost by waiting; this paces a very committed player so each opening is an event (open question 4).

**Why both routes, and not tasks for regions and GRASS for comforts.** Tasks are the main road: they say plainly what the game is for. GRASS is the side road for people whose rest does not fit a task (no evenings free, no long rests, shift work, a newborn) and for players who earn most of their GRASS from outings. Prices are set at about one and a half to two times the GRASS a player would earn by doing the task's rest as a nap, so the task is usually quicker and GRASS is never the obvious best. Comforts and shortcuts are GRASS only, which gives GRASS a lasting use after the road is done.

### 2.4 The first road (to be matched to `world-plan.md`)

Numbers are proposals for Matt; all in real minutes.

| #   | Way                 | Opens                                                                                 | Kind | In reach after | Task                                                 | Or GRASS |
| --- | ------------------- | ------------------------------------------------------------------------------------- | ---- | -------------- | ---------------------------------------------------- | -------- |
| W1  | The Headland stile  | The Headland (sea cliffs, lookout tower)                                              | Area | the start      | one rest of 10 min                                   | 25       |
| W2  | The ridge col       | The Frostline Highlands: Fir Hollow, Snowmelt Lake, the Snow Saddle, the High Lookout | Area | the start      | 45 min of rest in all                                | 60       |
| W3  | The valley train    | Cogsworth Junction and the Canal                                                      | Line | the start      | one rest of 30 min                                   | 120      |
| W4  | The Driftwood Ferry | The Tidebloom Isles                                                                   | Line | the start      | an evening rest of 45 min                            | 150      |
| W5  | The desert line     | Dust Gulch, the Desert Oasis, the Scorched Pass                                       | Line | W3             | an hour of rest on 3 different days                  | 250      |
| W6  | The chasm bridge    | Hearthold Castle, the Ember Caldera, Cinder Springs                                   | Area | W5             | 6 hours of rest in all                               | 350      |
| W7  | The maglev          | Neon Harbour and the Skyport                                                          | Line | W3             | an evening without the phone: an evening rest of 2 h | 450      |
| W8  | The space elevator  | Halcyon Station                                                                       | Line | W7             | an hour of rest on 7 different days                  | 700      |
| W9  | The shuttle         | Lumen                                                                                 | Line | W8             | a long rest of 5 h, on 3 different days              | 900      |

The tasks follow the atlas's theme (a journey from rest to screens and back to sleep): the screen city opens with an evening away from the screen, and the quiet moon, the deepest rest, with long rests. A complete road costs 3,005 GRASS by the side road, about 50 hours of napping at today's rate of 1 GRASS a minute.

**Shortcuts and comforts (GRASS only, examples):** the mine cart from Dust Gulch to the caldera's cart bay (100, after W6; until then the walk goes over the bridge); lanterns along the ridge trail (40); a rowing boat on the millpond (60). The world plan picks the real list; each is presentation or a quicker way, never a reward.

**Kept as they are:** the Mountain Retreat outing still needs level 2; the cabin itself stays walkable. Levels never gate a way.

**Area gates need one way in.** An area is closed only if every way into it is closed. The Headland meets both Driftwood Harbour and the Town Park along open borders, and the Frostline meets the Ridge at the narrow col and along Fir Hollow's whole edge (`zonePorts` today), so `world-plan.md` must either give the area a single chokepoint or draw a barrier on each way in. A check enforces it (section 4).

### 2.5 How a way looks and behaves

**In the world.** Each way is drawn by the generator of the region it stands in, in two states (closed, open), with a resident beside it who explains it:

| Way             | Closed                                                                                | Open                                                            | Who is there         |
| --------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------- |
| Headland stile  | The cliff path's stile has a broken step; a hurdle leans across it                    | A new stile; the old hurdle against the wall                    | The shepherd         |
| Ridge col       | A pine has come down across the gap above the cabin, snow on its trunk                | Sawn into rounds, stacked beside the trail, an axe in the block | A forester           |
| Valley train    | The engine in its shed at the halt, boiler cold, the signal at danger                 | Steam up at the platform, the signal off                        | The porter           |
| Driftwood Ferry | The ferry on the slipway with a patched hull and a tar pot                            | Afloat at the jetty, its flag up                                | The boatwoman        |
| Desert line     | At Cogsworth's platform a goods wagon caked in sand; the departure board shows a dune | The wagon unloaded; the board shows a cactus                    | A tinkerer           |
| Chasm bridge    | The long bridge's middle span missing; a mason's crane and stacked blocks             | The span closed, banners on the posts                           | Masons               |
| Maglev          | The terminus on the Canal dark, the car's glass dusty                                 | Lit and humming                                                 | A clerk              |
| Space elevator  | At the Skyport's anchor, the capsule parked, the ribbon unlit                         | The ribbon lit, the capsule cycling                             | A porter             |
| Shuttle         | At Halcyon's hatch, the shuttle under a cover, a star chart with a gap                | The hatch lit, the chart complete                               | The station botanist |

The barrier blocks walking only where it is drawn (world rules: no invisible walls), and it is a prop with a stand in front of it. Opening follows the motion rule (anticipate, act, settle): the next time the place is on screen, the residents finish the job in a short, finite beat (a saw stroke and the log rolls, steam rises and the signal drops), then the open state stays. With reduced motion it is simply open. The world remembers: the sawn logs stay by the trail.

**On the map.** A closed line is drawn in faded, dashed ink with the way's pictogram (a log, a cold engine, an anchor, a dune, a broken arch, a dark car, a ribbon, a covered shuttle). The regions beyond keep today's "???" under fog. When it opens, the line inks in solid; the region's name appears once walked, as now. No padlocks and no numbers on the map itself; tapping a way's pictogram opens its card.

**Before and after, for the player.** Before: a believable obstacle, a person who explains it, a card with two meters. During: each rest adds tally marks; the nap sheet says which ways the next rest helps. After: welcome back says what changed ("THE FERRY IS AFLOAT") beside the minutes and GRASS, with a small picture; the next visit shows the open way. Nothing navigates on its own.

**The companion's lines** (lowercase, short, never nagging; each said at most once a day, and never in quiet view):

- First seeing a closed way: "the ferry's being mended. if we rest a while, i bet it's ready."
- On the card: "we've rested 30 of 45 minutes toward the ridge path. no rush."
- Chipping in: "40 grass for the bridge. it'll keep it safe for us."
- Paid in full: "that's all of it. let's rest and they'll finish."
- At welcome back: "while you were away, the train got its steam back. want to ride?"
- When the task beats the GRASS: "the ferry's done, so the boatwoman gave our grass back."
- Never: "you missed", "don't lose", "only N hours left", or anything about a streak.

## 3. Pacing

Two made-up players, both starting on a Monday. Rest counts are their real habits; nobody is asked to keep them up.

- **Light:** one 30-minute rest on weekdays (two of them in the evening around 19:00), a 60-minute rest on Sunday afternoon, nothing on Saturday; never a rest overnight. Puts about 20 GRASS into ways on each day they rest.
- **Committed:** a 60-minute afternoon rest and a 45-minute evening rest every day, a nap through the night (23:00 to 07:00) on Sunday to Thursday nights, and one 2-hour evening rest on Saturday. Chips in nothing; GRASS goes to comforts.

**The first week**

| Day    | Light                                                                              | Committed                                                                                         |
| ------ | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| 1 Mon  | **The Headland** (first rest). Ridge 30/45 min, the train's task met (waits a day) | **The Headland** (afternoon rest). The ridge, the train and the ferry are met by the evening rest |
| 2 Tue  | **The Frostline Highlands**                                                        | **The Frostline Highlands** (as the night's rest ends)                                            |
| 3 Wed  | **Cogsworth** (the desert line and the maglev come in reach)                       | **Cogsworth**; the desert line's first day                                                        |
| 4 Thu  | Evening rest of 30 min (the ferry wants 45): nothing opens                         | **The Tidebloom Isles**; the desert line's second day                                             |
| 5 Fri  | Nothing opens; GRASS toward the ferry 100/150                                      | **Sunstone Reach: Dust Gulch, the Oasis, the Scorched Pass** (third day)                          |
| 6 Sat  | No rest                                                                            | **Neon Harbour** (the 2-hour evening rest); the bridge at 4 h 45 of 6 h                           |
| 7 Sun  | The desert line's first day (the hour on Sunday)                                   | **Hearthold, the Caldera and Cinder Springs**; the elevator's first day                           |
| Opened | 3 of 9 ways                                                                        | 7 of 9 ways                                                                                       |

**The first month**

- **Light:** week 2, the ferry opens on GRASS (around day 10); week 3, the desert line opens on the third Sunday (day 21) and the GRASS chipped into it since comes back; the chasm bridge follows around day 30, on that GRASS or on six hours of rest, whichever comes first. So at a month: the whole valley, the Frostline, Cogsworth, the Isles and all of Sunstone Reach (6 of 9). Neon Harbour follows in month 2 (an evening rest of 2 hours, or 450 GRASS), Halcyon and Lumen in months 3 and 4 by GRASS or long rests. With gentle pace on, roughly twice as fast.
- **Committed:** the elevator opens on day 13 (seven days with an hour) and the shuttle to Lumen on day 17 (three nights). After that the road is done; GRASS goes to shortcuts and comforts, and later regions bring new ways.

These are the numbers to tune first in play (they are inferences, not measurements). The levers are the task targets, the prices, the one-a-day rule and gentle pace. The other lever is outside this file: if C9 changes how GRASS is earned (Rest 2x, Focus 1.5x), the prices move with it.

## 4. Save, migration, store and tests

**The save field.** A new optional top-level field on `Saved`, beside `world` (not on `player`, which is a synced backend row and would need a database migration):

```ts
type WayId =
  | 'headland'
  | 'ridge-col'
  | 'valley-train'
  | 'ferry'
  | 'desert-line'
  | 'chasm-bridge'
  | 'maglev'
  | 'elevator'
  | 'shuttle'
  | 'mine-cart'
  | string; // future ids kept
type WaysSave = {
  /** when each way opened, and how */
  open: Record<WayId, { at: number; by: 'task' | 'grass' | 'legacy' }>;
  /** when each way came in reach; rest before this does not count for it */
  reach: Record<WayId, number>;
  /** progress per way: rest minutes in all, the longest single rest, qualifying days and long rests */
  progress: Record<
    WayId,
    {
      minutes: number;
      best: number;
      days: string[];
      longs: string[];
      evening: number;
    }
  >;
  /** GRASS held by each way, never lost; returned if the task opens it first */
  paid: Record<WayId, number>;
  /** the calendar day the last way opened (the one-a-day rule) */
  lastOpenDay: string;
};
```

`SAVE_VERSION` stays 1: the field is additive and optional, like `world`, `mapSeen` and `decor`. Older builds keep it untouched through `retainUnknown`. Unknown way ids are kept, never dropped.

**Migration (no player loses a place).** When `ways` is missing, it is derived once on load:

- Every way whose far side holds a zone in `world.visited`, or the zone the saved spot stands in, is open (`by: 'legacy'`), together with every way before it on its route (a player who has walked in Neon Harbour keeps the valley train and the maglev).
- Every other way is closed, in reach by today's rules, with progress starting at the migration time. No backlog of past rest is converted, and no welcome flood: the first way that later opens is announced as usual.
- GRASS, levels, hats, cards, visitors, decor and `world` are untouched.
- A saved spot in a closed place cannot happen (it would be in `visited`), but if a future layout change ever produced one, the spot's place counts as open.

**Who changes what.** `lib/save-data.ts` (the shape) is Codex's; `lib/world-save.ts` stays Claude A's and does not change (ways are their own field). The legacy derivation needs the world's geometry (which zones lie behind which way), so it lives in Claude A's catalogue and Codex calls it from the restore.

**The pure modules.**

- `lib/world-ways.ts` (Claude A): the catalogue as data. Each way's id, kind, the region and zone it stands in, its barrier (a port span or walk cells) and stand, the stops or zones it opens, its prerequisite, its task (kind and target) and price, its pictogram. Helpers: `zonesBehind(way)`, `openWalk(region, open)` and `openLinks(open)`.
- `lib/way-progress.ts` (Codex): `restoreWays(value, world)`, `legacyWays(world)`, `settleRest(ways, rest, now)` (adds a finished rest to every way in reach and returns the ways that open, at most one a day), `chipIn(ways, way, amount)`, `refunds(ways, opened)`, `taskMet(way, progress)`, `meter(way, ways)` for the card, and the gentle-pace scale. Pure; time is passed in.

**Store actions (Codex, `lib/game.ts`).**

- `chipIn(way, amount)`: only while awake, not in battle and not paused by the play budget (as feeding and hats); never more than the wallet or the remaining price.
- Settlement: `tick()` on an outing's completion and `wake()` call `settleRest` with the rest's start, end and minutes; opened ways go on the welcome reward (`WelcomeReward.ways`), refunds go to the wallet and the reward's GRASS line.
- `seeWay(way)`: remembers that the player has seen a closed way, for the companion's first line (presentation only).
- The rest's time scale comes from one constant, so demo speed and real time share the same rules.

**Walking and travel (Claude A).** `regionWalk(region)` gains the set of open ways and closes the barrier cells of every closed one (the hub's `hubWalk` follows). `travelRoute` and the travel card offer only open lines; a closed line is listed under them with its way card. A trip of several legs is offered only if every leg is open.

**Tests.**

- `lib/way-progress.test.ts` as `check:ways` in `npm run check` (Codex): an open way never closes; `paid` never decreases except by refund on opening; a refund equals what was paid; a paid way opens only at the end of a rest of 10 minutes or more; at most one way per calendar day, in road order; only rest after `reach` counts; an evening rest is judged by its start in local time (midnight and daylight-saving edges); days count apart, not in a row; a rest across midnight counts on both days; an early return counts its minutes; migration opens everything behind visited zones and the route to them and nothing else; unknown ids survive a round trip; gentle pace halves targets and prices.
- `lib/world-ways.test.ts` in `check:world` (Claude A): every way's stand is open, reachable ground on the near side; with every way closed, a flood fill from the garden and every open stop reaches no zone behind a closed way; with all open, every zone is reachable as today; barriers lie only where a barrier prop is drawn; every line's way matches a `travelLinks` pair.
- `scripts/check-garden.cjs` (hub) and the world screen: an interrupted walk to a closed way never travels or opens anything.

## 5. Interface

Where the player meets ways, all in the pixel frames, the pixel font and the HUD that exists:

- **In the world: the way's card.** Standing at a way opens its card above the hotbar, like a place card: the way's name (uppercase), its pictogram, one line of what it needs ("ONE REST OF 30 MIN"), a tally meter (one mark per 5 or 15 minutes, or per day; no percentage), the GRASS meter ("40 / 150 GRASS") and two buttons, CHIP IN 10 and CHIP IN ALL, each at least 44 px. The card closes when the companion walks off. The resident's speech bubble carries the explanation.
- **The map.** Ways in reach show their pictogram on the line or border; a WAYS page in the map sheet lists the ways in reach (at most three, in road order) with both meters and the same buttons. The guidance "!" (`gardenMarker`'s pattern) can mark the next way once, never as a badge count.
- **The NAP sheet.** One quiet line under START: "this rest helps: the valley train". The honesty line sits in the sheet's small print. A switch in the guide hides way progress altogether.
- **Welcome back.** A row per opened way ("THE VALLEY TRAIN IS RUNNING") with a small picture, beside the minutes and GRASS; a refund shows in the GRASS line. Tapping the row opens the map at the way; nothing navigates by itself.
- **The companion.** At most one line a day about ways, at the hub, from the list in 2.5.
- **No new permanent HUD element.** The wallet stays where C9/L2 puts it.
- Touch targets at least 44 px; every control has a role and label; tally marks have a text equivalent for screen readers ("30 of 45 minutes"); reduced motion shows the open state without the opening beat.

## 6. Not in scope

- Real money, ads, a premium currency or a paid skip.
- Streaks that can break, daily or weekly quests, expiring tasks, timed events, push notifications about ways.
- Any loss: closing a way, decaying progress, raids or decay touching GRASS held by a way.
- Native screen-time integration (Screen Time, usage access): later, opt-in, and never required.
- Steps, location, health data or the camera as proof of time away.
- Changing missions, their rewards, the level 2 outing gate, battles, raids or the play budget.
- Balancing the whole economy (C9, L2): this file uses today's earning and moves with C9.
- Multiplayer: shared or gifted ways, friends opening ways for each other.
- Keys, items, combat or puzzles at gates.
- Where exactly each barrier is drawn (that is `world-plan.md` and the region owners' art).

## 7. Open questions for Matt

1. **Real time or demo time?** The game counts one real second as a minute. Ways at demo speed would all open within an hour of play. _Recommendation:_ build ways on one time constant, test at demo speed, and ship them to players only with real-duration rests (the next item in `break-experience.md`), keeping demo speed as a developer switch.
2. **Either route, or tasks for regions and GRASS for comforts?** _Recommendation:_ either route opens every way on the road, GRASS chipped in comes back if the task wins, and shortcuts and comforts are GRASS only.
3. **Should paid work finish at the end of the next rest?** _Recommendation:_ yes (a rest of 10 minutes or more), so GRASS never unlocks while the player watches the screen and every opening happens while they are away.
4. **One way a day at most?** _Recommendation:_ yes. It costs nobody anything and keeps each opening an event for committed players (all nine in about 17 days instead of about 8).
5. **Which ways, in which order?** _Recommendation:_ the nine above, matched to the gates in `world-plan.md`, with the valley's heart (eight places) always open so day one is generous.
6. **A gentle pace setting?** _Recommendation:_ yes, in the guide, halving every target and price, with no mark of it anywhere in the world.
7. **Evenings by the clock or by the daily rhythm?** `lib/daily-rhythm.ts` is planning only and says it never awards anything. _Recommendation:_ evening means 18:00 to midnight by the clock for now; using the player's Rest window would make the rhythm a game rule, so it waits for your yes.
8. **Ship after C9?** A lost raid still takes GRASS today, which could empty savings meant for a way (what is chipped in is safe). _Recommendation:_ build the module now, ship it to players after C9 makes GRASS impossible to lose.
9. **What does native screen-time data add, when it comes?** _Recommendation:_ nothing mechanical. If the player grants it, the companion can say "phone untouched, nice" after a rest, but ways open at the same pace for everyone, so web players and people who decline are never behind.
10. **Existing players and testers.** _Recommendation:_ keep every place they have walked open (and the route to it), close the rest, and add a developer switch that opens every way, so play-testing the far regions does not need days of rest.
11. **Lumen by GRASS too?** It is the end of the journey and the deepest rest. _Recommendation:_ keep both routes, for players who cannot take long rests.

## How to build it

| Order | What                                                                                                      | Owner                                                                    | Files                                                                                                                                                    |
| ----- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | Matt answers section 7; `world-plan.md` fixes where each barrier stands                                   | Matt, Claude A                                                           | this file, `world-plan.md`                                                                                                                               |
| 1     | The catalogue as data, the walk and travel helpers, `world-ways.test.ts`                                  | Claude A                                                                 | `lib/world-ways.ts`, `lib/world-places.ts`, `lib/region-walk.ts`, `lib/world-save.test.ts`                                                               |
| 2     | Progress, settlement, chip-in, refunds, migration; `check:ways`                                           | Codex                                                                    | `lib/way-progress.ts` and its test, `lib/save-data.ts` (the `ways` shape)                                                                                |
| 3     | Store actions and settlement in `tick()`/`wake()`; `WelcomeReward.ways`; the time constant                | Codex                                                                    | `lib/game.ts`, `lib/visitors.ts` (the reward type), `lib/game.integration.test.ts`                                                                       |
| 4     | Barrier art, closed and open, with the resident, per region                                               | Claude E (valley), C (isles, Cogsworth, city), D (Sunstone, space, moon) | their zone generators and props, regenerated maps                                                                                                        |
| 5     | Walking and travel honour closed ways; the way card; the map's pictograms and WAYS page; the opening beat | Claude A                                                                 | `lib/region-walk.ts`, `lib/world-cards.ts`, `components/place-card.tsx`, `app/(tabs)/world.tsx`, `components/atlas-walk.tsx`, `components/world-map.tsx` |
| 6     | The hub: way cards and walking in the valley, the NAP sheet's line, welcome back, the companion's lines   | Claude B                                                                 | `components/garden-world.tsx` and the hub layer; the NAP sheet and welcome back after checking their owner on the crew board                             |
| 7     | Play-test at demo speed with the developer switch; then at real time once rests are real                  | Claude A                                                                 | the PR preview                                                                                                                                           |

Steps 1 and 2 can run side by side once Matt has answered; step 3 waits for 2, step 5 for 1 and 3, step 6 for 3. Each step is its own PR, and none ships to players before open questions 1 and 8 are settled.
