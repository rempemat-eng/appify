extends GdUnitTestSuite
## Building a zone end to end in the editor (10 Nov): the faults found by driving the dock in a
## real editor, each held by a test that fails on the code before its fix, and the editor-built
## fixture zone (kit/zones/editor_glade.json, zones/editor_glade/editor_glade.tscn).

const Operations := preload("res://addons/world_editor/operations.gd")
const Dock := preload("res://addons/world_editor/dock.gd")
const Rules := preload("res://addons/world_editor/rules_adapter.gd")
const ZonePlan := preload("res://tools/kit_zone.gd")

var _fixtures: Array[Dictionary] = []
var _scenes: Array[Node] = []

## What the dock needs of the EditorPlugin, without an editor.
class StubPlugin extends Node:
	var brush := ""
	var tool_mode := "brush"
	var brush_size := 1
	var route_width := 2
	var facing := "s"
	var selected_variant := ""
	var selected_stage := ""
	var scatter := false
	var clipboard: Array = []
	var operations: Object
	var verdict: Dictionary = {}
	func refresh_preview() -> void:
		pass
	func validate_zone() -> Dictionary:
		return verdict

func after_test() -> void:
	for fixture in _fixtures:
		# the refresh callback captures its operations: let go, or neither is ever freed
		for connection in fixture.operations.changed.get_connections():
			fixture.operations.changed.disconnect(connection.callable)
		fixture.history.clear_history()
		fixture.history.free()
		if is_instance_valid(fixture.zone):
			fixture.zone.free()
	_fixtures.clear()
	for scene in _scenes:
		if is_instance_valid(scene):
			scene.free()
	_scenes.clear()

func _library() -> Dictionary:
	var result := {}
	for path in ["terrain/lawn", "terrain/path", "terrain/water", "prop/woodland_forest_bench", "prop/woodland_stump"]:
		var piece: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/pieces/%s.json" % path))
		result[piece.id] = piece
	return result

## A lab of real candidate pieces with the real relation engine and the real prop scenes, and the
## derived data refreshed after every change as the plugin does.
func _fixture(extra_plan: Dictionary = {}) -> Dictionary:
	var plan := {"zone": "authoring_fixture", "lab": true, "legend": {".": "lawn", "#": "path", "~": "water"},
		"rows": ["..........", "..........", "..........", "##########", "##########", "..........", "........~~", "........~~"],
		"spawns": {"start": [36, 84]}}
	plan.merge(extra_plan, true)
	var zone := ZonePlan.scene_from_plan(plan)
	add_child(zone)
	var ground := zone.get_node("Ground") as TerrainGround
	await get_tree().process_frame
	await get_tree().physics_frame
	var history := UndoRedo.new()
	var ops := Operations.new()
	ops.configure(zone, ground, history, {"library": _library(), "relation_evaluator": Callable(Rules, "placement")})
	ops.changed.connect(func() -> void: ops.refresh_derived(ops.last_changed_ground))
	var f := {"zone": zone, "ground": ground, "history": history, "operations": ops}
	_fixtures.append(f)
	return f

func _blocked(ground: TerrainGround) -> int:
	var walk := ground.get_node_or_null("KitWalk") as KitWalk
	return "".join(walk.rows).count("#") if walk != null else -1

func _shadow_hash(ground: TerrainGround) -> int:
	return hash((ground.get("_shadow_img") as Image).get_data())

# --- wrong output: a second click stacked an invisible twin

func test_a_second_click_on_one_spot_does_not_stack_a_twin() -> void:
	var f := await _fixture()
	var first: Dictionary = f.operations.place_piece("woodland_stump", Vector2(132, 48))
	assert_bool(first.ok).override_failure_message(str(first)).is_true()
	var second: Dictionary = f.operations.place_piece("woodland_stump", Vector2(132, 48))
	assert_bool(second.ok).is_false()
	assert_str(second.diagnostics[0].rule).is_equal("rules.duplicate")
	assert_int(f.ground.pieces().size()).is_equal(1)
	# beside it is still fine, and so is the same spot once the first is undone
	assert_bool(f.operations.place_piece("woodland_stump", Vector2(180, 48)).ok).is_true()
	assert_bool(f.history.undo()).is_true()
	assert_bool(f.history.undo()).is_true()
	assert_bool(f.operations.place_piece("woodland_stump", Vector2(132, 48)).ok).is_true()

# --- wrong output: Godot's own move and delete left the walk mask, shadows and bake stale

