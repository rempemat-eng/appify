# World clock data (Y8)

slot=prism. `game/core/world_clock.gd` supplies presentation-time data and a
`changed(snapshot)` hook for the future X3 routine consumer. Existing Godot
villagers select idle/work/talk from proximity; there was no clock or weather
model to extend. Their code and behaviour remain unchanged.

The current development plan authorises Y8; the living-world plan makes
atmosphere presentation only. Neither defines the Godot cycle length, phase
boundaries or weather probabilities. `WorldClock.configure(period, phases,
weather, elapsed)` therefore requires those inputs explicitly. The synthetic
60-second day/night cycle in tests is a test fixture, not a production setting.
No clock is installed as an autoload, no scene advances it, and no save fields,
rewards, combat timers, progression, lighting or weather art change.

`period` is positive finite presentation seconds per cycle. `phases` is a
nonempty ordered array of dictionaries with unique nonblank string `id`s and
finite `at` fractions: the first starts at zero, subsequent starts strictly
increase below one. Ranges include their start and exclude the next start.
Weather is an explicit nonblank identifier; this model assigns no probability
or gameplay meaning to it. Additional phase metadata is copied, never mutated.

`snapshot()` returns a detached dictionary with `day` (zero based), `time`
(seconds within the cycle), `fraction`, `phase`, `weather` and `active`.
Unconfigured clocks return an empty dictionary. `advance(seconds)` takes an
explicit nonnegative delta. `set_active(false)` discards subsequent deltas;
resuming never catches up a backlog. `seek(elapsed)` deliberately supports
external samples and preview rewinds even while inactive. `set_weather(id)`
changes weather explicitly. Each real state change emits one final snapshot;
coarse jumps do not replay every crossed phase or day. An X3 consumer should
select its current routine from that sample, rather than count transition events.

Malformed/nonfinite inputs, time beyond the exactly representable day-index
range (less than 2^53−1 cycles), or advances too small to change the stored float
return false with `last_error`, preserving state and emitting no change. Those
are numerical admission limits, not game balance. Callers must handle refusal.
Valid no-op calls clear `last_error` without emitting a signal.

The existing `check:godot` discovers `game/test/test_world_clock.gd`. It covers
boundaries, wrap, coarse steps, pause/resume, explicit weather, signal/input
isolation, invalid configuration and numerical limits. Production period and
phase/weather data, X3 routine wiring, persistence, wall-clock synchronisation,
rendering, gameplay, phone/native and long-duration soak testing remain outside
this data-model step. Claude A decides those integration inputs and reviews it.
