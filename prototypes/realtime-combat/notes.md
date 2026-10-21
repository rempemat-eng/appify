# NapAttack real-time action prototype

Matt, 21 Oct 00:06: "try Real-time action and In-world turn-based (with more special enemies in arenas)". Then, 00:07: "maybe try real time action with a rotated phone". This is the real-time one, built from mock 1 (light action on the field). It is one file, `index.html` (471 KB, every image and both fonts embedded, no network requests). Open it on a phone, upright or turned sideways.

## Controls

| | Touch | Keyboard / mouse |
| --- | --- | --- |
| Walk | Drag anywhere, or start on the soft stick bottom-left. A short drag walks (20 px/s); a long one runs (50 px/s), at the speeds in Bramble's `data.json` | Arrow keys or WASD; mouse drag |
| Loose | Tap a Glare, or press LOOSE (bottom-right) | Space, J or Enter |
| Dodge | Flick (a quick swipe), or press DODGE | Shift, K or L |
| Pause | The pause button, top right (also pauses on its own when the app goes to the background) | Esc or P |

Upright, LOOSE and DODGE sit in the right thumb's arc. Turned sideways, the stick is on the left and LOOSE and DODGE are stacked on the right, for two thumbs. The HUD is in the top corners and keeps clear of the notch on both sides.

## What to look for

1. **The field fight.** Walk south from the hollow oak. Three Glares come in from the screen edges, slowly enough to see them first. Each has a restless bar of 2 or 3 segments. One Glare at a time marks its attack on the ground: a **FLASH** lane fills towards you with chevrons and a dashed rim, or a **PING** ring closes in. Each telegraph lasts 1.15 to 1.45 s, and the beat is one solid brightening, never a strobe. Roll or step out. Calming a Glare turns it gold; it closes its eyes, folds up and drifts off into the trees as a spark.
2. **Stillness becomes strength.** Stand still near a Glare and Bramble draws his bow. You see the draw frames, three Aim pips over his head and a ring at his feet filling in three arcs. When Aim is full, a loosed arrow takes two segments, flies gold and makes a wind-up fizzle. Moving cancels the draw.
3. **Walking away.** The Glares never chase far. Go about 140 px (art pixels) from where the fight began, over the bridge for example, and they lose interest and drift off. Come back and they return.
4. **The arena.** A forester's signpost at the fork points to the stone circle, where the **Static Storm** waits: a knot of Glares round one big screen. Step into the ring and the stones light a dotted boundary, the camera locks on the ring and a boss bar appears. The fight has three phases:
   - **Wound tight** (6 segments): it sweeps a long lane through you, then drops two PINGs at once.
   - **Split**: it throws off three small Glares and raises a violet shield. Arrows bounce off with a "tink" until the three are calmed.
   - **Last gust** (5 segments): it lays a fan across the ring, then PINGs.

   When it is calmed, the storm warms, folds and bursts into fireflies. Bramble plays his victory pose, the Mossling hops, and a card offers Spar again or Walk on.
5. **Getting tired.** At 0 HP (Bramble has 80: 60 + 10 at shared level 2), Bramble flops down and naps, the Mossling curls up beside him, and the Glares drift off. A card says nothing is lost, and Get up restores him. In the arena, the storm winds itself back up. Out of a fight, standing still slowly refills HP.
6. **Feel.** Each hit has an anticipation (the draw), the act (the release frame hands over to a flying arrow) and a settle. On a hit the game holds for 3 to 10 frames, and the screen shakes by one or two art pixels. Dodges leave two fading afterimages and puffs of dust. The Mossling follows a step behind, on Bramble's back side.
7. **Settings (pause menu).** Reduced motion follows the phone's setting and can be toggled. It turns off shake, afterimages, Glare flicker and bob, drifting sparks and confetti, and the dotted ring's crawl. Hit flashes become an outline. There is also Gentle pace (telegraphs 1.5 times longer, slower Glares) and Sound (tiny synthesised blips). Start over and How to play are in the same menu. Choices are kept in local storage when the browser allows it.

## Rendering

The world is drawn at 1 art pixel per pixel into an offscreen canvas and scaled up by a whole number. The scale is 2 CSS px per art px upright and one step in (3) sideways, multiplied by the device pixel ratio and rounded, so it is 6 or 9 device px on a 3x phone. The camera snaps to device pixels. Ground effects (telegraphs, glows, shadows, the Aim ring) are written into one ImageData buffer per frame, so they sit on the same pixel grid as the sprites. Text over the world uses the game's Pixelify Sans at device resolution. The HUD and buttons are DOM elements with `env(safe-area-inset-*)` padding. All touch targets are 44 CSS px or larger (LOOSE 88, DODGE 66 x 58, pause 48, menu rows 48 tall). A Glare's tap area is at least 30 px in radius.

## Testing (Playwright, Chromium from /opt/pw-browsers)