func test_godots_own_move_and_delete_refresh_the_walk_mask_shadows_and_baked_preview() -> void:
	var f := await _fixture()
	var ops: Operations = f.operations
	var ground: TerrainGround = f.ground
	var placed: Dictionary = ops.place_piece("woodland_stump", Vector2(132, 48))
	assert_bool(placed.ok).override_failure_message(str(placed)).is_true()
	var piece := placed.node as KitPiece
	var walk := ground.get_node("KitWalk") as KitWalk
	var with_stump := walk.rows.duplicate()
	assert_that(with_stump).is_equal(KitWalk.derive(ground))
	# a bake made now matches the pieces; nothing changed, so nothing to sync
	ground.baked = ImageTexture.create_from_image(Image.create_empty(8, 8, false, Image.FORMAT_RGBA8))
	assert_bool(ground.showing_baked()).is_true()
	assert_bool(ops.sync_native_edits()).is_false()
	assert_bool(ground.showing_baked()).is_true()
	# Godot's move tool or the inspector: the node moves, no operation runs
	piece.position += Vector2(48, 96)
	assert_that(walk.rows).is_equal(with_stump)            # stale until the editor's history says so
	assert_bool(ops.sync_native_edits()).is_true()
	assert_that(walk.rows).is_equal(KitWalk.derive(ground))
	assert_that(walk.rows).is_not_equal(with_stump)
	assert_bool(ground.showing_baked()).is_false()         # the bake's shadow is where the stump was
	var moved_shadow := _shadow_hash(ground)
	ground.rebuild_shadows()
	assert_int(_shadow_hash(ground)).is_equal(moved_shadow)
	# the scene tree's delete
	var before := _blocked(ground)
	piece.get_parent().remove_child(piece)
	assert_bool(ops.sync_native_edits()).is_true()
	assert_int(_blocked(ground)).is_less(before)
	assert_that(walk.rows).is_equal(KitWalk.derive(ground))
	assert_bool(ops.sync_native_edits()).is_false()
	piece.free()

func test_the_docks_own_undo_keeps_the_baked_preview_exact() -> void:
	# The sync must not mistake the dock's own transactions for foreign edits.
	var f := await _fixture()
	var ground: TerrainGround = f.ground
	ground.baked = ImageTexture.create_from_image(Image.create_empty(8, 8, false, Image.FORMAT_RGBA8))
	assert_bool(f.operations.place_piece("woodland_stump", Vector2(132, 48)).ok).is_true()
	assert_bool(ground.showing_baked()).is_false()
	assert_bool(f.operations.sync_native_edits()).is_false()
	assert_bool(f.history.undo()).is_true()
	assert_bool(f.operations.sync_native_edits()).is_false()
	assert_bool(ground.showing_baked()).is_true()

# --- wrong output: a zone saved after a dock edit logged an engine error in every fresh game

func test_a_zone_saved_after_an_edit_carries_no_runtime_walk_token() -> void:
	var f := await _fixture()
	assert_bool(f.operations.place_piece("woodland_stump", Vector2(132, 48)).ok).is_true()
	var ground: TerrainGround = f.ground
	assert_object(ground.get_node_or_null("KitWalk")).is_not_null()
	# KitWalk's owner token is an instance id of this process. Saved, it made
	# is_instance_id_valid() log "slot >= slot_max" when another process loaded the zone.
	assert_bool(ground.has_meta(&"kit_walk_owner")).is_false()
	# KitWalk also rebuilds by itself when cells change, and marks its ground again
	assert_bool(f.operations.paint_cells([Vector2i(0, 0)], "path").ok).is_true()
	(ground.get_node("KitWalk") as KitWalk).rebuild(ground)
	assert_bool(ground.has_meta(&"kit_walk_owner")).is_true()
	f.operations.prepare_save()                              # what the plugin does before a save
	assert_bool(ground.has_meta(&"kit_walk_owner")).is_false()
	var packed := PackedScene.new()
	assert_int(packed.pack(f.zone)).is_equal(OK)
	var again := packed.instantiate()
	_scenes.append(again)
	assert_bool(again.get_node("Ground").has_meta(&"kit_walk_owner")).is_false()
	assert_object(again.get_node_or_null("Ground/KitWalk")).is_not_null()
	# and the walk node still takes the next edit
	assert_bool(f.operations.place_piece("woodland_stump", Vector2(180, 48)).ok).is_true()
	assert_that((ground.get_node("KitWalk") as KitWalk).rows).is_equal(KitWalk.derive(ground))

