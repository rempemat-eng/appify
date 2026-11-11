extends Node
## The zone loader. Zones are scenes listed in res://data/zones.json ({"woodland": "res://zones/...tscn"}).
## The game scene calls `attach(root, player)` once; `go_to(zone, spawn)` then swaps the zone under `root`,
## moves the one player into the new zone's Actors node at the named spawn, records where the player is in
## the save (and the flag "visited:<zone>"), and emits `zone_changed`. Doors (world/door.gd) call it; so does loading a save.

signal zone_changing(zone_id: String)
signal zone_changed(zone: Zone)

const TABLE := "res://data/zones.json"

var table: Dictionary = {}
var root: Node
var player: Node2D
var current: Zone
var _busy := false

func _ready() -> void:
	var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(TABLE))
	table = doc if typeof(doc) == TYPE_DICTIONARY else {}

func attach(zone_root: Node, the_player: Node2D) -> void:
	root = zone_root
	player = the_player

func has_zone(zone_id: String) -> bool:
	return table.has(zone_id) and ResourceLoader.exists(table[zone_id])

## Loads `zone_id` and places the player at `spawn` (a Marker2D name in the zone's Spawns or Stands).
## Returns false, and leaves the current zone alone, when the zone is not built yet.
func go_to(zone_id: String, spawn: String = "start") -> bool:
	if _busy or root == null:
		return false
	if not has_zone(zone_id):
		push_warning("Zones: '%s' is not built yet (data/zones.json)" % zone_id)
		return false
	_busy = true
	zone_changing.emit(zone_id)
	Quests.zone_loading()
	var next: Zone = (load(table[zone_id]) as PackedScene).instantiate()
	if current != null:
		if player != null and player.get_parent() == current.actors:
			current.actors.remove_child(player)
		root.remove_child(current)
		current.queue_free()
	root.add_child(next)
	current = next
	if player != null:
		if player.get_parent() != null:
			player.get_parent().remove_child(player)
		next.actors.add_child(player)
		player.global_position = next.spawn_position(spawn)
		if player.has_method("reset_motion"):
			player.reset_motion()
		_face_into(next)
	SaveGame.data.zone = zone_id
	SaveGame.data.spawn = spawn
	SaveGame.set_flag("visited:" + zone_id)
	Quests.notify("enter:" + zone_id)
	_busy = false
	zone_changed.emit(next)
	return true

const ARRIVAL_DOOR := 120.0   ## texels: a spawn this near a door is where that door's arrivals stand

## Arriving beside a door, the player looks away from it, into the zone (down the Undercroft's hall, not
## at the wall the hatch stair came through). It sets the aim the body's facing follows; a mouse or a
## stick aims again as soon as it is read, so this is what a player sees who has touched neither.
func _face_into(zone: Zone) -> void:
	var doors := zone.get_node_or_null("Doors")
	if doors == null or not "aim" in player:
		return
	var nearest: Node2D = null
	for d in doors.get_children():
		var door := d as Node2D
		if door != null and (nearest == null or door.global_position.distance_squared_to(player.global_position)
				< nearest.global_position.distance_squared_to(player.global_position)):
			nearest = door
	if nearest == null or nearest.global_position.distance_to(player.global_position) > ARRIVAL_DOOR:
		return
	var away := player.global_position - nearest.global_position
	var dir := Vector2(signf(away.x), 0.0) if absf(away.x) >= absf(away.y) else Vector2(0.0, signf(away.y))
	player.set("aim", dir)
	if "facing" in player:
		player.set("facing", CastSprite.facing_for(dir, String(player.get("facing"))))