- `test/play.py portrait|landscape [--tired]` plays the whole thing with real touch input (CDP multi-touch). It holds a drag to walk, flicks and presses DODGE when a telegraph covers Bramble, stands still to draw, and alternates between tapping Glares and pressing LOOSE. It walks to the ring and calms the storm through all three phases. Portrait 402 x 874 and landscape 874 x 402, both at 3x with touch emulation, both finished, with no page errors. The `--tired` run lets Bramble drop to 0 HP first and checks the down card and Get up.
- `test/checks.py` checks the frame rate without screenshots running, keyboard walking, mouse drag at 1280 x 800, walking away (the "lose interest" toast), the reduced-motion toggle (shake stays 0), the landscape layout with notch insets of 59 px each side and 21 px at the bottom (HUD, pause and stick sit inside them), and the how-to card in both orientations.
- A selection of the screenshots is in `shots/` (`p-` upright, `l-` sideways), reduced to 256 colours to keep the repository small. The test scripts write the full set there again.
- **Frame rate on this machine:** headless Chromium with software rendering (no GPU) in this container runs at 57 to 60 fps while walking and in the field fight. It dipped to the 40s and 50s only while full-resolution screenshots were being captured, and to around 30 when two test browsers ran at once. This says nothing about a phone.

Bugs found by playing and fixed: rolls into a stone or a fence now turn up to 90 degrees towards open ground; a hit can be rolled out of after 0.22 s; the storm's second PING no longer lands on the first; a split clears the storm's old telegraphs; the pace in phase 2 was too relentless to shoot back; the Mossling sat on Bramble's head when he walked south; Glares lost interest too easily during normal dodging; the end cards covered Bramble.

## What is placeholder

- **No dodge roll frames.** The dodge is a run frame with a 3 px hop, afterimages and dust. Mock 1 counts the roll at about 12 frames.
- **Shooting north or south** uses the east or west attack frames (production only has E and W), and the release hands over to a code-drawn arrow. The arrow pixels on frames 4 to 6 were cut from the frames at build time.
- **The Mossling** uses production familiar frames (BLOB walk, curl and the perch-idle loop as its standing idle). It follows on the ground; it does not ride the shoulder in fights as cast.md describes.
- **Glares** are the first-pass art from `build/lib/glare.py`. **The Static Storm** (`build/storm.py`) and the **signpost** are new pixel art drawn for this prototype. None of them has been checked against the asset ledger or the art-style counts.
- **Telegraphs, the shield, sparks, petals, the arrow and the goal chevron** are drawn in code.
- **Numbers are guesses:** damage 8 to 14, telegraphs 1.15 to 1.45 s, arena gaps 1.2 to 1.6 s, storm 6 + 3 x 2 + 5 segments. A field fight took the bot 20 to 40 s and the arena 50 to 90 s.
- **No rewards** (no Dream Dust, nothing to collect), no daily limit, no save. Sound is a few synthesised tones.
- **The woodland** is rendered from the repo's `assets/zones/woodland/ground.png` and props at 1x, with collision from the zone's walk grid. The water does not animate.

## Bringing it into the real app (React Native, native readiness)

- **Loop and rendering.** This is a single canvas 2D loop. In the app, either use `@shopify/react-native-skia` (a Canvas with `drawImageRect` from atlases, with filter quality none for nearest neighbour), or keep sprites as Views driven by `react-native-reanimated` shared values with a `useFrameCallback` loop, as mock 1's notes suggest. Skia is the closer match to this code: one atlas per actor and per-pixel telegraphs as small images or paths. Either way, a frame-time spike on a mid-range Android comes first.
- **Input.** Pointer events map to `react-native-gesture-handler`: Pan for the floating stick (simultaneous with button taps for two thumbs), Fling for the dodge, and Tap on Glares through the same 30 px hit test. Keyboard is web only.
- **Browser objects.** This file uses `document`, `window`, `localStorage`, `matchMedia`, `AudioContext` and `visibilitychange`. In the app these become, respectively: RN components; `useWindowDimensions`, with `useSafeAreaInsets` replacing `env()`; the game store or AsyncStorage for settings; `AccessibilityInfo.isReduceMotionEnabled`; expo-av sounds; and `AppState`. Any web-only pieces go behind `Platform.OS === 'web'` and are recorded in `scripts/native-safe.json`.
- **Assets.** The atlases and fonts are data: URIs here only to keep one file. In the app they are bundled with `import`. The build script (`build/build_assets.py`) shows how each is cut from the character pipeline's output and the zone PNGs.
- **Rules.** The simulation (`step`, foes, telegraphs, arrows) is plain functions over one state object, with no DOM. It could move into `lib/` as a pure module with a fixed 60 Hz step and be tested in the same harness style as the garden checks. The deterministic parts are timing and damage; the Glares' wander and attack picks use `Math.random` and would need a seeded random for tests.
- **Not tested:** any real phone, iOS Safari's address bar and gesture quirks, the native app, real latency on touch screens, battery, and how two thumbs actually feel sideways. Everything here comes from desktop Chromium with touch emulation.

## Files

- `index.html`: the prototype.
- `build/`: `build_assets.py` (packs the art into `build/assets.json`, which is not kept in the repository), `storm.py` (the Static Storm), `lib/` (the mock kit it draws with: the Glare, icons, zone reader), `template.html` (the game source), `build.py` (inlines everything). After editing `template.html`, `python3 build/build.py` rebuilds `index.html`, taking the packed art from the current `index.html`. Re-packing the art needs the character pipeline's output: see `../README.md`.
- `test/`: `play.py`, `checks.py`.
- `shots/`: a selection of the screenshots from the runs above.
