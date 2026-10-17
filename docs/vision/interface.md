# Interface

## Layout: the world is the screen

```
┌──────────────────────────────┐
│ [pet] NAME ♥▬▬  ⛨0:30 ⛬20 3:00 ☰ │  ← GameHud (components/game-hud.tsx), floats on top
│                              │
│   forest band (behind HUD)   │
│   hut · nook · stall         │
│   pond · path · beds         │  ← GardenWorld fills the phone; a camera follows the
│   stream + bridge            │     companion on screens shorter than the map
│   meadow (grows) · orchard   │
│   fence + gate               │
│ [HOME][MISSIONS][ NAP ][ARENA][SHOP] │ ← GameHotbar (custom tab bar), NAP raised in the middle
└──────────────────────────────┘
```

- Home never scrolls. Everything Home used to stack below the garden now lives in a sheet or in the world:
  - **Nap and break ideas:** the NAP sheet (from the hotbar or the bed).
  - **Companion:** the HUD portrait opens the companion sheet.
  - **Deck, journal, feed, rhythm, stats, garden trail, how it works:** the ☰ menu.
  - **Keepsakes:** tap them in the garden.
  - **Guidance:** a "!" marker over the next place (`gardenMarker()`), and the companion's speech bubble.
- Other tabs (Missions, Arena, Shop) are still scrolling `Page`s. Pages pad themselves with `hudClearance()` and `hotbarClearance()` from `lib/layout.ts`. Turning them into places in the world is on the roadmap.
- Sheets: `lib/ui.ts` holds which sheet is open (`nap | menu | companions | rhythm | stats | trail`). `components/game-menus.tsx` renders them all once, beside the tabs. Any open sheet pauses the garden.
- Shared game sheets keep a visible CLOSE button beside the title, above the scrolling content. It uses the same pixel button and 44 px target as the other controls. Backdrop and Escape/Back dismissal stay available; closing the nap sheet discards its unfinished break idea.

## Pixel frames

- `components/pixel-frame.tsx`:
  - `PixelFrame` is a framed surface.
  - `FrameShape` is just the shape, for custom controls.
  - `frameTones` are the colourways: paper, parchment, leaf, gold, nap, danger, night, glass, disabled.
  - `usePixelUnit()` gives the size of one garden pixel on screen (2 on phones, 3 in the wide column), so frames share the world's pixel grid.
- A frame has:
  - notched corners;
  - a 1-unit outline in the shared outline colour;
  - a lit top and left edge, and a shaded bottom and right edge;
  - an optional raised base (`depth`).

  Corners are transparent, so frames sit cleanly over the world.

- Buttons (`PixelButton`) are a raised frame that sinks by its base depth while pressed. There are no rounded corners anywhere: `art/materials.json` geometry radii are 0.

## Type

- One pixel font: **Pixelify Sans** (`PixelifySans_400Regular`, `_500Medium` for body, `_700Bold` for labels and headings). `PixelText` still uses Press Start 2P for large display numbers and titles (16 px and above).
- Keep body copy at 13 to 15 px and labels at 10 to 13 px. Pixel fonts blur at odd sizes, so check them in a screenshot.
- The companion speaks in lowercase (speech bubbles). Interface labels are uppercase.

## Accessibility we keep

- Touch targets of at least 44 px, even where the drawn frame is smaller (use `hitSlop` or padding).
- Every control has a role and a label. Decorative art is hidden from assistive tech.
- Reduced motion: no bobbing, no idle chatter rotation, instant walking.
