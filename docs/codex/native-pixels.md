# C34: nearest-neighbour world tiles on iOS and Android

This is a default-off device probe, not a switch of the game's renderer. The game still uses its existing images and the web path is unchanged. C34 addresses the native crispness question in `docs/vision/region-canvas.md` on `claude-a/region-canvas` (PR #123). Claude A owns the eventual world renderer in #126.

**Candidate:** one native Skia canvas for the mounted ground tiles, with `FilterMode.Nearest` and `MipmapMode.None`. The probe can compare it with Skia's linear sampling and React Native `Image`, using the same 2× source tiles, camera, viewport and pixel grid.

**Device results are pending.** A TypeScript check, Hermes bundle or desktop browser does not establish iOS or Android crispness, frame time or memory use. The counters in this probe also do not measure GPU render time or process memory.

## What is behind the flag

Set `EXPO_PUBLIC_NATIVE_PIXELS=1` in the Metro process, then open `/native-pixels` in a native development build. An unset flag, `0`, or any value other than the exact string `1` leaves the probe disabled. The web route returns to the existing home screen. The native probe is loaded after the flag check; its Skia canvas does not replace or wrap the live game.

The comparison uses the game's `pixelScale` contract: one art pixel occupies a whole number of physical display pixels. Camera positions are snapped to physical display pixels (a fraction of an art pixel), while every art pixel spans a whole number of physical pixels. This matters on Android devices with a fractional density as well as 2× and 3× iPhones. Nearest sampling alone cannot repair a fractional transform applied later to the whole canvas.

The controls pan the camera in either direction and start a finite 30-second sweep across tile boundaries. Controls are at least 44 points. The sweep stops when the screen loses focus or the app becomes inactive, and automatic movement respects reduced motion; manual pan remains available. A stationary image and manual pan are sufficient for the crispness check.

The displayed frame statistics are intervals between **JavaScript frame callbacks**, with p50, p95 and an over-budget count. They can reveal JS stalls during this probe. They are neither native frame-render durations nor GPU measurements, and are not evidence that the scene meets the display's frame deadline. Use the platform tools below for that decision.

## Options compared

| Option                                | Pixel sampling                                                                        | Cost and limits                                                                                                                                                                    | C34 decision                                                      |
| ------------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| React Native `Image`, 2× pictures     | Existing native path; no portable nearest-filter prop                                 | No new native dependency; useful as the baseline. `resizeMode="stretch"` controls geometry, not a nearest-neighbour sampler.                                                       | Keep as the comparison, not a claimed crisp solution.             |
| Skia, one canvas, 2× pictures         | Explicit nearest filter, mipmaps disabled                                             | Adds a native dependency and requires rebuilding the development client. Image lifetime, texture uploads, memory and frame time need device measurements.                          | Implement behind the flag; do not turn on the world renderer yet. |
| A small native image view             | iOS layer magnification/minification filters; Android bitmap paint filtering disabled | Could fit the existing image renderer, but needs two platform implementations, native project integration and maintenance. No such implementation or measurement is included here. | Alternative if the Skia measurements are unacceptable.            |
| Generate 4× pictures and keep `Image` | Avoids resampling only when source and physical display pixels match                  | Four times the decoded payload of 2× pictures. Matching one phone's density is not a general sampling guarantee.                                                                   | Fallback, not selected.                                           |

A 256×256-art-pixel tile stored at 2× is a 512×512 RGBA image: **1 MiB** of uncompressed pixel payload. Twelve unique mounted ground tiles therefore account for at most **12 MiB of source pixel payload** in this fixture. The comparable 1× and 4× payloads would be 3 MiB and 48 MiB. Those are arithmetic budgets, not measured allocations: native image caches, CPU copies, GPU textures, canvas surfaces and the rest of the app add memory. Unmounting an image does not prove its cache entry has been released.

## Fixture provenance and scope

