# Dream Dust economy simulation (C33 / C40)

A deterministic solo ledger over 8 weeks (56 fixed civil days). All durations below are real minutes. These are simulated policies and proposed scenarios, not changes to the game or forecasts of player behaviour. The saved balance field remains `grass`.

## Sources and assumptions

- Live catalogue and rules: [main `162d88e4eb1450e1e54e3c72a492ff5da24c0cdc`](https://github.com/rempemat-eng/appify/commit/162d88e4eb1450e1e54e3c72a492ff5da24c0cdc), [game.ts](https://github.com/rempemat-eng/appify/blob/162d88e4eb1450e1e54e3c72a492ff5da24c0cdc/lib/game.ts), [offline-rules.ts](https://github.com/rempemat-eng/appify/blob/162d88e4eb1450e1e54e3c72a492ff5da24c0cdc/lib/offline-rules.ts) and [cards.ts](https://github.com/rempemat-eng/appify/blob/162d88e4eb1450e1e54e3c72a492ff5da24c0cdc/lib/cards.ts).
- L2 multipliers come from [living-world-plan.md](https://github.com/rempemat-eng/appify/blob/162d88e4eb1450e1e54e3c72a492ff5da24c0cdc/docs/vision/living-world-plan.md). G10 is the [PR #143 proposal](https://github.com/rempemat-eng/appify/blob/0aa6661319a204d997fcb0ef558966521377422f/docs/vision/gameplay-regions.md); regional outings, ways, comforts and new sinks are excluded.
- C40 uses [the Dream Dust source/sink map](https://github.com/rempemat-eng/appify/blob/43582c31097874ccd0274d6e67b2381fa500f70f/docs/mechanics/dream-dust.md) and imports limits directly from [rest-recognition.ts](https://github.com/rempemat-eng/appify/blob/43582c31097874ccd0274d6e67b2381fa500f70f/lib/rest-recognition.ts) at `43582c31097874ccd0274d6e67b2381fa500f70f` (#195). The new rate is an explicit assumption for Matt to judge.
- Schedules, spending targets, exposure and button presses are assumptions, not observations. Weeks start Monday; civil-day arithmetic has no host clock, timezone or DST. Only declared sessions earn rest rewards.

All profiles start with 20 Dust, level 1, mood 80 and no hats.

| Player    | Repeating rest and outing schedule                                                                                                                                                                             | Shopping / play visit                                 | Feeding and spars                               | Target level |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ----------------------------------------------- | ------------ |
| Light     | Mon, Wed, Fri 18:00: 30 min plain nap<br>Tue, Thu 12:00: 30 min book<br>Sun 14:00: 60 min mountain                                                                                                             | Mon, Tue, Wed, Thu, Fri, Sun 19:00; 60 s active       | 1 attempted / visit; 0/0/0/0/0/0/1 wins Mon–Sun | 5            |
| Regular   | Mon, Tue, Wed, Thu, Fri 10:00: 45 min plain nap<br>Mon, Tue, Wed, Thu, Fri, Sat, Sun 18:00: 30 min plain nap<br>Sat 14:00: 30 min book<br>Sun 14:00: 60 min mountain<br>Mon, Wed, Fri 23:00: 480 min plain nap | Mon, Tue, Wed, Thu, Fri, Sat, Sun 19:00; 90 s active  | 1 attempted / visit; 1/0/1/0/1/0/1 wins Mon–Sun | 10           |
| Committed | Mon, Tue, Wed, Thu, Fri, Sat, Sun 14:00: 60 min mountain<br>Mon, Tue, Wed, Thu, Fri, Sat, Sun 18:00: 45 min plain nap<br>Mon, Tue, Wed, Thu, Fri 23:00: 480 min plain nap                                      | Mon, Tue, Wed, Thu, Fri, Sat, Sun 19:00; 120 s active | 1 attempted / visit; 3/3/3/3/3/3/3 wins Mon–Sun | 20           |

Protected rhythm: enabled. Rest: Mon, Tue, Wed, Thu, Fri, Sat, Sun, 23:00–07:00. Focus: Mon, Tue, Wed, Thu, Fri, 09:00–17:00. Overnight windows belong to their starting weekday.

| Scenario                        | Credited min / real min | Nap Dust / credited min | Rest | Focus | Daytime payment                   | Qualifying night                                 | Well-kept gift / eligible visit |
| ------------------------------- | ----------------------- | ----------------------- | ---- | ----- | --------------------------------- | ------------------------------------------------ | ------------------------------- |
| Today (demo clock)              | 60                      | 1                       | 1×   | 1×    | Uncapped                          | Per minute at the applicable window rate         | 0                               |
| L2 (real time)                  | 1                       | 1                       | 2×   | 1.5×  | Uncapped                          | Per minute at the applicable window rate         | 0                               |
| G10 (proposal)                  | 1                       | 1                       | 1×   | 1.5×  | 240 in full, then 25%             | 60 per qualifying night, outside daytime ceiling | 0                               |
| Real rate + tier 0 (assumption) | 1                       | 1                       | 1×   | 1×    | 12 h / nap; 16 h / day (credited) | Per minute at the applicable window rate         | 0                               |

TODAY retains the demo clock: one real second pays one Dust, so an eight-hour plain nap pays **28,800**. L2 pays **960** for that nap (Rest 2×); G10 pays **60** as its qualifying-night gift. The new real-rate tier-0 assumption pays **480** (one Dust per credited real minute, no protected-hour multiplier or night gift). All four current hats together cost 280.

### Real rate + tier 0

The imported limits allow 720 credited real minutes per nap and 960 per civil day. Foreground time beyond the initial 60 s grace is excluded; the grace still counts. A nap crossing midnight retains its per-nap total while daily room resets. The prototype currently returns demo-second credit, so this simulator uses its limits with an explicit real-minute adapter rather than treating those raw credits as real minutes.

Profiles assume the phone is put away immediately (zero initial foreground minutes). A session can instead specify `foregroundMinutes`; after that interval it is away. Exclusions in these profiles: Light: 0 foreground / 0 cap minutes; Regular: 0 foreground / 0 cap minutes; Committed: 0 foreground / 0 cap minutes. Their schedules do not reach the caps; independent boundary fixtures, including long/split naps, midnight and foreground grace, test those limits. This continuous-minute ledger does not emulate timer rounding, clock changes or native lifecycle.

Caps/foreground exclusions affect plain naps, including a locked outing replaced by a nap. Missions retain their existing duration and fixed reward; there is no passive nap Dust on top, nor earning after the mission deadline. An early return retains credited minutes/cards but grants no completion reward. These conventions are identical across the comparisons apart from the labelled clock rates.

### Other scenario and shopping conventions

G10 nights need at least 240 real minutes and start in Rest (or 20:00–02:00 if rhythm is disabled). One gift per wake day prevents split-night duplication. The daytime taper combines naps and outings: 240 Dust in full, then 25% of the excess; night gifts and spars sit outside it. This is a taper, not a hard maximum. L2/G10 outing multipliers are weighted by time in each window, including Mountain's all-hats bonus, as an explicit interpretation of the proposals.

The well-kept gift is zero: neither its amount nor health threshold is agreed. No invented medicine, repair, decoration or #146 home-base costs are added. At each visit, configured spar wins (first 3 daily wins × 5) and any gift settle, feeding is attempted, then at most one level and one unowned hat are bought if affordable. Active visits reduce mood at one per 3 s; each 5-Dust feed restores 20, capped at 100. Rest restores one mood per credited minute.

Levels cost 50 × current level. Targets are shopping policy, not game caps. Mountain uniformly draws from the unowned catalogue, matching the game's selection rule; once all hats are owned it pays 50 extra Dust. Seed 73421 is mixed with the player ID. The independent raid stream uses 91283; enabling raids cannot consume hat draws, although changed affordability can change which hats remain. A single seed path is illustrative, not an expectation or uncertainty interval.

## 8-week results

Earned excludes the starting balance; Spent is successful purchases only. **Wallet = 20 + earned − spent − raid losses.** Hat counts distinguish purchases and free grants.

| Scenario / player |    Earned | Spent | Raid losses | Ending wallet | Level | Bought / free hats |
| ----------------- | --------: | ----: | ----------: | ------------: | ----: | -----------------: |
| TODAY / Light     |    45,800 | 1,020 |           0 |        44,800 |     5 |              4 / 0 |
| TODAY / Regular   |   902,240 | 2,810 |           0 |       899,450 |    10 |              4 / 0 |
| TODAY / Committed | 1,318,540 | 9,870 |           0 |     1,308,690 |    20 |              2 / 2 |
| L2 / Light        |     3,750 |   870 |           0 |         2,900 |     5 |              3 / 1 |
| L2 / Regular      |    29,660 | 2,810 |           0 |        26,870 |    10 |              4 / 0 |
| L2 / Committed    |    56,600 | 9,870 |           0 |        46,750 |    20 |              2 / 2 |
| G10 / Light       |     3,750 |   870 |           0 |         2,900 |     5 |              3 / 1 |
| G10 / Regular     |     8,060 | 2,810 |           0 |         5,270 |    10 |              4 / 0 |
| G10 / Committed   | 17,581.25 | 9,870 |           0 |      7,731.25 |    20 |              2 / 2 |
| TIER0 / Light     |     3,270 |   870 |           0 |         2,420 |     5 |              3 / 1 |
| TIER0 / Regular   |    17,240 | 2,810 |           0 |        14,450 |    10 |              4 / 0 |
| TIER0 / Committed |    33,520 | 9,870 |           0 |        23,670 |    20 |              2 / 2 |

## Days to levels and all hats

First simulation day owning the item (day 1 is Monday; day 0 means already owned initially). A policy stopping below a level is distinguished from an unaffordable milestone. These are actual purchases under the stated policy, not earliest affordable unlocks or an optimised path.

| Scenario / player | Level 5 |            Level 8 |            Level 12 | All hats |
| ----------------- | ------: | -----------------: | ------------------: | -------: |
| TODAY / Light     |       4 | Policy stops at L5 |  Policy stops at L5 |        4 |
| TODAY / Regular   |       4 |                  7 | Policy stops at L10 |        4 |
| TODAY / Committed |       4 |                  7 |                  11 |        3 |
| L2 / Light        |      11 | Policy stops at L5 |  Policy stops at L5 |        8 |
| L2 / Regular      |       4 |                  7 | Policy stops at L10 |        4 |
| L2 / Committed    |       4 |                  7 |                  11 |        3 |
| G10 / Light       |      11 | Policy stops at L5 |  Policy stops at L5 |        8 |
| G10 / Regular     |       7 |                 13 | Policy stops at L10 |        5 |
| G10 / Committed   |       4 |                  7 |                  12 |        3 |
| TIER0 / Light     |      14 | Policy stops at L5 |  Policy stops at L5 |        7 |
| TIER0 / Regular   |       4 |                  7 | Policy stops at L10 |        4 |
| TIER0 / Committed |       4 |                  7 |                  11 |        3 |

## Source and spending ledger

| Scenario / player |      Naps | Outings | Night gifts | Spars | Well-kept | Defense gains | Feeding | Levels | Hats |
| ----------------- | --------: | ------: | ----------: | ----: | --------: | ------------: | ------: | -----: | ---: |
| TODAY / Light     |    43,200 |   2,560 |           0 |    40 |         0 |             0 |     240 |    500 |  280 |
| TODAY / Regular   |   900,000 |   2,080 |           0 |   160 |         0 |             0 |     280 |  2,250 |  280 |
| TODAY / Committed | 1,306,800 |  10,900 |           0 |   840 |         0 |             0 |     280 |  9,500 |   90 |
| L2 / Light        |       720 |   2,990 |           0 |    40 |         0 |             0 |     240 |    500 |  130 |
| L2 / Regular      |    27,420 |   2,080 |           0 |   160 |         0 |             0 |     280 |  2,250 |  280 |
| L2 / Committed    |    41,010 |  14,750 |           0 |   840 |         0 |             0 |     280 |  9,500 |   90 |
| G10 / Light       |       720 |   2,990 |           0 |    40 |         0 |             0 |     240 |    500 |  130 |
| G10 / Regular     |     4,380 |   2,080 |       1,440 |   160 |         0 |             0 |     280 |  2,250 |  280 |
| G10 / Committed   |  1,256.25 |  13,085 |       2,400 |   840 |         0 |             0 |     280 |  9,500 |   90 |
| TIER0 / Light     |       720 |   2,510 |           0 |    40 |         0 |             0 |     240 |    500 |  130 |
| TIER0 / Regular   |    15,000 |   2,080 |           0 |   160 |         0 |             0 |     280 |  2,250 |  280 |
| TIER0 / Committed |    21,780 |  10,900 |           0 |   840 |         0 |             0 |     280 |  9,500 |   90 |

| Scenario / player | Completed outings | Gated → nap | Early outings | Credited minutes | Card grants | Hats owned                  |
| ----------------- | ----------------: | ----------: | ------------: | ---------------: | ----------: | --------------------------- |
| TODAY / Light     |                24 |           0 |             0 |           44,160 |        2969 | CAP, SHADES, TOP HAT, CROWN |
| TODAY / Regular   |                16 |           0 |             0 |          900,720 |       60065 | CAP, SHADES, TOP HAT, CROWN |
| TODAY / Committed |                55 |           1 |             0 |        1,310,100 |       87396 | CAP, TOP HAT, SHADES, CROWN |
| L2 / Light        |                24 |           0 |             0 |            1,680 |         137 | CAP, SHADES, TOP HAT, CROWN |
| L2 / Regular      |                16 |           0 |             0 |           15,720 |        1065 | CAP, SHADES, TOP HAT, CROWN |
| L2 / Committed    |                55 |           1 |             0 |           25,080 |        1728 | CAP, TOP HAT, SHADES, CROWN |
| G10 / Light       |                24 |           0 |             0 |            1,680 |         137 | CAP, SHADES, TOP HAT, CROWN |
| G10 / Regular     |                16 |           0 |             0 |           15,720 |        1065 | CAP, SHADES, TOP HAT, CROWN |
| G10 / Committed   |                55 |           1 |             0 |           25,080 |        1728 | CAP, TOP HAT, SHADES, CROWN |
| TIER0 / Light     |                24 |           0 |             0 |            1,680 |         137 | CAP, SHADES, TOP HAT, CROWN |
| TIER0 / Regular   |                16 |           0 |             0 |           15,720 |        1065 | CAP, SHADES, TOP HAT, CROWN |
| TIER0 / Committed |                55 |           1 |             0 |           25,080 |        1728 | CAP, TOP HAT, SHADES, CROWN |

Card grants are not unique cards or final deck size: one common grant per 15 credited minutes, one per completed outing and the level-three grant. Deck composition/combat is not simulated. Eight weeks is 56 days, not two calendar months; these numbers need not reproduce #143's monthly sketch.

## Optional SIMULATE INCOMING RAID line

**OFF by default in this report.** Run `npm run sim:economy -- --incoming-raids` to enable it; this rewrites the same generated report/chart. Rerun without the switch to restore the baseline; `--check` must use the same switch as the generated output.

Assume exposure at each visit's start and 1 attempted button press(es), spaced by the 60 s recovery and only while the visit is still active. No extra visit or screen time is added and none occur during rests/missions. Care/exposure and press frequency are external assumptions, not a full status emulator. The initial press settles before shopping; any later press sees the remaining wallet.

Today's local button rules are a 50% attacker-win chance: lose min(wallet, max(10, floor(wallet × 0.3))); otherwise defend and gain 20 Dust. Gains and losses are separate. This is an isolated sensitivity using current button rules even for proposals; it does not implement L2's proposed removal of raid losses. Neither raids nor defense gains are included in the G10 daytime taper.

| Scenario / player | Landed attempts | Defended | Defense gains | Raid losses |
| ----------------- | --------------: | -------: | ------------: | ----------: |
| TODAY / Light     |               0 |        0 |             0 |           0 |
| TODAY / Regular   |               0 |        0 |             0 |           0 |
| TODAY / Committed |               0 |        0 |             0 |           0 |
| L2 / Light        |               0 |        0 |             0 |           0 |
| L2 / Regular      |               0 |        0 |             0 |           0 |
| L2 / Committed    |               0 |        0 |             0 |           0 |
| G10 / Light       |               0 |        0 |             0 |           0 |
| G10 / Regular     |               0 |        0 |             0 |           0 |
| G10 / Committed   |               0 |        0 |             0 |           0 |
| TIER0 / Light     |               0 |        0 |             0 |           0 |
| TIER0 / Regular   |               0 |        0 |             0 |           0 |
| TIER0 / Committed |               0 |        0 |             0 |           0 |

## Weekly ending wallets

![Four scenario panels with independent labelled vertical scales compare weekly wallets for light, regular and committed players.](economy-sim.svg)

Player colours and week positions match; vertical scales differ by scenario. Compare labelled amounts, not apparent slopes across panels. Rest earnings are attributed to their civil accrual days but become spendable on return; end-of-day wallets are accrual summaries, not permission to shop mid-nap.

| Scenario / player |      W1 |      W2 |      W3 |      W4 |       W5 |       W6 |        W7 |        W8 |
| ----------------- | ------: | ------: | ------: | ------: | -------: | -------: | --------: | --------: |
| TODAY / Light     |   4,935 |  10,630 |  16,325 |  22,020 |   27,715 |   33,410 |    39,105 |    44,800 |
| TODAY / Regular   | 111,085 | 222,980 | 335,725 | 448,470 |  561,215 |  673,960 |   786,705 |   899,450 |
| TODAY / Committed | 166,200 | 326,720 | 486,840 | 651,210 |  815,580 |  979,950 | 1,144,320 | 1,308,690 |
| L2 / Light        |      45 |     230 |     675 |   1,120 |    1,565 |    2,010 |     2,455 |     2,900 |
| L2 / Regular      | 2,012.5 |   4,835 | 8,507.5 |  12,180 | 15,852.5 |   19,525 |  23,197.5 |    26,870 |
| L2 / Committed    |   5,255 |   8,490 |  11,325 |  18,410 |   25,495 |   32,580 |    39,665 |    46,750 |
| G10 / Light       |      45 |     230 |     675 |   1,120 |    1,565 |    2,010 |     2,455 |     2,900 |
| G10 / Regular     |   212.5 |     285 |   407.5 |   1,380 |  2,352.5 |    3,325 |   4,297.5 |     5,270 |
| G10 / Committed   |     545 |  228.75 |   312.5 |  846.25 |    1,180 | 3,363.75 |   5,547.5 |  7,731.25 |
| TIER0 / Light     |      75 |     110 |     495 |     880 |    1,265 |    1,650 |     2,035 |     2,420 |
| TIER0 / Regular   |     460 |   1,730 |   3,850 |   5,970 |    8,090 |   10,210 |    12,330 |    14,450 |
| TIER0 / Committed |   2,475 |   2,810 |   2,745 |   6,930 |   11,115 |   15,300 |    19,485 |    23,670 |

## Limits and reproduction

- Live rules, payouts, saves, UI and art are unchanged. The app never imports this simulator.
- Real backend raids, Together bonuses, multiplayer, visitors, device use and timer/clock faults are excluded. The optional local button is off in baseline results.
- The authored policies deliberately limit purchases. Different hat/raid seeds can change spending and milestones; no outcome distribution or causal behavioural claim is estimated.
- Reproduce with `npm run sim:economy`; validate fixtures and generated Markdown/SVG with `npm run check:economy-sim`. Both use only pinned source inputs and fixed seeds.
