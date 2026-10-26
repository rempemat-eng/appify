class_name FreedCreature
extends Node2D
## A creature that has just been freed (game-design 4: the shard pops out, it shakes itself, calms
## and runs off): plays `freed` where it fell, then `freed_move` away from the player and fades
## out. Finite (gone after LEAVE seconds of walking); under reduced motion it calms in place and
## fades without walking. Looks only: no rewards, collisions or saves.

const LEAVE := 1.6
const FADE := 0.6
const SHARD := preload("res://assets/enemies/shard.png")

var character := ""
var facing := "S"
var away := Vector2.DOWN
var sprite: CastSprite
var _t := 0.0

func _ready() -> void:
	sprite = CastSprite.new()
	sprite.name = "Sprite"
	add_child(sprite)
	if not sprite.load_character(character):
		queue_free()
		return
	sprite.play_clip("freed", facing, true)
	if not SaveGame.setting("reduced_motion", false):
		_pop_shard()

## The shard leaves the creature as its own finite effect: it rises from where it was lodged,
## tumbles and fades (the drawings only show it working loose).
func _pop_shard() -> void:
	var s := Sprite2D.new()
	s.texture = SHARD
	s.position = sprite.anchor("shard", 1)
	add_child(s)
	var t := create_tween().set_parallel(true)
	t.tween_property(s, "position", s.position + Vector2(10, -42), 0.55).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	t.tween_property(s, "rotation", 2.6, 0.55)
	t.tween_property(s, "modulate:a", 0.0, 0.25).set_delay(0.35)
	t.chain().tween_callback(s.queue_free)

func _process(delta: float) -> void:
	if sprite == null:
		return
	var reduced: bool = SaveGame.setting("reduced_motion", false)
	if sprite.clip == "freed":
		sprite.advance(delta)
		if sprite.finished:
			if reduced:
				sprite.play_clip("idle", facing, true)
			else:
				sprite.play_clip("freed_move", CastSprite.facing_for(away, facing), true)
		return
	_t += delta
	if not reduced:
		sprite.advance(delta)
		position += away * maxf(sprite.walk_speed(), 20.0) * delta
	modulate.a = clampf((LEAVE - _t) / FADE, 0.0, 1.0)
	if _t >= LEAVE:
		queue_free()
