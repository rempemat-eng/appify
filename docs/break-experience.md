# Short visits, meaningful time away

NapAttack's intended loop is choose → leave → return → remember. The garden should make a short visit pleasant and give the player an understandable reason to put their phone aside. More taps, longer visits or more reward claims would not establish that this works.

## Current experience

- A Home nap stays one action. An optional break-idea drawer connects the header, main nap button and garden bed to the same Rest/Read/Move/Create intention. Opening the drawer pauses garden actions. The draft resets on departure or leaving Home.
- A selected idea offers one concrete invitation and explains its garden keepsake. Recording remains an explicit, optional self-report after settlement, without extra rewards or stats.
- The nap screen names the companion, invites the player to put the phone down, and distinguishes an untimed nap from a 15/30/60-second demonstration of a mission. Quiet view removes decorative scenes while preserving session information and wake controls. The preference survives another break and reopening; it changes presentation only.
- A finished mission settles its cards, GRASS, visitor, postcard and optional reflection once, then waits in its existing shielded mission mode. The welcome sheet stays protected without spending foreground allowance or lowering mood. Returning to the garden starts a fresh 30-second care window and resumes ordinary play accounting. Waiting grants no additional offline minutes or rewards.
- WAKE UP during a timed mission opens a deliberate early-return choice. Escape/Back opens that same choice and cancels it on a second press, rather than silently forfeiting the completion reward. Untimed naps still wake directly from their explicit button; Escape/Back leaves them running.
- The return sheet keeps the garden route and adds an explicit untimed-nap route. It never automatically starts another break. Recent reflections remain accessible in the Field Journal within the existing bounded backlog. Visitor befriending remains available before departure; no indefinite visit is promised.
- Established players see a companion invitation and PLAN A BREAK as the primary Garden Trail action. Practice, the journal and changing companions remain optional details in the expanded trail.
- Stats closes when Home loses focus. Waiting visitors share Home's activity gate, cancel hidden motion and respect reduced motion. Break-history transitions also respect reduced motion.

The accelerated clock remains a demo: one elapsed second represents one simulated offline minute. This app does not verify phone inactivity, sleep, reading, movement or creativity. Missions automatically finish, but the player remains shielded until choosing to return. Existing mission payouts, completion thresholds and visitor deadlines remain unchanged. The pending return is saved locally and retains the existing backend mission mode; it requires no schema change. Older already-awake return sheets keep their previous state when migrated.

## Manual play-test still required

The workspace connection failed during implementation, so these scenarios have source/CI coverage where indicated but no new live browser or phone result. Use a disposable profile on the current PR preview and keep its origin unchanged for persistence checks.

| Scenario                                                    | Expected experience                                                                                                                               |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Quick Home nap                                              | Starts directly with Just a break; no required intention or extra confirmation.                                                                   |
| Read/Move idea → header/main/bed                            | Each route captures the chosen idea once. Opening the idea drawer cancels any pending walk; the next break begins unplanned.                      |
| Leave Home while choosing                                   | Returning does not reopen the drawer or reuse an unfinished choice.                                                                               |
| Ordinary nap and each mission                               | Companion name and clock are clear. Demo duration is honest; no phone-lock or measured-inactivity claim.                                          |
| Quiet view on/off                                           | Decorative worlds and effects disappear/reappear. Timer, help, shared-session information and wake remain usable, with no model or reward change. |
| Return → garden                                             | Settles the sheet and returns awake. No automatic next nap.                                                                                       |
| Return → Start a nap                                        | Dismisses rewards, navigates home and starts the existing untimed nap only after this explicit action.                                            |
| Waiting visitor                                             | Befriend remains usable when visible; covered or stale callbacks do nothing. No hidden peek, blink or celebration continues after coverage.       |
| Starter retained / visitor selected                         | PLAN A BREAK remains the established player's primary invitation. Switching companions or sparring is optional inside the trail.                  |
| Stats → blur → return                                       | Stats closes and the garden reactivates.                                                                                                          |
| Reduced motion, 320px width, short landscape and large text | Controls stay reachable; optional sections wrap, return content scrolls and footer stays in the sheet.                                            |
| Lock/background → resume                                    | Session settles once with correct original companion/intention. This needs real browser/device execution, not only the substituted harness.       |

Source harnesses substitute React, native UI, animation and storage boundaries. They check emitted controls, callback routing, cancellation plans and model independence; they cannot establish native frame quality, real modal stacking or reduced phone use.

## Design references and later work

Forest makes a completed session part of a lasting visible landscape: https://www.forestapp.cc/
Finch lets the user choose one featured goal: https://help.finchcare.com/hc/en-us/articles/37780061122957-Goal-of-the-Day-Explained
Pokémon Sleep separates the night session from discoveries on return: https://www.pokemonsleep.net/en/pokemon/

These suggest visible keepsakes, one optional priority and a clear return reveal. They do not prove a behavioural effect in NapAttack, and their blocking, tracking or penalty systems are not present here.

Next substantial work is a reliable real-duration session mode, with explicit persistence, resume and interruption rules. Then consider a modest player-chosen garden project spanning several breaks, with progress preserved without daily expiry. Protected-hour perks and individual pet bonuses need separate rule and balance decisions; real multiplayer remains later.
