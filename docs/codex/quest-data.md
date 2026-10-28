# Quest and dialogue data checks

Run `npm run check:quests`, or just the read-only CLI:

```sh
python3 -m scripts.narrative.validate
python3 -m scripts.narrative.validate --root /path/to/game
```

The default root is this repository's `game/`. The checker reads the immediate
JSON files in `data/quests/` and `data/dialogue/`, matching the two existing
autoloads. It never writes authored data or saves. A finding includes its source
file, JSON location, code and explanation; any finding makes the CLI exit 1.
Missing directories, unreadable/invalid JSON and duplicate object keys fail
cleanly. Output is deterministic.

`check:quests` runs the dedicated regression suite and validates every authored
file. It is part of `npm run check`, so ordinary `verify` CI runs it too. No new
Python package is needed.

## Existing runtime contract

This tool extends `game/core/quests.gd` and `game/core/dialogue.gd`; it does not
replace either. At introduction, the corpus has 20 quest files, six dialogue
files, 35 merged speakers and 149 dialogue entries. Existing Godot quest tests
exercise events, completion, rewards and dialogue selection.

Quests have unique nonempty IDs and a nonempty sequence of uniquely named
steps. The checker validates known field shapes, quest/step references and the
speaker of every `talk:<id>` event. Other event strings, flag names and restore
IDs remain open to world scripts; the tool does not invent a producer registry.
Opaque extension metadata is allowed. The supported condition operators are
exactly those in `Quests.check`: `flags`, `not_flags`, `done`, `active`,
`not_started`, `step`, `restored`, `not_restored` and `glint_at_least`.
Misspelled operators fail instead of silently becoming ignored guards.
Known numeric fields must be integral and survive Godot's JSON float64/int64
conversion exactly. Priorities must also have a representable negated sort key;
the minimum int64 value overflows in the runtime's descending-priority sort.

A quest step completes through its event and `if` condition **or** its separate
`done_if`. The checker preserves both alternatives. A quest with no declared
start event may be started by the existing public `start_quest` API. Dialogue
speaker IDs may occur in multiple files: files merge alphabetically, then
entries sort by descending integer priority, retaining their original order on
ties. A missing fallback, empty lines array, or blank/whitespace strings is valid.
`talk` still sends its event
when no lines match.

## What reachability establishes

The quest analysis starts from fresh `none` states and computes possible
progress through the declared sequential steps. A start sees its own quest in
`none`; a completion sees its own exact active step. This detects self-state
contradictions, missing completion routes and prerequisites that deadlock
normal event-driven progression. It does not guess which world events can fire,
whether an external flag will be produced, or whether the player can afford a
particular action. Script-started quests remain possible.

The analysis keeps a union of possible states, including states that could come
from different playthroughs. It can therefore miss a historical deadlock; it
does not call unknown external state impossible. Direct scripted quest starts,
legacy saves, actual world navigation and a whole-game playthrough are outside
this fresh-state proof.

Dialogue analysis checks contradictory conditions and whether the **union** of
earlier merged conditions covers every state matching a later entry. Quest
states are exclusive; a specific step implies active, and higher Glint
thresholds imply lower ones. Missing/null conditions and `{}` differ exactly as
they do in the runtime: an object with no threshold still tests Glint >= 0,
whereas a missing condition returns true immediately. Negative legacy Glint is
kept possible. Complex branch analysis has a bounded budget; exhausting it
conservatively leaves a branch possibly reachable instead of reporting a false
shadowing error.

Structural/reference errors are reported across all files first. They must be
fixed before semantic graph analysis runs. Passing this checker establishes
data consistency under these rules; it does not approve story, rewards, art,
game balance or a rendered/native playtest.
