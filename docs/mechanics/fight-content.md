# Fight content: the model, the simulation and the decisions

Claude L (gameplay mechanics), 21 Oct. **A proposal. Nothing here changes a game rule.** The game still fights with `lib/battle.ts`; this page, `lib/fight-content.ts` (the content as data) and `lib/fight-sim.ts` (the proposed engine, for simulation only) wait for Matt. Fights stay Pokémon-style: the separate battle screen with turn-based cards (Matt, 21 Oct 10:03). Read with [fights.md](../vision/fights.md) and [cast.md](../vision/cast.md); the numbers are in [fight-sim.md](fight-sim.md) (`npm run sim:fights`).

## 1. What is built

| Piece             | Where                                            | What it holds                                                                                                                                                                                                                                                                                                                                               |
| ----------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The fourteen folk | `folk` in `lib/fight-content.ts`                 | Each folk's passive (with its numbers), four signature cards, and three variant choices at shared levels 4, 8 and 12. The ten from fights.md section 5, retuned; Tally, Tam, Tuff and Bunk drafted from cast.md                                                                                                                                             |
| The familiar      | `restedSpecials`, `restedCharge`, `pipsFor`      | One rested special per family. One pip per 20 minutes of rest since your last spar, at most three (an hour); only rest fills it                                                                                                                                                                                                                             |
| Ring rivals       | `rivals`, `rivalDeck`, `noRing`                  | Ten rings, one rival each: a family, a level (the ring's suggested shared level), a zen field (0 under F4') and one passive from the folk list. Rival decks are the player's deck at that level with the region's flavour swapped in, so a ring measures the folk and not the cards. The Brackens, the Lull and the Tidebloom Isles have no ring, by design |
| Animation needs   | `fightAnimation`                                 | The poses, effects, beats and shared pieces fights need (section 6)                                                                                                                                                                                                                                                                                         |
| The engine        | `lib/fight-sim.ts`                               | Today's engine plus stacks, the clock, soak, softening, tricks (muted and reflected), heal over time, still turns, the special, variants and the spar fixes as switches (`todayRules`, `proposedRules`)                                                                                                                                                     |
| The simulation    | `scripts/sim-fights.ts`, `lib/fight-sim.test.ts` | Seeded and deterministic. The report carries a hash of its inputs, and `npm run check:fight-sim` (in `npm run check`) fails if the data or engine changed without regenerating it                                                                                                                                                                           |

Rival names wait for Claude K's resident stories; each is named by role. Ring levels are a proposal for Claude K's unlock table.

## 2. What the simulation found

