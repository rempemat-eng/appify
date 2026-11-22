extends Node
## The save: one versioned JSON document in user:// (game-design.md 3, session safety).
## `data` is the live state every system reads and writes; `save()` and `load_save()` move it to and
## from disk. Bump VERSION and add a step to `_migrate` whenever a field changes shape, so old saves load.
## Writes go to a temporary file first and are renamed into place, so a crash never leaves half a save.
##
## The save is read once, when the process starts (`-- --fresh` skips it). The game scene never reads the
## disk itself: it plays whatever `data` holds, so a test that instances it gets the state the test set
## up and not a file an earlier test happened to write.

signal loaded
signal saved(path: String)

const VERSION := 2
# JSON numbers must retain exact whole values through Godot's float-based parser.
const MAX_EXACT_INTEGER := 9007199254740991
const DEFAULT_PATH := "user://save_0.json"
## The raid record's states (core/raids.gd STATES; kept here so the save does not depend on the autoload).
const RAID_STATES := ["none", "announced", "postponed", "pending", "running", "won", "lost"]
## The sound settings and their defaults (version 2; ui/sound_menu.gd shows them, core/sound.gd reads them).
const SOUND_SETTINGS := {"sound_effects": true, "ambience": true, "gentle_sound": false}
## The pixel scales main/pixel_screen.gd knows; the first is the default.
const PIXEL_SCALES := ["fill", "whole"]

var data: Dictionary = fresh()
var path := DEFAULT_PATH

## What reading the save at start came to: OK, ERR_FILE_NOT_FOUND (a new game), ERR_PARSE_ERROR or
## ERR_INVALID_DATA (a damaged file, kept aside), ERR_UNAVAILABLE (a newer game's save, left alone).
var boot_error: Error = OK

## A failed old-folder import must not be hidden by a fresh autosave in the new folder.
## Explicit saves to other paths remain available; boot retries the import next time.
var _legacy_import_target := ""
var _legacy_import_error: Error = OK

## Where the game resumes while the player is in a lab zone (Zones.go_to sets it on entering one and
## clears it on leaving): a save made meanwhile names this zone and spawn, never the lab's.
var resume: Dictionary = {}
## True when the save on disk still names a lab and `resume` has not been written yet.
var resume_unsaved := false

func _ready() -> void:
	# the test build keeps a save of its own and never writes the real one (core/test_build.gd)
	if TestBuild.on():
		path = TestBuild.SAVE_PATH
	boot(OS.get_cmdline_user_args().has("--fresh"))

## Reads the save once, when the process starts. A file that cannot be read as a save is copied to
## "<path>.broken" before the new game's first autosave writes over it; a save from a newer version of
## the game is left alone, and `save()` goes on refusing to overwrite it (the game says so: game.gd).
func boot(fresh_start := false) -> Error:
	boot_error = OK
	_legacy_import_target = ""
	_legacy_import_error = OK
	if fresh_start:
		return OK
	var legacy := _legacy_save_path()
	if legacy != "":
		boot_error = _import_legacy_save(legacy, path)
		if boot_error != OK:
			return boot_error
	var real := _test_build_seed()
	if real != "":
		# the test build's first start goes on from the real game: a byte copy of the real save, made only
		# while the test build has no save of its own. The real file is read, never written.
		var copied := _copy_legacy_save(real, path)
		if copied != OK:
			push_warning("SaveGame: the test build could not copy the real save (error %d); it starts afresh" % copied)
	boot_error = load_save()
	if boot_error == ERR_PARSE_ERROR or boot_error == ERR_INVALID_DATA:
		var file := ProjectSettings.globalize_path(path)
		DirAccess.copy_absolute(file, file + ".broken")
	return boot_error

## Both names use Godot's custom user directory. Derive their shared desktop parent from
## the OS path (not user://, whose trailing slash would select the wrong parent).
## Explicit/custom save paths and --fresh never search another directory for progress.
func _legacy_save_path() -> String:
	if path != DEFAULT_PATH:
		return ""
	return _legacy_folder_save()

## The old folder's save (napattack/save_0.json beside this game's user folder), wherever `path` points.
func _legacy_folder_save() -> String:
	return OS.get_user_data_dir().get_base_dir().path_join("napattack/save_0.json")

## The real save as this game keeps it (the test build reads it, never writes it).
func _real_save_path() -> String:
	return DEFAULT_PATH

## The real save a test build's own save starts as (core/test_build.gd), or "" outside the test build:
## save_0.json, or, when there is none, the old napattack folder's save, as a normal start would import it.
## Deleting the test build's save makes its next start take a new copy.
func _test_build_seed() -> String:
	if path != TestBuild.SAVE_PATH:
		return ""
	var real := _real_save_path()
	if FileAccess.file_exists(real):
		return real
	var legacy := _legacy_folder_save()
	return legacy if FileAccess.file_exists(legacy) else real

func _import_legacy_save(source: String, target: String) -> Error:
	_legacy_import_target = ProjectSettings.globalize_path(target)
	_legacy_import_error = _copy_legacy_save(source, target)
	return _legacy_import_error