The twelve files in `assets/native-pixels/` are exact, unchanged 2× world-ground tiles from PR #123, commit `9946d1f82f85ca91dded7da0899b24fff250df81`:

```text
assets/world/continent/t_0_2.png  ... t_2_2.png
assets/world/continent/t_0_3.png  ... t_2_3.png
assets/world/continent/t_0_4.png  ... t_2_4.png
assets/world/continent/t_0_5.png  ... t_2_5.png
```

The probe places column `c`, row `r` at logical point `(c * 256, (r - 2) * 256)`. The resulting patch is 768×1024 art pixels. The pictures are bundled with static `require` calls rather than fetched from `public/` or GitHub. They are sampling specimens, not new art or approval to reuse these assets in a rebuilt region. Their original chunk origins and the continent layout remain Claude A's responsibility.

This probe covers static ground tiles, their edges, camera movement and image loading. It does not migrate walks, saves, props, water sheets, decks, scenery, companion layering or the garden. It cannot establish the complete world's memory or frame budget. In particular, the 25 MiB ground-plus-flow budget in the canvas plan needs a later measurement with those layers actually mounted.

## Matt: install a development build on a physical device

Use a disposable local game profile. You need a new client containing Skia; the development client made on 19 October predates this dependency. Reloading its JavaScript cannot add the native module. Expo Go and a desktop browser are not substitutes for this check.

From this branch's checkout:

```bash
git switch codex/native-pixels
npm ci
```

Choose **one** way to install a new native development client:

1. **Local iPhone build:** on a Mac with Xcode, CocoaPods, signing configured and the unlocked iPhone connected and trusted, run:

   ```bash
   EXPO_PLATFORM=native npx expo run:ios --device --no-bundler
   ```

   Select the physical iPhone and complete any signing or Developer Mode prompts. This generates native projects locally; do not commit generated projects for this spike.

2. **Local Android build:** with the Android SDK, a connected phone and USB debugging enabled, run:

   ```bash
   EXPO_PLATFORM=native npx expo run:android --device --no-bundler
   ```

   Select the physical phone and accept its USB debugging prompt.

3. **EAS development build:** if using the linked Expo project and an account with build access, run the command for your device:

   ```bash
   npx eas-cli@25.2.0 build --profile development --platform ios
   npx eas-cli@25.2.0 build --profile development --platform android
   ```

   Run only the platform you need. For iOS, EAS may require registering the physical device and provisioning it; follow its prompts. Install the resulting internal-distribution build on that device. `development-simulator` produces a simulator app and does not install on an iPhone. EAS may consume a build credit. The native dependency is included by the package installation; the runtime probe flag will be supplied by Metro next.

Start Metro on the computer, on a network the phone can reach:

```bash
EXPO_PLATFORM=native EXPO_PUBLIC_NATIVE_PIXELS=1 npx expo start --dev-client --clear --lan
```

Open the installed development client and connect using the terminal's QR code. On a fresh disposable profile, finish seed selection and naming, then dismiss any welcome or guide overlays. These global game overlays still run on this development screen. Once it has loaded the project, open `screenagotchi://native-pixels` on that phone. On an iPhone, enter that URL in Safari and accept the prompt to open NapAttack. On a USB-connected Android phone, the exact command is:

```bash
adb shell am start -W -a android.intent.action.VIEW \
  -d 'screenagotchi://native-pixels' me.bilt.appify
```

`screenagotchi` is the current scheme in `app.config.ts`; `me.bilt.appify` is the current default Android package. Substitute the configured package only if you deliberately built with a different `BILT_ANDROID_PACKAGE`. If the link opens the client launcher rather than the project, connect Metro first and open the route link again.

To test the default-off behavior, stop Metro and restart it without `EXPO_PUBLIC_NATIVE_PIXELS`, with `--clear`, then reopen the route. To disable the spike after testing, leave the flag unset. No save migration or cleanup is required.

## Matt: compare crispness, memory and frame time

