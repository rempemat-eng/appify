extends GdUnitTestSuite
## The test build (core/test_build.gd; Matt, 22 Nov: "Yes, test build first") and the woodland's way to the
## Frostline (Matt, 22 Nov: the shard crows on the woodland's upper lawn, the north door when Moss's loaf
## starts). With the switch off, as in every shipped build, nothing that a player can reach changes: no door
## opens, no crow wakes, the Frostline is not in the table and stays a lab, the save is the real one and no
## tag shows. With it on, the Frostline is a zone like any other (autosave, card, quest HUD), the loaf can
## start and finish, and the game keeps a save of its own that starts as a copy of the real one.

const SAVE := "user://test_test_build_save.json"
const REAL := "user://test_test_build_real.json"
const OWN := "user://test_test_build_own.json"
const BREAD := "a1_bread_for_the_bothy"
const SLICE := ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again"]

## A save whose test-build seed is a disposable file, never the player's real save_0.json.
class SeededSave:
	extends "res://core/save_game.gd"
	var real_source := ""

	func _test_build_seed() -> String:
		return real_source

var _holder: Node2D
var _player: Player
var _saves: Array[Node] = []

func before_test() -> void:
	TestBuild.forced = null
	SaveGame.reset()
	SaveGame.path = SAVE
	_holder = auto_free(Node2D.new())
	add_child(_holder)
	_player = auto_free(load("res://actors/player.tscn").instantiate())
	_player.input_enabled = false
	Zones.current = null
	Zones.attach(_holder, _player)

func after_test() -> void:
	TestBuild.forced = null
	Zones.table.erase("frostline")
	SaveGame.path = SaveGame.DEFAULT_PATH
	for f: String in [SAVE, REAL, OWN, OWN + ".name-migration.tmp", OWN + ".tmp"]:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(f))
	for s: Node in _saves:
		s.free()
	_saves.clear()
	Zones.current = null
	Zones.root = null
	SaveGame.reset()

func _ticks(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

func _slice_done() -> void:
	for q: String in SLICE:
		SaveGame.data.quests[q] = {"state": "done", "step": 2}

func _woodland() -> Zone:
	assert_bool(Zones.go_to("woodland", "start")).is_true()
	return Zones.current

func _crows(zone: Zone) -> Array:
	var out := []
	for c in zone.get_node("Actors/ColCrowsCamp/ColCrows/Camp").get_children():
		if c is SliceEnemy:
			out.append(c)
	return out

## Switched off means not processing and out of the physics space (Conditional, CollisionObject2D's
## DISABLE_MODE_REMOVE): a hidden crow neither thinks, nor blocks, nor can be hit.
func _active(e: SliceEnemy) -> bool:
	return e.is_visible_in_tree() and e.can_process() and PhysicsServer2D.body_get_space(e.get_rid()).is_valid()

# --- the switch ----------------------------------------------------------------------------------
func test_the_switch_is_off_in_the_test_run_and_reads_the_feature_or_the_argument() -> void:
	# gdUnit runs without --test-build and without the export feature: the shipped behaviour
	assert_bool(OS.get_cmdline_user_args().has(TestBuild.ARG)).is_false()
	assert_bool(OS.has_feature(TestBuild.FEATURE)).is_false()
	assert_bool(TestBuild.on()).is_false()
	TestBuild.forced = true
	assert_bool(TestBuild.on()).is_true()
	assert_bool(TestBuild.candidate("frostline")).is_true()
	assert_bool(TestBuild.candidate("woodland")).is_false()
	assert_str(TestBuild.tag("frostline")).is_equal("test build: unfinished art")
	assert_str(TestBuild.tag("woodland")).is_equal("test build")
	TestBuild.forced = false
	assert_bool(TestBuild.candidate("frostline")).is_false()
	assert_str(TestBuild.tag("frostline")).is_equal("")

func test_the_test_build_lists_the_frostline_and_no_shipped_zone() -> void:
	var listed: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(Zones.TABLE))
	assert_dict(TestBuild.zones()).is_equal({"frostline": "res://zones/frostline/frostline.tscn"})
	for id: String in TestBuild.zones():
		assert_bool(listed.has(id)).override_failure_message("%s ships: take it out of data/test_build.json" % id).is_false()

# --- switch off: nothing reachable changes --------------------------------------------------------
func test_off_the_frostline_is_unbuilt_and_the_loaf_cannot_start() -> void:
	_slice_done()
	assert_bool(Zones.has_zone("frostline")).is_false()
	assert_bool(Quests.has_flag("zone_built:frostline")).is_false()
	assert_bool(Quests.check(Quests.defs[BREAD].start["if"])).is_false()
	assert_str(SaveGame.path).is_equal(SAVE)       # set by this suite: the autoload chose DEFAULT_PATH
	var fresh: Node = auto_free(load("res://core/save_game.gd").new())
	assert_str(fresh.path).is_equal(SaveGame.DEFAULT_PATH)
	assert_str(fresh._test_build_seed()).is_equal("")

