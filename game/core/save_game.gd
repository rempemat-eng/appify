extends Node
## The save: one versioned JSON document in user:// (game-design.md 3, session safety).
## `data` is the live state every system reads and writes; `save()` and `load_save()` move it to and
## from disk. Bump VERSION and add a step to `_migrate` whenever a field changes shape, so old saves load.
## Writes go to a temporary file first and are renamed into place, so a crash never leaves half a save.

signal loaded
signal saved(path: String)

const VERSION := 1
const DEFAULT_PATH := "user://save_0.json"

var data: Dictionary = fresh()
var path := DEFAULT_PATH

static func fresh() -> Dictionary:
	return {
		"version": VERSION,
		"zone": "woodland",
		"spawn": "start",
		"glint": 0,
		"flags": {},
		"quests": {},
		"player": {"hp": 5, "max_hp": 5},
		"settings": {"reduced_motion": false, "pixel_scale": "fill"},
	}

func reset() -> void:
	data = fresh()

# --- flags and Glint ---------------------------------------------------------
func has_flag(flag: String) -> bool:
	return bool(data.flags.get(flag, false))

func set_flag(flag: String, on: bool = true) -> void:
	if on:
		data.flags[flag] = true
	else:
		data.flags.erase(flag)

func add_glint(amount: int) -> void:
	data.glint = int(data.glint) + amount

func setting(key: String, default: Variant = null) -> Variant:
	return data.settings.get(key, default)

# --- disk ----------------------------------------------------------------------
func save(to: String = "") -> Error:
	var target := to if to != "" else path
	var tmp := target + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		push_error("SaveGame: cannot write %s (%s)" % [tmp, error_string(FileAccess.get_open_error())])
		return FileAccess.get_open_error()
	data.version = VERSION
	f.store_string(JSON.stringify(data, "\t", true))
	f.close()
	var err := DirAccess.rename_absolute(tmp, target)
	if err == OK:
		saved.emit(target)
	return err

## Loads `from` (or the default path). A missing file starts a fresh game and returns ERR_FILE_NOT_FOUND.
func load_save(from: String = "") -> Error:
	var source := from if from != "" else path
	if not FileAccess.file_exists(source):
		reset()
		return ERR_FILE_NOT_FOUND
	var json := JSON.new()
	if json.parse(FileAccess.get_file_as_string(source)) != OK or typeof(json.data) != TYPE_DICTIONARY:
		# a warning, not an error: the running game is kept and the broken file is left for inspection
		push_warning("SaveGame: %s is not a save document; keeping the running game" % source)
		return ERR_PARSE_ERROR
	data = _migrate(json.data)
	loaded.emit()
	return OK

## Brings an older document up to VERSION one step at a time, then fills any missing keys from fresh().
## JSON has no integers, so whole numbers are restored here too.
func _migrate(doc: Dictionary) -> Dictionary:
	var v := int(doc.get("version", 0))
	if v > VERSION:
		push_warning("SaveGame: save version %d is newer than this build (%d)" % [v, VERSION])
	# while v < VERSION: match v: 1: ...  (add one step per version bump, then v += 1)
	var out := fresh()
	for k in doc:
		out[k] = doc[k]
	for k in fresh().settings:
		if not out.settings.has(k):
			out.settings[k] = fresh().settings[k]
	out.version = VERSION
	out.glint = int(out.glint)
	out.player.hp = int(out.player.get("hp", 5))
	out.player.max_hp = int(out.player.get("max_hp", 5))
	for q in out.quests.values():
		q.step = int(q.get("step", 0))
	return out
