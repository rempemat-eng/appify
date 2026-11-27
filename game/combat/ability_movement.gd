class_name AbilityMovement
extends RefCounted
## Original v movement/vault/echo subphase on canonical snapshots (fixed 1/60).
## Caller runs player timers/action releases first. No clock, terrain or actor adapter.

const DT := 1.0 / 60.0
const EPS := 1.0e-8

static func tick(source: Dictionary, input: Dictionary, resolve_position: Callable = Callable()) -> Dictionary:
	var state := source.duplicate(true)
	var p: Dictionary = state.player
	var mx := float(input.moveX)
	var my := float(input.moveY)
	var magnitude := sqrt(mx * mx + my * my)
	p.moving = magnitude > 0.08
	var speed := 43.0 if p.id == "cairn" else (49.0 if p.id == "clack" else (63.0 if p.id in ["velvet", "tam"] else 57.0))
	var multiplier := 1.0
	if p.blocking:
		multiplier = 0.42
	elif p.action == "hit":
		multiplier = 0.2
	elif p.action == "special":
		multiplier = 0.4
	elif p.action == "secondary" and p.id == "nix":
		multiplier = 1.0
	elif p.action in ["secondary", "primary"]:
		multiplier = 0.64
	var old_x := float(p.x)
	var old_y := float(p.y)
	var was_vaulting: bool = p.vaultRemaining > 0
	if p.moving:
		var distance := speed * DT * multiplier * (1.28 if p.id == "tam" and AbilityImpacts._powered(state) else 1.0)
		p.x += mx / maxf(1, magnitude) * distance
		p.y += my / maxf(1, magnitude) * distance
	if p.vaultRemaining > EPS:
		p.vaultRemaining = maxf(0, p.vaultRemaining - DT)
		p.vaultHeight = 18 * sin(PI * (1 - p.vaultRemaining / p.vaultDuration))
		p.airborne = p.vaultHeight > 2
		p.x += 72 * p.vaultDirX * DT
		p.y += 72 * p.vaultDirY * DT
		if p.vaultRemaining <= EPS:
			p.vaultHeight = 0
			p.airborne = false
			_separate(state, 1)
			AbilityImpacts._fx(state, "vault-land", p.x, p.y, 12, 0.25)
	_clamp(state)
	if not p.airborne:
		_separate(state, 0)
		_clamp(state)
	# Optional actor boundary: all canonical movement remains a plan until the
	# owning CharacterBody resolves it. Later walk/echo effects use the actual result.
	resolve_actor_position(state, old_x, old_y, resolve_position)
	if not was_vaulting:
		var dx := float(p.x) - old_x
		var dy := float(p.y) - old_y
		p.walkDistance += sqrt(dx * dx + dy * dy)
	if p.action in ["idle", "walk"]:
		p.action = "walk" if p.moving else "idle"
		p.actionDuration = 0.66 if p.moving else 1.36
	if p.id == "velvet" and AbilityImpacts._powered(state) and p.moving:
		state.echoIn -= DT
		if state.echoIn <= EPS:
			AbilityImpacts._field(state, "echo", p.x - 8 * p.dirX, p.y - 8 * p.dirY, 11, 1.15, 0)
			state.echoIn = 0.4
	return state

static func resolve_actor_position(state: Dictionary, old_x: float, old_y: float, resolver: Callable) -> void:
	if not resolver.is_valid():
		return
	var p: Dictionary = state.player
	var actual: Variant = resolver.call(float(p.x), float(p.y))
	if actual is Dictionary and (actual.get("x") is float or actual.get("x") is int) and (actual.get("y") is float or actual.get("y") is int) and is_finite(float(actual.x)) and is_finite(float(actual.y)):
		p.x = float(actual.x)
		p.y = float(actual.y)
	else:
		p.x = old_x
		p.y = old_y

static func _clamp(state: Dictionary) -> void:
	var p: Dictionary = state.player
	p.x = clampf(p.x, 12, state.width - 12)
	p.y = clampf(p.y, 23, state.height - 12)

static func _separate(state: Dictionary, padding: float) -> void:
	var p: Dictionary = state.player
	# Sequential array order is observable at corners and among overlapping bodies.
	for enemy in state.enemies:
		var dx := float(p.x) - float(enemy.x)
		var dy := float(p.y) - float(enemy.y)
		var length := sqrt(dx * dx + dy * dy)
		var overlap: float = p.radius + enemy.radius + padding - length
		if enemy.hp > 0 and overlap > 0:
			p.x += (dx / length if length > EPS else 1.0) * overlap
			p.y += (dy / length if length > EPS else 0.0) * overlap
