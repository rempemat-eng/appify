# Native build checklist (iOS and Android)

Claude M, 21 Oct 2026. What a development build needs today, what blocks one, and what to check once it runs. The rules that keep the code portable are in [native-readiness.md](native-readiness.md); the budgets are in `lib/budgets.ts`.

## What blocks a development build today

**Nothing in the code.** Checked on main + #183 + this branch (21 Oct, in the cloud, no device):

| Check                                  | Result                                                                                    |
| -------------------------------------- | ----------------------------------------------------------------------------------------- |
| `npx expo-doctor` (1.21.5)             | 21 of 21 checks pass                                                                      |
| `npm run export:ios` (Hermes)          | passes (in `npm run verify`)                                                              |
| `npx expo export -p android` (Hermes)  | passes (not in `verify`; run it when native code changes)                                 |
| `npm run check:native`                 | passes: browser objects guarded, web-only packages only in web files                      |
| Native packages since the 19 Oct build | none added, so the existing iOS simulator dev client (`28ca170a`) still runs today's code |

What a build does need, all on Matt's side:

1. **An Expo sign-in** (`npx eas-cli@25.2.0 login --browser`) in a real terminal. Agents never enter credentials.
2. **iOS simulator:** `npx eas-cli@25.2.0 build --profile development-simulator --platform ios --non-interactive --no-wait` (about 10 minutes on the free plan), then `npx expo start` and open it in the simulator.
3. **iOS device:** the `development` profile, which needs an Apple Developer account and the device registered (`eas device:create`). Not done yet.
4. **Android:** `npx eas-cli@25.2.0 build --profile development --platform android` gives an APK for an emulator or a phone. No Android build has been made yet; it needs no account beyond Expo's.
5. **A new dev client only when native code changes:** a new native package (for example Skia, with #152), a config plugin, or `app.config.ts`. JavaScript, art and sound load from the dev server.

## What to check on the first run (and record in native-readiness.md)

- [ ] Onboarding, including typing names (simulator text input did not reach the field on 19 Oct).
- [ ] The garden: tap-walk, a walk interrupted mid-way, a nap and waking, a spar.
- [ ] The HUD and hotbar inside the safe areas, with the home indicator clear of the hotbar; every target at least 44 pt.
- [ ] Sound: effects after the first tap, ambience in the garden, the silent switch mutes, music from another app keeps playing, nothing plays in the background, Gentle sound.
- [ ] Saves survive closing and reopening the app.
- [ ] The status bar is readable on the cream background (it drew white on 19 Oct; it wants the dark style).
- [ ] Pixel crispness of world tiles: React Native's `Image` filters linearly, so tiles at 1 image px a texel look soft. See #152 below.
- [ ] Frame time and memory in Xcode Instruments or Android Studio's profiler, on the hub and on `/world?station=pier`, against the budgets below.

## Budgets (`npm run check:budgets`, also in `check:core`)

|                              | Density 1 (today)     | Density 2                                                                      |
| ---------------------------- | --------------------- | ------------------------------------------------------------------------------ |
| World tiles in view, decoded | 12 tiles, 25 MiB      | 15 tiles, 31 MiB (2x phones and the S25 Ultra see a wider view)                |
| Moving water                 | as today              | kept at 1x (drawn 2 x 2) or stored as deltas; at 1 px a texel it would cost 4x |
| Pictures on disk             | 20 MB (16.3 MB today) | 50 MB ceiling (#183 estimates 24 to 50 MB)                                     |
| Sound on disk                | 2.75 MiB (2.6 today)  | the same; region loops need about 6 MB (docs/vision/sound.md)                  |

The check walks every tested phone size in every region at density 1 and 2. It measures source data and files, not a phone's memory.

## Landing #152 (C34, native nearest-neighbour tiles)

#152's one requested change was to take its 12 tiles from #123, which has now merged. The order:

1. **Codex C34 (owner of #152):** import the specimens from `assets/world/continent`, take the tile size from `lib/world-canvas.ts` (`WORLD_TILE`), delete `assets/native-pixels/`, and keep both flags off. Then Claude A merges it. It adds `@shopify/react-native-skia`, so a new dev client is needed afterwards (step 5 above).
2. **Matt:** one dev build with the flag (`EXPO_PUBLIC_NATIVE_PIXELS=1`), open `screenagotchi://native-pixels`, and capture the comparison docs/codex/native-pixels.md lists (Image linear against Skia nearest) on one iPhone and one Android phone.
3. **Claude A:** route `atlas-walk`'s tiles through `PixelImageLayer` once the captures show Skia nearest crisp and within the frame and memory budgets.

Density 2 makes step 3 more important: 2x tiles are stored at 1 image px a texel, so without nearest filtering they are as soft on native as today's 2x tiles.
