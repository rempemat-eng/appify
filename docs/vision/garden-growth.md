# The garden grows

> **Superseded 21 Oct by [game-design.md](game-design.md).** Nothing grows from time away any more; the beds and orchard become the village's crop plots, which grow by outings (its section 7.5).

Time away from the phone visibly changes the world. This is presentation only: it never adds Dream Dust, cards or stats, and nothing ever wilts or goes backwards.

## The meadow

- **Input:** the player's lifetime simulated break minutes (`player.offline_seconds`, which counts simulated minutes).
- **Logic:** `lib/garden-growth.ts`, a pure module tested by `lib/garden-growth.test.ts`.
- **Beds:** six flower beds (tulip, chamomile, lavender) are sown at 10, 30, 60, 100, 150 and 220 minutes. Each then grows a stage every 15 minutes: sown, sprout, leaves, bud, bloom.
- **Orchard:** three orchard pits get a seedling marker at 90, 240 and 480 minutes. A seedling becomes a sapling at +30, a young tree at +120, a grown tree at +300 and a fruiting tree at +600.
- **The sign:** tapping the meadow sign, a bed or a tree walks the companion over. It says what is growing and roughly when the next change comes (`meadowLine()`). The line never sets a target and never nags.
- **Art:** stage sprites come from `scripts/art/garden_meadow.py` (`growth_sprites()`). Bed and pit positions come from the generated map (`gardenPlots`, `gardenOrchard`).

## Ideas for later

- Kept keepsakes could plant something specific: a reading memory grows a little book tree, a rest memory a lantern flower.
- Seasons could change the meadow's palette (they would need the night and season tints planned together).
- A friend's visit could leave a sapling (it needs the social backend; see roadmap.md).
