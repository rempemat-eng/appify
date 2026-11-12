extends GdUnitTestSuite
## The Frostline (game/kit/zones/frostline.json, game/data/plans/frostline.json): built from its kit plan
## as a lab of candidate pieces, not yet in data/zones.json, opened for a run by --try-zone (core/zones.gd).
## Its solids (the edge, the tarn, the hut, the pines and boulders), its reach (from the arrival every
## talk area, the camp and the door can be walked to), and its quests played on it: the warden's loaf,
## the ring and the ibex, and Under the snout waiting for the ice caves.

const SAVE := "user://test_frostline_save.json"
const PLAYER_R := 9.0       ## actors/player.tscn: a circle of r 9 ...
const PLAYER_UP := 4.0      ## ... its centre 4 texels above the feet
const STEP := 6.0
const SLICE := ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again"]

var _holder: Node2D
var _player: Player

func before_test() -> void:
	SaveGame.reset()
	SaveGame.path = SAVE
	_holder = auto_free(Node2D.new())
	add_child(_holder)
	_player = auto_free(load("res://actors/player.tscn").instantiate())
	_player.input_enabled = false
	Zones.current = null
	Zones.attach(_holder, _player)
	Zones.try_zones(PackedStringArray(["--try-zone=frostline"]))

func after_test() -> void:
	Zones.table.erase("frostline")
	SaveGame.path = SaveGame.DEFAULT_PATH
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE))
	Zones.current = null
	Zones.root = null
	SaveGame.reset()

func _enter(spawn := "start") -> Zone:
	assert_bool(Zones.go_to("frostline", spawn)).is_true()
	return Zones.current

func _ticks(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

func _fits(space: PhysicsDirectSpaceState2D, at: Vector2, r: float) -> bool:
	var circle := CircleShape2D.new()
	circle.radius = r
	var q := PhysicsShapeQueryParameters2D.new()
	q.shape = circle
	q.transform = Transform2D(0.0, at)
	q.collision_mask = 1
	q.collide_with_areas = false
	return space.intersect_shape(q, 1).is_empty()

func _stands(space: PhysicsDirectSpaceState2D, feet: Vector2) -> bool:
	return _fits(space, feet + Vector2(0, -PLAYER_UP), PLAYER_R)

func _plan() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string("res://kit/zones/frostline.json"))

# --- in the build, not yet in the world ----------------------------------------------------------
func test_the_frostline_is_a_lab_that_nothing_leads_to_yet() -> void:
	var listed: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(Zones.TABLE))
	assert_bool(listed.has("frostline")).override_failure_message(
		"the Frostline is listed: its door from the woodland and Matt's approval of its pieces come first").is_false()
	assert_bool(_plan().get("lab", false)).is_true()
	var zone := _enter()
	assert_bool(Zones.is_lab(zone)).is_true()
	assert_str(zone.zone_id).is_equal("frostline")
	# --try-zone adds only a built zone that is not listed, and only once
	Zones.table.erase("frostline")
	assert_array(Array(Zones.try_zones(PackedStringArray(["--try-zone=frostline", "--try-zone=nowhere", "--try-zone=woodland"])))).is_equal(["frostline"])
	assert_array(Array(Zones.try_zones(PackedStringArray(["--try-zone=frostline"])))).is_empty()

