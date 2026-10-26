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
	var files := Array(DirAccess.get_files_at(DIR))
	files.sort()
	for f in files:
		if f.ends_with(".json"):
			var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(DIR.path_join(f)))
			if typeof(doc) == TYPE_DICTIONARY:
				add_doc(doc)
			else:
				push_error("Dialogue: %s is not a JSON object" % f)

## Adds one file's speakers. A speaker named in several files (an act's file adding lines to the
## slice's Moss, say) keeps the first file's name and gets every file's entries, ordered by each
## entry's optional "priority" (default 0, higher first); equal priorities keep file order.
func add_doc(doc: Dictionary) -> void:
	for id in doc:
		var sp: Dictionary = doc[id]
		if not speakers.has(id):
			speakers[id] = {"name": sp.get("name", id), "entries": []}
		var all: Array = speakers[id].entries + sp.get("entries", [])
		var keyed := []
		for i in all.size():
			keyed.append([-int(all[i].get("priority", 0)), i, all[i]])
		keyed.sort()
		speakers[id].entries = keyed.map(func(k): return k[2])

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
