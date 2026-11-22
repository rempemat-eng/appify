class_name TestBuild
extends RefCounted
## The test build (Matt, 22 Nov 2026, docs/vision/decisions-2026-11-22.md: "Yes, test build first"): Matt
## plays the zones in data/test_build.json (the Frostline) before their art is approved. With the switch
## on, each of them joins the zone table (core/zones.gd add_test_zones), so its doors lead to it and
## "zone_built:<id>" holds; it is not treated as a lab (autosave, the story card and the quest HUD work
## there); a corner tag says "test build: unfinished art" (game.gd); and the game reads and writes its own
## save, SAVE_PATH, never the real one (core/save_game.gd). With the switch off, as in every shipped build,
## none of this happens: nothing reads data/test_build.json and the game is as it was.
##
## The switch is on in either of two ways:
##   - an exported build whose preset lists the custom feature `test_build` (Project > Export > Features);
##     the shipped presets do not, and the preset for Matt's test build is a scratch one, never committed
##   - `-- --test-build` on the command line of a debug build (the editor's binary), as --try-zone and
##     --play are: playtest routes use it (game/tools/routes/col_path.txt). A release export ignores it.

const TABLE := "res://data/test_build.json"
const FEATURE := "test_build"
const ARG := "--test-build"
## The test build's own save, beside the real one (save_game.gd DEFAULT_PATH). On its first start it is a
## copy of the real save, if there is one, so Matt plays on from where his game is; after that the two
## never meet: the test build only ever reads the real file, once, and never writes it.
const SAVE_PATH := "user://test_build_save.json"
const TAG := "test build"
const TAG_UNFINISHED := "test build: unfinished art"

## Tests set this to true or false; null reads the build (the feature and the argument).
static var forced: Variant = null
static var _zones: Variant = null

static func on() -> bool:
	if forced != null:
		return bool(forced)
	return OS.has_feature(FEATURE) or (OS.is_debug_build() and OS.get_cmdline_user_args().has(ARG))

## The test build's zones, {id: scene path}, as data/test_build.json lists them (whether or not it is on).
static func zones() -> Dictionary:
	if _zones == null:
		var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(TABLE)) if FileAccess.file_exists(TABLE) else null
		_zones = doc.get("zones", {}) if typeof(doc) == TYPE_DICTIONARY and typeof(doc.get("zones")) == TYPE_DICTIONARY else {}
	return _zones

## True when `zone_id` is one of the test build's zones and the switch is on: a zone with unfinished art
## that this build plays as a real zone, not as a lab.
static func candidate(zone_id: String) -> bool:
	return on() and zones().has(zone_id)

## The corner tag in `zone`: "" with the switch off; "test build: unfinished art" in a zone of the test
## build, and in any other zone while it shows a piece that waits for one (shows_piece: the woodland's north
## door and its stand-in shard crows, once Moss's loaf starts); "test build" everywhere else.
static func tag(zone: Node) -> String:
	if not on():
		return ""
	var zone_id := String(zone.get("zone_id")) if zone != null else ""
	return TAG_UNFINISHED if zones().has(zone_id) or shows_piece(zone) else TAG

## True while `zone` shows a piece that only the test build can open: a Conditional whose condition holds,
## or a door that is open, and that waits for "zone_built:<a zone of the test build>". Read from the
## conditions themselves, not from visibility, so the answer is right in the same frame a quest moves.
static func shows_piece(zone: Node) -> bool:
	if zone == null:
		return false
	for node in zone.find_children("*", "Node2D", true, false):
		var cond_text := ""
		if node is Conditional:
			cond_text = (node as Conditional).only_if
		elif node is Door:
			cond_text = (node as Door).only_if
		if cond_text == "" or not _waits_for_a_test_zone(cond_text):
			continue
		if node is Door and (node as Door).is_open():
			return true
		if node is Conditional and Quests.check(JSON.parse_string(cond_text)):
			return true
	return false

static func _waits_for_a_test_zone(cond_text: String) -> bool:
	var cond: Variant = JSON.parse_string(cond_text)
	if typeof(cond) != TYPE_DICTIONARY:
		return false
	for f: Variant in cond.get("flags", []):
		if String(f).begins_with("zone_built:") and zones().has(String(f).trim_prefix("zone_built:")):
			return true
	return false