All figures are from [fight-sim.md](fight-sim.md) at its current input hash, measured with the one-turn-lookahead "smart" player unless a row says "casual" (a third of its turns by today's `chooseAI`). fights.md 4.8 asks for AUTO play at 4,000 spars a cell; this report uses 360 spars a cell (180 for the per-folk deltas), so a gap of 5 points or less is within sampling noise.

1. **A two-sided edge decides a matched spar.** With today's small 0 to 3 roll, x 1.05 / x 0.95 between families already gives a 34-point mean spread between the best and worst family at a ring (57 at worst), and today's x 1.5 / x 0.67 gives 100 (section 4). A one-sided x 1.05 on your own hits moves only 3 to 6 points (section 2). This is why today's spar is decided by family (fights.md 1.3).
2. **Today's spar is reproduced.** Against Dave, unrested, level 1: REST 0 %, ROAM 49 %, FOCUS 100 % (fights.md 1.3 found 0 / 53 / 100). Rested, Dave copies your zen and ROAM falls to 6 %.
3. **REST's habit power never lands.** REST's habit cards (DEEP BREATH, EARLY NIGHT) have no power, so its +3 never applies, while FOCUS gets it on STRETCH, the commonest card. The proposal lets a powerless habit card heal 3 instead; REST still trails (72 % against 77 and 79 over all spars), so this is a partial fix, not a cure.
4. **Zen decides spars once it is one-sided.** With F3, F4 (Dave without your zen) and F5 together, a rested player wins 98 to 100 % (section 5).
5. **Guard rails: 8 of 12 rows pass, one of them by a rule change.** Pass as specified: 1b (casual starter floor, worst 42 %), 2a, 2c, 3, 4, 5, 7 (no measurable difference between variants at this sample), 8a (+9 against a rail of 10, inside noise). 8b passes because the proposal removes zen from spars (D2); zen as built would move spars by up to 28 points. Fail: 1 (smart starter floor, worst 36 %, Velvet with REST against Dave), 2b (one folk is up to 24 points from the cast mean at a single ring; about a dozen cells exceed 12, mostly Dave at level 1 and Ashe at the late rings), and 6 (Pendle's careful line beats its casual line by 13; the rail is 10).
6. **The cast is level overall.** Every folk is within 10 points of the cast mean over all rings, no folk is best everywhere, and spars last about 7 of your turns with under 5 % at the limit. Raids under today's rules show no banking outlier (all within 5 points of the mean).
7. **Known asymmetry.** Rivals play `chooseAI` with habit cards and one passive; the player has four signature cards and plays the smart line. The ring win rates (67 to 89 % by ring) therefore measure "a careful folk against today's AI", not what a person will feel.

## 3. Decisions, with options

Each decision lists the options drafted for it. **Recommended** marks what the simulation runs as `proposedRules`.

### D1. Families in a spar

| Option                                                                                                                      | What it means                                                      | Evidence (section 4: mean / largest spread) |
| --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------- |
| A. Today: x 1.5 / x 0.67 everywhere                                                                                         | Bring the right familiar or lose                                   | 100 / 100                                   |
| B. **Recommended:** no damage multiplier in spars; a rival's family shapes its deck and its look; raids keep x 1.5 / x 0.67 | Type is flavour in spars and bites in raids; one rule fewer than C | 10 / 19                                     |
| C. No multiplier, +1 starting energy with the advantage                                                                     | The edge is lost to the energy cap: indistinguishable from B       | 10 / 19                                     |
| D. A soft multiplier, x 1.05 / x 0.95                                                                                       | Closest to today's rule, too small to read on screen               | 34 / 57                                     |
| E. No multiplier; your first damaging card x 1.5 with the advantage ("super effective", once)                               | The Pokémon moment, bounded                                        | 19 / 43                                     |

cast.md section 2 says the family keeps "today's matchup, unchanged". B changes that for spars only, so it is Matt's call. If he wants type to bite in spars, E is the bounded way (one ring then has a 43-point family gap).

### D2. Zen in a spar (F4)

| Option                                                                                              | Evidence (section 5)                                                                                                          |
| --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| A. Today: Dave copies your zen                                                                      | rested spars time out and count as losses (ROAM 6 % rested at level 1)                                                        |
| B. F4 as first proposed: rivals have their own zen, Dave none                                       | rested players win 98 to 100 %: rest decides                                                                                  |
| C. **Recommended, F4':** zen does not count in spars, for either side; it still guards you in raids | rested and unrested win the same, by construction; rest's reward in a spar is the rested special (D3), which is not built yet |

### D3. The rested special

| Option                                                                                                                                                                                                                        | Evidence                                                                                                          |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| A. fights.md: heal 8 per pip and guard / refill and draw 1 per pip / +4 power per pip, using your turn's action                                                                                                               | a refill that costs the turn wastes itself; an earlier draft (not in the current report) measured up to 18 points |
| B. **Recommended:** a free action beside your card; heal 3 per pip, guard at three / +1 energy per pip, draw 1 at three / +1 power per pip, ignoring guard. Mote's Dream is half a full special (heal 4; +1 energy; +1 power) | largest +9 (rail 10)                                                                                              |

### D4. Timed presses (F1)

| Option                                                                                                                  | Evidence                                                                                  |
| ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| A. fights.md: NICE x 1.25 on your hit, BRACED x 0.75 on theirs                                                          | not in the current report; an earlier run of x 1.1 / x 0.9 moved spars by up to 40 points |
| B. **Recommended:** NICE x 1.05 on your hit; BRACED is a stamp with no number; a miss is a plain hit; TIMING can be OFF | largest +6 (rail 15). Rail 4 is measured without BRACED, since B gives it no number       |

### D5. Rings and rivals

| Option                                                                                                                                     | What it means                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| A. **Recommended:** ten rings, rival decks equal to the player's deck at the ring's level plus regional swaps, rival zen 0, levels 1 to 12 | 67 to 89 % by ring for the smart player (section 1); casual starter floor 42 % |
| B. Rivals with hand-built, attack-heavy decks (Dave's style)                                                                               | the first draft, not in the current report: 0 to 30 % at the late rings        |

## 4. Grader scores

Three independent graders scored the options out of 10 (player experience; production cost and risk; pillars and evidence). They graded the draft before the fixes below, so C still carried the "+1 energy" claim and the text errors they found.

| Option               | Player experience | Production and risk | Pillars and evidence |
| -------------------- | ----------------: | ------------------: | -------------------: |
| D1 A, today          |                 2 |                   4 |                    2 |
| D1 B, no multiplier  |                 4 |                   7 |                    6 |
| D1 C, +1 energy      |                 5 |                   5 |                    6 |
| D1 D, x 1.05 / 0.95  |                 4 |                   5 |                    4 |
| D2 A, copy           |                 1 |                   3 |                    2 |
| D2 B, F4             |                 3 |                   4 |                    2 |
| D2 C, F4'            |                 7 |                   8 |                    7 |
| D3 A, fights.md      |                 4 |                   4 |                    3 |
| D3 B, free action    |                 6 |                   6 |                    7 |
| D4 A, x 1.25         |                 3 |                   4 |                    3 |
| D4 B, x 1.05         |                 8 |                   8 |                    8 |
| D5 A, mirrored decks |                 7 |                   7 |                    6 |
| D5 B, attack decks   |                 2 |                   4 |                    2 |
| F3 + F4' + F5        |                 6 |   F5 9, F4' 9, F3 7 |       7 as a package |

What changed because of them:

- **Fixed in the engine:** a skipped, dozed or bell turn no longer counts as a still turn; the bell no longer costs Ashe two turns; STARDUST repeats only power and heal; Nix's mute now reaches signature cards' tricks too; a muted BELL TOLL no longer strips guard; the lookahead rolls 1, not 2; variant A applies its own numbers; Dave's timing is rolled as today.
- **Fixed in the data:** card texts that did not match their numbers (SIGNAL LAMP, PLATFORM TEA, SPRING TIDE, KING TIDE); Pendle's clock and Bunk's dream are whole numbers (+3, +2) instead of x 1.15 and 15 %; rival zen is 0 (it contradicted F4').
- **Changed in the recommendation:** D1 is now B, since C's edge did nothing; option E was added (from the player-experience grader). Claims the report did not carry are labelled as earlier drafts.
- **Still open, from the graders:** the first spar against Dave is a coin flip (48 to 52 % at level 1) and trivial by level 3 (93 %), so a scripted, softer first spar (F6) is worth a look; rivals reuse passives (Tide and Bedrock twice each) and would gain from one signature card each; long passives (Nix, Puffcap) need icons that read at 402 px; F3 makes `Combat.result` three-way, which touches rewards, history and the result screen.

## 5. Today's spar: F3 to F5, for Matt (through Claude A)

Today's spar against Dave is decided before the first card: Dave is always ROAM, so a Mossling (REST) wins 0 % and a Pebbling (FOCUS) 100 % at level 1; a rested player's spars time out because Dave copies their zen (section 5 of the report). Three fixes have waited for Matt since PR #157. **Recommended as a package:**

- **F5, Dave mirrors your familiar's family.** Each family then wins about half its level-1 spars (48, 49 and 52 %) and 93 to 94 % at level 3.
- **F4', zen does not count in spars,** instead of F4 ("Dave has no zen"), which hands a rested player 98 to 100 %. Zen keeps guarding you in raids. Rest gives nothing in today's spar until the rested special is built.
- **F3, a spar at the round limit is a draw** ("a good match"), not your loss. With F4' it almost never triggers (2 % of REST spars at level 1); it is a kind safety net. It makes the result three-way, so it is the larger code change.

All three touch no art and no Dream Dust (a draw pays nothing, as a loss pays nothing).

## 6. For Claude J: what fights need from characters and animation

As data in `fightAnimation` (lib/fight-content.ts). Per folk: 12 poses per facing, east and west drawn (ready x 2, wind-up, strike x 2 with the second the impact frame, guard, hit, cast x 2, sits down, cheer x 2); a lean set of 8; one 3-frame effect per signature card (56 in all); one pip or status icon. Per family on the shoulder: idle x 2, cling, cheer, cast x 2, each facing; three 6-frame specials. Rivals: west-facing poses and two effects. Shared: hit spark, NICE ring, tinted ground puff, doze glyph, bell ring, intent and pip icons. Beats the screen keys on: ready, windup, strike, impact, cast, guard, hit, heal, stack, special, doze, bell, sitDown, cheer, bow. Reduced motion: held stills of 300 ms, no flash or shake.

## 7. Next (Codex tasks on issue #149)

C38 tunes the failing rails (1, 2b, 6) with the content's numbers only; C39 adds intents (F2), an AUTO player and a first-move check to the sim; C40 brings C33's economy sim up to the Dream Dust map ([dream-dust.md](dream-dust.md)); C41 ports F5 and F4' (then F3) into the game, only once Matt has decided. None of C38 to C40 changes `lib/battle.ts`.

## Limits

The "smart" player looks one turn ahead with rolls at their mean, and rivals play today's `chooseAI`; people will play differently. Intents are not modelled. Decks are a fixed middling deck per level, not a rested player's random one. Nothing was played on a phone.
