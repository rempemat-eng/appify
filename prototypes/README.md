# Fight prototypes (archived)

Two playable fight prototypes from 21 Oct, kept for reference. **Neither is part of NapAttack's build.** NapAttack's fights stay Pokémon-style: today's separate battle screen with turn-based cards (Matt, 21 Oct 10:03; `docs/vision/fights.md`, "Decision").

| Folder | What it is | Status |
| --- | --- | --- |
| [`realtime-combat/`](realtime-combat/notes.md) | Real-time action on the woodland path: Bramble walks, dodges and looses arrows at Glares, then calms the Static Storm in the stone ring. Upright or turned sideways on a phone. | **Kept for a possible spin-off game** (Matt, 21 Oct 10:03: "i might want to create a spin off game, so save the live action combat system somewhere"). |
| [`inworld-turns/`](inworld-turns/notes.md) | Turn-based fights on the world's own ground: the camera zooms in where you meet a Glare, cards on a ring under the thumb, terrain spots, a timed tap. | Superseded design, kept as a record. |

Each folder's `notes.md` gives the controls, what to look for, how it was tested, what is placeholder and how it could move into a React Native app.

## Open one

Each prototype is one self-contained file, `index.html`, with every image and font embedded and no network requests. Open it in a browser (`file://` works), or serve the folder and open it on a phone:

```sh
python3 -m http.server -d prototypes/realtime-combat 8000
```

## Rebuild one

- **After editing the game code** (`realtime-combat/build/template.html` or `inworld-turns/src/index.src.html`): `python3 prototypes/realtime-combat/build/build.py` or `python3 prototypes/inworld-turns/tools/assemble.py`. Without a packed `assets.json`, both take the embedded art and fonts from the current `index.html`, so no other files are needed. Run on the committed sources, both give back the committed `index.html` byte for byte.
- **Re-packing the art** (`realtime-combat/build/build_assets.py`, `inworld-turns/tools/build_assets.py`, then the step above) reads the woodland zone, icons and fonts from this repository (or `NAPATTACK_REPO`, with `node_modules` installed) and Bramble's and the Mossling's frames from the character pipeline's `out/` folder, which is not in the repository yet: set `NAPATTACK_CHARART` to it. The mock kit the scripts draw with is in `build/lib/` and `tools/lib/`. On 21 Oct, re-packing with the pipeline's output gave back the committed `index.html` byte for byte from the commit the prototypes were built on (`3be7d88`), and the same pictures pixel for pixel from main at `1171a9e` (only the ground's PNG encoding differs). Main's woodland may change or be retired later; the committed `index.html` files keep the art they were built with. `assets.json` and `__pycache__/` are ignored.
- **Play-tests** (`realtime-combat/test/`, `inworld-turns/tools/play.py`) use Python Playwright with Chromium and write screenshots to `shots/`. Only a few screenshots are committed, reduced to 256 colours.

## The art in them

Every picture in both prototypes is NapAttack's own art, checked on 21 Oct: the woodland ground and props are the repository's `assets/zones/` files (identical to main at `1171a9e`), Bramble and the Mossling come from NapAttack's character pipeline, the icons and card art from `lib/icon-art.ts` and `lib/card-art.ts`, and the Glares, the Static Storm and the signpost were drawn by the scripts here. No other game's art or screenshots are included. The fonts are Pixelify Sans and Press Start 2P (SIL Open Font License), the same packages the app uses. Glares, the Storm and the signpost are first-pass mock art, not checked against the asset ledger.

## Kept out of the app

The folder is excluded from `tsc` (`tsconfig.json`), oxlint (`.oxlintrc.json`), oxfmt (`.oxfmtrc.json`), Metro (`metro.config.cjs` block list) and the asset ledger's file walk (`scripts/check-assets.cjs`). `check:native` and `check:images` only read the app's source folders (`app/`, `components/`, `lib/`, and `hooks/` for `check:native`). The web export copies only `public/` and the bundle, so nothing here ships. Do not import from this folder into the app; port what is needed instead, as each `notes.md` describes.
