# Roadmap

> The order of work now lives in [development-plan.md](development-plan.md) (27 Oct). The lists below are kept for history.

## Now: make it feel like one finished game

The work in progress follows [coherence-plan.md](coherence-plan.md) (Matt's review of 17 Oct): layering and outline fixes (done), an interface system with symmetric insets and a type hierarchy, a detailed pixel icon set, a Stardew-style tabbed game menu, a denser pixel grid with the garden and worlds redrawn at proper proportions and cleaner shading, readable characters, and the mission map as a place.

1. **Art pass on the rest of the world, using the art-style.md rules.**
   - Done (17 Oct): garden, hut, stall, signpost, trees, pines, bushes, rocks, ground, shadows, mission worlds.
   - Also done: battle backdrops (framed by shared-style trees), scene vignettes (hard shadows).
   - Checked: companions and visitors already use a near-black outline and five-tone shading, so they fit.
2. **Missions, Arena and Shop as places, not pages.**
   - Shop becomes the inside of Moss's stall.
   - Missions: first departure-map pass (17 Oct), with three reused landmarks, one selected outing and pinned launch controls. Phone/landscape/increased-text visual checks remain pending; this is not a walking overworld.
   - Arena becomes a clearing beyond the fence.

   Same HUD and hotbar, no long scrolling lists.

3. **Pixel frames on every remaining surface.** Done (17 Oct): journal, welcome back, battle HUD and cards, onboarding, guide, rhythm editor, companion picker and nap screen now use `FrameFill`, `PixelSwitch` and `PixelInput`.
4. **Sound.** First pass done (17 Oct): a generated palette of soft effects plus day and night garden ambience, with two switches in the guide (see sound.md). Next: tune by ear on a phone.
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
