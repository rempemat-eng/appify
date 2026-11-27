class_name AbilityStrikes
extends RefCounted
## Pure canonical O/S/C strike snapshots, not actor/world collision or health adapters.

static func arc(source: Dictionary, reach: float, cosine: float, amount: float,
		knockback := 0.0) -> Dictionary:
	var state := source.duplicate(true)
	var player: Dictionary = state.player
	# Capture membership before damage/passives can move or defeat later enemies.
	var targets: Array = []
	for enemy in state.enemies:
		var distance := AbilityImpacts._distance(player, enemy)
		var dot: float = ((float(enemy.x) - player.x) * player.actionDirX + (float(enemy.y) - player.y) * player.actionDirY) / maxf(1, distance)
		if enemy.hp > 0 and distance <= reach + enemy.radius and dot >= cosine:
			targets.append(enemy)
	for enemy in targets:
		AbilityImpacts._damage(state, enemy, amount, knockback)
	AbilityImpacts._fx(state, "arc", player.x + player.actionDirX * reach * 0.58,
		player.y + player.actionDirY * reach * 0.58, 0.63 * reach, 0.22, player.x, player.y)
	if targets.is_empty():
		AbilityDefence._event(state, "miss", "Swing missed")
	return state

static func beam(source: Dictionary, reach: float, radius: float, amount: float,
		pierce: bool, kind: String) -> Dictionary:
	var state := source.duplicate(true)
	var player: Dictionary = state.player
	var end := {"x": player.x + player.actionDirX * reach, "y": player.y + player.actionDirY * reach}
	var targets: Array = []
	for enemy in state.enemies:
		var along: float = (float(enemy.x) - player.x) * player.actionDirX + (float(enemy.y) - player.y) * player.actionDirY
		if enemy.hp <= 0 or along < -enemy.radius or along > reach + enemy.radius:
			continue
		if AbilityFields._segment_distance(enemy, player, end) <= radius + enemy.radius:
			# Stable insertion keeps the reference array order for distance ties.
			var distance := AbilityImpacts._distance(enemy, player)
			var index := targets.size()
			while index > 0 and AbilityImpacts._distance(targets[index - 1], player) > distance:
				index -= 1
			targets.insert(index, enemy)
	if not pierce and targets.size() > 1:
		targets.resize(1)
	for enemy in targets:
		AbilityImpacts._damage(state, enemy, amount, 10 if kind == "lunge" else 0)
	AbilityImpacts._fx(state, kind, end.x, end.y, radius, 0.24, player.x, player.y)
	if targets.is_empty():
		AbilityDefence._event(state, "miss", kind + " missed")
	return state

static func dash(source: Dictionary, reach: float) -> Dictionary:
	var state := source.duplicate(true)
	var player: Dictionary = state.player
	var distance := reach
	for enemy in state.enemies:
		if enemy.hp <= 0:
			continue
		var dx := float(enemy.x) - float(player.x)
		var dy := float(enemy.y) - float(player.y)
		var along: float = dx * player.actionDirX + dy * player.actionDirY
		var side: float = absf(dx * player.actionDirY - dy * player.actionDirX)
		if along > 0 and side < enemy.radius + player.radius:
			distance = minf(distance, maxf(0, along - enemy.radius - player.radius - 2))
	player.x = clampf(player.x + player.actionDirX * distance, 12, state.width - 12)
	player.y = clampf(player.y + player.actionDirY * distance, 23, state.height - 12)
	return state
