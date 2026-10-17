# Roadmap

## Now: make it feel like one finished game

1. **Art pass on the rest of the world, using the art-style.md rules.**
   - Moss's stall and the small props.
   - Mission worlds (`worlds.py`) and battle backdrops (`battle.py`), which still use the older, softer style.
   - Companions and visitors: check that their outlines and shading match the new garden.
2. **Missions, Arena and Shop as places, not pages.**
   - Shop becomes the inside of Moss's stall.
   - Missions becomes a world map past the gate.
   - Arena becomes a clearing beyond the fence.

   Same HUD and hotbar, no long scrolling lists.

3. **Pixel frames on every remaining surface:** journal, welcome back, battle HUD, onboarding, guide.
4. **Sound:** soft ambience and small effects (footsteps, splash, page turn).
5. **Real phone testing.** Everything so far is tested in a desktop browser at phone size.

## Next: content

- More visitors and their small stories.
- More mission places.
- Garden decorations unlocked by breaks (cosmetic only).
- Seasons.

## Later

- **Real screen-time:** native builds that use Apple Screen Time and Android's app-usage access, so naps measure actual time away.
- **Friends** (not started; Matt has not yet chosen which first):
  - read-only garden visits;
  - a cooperative grove.

  See companion-roadmap.md for the constraints already written down.

## Decisions made

- **Tone:** cosy (Matt, 16 Oct 2026). Gentle and encouraging, never shaming.
- **View:** top-down 2D only. The 2.5D tilt view was retired from the garden; mission worlds still use the projection code.
- **Layout:** the world fills the screen, with a HUD, a hotbar and menus on top.
