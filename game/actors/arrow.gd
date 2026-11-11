class_name Arrow
extends Area2D
## Bramble's arrow. It leaves the bow at the drawing's arrow_tip anchor on the release frame and
## flies straight along the aim. The node sits on the ground under the arrow (so it y-sorts and
## hits bodies like everything else); the arrow itself is drawn `height` texels above it. It stops at
## solids (layer 1) and at enemies (layer 3), and flies over low solids (layers 1 and 5): docs/physics.md.
## Drawn in the cast's colours (bow wood shaft, steel head, pale fletching) with a dark outline.

const SPEED := 140.0 * Player.DENSITY     ## world px a second
const LIFETIME := 0.9
const KNOCKBACK := 90.0 * Player.DENSITY
const RADIUS := 4.0                       ## the arrow's body on the ground, in texels
const WALLS := 1                          ## layer 1: every solid (docs/physics.md)
const ENEMIES := 4                        ## layer 3
const LOW := 16                           ## layer 5: a solid that stops feet and that a shot flies over

signal struck(target: Node)

var dir := Vector2.RIGHT
var height := 0.0
var _t := 0.0

## Places the arrow at the bow's tip. `archer` is who shot it; left out, it is the player among the arrow's
## own siblings that stands nearest the tip (the player adds its arrow to its own parent), so no tree-wide
## lookup decides it and a second archer in the zone is never mistaken for the first.
func setup(at_ground: Vector2, lift: float, direction: Vector2, archer: Node2D = null) -> void:
	global_position = at_ground
	height = lift
	dir = direction.normalized()
	_start_clear_of_walls(archer if archer != null else _archer_beside(at_ground))

func _archer_beside(tip: Vector2) -> Node2D:
	var best: Node2D = null
	var best_d := INF
	var host := get_parent()
	if host == null:
		return null
	for sibling in host.get_children():
		if sibling is Node2D and sibling.is_in_group("player"):
			var d: float = sibling.global_position.distance_to(tip)
			if d < best_d:
				best = sibling
				best_d = d
	return best

## True for a solid a shot flies over: water, a drop, a bench, a stump (layer 5, set by the zone generators).
static func is_low(body: Object) -> bool:
	return body is CollisionObject2D and (body.collision_layer & LOW) != 0

## The arrow starts at the bow's tip, ahead of the archer. Standing against a wall, that point can lie
## inside or beyond the wall, and the arrow would fly on from there: the Thornback could be freed through
## the closed seal. If a wall stands between the archer's feet and the tip, the arrow starts at the feet
## instead, and the wall stops it in flight like any other (or it flies free, when it is aimed away).
## The path is tested as wide as the arrow is (RADIUS), not as a line: a line could pass a corner that the
## arrow's body then touched at the tip, and the arrow died at the bow without having flown (10 Nov).
func _start_clear_of_walls(archer: Node2D) -> void:
	if archer == null or not is_inside_tree():
		return
	if walled_off(get_world_2d().direct_space_state, archer.global_position, global_position):
		global_position = archer.global_position

## True when a solid that stops shots lies on the way from `from` to `to` for a body RADIUS wide: three
## parallel lines (the middle and both flanks) and the body's place at `to`. Low solids do not count.
static func walled_off(space: PhysicsDirectSpaceState2D, from: Vector2, to: Vector2) -> bool:
	var along := to - from
	var side := along.orthogonal().normalized() * RADIUS if along.length() > 0.01 else Vector2.ZERO
	for offset in [Vector2.ZERO, side, -side]:
		var ray := PhysicsRayQueryParameters2D.create(from + offset, to + offset, WALLS)
		var skip: Array[RID] = []
		for i in 8:                          # step past the low solids on the line
			ray.exclude = skip
			var hit := space.intersect_ray(ray)
			if hit.is_empty():
				break
			if not is_low(hit.collider):
				return true
			skip.append(hit.rid)
	var at := PhysicsShapeQueryParameters2D.new()
	var body := CircleShape2D.new()
	body.radius = RADIUS
	at.shape = body
	at.transform = Transform2D(0.0, to)
	at.collision_mask = WALLS
	for hit in space.intersect_shape(at, 8):
		if not is_low(hit.collider):
			return true
	return false

func _ready() -> void:
	collision_layer = 0
	collision_mask = WALLS | ENEMIES
	monitoring = true
	# monitorable stays on: an area that cannot be monitored does not report the walls (static bodies)
	# it overlaps, and arrows flew through every wall. Its layer is 0, so nothing detects the arrow.
	var shape := CollisionShape2D.new()
	var c := CircleShape2D.new()
	c.radius = RADIUS
	shape.shape = c
	add_child(shape)
	body_entered.connect(_on_body)

func _physics_process(delta: float) -> void:
	_t += delta
	if _t >= LIFETIME:
		queue_free()
		return
	global_position += dir * SPEED * delta
	queue_redraw()

func _on_body(body: Node) -> void:
	if is_low(body):
		return                       # it flies over water, a drop, a bench or a stump
	if body.is_in_group("enemy") and body.has_method("take_hit"):
		body.take_hit(1, dir, KNOCKBACK)
		struck.emit(body)
	queue_free()

func _draw() -> void:
	var tip := Vector2(0, -height).round()
	var tail := (tip - dir * 18.0).round()
	var ink := Color("#2a1c1a")
	draw_line(tail, tip, ink, 3.0)
	draw_line(tail + dir * 2.0, tip - dir * 3.0, Color("#ba7432"), 1.0)
	draw_line(tip - dir * 3.0, tip, Color("#d6dae0"), 1.0)
	draw_line(tail, tail + dir * 3.0, Color("#e4e0da"), 1.0)
