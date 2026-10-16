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

`verify` runs all source checks and then exports the web preview. Use `npm run check` for checks without an export, or `npm run check:garden` for garden regressions alone. Both Claude and Codex should follow `AGENTS.md`, work from the latest GitHub source, preserve concurrent changes and hand off a tested PR and preview. The user merges ready changes. GitHub runs the same `npm run verify` command for pull requests and pushes to `main` via `.github/workflows/verify.yml`. Keep that check green before merging; making it a required branch-protection check is a separate repository setting.

`check:game` requires Node.js 22.15 or newer and runs the actual game store with test-only native API and storage boundaries. It checks nap rewards, reloads, missions, visitors, purchases, sparring and unavailable online actions. It does not render screens or validate real multiplayer or physical-device behaviour.

`check:garden` executes the garden source with substituted React, timer, native and animation boundaries. It checks movement plans, cancellation, finite effects, coordinate handling, prop geometry and hotspot reachability. It does not validate real animation scheduling, browser pointer dispatch or phone layouts; the live preview remains part of review.

The exported web files are written to `dist`. Serve them over HTTP when testing; opening individual HTML files directly does not reproduce normal routing or browser storage behaviour.

The game currently uses accelerated demo time: one real second represents one simulated offline minute. The play allowance and its 30-minute window use real time. Phone usage and sleep are not measured. Real multiplayer and device suspension require separate testing with a configured backend and physical devices.

## Garden artwork

The garden is a 192 × 176 native-pixel scene, exported at 6× with nearest-neighbour scaling. Edit `scripts/art/garden.py` and `garden_decor.py`, then run `PYTHONDONTWRITEBYTECODE=1 python scripts/art/garden.py` with Pillow installed. This regenerates the PNGs and the object sizes, hotspots and walk grid in `lib/garden-map.ts`. Format the generated map with `npx oxfmt --write lib/garden-map.ts` before committing it. Companion artwork is generated separately by `scripts/art/pets.py`.

Keep light coming from the upper left, use material-specific highlights and shaded faces, and concentrate texture near borders and objects. Leave the companion's clearing quiet. Lavender fabric, leaf fittings and warm timber connect the garden's objects. New object footprints must leave every hotspot reachable. Decorative pixel assets retain their art size; interactive targets are at least 44 screen pixels. Check awake and napping scenes, reduced motion and phone-sized layouts after changes.

Garden interactions should be small moments of care and discovery. Visiting the reading nook, watering the flowers, greeting the pond's frog, patting the companion and switching the lantern should provide clear visual and text feedback without adding currency, chores or another reward loop. Props respond after the companion arrives. Interrupting a journey or leaving Home must cancel its pending action. Decorative effects respect reduced motion and stop when the garden is inactive; the nap garden remains scenery.

Animation uses a shared native pixel grid with stepped poses: a four-frame terrain loop, four-phase walking, and finite reactions with a lead-in, a clear action and a quiet settle. Keep still scenery still, stagger ambient motion, and preserve static success feedback under reduced motion. The HUD uses labelled resources, 44-pixel controls, a nap action above the scene and a consistent icon-above-label dock. Keep full values in accessibility labels when compacting large resource totals.
