# NapAttack

A small garden game for taking time away: nap, go on missions, collect habit cards and visitors, customise your companion, and practise card battles.

## Run this source locally

Use Node.js 24 (recommended), or 20.19.4 or newer to run the app:

```sh
npm ci
npm run dev
```

No backend configuration is required for the local garden, missions, shop, sparring, Field Journal or daily rhythm planner. Progress is saved on this device. Clearing browser data or changing the preview's origin creates a separate local save.

Pairing, player raids and Together naps require this project's online backend. If neither or only one of `EXPO_PUBLIC_BILT_URL` and `EXPO_PUBLIC_BILT_ANON_KEY` is supplied, the app starts in local mode without creating a backend client or attempting game sync. An invalid client configuration also falls back to local mode. Pending online reports remain saved for a configured build.

To enable online play, supply both variables with the existing project's genuine backend URL and public anonymous key before starting or exporting Expo. Do not invent substitute credentials. Restart Expo after changing build settings. Configured builds retain the existing online behaviour; the local preview does not simulate other players.

## Shared browser play-testing

The repository includes `vercel.json` for an HTTPS web preview. Connect Vercel to `rempemat-eng/appify`. Deploy `main` for the latest merged app, or choose the active pull request's head branch under **Deployments → Create Deployment** to test proposed changes. The branch must exist in the repository connected to that Vercel project.

Use the repository root, the **Other** framework preset and Node.js 24. The configuration installs with `npm ci`, builds with `npm run export:web`, serves `dist` and sends client routes back to the app so refreshing `/journal` works. Leave both Bilt backend variables unset for local garden testing.

With the GitHub integration enabled, future branch pushes create updated preview deployments. Share the preview URL for browser testing. If access protection is enabled, use Vercel's sharing or sign-in flow to grant access. Keep using the branch URL in the same browser profile when checking saved progress: each different origin or browser has a separate local save.

This preview covers the web experience, including layout, navigation, animations and game interactions. It does not verify native phone behaviour, screen-time monitoring or multiplayer. The existing accelerated demo time remains in effect.

## Export and check

```sh
npm run verify
```

`verify` runs TypeScript, lint, core rules, companion profiles and memories, game-store integration, garden and shared-view regression checks, and the web export. GitHub Actions runs it on PRs and pushes to `main`. Both agents follow `AGENTS.md`, with one integration owner per task branch and a check against newer main changes before handoff. The user merges ready PRs.

`check:garden` substitutes React, timer and animation boundaries while exercising the actual garden, pathfinding and projection source. It verifies emitted plans and geometry, not native scheduling or rendered phone layouts.

`check:game` requires Node.js 22.15 or newer and runs the actual game store with test-only native API and storage boundaries. It checks nap rewards, reloads, missions, visitors, purchases, sparring and unavailable online actions. It does not render screens or validate real multiplayer or physical-device behaviour.

The exported web files are written to `dist`. Serve them over HTTP when testing; opening individual HTML files directly does not reproduce normal routing or browser storage behaviour.

The game currently uses accelerated demo time: one real second represents one simulated offline minute. The play allowance and its 30-minute window use real time. Phone usage and sleep are not measured. Real multiplayer and device suspension require separate testing with a configured backend and physical devices.

## Native project readiness

```sh
npx --yes expo-doctor@1.21.5
EXPO_PLATFORM=native EXPO_NO_DOTENV=1 npx expo prebuild --platform all --no-install
```

The Native readiness workflow runs these checks on every PR and can also be started manually. It generates both native projects without installing CocoaPods, signing an app or compiling native code, checks the iOS and Android project files exist, and fails if generation changes tracked source. Generated `ios/` and `android/` folders remain ignored; edit Expo configuration or config plugins to make persistent native changes.

`eas.json` includes an internal `development` build profile using the installed Expo development client and a `development-simulator` profile for the iOS Simulator. Both set `EXPO_PLATFORM=native` so the existing native development-client configuration is included. They prepare configuration for later EAS builds; CI does not contact an EAS account, create builds or manage credentials. Review the existing app identifiers before making a signed build. Passing Doctor and Prebuild does not verify native compilation, simulator behaviour, physical devices, background timing or phone-usage measurement.

## Garden artwork

All pixel art is generated by deterministic Python scripts (Pillow) and committed:

