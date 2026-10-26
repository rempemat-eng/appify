class_name AbilityArenaDriver
extends AbilityActionDriver
## Concrete isolated encounter/practice driver. Never maps world HP or creates
## Godot projectiles: canonical snapshots own those effects exactly once.
## Not installed by default. Contact/art and C61 live-world adapters remain separate.

signal player_phase_observed(before: Dictionary, after: Dictionary, delta: float)

var _state: Dictionary = {}
var _origin := Vector2.ZERO
var _scale := 0.0
var _enabled := false
var _requests := {"primary": false, "secondary": false, "special": false}
var _mover := Callable()
var _requested_aim := Vector2.ZERO
var last_error := ""
var _presentation: AbilityContactConsumer = null
var _pose := Callable()

## Bind explicitly supplied art clocks and display callbacks to this driver only.
## A rejected replacement preserves the existing binding. No scene enables this.
func bind_presentation(provider: Callable, draw: Callable, contact: Callable, pose: Callable = Callable()) -> bool:
	if not _enabled:
		return false
	var candidate := AbilityContactConsumer.new()
	if not candidate.configure(provider, draw, contact):
		return false
	clear_presentation()
	_presentation = candidate
	_pose = pose
	player_phase_observed.connect(_presentation.observe)
	return true

func clear_presentation() -> void:
	if _presentation == null:
		return
	var old := _presentation
	_presentation = null
	old.cancel()
	var previous_pose := _pose
	_pose = Callable()
	if previous_pose.is_valid():
		previous_pose.call({}) # release the body offset on every lifecycle cancellation
	if player_phase_observed.is_connected(old.observe):
		player_phase_observed.disconnect(old.observe)

func configure(source: Dictionary, canonical_origin_in_actor_texels: Vector2) -> bool:
	if source.get("mode") not in ["encounter", "practice"] or not source.get("player") is Dictionary:
		return false
	if not source.has_all(["width", "height", "time", "tick", "accumulator", "status", "previous", "queuedAction", "queueRemaining", "enemies", "projectiles", "fields", "turrets", "effects", "events", "statistics", "serial", "rng", "seed", "echoIn", "currentIn"]):
		return false
	if not source.player.has_all(["x", "y", "hp", "action", "specialRemaining", "cooldowns"]):
		return false
	if AbilityCatalogue.kit(str(source.player.get("id", ""))).is_empty():
		return false
	if not is_finite(canonical_origin_in_actor_texels.x) or not is_finite(canonical_origin_in_actor_texels.y):
		return false
	clear_presentation() # a new snapshot needs a fresh, explicit presentation contract
	_state = source.duplicate(true)
	_origin = canonical_origin_in_actor_texels
	_scale = float(AbilityCatalogue.units().canonical_to_actor)
	_enabled = true
	last_error = ""
	_clear_requests()
	return true

func snapshot() -> Dictionary:
	return _state.duplicate(true)

func plans_movement() -> bool:
	return true

func is_busy() -> bool:
	return _enabled and (_state.player.action not in ["idle", "walk"] or _state.player.specialRemaining > 0)

func character_changed(id: String) -> void:
	if not _state.is_empty() and id != _state.player.id:
		cancel("character_changed") # caller must configure the new canonical snapshot explicitly

func request(action: String, direction: Vector2) -> bool:
	if not _enabled or _state.status != "playing" or not _requests.has(action):
		return false # universal dodge has no recovered canonical rule; do not invent one
	if not is_finite(direction.x) or not is_finite(direction.y):
		return false
	_requested_aim = direction
	_requests[action] = true
	return true

func cancel(reason: String) -> void:
	_enabled = false
	clear_presentation()
	_clear_requests()
	_mover = Callable()
	last_error = reason

func tick(controls: Dictionary, context: Dictionary, delta: float) -> void:
	if not _enabled or not is_finite(delta) or delta <= 0:
		return
	if not bool(controls.get("active", false)):
		_clear_requests()
		_state.previous = {"primary": false, "secondary": false, "block": false, "special": false}
		_state.queuedAction = null
		_state.queueRemaining = 0.0
		return
	if context.get("character") != _state.player.id or not context.get("move_actor") is Callable or not context.move_actor.is_valid():
		last_error = "missing actor movement contract or character mismatch"
		return
	_mover = context.move_actor
	var move: Vector2 = controls.get("move", Vector2.ZERO)
	var aim: Vector2 = _requested_aim if _requested_aim.length() > 0.1 else controls.get("aim", Vector2.RIGHT)
	# Canonical aim is an absolute target, while Player supplies a direction.
	var raw := {"moveX": move.x, "moveY": move.y,
		"aimX": float(_state.player.x) + aim.x * 100.0,
		"aimY": float(_state.player.y) + aim.y * 100.0,
		"primary": bool(controls.get("primary", false)) or _requests.primary,
		"secondary": bool(controls.get("secondary", false)) or _requests.secondary,
		"special": bool(controls.get("special", false)) or _requests.special,
		"block": bool(controls.get("guard", false))}
	var previous_tick := int(_state.tick)
	_state = AbilitySimulation.step(_state, raw, delta, _resolve_position, _observe_player)
	_mover = Callable()
	if _enabled and _pose.is_valid():
		_pose.call(_state.duplicate(true)) # final movement/landing height, even without a new drawing
	if int(_state.tick) != previous_tick:
		_clear_requests()

func _resolve_position(x: float, y: float) -> Dictionary:
	if not _enabled or not _mover.is_valid():
		return {} # a drawing/contact callback can detach the actor during this fixed step
	var target := _origin + Vector2(x, y) * _scale
	var actual: Variant = _mover.call(target)
	if not actual is Vector2 or not is_finite(actual.x) or not is_finite(actual.y):
		last_error = "invalid actor movement result"
		return {}
	return {"x": float(actual.x - _origin.x) / _scale, "y": float(actual.y - _origin.y) / _scale}

func _clear_requests() -> void:
	_requests = {"primary": false, "secondary": false, "special": false}
	_requested_aim = Vector2.ZERO

func _observe_player(before: Dictionary, after: Dictionary, delta: float) -> void:
	if _enabled and _pose.is_valid():
		if _pose.call(after.duplicate(true)) != true:
			return # malformed height cannot show a release/contact at a stale elevation
	if _enabled:
		player_phase_observed.emit(before, after, delta)