## Copy the original bytes, never a reconstructed document: unknown fields and formatting
## survive. An existing destination (even damaged, newer, or a directory) always wins.
func _copy_legacy_save(source: String, target: String) -> Error:
	if FileAccess.file_exists(target) or DirAccess.dir_exists_absolute(target):
		return OK
	if not FileAccess.file_exists(source):
		return OK
	var input := FileAccess.open(source, FileAccess.READ)
	if input == null:
		return FileAccess.get_open_error()
	var length := input.get_length()
	var bytes := input.get_buffer(length)
	var err := input.get_error()
	input.close()
	if err != OK and err != ERR_FILE_EOF:
		return err
	if bytes.size() != length:
		return ERR_FILE_CANT_READ
	# The existing loader owns validation and damaged/future-save handling after copying.
	var tmp := target + ".name-migration.tmp"
	var output := FileAccess.open(tmp, FileAccess.WRITE)
	if output == null:
		return FileAccess.get_open_error()
	output.store_buffer(bytes)
	output.flush()
	err = output.get_error()
	output.close()
	if err == OK:
		# Do not replace a destination observed while importing.
		if FileAccess.file_exists(target) or DirAccess.dir_exists_absolute(target):
			DirAccess.remove_absolute(tmp)
			return OK
		err = DirAccess.rename_absolute(tmp, target)
	if err != OK:
		DirAccess.remove_absolute(tmp)
	return err

static func fresh() -> Dictionary:
	return {
		"version": VERSION,
		"zone": "woodland",
		"spawn": "start",
		"glint": 0,
		"flags": {},
		"quests": {},
		"tracked": "",
		"player": {"hp": 5, "max_hp": 5},
		"village": {"restored": {}},
		"paid": {},          # creatures that have paid their Glint (core/glint_cache.gd), "<camp>/<name>": true
		"caches": [],        # Glint left where the player went down: {zone, x, y, glint}
		# the one raid on the town (core/raids.gd): older saves load with this, no raid pending
		"raid": {"id": "", "state": "none", "postponed": 0, "wave": 0, "layout": {}, "repairs": false},
		# sound (core/sound.gd, ui/sound_menu.gd): effects and ambience on, Gentle sound off, since version 2
		"settings": {"reduced_motion": false, "pixel_scale": "fill",
			"sound_effects": true, "ambience": true, "gentle_sound": false},
	}

func reset() -> void:
	resume = {}
	resume_unsaved = false
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
	if not resume.is_empty():
		document.zone = String(resume.get("zone", document.zone))
		document.spawn = String(resume.get("spawn", document.spawn))
	var target := to if to != "" else path
	if _legacy_import_error != OK and ProjectSettings.globalize_path(target) == _legacy_import_target:
		return _legacy_import_error
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
	resume_unsaved = false
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
	resume = {}
	resume_unsaved = false
	data = _migrate(json.data)
	loaded.emit()
	return OK

## Versionless/explicit-0 documents are the legacy partial shape; v1 existed both before
## and after village was added. Version 2 (13 Nov) added the three sound settings: a save from
## before sound loads with effects and ambience on and Gentle sound off, whatever else it holds.
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
			1:
				# v1 -> v2: the sound settings, at their defaults (the switches did not exist before, so
				# a v1 save holds no choice). A document with no settings at all is filled below.
				if out.has("settings"):
					for key: String in SOUND_SETTINGS:
						if not out.settings.has(key):
							out.settings[key] = SOUND_SETTINGS[key]
				v = 2
		out.version = v
	_fill_missing(out, fresh())
	# a sound setting that is not a switch (a damaged or hand-edited save) goes back to its default: three
	# switches are no reason to refuse a save and the progress in it (15 Nov)
	for key: String in SOUND_SETTINGS:
		if not out.settings[key] is bool:
			out.settings[key] = SOUND_SETTINGS[key]
	# and so do reduced motion and the pixel scale (15 Nov, the audit of #494: until then either one refused
	# the whole save); a scale this build does not know is "fill" too
	if not out.settings.reduced_motion is bool:
		out.settings.reduced_motion = false
	if not (out.settings.pixel_scale is String and String(out.settings.pixel_scale) in PIXEL_SCALES):
		out.settings.pixel_scale = "fill"
	out.version = VERSION
	out.glint = int(out.glint)
	for cache: Dictionary in out.caches:
		for key: String in ["x", "y", "glint"]:
			cache[key] = int(cache[key])
	# a save from before raids (12 Nov) gets the record above from fresh(): state "none", nothing pending,
	# whatever its flags say; the raid is earned and announced from there (core/raids.gd)
	for key: String in ["postponed", "wave"]:
		out.raid[key] = int(out.raid[key])
	# a state this build does not know (a hand-edited or damaged save) would freeze the raid: start it afresh
	if not String(out.raid.state) in RAID_STATES:
		out.raid.state = "none"
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
			out[key] = value.duplicate(true) if (value is Dictionary or value is Array) else value
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
	for key in ["zone", "spawn", "tracked"]:
		if doc.has(key) and not doc[key] is String:
			return ERR_INVALID_DATA
	if doc.has("caches"):
		if not doc.caches is Array:
			return ERR_INVALID_DATA
		for cache: Variant in doc.caches:
			if not cache is Dictionary or not cache.get("zone") is String:
				return ERR_INVALID_DATA
			for key: String in ["x", "y", "glint"]:
				if not _whole_number(cache.get(key)):
					return ERR_INVALID_DATA
	for key in ["flags", "quests", "player", "village", "settings", "paid"]:
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
	if doc.has("raid"):
		if not doc.raid is Dictionary:
			return ERR_INVALID_DATA
		for key: String in ["id", "state"]:
			if doc.raid.has(key) and not doc.raid[key] is String:
				return ERR_INVALID_DATA
		for key: String in ["postponed", "wave"]:
			if doc.raid.has(key) and (not _whole_number(doc.raid[key]) or doc.raid[key] < 0):
				return ERR_INVALID_DATA
		if doc.raid.has("repairs") and not doc.raid.repairs is bool:
			return ERR_INVALID_DATA
		if doc.raid.has("layout"):
			if not doc.raid.layout is Dictionary:
				return ERR_INVALID_DATA
			for kind: Variant in doc.raid.layout.values():
				if not kind is String:
					return ERR_INVALID_DATA
	# the settings inside are not checked here: `_migrate` puts a damaged one back to its default
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

