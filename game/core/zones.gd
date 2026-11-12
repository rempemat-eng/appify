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
	if OS.is_debug_build():
		try_zones(OS.get_cmdline_user_args())

## `--try-zone=<id>` (debug builds only, as --play): a zone that is built (res://zones/<id>/<id>.tscn) but
## not yet in data/zones.json, because nothing in the world leads to it yet, joins the table for this run,
## so a playtest route can start in it (tools/playtest.sh, a route's `#! args:` line). While it is in the
## table, "zone_built:<id>" holds as it will once the zone is listed. Returns the ids added.
func try_zones(args: PackedStringArray) -> PackedStringArray:
	var added := PackedStringArray()
	for a in args:
		if not a.begins_with("--try-zone="):
			continue
		var id := a.trim_prefix("--try-zone=")
		var path := "res://zones/%s/%s.tscn" % [id, id]
		if id.is_valid_identifier() and not table.has(id) and ResourceLoader.exists(path):
			table[id] = path
			added.append(id)
	return added

func attach(zone_root: Node, the_player: Node2D) -> void:
	root = zone_root
	player = the_player

## A zone built from a lab plan (its ground says `lab`): kitlab, the Brackens lab, woodland_kit.
static func is_lab(zone: Node) -> bool:
	if zone == null:
		return false
	var ground := zone.get_node_or_null("Ground")
	return ground != null and ground.get("lab") == true

## True while the player stands in a lab zone: no autosave, no story card, no quest on the HUD.
func in_lab() -> bool:
	return current != null and is_instance_valid(current) and is_lab(current)

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
	# A lab zone (an editor test bed, started by name) is never where the game resumes: the save
	# keeps the zone the player came from, and the lab leaves no "visited" mark. Before this, one
	# start of a lab made it the save's zone, so every later start opened inside it with no door out.
	if is_lab(next):
		if SaveGame.resume.is_empty():
			# a save made before this rule may already name the lab: it resumes at the game's start
			var fresh := SaveGame.fresh()
			var from_lab := String(SaveGame.data.zone) == zone_id
			SaveGame.resume = {"zone": fresh.zone if from_lab else String(SaveGame.data.zone),
				"spawn": fresh.spawn if from_lab else String(SaveGame.data.spawn)}
			# nothing is autosaved in a lab, so that one save is made at once (game.gd autosave),
			# or the file would go on naming the lab and every start would open in it again
			SaveGame.resume_unsaved = from_lab
	else:
		SaveGame.resume = {}
		SaveGame.set_flag("visited:" + zone_id)
	SaveGame.data.zone = zone_id
	SaveGame.data.spawn = spawn
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
