# Art pipeline

How NapAttack's art is made, so it stays consistent and nothing gets cut off. Read this before drawing or placing anything. The rules for how things should look are in `art-style.md` and `coherence-plan.md`.

## Sources

- **Generators** in `scripts/art/` draw every sprite from the shared material ramps in `art/materials.json`: light from the upper left, clean planes, material-tinted outlines. Run one with `python3 scripts/art/<name>.py`, then `npx oxfmt --write` the TypeScript it generates. Never edit generated PNGs or generated `lib/*-map.ts` files by hand.
- **Layouts** (where props stand) live in the generators for now (`OBJECTS` in `garden.py`). A level editor such as [LDtk](https://ldtk.io) can take over later: the generator would read its JSON export, so Matt can move props himself.
- **Hand touch-ups** (planned): a sprite may get a hand-painted override PNG made in Aseprite or Pixelorama. Overrides go through the same checks.

## The sprite contract

1. Draw on a **padded** canvas (`Canvas(w, h, pad=PAD)`). Art may stray past its nominal box; nothing is dropped.
2. `style.finalize(canvas, name=...)` gives the art its complete tinted outline in a free pixel of room, then **trims** it to the art and records the offset (`ox`, `oy`) of the trimmed top-left from the nominal origin. Placement adds the offset.
3. If art reaches the edge of the padding, finalize **fails**: drawing really was cut off.
4. Fixed boxes (meadow growth stages anchored to a bed) use `keep_size=True`: the art must leave room for its outline inside the box, except along the ground row.
5. The garden generator fails if an object sticks out above the map's top band (`TOP`).

## Scale and export

- One art pixel is the game's shared pixel (`lib/pixel-scale.ts`): a whole number of device pixels, about 300 art pixels across a phone (4 device pixels, 1.33 CSS px, on a 3x phone). The world, the characters, the frames and the icons all use it.
- The garden is exported at 4x (one image pixel per device pixel on a 3x phone). Other folders are still 6x until step 7 moves them.
- Only animated parts animate: the garden ground is one still image; the stream and pond are small four-frame overlays (`gardenWater`).
- Shadows and contact shading are baked into the ground, so depth costs nothing at runtime on a phone. An animal that wanders is the exception: its shadow is its own small picture (`<sprite>_shade`) that walks with it.

## Animals that live

Every placed animal has an idle loop and, if it moves, a short wander (art-faults.md A9). `scripts/art/animal_frames.py` holds the kinds (`KINDS`: the still drawn facing each way, the idle accents, the two walk frames, where it may go: ground, water, the shallows, or nowhere) and writes `zoneAnimals` and `zoneAnimalSpots` into `lib/zone-maps.ts`; `components/atlas-animals.tsx` plays them on the walk's shared clock, still with reduced motion or an inactive screen.

- **Frames** are named `<still>_<role>`: `sheep_look`, `sheep_chew`, `sheep_step1`, `sheep_step2`; the other facing has its own still with the same roles (`sheep_left_look` ...). Draw both facings lit from the upper left; never rely on mirroring.
- **Drawing them by hand**: a module that returns a frame under one of these names (in its `props()`) replaces the derived one. Until then `animal_frames.frames()` derives frames from the still (the head moved, a leg stepped, the tail swished), which is a stopgap for stills drawn without frames. The cat (`zones.CAT_POSES`) and the ibex (`frost_props.IBEX_POSES`) are drawn from region masks shaded by `animal_frames.paint_mask`, so their west sides are drawn, not mirrored.
- **Where they go** is chosen by the generator from the walk grid and terrain: a few spots within the kind's `reach`, with the feet clear of props, water (unless it swims), walls and cliffs all along the way; `lib/animal-life.test.ts` checks every loop and way again. Their home spot and the walk grid do not change.

## Checks

- `npm run check:sprites`: every silhouette is outlined on every side (garden, growth, mission props, icons).
- `npm run check:art`: material ramps, card art and world identities.
- `npm run check:garden`: geometry, reachability and hit areas against the generated map and the real pixel scale.
- Codex queue C6 adds a CI check that regenerating the art changes no files; C7 adds an image-memory report.
