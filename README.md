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

## Export and check

```sh
npm run export:web
npm run lint
npm run check:core
npm run check:game
```

`check:game` requires Node.js 22.15 or newer and runs the actual game store with test-only native API and storage boundaries. It checks nap rewards, reloads, missions, visitors, purchases, sparring and unavailable online actions. It does not render screens or validate real multiplayer or physical-device behaviour.

The exported web files are written to `dist`. Serve them over HTTP when testing; opening individual HTML files directly does not reproduce normal routing or browser storage behaviour.

The game currently uses accelerated demo time: one real second represents one simulated offline minute. The play allowance and its 30-minute window use real time. Phone usage and sleep are not measured. Real multiplayer and device suspension require separate testing with a configured backend and physical devices.
