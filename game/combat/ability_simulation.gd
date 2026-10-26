class_name AbilitySimulation
extends RefCounted
## Pure canonical arena dispatcher. Does not run legacy enemy AI or drive Godot actors.
## Encounter/practice only until the C61/world bridge supplies its own ordered enemy phase.

const DT := 1.0 / 60.0
const EPS := 1.0e-8

static func step(source: Dictionary, raw_input: Dictionary, delta: float, resolve_position: Callable = Callable()) -> Dictionary:
	if raw_input.get("active") is bool and raw_input.active == false:
		return source
	var elapsed := clampf(delta, 0.0, 0.1) if is_finite(delta) else 0.0
	if elapsed <= 0:
		return source
	# Leave unsupported legacy live mode untouched in debug AND release builds.
	if source.mode == "live":
		return source
	var state := source.duplicate(true)
	state.accumulator += elapsed
	var input := normalise_input(raw_input, state.player)
	while state.accumulator + EPS >= DT:
		state.accumulator = maxf(0.0, state.accumulator - DT)
		if state.status == "playing":
			state = _playing_tick(state, input, resolve_position)
		else:
			state.time += DT
			state.tick += 1
			state.player.actionElapsed = minf(state.player.actionDuration, state.player.actionElapsed + DT)
			_expire_effects(state)
	if state.accumulator < EPS:
		state.accumulator = 0.0
	return state

static func normalise_input(raw: Dictionary, player: Dictionary) -> Dictionary:
	return {"moveX": clampf(_number(raw.get("moveX")), -1, 1),
		"moveY": clampf(_number(raw.get("moveY")), -1, 1),
		"aimX": _number(raw.get("aimX"), player.aimX),
		"aimY": _number(raw.get("aimY"), player.aimY),
		"primary": _truthy(raw.get("primary")), "secondary": _truthy(raw.get("secondary")),
		"block": _truthy(raw.get("block")), "special": _truthy(raw.get("special")), "active": true}

static func _number(value: Variant, fallback: float = 0.0) -> float:
	return float(value) if (value is float or value is int) and is_finite(float(value)) else fallback

static func _truthy(value: Variant) -> bool:
	# Match the original JS input coercion, including truthy empty containers.
	if value == null:
		return false
	if value is bool:
		return value
	if value is float or value is int:
		return float(value) != 0 and not is_nan(float(value))
	if value is String:
		return not value.is_empty()
	return true

static func _playing_tick(source: Dictionary, input: Dictionary, resolve_position: Callable = Callable()) -> Dictionary:
	# These reducers already own release/resource/launch mutations. Do not also tick
	# AbilityClock/AbilityResources/AbilityRunner or replay projectile planning here.
	var state := AbilityPlayerPhase.tick(source, input)
	# Some committed secondary releases displace the player before ordinary walking.
	# Resolve that displacement first, so a blocked dash is not counted backwards
	# as walk distance and subsequent movement/effects start at the actual body.
	if resolve_position.is_valid() and (state.player.x != source.player.x or state.player.y != source.player.y):
		AbilityMovement.resolve_actor_position(state, source.player.x, source.player.y, resolve_position)
	state = AbilityMovement.tick(state, input, resolve_position)
	state = AbilityFields.tick_statuses(state)
	if state.player.hp <= 0:
		return state
	state = AbilityProjectilePhase.tick(state)
	if state.player.hp <= 0:
		return state
	state = AbilityFields.tick_fields(state)
	state = AbilityTurrets.tick(state)
	_expire_effects(state)
	var p: Dictionary = state.player
	match p.id:
		"morel": p.resource = state.fields.filter(func(f: Dictionary) -> bool: return f.kind == "reagent").size()
		"mirra": p.resource = state.fields.filter(func(f: Dictionary) -> bool: return f.kind == "seal").size()
		"nix": p.resource = p.heat
		"tam":
			p.resource = 0
			for enemy in state.enemies:
				p.resource = maxf(p.resource, enemy.frost)
		_: p.resource = 0
	state.previous = {"primary": input.primary, "secondary": input.secondary,
		"block": input.block, "special": input.special}
	if state.status == "playing" and state.mode != "practice" and state.enemies.all(func(enemy: Dictionary) -> bool: return enemy.hp <= EPS):
		state.status = "victory"
		p.specialRemaining = 0
		p.blocking = false
		p.action = "idle"
		p.actionElapsed = 0
		p.actionReleased = true
		state.projectiles = []
		state.fields = []
		state.turrets = []
		p.vaultRemaining = 0
		p.vaultHeight = 0
		p.airborne = false
		AbilityDefence._event(state, "defeat", "Practice wave cleared")
	return state

static func _expire_effects(state: Dictionary) -> void:
	for effect in state.effects:
		effect.remaining -= DT
	state.effects = state.effects.filter(func(effect: Dictionary) -> bool: return effect.remaining > EPS)
