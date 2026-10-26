class_name AbilityProjectilePhase
extends RefCounted
## Fixed-step PLAYER-projectile phase on canonical snapshots. Not actor HP or terrain.
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
	# Enemy/decoy/guard path is not ported yet. Reject mixed input before any processing.
	for shot in state.projectiles:
		if shot.owner != "player":
			assert(false, "Enemy projectile phase requires the guard/decoy port")
			return source.duplicate(true) # Release builds also refuse mixed input.
	var survivors: Array = []
	for shot in state.projectiles:
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
	state.projectiles = survivors
	return state