# --- solids -------------------------------------------------------------------------------------
func test_the_tarn_the_hut_and_the_zone_edge_stop_the_player_and_the_trod_does_not() -> void:
	var zone := _enter()
	await _ticks(2)
	var space := zone.get_world_2d().direct_space_state
	var cell := 24.0
	var rows: Array = _plan().rows
	# the tarn's ice and its open water (the ice-cut, the inflow, the outlet), every cell with its own kind
	# all round it, except under the footbridge's deck
	var deck := Rect2(Vector2(19.5 * cell - 60, 40 * cell - 48), Vector2(120, 48))
	var wet := 0
	for y in range(1, rows.size() - 1):
		for x in range(1, String(rows[y]).length() - 1):
			var k: String = rows[y][x]
			if k not in ["a", "i"] or deck.has_point(Vector2(x + 0.5, y + 0.5) * cell):
				continue
			if rows[y - 1][x] == k and rows[y + 1][x] == k and rows[y][x - 1] == k and rows[y][x + 1] == k:
				wet += 1
				assert_bool(_stands(space, Vector2(x + 0.5, y + 0.5) * cell)).override_failure_message(
					"the player stands in the tarn or its water at cell %d, %d" % [x, y]).is_false()
	assert_int(wet).is_greater(60)
	# the footbridge carries the hut spur over the outlet
	assert_bool(_stands(space, Vector2(19.5 * cell, 940.0))).override_failure_message("the footbridge's deck is not walkable").is_true()
	# every trodden cell is open (no piece stands on the Col Path)
	var blocked: Array[Vector2i] = []
	for y in rows.size():
		for x in String(rows[y]).length():
			if rows[y][x] == "b" and not _fits(space, Vector2(x + 0.5, y + 0.5) * cell, 4.0):
				blocked.append(Vector2i(x, y))
	assert_array(blocked).override_failure_message("solids on the trod at %s" % str(blocked)).is_empty()
	# the hut: its walls stop the player across their width, its door is on the trod
	var hut := zone.get_node("Props/col_hut") as Node2D
	for dx in [-90, -45, 0, 45, 90]:
		assert_bool(_stands(space, hut.position + Vector2(dx, -30))).override_failure_message(
			"the player stands inside the Col hut at %d" % dx).is_false()
	assert_bool(_stands(space, hut.position + Vector2(-10, 36))).is_true()
	# the zone's edge: nobody walks off the ground
	var size := Vector2(String(rows[0]).length(), rows.size()) * cell
	for p in [Vector2(-12, 600), Vector2(size.x + 12, 600), Vector2(600, -12), Vector2(300, size.y + 14)]:
		assert_bool(_stands(space, p)).override_failure_message("the player stands off the ground at %s" % str(p)).is_false()
	# the cirque's step: the face stops the player across the zone (rows 18 to 21) except on its stair
	var open_cols: Array[int] = []
	for x in String(rows[0]).length():
		if _stands(space, Vector2(x + 0.5, 20.0) * cell):
			open_cols.append(x)
	assert_array(open_cols).override_failure_message("the face is open at columns %s" % str(open_cols)).is_equal([22, 23, 24, 25, 26])

# --- reach --------------------------------------------------------------------------------------
func test_from_the_arrival_every_talk_area_the_camp_and_the_door_can_be_walked_to() -> void:
	var zone := _enter("woodland")
	await _ticks(2)
	var space := zone.get_world_2d().direct_space_state
	var bounds := zone.bounds
	var nx := int(bounds.size.x / STEP)
	var ny := int(bounds.size.y / STEP)
	var start := Vector2i((zone.spawn_position("woodland") / STEP).round())
	assert_bool(_stands(space, Vector2(start) * STEP)).is_true()
	var seen := {start: true}
	var todo: Array[Vector2i] = [start]
	while not todo.is_empty():
		var c: Vector2i = todo.pop_back()
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = c + d
			if n.x < 0 or n.y < 0 or n.x >= nx or n.y >= ny or seen.has(n):
				continue
			if _stands(space, Vector2(n) * STEP):
				seen[n] = true
				todo.append(n)
	assert_int(seen.size()).is_greater(8000)
	var reached := func(at: Vector2, within: float) -> bool:
		for k: Vector2i in seen:
			if (Vector2(k) * STEP).distance_to(at) <= within:
				return true
		return false
	for path in ["Actors/HutWarden", "Actors/IceCutter"]:
		var talk := zone.get_node(path) as Interactable
		var r := ((talk.get_node("Shape") as CollisionShape2D).shape as CircleShape2D).radius
		assert_bool(reached.call(talk.global_position, r)).override_failure_message("%s cannot be walked to" % path).is_true()
	for e in zone.get_node("Actors/FellsIbexCamp/Camp").get_children():
		if e is CharacterBody2D:
			assert_bool(reached.call((e as Node2D).global_position, 40.0)).override_failure_message(
				"the ibex at %s cannot be walked to" % str((e as Node2D).global_position)).is_true()
	var door := zone.get_node("Doors").get_child(0) as Node2D
	assert_bool(reached.call(door.global_position, 30.0)).is_true()

