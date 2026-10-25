class_name Arrow
extends Area2D
## Bramble's arrow. It leaves the bow at the drawing's arrow_tip anchor on the release frame and
## flies straight along the aim. The node sits on the ground under the arrow (so it y-sorts and
## hits bodies like everything else); the arrow itself is drawn `height` texels above it.
## Drawn in the cast's colours (bow wood shaft, steel head, pale fletching) with a dark outline.

const SPEED := 140.0 * Player.DENSITY     ## world px a second
const LIFETIME := 0.9
const KNOCKBACK := 90.0 * Player.DENSITY

signal struck(target: Node)

var dir := Vector2.RIGHT
var height := 0.0
var _t := 0.0

func setup(at_ground: Vector2, lift: float, direction: Vector2) -> void:
	global_position = at_ground
	height = lift
	dir = direction.normalized()

func _ready() -> void:
	collision_layer = 0
	collision_mask = 1 | 4           # walls and enemies
	monitoring = true
	monitorable = false
	var shape := CollisionShape2D.new()
	var c := CircleShape2D.new()
	c.radius = 4.0
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
