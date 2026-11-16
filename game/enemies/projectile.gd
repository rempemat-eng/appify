class_name SliceEnemyShot
extends Node2D
## Slow, finite shot; physics ray prevents tunnelling and stops at solid cover. Like the player's arrow it
## flies over low solids (a bench, a stump, water: Arrow.is_low, docs/physics.md), so cover works both ways.
## Where it breaks it leaves a splat in the seed's colours (actors/impact.gd, 16 Nov): on the player (whose
## own hurt flash and cue follow), on a solid (with the `shot_wall` cue) and, smaller, where it falls at the end
## of its flight. Drawing and sound only: no rule changes.
const LIFT := 6.0          # the seed is drawn this far above the shot's ground point (creature_look.gd)
const SPEED := 80.0 * 3.0  # less than the player's 100 world px/s dodge
var direction := Vector2.RIGHT
var lifetime := 1.4
var damage := 1
var source: Node
var finished := false

func _physics_process(delta: float) -> void:
	if finished:
		return
	var next := global_position + direction * SPEED * delta
	var query := PhysicsRayQueryParameters2D.create(global_position, next, 3)
	var hit := {}
	var skip: Array[RID] = []
	for i in 8:                              # step past the low solids on this stretch
		query.exclude = skip
		hit = get_world_2d().direct_space_state.intersect_ray(query)
		if hit.is_empty() or not Arrow.is_low(hit.collider):
			break
		skip.append(hit.rid)
		hit = {}
	if not hit.is_empty():
		var body: Object = hit.collider
		if body.has_method("take_damage"):
			body.take_damage(damage, direction)
		else:
			Sound.play(&"shot_wall")
		Impact.spawn(get_parent(), Impact.Kind.SPLAT, hit.position, LIFT, direction, false, null, Impact.SEED_TINT)
		finish()
		return
	global_position = next
	lifetime -= delta
	if lifetime <= 0.0:
		Impact.spawn(get_parent(), Impact.Kind.SPLAT, global_position, 0.0, direction, false, null, Impact.SEED_TINT)
		finish()

func finish() -> void:
	if finished:
		return
	finished = true
	queue_free()

func _draw() -> void:
	draw_circle(Vector2.ZERO, 5.0, Color(1.0, 0.8, 0.35))