# --- the quests ---------------------------------------------------------------------------------
func _finish_slice() -> void:
	for q in SLICE:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	SaveGame.set_flag("shard_home:woodland")

func test_the_loaf_the_ring_and_the_ibex_play_out_here_and_the_snout_waits_for_the_ice_caves() -> void:
	_finish_slice()
	Quests.notify("talk:moss")
	assert_str(Quests.current_step("a1_bread_for_the_bothy").get("id", "")).is_equal("col")
	Quests.notify("camp:col_crows")
	var zone := _enter("woodland")
	assert_str(Quests.current_step("a1_bread_for_the_bothy").get("id", "")).is_equal("warden")
	# the people and the camp the quests name stand in the zone
	assert_str(String(zone.get_node("Actors/HutWarden").get("speaker_id"))).is_equal("hut_warden")
	assert_str(String(zone.get_node("Actors/IceCutter").get("speaker_id"))).is_equal("ice_cutter")
	assert_str(String(zone.get_node("Actors/FellsIbexCamp/Camp").get("camp_id"))).is_equal("fells_ibex")
	assert_str(Dialogue.lines_for("hut_warden")[0]).starts_with("Bread!")
	Quests.notify("talk:hut_warden")
	assert_str(Quests.state("a1_bread_for_the_bothy")).is_equal("done")
	assert_str(Quests.current_step("a1_the_ring_is_shut").get("id", "")).is_equal("fells")
	Quests.notify("camp:fells_ibex")
	SaveGame.set_flag("camp_cleared:fells_ibex")
	Quests.notify("talk:hut_warden")
	assert_str(Quests.state("a1_the_ring_is_shut")).is_equal("done")
	assert_bool(SaveGame.has_flag("ring_open:frostline")).is_true()
	# the ice caves are not built: the snout does not start, the warden says why, the HUD says so
	SaveGame.data.quests["a1_the_torn_roof"] = {"state": "done", "step": Quests.defs["a1_the_torn_roof"].steps.size()}
	assert_str(Quests.state("a1_under_the_snout")).is_equal("none")
	assert_str("\n".join(Dialogue.lines_for("hut_warden"))).contains("sealed with new ice")
	assert_str(Quests.lead().get("text", "")).contains("sealed")
	# once they are, it starts as act 1 tells it
	Zones.table["ice_caves"] = "res://test/fixtures/zone_a.tscn"
	Quests.notify("talk:hut_warden")
	Zones.table.erase("ice_caves")
	assert_str(Quests.current_step("a1_under_the_snout").get("id", "")).is_equal("cutter")

## A save holding a quest whose zone is not built is shelved on load, and only then (core/quests.gd
## shelve_unbuilt, deferred until Zones has read its table): the logic audit of #478, item 9.
func test_a_quest_is_shelved_only_while_its_zone_is_not_built() -> void:
	_finish_slice()
	SaveGame.data.quests["a1_bread_for_the_bothy"] = {"state": "active", "step": 1}
	SaveGame.data.tracked = "a1_bread_for_the_bothy"
	Quests.shelve_unbuilt()
	assert_str(Quests.state("a1_bread_for_the_bothy")).is_equal("active")
	Zones.table.erase("frostline")
	Quests.shelve_unbuilt()
	assert_str(Quests.state("a1_bread_for_the_bothy")).is_equal("none")
	assert_str(String(SaveGame.data.tracked)).is_equal("")
	var before: Dictionary = SaveGame.data.quests.duplicate(true)
	Quests.shelve_unbuilt()
	assert_dict(SaveGame.data.quests).is_equal(before)
