class_name AbilityTurrets
extends RefCounted
## Original N phase on canonical snapshots, not Godot actors or autonomous targeting.
## Caller owns playing/active gates, form/designation time, phase order and shot dispatch.

const STEP := 1.0 / 60.0
const EPSILON := 1.0e-8

static func tick(source: Dictionary) -> Dictionary:
	var state := source.duplicate(true)
	var player: Dictionary = state.player
	if player.id != "rook" or not AbilityImpacts._powered(state) or player.hp <= 0:
		state.turrets = []
		return state
	for index in state.turrets.size():
		var turret: Dictionary = state.turrets[index]
		turret.remaining -= STEP
		turret.cooldown -= STEP
		# Formation uses surviving array order, including a lone surviving right turret.
		var goal_x := float(player.x) + (-16.0 if index == 0 else 16.0)
		var goal_y := float(player.y) - 14.0
		turret.x += (goal_x - turret.x) * (7.0 / 60.0)
		turret.y += (goal_y - turret.y) * (7.0 / 60.0)
		var target: Dictionary = {}
		for enemy in state.enemies:
			if enemy.id == player.designatedId and enemy.hp > 0 and AbilityImpacts._distance(enemy, player) < 190:
				target = enemy
				break
		turret.targetId = target.id if not target.is_empty() else null
		turret.aimX = target.x if not target.is_empty() else player.aimX
		turret.aimY = target.y if not target.is_empty() else player.aimY
		if not target.is_empty() and turret.cooldown <= EPSILON and AbilityImpacts._distance(turret, player) < 55:
			var distance := AbilityImpacts._distance(target, turret)
			var nx: float = (target.x - turret.x) / distance if distance > EPSILON else 1.0
			var ny: float = (target.y - turret.y) / distance if distance > EPSILON else 0.0
			state.serial += 1
			state.projectiles.append({"id": state.serial, "kind": "turret-pulse", "owner": "player",
				"x": turret.x, "y": turret.y, "vx": 205 * nx, "vy": 205 * ny,
				"radius": 2, "remaining": 1, "damage": 7, "pierce": 0, "hitIds": [],
				"blastRadius": 0, "source": "rook", "powered": true, "launchHeight": 0,
				"age": 0, "flightDuration": clampf(distance / 205.0, 0.05, 1.0)})
			turret.cooldown = 0.44
	# Original order: a turret may fire on its final tick, then disappears.
	state.turrets = state.turrets.filter(func(turret: Dictionary) -> bool: return turret.remaining > EPSILON)
	return state