# --- blocks authoring: no way to put the brush down; a wall of advice hid the fault

func _dock(f: Dictionary) -> Dictionary:
	var plugin := StubPlugin.new()
	plugin.operations = f.operations
	add_child(plugin)
	var dock := Dock.new()
	dock.plugin = plugin
	add_child(dock)
	dock.set_zone(f.zone, f.ground)
	_scenes.append(dock)
	_scenes.append(plugin)
	return {"dock": dock, "plugin": plugin}

func test_the_select_tool_puts_the_brush_down() -> void:
	var f := await _fixture()
	var d := _dock(f)
	var dock: Control = d.dock
	assert_int(dock.pieces.item_count).is_greater(0)
	dock.pieces.select(0)
	dock._piece_selected(0)
	assert_str(d.plugin.brush).starts_with("piece:")
	var button := dock.find_child("SelectTool", true, false) as Button
	assert_object(button).is_not_null()
	button.pressed.emit()
	assert_str(d.plugin.brush).is_equal("")
	assert_bool(dock.pieces.is_anything_selected()).is_false()
	# a material brush too, through the method Escape calls
	dock.mats.select(0)
	dock._material_selected(0)
	assert_str(d.plugin.brush).starts_with("material:")
	dock.select_tool()
	assert_str(d.plugin.brush).is_equal("")

func test_validation_lists_faults_before_advice() -> void:
	var f := await _fixture()
	var d := _dock(f)
	var advice := []
	for i in 30:
		advice.append({"check": "rules.scale", "severity": "advice", "message": "piece %d is unclassified" % i})
	advice.append({"check": "rules.route_water", "severity": "fault", "message": "route meets water without a deck"})
	d.plugin.verdict = {"ok": false, "diagnostics": advice}
	d.dock._validate()
	var lines: PackedStringArray = d.dock.status.text.split("\n")
	assert_str(lines[0]).is_equal("1 fault, 30 advice.")
	assert_str(lines[1]).is_equal("rules.route_water: route meets water without a deck")

func test_a_result_survives_the_palette_refresh_its_own_files_cause() -> void:
	# Save and export plan writes files; the editor then reports the file system changed and the
	# dock rebuilt its palette, replacing "Wrote ..." (and its warning about actors a plan cannot
	# hold) with the palette's count four frames later (the audit of #465).
	var f := await _fixture()
	var d := _dock(f)
	var dock: Control = d.dock
	var result := "Wrote res://kit/zones/x.json. Not in the plan (scene only): Actors/HatchPicture."
	dock.say(result)
	dock._files_changed()
	assert_str(dock.status.text).is_equal(result)
	assert_int(dock.pieces.item_count).is_greater(0)       # the palette was still rebuilt
	# when the library itself changed, the palette says so
	var library := _library()
	library.erase("woodland_stump")
	f.operations.configure(f.zone, f.ground, f.history, {"library": library, "relation_evaluator": Callable(Rules, "placement")})
	dock._files_changed()
	assert_str(dock.status.text).contains("terrain materials")

func test_no_open_zone_is_not_reported_as_an_empty_library() -> void:
	var f := await _fixture()
	var d := _dock(f)
	d.dock.set_zone(null, null)
	assert_str(d.dock.status.text).contains("No kit zone is open")
	assert_bool(d.dock.validate_button.disabled).is_true()

# --- actors and wiring: spawns, doors and actors placed with one click, exported by the plan

