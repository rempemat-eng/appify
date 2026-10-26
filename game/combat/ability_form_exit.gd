class_name AbilityFormExit
extends RefCounted
## Canonical X transition only. Caller owns expiry detection and once-only delivery.

static func finish(source: Dictionary, interrupted := false) -> Dictionary:
	var state := source.duplicate(true)
	var player: Dictionary = state.player
	player.specialRemaining = 0
	if player.id == "rook":
		state.turrets = []
		player.designatedId = null
	if player.id == "ashe" and not interrupted and player.hp > 0:
		var old_x: float = player.actionDirX
		var old_y: float = player.actionDirY
		player.actionDirX = player.dirX
		player.actionDirY = player.dirY
		var end := {"x": player.x + 98 * player.actionDirX, "y": player.y + 98 * player.actionDirY}
		var targets: Array = []
		for enemy in state.enemies:
			var along: float = (enemy.x - player.x) * player.actionDirX + (enemy.y - player.y) * player.actionDirY
			if enemy.hp > 0 and along >= -enemy.radius and along <= 98 + enemy.radius and AbilityFields._segment_distance(enemy, player, end) <= 13 + enemy.radius:
				targets.append(enemy)
		# Original beam sorts its captured target list before synchronous damage.
		targets.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return AbilityImpacts._distance(a, player) < AbilityImpacts._distance(b, player))
		for enemy in targets:
			AbilityImpacts._damage(state, enemy, 34)
		AbilityImpacts._fx(state, "fire-finisher", end.x, end.y, 13, 0.24, player.x, player.y)
		if targets.is_empty():
			AbilityDefence._event(state, "miss", "fire-finisher missed")
		player.actionDirX = old_x
		player.actionDirY = old_y
		AbilityImpacts._field(state, "flame", player.x + 52 * player.dirX, player.y + 52 * player.dirY, 16, 1, 7)
	AbilityDefence._event(state, "special-end", "Form interrupted" if interrupted else "Form ended")
	return state
