class_name WalkOff
extends Node
## Somebody sets off ahead of the player and is gone (15 Nov: Hale said she would be right behind
## Bramble and then stood by her tree until the next zone loaded). Added to an Interactable by its zone
## when a quest with `walks_off` starts (world/zone.gd, data/quests/road_to_crossroads.json): from that
## moment there is nothing to talk to here, her post no longer blocks the path, and she walks toward
## `toward` at her own walking pace for LEAVE seconds, fading out over the last FADE, as a freed
## creature does. Finite; under reduced motion she is gone as the talk closes, with no walk and no fade.
## Looks and the talk area only: the quest's own flags say where she stands from the next zone load.

const LEAVE := 1.6
const FADE := 0.6

var who: Interactable
var toward := Vector2.ZERO           ## a point in the zone, in texels
var _dir := Vector2.ZERO
var _speed := 0.0
var _t := 0.0

func _ready() -> void:
	if who == null:
		who = get_parent() as Interactable
	if who == null:
		queue_free()
		return
	who.leaving = true
	who.queue_redraw()                           # the "!" goes with her
	for c in who.get_children():
		if c is CollisionObject2D:               # her post: nothing to walk round once she has left it
			(c as CollisionObject2D).collision_layer = 0
	var player := get_tree().get_first_node_in_group("player")
	if player != null:
		Interactable.refocus(player)
	_dir = (toward - who.global_position).normalized()
	var body := _body()
	_speed = body.walk_speed() if body != null else 0.0
	if _speed <= 0.0 or _dir == Vector2.ZERO or SaveGame.setting("reduced_motion", false):
		_gone()
		return
	body.walking = _dir

func _body() -> Villager:
	for c in who.get_children():
		if c is Villager:
			return c
	return null

## How far she goes before she is gone, in texels (the tests hold this stretch free of solids).
static func reach(speed: float) -> float:
	return speed * LEAVE

func _process(delta: float) -> void:
	_t += delta
	if _t >= LEAVE:
		_gone()
		return
	who.position += _dir * _speed * delta
	who.modulate.a = clampf((LEAVE - _t) / FADE, 0.0, 1.0)

func _gone() -> void:
	who.visible = false
	who.modulate.a = 1.0
	var body := _body()
	if body != null:
		body.walking = Vector2.ZERO
	set_process(false)
	queue_free()