func test_gameplay_is_placed_in_one_undo_and_exported() -> void:
	var f := await _fixture()
	var ops: Operations = f.operations
	var before := ZonePlan.canonical(ops.export_plan().plan)
	var spawn: Dictionary = ops.place_gameplay("spawn", Vector2(200, 84), {"id": "east"})
	assert_bool(spawn.ok).override_failure_message(str(spawn)).is_true()
	var door: Dictionary = ops.place_gameplay("door", Vector2(235, 84), {"to": "kitlab"})
	assert_bool(door.ok).override_failure_message(str(door)).is_true()
	var sign: Dictionary = ops.place_gameplay("interactable", Vector2(60, 60), {"id": "Sign", "speaker": "stone_sign", "verb": "Read"})
	assert_bool(sign.ok).override_failure_message(str(sign)).is_true()
	var camp: Dictionary = ops.place_gameplay("camp", Vector2(120, 150), {"camp": "glade", "count": 2})
	assert_bool(camp.ok).override_failure_message(str(camp)).is_true()
	var plan: Dictionary = ops.export_plan().plan
	assert_str(ZonePlan.plan_error(plan)).is_equal("")
	assert_that(plan.spawns.east).is_equal([204.0, 84.0])              # snapped to 4 world px
	assert_that(plan.doors).is_equal([{"id": "Door", "rect": [9.0, 2.0, 1.0, 3.0], "to": "kitlab"}])
	assert_int(plan.actors.size()).is_equal(2)
	assert_that(plan.actors[0]).is_equal({"id": "Sign", "kind": "interactable", "at": [60.0, 60.0], "speaker": "stone_sign", "verb": "Read"})
	assert_str(plan.actors[1].camp).is_equal("glade")
	assert_int(plan.actors[1].enemies.size()).is_equal(2)
	# the nodes are what the hand-made zones use
	assert_object((sign.node as Node).get_script()).is_same(load("res://world/interactable.gd"))
	assert_object((door.node as Node).get_script()).is_same(load("res://world/door.gd"))
	assert_object(sign.node.owner).is_same(f.zone)
	# a refusal leaves no history: nobody stands in the pond, and a taken name is not reused
	var version: int = f.history.get_version()
	assert_str(ops.place_gameplay("spawn", Vector2(228, 180)).diagnostics[0].rule).is_equal("rules.walk")
	assert_str(ops.place_gameplay("interactable", Vector2(60, 36), {"id": "Sign", "speaker": "x"}).diagnostics[0].rule).is_equal("rules.instance_id")
	assert_str(ops.place_gameplay("villager", Vector2(60, 36)).diagnostics[0].rule).is_equal("plan.actor")
	assert_int(f.history.get_version()).is_equal(version)
	# each placement was one action
	for i in 4:
		assert_bool(f.history.undo()).is_true()
	assert_bool(f.history.has_undo()).is_false()
	assert_str(ZonePlan.canonical(ops.export_plan().plan)).is_equal(before)
	assert_bool(f.history.redo()).is_true()
	assert_bool(ops.export_plan().plan.spawns.has("east")).is_true()

func _actors_plan() -> Dictionary:
	return {"zone": "actors_fixture", "lab": true, "legend": {".": "lawn"}, "rows": ["........", "........", "........", "........", "........", "........"],
		"spawns": {"start": [36, 84]},
		"actors": [
			{"id": "Sign", "kind": "interactable", "at": [60, 60], "speaker": "stone_sign", "verb": "Read", "radius": 36, "marker_height": 44},
			{"id": "Hale", "kind": "villager", "at": [96.5, 72], "speaker": "hale", "character": "hale", "facing": "W", "marker_height": 86,
				"if": {"not_started": ["road_to_crossroads"]}},
			{"id": "Forge", "kind": "restore", "at": [120, 48], "restore": "forge"},
			{"id": "Camp", "kind": "camp", "at": [144, 108], "camp": "glade", "enemies": [[132, 96], [156, 120.5]]},
			{"id": "Den", "kind": "scene", "at": [48, 120], "scene": "res://actors/enemy.tscn"},
		]}

