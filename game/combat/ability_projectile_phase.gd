class_name AbilityProjectilePhase
extends RefCounted
## Fixed-step ordered projectile phase on canonical snapshots. Not actor HP or terrain.
## Apply impacts synchronously between projectiles; never reuse one stale target snapshot.

const ALIASES := {"hitIds": "hit_ids", "blastRadius": "blast_radius",
	"launchHeight": "launch_height", "flightDuration": "flight_duration"}

static func from_canonical(source: Dictionary) -> Dictionary:
	var shot := source.duplicate(true)
	shot.position = {"x": float(source.x), "y": float(source.y)}
	shot.velocity = {"x": float(source.vx), "y": float(source.vy)}
	for key in ["x", "y", "vx", "vy"]:
		shot.erase(key)
	for key in ALIASES:
		if shot.has(key):
			shot[ALIASES[key]] = shot[key]
			shot.erase(key)
	return shot

static func to_canonical(source: Dictionary) -> Dictionary:
	var shot := source.duplicate(true)
	shot.x = float(source.position.x)
	shot.y = float(source.position.y)
	shot.vx = float(source.velocity.x)
	shot.vy = float(source.velocity.y)
	shot.erase("position")
	shot.erase("velocity")
	for key in ALIASES:
		if shot.has(ALIASES[key]):
			shot[key] = shot[ALIASES[key]]
			shot.erase(ALIASES[key])
	return shot

static func tick(source: Dictionary) -> Dictionary:
	var state := source.duplicate(true)
	if state.status == "defeat":
		state.projectiles = []
		return state
	var survivors: Array = []
	for shot in state.projectiles:
		if state.status == "defeat":
			break
		if shot.owner == "enemy":
			var enemy_step := _enemy_step(state, shot)
			state = enemy_step.state
			if enemy_step.alive:
				survivors.append(enemy_step.shot)
			continue
		var targets: Array[Dictionary] = []
		for enemy in state.enemies:
			targets.append({"id": enemy.id, "position": {"x": float(enemy.x), "y": float(enemy.y)},
				"radius": enemy.radius, "hp": enemy.hp})
		var seals: Array[Dictionary] = []
		for field in state.fields:
			if field.kind == "seal":
				seals.append({"position": {"x": float(field.x), "y": float(field.y)},
					"radius": field.radius, "remaining": field.remaining})
		var step := AbilityFlight.tick_scalar(from_canonical(shot), targets, seals,
			{"left": 0.0, "top": 16.0, "right": float(state.width), "bottom": float(state.height)})
		for event in step.events:
			if event.type == "water-shaped":
				AbilityImpacts._fx(state, "water-shaped", event.position.x, event.position.y, 12, 0.25)
			elif event.type == "impact":
				state = AbilityImpacts.impact(state, to_canonical(event.shot), event.target_id)
		if step.alive:
			survivors.append(to_canonical(step.shot))
	state.projectiles = [] if state.status == "defeat" else survivors
	return state

static func _enemy_step(state: Dictionary, source: Dictionary) -> Dictionary:
	var shot := source.duplicate(true)
	var old_x := float(shot.x)
	var old_y := float(shot.y)
	var delta := minf(1.0 / 60.0, maxf(0.0, shot.remaining))
	shot.age += delta
	shot.x += shot.vx * delta
	shot.y += shot.vy * delta
	shot.remaining -= 1.0 / 60.0
	# Decoys are broken in field order but do not absorb the shot in the original F.
	for field in state.fields:
		if field.kind in ["hologram", "echo"] and field.remaining > 0 and _segment_gap(
				field.x, field.y, old_x, old_y, shot.x, shot.y) <= field.radius + shot.radius:
			field.remaining = 0
			AbilityImpacts._fx(state, "projection-break", field.x, field.y, 13, 0.3)
	if _segment_gap(state.player.x, state.player.y, old_x, old_y, shot.x, shot.y) <= shot.radius + state.player.radius:
		state = AbilityDefence.damage(state, shot.damage, old_x, old_y)
		return {"state": state, "shot": shot, "alive": false}
	var outside: bool = shot.x < 0 or shot.x > state.width or shot.y < 16 or shot.y > state.height
	return {"state": state, "shot": shot, "alive": shot.remaining > 1.0e-8 and not outside}

static func _segment_gap(x: float, y: float, ax: float, ay: float, bx: float, by: float) -> float:
	var dx := bx - ax
	var dy := by - ay
	var denominator := dx * dx + dy * dy
	var along := clampf(((x - ax) * dx + (y - ay) * dy) / (denominator if denominator != 0 else 1.0), 0, 1)
	var gap_x := x - ax - dx * along
	var gap_y := y - ay - dy * along
	return sqrt(gap_x * gap_x + gap_y * gap_y)
