class_name AbilityFields
extends RefCounted
## Reference fixed-step phase primitives; snapshots use canonical x/y/camelCase.
## Caller owns time/tick, active/playing gates, player clocks, projectile and AI order.
## These phases do not advance effects, player timers, turrets or Godot actors.

const STEP := 1.0 / 60.0
const EPSILON := 1.0e-8

static func tick_fields(source: Dictionary) -> Dictionary:
	var state := source.duplicate(true)
	# Retain original order: even a field expiring this tick acts before removal.
	for field in state.fields:
		field.remaining -= STEP
		field.tickIn -= STEP
		if field.kind == "gravity":
			for enemy in state.enemies:
				var distance := AbilityImpacts._distance(enemy, field)
				if enemy.hp <= 0 or distance > field.radius + enemy.radius:
					continue
				var direction := _direction(enemy, field)
				var pull := minf(distance, STEP * (13 if enemy.kind in ["tank", "dummy"] else 32))
				enemy.x += direction.x * pull
				enemy.y += direction.y * pull
				enemy.slowRemaining = 0.2
		if field.tickIn <= EPSILON:
			field.tickIn = 0.45 if field.kind == "gravity" else 0.6
			if field.damage != 0:
				for enemy in state.enemies:
					if enemy.hp > 0 and AbilityImpacts._distance(enemy, field) <= field.radius + enemy.radius:
						AbilityImpacts._damage(state, enemy, field.damage, 0, field.kind != "gravity")
			if field.kind == "ice":
				for enemy in state.enemies:
					if enemy.hp > 0 and AbilityImpacts._distance(enemy, field) <= field.radius + enemy.radius:
						enemy.slowRemaining = 0.7
	state.fields = state.fields.filter(func(f: Dictionary) -> bool: return f.remaining > EPSILON)
	if state.player.id == "mirra" and AbilityImpacts._powered(state):
		state.currentIn -= STEP
		if state.currentIn <= EPSILON:
			state.currentIn = 0.35
			var points: Array = [state.player]
			points.append_array(state.fields.filter(func(f: Dictionary) -> bool: return f.kind == "seal"))
			var hit := {}
			for index in range(1, points.size()):
				var start: Dictionary = points[index - 1]
				var end: Dictionary = points[index]
				AbilityImpacts._fx(state, "current", end.x, end.y, 5, 0.38, start.x, start.y)
				for enemy in state.enemies:
					if enemy.hp > 0 and not hit.has(enemy.id) and _segment_distance(enemy, start, end) <= 6 + enemy.radius:
						AbilityImpacts._damage(state, enemy, 10)
						enemy.slowRemaining = 0.5
						hit[enemy.id] = true
	return state

static func tick_statuses(source: Dictionary) -> Dictionary:
	# Only L's status prelude. C61 remains the enemy-AI owner; no legacy AI port.
	var state := source.duplicate(true)
	for enemy in state.enemies:
		for key in ["rootRemaining", "slowRemaining", "stunRemaining", "vulnerableRemaining"]:
			enemy[key] = maxf(0, float(enemy[key]) - STEP)
		if state.time - enemy.lastHitAt > 3:
			enemy.frost = 0
		if enemy.hp <= 0:
			enemy.phaseRemaining = maxf(0, enemy.phaseRemaining - STEP)
	return state

static func _direction(start: Dictionary, end: Dictionary) -> Dictionary:
	var distance := AbilityImpacts._distance(start, end)
	return {"x": (end.x - start.x) / distance if distance > EPSILON else 1.0,
		"y": (end.y - start.y) / distance if distance > EPSILON else 0.0}

static func _segment_distance(point: Dictionary, start: Dictionary, end: Dictionary) -> float:
	var dx := float(end.x) - float(start.x)
	var dy := float(end.y) - float(start.y)
	var squared := dx * dx + dy * dy
	var fraction := clampf(((point.x - start.x) * dx + (point.y - start.y) * dy) / squared, 0, 1) if squared != 0.0 else 0.0
	return sqrt(pow(point.x - start.x - fraction * dx, 2) + pow(point.y - start.y - fraction * dy, 2))
