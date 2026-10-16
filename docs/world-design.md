# NapAttack's garden and journeys

The garden is a companion's home. Missions give that companion places to explore while the player takes a break. Returning brings a small story: an earned card, a dated postcard, a visitor or an optional memory of something the player chose to do. The point is to make time away feel connected to the garden, without requiring a chore before leaving or a task when returning.

## Places that exist

Use the current names consistently. The garden and mission worlds are separate scenes; they are not a continuous map that the player can walk between.

| Place            | Role in the world                                      | Existing behaviour                                                                                                                                                                                                   |
| ---------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Garden           | Home, a quiet clearing and the place friends return to | Tap to walk, pat the companion, read at the bench, water flowers, watch the pond and change the lantern. These interactions are cosmetic. The hut, mailbox, stall, signpost and gate open existing app destinations. |
| Park Patrol      | A short outing among trees and paths                   | A 15-simulated-MIN mission, available at level 1. Finishing awards 20 GRASS, a rare card and a park postcard. Accumulated offline time can also earn common cards.                                                   |
| Book Club        | A quiet place for stories and concentration            | A 30-simulated-MIN mission, available at level 1. Finishing awards 60 GRASS, a rare card and a library postcard. A Read intention is optional; the app does not verify reading.                                      |
| Mountain Retreat | A longer journey into open space                       | A 60-simulated-MIN mission, available at level 2. Finishing awards 150 GRASS, an epic card, a mountain postcard and an unowned hat, or 50 additional GRASS if all hats are owned.                                    |

The mission scenes show the companion walking a route. Their resident creatures are scenery; seeing one there does not record a meeting or befriend it. A break idea is independent of the destination. For example, the player can choose Rest before Park Patrol or Create before Book Club. A destination must never certify what happened outside the app.

## Three connections to make clear

1. **Home.** The garden is pleasant to explore, but its decorative interactions carry no currency, rewards or care obligation. The existing play allowance counts time spent in the app; it does not require the player to inspect every prop.
2. **Away.** A mission protects the garden and lets the companion explore its destination. This remains a demo: one real second represents one simulated offline minute. Neither sleep nor device inactivity is measured. Missions pay completion rewards, rather than per-minute GRASS; an early return keeps accumulated common-card earnings without claiming completion.
3. **Return.** The Field Journal holds visitor meetings, dated mission postcards and kept memories. Befriending a visitor during its visit makes it available as a companion. Selecting a companion preserves shared level, GRASS, hats, cards and collection; it does not reset the account or replace the starter's saved identity.

The Home `GardenJourney` panel offers one relevant next destination, derived from existing progress. It can point to a first outing, explain befriending, suggest a first postcard, introduce companion selection or invite local practice. Its expandable Garden Trail explains the three connections. It reads the supplied player and invokes caller callbacks only; it does not navigate automatically, write game state or grant rewards. These invitations are optional, not a mandatory quest chain.

## Let real life leave a trace

Mission intentions are Rest, Read, Move and Create, with Just a break as the default. After returning, the player may explicitly keep or skip a lantern, bookmark, leaf or sketch. A keepsake belongs to the companion who started the break. It is self-reported and cosmetic, without extra GRASS, cards, bond strength or battle power. An early return can still lead to an honest reflection.

The latest 30 kept memories and up to five unanswered reflections are saved locally. Companion profiles show their own keepsakes, and the Field Journal pages through the saved album. They are not cloud-backed memories or evidence of a real-world activity.

The existing daily rhythm planner is another optional connection to daily life. It schedules Rest, Focus and Own time using device-local time and supports overnight windows. It does not enforce protected hours, block phone use, measure sleep or multiply rewards. Protected-hour rewards, automatic activity verification and individual mechanical pet bonuses remain proposals.

## Practice now, social worlds later

Dave provides local practice with the existing cards and family matchups. Player raids, pairing and Together require the online backend; local play does not simulate other people. Do not present a multiplayer invitation as the next required step in the Home trail.

Garden visits, shared walks, a cooperative grove and persistent gifts are future work. They need explicit decisions about storage, recipient permission, limits and the effect of other people's actions. The existence of a mission world or a friend code does not establish that these features already work.

## Visual and interaction rules

- Home and destination scenes share the native pixel grid, upper-left lighting and clear depth cues. Preserve each place's materials and landmarks rather than adding the same decoration everywhere.
- Keep a quiet clearing around the active companion. Small details can reward looking, but interactive objects need readable silhouettes, reachable paths and touch targets of at least 44 screen pixels.
- Walking, arrivals and prop reactions should anticipate, act and settle. Decorative clocks stop when the scene is inactive and respect reduced motion.
- Supporting copy should explain what can happen next. Keep demo limits and activity verification statements close to the relevant decision, without turning the world into a technical walkthrough.
- Keep earned progress separate from optional stories. A skipped intention, memory or practice fight must not injure the companion, remove a collectible or block the next break.
