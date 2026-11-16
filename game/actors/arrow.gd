class_name Arrow
extends Area2D
## Bramble's arrow. It leaves the bow at the drawing's arrow_tip anchor on the release frame and
## flies straight along the aim. The node sits on the ground under the arrow (so it y-sorts and
## hits bodies like everything else); the arrow itself is drawn `height` texels above it. It stops at
## solids (layer 1) and at enemies (layer 3), and flies over low solids (layers 1 and 5): docs/physics.md.
## Drawn in the cast's colours (bow wood shaft, steel head, pale fletching) with a dark outline.
## Where it stops it leaves an Impact (actors/impact.gd, 16 Nov): a star and the arrow stuck in a creature it
## hurt (and a hit-stop), steel streaks and the arrow bouncing off one it glanced off, dust and the arrow stuck
## in a solid, and the arrow falling to the ground at the end of its flight. The arrow itself still goes the
## moment it stops, as before: the effect is drawing only and changes no rule.

const SPEED := 140.0 * Player.DENSITY     ## world px a second
const LIFETIME := 0.9
const KNOCKBACK := 90.0 * Player.DENSITY
const RADIUS := 4.0                       ## the arrow's body on the ground, in texels
const WALLS := 1                          ## layer 1: every solid (docs/physics.md)
const ENEMIES := 4                        ## layer 3
const LOW := 16                           ## layer 5: a solid that stops feet and that a shot flies over
const INK := Color("#2a1c1a")
const WOOD := Color("#ba7432")
const HEAD := Color("#d6dae0")
const FLETCH := Color("#e4e0da")

signal struck(target: Node)

var dir := Vector2.RIGHT
var height := 0.0
var _t := 0.0
var _left := false

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
		_leave(Impact.Kind.DROP)
		queue_free()
		return
	global_position += dir * SPEED * delta
	queue_redraw()

func _on_body(body: Node) -> void:
	if is_low(body):
		return                       # it flies over water, a drop, a bench or a stump
	if body.is_in_group("enemy") and body.has_method("take_hit"):
		# an enemy says whether the hit counted; one that glanced off (enemies/glance.gd) is not reported as
		# struck, so the camera does not shake for it as for a hit
		var counted: Variant = body.take_hit(1, dir, KNOCKBACK)
		if counted == null or bool(counted):
			if _leave(Impact.Kind.HIT, body as Node2D):
				Impact.hit_stop(get_tree())
			struck.emit(body)
		else:
			_leave(Impact.Kind.CLINK, null, body as Node2D)
	else:
		Sound.play(&"arrow_wall")        # it stopped at a solid
		_leave(Impact.Kind.WALL)
	queue_free()

## Leaves the mark of where it stopped, once (two bodies met in one step still count as before, but draw one
## mark). Returns whether it left one.
## `on` is the creature the stuck arrow rides on; `met` the creature it met (for the height of the mark).
func _leave(what: Impact.Kind, on: Node2D = null, met: Node2D = null) -> bool:
	if _left or not is_inside_tree():
		return false
	_left = true
	var lift := Impact.body_lift(met if met != null else on, height)
	return Impact.spawn(get_parent(), what, global_position, lift, dir, true, on) != null

func _draw() -> void:
	draw_arrow(self, Vector2(0, -height), dir, true)

## The arrow drawn on `ci` with its tip at `tip` (local texels), flying along `along`. Without its head it is
## the arrow stuck in something: the shaft ends where the head went in (actors/impact.gd).
static func draw_arrow(ci: CanvasItem, tip: Vector2, along: Vector2, head: bool, alpha := 1.0) -> void:
	if alpha <= 0.0:
		return
	var a := tip.round()
	var tail := (a - along * 18.0).round()
	var end := a if head else (a - along * 3.0).round()
	ci.draw_line(tail, end, Color(INK, alpha), 3.0)
	ci.draw_line(tail + along * 2.0, a - along * 3.0, Color(WOOD, alpha), 1.0)
	if head:
		ci.draw_line(a - along * 3.0, a, Color(HEAD, alpha), 1.0)
	ci.draw_line(tail, tail + along * 3.0, Color(FLETCH, alpha), 1.0)