Record the tested Git SHA, device model, OS, display refresh rate, density, development build identifier and renderer mode. Keep the same viewport, camera locations, display settings and sweep for every comparison. Disable remote JS debugging, close unrelated apps, allow the phone to cool and avoid recording the screen while collecting timings. A development build is required for this spike's requested comparison; it is not a final release-performance benchmark.

1. **Crispness:** compare React Native Image, Skia linear and Skia nearest at the same camera position. Look at high-contrast one-art-pixel details and tile seams, then move the camera across seams. Save native-resolution screenshots without messaging-app resizing. Inspect them at an integer zoom with a nearest-neighbour viewer. Nearest should preserve hard colour boundaries without blended fringe colours or gaps. On a 3-physical-pixels-per-art-pixel setting, the source's two stored pixels per art pixel need not each have equal display widths; judge the authored art-pixel blocks. Repeat on iOS and Android, including a fractional-density Android phone if available.
2. **Warm and cold loading:** inspect the first appearance of each tile, then pan away and back repeatedly. Note blank tiles, seams, flashes, errors and changes in the mounted count. Check the finite sweep and manual pan with reduced motion on and off; background the app and navigate away during a sweep, then return. Motion must stay stopped until explicitly restarted.
3. **iOS memory:** attach Xcode to the physical device's process. In Instruments, use Allocations together with VM Tracker, and inspect the process's physical footprint and graphics-related allocations. Record a stationary warmed sample, peak during a 30-second sweep, and the value after leaving the route and waiting for it to settle. Repeat from a fresh app launch for each renderer so one renderer's cache does not become another's baseline. Save the Instruments trace and record what each reported memory number measures.
4. **iOS frame timing:** use Instruments' Animation Hitches/Core Animation tools on the physical device. Record the same 30-second sweep, frame deadlines and hitches. Use a Metal System Trace where supported to investigate texture uploads or GPU stalls. Report native timing separately from the probe's JS callback intervals.
5. **Android memory:** use Android Studio's Memory Profiler on the debuggable physical-device process, recording Java/Kotlin, native and graphics memory where the device exposes them. Also capture `adb shell dumpsys meminfo me.bilt.appify` at the stationary, sweep-peak and post-exit points. Fresh-launch each mode and repeat the same path. Do not call Java heap size the app's total memory.
6. **Android frame timing:** capture an Android Studio System Trace/Perfetto trace including the app, graphics and FrameTimeline tracks where available. Inspect missed deadlines, RenderThread work and GPU/SurfaceFlinger timing during the sweep. As an additional summary, run `adb shell dumpsys gfxinfo me.bilt.appify reset` before a sweep and `adb shell dumpsys gfxinfo me.bilt.appify framestats` after it. `gfxinfo` can omit work from a separate native rendering surface, so retain the system trace and state the coverage.
7. **Repeat:** take at least three warmed runs per renderer on each platform. Use the phone's actual refresh rate to interpret deadlines (16.67 ms at 60 Hz; 8.33 ms at 120 Hz). Record p50/p95 native frame duration or deadline data as supported by that profiler, hitch counts, peak memory, and run-to-run variation. Do not substitute the on-screen JS p95 for missing native timing.

Keep the captures outside the public repository if they contain device identifiers or personal information. Link a sanitized result or write its measured values here when reporting back to Claude A.

| Platform and device      | Mode                   | Crispness and seams | Native frame timing and hitches | Process memory, peak / post-exit | Evidence |
| ------------------------ | ---------------------- | ------------------- | ------------------------------- | -------------------------------- | -------- |
| iOS, physical device     | React Native Image, 2× | Pending             | Pending                         | Pending                          | Not run  |
| iOS, physical device     | Skia linear, 2×        | Pending             | Pending                         | Pending                          | Not run  |
| iOS, physical device     | Skia nearest, 2×       | Pending             | Pending                         | Pending                          | Not run  |
| Android, physical device | React Native Image, 2× | Pending             | Pending                         | Pending                          | Not run  |
| Android, physical device | Skia linear, 2×        | Pending             | Pending                         | Pending                          | Not run  |
| Android, physical device | Skia nearest, 2×       | Pending             | Pending                         | Pending                          | Not run  |