func test_off_the_woodland_has_no_open_north_door_and_no_live_crow() -> void:
	_slice_done()
	# even a save that holds the loaf active (made by a test build) shows nothing: the quest is shelved
	SaveGame.data.quests[BREAD] = {"state": "active", "step": 0}
	Quests.shelve_unbuilt()
	assert_str(Quests.state(BREAD)).is_equal("none")
	var zone := _woodland()
	await _ticks(3)
	assert_bool((zone.get_node("Doors/ToFrostline") as Door).is_open()).is_false()
	assert_bool((zone.get_node("Actors/ColCrowsCamp") as CanvasItem).visible).is_false()
	var crows := _crows(zone)
	assert_int(crows.size()).is_equal(3)
	for e: SliceEnemy in crows:
		assert_bool(_active(e)).override_failure_message("%s is live with the switch off" % e.name).is_false()
		assert_str(e.state).is_equal("idle")
	# the camera's fight test sees no fight from them (its input switch is the only other reason here)
	_player.input_enabled = true
	assert_str(CameraFraming.game_block_reason(_player)).is_equal("")
	_player.input_enabled = false

func test_off_the_frostline_opened_by_name_is_still_a_lab() -> void:
	Zones.try_zones(PackedStringArray(["--try-zone=frostline"]))
	assert_bool(Zones.go_to("frostline", "woodland")).is_true()
	assert_bool(Zones.in_lab()).is_true()
	assert_bool(SaveGame.has_flag("visited:frostline")).is_false()
	assert_bool(SaveGame.resume.is_empty()).is_false()

# --- switch on ----------------------------------------------------------------------------------
func test_on_the_frostline_joins_the_table_and_is_no_lab() -> void:
	TestBuild.forced = true
	assert_array(Array(Zones.add_test_zones())).is_equal(["frostline"])
	assert_array(Array(Zones.add_test_zones())).is_empty()
	assert_bool(Quests.has_flag("zone_built:frostline")).is_true()
	assert_bool(Zones.go_to("frostline", "woodland")).is_true()
	assert_bool(Zones.is_lab(Zones.current)).is_true()      # its ground still says so ...
	assert_bool(Zones.in_lab()).is_false()                  # ... but the test build plays it as a zone
	assert_bool(SaveGame.has_flag("visited:frostline")).is_true()
	assert_bool(SaveGame.resume.is_empty()).is_true()
	assert_str(String(SaveGame.data.zone)).is_equal("frostline")
	# with the switch off again the same zone is a lab once more
	TestBuild.forced = false
	assert_bool(Zones.in_lab()).is_true()

func test_on_the_door_and_the_crows_wait_for_the_loaf() -> void:
	TestBuild.forced = true
	Zones.add_test_zones()
	_slice_done()
	var zone := _woodland()
	await _ticks(3)
	var door := zone.get_node("Doors/ToFrostline") as Door
	assert_str(door.target_zone).is_equal("frostline")
	assert_str(door.target_spawn).is_equal("woodland")
	assert_bool(door.is_open()).is_false()
	for e: SliceEnemy in _crows(zone):
		assert_bool(_active(e)).is_false()
	# Moss gives the loaf: the camp wakes where the woodland already is, and the door opens
	Quests.notify("talk:moss")
	assert_str(Quests.state(BREAD)).is_equal("active")
	await _ticks(3)
	assert_bool(door.is_open()).is_true()
	assert_bool((zone.get_node("Actors/ColCrowsCamp") as CanvasItem).visible).is_true()
	var crows := _crows(zone)
	for e: SliceEnemy in crows:
		assert_bool(_active(e)).override_failure_message("%s is not live once the loaf starts" % e.name).is_true()
	assert_array(crows.map(func(e: SliceEnemy) -> String: return e.role)).contains_exactly_in_any_order(
		["rusher", "rusher", "shooter"])
	# freeing them clears the col: way_open:W2, the next step, and the door stays open
	for e: SliceEnemy in crows:
		e.died.emit()
	assert_bool(SaveGame.has_flag("camp_cleared:col_crows")).is_true()
	assert_bool(SaveGame.has_flag("way_open:W2")).is_true()
	assert_int(int(SaveGame.data.quests[BREAD].step)).is_equal(1)
	assert_bool(door.is_open()).is_true()

func test_on_the_loaf_starts_and_finishes_and_the_lead_and_closing_card_follow() -> void:
	TestBuild.forced = true
	Zones.add_test_zones()
	_slice_done()
	SaveGame.data.quests["a1_the_torn_roof"] = {"state": "done", "step": 2}
	SaveGame.set_flag("first_night_won")
	# the slice's closing card waits for the Frostline to be unbuilt: in the test build Moss's loaf leads on
	assert_str(str(Quests.due_card().get("id", ""))).is_not_equal("closing")
	assert_str(str(Quests.lead().get("text", ""))).contains("Moss has a loaf")
	Quests.notify("talk:moss")
	assert_str(Quests.state(BREAD)).is_equal("active")
	Quests.notify("camp:col_crows")
	SaveGame.set_flag("camp_cleared:col_crows")
	Quests.notify("camp:col_crows")
	assert_bool(Zones.go_to("frostline", "woodland")).is_true()
	Quests.notify("talk:hut_warden")
	assert_str(Quests.state(BREAD)).is_equal("done")
	assert_bool(SaveGame.has_flag("met_hut_warden")).is_true()

