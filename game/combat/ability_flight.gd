class_name AbilityFlight
extends RefCounted
## One canonical 1/60s player-projectile step. Pure snapshots/impact commands, never world HP.
## The future dispatcher must apply each impact synchronously before the next projectile tick.
## Targets: {id, position: Vector2, radius, hp}; seals: {position, radius, remaining}.
const STEP := 1.0 / 60.0
const EPS := 1.0e-8

static func tick(source: Dictionary, targets: Array[Dictionary] = [],
		seals: Array[Dictionary] = [], bounds := Rect2(0, 16, 320, 164)) -> Dictionary:
	assert(source.owner == "player", "Enemy projectile/decoy/guard handling is a separate port step")
	var shot := source.duplicate(true)
	var events: Array[Dictionary] = []
	var start: Vector2 = shot.position
	var dt := minf(STEP, maxf(0.0, float(shot.remaining)))
	shot.age += dt
	shot.position += shot.velocity * dt
	shot.remaining -= STEP
	var finish: Vector2 = shot.position
	if shot.kind == "water" and not shot.get("amplified", false):
		var seal_t := INF
		var target_t := INF
		for seal in seals:
			if float(seal.remaining) > 0.0:
				seal_t = minf(seal_t, entry(start, finish, seal.position, float(seal.radius)))
		for target in targets:
			if _eligible(target, shot):
				target_t = minf(target_t, entry(start, finish, target.position,
					float(target.radius) + float(shot.radius)))
		if seal_t != INF and seal_t <= target_t:
			shot.amplified = true
			shot.damage = 28.0
			shot.radius = 6.0
			shot.pierce = 1
			events.append({"type": "water-shaped", "position": start.lerp(finish, seal_t)})
	var contacts: Array[Dictionary] = []
	for target in targets:
		if _eligible(target, shot) and distance_to_segment(target.position, start, finish) <= float(target.radius) + float(shot.radius):
			contacts.append(target)
	# Original F sorts by centre distance from the segment start, with stable ties.
	# This is deliberately not a newly designed earliest-circle-entry ordering.
	for i in range(1, contacts.size()):
		var value := contacts[i]
		var j := i
		while j > 0 and start.distance_to(contacts[j - 1].position) > start.distance_to(value.position):
			contacts[j] = contacts[j - 1]
			j -= 1
		contacts[j] = value
	for target in contacts:
		if float(shot.blast_radius) > 0.0 or shot.kind == "flask":
			shot.position = target.position
		# T observes the previous hit_ids; insertion follows impact (powered arrow root transfer).
		events.append({"type": "impact", "target_id": target.id, "shot": shot.duplicate(true)})
		shot.hit_ids.append(target.id)
		if int(shot.pierce) <= 0:
			return {"alive": false, "shot": shot, "events": events}
		shot.pierce -= 1
	var pos: Vector2 = shot.position
	# Original bounds include the right/bottom edges (Rect2.has_point does not).
	var outside := pos.x < bounds.position.x or pos.x > bounds.end.x or pos.y < bounds.position.y or pos.y > bounds.end.y
	if float(shot.remaining) <= EPS or outside:
		if shot.kind == "flask" or float(shot.blast_radius) > 0.0:
			events.append({"type": "impact", "target_id": null, "shot": shot.duplicate(true)})
		return {"alive": false, "shot": shot, "events": events}
	return {"alive": true, "shot": shot, "events": events}

static func _eligible(target: Dictionary, shot: Dictionary) -> bool:
	return float(target.hp) > 0.0 and not target.id in shot.hit_ids

static func distance_to_segment(point: Vector2, start: Vector2, finish: Vector2) -> float:
	var delta := finish - start
	var denominator := delta.length_squared()
	var t := clampf((point - start).dot(delta) / (denominator if denominator != 0.0 else 1.0), 0.0, 1.0)
	return point.distance_to(start + delta * t)

static func entry(start: Vector2, finish: Vector2, centre: Vector2, radius: float) -> float:
	var delta := finish - start
	var offset := start - centre
	if offset.length_squared() <= radius * radius:
		return 0.0
	var aa := delta.length_squared()
	var bb := 2.0 * offset.dot(delta)
	var discriminant := bb * bb - 4.0 * aa * (offset.length_squared() - radius * radius)
	if aa <= EPS or discriminant < 0.0:
		return INF
	var t := (-bb - sqrt(discriminant)) / (2.0 * aa)
	return t if t >= 0.0 and t <= 1.0 else INF
