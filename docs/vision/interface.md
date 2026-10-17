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
- Forms and pickers (the companions picker, the rhythm editor) instead pin their DONE or CANCEL/SAVE actions below the scrolling content. Do not add a second header CLOSE to them; the rule is one visible way out that never scrolls away.

## Pixel frames

- `components/pixel-frame.tsx`:
  - `PixelFrame` is a framed surface.
  - `FrameShape` is just the shape, for custom controls.
  - `FrameFill` draws the frame behind an existing View, Pressable or Animated.View. Put it first among the children and remove the parent's border and background. `fill` and `outline` derive a tone for one-off colours (`toneFrom()`), `inset` gives a recessed well (art wells, tracks, tab bars), and `depth` adds the raised base.
  - `PixelSwitch` replaces React Native's `Switch` and `PixelInput` replaces a bare `TextInput` (a recessed well with a gold focus ring). Do not use the native switch or a bordered text box.
  - `PixelTail` is the stepped speech-bubble tail.
  - `frameTones` are the colourways: paper, parchment, leaf, gold, nap, danger, night, glass, disabled, field and fieldFocus (inputs), and lantern (night panels with a gold rim).
  - `usePixelUnit()` gives the size of one garden pixel on screen (2 on phones, 3 in the wide column), so frames share the world's pixel grid.
- Every surface uses these frames: sheets, panels, cards, chips, toggles, inputs, the journal, the battle HUD, onboarding and the nap screen. The old `panelStyle` (a border with a soft shadow) is gone. Straight one-colour borders remain only around scene art and in-world details.
- Inner tiles (choices, tabs, rhythm windows) use the softer `c.outline` brown; outer panels and buttons use the near-black outline. This keeps the hierarchy readable.
- On the web, an absolutely positioned frame paints above unpositioned siblings. `public/index.html` therefore gives `svg`, `input` and `textarea` `position: relative`. Keep that rule, and wrap any other unpositioned content in a View.
- In source-level harnesses, `@/components/*` imports are placeholders. Inside a component that a harness renders (ScreenOff, Home, the visitor and rhythm cards), use `<FrameFill />` as an element rather than calling `usePixelUnit()` directly.
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
- Pixel switches keep switch semantics and work with pointer, Enter and Space on web. Space must not scroll the sheet or toggle repeatedly while held; native presses stay with Pressable. `npm run check:pixel-controls` covers the emitted web handler, not browser or device event dispatch.
- Reduced motion: no bobbing, no idle chatter rotation, instant walking.