func test_actors_round_trip_every_kind_through_a_saved_scene() -> void:
	var plan := _actors_plan()
	assert_str(ZonePlan.plan_error(plan)).is_equal("")
	var root := ZonePlan.scene_from_plan(plan)
	_scenes.append(root)
	assert_object(root).is_not_null()
	# the nodes the game's own systems expect
	var sign := root.get_node("Actors/Sign") as Area2D
	assert_str(sign.get("speaker_id")).is_equal("stone_sign")
	assert_float((sign.get_node("Shape") as CollisionShape2D).shape.radius).is_equal(36.0)
	var holder := root.get_node("Actors/If_Hale")
	assert_object(holder.get_script()).is_same(load("res://world/conditional.gd"))
	assert_that(JSON.parse_string(holder.get("only_if"))).is_equal({"not_started": ["road_to_crossroads"]})
	assert_str(holder.get_node("Hale/Body").get("character")).is_equal("hale")
	assert_object(root.get_node("Actors/Forge").get_script()).is_same(load("res://world/restore_site.gd"))
	var camp := root.get_node("Actors/Camp")
	assert_str(camp.get("camp_id")).is_equal("glade")
	assert_int(camp.get_child_count()).is_equal(2)
	assert_vector((camp.get_child(1) as Node2D).position + (camp as Node2D).position).is_equal(Vector2(156, 120.5))
	assert_str(ZonePlan.canonical(ZonePlan.plan_from_scene(root))).is_equal(ZonePlan.canonical(plan))
	assert_that(ZonePlan.unexported_actors(root)).is_empty()
	# through a file on disk, as a zone is kept
	var packed := PackedScene.new()
	assert_int(packed.pack(root)).is_equal(OK)
	var path := "user://actors_round_trip.tscn"
	assert_int(ResourceSaver.save(packed, path)).is_equal(OK)
	var again := (ResourceLoader.load(path, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene).instantiate() as Node2D
	_scenes.append(again)
	DirAccess.remove_absolute(path)
	assert_str(ZonePlan.canonical(ZonePlan.plan_from_scene(again))).is_equal(ZonePlan.canonical(plan))
	# an edit in the inspector reaches the plan; nothing else moves
	again.get_node("Actors/Sign").set("speaker_id", "waystone")
	(again.get_node("Actors/Camp") as Node2D).position += Vector2(24, 0)
	var edited: Dictionary = ZonePlan.plan_from_scene(again)
	assert_str(edited.actors[0].speaker).is_equal("waystone")
	assert_that(edited.actors[3].at).is_equal([168.0, 108.0])
	assert_that(edited.actors[3].enemies).is_equal([[156.0, 96.0], [180.0, 120.5]])
	assert_that(edited.actors[1]).is_equal(plan.actors[1])

func test_instanced_actors_and_pieces_stay_instances_in_the_saved_zone() -> void:
	# The zone file must hold "an enemy here", not a copy of the enemy scene's values: before
	# 10 Nov each instance was saved with its scene's script, layers and motion mode as the zone's
	# own overrides, which would have outlived any later change to actors/enemy.tscn.
	var plan := _actors_plan()
	plan["pieces"] = [{"id": "stump", "piece": "woodland_stump", "at": [36, 132]}]
	var root := ZonePlan.scene_from_plan(plan)
	_scenes.append(root)
	var packed := PackedScene.new()
	assert_int(packed.pack(root)).is_equal(OK)
	var path := "user://instances_stay_instances.tscn"
	assert_int(ResourceSaver.save(packed, path)).is_equal(OK)
	var text := FileAccess.get_file_as_string(path)
	DirAccess.remove_absolute(path)
	assert_str(text).contains('[node name="Enemy1" parent="Actors/Camp"')
	assert_str(text).not_contains("motion_mode")
	assert_str(text).not_contains("res://actors/enemy.gd")
	assert_str(text).contains('[node name="stump" parent="Props"')
	assert_str(text).not_contains('piece_id = "woodland_stump"')
	# and the dock's own placements
	var f := await _fixture()
	assert_bool(f.operations.place_piece("woodland_stump", Vector2(132, 48)).ok).is_true()
	assert_int(packed.pack(f.zone)).is_equal(OK)
	assert_int(ResourceSaver.save(packed, path)).is_equal(OK)
	text = FileAccess.get_file_as_string(path)
	DirAccess.remove_absolute(path)
	assert_str(text).contains('[node name="woodland_stump" parent="Props"')
	assert_str(text).not_contains('piece_id = "woodland_stump"')

func test_hand_made_actors_export_and_what_a_plan_cannot_hold_is_reported() -> void:
	var f := await _fixture()
	var actors := f.zone.get_node("Actors") as Node2D
	# Add Node in Godot: an Area2D with the game's script and a Shape, as zones/woodland has
	var sign := Area2D.new()
	sign.name = "StoneSign"
	sign.set_script(load("res://world/interactable.gd"))
	sign.set("speaker_id", "stone_sign")
	sign.position = Vector2(60, 60)
	var shape := CollisionShape2D.new()
	shape.name = "Shape"
	shape.shape = CircleShape2D.new()
	(shape.shape as CircleShape2D).radius = 30.0
	sign.add_child(shape)
	actors.add_child(sign)
	var picture := Sprite2D.new()
	picture.name = "HatchPicture"
	actors.add_child(picture)
	var plan: Dictionary = f.operations.export_plan().plan
	assert_that(plan.actors).is_equal([{"id": "StoneSign", "kind": "interactable", "at": [60.0, 60.0], "speaker": "stone_sign"}])
	assert_that(ZonePlan.unexported_actors(f.zone)).is_equal(["Actors/HatchPicture"])
	# Validate says so beside the physical findings, as advice
	var options := {"library": _library(), "relation_evaluator": Callable(Rules, "placement"),
		"zone_validator": func(_plan: Dictionary, _lib: Dictionary) -> Dictionary: return {"ok": true, "diagnostics": []}}
	f.operations.configure(f.zone, f.ground, f.history, options)
	var verdict: Dictionary = f.operations.validate()
	assert_bool(verdict.ok).is_true()
	assert_str(verdict.diagnostics[0].check).is_equal("plan.actor_unexported")
	assert_str(verdict.diagnostics[0].message).contains("Actors/HatchPicture")

func test_malformed_actors_are_refused_before_any_node_is_made() -> void:
	var cases := {
		"id": {"id": "a/b"}, "kind": {"kind": "boss"}, "at": {"at": [1]}, "speaker": {"speaker": ""},
		"radius": {"radius": -1}, "if": {"if": "always"}, "marker_height": {"marker_height": "tall"},
	}
	for field in cases:
		var plan := _actors_plan()
		plan.actors[0].merge(cases[field], true)
		assert_str(ZonePlan.plan_error(plan)).override_failure_message(field).contains("actors[0]." + field)
		assert_object(ZonePlan.scene_from_plan(plan)).is_null()
	var twice := _actors_plan()
	twice.actors[2].id = "Sign"
	assert_str(ZonePlan.plan_error(twice)).contains("repeats 'Sign'")
	var camp := _actors_plan()
	camp.actors[3].enemies = []
	assert_str(ZonePlan.plan_error(camp)).contains("actors[3].enemies")
	var scene := _actors_plan()
	scene.actors[4].scene = "res://actors/missing.tscn"
	assert_str(ZonePlan.plan_error(scene)).contains("actors[4].scene")

func test_inherited_actors_stay_with_their_source_scene() -> void:
	# woodland_kit takes its Actors from the hand-made woodland (gameplay_from): they are not
	# copied into its plan, so its export is unchanged by the actors field.
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/zones/woodland_kit.json"))
	var root := ZonePlan.scene_from_plan(plan)
	_scenes.append(root)
	assert_int(root.get_node("Actors").get_child_count()).is_greater(0)
	assert_bool(ZonePlan.plan_from_scene(root).has("actors")).is_false()
	assert_that(ZonePlan.unexported_actors(root)).is_empty()

# --- the scene and its plan are one document in two files

func test_committed_kit_scenes_export_their_committed_plans() -> void:
	# Saving a zone in the editor without exporting its plan leaves the two apart, and the Python
	# checks, the bake and reviewers then read the old plan. The dock's Save and export plan
	# writes both; this holds every committed pair together.
	var dir := DirAccess.open("res://kit/zones")
	var checked := 0
	for file in dir.get_files():
		if not file.ends_with(".json"):
			continue
		var zone_id := file.get_basename()
		var scene_path := "res://zones/%s/%s.tscn" % [zone_id, zone_id]
		if not ResourceLoader.exists(scene_path):
			continue
		var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/zones/" + file))
		var root := (load(scene_path) as PackedScene).instantiate() as Node2D
		_scenes.append(root)
		var exported: Dictionary = ZonePlan.plan_from_scene(root, plan if not root.has_meta(ZonePlan.PLAN_META) else {})
		assert_str(ZonePlan.canonical(exported)).override_failure_message(
			"%s and %s disagree: export the plan from the dock (Save and export plan) or rebuild the scene from its plan." % [scene_path, file]
		).is_equal(ZonePlan.canonical(plan))
		checked += 1
	assert_int(checked).is_greater_equal(5)

func test_export_plan_file_writes_the_canonical_plan() -> void:
	var f := await _fixture()
	assert_bool(f.operations.place_gameplay("spawn", Vector2(200, 84), {"id": "east"}).ok).is_true()
	var path := "user://authoring_fixture_plan.json"
	var result: Dictionary = f.operations.export_plan_file(path)
	assert_bool(result.ok).override_failure_message(str(result)).is_true()
	var text := FileAccess.get_file_as_string(path)
	DirAccess.remove_absolute(path)
	assert_str(text).is_equal(ZonePlan.canonical(f.operations.export_plan().plan))
	assert_bool(FileAccess.file_exists(path + ".tmp")).is_false()
	# rebuilt from that file, the zone exports the same document again
	var rebuilt := ZonePlan.scene_from_plan(JSON.parse_string(text))
	_scenes.append(rebuilt)
	assert_str(ZonePlan.canonical(ZonePlan.plan_from_scene(rebuilt))).is_equal(text)

# --- wrong output: the player walked off the edge of a kit zone

func test_a_built_zone_is_walled_at_its_edge() -> void:
	var f := await _fixture()
	var edge := f.zone.get_node_or_null("Edge") as StaticBody2D
	assert_object(edge).is_not_null()
	assert_int(edge.collision_layer & 1).is_equal(1)
	await get_tree().physics_frame
	await get_tree().physics_frame
	var space: PhysicsDirectSpaceState2D = f.zone.get_world_2d().direct_space_state
	var probe := PhysicsShapeQueryParameters2D.new()
	probe.shape = CircleShape2D.new()
	(probe.shape as CircleShape2D).radius = 6.0
	probe.collision_mask = 1
	var size := Vector2(f.ground.size_px())
	for outside in [Vector2(-10, 84), Vector2(size.x + 10, 84), Vector2(100, -10), Vector2(100, size.y + 10), Vector2(-10, -10)]:
		probe.transform = Transform2D(0.0, outside)
		assert_int(space.intersect_shape(probe).size()).override_failure_message("open at %s" % outside).is_greater(0)
	# inside, along the edge and at an edge door, nothing is in the way
	for inside in [Vector2(8, 84), Vector2(size.x - 8, 84), Vector2(100, 8)]:
		probe.transform = Transform2D(0.0, inside)
		assert_int(space.intersect_shape(probe).size()).override_failure_message("blocked at %s" % inside).is_equal(0)
	# the edge is the zone's own, not authoring data: the plan does not change
	assert_bool(f.operations.export_plan().plan.has("Edge")).is_false()

func test_a_door_spawn_or_actor_outside_the_ground_is_refused() -> void:
	# The edge walls made a door just past the ground unreachable (the audit of #465: a door at
	# [20, 5, 1, 3] on a zone 20 cells wide was accepted and the player pushed at the wall for 22 s).
	var base := {"zone": "outside_fixture", "lab": true, "legend": {".": "lawn"}, "rows": ["....", "....", "...."]}
	var inside := base.duplicate(true)
	inside.merge({"doors": [{"id": "East", "rect": [3, 0, 1, 3], "to": "kitlab"}], "spawns": {"start": [0, 0], "corner": [96, 72]},
		"actors": [{"id": "Camp", "kind": "camp", "at": [48, 36], "camp": "c", "enemies": [[96, 72]]}]})
	assert_str(ZonePlan.plan_error(inside)).is_equal("")
	var cases := {
		"doors[0].rect must lie inside the ground": {"doors": [{"id": "East", "rect": [4, 0, 1, 3], "to": "kitlab"}]},
		"doors[0].rect must lie inside the ground (4 by 3 cells)": {"doors": [{"id": "South", "rect": [1, 2, 2, 2], "to": "kitlab"}]},
		"doors[0].rect must lie": {"doors": [{"id": "West", "rect": [-1, 0, 1, 3], "to": "kitlab"}]},
		"spawns.far must lie inside the ground": {"spawns": {"far": [97, 10]}},
		"spawns.above must lie inside the ground": {"spawns": {"above": [10, -1]}},
		"actors[0] must stand inside the ground": {"actors": [{"id": "Sign", "kind": "interactable", "at": [10, 80], "speaker": "s"}]},
		"actors[0] must stand inside the ground: [120.0, 10.0]": {"actors": [{"id": "Camp", "kind": "camp", "at": [48, 36], "camp": "c", "enemies": [[120.0, 10.0]]}]},
	}
	for message in cases:
		var plan := base.duplicate(true)
		plan.merge(cases[message])
		assert_str(ZonePlan.plan_error(plan)).override_failure_message("%s: got '%s'" % [message, ZonePlan.plan_error(plan)]).contains(message)
		assert_object(ZonePlan.scene_from_plan(plan)).is_null()
	# cells as the plan's unit: the same rule in cells
	var cells := base.duplicate(true)
	cells.merge({"coordinate_space": "cells", "spawns": {"start": [4, 3]}})
	assert_str(ZonePlan.plan_error(cells)).is_equal("")
	cells.spawns.start = [4.5, 3]
	assert_str(ZonePlan.plan_error(cells)).contains("spawns.start must lie inside the ground")

# --- one walk mask, twice (scripts/art/kit/walk.py and world/terrain/walk.gd)

func test_the_walk_mask_matches_the_python_export() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://test/fixtures/kit/walk_parity.json"))
	var root := ZonePlan.scene_from_plan(fixture.plan)
	add_child(root)
	_scenes.append(root)
	await get_tree().process_frame
	var rows := KitWalk.derive(root.get_node("Ground") as TerrainGround)
	assert_that(Array(rows)).is_equal(fixture.rows)

# --- the editor-built zone

func _glade() -> Node2D:
	var root := (load("res://zones/editor_glade/editor_glade.tscn") as PackedScene).instantiate() as Node2D
	_scenes.append(root)
	return root

func test_the_editor_built_glade_is_a_whole_zone() -> void:
	var root := _glade()
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/zones/editor_glade.json"))
	assert_str(ZonePlan.plan_error(plan)).is_equal("")
	assert_bool(plan.lab).is_true()
	# ground, a path, a pond, props, two spawns, a door, a talk area and a camp
	var materials := {}
	for row in plan.rows:
		for glyph in row:
			materials[plan.legend[glyph]] = true
	assert_that(materials.keys()).contains(["lawn", "path", "water"])
	assert_int(plan.pieces.size()).is_greater_equal(8)
	assert_that(plan.spawns.keys()).contains(["start", "east"])
	assert_int(plan.doors.size()).is_equal(1)
	var kinds := {}
	for actor in plan.actors:
		kinds[actor.kind] = true
	assert_that(kinds.keys()).contains(["interactable", "camp"])
	# rebuilt from its plan it is the same zone: nothing lives only in the scene
	var rebuilt := ZonePlan.scene_from_plan(plan)
	_scenes.append(rebuilt)
	assert_str(ZonePlan.canonical(ZonePlan.plan_from_scene(rebuilt))).is_equal(ZonePlan.canonical(plan))
	assert_that(ZonePlan.unexported_actors(root)).is_empty()
	assert_bool(root.get_node("Ground").has_meta(&"kit_walk_owner")).is_false()
	assert_object(root.get_node_or_null("Edge")).is_not_null()
	# kit/terrain/materials.tres has no uid of its own, so the editor invents one that only its own
	# cache knows and writes it into every zone it saves; elsewhere each load then warns "invalid
	# UID". A committed zone names that file by its path alone.
	var text := FileAccess.get_file_as_string("res://zones/editor_glade/editor_glade.tscn")
	for line in text.split("\n"):
		if line.begins_with("[ext_resource") and line.contains("res://kit/terrain/"):
			assert_str(line).not_contains("uid=")
	# it is a fixture, not a place in the game
	var zones: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/zones.json"))
	assert_bool(zones.has("editor_glade")).is_false()

func test_the_glade_blocks_its_pond_and_props_and_leaves_its_path_open() -> void:
	var root := _glade()
	add_child(root)
	for i in 4:
		await get_tree().process_frame
		await get_tree().physics_frame
	var ground := root.get_node("Ground") as TerrainGround
	var walk := ground.get_node("KitWalk") as KitWalk
	assert_that(walk.rows).is_equal(KitWalk.derive(ground))
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/zones/editor_glade.json"))
	for y in plan.rows.size():
		for x in plan.rows[y].length():
			var material: String = plan.legend[plan.rows[y][x]]
			if material == "water":
				assert_str(walk.rows[y * 2][x * 2]).override_failure_message("water at %d,%d is open" % [x, y]).is_equal("#")
	for id in plan.spawns:
		var at := Vector2(plan.spawns[id][0], plan.spawns[id][1])
		assert_str(walk.rows[int(at.y / 12)][int(at.x / 12)]).override_failure_message("spawn %s is blocked" % id).is_equal(".")
	# the body the game uses stops at the pond and walks the path
	var space := root.get_world_2d().direct_space_state
	var probe := PhysicsShapeQueryParameters2D.new()
	probe.shape = CircleShape2D.new()
	(probe.shape as CircleShape2D).radius = 6.0
	probe.collision_mask = 1
	var pond := Vector2.ZERO
	for y in plan.rows.size() - 1:
		for x in plan.rows[y].length() - 1:
			var water := true
			for cell in [[x, y], [x + 1, y], [x, y + 1], [x + 1, y + 1]]:
				water = water and plan.legend[plan.rows[cell[1]][cell[0]]] == "water"
			if water and pond == Vector2.ZERO:
				pond = Vector2(x + 1, y + 1) * 24.0
	assert_vector(pond).is_not_equal(Vector2.ZERO)
	probe.transform = Transform2D(0.0, pond)
	assert_int(space.intersect_shape(probe).size()).is_greater(0)
	probe.transform = Transform2D(0.0, Vector2(plan.spawns.start[0], plan.spawns.start[1]))
	assert_int(space.intersect_shape(probe).size()).is_equal(0)
