extends Node
## The save: one versioned JSON document in user:// (game-design.md 3, session safety).
## `data` is the live state every system reads and writes; `save()` and `load_save()` move it to and
## from disk. Bump VERSION and add a step to `_migrate` whenever a field changes shape, so old saves load.
## Writes go to a temporary file first and are renamed into place, so a crash never leaves half a save.

signal loaded
signal saved(path: String)

const VERSION := 1
# JSON numbers must retain exact whole values through Godot's float-based parser.
const MAX_EXACT_INTEGER := 9007199254740991
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
		"village": {"restored": {}},
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
	# Validate a copy before opening the temporary file or changing the live version.
	var err := _document_error(data)
	if err != OK:
		return err
	var document := _migrate(data)
	var target := to if to != "" else path
	# A failed load must not let the next autosave overwrite a newer game's document.
	err = _target_error(target)
	if err != OK:
		return err
	var tmp := target + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return FileAccess.get_open_error()
	f.store_string(JSON.stringify(document, "\t", true))
	f.flush()
	err = f.get_error()
	f.close()
	if err == OK:
		err = DirAccess.rename_absolute(tmp, target)
	if err != OK:
		DirAccess.remove_absolute(tmp)
		return err
	data.version = VERSION
	saved.emit(target)
	return OK

## Missing files start fresh. Invalid, unreadable or future documents preserve the running game.
## Loading never rewrites the source file; a successful explicit save publishes a migrated document.
func load_save(from: String = "") -> Error:
	var source := from if from != "" else path
	if not FileAccess.file_exists(source):
		reset()
		return ERR_FILE_NOT_FOUND
	var f := FileAccess.open(source, FileAccess.READ)
	if f == null:
		return FileAccess.get_open_error()
	var text := f.get_as_text()
	var read_error := f.get_error()
	f.close()
	if read_error != OK and read_error != ERR_FILE_EOF:
		return read_error
	var json := JSON.new()
	if json.parse(text) != OK or typeof(json.data) != TYPE_DICTIONARY:
		return ERR_PARSE_ERROR
	var err := _document_error(json.data)
	if err != OK:
		return err
	data = _migrate(json.data)
	loaded.emit()
	return OK

## Versionless/explicit-0 documents are the legacy partial shape; v1 existed both before
## and after village was added. No gameplay shape changes here, so VERSION stays 1.
## Empty means refused; accepted documents are detached copies, including unknown fields.
func _migrate(doc: Dictionary) -> Dictionary:
	if _document_error(doc) != OK:
		return {}
	var out := doc.duplicate(true)
	var v := int(out.get("version", 0))
	while v < VERSION:
		match v:
			0:
				# v0 -> v1: add the version marker; defaults are filled below.
				v = 1
		out.version = v
	_fill_missing(out, fresh())
	out.version = VERSION
	out.glint = int(out.glint)
	out.player.hp = int(out.player.hp)
	out.player.max_hp = int(out.player.max_hp)
	for r in out.village.restored:
		out.village.restored[r] = int(out.village.restored[r])
	for q in out.quests.values():
		q.step = int(q.get("step", 0))
	return out

func _fill_missing(out: Dictionary, defaults: Dictionary) -> void:
	for key in defaults:
		if not out.has(key):
			var value: Variant = defaults[key]
			out[key] = value.duplicate(true) if value is Dictionary else value
		elif defaults[key] is Dictionary:
			_fill_missing(out[key], defaults[key])

## Validate structure, not story IDs, balances or game rules. Unknown keys stay opaque.
## A future version is refused even when its known fields look compatible.
func _document_error(doc: Dictionary) -> Error:
	var version: Variant = doc.get("version", 0)
	if not _whole_number(version) or version < 0:
		return ERR_INVALID_DATA
	if version > VERSION:
		return ERR_UNAVAILABLE
	for key in ["zone", "spawn"]:
		if doc.has(key) and not doc[key] is String:
			return ERR_INVALID_DATA
	for key in ["flags", "quests", "player", "village", "settings"]:
		if doc.has(key) and not doc[key] is Dictionary:
			return ERR_INVALID_DATA
	if doc.has("glint") and not _whole_number(doc.glint):
		return ERR_INVALID_DATA
	var player: Dictionary = doc.get("player", {})
	for key in ["hp", "max_hp"]:
		if player.has(key) and not _whole_number(player[key]):
			return ERR_INVALID_DATA
	var village: Dictionary = doc.get("village", {})
	if village.has("restored") and not village.restored is Dictionary:
		return ERR_INVALID_DATA
	for tier in village.get("restored", {}).values():
		if not _whole_number(tier):
			return ERR_INVALID_DATA
	for record in doc.get("quests", {}).values():
		if not record is Dictionary:
			return ERR_INVALID_DATA
		if record.has("step") and not _whole_number(record.step):
			return ERR_INVALID_DATA
		if record.has("state") and not record.state is String:
			return ERR_INVALID_DATA
	var settings: Dictionary = doc.get("settings", {})
	if settings.has("reduced_motion") and not settings.reduced_motion is bool:
		return ERR_INVALID_DATA
	if settings.has("pixel_scale") and not settings.pixel_scale is String:
		return ERR_INVALID_DATA
	return OK

func _target_error(target: String) -> Error:
	if not FileAccess.file_exists(target):
		return OK
	var file := FileAccess.open(target, FileAccess.READ)
	if file == null:
		return FileAccess.get_open_error()
	var text := file.get_as_text()
	var err := file.get_error()
	file.close()
	if err != OK and err != ERR_FILE_EOF:
		return err
	var json := JSON.new()
	if json.parse(text) == OK and json.data is Dictionary:
		var version: Variant = json.data.get("version", 0)
		if typeof(version) in [TYPE_INT, TYPE_FLOAT] and version > VERSION:
			return ERR_UNAVAILABLE
	return OK

func _whole_number(value: Variant) -> bool:
	if typeof(value) == TYPE_INT:
		return value >= -MAX_EXACT_INTEGER and value <= MAX_EXACT_INTEGER
	return typeof(value) == TYPE_FLOAT and is_finite(value) and value == floor(value) \
		and value >= -MAX_EXACT_INTEGER and value <= MAX_EXACT_INTEGER
