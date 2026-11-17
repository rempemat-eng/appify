class_name Zone
extends Node2D
## The root of a playable zone scene (zones/<id>/<id>.tscn). Expected children:
##   Base     the generated <id>_base.tscn (ground, water, y-sorted Objects, Walls, Stands)
##   Actors   a y-sorted Node2D: the player, people, camps and enemies go here
##   Spawns   Marker2D nodes named for where doors and saves put the player (falls back to Base/Stands)
## The root and Base are y-sorted too, so actors sort against the base's trees and stones.
## Every zone gets an Occlusion child (world/occlusion.gd): the faint copy that keeps the player and the
## enemies readable behind tall scenery. docs/physics.md has the whole model.

@export var zone_id := ""
@export var bounds := Rect2()  ## camera limits in texels; empty means the Base ground's size

var occlusion: Occlusion

@onready var actors: Node2D = $Actors

func _ready() -> void:
	y_sort_enabled = true
	occlusion = Occlusion.new()
	occlusion.zone = self
	add_child(occlusion)
	if bounds.size == Vector2.ZERO:
		var ground := get_node_or_null("Base/Ground") as Sprite2D
		if ground != null and ground.texture != null:
			bounds = Rect2(Vector2.ZERO, ground.texture.get_size())
	Quests.started.connect(_on_quest_started)
	Impact.prepare_ground(self)   # the dust's tone grid, built as the zone is made, not on its first puff

## A quest with `walks_off` {speaker, zone, toward: [x, y] texels} that starts in this zone sends that
## speaker ahead: she walks off toward the point and is gone (world/walk_off.gd). The quest's own flags
## place her from the next zone load (road_to_crossroads: `next_visit_flags`).
func _on_quest_started(id: String) -> void:
	var off: Variant = Quests.defs.get(id, {}).get("walks_off")
	if typeof(off) != TYPE_DICTIONARY or String(off.get("zone", "")) != zone_id:
		return
	var toward: Array = off.get("toward", [])
	for it in find_children("*", "Area2D", true, false):
		if it is Interactable and (it as Interactable).speaker_id == String(off.get("speaker", "")) and not (it as Interactable).leaving \
				and (it as Interactable).is_visible_in_tree() and toward.size() == 2:
			var walk := WalkOff.new()
			walk.name = "WalkOff"
			walk.who = it
			walk.toward = Vector2(float(toward[0]), float(toward[1]))
			it.add_child(walk)

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
