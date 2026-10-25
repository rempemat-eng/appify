extends Node
## Minimal dialogue: who says what, chosen by quest state. Data lives in res://data/dialogue/*.json:
##
##   { "stone_sign": { "name": "Weathered sign",
##                     "entries": [ { "if": { "done": ["woodland_stones"] }, "lines": ["..."] },
##                                  { "lines": ["the default, last"] } ] } }
##
## `talk(id)` picks the first entry whose condition holds (Quests.check), shows its lines through
## whatever box listens to `opened` (ui/dialogue_box.gd), waits for `closed`, then reports
## "talk:<id>" to Quests. With no box listening (tests, headless checks) it closes at once.
## Dialogic was considered and not adopted yet: see docs/godot.md.

signal opened(speaker: String, lines: PackedStringArray)
signal closed

const DIR := "res://data/dialogue"

var speakers: Dictionary = {}
var busy := false

func _ready() -> void:
	for f in DirAccess.get_files_at(DIR):
		if f.ends_with(".json"):
			var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(DIR.path_join(f)))
			if typeof(doc) == TYPE_DICTIONARY:
				speakers.merge(doc, true)
			else:
				push_error("Dialogue: %s is not a JSON object" % f)

func lines_for(id: String) -> PackedStringArray:
	var sp: Dictionary = speakers.get(id, {})
	for e in sp.get("entries", []):
		if Quests.check(e.get("if")):
			return PackedStringArray(e.get("lines", []))
	return PackedStringArray()

func talk(id: String) -> void:
	if busy:
		return
	var lines := lines_for(id)
	if not lines.is_empty():
		busy = true
		if opened.get_connections().is_empty():
			busy = false
		else:
			opened.emit(speakers[id].get("name", id), lines)
			await closed
			# stay busy a moment, so the key that closed the box does not reopen it or swing
			await get_tree().create_timer(0.15).timeout
			busy = false
	Quests.notify("talk:" + id)
