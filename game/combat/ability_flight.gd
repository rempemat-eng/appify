class_name AbilityFlight
extends RefCounted
## One canonical 1/60s player-projectile step. Pure snapshots/impact commands, never world HP.
## The future dispatcher must apply each impact synchronously before the next projectile tick.
## Targets: {id, position: Vector2, radius, hp}; seals: {position, radius, remaining}.
const STEP := 1.0 / 60.0
const EPS := 1.0e-8

static func tick(source: Dictionary, targets: Array[Dictionary] = [],
		seals: Array[Dictionary] = [], bounds := Rect2(0, 16, 320, 164)) -> Dictionary:
	# Compatibility boundary for Vector2 callers. Canonical snapshots use tick_scalar so
	# converting to float32 cannot change strict arena/contact/entry decisions.
	var shot := source.duplicate(true)
	shot.position = _point(source.position)
	shot.velocity = _point(source.velocity)
	var scalar_targets := _scalar_positions(targets)
	var scalar_seals := _scalar_positions(seals)
	var result := tick_scalar(shot, scalar_targets, scalar_seals,
		{"left": bounds.position.x, "top": bounds.position.y,
		 "right": bounds.end.x, "bottom": bounds.end.y})
	_vector_shot(result.shot)
	for event in result.events:
		if event.has("shot"):
			_vector_shot(event.shot)
		if event.has("position"):
			event.position = Vector2(event.position.x, event.position.y)
	return result

static func _point(value: Vector2) -> Dictionary:
	return {"x": float(value.x), "y": float(value.y)}

static func _scalar_positions(items: Array[Dictionary]) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for item in items:
		var copy := item.duplicate(true)
		copy.position = _point(item.position)
		result.append(copy)
	return result

static func _vector_shot(shot: Dictionary) -> void:
	shot.position = Vector2(shot.position.x, shot.position.y)
	shot.velocity = Vector2(shot.velocity.x, shot.velocity.y)

## Double-precision x/y dictionaries for position/velocity, including targets and seals.
## This is the same core as tick; no Vector2 conversion occurs before gameplay decisions.
static func tick_scalar(source: Dictionary, targets: Array[Dictionary] = [],
		seals: Array[Dictionary] = [], bounds := {"left": 0.0, "top": 16.0, "right": 320.0, "bottom": 180.0}) -> Dictionary:
	assert(source.owner == "player", "Enemy projectile/decoy/guard handling is a separate port step")
	var shot := source.duplicate(true)
	var events: Array[Dictionary] = []
	var start: Dictionary = shot.position.duplicate()
	var dt := minf(STEP, maxf(0.0, float(shot.remaining)))
	shot.age += dt
	shot.position.x += float(shot.velocity.x) * dt
	shot.position.y += float(shot.velocity.y) * dt
	shot.remaining -= STEP
	var finish: Dictionary = shot.position.duplicate()
	if shot.kind == "water" and not shot.get("amplified", false):
		var seal_t := INF
		var target_t := INF
		for seal in seals:
			if float(seal.remaining) > 0.0:
				seal_t = minf(seal_t, _entry(start, finish, seal.position, float(seal.radius)))
		for target in targets:
			if _eligible(target, shot):
				target_t = minf(target_t, _entry(start, finish, target.position,
					float(target.radius) + float(shot.radius)))
		if seal_t != INF and seal_t <= target_t:
			shot.amplified = true
			shot.damage = 28.0
			shot.radius = 6.0
			shot.pierce = 1
			events.append({"type": "water-shaped", "position": {"x": start.x + (finish.x - start.x) * seal_t, "y": start.y + (finish.y - start.y) * seal_t}})
	var contacts: Array[Dictionary] = []
	for target in targets:
		if _eligible(target, shot) and _distance_to_segment(target.position, start, finish) <= float(target.radius) + float(shot.radius):
			contacts.append(target)
	# Original F sorts by centre distance from the segment start, with stable ties.
	# This is deliberately not a newly designed earliest-circle-entry ordering.
	for i in range(1, contacts.size()):
		var value := contacts[i]
		var j := i
		while j > 0 and _distance(start, contacts[j - 1].position) > _distance(start, value.position):
			contacts[j] = contacts[j - 1]
			j -= 1
		contacts[j] = value
	for target in contacts:
		if float(shot.blast_radius) > 0.0 or shot.kind == "flask":
			shot.position = target.position.duplicate()
		# T observes the previous hit_ids; insertion follows impact (powered arrow root transfer).
		events.append({"type": "impact", "target_id": target.id, "shot": shot.duplicate(true)})
		shot.hit_ids.append(target.id)
		if int(shot.pierce) <= 0:
			return {"alive": false, "shot": shot, "events": events}
		shot.pierce -= 1
	var pos: Dictionary = shot.position
	# Original bounds include the right/bottom edges (Rect2.has_point does not).
	var outside: bool = pos.x < bounds.left or pos.x > bounds.right or pos.y < bounds.top or pos.y > bounds.bottom
	if float(shot.remaining) <= EPS or outside:
		if shot.kind == "flask" or float(shot.blast_radius) > 0.0:
			events.append({"type": "impact", "target_id": null, "shot": shot.duplicate(true)})
		return {"alive": false, "shot": shot, "events": events}
	return {"alive": true, "shot": shot, "events": events}

static func _eligible(target: Dictionary, shot: Dictionary) -> bool:
	return float(target.hp) > 0.0 and not target.id in shot.hit_ids

static func _distance(a: Dictionary, b: Dictionary) -> float:
	var dx := float(a.x) - float(b.x)
	var dy := float(a.y) - float(b.y)
	return sqrt(dx * dx + dy * dy)

static func distance_to_segment(point: Vector2, start: Vector2, finish: Vector2) -> float:
	return _distance_to_segment(_point(point), _point(start), _point(finish))

static func _distance_to_segment(point: Dictionary, start: Dictionary, finish: Dictionary) -> float:
	var dx := float(finish.x) - float(start.x)
	var dy := float(finish.y) - float(start.y)
	var denominator := dx * dx + dy * dy
	var t := clampf(((float(point.x) - float(start.x)) * dx + (float(point.y) - float(start.y)) * dy) / (denominator if denominator != 0.0 else 1.0), 0.0, 1.0)
	return _distance(point, {"x": float(start.x) + dx * t, "y": float(start.y) + dy * t})

static func entry(start: Vector2, finish: Vector2, centre: Vector2, radius: float) -> float:
	return _entry(_point(start), _point(finish), _point(centre), radius)

static func _entry(start: Dictionary, finish: Dictionary, centre: Dictionary, radius: float) -> float:
	var dx := float(finish.x) - float(start.x)
	var dy := float(finish.y) - float(start.y)
	var ox := float(start.x) - float(centre.x)
	var oy := float(start.y) - float(centre.y)
	var offset_sq := ox * ox + oy * oy
	if offset_sq <= radius * radius:
		return 0.0
	var aa := dx * dx + dy * dy
	var bb := 2.0 * (ox * dx + oy * dy)
	var discriminant := bb * bb - 4.0 * aa * (offset_sq - radius * radius)
	if aa <= EPS or discriminant < 0.0:
		return INF
	var t := (-bb - sqrt(discriminant)) / (2.0 * aa)
	return t if t >= 0.0 and t <= 1.0 else INF
