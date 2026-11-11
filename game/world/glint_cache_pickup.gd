class_name GlintCachePickup
extends Area2D
## A cache of Glint lying where the player went down (core/glint_cache.gd). Walking over it picks it up.
## It is drawn with the HUD's own Glint mark on a small shadow: one still drawing, nothing loops. Picked
## up, the mark rises and fades for RISE seconds and is gone; under reduced motion it is gone at once.
## No sound (the build has none).

signal collected(glint: int)

const RISE := 0.35
const MARK := preload("res://ui/art/glint.png")

var cache := {}
var _mark: Sprite2D
var _taken := false

func _ready() -> void:
	collision_layer = 0
	collision_mask = 2                      # the player
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 18.0
	shape.shape = circle
	add_child(shape)
	_mark = Sprite2D.new()
	_mark.texture = MARK
	_mark.scale = Vector2(3, 3)             # the HUD mark, one image pixel a world px
	_mark.position = Vector2(0, -12)
	add_child(_mark)
	body_entered.connect(_on_body)

func _draw() -> void:
	draw_set_transform(Vector2(2, 1), 0.0, Vector2(1.0, 0.4))
	draw_circle(Vector2.ZERO, 14.0, Color(0.06, 0.08, 0.04, 0.3))

func _on_body(body: Node) -> void:
	if _taken or not body.is_in_group("player"):
		return
	_taken = true
	var got := GlintCache.collect(cache)
	collected.emit(got)
	set_deferred("monitoring", false)
	if SaveGame.setting("reduced_motion", false):
		queue_free()
		return
	var tween := create_tween().set_parallel(true)
	tween.tween_property(_mark, "position:y", _mark.position.y - 30.0, RISE)
	tween.tween_property(self, "modulate:a", 0.0, RISE)
	tween.chain().tween_callback(queue_free)
