# Matt's decisions, 11 November 2026

Matt answered these on 11 Nov (09:45 to 10:00, London). They stand until he changes them, and they override older text where the two disagree. AGENTS.md carries the process rules.

## How work runs

- **Order of work.** Finish the three-zone slice (woodland, Crossroads, Undercroft) before any new region: land the open PRs, then art for the slice, then polish (sound, phone playtests). The Brackens stays a lab zone until the slice is done.
- **Art review rounds.** The Eastward bar is unchanged. An asset gets at most 3 independent audit rounds. After the third, Matt decides by eye from a side-by-side sheet.
- **Art merges.** Claude A merges art that passes the independent asset and scene gates. Matt judges looks by playing a weekly build; anything he dislikes is reverted or redrawn. He no longer approves each art PR.
- **`game/actors/player.gd`** may be edited. One stream at a time edits it, and the combat auditor checks feel with real input.
- **The old screen-time app** (the Expo web app) is archived on a git tag and removed from main.
- **The name.** "MyGame" stays the placeholder for now. "NapAttack" goes everywhere it is current (project name, save folder, titles, docs that describe the game today). Saves made under the old folder are carried over, never lost.
- **The choked well** stays as recorded: the lantern clears it. Draft #469 is closed.

## Combat

- **Low cover.** A melee enemy blocked by a low solid walks round it. Arrows still fly over low solids.
- **Mossling** health goes from 3 to 5. Fight Glint stays 2.
- **The Thornback** heals to full 3 s after the player leaves its arena, like every other enemy at home.
- **The glance rule stays.** An arrow from beyond an enemy's reach does no harm. It must read as a miss: a spark, a clink mark and, once sound exists, a sound.

My own calls (Claude A), within these rulings:

- **The creature leash line.** A creature's committed wind-up and strike finish even across its leash, and an enemy the player has hurt (elite, shield, rusher, mossling alike) keeps coming across its leash for up to 3 s after the last hurt (the mossling's `PROVOKED_TIME`), then goes home. It never leaves its zone, and the give-up after 2.5 s without progress still applies inside those 3 s.
- **Columns stay solid**: dead spots behind them both ways, as on main.
- **The downed cache keeps "carried"** Glint (20 % of what the player carries).
- **The 1.6 run-in stays**: an enemy woken by a shot runs in 1.6 times as fast until its first wind-up.

## The world

- **The forge** paid before Hale is home shows a dark hearth until she arrives. An ember drawing goes into the art queue.
- **The hut rest** is free and unlimited.
- The raised beds stay walkable (Claude A's call; Matt did not object).

## Already decided on 10 Nov

These came with "i approve your suggestions":

- Downed cache at 20 % of carried Glint.
- Glint from fights: 2 a mossling, 3 an Undercroft creature, 10 the Thornback, each paid once.
- No healing while walking home; full health 3 s after home; a hit wakes an idle enemy within 330 px.
- Hut rest.
- The Thornback's safe zone closed.
- The seal plate moved off the door-lever line.
- Ghosting the player behind tall things.
- Arrows over low solids.
- The generators stay for the three slice zones, and the Brackens' first screen is built as a lab zone.

## Still open

- The game's final name.
- The Codex set-up in section 9 of the plan PR #461.
- Approving the 264 library pieces. This now runs through the asset gate with the 3-round cap above.
