# Native readiness: keeping NapAttack ready to become an app

NapAttack runs as a web app today. Matt wants it to become an iPhone and Android app eventually, but not yet (19 Oct 2026). Until then we don't build for native or chase native bugs. We just don't make the move harder. This page lists the guardrails that keep it portable and what is checked automatically.

## Where it stands (19 Oct 2026)

- **The project.** It is an Expo project (SDK 57, React Native 0.86) with expo-router. Its storage (AsyncStorage), sound (expo-audio) and lifecycle (AppState, `useAppActive`) use libraries made for native as well as the web.
- **Web-only pieces.** The map has a web-only version (`components/MapView.web.tsx`) next to a native `MapView.tsx`. The PWA pieces (the service worker and the install prompt) switch themselves off outside the web.
- **Build setup.**
  - `eas.json` has a `development` profile and a `development-simulator` profile. The app is linked to the Expo project `@napattack/screenagotchi` (`owner` and `extra.eas.projectId` in `app.config.ts`).
  - **The baseline build, 19 Oct.** A first iOS simulator development build was made on Expo's servers (build `28ca170a`, about 10 minutes on the free plan). On the iPhone 18 Pro simulator it installs, loads the game from the dev server and runs the first screens natively: the seed choice, the naming form and its check that a name is given.
  - **Not checked yet:** typing into a text field (simulator text input didn't reach the field), the world itself, sound and saves.
  - **Native-only nit:** the status bar's clock and battery are drawn white on the cream background, so they're hard to see. The status bar style wants to be dark there.
- **CI.** "Native readiness" runs `expo-doctor` and `expo prebuild` whenever the native config or the packages change.

## The rules

1. **Browser objects only on the web.**
   - **What:** `window.*`, `document.*`, `navigator.*`, `localStorage`, `matchMedia` and the like belong behind `Platform.OS === 'web'`, or in a `name.web.tsx` file that has a native sibling (`name.tsx`).
   - **Why `typeof window` won't do:** React Native defines `window` as its global object, so `typeof window !== 'undefined'` is true in the app. That is not a guard.
   - **Checked:** `npm run check:native` fails on any new use until it is guarded and recorded in `scripts/native-safe.json`, with a sentence on how it's kept off native.
2. **Web-only packages only in web files.** `react-dom`, `pigeon-maps`, `workbox` and `posthog-js` are imported from `.web.tsx` files, or loaded with `import()` behind `Platform.OS === 'web'`. Checked.
3. **New packages must work on iOS and Android.**
   - Add them with `npx expo install <package>`, which picks versions that match the Expo SDK.
   - Prefer Expo or React Native libraries over ones built on the DOM.
   - "Native readiness" runs `expo-doctor` on every package change.
4. **Assets are bundled, not fetched from the site.**
   - Game art and sounds are `import`ed or `require`d, so Metro packs them into the app.
   - `public/` (icons, the manifest, `index.html`) exists only on the web.
5. **Touch first.**
   - Every action works with a tap, on targets of at least 44 points.
   - Nothing depends on hover.
   - The keyboard is an extra (`lib/keyboard-walk.ts` is web-only).
6. **Lay out with the screen's real size.**
   - Use `useWindowDimensions` and `useSafeAreaInsets`.
   - Use no CSS-only sizes (`vh`, `dvh`), and don't assume a browser's toolbar.
   - The app is portrait.
7. **Lifecycle through React Native.** Use `AppState` / `useAppActive`, not `document.visibilityState`. Navigate with expo-router, not `window.location`.
8. **Sound through expo-audio.** The "wait for a first gesture" gate is web-only (browsers block audio until one); native plays at once.

## What is checked automatically

| Check                  | What it proves                                                                                                                    | Where                                                                         |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `npm run check:native` | No unreviewed browser objects, no static web-only imports, every `.web.tsx` has a native sibling. Reads source only.              | part of `npm run check`                                                       |
| `npm run export:ios`   | The whole app bundles and compiles (Hermes) for iOS: imports resolve and nothing is web-only at bundle time. It takes about 15 s. | part of `npm run verify`                                                      |
| Native readiness (CI)  | `expo-doctor` passes and `expo prebuild` generates the iOS and Android projects.                                                  | `.github/workflows/native-readiness.yml`, on native config or package changes |

None of these runs the app on a phone. Now and then (Matt asked for this), check the content on a phone:

- **Phone-sized screens:** open the dev server in the iPhone simulator's Safari. For example, `/world?station=pier` jumps to Driftwood. Stations open with `?station=` and named places with `?place=`; a station given as `?place=` falls back to the saved spot.
- **The real app:** run the simulator development build (below) against the same dev server.

## Making a build (only when someone asks for one)

```bash
npx eas-cli@25.2.0 login --browser
```

The sign-in needs a real terminal: run it in a Terminal panel tab.

```bash
npx eas-cli@25.2.0 build --profile development-simulator --platform ios --non-interactive --no-wait
```

This builds a simulator app on Expo's servers. It loads the game's code from the local dev server (`npx expo start`), so later changes need no new build. A local build on this Mac would also need CocoaPods, which isn't installed.

## Before a store release (later, not now)

- **App identity:** your own bundle identifier and Android package. `me.bilt.appify` is a placeholder from the Bilt days.
- **Store accounts:** an Apple Developer account and a Google Play account.
- **Build setup:** a production profile in `eas.json` and `eas submit`.
- **Icons and splash:** at every size the stores ask for.
- **Apple requirements:** a privacy manifest and Apple's App Store review rules.
- **Real screen time (roadmap):** it needs Apple's Family Controls entitlement, which Apple must approve, and Android's usage-access permission.
