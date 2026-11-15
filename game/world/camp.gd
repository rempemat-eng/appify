class_name Camp
extends Node2D
## A group of enemies that counts as one fight. Its child enemies report `died`; when the last one falls
## the camp sets the flag "camp_cleared:<camp_id>" and reports "camp:<camp_id>" to the quests. A cleared
## camp stays cleared: on load it removes its enemies. Each creature freed pays its Glint once for the life
## of the save (core/glint_cache.gd): a camp that is back after a zone reload or a defeat pays nothing again.
##
## A camp spread over several rooms is one camp for each room (data/camps.json, 15 Nov: the Undercroft's
## five creatures were one camp, so going down in the third room brought the first two back). A room's
## camp follows the same rules on its own: its last creature freed sets "camp_cleared:<room camp id>" and
## reports "camp:<room camp id>", and its creatures are gone on every later load. The whole camp is
## cleared, as before, when its last creature falls, which is when its last room is cleared. Creatures
## keep paying under the whole camp's id, so "paid once" holds across the change.

signal cleared

const ROOMS := "res://data/camps.json"

@export var camp_id := ""

var _left := 0
var _room_of := {}       ## creature node name -> its room's camp id (only for a camp of rooms)
var _room_left := {}     ## room camp id -> creatures of it not yet freed

static var _rooms := {}

## The room camps of camp `id`: [{id, room, creatures: [node names]}], or [] for a camp that is one camp.
static func rooms_of(id: String) -> Array:
	if _rooms.is_empty():
		var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(ROOMS)) if FileAccess.file_exists(ROOMS) else null
		_rooms = doc if typeof(doc) == TYPE_DICTIONARY else {"_none": true}
	var entry: Variant = _rooms.get(id)
	return entry.get("rooms", []) if typeof(entry) == TYPE_DICTIONARY else []

func _ready() -> void:
	y_sort_enabled = true
	if SaveGame.has_flag("camp_cleared:" + camp_id):
		for c in get_children():
			c.queue_free()
		return
	for room: Dictionary in rooms_of(camp_id):
		for creature: String in room.get("creatures", []):
			_room_of[creature] = String(room.id)
	for c in get_children():
		if c.has_signal("died"):
			var room := String(_room_of.get(String(c.name), ""))
			if room != "" and SaveGame.has_flag("camp_cleared:" + room):
				c.queue_free()             # its room is cleared: it stays empty, as a whole camp does
				continue
			_left += 1
			if room != "":
				_room_left[room] = int(_room_left.get(room, 0)) + 1
			c.died.connect(_on_died.bind(c))
	if _left <= 0 and not _room_of.is_empty():
		_clear.call_deferred()             # every room was cleared, and the save lacks only the whole camp's flag

func is_cleared() -> bool:
	return SaveGame.has_flag("camp_cleared:" + camp_id)

## True once the room camp `room_id` of this camp is cleared (the whole camp cleared counts).
func room_cleared(room_id: String) -> bool:
	return is_cleared() or SaveGame.has_flag("camp_cleared:" + room_id)

static func kind_of(creature: Node) -> String:
	return "boss" if creature is Thornback else ("creature" if creature is SliceEnemy else "mossling")

func _on_died(who: Node) -> void:
	GlintCache.pay_once("%s/%s" % [camp_id, who.name], kind_of(who))
	var room := String(_room_of.get(String(who.name), ""))
	if room != "":
		_room_left[room] = int(_room_left.get(room, 0)) - 1
		if int(_room_left[room]) <= 0 and not SaveGame.has_flag("camp_cleared:" + room):
			SaveGame.set_flag("camp_cleared:" + room)
			Quests.notify("camp:" + room)
	_left -= 1
	if _left <= 0:
		_clear()

func _clear() -> void:
	if is_cleared():
		return
	SaveGame.set_flag("camp_cleared:" + camp_id)
	Quests.notify("camp:" + camp_id)
	cleared.emit()
