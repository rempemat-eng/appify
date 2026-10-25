class_name AbilityClock
extends RefCounted
## Canonical action clock only. Emits ordered commands; it never deals damage or advances art.
## The world runner will consume these commands after displaying the contact drawing. Keeping
## that boundary explicit prevents the old Player and animation preview from duplicating hits.

var character := ""
var kit := {}
var action := ""
var elapsed := 0.0
var duration := 0.0
var release_at := 0.0
var released := false
var instance := 0
var powered_remaining := 0.0
var cooldowns := {"primary": 0.0, "secondary": 0.0, "special": 0.0}
var _events: Array[Dictionary] = []
var _queued := ""
var _queue_remaining := 0.0
var _held_primary := false
var _held_guard := false
var _secondary_was_held := false
var _special_was_held := false
var _action_powered := false

func configure(id: String) -> bool:
	var data := AbilityCatalogue.kit(id)
	if data.is_empty():
		return false
	character = id
	kit = data
	action = ""
	elapsed = 0.0
	powered_remaining = 0.0
	cooldowns = {"primary": 0.0, "secondary": 0.0, "special": 0.0}
	_events.clear()
	_queued = ""
	_queue_remaining = 0.0
	_held_primary = false
	_held_guard = false
	_secondary_was_held = false
	_special_was_held = false
	return true

func is_powered() -> bool:
	return powered_remaining > 0.00000001

func is_busy() -> bool:
	return action != ""

## Direct commitment is useful for tests and action-driver requests. Resource/terrain eligibility
## belongs to the future runner, which must check it before this commitment (ammo, heat, tether).
func commit(name: String) -> bool:
	if kit.is_empty() or is_busy() or not cooldowns.has(name) or cooldowns[name] > 0.00000001:
		return false
	_action_powered = is_powered()
	var spec: Dictionary = kit["powered" if _action_powered else "base"].actions[name]
	action = name
	elapsed = 0.0
	duration = float(spec.duration_seconds)
	release_at = float(spec.release_seconds)
	released = false
	instance += 1
	cooldowns[name] = float(spec.cooldown_seconds)
	_event("commit", name)
	if release_at <= 0.00000001:
		_release()
	return true

## One queue slot, special wins simultaneous rising edges. Holding guard clears the slot.
func input(primary: bool, secondary: bool, special: bool, guard: bool) -> void:
	_held_primary = primary
	_held_guard = guard
	if guard:
		_queued = ""
		_queue_remaining = 0.0
	else:
		var wanted := ""
		if secondary and not _secondary_was_held and cooldowns.secondary <= 0.00000001:
			wanted = "secondary"
		if special and not _special_was_held and cooldowns.special <= 0.00000001:
			wanted = "special"
		if wanted != "":
			_queued = wanted
			_queue_remaining = 0.7
	_secondary_was_held = secondary
	_special_was_held = special
	_try_input()

func _try_input() -> void:
	if _held_guard or is_busy():
		return
	if _queued != "":
		var wanted := _queued
		_queued = "" # consumed on commitment attempt, even if the runner later rejects it
		_queue_remaining = 0.0
		commit(wanted)
	elif _held_primary:
		commit("primary")

## Divide at every release, completion, cooldown, queue and form boundary. A long step must not
## move form start back to the beginning of the step or lose a release between two drawings.
## The caller supplies active simulation time; inactive time deliberately freezes every clock.
func advance(delta: float, active: bool = true) -> void:
	if not active or delta <= 0.0 or kit.is_empty():
		return
	var remaining := delta
	while remaining > 0.00000001:
		_try_input()
		var step := remaining
		if is_busy():
			step = minf(step, duration - elapsed)
			if not released:
				step = minf(step, release_at - elapsed)
		if is_powered():
			step = minf(step, powered_remaining)
		if _queue_remaining > 0.00000001:
			step = minf(step, _queue_remaining)
		for value in cooldowns.values():
			if value > 0.00000001:
				step = minf(step, value)
		# All zero-time boundaries are handled below before the next iteration.
		step = maxf(step, 0.0)
		var was_powered := is_powered()
		if is_busy():
			elapsed += step
		for name in cooldowns:
			cooldowns[name] = maxf(cooldowns[name] - step, 0.0)
		powered_remaining = maxf(powered_remaining - step, 0.0)
		_queue_remaining = maxf(_queue_remaining - step, 0.0)
		remaining -= step
		if was_powered and not is_powered():
			_event("powered_off", "natural")
		if is_busy() and not released and elapsed + 0.00000001 >= release_at:
			_release()
		if is_busy() and elapsed + 0.00000001 >= duration:
			_event("complete", action)
			action = ""
		if _queue_remaining <= 0.00000001:
			_queued = ""

func cancel(reason: String = "interrupted") -> void:
	if is_busy():
		_event("cancel", reason)
	action = ""
	_queued = ""
	_queue_remaining = 0.0
	_held_primary = false
	_held_guard = false

func end_form(reason: String) -> void:
	if is_powered():
		powered_remaining = 0.0
		_event("powered_off", reason)

func drain_events() -> Array[Dictionary]:
	var result := _events
	_events = []
	return result

func _release() -> void:
	released = true
	_event("release", action)
	if action == "special":
		powered_remaining = float(kit.powered.duration_seconds)
		_event("powered_on", action)

func _event(kind: String, name: String) -> void:
	_events.append({"kind": kind, "action": name, "instance": instance,
		"elapsed": elapsed, "powered_at_commit": _action_powered})