No new browser-object uses were added, so `scripts/native-safe.json` needs no new entries. The animation callbacks are React Native APIs; the web sibling imports only the existing router.

## Desktop validation

Implementation commit `7474c3f` passed `EXPO_PUBLIC_NATIVE_PIXELS=1 npm run verify` (including iOS Hermes and zero lint warnings), the additional flagged Android export, `npm run check:art-repro` for all eleven generators, and the geometry/2× fixture checks in `check:native-pixels`. The flag-off iOS export also passed before the component boundary was tightened.

Desktop Chromium passed 32 existing screen checks at 320 day/normal and 402 night/reduced. The final web export contains no probe, fixture or Skia code; a route smoke test redirects `/native-pixels` to Home without probe/Skia requests or page errors. The screen harness exercises the existing web game; it does not render the native probe. No native binary was compiled or run here.

## Handoff to Claude A

Keep the candidate off until both platforms have acceptable crispness and profiler results. Claude A supplied the adapter ownership boundary in [issue #149, comment 6302142768](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6302142768), after the first verified spike. C34 now supplies that boundary in `components/pixel-image.tsx` and `components/pixel-image.native.tsx`; `NativePixelTiles` uses it. No existing Claude renderer component is edited.

The shared contract is:

```tsx
type PixelImageProps = {
  source: number; // bundled Metro asset, such as worldTileArt[t.art]
  x: number;
  y: number;
  width: number;
  height: number; // DIPs relative to the layer
  nearest?: boolean; // native default true; web retains its existing CSS path
  onError?: (error: Error) => void;
};
// ONE layer for the mounted ground set, not a layer per tile:
<PixelImageLayer width={viewportWidth} height={viewportHeight}>
  {mounted.map((tile) => (
    <PixelImage key={tile.id} {...tileDipRect(tile)} />
  ))}
</PixelImageLayer>;
```

`PixelImageLayer` is one native Skia canvas. Each native `PixelImage` is a drawing node inside it, not a standalone native view. On the web the layer is a `View` with `data-pixel`, and each image keeps the existing `Image`, `resizeMode="stretch"`, absolute left/top and explicit width/height geometry. The adapter normalizes image errors to `Error` on both platforms.

For #126, Claude A groups the mounted ground images under one viewport-sized layer and supplies snapped rectangles relative to that layer. **Do not replace each `Image` under its existing tile `View` independently:** Skia draw nodes must be under the shared canvas, and one canvas per tile defeats the surface budget. Keep flow, deck, prop and companion layering outside or explicitly inside that single drawing surface as appropriate; verify the complete composition before enabling it. The pinned renderer reviewed for this contract is #126 at `b38bbe27b7fbedfb0610f9f512be529a1b83eb0f`.

The probe convenience component `NativePixelTiles` takes world art coordinates, tile size 256, the snapped camera and `pixelScale` unit, then converts rectangles to DIPs. Supply generated `worldTileArt` imports once #123 is integrated; remove the twelve copied specimens when the probe can read those imports directly. The substituted-boundary adapter check in `check:native-pixels` covers unchanged web geometry, default/linear native sampling, no mipmaps, error forwarding and one surface for twelve images. It is not native runtime evidence.

Keep the web renderer's existing `Image` plus `data-pixel` path. Do not make the world dependent on this development route. Before enabling nearest rendering in the game, check fill tiles, image failure behavior, tile-mount hysteresis and memory retention, moving water/decks, props and tall scenery, clipping and layering, and inactivity/reduced-motion behavior in that complete renderer. A later 1× experiment must regenerate source tiles and repeat device measurements; C34's 2× comparison does not approve a 1× rollout.
