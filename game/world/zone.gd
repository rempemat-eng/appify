class_name Zone
extends Node2D
## The root of a playable zone scene (zones/<id>/<id>.tscn). Expected children:
##   Base     the generated <id>_base.tscn (ground, water, y-sorted Objects, Walls, Stands)
##   Actors   a y-sorted Node2D: the player, people, camps and enemies go here
##   Spawns   Marker2D nodes named for where doors and saves put the player (falls back to Base/Stands)
## The root and Base are y-sorted too, so actors sort against the base's trees and stones.

@export var zone_id := ""
@export var bounds := Rect2()  ## camera limits in texels; empty means the Base ground's size

@onready var actors: Node2D = $Actors

func _ready() -> void:
	y_sort_enabled = true
	if bounds.size == Vector2.ZERO:
		var ground := get_node_or_null("Base/Ground") as Sprite2D
		if ground != null and ground.texture != null:
			bounds = Rect2(Vector2.ZERO, ground.texture.get_size())

func spawn_position(spawn: String) -> Vector2:
	for path in ["Spawns/" + spawn, "Base/Stands/" + spawn]:
		var m := get_node_or_null(path) as Node2D
		if m != null:
			return m.global_position
	push_warning("Zone %s: no spawn '%s', using the first" % [zone_id, spawn])
	var spawns := get_node_or_null("Spawns")
	if spawns != null and spawns.get_child_count() > 0:
		return (spawns.get_child(0) as Node2D).global_position
	return bounds.get_center()
