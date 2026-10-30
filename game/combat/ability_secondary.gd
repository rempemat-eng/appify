class_name AbilitySecondary
extends RefCounted
## Original q release on canonical snapshots. Caller owns contact/once-only dispatch.
## Includes Pendle's canonical ammo/reload mutation: do not consume it a second time.

static func release(source: Dictionary) -> Dictionary:
	var state := source.duplicate(true)
	var p: Dictionary = state.player
	var powered := AbilityImpacts._powered(state)
	match str(p.id):
		"bramble": state = AbilityStrikes.arc(state, 36, -0.1, 26, 25)
		"morel":
			var ids: Array = []
			for field in state.fields:
				if field.kind == "reagent" and AbilityImpacts._distance(p, field) <= 155:
					ids.append(field.id)
			if ids.is_empty():
				state = AbilityStrikes.arc(state, 34, 0, 20, 13)
			else:
				state = AbilityImpacts.react(state, ids, powered)
			p = state.player
			AbilityImpacts._fx(state, "catalyst", p.x + 18 * p.actionDirX, p.y + 18 * p.actionDirY, 24, 0.25)
		"velvet":
			# Capture the arc before damage/passives mutate any target.
			var targets: Array = []
			for enemy in state.enemies:
				var distance := AbilityImpacts._distance(p, enemy)
				var dot: float = ((float(enemy.x) - p.x) * p.actionDirX + (float(enemy.y) - p.y) * p.actionDirY) / maxf(1, distance)
				if enemy.hp > 0 and distance <= 55 + enemy.radius and dot >= -0.05:
					targets.append(enemy)
			for enemy in targets:
				enemy.stunRemaining = 0.25 if enemy.kind == "tank" else 0.65
				enemy.vulnerableRemaining = 2.2
				AbilityImpacts._damage(state, enemy, 9, 0)
			AbilityImpacts._fx(state, "lantern", p.x + 23 * p.actionDirX, p.y + 23 * p.actionDirY, 32, 0.4)
		"cairn": _launch(state, "boulder", atan2(p.actionDirY, p.actionDirX), 115, 40 if powered else 34, 7, 1.3, 0, 30 if powered else 0)
		"iona":
			var old_x := float(p.x)
			var old_y := float(p.y)
			state = AbilityStrikes.dash(state, 34)
			state = AbilityStrikes.beam(state, 49, 9, 29, true, "lunge")
			p = state.player
			AbilityImpacts._fx(state, "lunge", p.x, p.y, 9, 0.3, old_x, old_y)
			if powered:
				AbilityImpacts._field(state, "gust", (p.x + old_x) / 2, (p.y + old_y) / 2, 25, 1.5, 8)
		"tam":
			state = AbilityStrikes.beam(state, 100, 8, 24, true, "ice-ridge")
			p = state.player
			for enemy in state.enemies:
				if enemy.hp > 0 and _in_beam(p, enemy, 100, 8):
					enemy.slowRemaining = 2
					if powered:
						enemy.rootRemaining = maxf(enemy.rootRemaining, 0.22 if enemy.kind == "tank" else 0.6)
			AbilityImpacts._field(state, "ice", p.x + 52 * p.actionDirX, p.y + 52 * p.actionDirY, 19, 2, 0)
		"brine":
			var target: Dictionary = {}
			for enemy in state.enemies:
				if enemy.id == p.tetherId and enemy.hp > 0 and AbilityImpacts._distance(p, enemy) <= 185:
					target = enemy
					break
			if target.is_empty():
				state = AbilityStrikes.arc(state, 32, 0.2, 21, 16)
			else:
				var distance := AbilityImpacts._distance(p, target)
				var dx := float(target.x) - float(p.x)
				var dy := float(target.y) - float(p.y)
				var nx := dx / distance if distance > 1.0e-8 else 1.0
				var ny := dy / distance if distance > 1.0e-8 else 0.0
				var pull := minf(maxf(0, distance - p.radius - target.radius - 3), 61 if powered else 42)
				if target.kind in ["tank", "dummy"]:
					p.x += nx * pull
					p.y += ny * pull
				else:
					target.x -= nx * pull
					target.y -= ny * pull
				AbilityImpacts._damage(state, target, 23 if powered else 15, 0)
				AbilityImpacts._fx(state, "tether", target.x, target.y, 2, 0.35, p.x, p.y)
				p.tetherRemaining = 2 if powered else 0
				if not powered:
					p.tetherId = null
		"pendle":
			if powered:
				state = AbilityStrikes.beam(state, 44, 0.5, 22, false, "rifle-butt")
			else:
				var rounds := mini(3, int(p.ammo))
				p.ammo -= rounds
				var angle := atan2(p.actionDirY, p.actionDirX)
				for index in rounds:
					_launch(state, "fan-bullet", angle + 0.11 * (index - (rounds - 1) / 2.0), 270, 18, 2, 0.75)
				p.reload = 1.4
				AbilityDefence._event(state, "reload", "Reloading")
		"mirra":
			var distance := minf(112, sqrt(pow(float(p.aimX) - p.x, 2) + pow(float(p.aimY) - p.y, 2)))
			var x: float = p.x + p.actionDirX * distance
			var y: float = p.y + p.actionDirY * distance
			AbilityImpacts._field(state, "seal", x, y, 18, 8 if powered else 6, 0)
			for enemy in state.enemies:
				if enemy.hp > 0 and AbilityImpacts._distance(enemy, {"x": x, "y": y}) <= 18 + enemy.radius:
					enemy.slowRemaining = 1.5
					AbilityImpacts._damage(state, enemy, 10, 0)
			AbilityImpacts._fx(state, "seal", x, y, 18, 0.4)
		"ashe":
			state = AbilityStrikes.beam(state, 65, 9, 38 if powered else 32, true, "ember-thrust")
			p = state.player
			if powered:
				AbilityImpacts._field(state, "flame", p.x + 42 * p.actionDirX, p.y + 42 * p.actionDirY, 15, 2, 8)
		"clack":
			state = AbilityStrikes.arc(state, 43, 0.05, 25, 37)
			p = state.player
			AbilityImpacts._fx(state, "concussion", p.x + 22 * p.actionDirX, p.y + 22 * p.actionDirY, 28, 0.35)
		"nix":
			AbilityImpacts._field(state, "hologram", p.actionOriginX, p.actionOriginY, 7, 3, 0)
			AbilityImpacts._fx(state, "afterimage", p.actionOriginX, p.actionOriginY, 11, 0.35)
		"rook":
			p.vaultRemaining = p.vaultDuration
			AbilityImpacts._fx(state, "vault-lift", p.x, p.y, 12, 0.3)
		"mote":
			var distance := minf(100, sqrt(pow(float(p.aimX) - p.x, 2) + pow(float(p.aimY) - p.y, 2)))
			AbilityImpacts._field(state, "gravity", p.x + p.actionDirX * distance, p.y + p.actionDirY * distance, 39 if powered else 32, 2.3 if powered else 1.8, 4)
	return state

