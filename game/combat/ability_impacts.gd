class_name AbilityImpacts
extends RefCounted
## Pure canonical T/B/Y/G snapshot reducer, NOT a Godot actor health adapter.
## State uses the reference engine's x/y and camelCase fields in canonical units.
## Effects are presentation commands (colour is supplied by presentation, not this reducer).

static func impact(source: Dictionary, shot: Dictionary, target_id: Variant = null) -> Dictionary:
	var state := source.duplicate(true)
	var target := _enemy(state, target_id)
	if shot.kind == "flask":
		for enemy in state.enemies:
			if enemy.hp > 0 and _distance(enemy, shot) <= 16.0 + enemy.radius:
				_damage(state, enemy, shot.damage)
		_field(state, "reagent", shot.x, shot.y, 18, 5, 3)
		_fx(state, "flask-break", shot.x, shot.y, 18, 0.35)
		if shot.powered:
			var ids: Array = []
			for field in state.fields:
				if field.kind == "reagent" and _distance(field, shot) <= 40:
					ids.append(field.id)
			if ids.size() > 1:
				_react(state, ids, true)
	elif shot.blastRadius > 0:
		for enemy in state.enemies:
			if enemy.hp > 0 and _distance(enemy, shot) <= shot.blastRadius + enemy.radius:
				_damage(state, enemy, shot.damage, 13 if shot.kind == "boulder" else 6)
		_fx(state, "stone-slam" if shot.kind == "boulder" else "explosion", shot.x, shot.y, shot.blastRadius, 0.35)
	elif not target.is_empty():
		_damage(state, target, shot.damage)
		if shot.kind == "harpoon" and target.hp > 0:
			state.player.tetherId = target.id
			state.player.tetherRemaining = 4 if shot.powered else 3
			_fx(state, "tether", target.x, target.y, 2, 0.3, state.player.x, state.player.y)
		if shot.kind == "arrow" and shot.powered and target.hp > 0:
			for id in shot.hitIds:
				var previous := _enemy(state, id)
				if not previous.is_empty():
					previous.rootRemaining = 0
			target.rootRemaining = 0.3 if target.kind == "tank" else 0.8
			_fx(state, "root", target.x, target.y, 12, 0.5)
		if shot.source == "rook" and shot.kind == "pulse" and target.hp > 0:
			state.player.designatedId = target.id
			state.player.designationRemaining = 1.2
		if shot.kind == "water" and target.hp > 0:
			target.slowRemaining = 1.2
	return state

static func damage(source: Dictionary, target_id: Variant, amount: float, knockback := 0.0) -> Dictionary:
	var state := source.duplicate(true)
	var enemy := _enemy(state, target_id)
	if not enemy.is_empty():
		_damage(state, enemy, amount, knockback)
	return state

static func field(source: Dictionary, kind: String, x: float, y: float, radius: float,
		remaining: float, amount: float) -> Dictionary:
	var state := source.duplicate(true)
	_field(state, kind, x, y, radius, remaining, amount)
	return state

static func react(source: Dictionary, ids: Array, chained: bool) -> Dictionary:
	var state := source.duplicate(true)
	_react(state, ids, chained)
	return state

static func _powered(state: Dictionary) -> bool:
	return float(state.player.specialRemaining) > 1.0e-8

static func _enemy(state: Dictionary, id: Variant) -> Dictionary:
	for enemy in state.enemies:
		if enemy.id == id:
			return enemy
	return {}

static func _distance(a: Dictionary, b: Dictionary) -> float:
	# Scalar doubles preserve the reference thresholds, independent of Vector2 precision.
	return sqrt(pow(float(a.x) - float(b.x), 2) + pow(float(a.y) - float(b.y), 2))