func test_on_the_frostline_s_door_and_the_woodland_s_meet() -> void:
	TestBuild.forced = true
	Zones.add_test_zones()
	assert_bool(Zones.go_to("frostline", "start")).is_true()
	var back := Zones.current.get_node("Doors/ToWoodland") as Door
	assert_str(back.target_zone).is_equal("woodland")
	assert_bool(back.is_open()).is_true()
	assert_bool(Zones.go_to(back.target_zone, back.target_spawn)).is_true()
	var spawn := Zones.current.get_node("Spawns/" + back.target_spawn) as Marker2D
	var door := Zones.current.get_node("Doors/ToFrostline") as Node2D
	assert_object(spawn).is_not_null()
	# the arrival stands clear of the north door's trigger, close enough to face away from it (zones.gd)
	var shape := (door.get_node("Shape") as CollisionShape2D).shape as RectangleShape2D
	var trigger := Rect2(door.position - shape.size / 2.0, shape.size)
	assert_bool(trigger.grow(12.0).has_point(spawn.position)).is_false()
	assert_float(spawn.position.distance_to(door.position)).is_less(Zones.ARRIVAL_DOOR)
	await _ticks(2)
	# and the player can stand there: no wall under the body (actors/player.tscn, a circle of r 9 four up)
	var q := PhysicsShapeQueryParameters2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 9.0
	q.shape = circle
	q.transform = Transform2D(0.0, spawn.position + Vector2(0, -4))
	q.collision_mask = 1
	assert_array(Zones.current.get_world_2d().direct_space_state.intersect_shape(q, 1)).is_empty()

# --- the save -----------------------------------------------------------------------------------
func _seeded(real := REAL) -> Node:
	var s: Node = load("res://test/test_test_build.gd").SeededSave.new()
	s.real_source = real
	s.path = OWN
	_saves.append(s)
	return s

func test_the_test_build_save_starts_as_a_copy_of_the_real_one_and_never_writes_it() -> void:
	var real_doc := {"version": 2, "glint": 116, "zone": "crossroads", "spawn": "square"}
	var f := FileAccess.open(REAL, FileAccess.WRITE)
	f.store_string(JSON.stringify(real_doc))
	f.close()
	var real_bytes := FileAccess.get_file_as_bytes(REAL)
	var s := _seeded()
	assert_int(s.boot()).is_equal(OK)
	assert_bool(FileAccess.get_file_as_bytes(OWN) == real_bytes).is_true()
	assert_int(int(s.data.glint)).is_equal(116)
	# the test build plays on and saves: only its own file moves
	s.data.glint = 7
	assert_int(s.save()).is_equal(OK)
	assert_bool(FileAccess.get_file_as_bytes(REAL) == real_bytes).is_true()
	# its next start loads its own save, not the real one again
	var again := _seeded()
	assert_int(again.boot()).is_equal(OK)
	assert_int(int(again.data.glint)).is_equal(7)
	assert_bool(FileAccess.get_file_as_bytes(REAL) == real_bytes).is_true()

func test_with_no_real_save_the_test_build_starts_afresh_and_fresh_skips_the_copy() -> void:
	var s := _seeded()
	assert_int(s.boot()).is_equal(ERR_FILE_NOT_FOUND)
	assert_bool(FileAccess.file_exists(OWN)).is_false()
	var f := FileAccess.open(REAL, FileAccess.WRITE)
	f.store_string(JSON.stringify({"version": 2, "glint": 3}))
	f.close()
	assert_int(_seeded().boot(true)).is_equal(OK)
	assert_bool(FileAccess.file_exists(OWN)).is_false()

func test_the_test_build_uses_its_own_save_path() -> void:
	assert_str(TestBuild.SAVE_PATH).is_not_equal(SaveGame.DEFAULT_PATH)
	var s: Node = auto_free(load("res://core/save_game.gd").new())
	s.path = TestBuild.SAVE_PATH
	assert_str(s._test_build_seed()).is_equal(SaveGame.DEFAULT_PATH)
	assert_str(s._legacy_save_path()).is_equal("")

# --- the corner tag ------------------------------------------------------------------------------
func test_the_tag_shows_only_in_the_test_build() -> void:
	SaveGame.set_flag("seen:opening")
	var off: Node2D = auto_free(load("res://game.tscn").instantiate())
	add_child(off)
	await _ticks(2)
	assert_object(off.test_tag).is_null()
	assert_object(get_tree().get_first_node_in_group("test_build_tag")).is_null()
	off.queue_free()
	await _ticks(2)
	TestBuild.forced = true
	Zones.add_test_zones()
	var on: Node2D = auto_free(load("res://game.tscn").instantiate())
	add_child(on)
	await _ticks(2)
	assert_str(on.test_tag.text).is_equal("test build")
	assert_bool(Zones.go_to("frostline", "woodland")).is_true()
	await _ticks(2)
	assert_str(on.test_tag.text).is_equal("test build: unfinished art")