static func _in_beam(p: Dictionary, enemy: Dictionary, reach: float, radius: float) -> bool:
	var along: float = (float(enemy.x) - p.x) * p.actionDirX + (float(enemy.y) - p.y) * p.actionDirY
	return along >= -enemy.radius and along <= reach + enemy.radius and AbilityFields._segment_distance(enemy, p, {"x": p.x + p.actionDirX * reach, "y": p.y + p.actionDirY * reach}) <= radius + enemy.radius

static func _launch(state: Dictionary, kind: String, angle: float, speed: float, damage: float,
		radius: float, remaining: float, pierce := 0, blast_radius := 0.0) -> void:
	var p: Dictionary = state.player
	var dx := cos(angle)
	var dy := sin(angle)
	state.serial += 1
	var distance := sqrt(pow(float(p.aimX) - p.x, 2) + pow(float(p.aimY) - p.y, 2))
	state.projectiles.append({"id": state.serial, "kind": kind, "owner": "player",
		"x": p.x + dx * 9, "y": p.y + dy * 9, "vx": dx * speed, "vy": dy * speed,
		"radius": radius, "remaining": remaining, "damage": damage, "pierce": pierce,
		"hitIds": [], "blastRadius": blast_radius, "source": p.id,
		"powered": AbilityImpacts._powered(state), "launchHeight": p.vaultHeight,
		"age": 0, "flightDuration": clampf((distance - 9) / speed, 0.05, remaining)})
