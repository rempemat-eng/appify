# Matt's decisions, 13 November 2026

Matt gave these between 12 and 14 Nov, after playing the first night; each carries its date. They stand until he changes them, and they override older text where the two disagree, `decisions-2026-11-11.md` included. AGENTS.md carries the process rules. Claude A recorded them here on 15 Nov; the wording is a summary, not a quotation.

**Three kinds of line are on this page.** A line with a date is Matt's. A line marked "Claude A's reading, not yet confirmed by Matt" is not his: it is how Claude A reads his answers, and it binds nobody until he confirms it. A line marked "from Claude A's brief, with no date of Matt's given for it" was handed on as his answer without a date; treat it as unconfirmed too until its date is added.

**None of this is built yet.** This page records the decisions and what each one needs. The first night on main still plays as `vertical-slice.md` ("The first night as built") describes it.

## The first night

- **(a) A broken shard lantern (Matt, 13 Nov).** If the raiders break the shard lantern, the lantern goes dark and the square looks worse until a night is held. No progress and no Glint is lost.
- **(b) The bell tower comes later (Matt, 13 Nov).** The bell tower is rebuilt later, and its bell is rung for the wolf moon. From Claude A's brief of 15 Nov, with no date of Matt's given for it: the first night is signalled by Hale striking her anvil, not by a bell.
- **(c) A one-off.** From Claude A's brief of 15 Nov, with no date of Matt's given for it: the first night happens once. **Claude A's reading, not yet confirmed by Matt:** raids return only as story sieges, once more shards are home, and Hale says so when the night is won.
- **(d) The bell tower as a purchase.** **Claude A's reading, not yet confirmed by Matt:** the bell tower is the slice's one optional Glint purchase. From Claude A's brief of 15 Nov, with no date of Matt's given for it: its cupola is drawn, so that paying visibly changes the square.

## The world

- **The Frostline is parked as a lab (Matt, 12 Nov).** It is not part of the slice. Its entrance stays at the woodland's north edge.

## How work runs

- **Matt plays on a Mac (Matt, 14 Nov).** The build he judges by eye has to run there.

## Still open

- **A four-position day and night cycle**, after the slice. Matt asked the question; nothing is decided.
- The items left open on 11 Nov (the game's final name, the Codex set-up in section 9 of the plan PR #461).

## Follow-up

What each line above needs before it is true in the game. Nothing here is started by this page, and the parts that follow from a reading of Claude A's (the story sieges in (c), the purchase in (d)) wait for Matt's word first.

- **(a) The dimmed shard.**
  - Rules: `game/core/raids.gd` (the `lost` state and its `repairs`, which today clear on the next walk into town: the dimmed square has to last until a night is held), `game/world/raid_night.gd`, `game/world/raid_lantern.gd`, `game/data/raids/first_night.json` (`repairs`).
  - Words: the loss card and Hale's lines in `game/data/dialogue/raids.json`, and the shard lantern's own line there.
  - Art: a dimmed state of the lit lantern, and the square "looking worse" (the two repairs are still flat blockout colours), in `game/zones/crossroads/art/` through the village module, each through the asset gate.
  - Tests and routes: `game/test/test_raids.gd` (nothing is taken: Glint, quests and restores are unchanged by a loss), and a route that loses the night, since `first_night.txt` only wins it.
  - Docs: `vertical-slice.md`, "The first night as built", point 6.
- **(b) The anvil.**
  - Words: the prepare screen's "Ring the bell" (`game/ui/raid_screen.gd`), Hale's "Ring when you're ready" (`raids.json`), the notice board's note in `game/data/dialogue/crossroads.json`, beat 8 of `vertical-slice.md` and `docs/godot.md` ("Raids").
  - Routes: `game/tools/routes/first_night.txt` presses the button by its text.
  - Art and sound: Hale striking the anvil (a clip for the cast's Hale, at her anvil by the forge), and an anvil cue in the sound set in place of a bell.
  - Left as it is: act 1's *The wolf moon* (`game/data/quests/a1_the_wolf_moon.json`, `a1_valley.json`) keeps the bell, which is what this decision says.
- **(c) A one-off.**
  - Words: Hale's line when the night is won (`raids.json`) says today that the bell will let them "hear the next lot coming". It has to say that raids come back only as story sieges, once more shards are home.
  - Rules: `game/core/raids.gd` already never offers a won raid again. No rule changes; a test in `test_raids.gd` should hold it.
  - Docs: the opening paragraph of `vertical-slice.md` ("raids that come from earned attention") and section 7.6 of `game-design.md` describe recurring raids.
- **(d) The bell tower.**
  - Data: the offer in `game/data/raids/first_night.json` (`reward.offers`, `bell_tower`, 50 Glint) and a site for its mark in `game/data/plans/crossroads.json`. *The wolf moon*'s first step is `restore:bell_tower`; it needs a `done_if` so a tower paid in the slice still counts.
  - Words: `restore_bell_tower` and `bell_tower` in `game/data/dialogue/a1_valley.json`, and Hale's offer in `raids.json`.
  - Art: the library's cupola in two states, empty and with the bell hung, drawn by the village module (`game/tools/gen_village.py`, `scripts/art/kit/`), through the asset gate.
  - Numbers: it is optional, so the story model (`game/test/story/test_story_model.gd`) must still finish with and without it. With every quest, restore and fight of the slice done the purse is 106 Glint (76 after the apothecary, and the night's 30), or 56 with the tower.
- **The Frostline as a lab.** `game/data/zones.json` does not register it, and the closing lead and card in `game/data/leads.json` hold while `zone_built:frostline` is false. When it comes back its door goes at the woodland's north edge (`game/zones/woodland/`), which today has no door there.
- **A Mac build.** Main has no export presets yet, and the packaging draft #464 covers Windows and Linux only. A weekly build Matt can play needs a macOS one.
- **Day and night.** Only the question is recorded. `game/core/world_clock.gd` and `game/data/sun.json` are where an answer would land.