| Script                                                    | Outputs                                                                                                        |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `scripts/art/garden.py` (+ `garden_decor.py`, `pixel.py`) | `assets/garden/*.png`, `lib/garden-map.ts` (objects, hotspots, walk grid)                                      |
| `scripts/art/pets.py`                                     | `lib/pet-sprites.ts` (Grasslings × 3 stages × 4 faces, 9 visitors, Doomscroll Dave, hats)                      |
| `scripts/art/battle.py`                                   | `assets/battle/*.png` (day/night battle field, fighter platform)                                               |
| `scripts/art/worlds.py`                                   | `assets/worlds/*.png`, `lib/world-maps.ts`, `lib/world-assets.ts` (mission worlds, props, routes and horizons) |

Run `npm run art` to regenerate everything and format the generated TypeScript. Re-running on unchanged scripts must produce no git diff; if it does, the change is unintended. The garden is a 192 × 176 native-pixel scene and all PNGs are exported at 6× nearest-neighbour; the web build keeps them crisp via `data-pixel` + `image-rendering: pixelated` in `global.css`. Pathfinding lives in `lib/garden-path.ts` and is covered by `lib/garden-path.test.ts`; sprite data integrity by `lib/art-sprites.test.ts` (both in `npm run check:core`).

Keep light coming from the upper left, use material-specific highlights and shaded faces, and concentrate texture near borders and objects. Leave the companion's clearing quiet. Lavender fabric, leaf fittings and warm timber connect the garden's objects. New object footprints must leave every hotspot reachable. Decorative pixel assets retain their art size; interactive targets are at least 44 screen pixels. Check awake and napping scenes, reduced motion and phone-sized layouts after changes.

Garden interactions should be small moments of care and discovery. Visiting the reading nook, watering the flowers, greeting the pond's frog, patting the companion and switching the lantern should provide clear visual and text feedback without adding currency, chores or another reward loop. Props respond after the companion arrives. Interrupting a journey or leaving Home must cancel its pending action. Decorative effects respect reduced motion and stop when the garden is inactive; the nap garden remains scenery.

Animation uses a shared native pixel grid with stepped poses: a four-frame terrain loop, four-phase walking, and finite reactions with a lead-in, a clear action and a quiet settle. Keep still scenery still, stagger ambient motion, and preserve static success feedback under reduced motion. The HUD uses labelled resources, 44-pixel controls, a nap action above the scene and a consistent icon-above-label dock. Keep full values in accessibility labels when compacting large resource totals.

## Companions

Tap the active pet’s name under the garden or use **Change Companion** to preview owned companions and their attributes before switching. The starter is always available; visitors become selectable once befriended. Switching is free while awake and outside a battle. Level, hats, cards and progress belong to the player and stay shared.

Personality traits and real-world invitations are descriptive. Battle notes explain the existing REST/ROAM/FOCUS rules; no new combat bonuses, tracking or rewards are introduced. Rarity does not make a companion stronger. Before a mission, choose an optional Rest, Read, Move or Create idea. When you return, explicitly keep or skip a self-reported memory. Keepsakes belong to the companion who began the break, give no extra rewards and remain available in the Field Journal’s Memories tab (latest 30, with pagination). Up to five unanswered reflections remain there too. “Just a break” needs no reflection. These choices do not measure sleep, reading, movement or phone use.

Design and research notes for later pet bonds and real-world connections are in `docs/companion-roadmap.md`.

## A living garden

Kept memories leave small reminders in the garden: a bookmark at the reading nook, a lantern beside the leaf light, a pressed leaf by the flower beds and a sketchboard beside the pond. Visiting these existing places recalls the latest matching memory; repeat visits bring out the active companion's personality. The Little Reminders shelf opens each keepsake's original companion, date and journal entry. Changing companions keeps these shared garden memories intact.

REST companions nestle beside a soft glow, ROAM companions investigate with a leaf gesture and FOCUS companions pause over a little scribble. Each visitor has its own responses. These finite, optional interactions keep feet and shadows fixed, respect reduced motion and stop when Home is inactive. They create no rewards or combat bonuses.

The Garden Trail connects home, mission destinations and the stories brought back. It offers one next step based on existing progress, with no daily task list. The rhythm planner remains an optional plan; it does not measure or reward sleep, work or phone use. [World design](docs/world-design.md) describes how the existing systems fit together and distinguishes later features.
