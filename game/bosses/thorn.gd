class_name ThornbackThorn
extends Area2D
## One thorn of the Thornback's volley: drawn by the kit in eight directions (art/thorn.png), it flies
## straight at 70 world px a second (slower than a roll), hurts the player once, and is gone when it
## meets a wall, leaves the arena or has flown its lifetime, so a volley always ends.

const SPEED := 70.0 * 3.0
const LIFETIME := 2.4
const SHEET := "res://bosses/thornback/art/thorn.png"

var direction := Vector2.RIGHT
var arena := Rect2()
var origin := Vector2.ZERO
var finished := false
var _t := 0.0

func _ready() -> void:
	collision_layer = 0
	collision_mask = 1 | 2   # walls and the player
	var shape := CollisionShape2D.new()
	var c := CircleShape2D.new()
	c.radius = 9.0
	shape.shape = c
	add_child(shape)
	var spr := Sprite2D.new()
	spr.texture = load(SHEET)
	spr.hframes = 8
	spr.frame = posmod(int(round(direction.angle() / (PI / 4.0))), 8)
	spr.position = Vector2(0, -12)
	add_child(spr)
	body_entered.connect(_on_body)

func _physics_process(delta: float) -> void:
	advance(delta)

func advance(delta: float) -> void:
	if finished:
		return
	_t += delta
	global_position += direction * SPEED * delta
	if _t >= LIFETIME or (arena.size != Vector2.ZERO and not arena.grow(24.0).has_point(global_position - origin)):
		finish()

func finish() -> void:
	finished = true
	queue_free()

func _on_body(body: Node) -> void:
	if finished:
		return
	if body.is_in_group("player"):
		if body.has_method("take_damage"):
			body.take_damage(1, direction)
		finish()
	elif not body.is_in_group("enemy"):
		finish()
