# Matt's decisions, 13 November 2026

Matt gave these between 12 and 14 Nov, after playing the first night; each carries its date. They stand until he changes them, and they override older text where the two disagree, `decisions-2026-11-11.md` included. AGENTS.md carries the process rules. Claude A recorded them here on 15 Nov; the wording is a summary, not a quotation.

**Two kinds of line are on this page.** A line with a date is Matt's. A line marked "Claude A's reading, not yet confirmed by Matt" is not his: it is how Claude A reads his answers, and it binds nobody until he confirms it.

**What is built.** The anvil's cue for (b) is on main since #487 (`raid_anvil`, played when the night begins; `raid_bell` is kept, unplayed, for the wolf moon). #492 builds (a), the rest of (b) and Hale's line for (c), in rules and words with no new art: a lost night leaves the shard lantern dark and the square looking worse (the two repairs stay) until a night is won (the save flag `shard_lantern_dark`), with no Glint lost (going down in a night leaves no cache), the prepare screen, Hale and a card call the night from her anvil, and Hale says it was the one night. Not built: the art in (a)'s follow-up (a drawn dimmed lantern, the repairs), the bell tower's cupola and its place as a purchase in (d), and everything under "The world" and "How work runs". `vertical-slice.md` ("The first night as built") describes the night as it plays.

## The first night

- **(a) The shard dims until held (Matt, 13 Nov: "Shard dims until held").** If the first night is lost, the shard lantern goes dark and the square looks worse until a night is won. No progress and no Glint is lost, and the night can be tried again.
- **(b) Hale's anvil signals (Matt, 13 Nov).** The first night is signalled by Hale striking her anvil, not by a bell. The bell tower is rebuilt later, and its bell is rung for the wolf moon.
- **(c) A one-off, and Hale says so (Matt, 13 Nov).** The first night happens once, and Hale says so when it is won. **Claude A's reading, not yet confirmed by Matt:** raids return only as story sieges, once more shards are home, and Hale says so when the night is won.
- **(d) The bell tower as a purchase.** The bell tower is optional, and its cupola is drawn, so that paying visibly changes the square (Matt, 13 Nov). **Claude A's reading, not yet confirmed by Matt:** the bell tower is the slice's one optional Glint purchase.

## The world

- **The Frostline is parked as a lab (Matt, 12 Nov).** It is not part of the slice. Its entrance stays at the woodland's north edge.

## How work runs

- **Matt plays on a Mac (Matt, 14 Nov).** The build he judges by eye has to run there.

## Still open

- **A four-position day and night cycle**, after the slice. Matt asked the question; nothing is decided.
- The items left open on 11 Nov (the game's final name, the Codex set-up in section 9 of the plan PR #461).

## Follow-up

What each line above needs before it is true in the game, with what is built since said at each (see "What is built" above). This page starts nothing itself, and the parts that follow from a reading of Claude A's (the story sieges in (c), the purchase in (d)) wait for Matt's word first.

- **(a) The shard dims until held.** Built in #492 except the art: the flag, the dark glass (the struck pane laid over the lit picture, and the unlit picture's own pixels round it; no new drawing), the repairs staying until a night is won, no cache of Glint for going down in a night, the words, the tests and the route `first_night_lost.txt`. What follows is what it needed.
  - Rules: `game/core/raids.gd` (the `lost` state and its `repairs`, which before #492 cleared on the next walk into town; they now last until a night is held), `game/world/raid_night.gd`, `game/world/raid_lantern.gd`, `game/data/raids/first_night.json` (`repairs`).
  - Words: the loss card and Hale's lines in `game/data/dialogue/raids.json`, and the shard lantern's own line there.
  - Art: a dimmed state of the lit lantern, and the square "looking worse" (the two repairs are still flat blockout colours), in `game/zones/crossroads/art/` through the village module, each through the asset gate.
  - Tests and routes: `game/test/test_raids.gd` (nothing is taken: Glint, quests and restores are unchanged by a loss), and a route that loses the night (`first_night_lost.txt`), since `first_night.txt` only wins it.
  - Docs: `vertical-slice.md`, "The first night as built", point 6.
- **(b) The anvil.** Built: the cue in #487; in #492 the words below except the notice board (reworded in #491) and a card and a spark at the anvil when the night is called. No new clip of Hale was drawn: her work clip already hammers at the anvil.
  - Words: the prepare screen's "Ring the bell" (`game/ui/raid_screen.gd`), Hale's "Ring when you're ready" (`raids.json`), the notice board's note in `game/data/dialogue/crossroads.json`, beat 8 of `vertical-slice.md` and `docs/godot.md` ("Raids").
  - Routes: `game/tools/routes/first_night.txt` presses the button by its text.
  - Art and sound: Hale striking the anvil (a clip for the cast's Hale, at her anvil by the forge), and an anvil cue in the sound set in place of a bell.
  - Left as it is: act 1's *The wolf moon* (`game/data/quests/a1_the_wolf_moon.json`, `a1_valley.json`) keeps the bell, which is what this decision says.
- **(c) A one-off.** Built in #492: Hale's line says it was the one night and they will not come again for this light (Matt's answer), and `test_raids.gd` holds that a won night is never offered again. It does not speak of story sieges, which is the unconfirmed reading. The docs named below are not changed.
  - Words: Hale's line when the night is won (`raids.json`) said, before #492, that the bell will let them "hear the next lot coming". Under the reading it would have to say that raids come back only as story sieges, once more shards are home.
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
