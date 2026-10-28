class_name WorldClock
extends RefCounted
## Presentation data for future routine consumers. Callers supply the cycle and phases;
## this object reads no wall clock, save, scene or gameplay state.

signal changed(value: Dictionary)

const MAX_EXACT_DAY := 9007199254740991.0
var last_error := ""
var _period := 0.0
var _elapsed := 0.0
var _weather := ""
var _active := true
var _phases: Array[Dictionary] = []

## Phases are ordered {id: String, at: fraction}, starting at zero. All values are
## explicit integration inputs; no production day length or weather policy is chosen here.
func configure(period: Variant, phases: Variant, weather: Variant, elapsed: Variant = 0.0) -> bool:
	if not _number(period) or float(period) <= 0.0:
		return _reject("period must be finite and positive")
	if not _valid_time(elapsed, float(period)):
		return _reject("elapsed time is outside the finite, exact-day range")
	if not _identifier(weather):
		return _reject("weather must be a nonempty identifier")
	if not phases is Array or phases.is_empty():
		return _reject("phases must be a nonempty array")
	var next: Array[Dictionary] = []
	var ids := {}
	var previous := -1.0
	for entry in phases:
		if not entry is Dictionary or not _identifier(entry.get("id")) or not _number(entry.get("at")):
			return _reject("each phase needs an identifier and finite numeric at fraction")
		var at := float(entry.at)
		if at < 0.0 or at >= 1.0 or at <= previous or (next.is_empty() and at != 0.0):
			return _reject("phase fractions must start at zero and strictly increase below one")
		if ids.has(entry.id):
			return _reject("phase identifiers must be unique")
		ids[entry.id] = true
		previous = at
		next.append(entry.duplicate(true))
	var before := snapshot()
	_period = float(period)
	_elapsed = float(elapsed)
	_weather = weather
	_phases = next
	return _publish(before)

## A detached current-state sample, not an event backlog. Half-open phase ranges
## include their start; the last phase extends to the end of the cycle.
func snapshot() -> Dictionary:
	if _period == 0.0:
		return {}
	var time := fposmod(_elapsed, _period)
	var fraction := time / _period
	var phase: String = _phases[0].id
	for entry in _phases:
		if fraction >= float(entry.at):
			phase = entry.id
	return {"day": int(floor(_elapsed / _period)), "time": time, "fraction": fraction,
		"phase": phase, "weather": _weather, "active": _active}

## Explicit elapsed presentation seconds. Paused calls are discarded, so resuming
## never applies accumulated offline time. Large steps publish the final state once.
func advance(seconds: Variant) -> bool:
	if _period == 0.0:
		return _reject("configure the clock before advancing")
	if not _number(seconds) or float(seconds) < 0.0:
		return _reject("advance must be finite and nonnegative")
	if not _active or float(seconds) == 0.0:
		last_error = ""
		return true
	var target := _elapsed + float(seconds)
	if target == _elapsed or not _valid_time(target, _period):
		return _reject("advance exceeds finite time or floating-point precision")
	return seek(target)

## An explicit external time sample, including deliberate rewinds for previews.
## This is not wired to SaveGame and does not change any existing save shape.
func seek(elapsed: Variant) -> bool:
	if _period == 0.0 or not _valid_time(elapsed, _period):
		return _reject("elapsed time is outside the configured finite, exact-day range")
	var before := snapshot()
	_elapsed = float(elapsed)
	return _publish(before)

func set_weather(weather: Variant) -> bool:
	if _period == 0.0 or not _identifier(weather):
		return _reject("configure the clock and supply a nonempty weather identifier")
	var before := snapshot()
	_weather = weather
	return _publish(before)

func set_active(active: bool) -> void:
	var before := snapshot()
	_active = active
	_publish(before)

func _publish(before: Dictionary) -> bool:
	last_error = ""
	var value := snapshot()
	if value != before:
		changed.emit(value)
	return true

static func _number(value: Variant) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value))

static func _identifier(value: Variant) -> bool:
	return value is String and not value.strip_edges().is_empty()

static func _valid_time(value: Variant, period: float) -> bool:
	return _number(value) and float(value) >= 0.0 and is_finite(float(value) / period) \
		and float(value) / period < MAX_EXACT_DAY

func _reject(message: String) -> bool:
	last_error = message
	return false