static func _damage(state: Dictionary, enemy: Dictionary, amount: float,
		knockback := 0.0, passive := true) -> void:
	if enemy.hp <= 0 or amount <= 0:
		return
	var player: Dictionary = state.player
	var actual := amount * (1.35 if enemy.vulnerableRemaining > 0 else 1.0)
	var before := float(enemy.hp)
	enemy.hp = maxf(1.0 if enemy.immortal else 0.0, before - actual)
	enemy.lastHitAt = state.time
	state.statistics.damageDealt += before - enemy.hp
	_event(state, "hit", "%d damage" % floori(before - enemy.hp + 0.5), enemy.id, before - enemy.hp)
	_fx(state, "impact", enemy.x, enemy.y, minf(15, 5 + 0.15 * actual), 0.18)
	if knockback != 0:
		var dx := float(enemy.x) - float(player.x)
		var dy := float(enemy.y) - float(player.y)
		var length := sqrt(dx * dx + dy * dy)
		var nx := dx / length if length > 1.0e-8 else 1.0
		var ny := dy / length if length > 1.0e-8 else 0.0
		var factor := 0.25 if enemy.kind in ["tank", "dummy"] else 1.0
		enemy.x = clampf(enemy.x + nx * knockback * factor, 12, state.width - 12)
		enemy.y = clampf(enemy.y + ny * knockback * factor, 23, state.height - 12)
	if passive and player.id == "tam":
		enemy.frost = mini(3, int(enemy.frost) + 1)
		enemy.slowRemaining = 1.2
		if _powered(state) and enemy.frost >= 3:
			enemy.frost = 0
			enemy.rootRemaining = 0.3 if enemy.kind == "tank" else 0.85
			_damage(state, enemy, 23, 0, false)
			_fx(state, "shatter", enemy.x, enemy.y, 19, 0.35)
	if passive and player.id == "iona" and _powered(state):
		var nearest: Dictionary = {}
		var distance := 55.0
		for other in state.enemies:
			var gap := _distance(enemy, other)
			if other.id != enemy.id and other.hp > 0 and gap < distance:
				nearest = other
				distance = gap
		if not nearest.is_empty():
			_damage(state, nearest, 12, 0, false)
			_fx(state, "lightning", nearest.x, nearest.y, 2, 0.22, enemy.x, enemy.y)
	if enemy.hp <= 0:
		enemy.phase = "defeat"
		enemy.phaseRemaining = 0.6
		state.statistics.kills += 1
		if player.tetherId == enemy.id:
			player.tetherId = null
		_event(state, "defeat", "%s defeated" % enemy.kind, enemy.id)

static func _field(state: Dictionary, kind: String, x: float, y: float,
		radius: float, remaining: float, amount: float) -> void:
	var capacity := 4 if kind in ["reagent", "echo"] else (5 if _powered(state) else 3) if kind == "seal" else 1 if kind == "hologram" else 10
	var matching: Array = state.fields.filter(func(f: Dictionary) -> bool: return f.kind == kind)
	if matching.size() >= capacity:
		var oldest: Variant = matching[0].id
		state.fields = state.fields.filter(func(f: Dictionary) -> bool: return f.id != oldest)
	state.serial += 1
	state.fields.append({"id": state.serial, "kind": kind,
		"x": clampf(x, 12, state.width - 12), "y": clampf(y, 23, state.height - 12),
		"radius": radius, "remaining": remaining, "damage": amount, "tickIn": 0.2, "source": state.player.id})

static func _react(state: Dictionary, ids: Array, chained: bool) -> void:
	var queue := ids.duplicate()
	var visited := {}
	while not queue.is_empty():
		var id: Variant = queue.pop_front()
		if visited.has(id):
			continue
		visited[id] = true
		var patch: Dictionary = {}
		for candidate in state.fields:
			if candidate.id == id and candidate.kind == "reagent":
				patch = candidate
		if patch.is_empty():
			continue
		state.fields = state.fields.filter(func(f: Dictionary) -> bool: return f.id != id)
		if chained:
			for other in state.fields:
				if other.kind == "reagent" and _distance(patch, other) <= 46:
					queue.append(other.id)
		for enemy in state.enemies:
			if enemy.hp > 0 and _distance(enemy, patch) <= patch.radius + 8 + enemy.radius:
				_damage(state, enemy, 39 if chained else 32, 5)
		_fx(state, "reaction", patch.x, patch.y, patch.radius + 8, 0.45)

static func _fx(state: Dictionary, kind: String, x: float, y: float, radius: float,
		duration: float, from_x: Variant = null, from_y: Variant = null) -> void:
	state.serial += 1
	var effect := {"id": state.serial, "kind": kind, "x": x, "y": y,
		"radius": radius, "remaining": duration, "duration": duration}
	if from_x != null:
		effect.fromX = from_x
		effect.fromY = from_y
	state.effects.append(effect)

static func _event(state: Dictionary, kind: String, text: String, target: Variant, amount: Variant = null) -> void:
	var event := {"time": state.time, "type": kind, "text": text, "targetId": target}
	if amount != null:
		event.amount = amount
	state.events.append(event)
	if state.events.size() > 80:
		state.events.pop_front()
