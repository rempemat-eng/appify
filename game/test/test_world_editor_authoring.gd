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
	ops.configure(zone, ground, history, {"library": _library(), "relation_evaluator": Callable(Rules, "placement"), "install_walk": true})
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

# --- wave 2 (11 Nov): the faults docs/world-editor.md recorded as open

func _scene_text(zone: Node) -> String:
	var packed := PackedScene.new()
	assert_int(packed.pack(zone)).is_equal(OK)
	var path := "user://authoring_scene_text.tscn"
	assert_int(ResourceSaver.save(packed, path)).is_equal(OK)
	var text := FileAccess.get_file_as_string(path)
	DirAccess.remove_absolute(path)
	var ids := RegEx.new()
	ids.compile("(unique_id=\\d+|uid=\"[^\"]*\"|id=\"[^\"]*\"|(Ext|Sub)Resource\\(\"[^\"]*\"\\))")
	return ids.sub(text, "", true)

func test_the_first_edits_undo_takes_the_walk_node_out_again() -> void:
	# An edit and its undo left an older lab scene with a KitWalk node it never had; saving then
	# changed how the zone collides (N1). The node now joins and leaves with the first edit.
	var f := await _fixture()
	var ground: TerrainGround = f.ground
	assert_object(ground.get_node_or_null("KitWalk")).is_null()
	var before := _scene_text(f.zone)
	assert_bool(f.operations.paint_cells([Vector2i(0, 0)], "path").ok).is_true()
	var walk := ground.get_node_or_null("KitWalk") as KitWalk
	assert_object(walk).is_not_null()
	assert_object(walk.owner).is_same(f.zone)
	assert_that(walk.rows).is_equal(KitWalk.derive(ground))
	# a second edit adds no second node, and its undo leaves the first
	assert_bool(f.operations.place_piece("woodland_stump", Vector2(132, 48)).ok).is_true()
	assert_bool(f.history.undo()).is_true()
	assert_object(ground.get_node_or_null("KitWalk")).is_same(walk)
	assert_bool(f.history.undo()).is_true()
	assert_object(ground.get_node_or_null("KitWalk")).is_null()
	assert_str(_scene_text(f.zone)).is_equal(before)
	assert_bool(f.history.redo()).is_true()
	assert_object(ground.get_node_or_null("KitWalk")).is_same(walk)
	assert_that(walk.rows).is_equal(KitWalk.derive(ground))

func test_a_stale_bake_stays_stale_through_a_save() -> void:
	# The "bake is current" flag was not saved, so a reopened zone showed its old baked ground
	# over cells painted since.
	var f := await _fixture()
	var ground: TerrainGround = f.ground
	ground.baked = load("res://zones/kitlab/ground_baked.png")
	assert_bool(ground.showing_baked()).is_true()
	var fresh := PackedScene.new()
	assert_int(fresh.pack(f.zone)).is_equal(OK)
	var current := fresh.instantiate()
	_scenes.append(current)
	add_child(current)
	assert_bool((current.get_node("Ground") as TerrainGround).showing_baked()).is_true()
	assert_bool(f.operations.paint_cells([Vector2i(0, 0)], "path").ok).is_true()
	assert_bool(ground.showing_baked()).is_false()
	var packed := PackedScene.new()
	assert_int(packed.pack(f.zone)).is_equal(OK)
	var again := packed.instantiate()
	_scenes.append(again)
	add_child(again)
	var reopened := again.get_node("Ground") as TerrainGround
	assert_object(reopened.baked).is_not_null()
	assert_bool(reopened.showing_baked()).is_false()
	# a new bake is current again, and that is saved too
	reopened.baked = load("res://zones/kitlab_tiers/ground_baked.png")
	assert_bool(reopened.showing_baked()).is_true()
	assert_int(packed.pack(again)).is_equal(OK)
	var third := packed.instantiate()
	_scenes.append(third)
	add_child(third)
	assert_bool((third.get_node("Ground") as TerrainGround).showing_baked()).is_true()

func test_a_new_zone_needs_ground_somebody_can_stand_on() -> void:
	assert_str(ZonePlan.new_zone_error("my_zone", "40x23", "lawn")).is_equal("")
	assert_str(ZonePlan.new_zone_error("my_zone", "40x23", "water")).contains("nobody can stand on")
	assert_str(ZonePlan.new_zone_error("my_zone", "40x23", "earth_face")).contains("nobody can stand on")
	assert_str(ZonePlan.new_zone_error("my_zone", "40x23", "tarmac")).contains("not a built terrain material")
	assert_str(ZonePlan.new_zone_error("My-Zone", "40x23", "lawn")).contains("zone id")
	assert_str(ZonePlan.new_zone_error("my_zone", "0x23", "lawn")).contains("--size")

func test_the_kits_tile_sets_carry_their_own_ids() -> void:
	# Without one the editor invents an id, keeps it in its own cache and writes it into every zone
	# it saves; any other checkout then warns "invalid UID" on each load.
	var header := RegEx.new()
	header.compile("^\\[gd_resource [^\\]]*uid=\"(uid://[a-y0-8]+)\"\\]")
	for file in ["materials.tres", "tiers.tres"]:
		var found := header.search(FileAccess.get_file_as_string("res://kit/terrain/" + file))
		assert_object(found).override_failure_message(file + " has no uid in its header").is_not_null()
		if found == null:
			continue
		# and the project knows the file by that id, so a scene that names it resolves
		var id := ResourceUID.text_to_id(found.get_string(1))
		assert_bool(ResourceUID.has_id(id)).is_true()
		assert_str(ResourceUID.get_id_path(id)).is_equal("res://kit/terrain/" + file)

# --- wave 2, step 3: height and water flow are painted in the dock

func test_the_tier_brush_paints_height_with_undo_and_the_walk_mask_follows() -> void:
	var f := await _fixture()
	var ops: Operations = f.operations
	var ground: TerrainGround = f.ground
	var before := ZonePlan.canonical(ops.export_plan().plan)
	assert_object(ground.get_tiers_layer()).is_null()
	var block := [Vector2i(4, 0), Vector2i(5, 0), Vector2i(4, 1), Vector2i(5, 1)]
	var painted: Dictionary = ops.paint_tiers(block, 1)
	assert_bool(painted.ok).override_failure_message(str(painted)).is_true()
	var plan: Dictionary = ops.export_plan().plan
	assert_that(plan.tiers.slice(0, 3)).is_equal(["0000110000", "0000110000", "0000000000"])
	assert_str(ZonePlan.plan_error(plan)).is_equal("")
	# the game's own derivation: a face under the south rim, and it is not walkable
	assert_int(ground.tier_at(Vector2i(4, 1))).is_equal(1)
	assert_int(ground.ground_at(Vector2i(4, 2))).is_equal(ground.kit.face_material)
	var walk := ground.get_node("KitWalk") as KitWalk
	assert_that(walk.rows).is_equal(KitWalk.derive(ground))
	assert_str(walk.rows[4][8]).is_equal("#")                 # the face cell (4, 2)
	assert_str(walk.rows[0][7]).is_equal("#")                 # the wall on the plateau's west edge
	assert_str(walk.rows[0][9]).is_equal(".")                 # the plateau's top is open
	# a second stroke raises part of it; its undo leaves the first
	assert_bool(ops.paint_tiers([Vector2i(5, 0)], 2).ok).is_true()
	assert_str(ops.export_plan().plan.tiers[0]).is_equal("0000120000")
	assert_bool(f.history.undo()).is_true()
	assert_str(ops.export_plan().plan.tiers[0]).is_equal("0000110000")
	# the first stroke's undo takes the layer it added out again: the plan is as it was
	assert_bool(f.history.undo()).is_true()
	assert_object(ground.get_tiers_layer()).is_null()
	assert_str(ZonePlan.canonical(ops.export_plan().plan)).is_equal(before)
	assert_bool(f.history.redo()).is_true()
	assert_int(ground.tier_at(Vector2i(5, 1))).is_equal(1)
	assert_that(walk.rows).is_equal(KitWalk.derive(ground))
	# refusals leave no history
	var version: int = f.history.get_version()
	assert_str(ops.paint_tiers(block, 4).diagnostics[0].rule).is_equal("rules.tier")
	assert_str(ops.paint_tiers([Vector2i(40, 0)], 1).diagnostics[0].rule).is_equal("rules.bounds")
	assert_bool(ops.paint_tiers(block, 1).changed).is_false()
	assert_int(f.history.get_version()).is_equal(version)

func test_tiers_painted_with_the_brush_give_the_mask_python_derives() -> void:
	# The parity fixture's plan with its tiers taken out, then painted back with the brush: the
	# plan is the fixture's again and the walk mask is the one walk.py derives from it.
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://test/fixtures/kit/walk_parity.json"))
	var flat: Dictionary = fixture.plan.duplicate(true)
	flat.erase("tiers")
	var zone := ZonePlan.scene_from_plan(flat)
	add_child(zone)
	await get_tree().process_frame
	var ground := zone.get_node("Ground") as TerrainGround
	var history := UndoRedo.new()
	var ops := Operations.new()
	ops.configure(zone, ground, history, {})
	_fixtures.append({"zone": zone, "ground": ground, "history": history, "operations": ops})
	for tier in [1, 2]:
		var cells := []
		for y in fixture.plan.tiers.size():
			for x in fixture.plan.tiers[y].length():
				if int(fixture.plan.tiers[y][x]) == tier:
					cells.append(Vector2i(x, y))
		assert_bool(ops.paint_tiers(cells, tier).ok).is_true()
	assert_that(ops.export_plan().plan.tiers).is_equal(fixture.plan.tiers)
	assert_that(Array(KitWalk.derive(ground))).is_equal(fixture.rows)

func test_the_flow_brush_paints_direction_on_water_only_with_undo() -> void:
	var f := await _fixture()
	var ops: Operations = f.operations
	var before := ZonePlan.canonical(ops.export_plan().plan)
	# the fixture's pond is cells (8..9, 6..7); the stroke overruns onto the lawn at (7, 6)
	var flowed: Dictionary = ops.paint_flow([Vector2i(7, 6), Vector2i(8, 6), Vector2i(8, 7)], "↓")
	assert_bool(flowed.ok).override_failure_message(str(flowed)).is_true()
	assert_int(flowed.skipped_dry).is_equal(1)
	assert_that(flowed.warnings).is_empty()                  # (8, 6) runs into (8, 7), which runs off the zone
	var plan: Dictionary = ops.export_plan().plan
	assert_that(plan.flow.slice(5, 8)).is_equal(["..........", "........↓.", "........↓."])
	assert_str(ZonePlan.plan_error(plan)).is_equal("")
	# the plan rebuilds to a zone that exports the same flow
	var rebuilt := ZonePlan.scene_from_plan(plan)
	_scenes.append(rebuilt)
	assert_that(ZonePlan.plan_from_scene(rebuilt).flow).is_equal(plan.flow)
	# another direction beside it, then erase one cell
	assert_bool(ops.paint_flow([Vector2i(9, 6)], "↘").ok).is_true()
	# an arrow that runs onto the lawn is painted, and named as unfinished
	var ashore: Dictionary = ops.paint_flow([Vector2i(9, 6)], "↑")
	assert_str(ashore.warnings[0].rule).is_equal("rules.water_flow")
	assert_bool(f.history.undo()).is_true()
	assert_bool(ops.paint_flow([Vector2i(8, 7)], ".").ok).is_true()
	assert_that(ops.export_plan().plan.flow.slice(6, 8)).is_equal(["........↓↘", ".........."])
	for i in 3:
		assert_bool(f.history.undo()).is_true()
	assert_object(f.ground.get_node_or_null("Flow")).is_null()
	assert_str(ZonePlan.canonical(ops.export_plan().plan)).is_equal(before)
	assert_bool(f.history.redo()).is_true()
	assert_str(ops.export_plan().plan.flow[6]).is_equal("........↓.")
	# an arrow on dry ground only is refused with the validator's own rule; a wrong glyph too
	var version: int = f.history.get_version()
	assert_str(ops.paint_flow([Vector2i(0, 0)], "→").diagnostics[0].rule).is_equal("rules.water_flow")
	assert_str(ops.paint_flow([Vector2i(8, 6)], "x").diagnostics[0].rule).is_equal("rules.water_flow")
	assert_int(f.history.get_version()).is_equal(version)

# --- wave 2, step 4: a sign's round post is its body and its walk cells

func test_a_signs_round_post_is_its_body_and_the_cells_the_mask_blocks() -> void:
	# The three signs' records give a round post (radius 5 texels at the foot). The prop builder
	# dropped it: their scenes had no body, and the walk mask blocked their whole 2 by 2 footprint.
	for id in ["woodland_stone_sign", "crossroads_waystone", "crossroads_notice_board"]:
		var entry: Dictionary = KitPiece.index()[id]
		assert_that(entry.get("collision_circle")).override_failure_message("%s: no round post in the index" % id).is_equal(5.0)
		assert_that(entry.collision).is_equal([-5.0, -5.0, 10.0, 10.0])
		var piece := (load("res://kit/props/%s.tscn" % id) as PackedScene).instantiate()
		_scenes.append(piece)
		var solid := piece.get_node_or_null("Solid") as StaticBody2D
		assert_object(solid).override_failure_message("%s: no body in its scene" % id).is_not_null()
		var collider := solid.get_node("Shape") as CollisionShape2D
		assert_bool(collider.shape is CircleShape2D).is_true()
		assert_float((collider.shape as CircleShape2D).radius).is_equal(5.0)
		assert_that(collider.position).is_equal(Vector2.ZERO)
	# one sign on a walk-grid node and one off it, on open lawn
	var plan := {"zone": "sign_fixture", "lab": true, "legend": {".": "lawn"},
		"rows": ["..........", "..........", "..........", ".........."], "spawns": {"start": [12, 12]},
		"pieces": [{"id": "on", "piece": "woodland_stone_sign", "at": [60, 48], "variant": "sign"},
			{"id": "off", "piece": "woodland_stone_sign", "at": [162, 54], "variant": "sign"}]}
	var zone := ZonePlan.scene_from_plan(plan)
	add_child(zone)
	_scenes.append(zone)
	await get_tree().process_frame
	var rows := KitWalk.derive(zone.get_node("Ground") as TerrainGround)
	var blocked := {}
	for y in rows.size():
		for x in rows[y].length():
			if rows[y][x] == "#":
				blocked[Vector2i(x, y)] = true
	# every texel inside either post lies in a blocked cell, and every blocked cell holds such a
	# texel or touches the circle: the mask is the body, to the grid
	var expected := {}
	for centre in [Vector2(60, 48), Vector2(162, 54)]:
		for y in range(-6, 7):
			for x in range(-6, 7):
				var at: Vector2 = centre + Vector2(x, y) + Vector2(0.5, 0.5)
				if at.distance_to(centre) < 5.0:
					expected[Vector2i(floori(at.x / KitWalk.STEP), floori(at.y / KitWalk.STEP))] = true
	assert_that(blocked.keys()).contains_exactly_in_any_order(expected.keys())
	assert_int(blocked.size()).is_equal(4 + 1)                # the node's four cells; one cell off it

func test_a_drystone_run_is_drawn_from_the_walls_own_pieces() -> void:
	# The run tool named every cell fence_<style>_<joins>; the drystone wall's cells are
	# wall_drystone_<joins>, so the Brackens' fold could not be drawn ("Unknown fence piece").
	var f := await _fixture()
	var ops: Operations = f.operations
	var library := _library()
	for id in ["wall_drystone_e", "wall_drystone_ew", "wall_drystone_sw", "wall_drystone_n"]:
		var piece: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/pieces/prop/%s.json" % id))
		library[id] = piece
	ops.configure(f.zone, f.ground, f.history, {"library": library, "relation_evaluator": Callable(Rules, "placement"), "install_walk": true})
	var run: Dictionary = ops.place_fence_run("drystone", [Vector2i(1, 0), Vector2i(2, 0), Vector2i(3, 0), Vector2i(3, 1)])
	assert_bool(run.ok).override_failure_message(str(run)).is_true()
	var ids := []
	for piece in f.zone.get_node("Props").get_children():
		ids.append(piece.piece_id)
	ids.sort()
	assert_that(ids).is_equal(["wall_drystone_e", "wall_drystone_ew", "wall_drystone_n", "wall_drystone_sw"])

func test_the_walk_node_is_a_real_instance_in_the_editor() -> void:
	# A zone saved once holds its KitWalk. In the editor a script that is not a tool script gives
	# that node a placeholder, and the add-on's rebuild() after every edit failed on it.
	assert_bool((load("res://world/terrain/walk.gd") as Script).is_tool()).is_true()

func test_the_dock_offers_the_tier_and_flow_brushes() -> void:
	var f := await _fixture()
	var d := _dock(f)
	var dock: Control = d.dock
	dock.tier_select.select(2)
	(dock.find_child("TierBrush", true, false) as Button).pressed.emit()
	assert_str(d.plugin.brush).is_equal("tier:2")
	dock.flow_select.select(3)
	(dock.find_child("FlowBrush", true, false) as Button).pressed.emit()
	assert_str(d.plugin.brush).is_equal("flow:→")
	dock.select_tool()
	assert_str(d.plugin.brush).is_equal("")

# --- the bake runs beside the editor, shows its progress and can be stopped

const BakeJob := preload("res://addons/world_editor/bake_job.gd")

func _python() -> String:
	var python := OS.get_environment("PYTHON")
	return "python3" if python.is_empty() else python

func _wait_until(done: Callable, seconds: float = 30.0) -> bool:
	var waited := 0.0
	while waited < seconds:
		if done.call():
			return true
		await get_tree().create_timer(0.1).timeout
		waited += 0.1
	return false

func test_a_bake_job_runs_beside_the_caller_reports_progress_and_can_be_cancelled() -> void:
	var log := ProjectSettings.globalize_path("user://bake_job_test.log")
	var job := BakeJob.new()
	# a stand-in for the painters: says where it is, then works for a long time
	var slow := "import sys,time\nf=open(sys.argv[1],'w',buffering=1)\nprint('painting water',file=f,flush=True)\ntime.sleep(120)\n"
	assert_bool(job.start(_python(), slow, PackedStringArray([log]), log, "Baking test")).is_true()
	# start() came back at once: the caller is not waiting for the 120 s
	assert_float(job.seconds()).is_less(5.0)
	assert_bool(await _wait_until(func() -> bool: return job.last_line() == "painting water")).is_true()
	assert_bool(job.running()).is_true()
	assert_str(job.progress_text()).starts_with("Baking test: ")
	assert_str(job.progress_text()).contains("painting water")
	assert_int(job.exit_code()).is_equal(-1)
	job.cancel()
	assert_bool(job.running()).is_false()
	assert_bool(job.cancelled()).is_true()
	assert_int(job.exit_code()).is_not_equal(0)            # killed, not finished
	DirAccess.remove_absolute(log)

func test_a_bake_job_hands_back_the_modules_exit_code_and_output() -> void:
	var repo := ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()
	var log := ProjectSettings.globalize_path("user://bake_job_test_module.log")
	var good := BakeJob.new()
	assert_bool(good.start_module(_python(), repo, "json.tool", PackedStringArray(["--help"]), log)).is_true()
	assert_bool(await _wait_until(func() -> bool: return not good.running())).is_true()
	assert_int(good.exit_code()).is_equal(0)
	assert_str(good.output()).contains("started json.tool")
	var bad := BakeJob.new()
	assert_bool(bad.start_module(_python(), repo, "scripts.art.kit.no_such_module", PackedStringArray(), log)).is_true()
	assert_bool(await _wait_until(func() -> bool: return not bad.running())).is_true()
	assert_int(bad.exit_code()).is_not_equal(0)
	assert_str(bad.output()).contains("no_such_module")
	assert_bool(bad.cancelled()).is_false()
	DirAccess.remove_absolute(log)

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
	# The sign can be read without hunting for the spot. When this was set its piece blocked a
	# square 24 texels either way from its foot and a talk area of the default 30 left a band
	# 2 world px deep (the audit of #465); 44 left 20 texels. Since wave 2 the sign blocks only
	# its round post, so the reach is more than was needed; it is kept.
	var sign: Area2D = root.get_node("Actors/Sign")
	var reach: float = (sign.get_node("Shape") as CollisionShape2D).shape.radius
	assert_float(reach).is_equal(44.0)
	assert_float(reach + 9.0 - (24.0 + 9.0)).is_greater_equal(18.0)
	# rebuilt from its plan it exports the same plan: no authored data lives only in the scene.
	# (The scene files still differ: the dock-saved one holds a KitWalk node, the rebuilt one
	# does not, so the stone sign collides differently. docs/world-editor.md lists that as open.)
	var rebuilt := ZonePlan.scene_from_plan(plan)
	_scenes.append(rebuilt)
	assert_str(ZonePlan.canonical(ZonePlan.plan_from_scene(rebuilt))).is_equal(ZonePlan.canonical(plan))
	assert_that(ZonePlan.unexported_actors(root)).is_empty()
	assert_bool(root.get_node("Ground").has_meta(&"kit_walk_owner")).is_false()
	assert_object(root.get_node_or_null("Edge")).is_not_null()
	# When the glade was saved kit/terrain/materials.tres had no uid of its own, and the editor
	# invented one that only its own cache knew. The glade names that file by its path alone; a
	# zone saved since wave 2 names it by the file's own uid (the Brackens lab below).
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

# --- wave 2, step 5: the Brackens' first screen, a lab built in the dock

func _brackens() -> Node2D:
	var root := (load("res://zones/brackens_lab/brackens_lab.tscn") as PackedScene).instantiate() as Node2D
	_scenes.append(root)
	return root

func test_the_brackens_lab_is_a_lab_made_of_the_brackens_own_pieces() -> void:
	var root := _brackens()
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/zones/brackens_lab.json"))
	assert_str(ZonePlan.plan_error(plan)).is_equal("")
	assert_bool(plan.lab).is_true()
	assert_str(plan.note).starts_with("LAB ZONE, not part of the game.")
	# only the Brackens' three grounds and pieces that carry the Brackens biome; none approved
	var materials := {}
	for row in plan.rows:
		for glyph in row:
			materials[plan.legend[glyph]] = true
	for id in materials:
		assert_bool(id in ["heath", "drove", "peat"]).override_failure_message("ground %s is not the Brackens'" % id).is_true()
	assert_int(plan.pieces.size()).is_greater_equal(16)
	for entry in plan.pieces:
		var piece: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/pieces/prop/%s.json" % entry.piece))
		assert_bool("brackens" in piece.biomes).override_failure_message("%s is not a Brackens piece" % entry.piece).is_true()
		assert_str(piece.approval.state).is_equal("candidate")
	# the ridge was painted with the tier brush
	assert_bool("".join(plan.tiers).contains("1") and "".join(plan.tiers).contains("2")).is_true()
	# the scene and the plan are one zone, and the scene names the tile sets by their own ids
	assert_str(ZonePlan.canonical(ZonePlan.plan_from_scene(root))).is_equal(ZonePlan.canonical(plan))
	assert_that(ZonePlan.unexported_actors(root)).is_empty()
	assert_bool(root.get_node("Ground").has_meta(&"kit_walk_owner")).is_false()
	var text := FileAccess.get_file_as_string("res://zones/brackens_lab/brackens_lab.tscn")
	assert_str(text).contains('uid="uid://damjj22xg5kso" path="res://kit/terrain/materials.tres"')
	assert_str(text).not_contains("ground_baked")           # no new picture: it shows live tiles
	# it can be started by name and nothing leads to it: no door in it, none into it
	var zones: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/zones.json"))
	assert_str(zones.get("brackens_lab", "")).is_equal("res://zones/brackens_lab/brackens_lab.tscn")
	assert_bool(plan.has("doors")).is_false()
	for id in zones:
		if id != "brackens_lab":
			assert_str(FileAccess.get_file_as_string(zones[id])).override_failure_message("%s leads to the lab" % id).not_contains("brackens_lab")

func test_the_brackens_lab_can_be_walked_from_end_to_end() -> void:
	var root := _brackens()
	add_child(root)
	for i in 4:
		await get_tree().process_frame
		await get_tree().physics_frame
	var ground := root.get_node("Ground") as TerrainGround
	var walk := ground.get_node("KitWalk") as KitWalk
	assert_that(walk.rows).is_equal(KitWalk.derive(ground))
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/zones/brackens_lab.json"))
	# flood the walk mask from the start spawn
	var start := Vector2i(int(plan.spawns.start[0] / 12), int(plan.spawns.start[1] / 12))
	var seen := {start: true}
	var queue := [start]
	while not queue.is_empty():
		var at: Vector2i = queue.pop_back()
		for step in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
			var next: Vector2i = at + step
			if next.y < 0 or next.y >= walk.rows.size() or next.x < 0 or next.x >= walk.rows[0].length():
				continue
			if not seen.has(next) and walk.rows[next.y][next.x] == ".":
				seen[next] = true
				queue.append(next)
	assert_str(walk.rows[start.y][start.x]).is_equal(".")
	var west := Vector2i(int(plan.spawns.west[0] / 12), int(plan.spawns.west[1] / 12))
	assert_bool(seen.has(west)).override_failure_message("the road is shut between the two spawns").is_true()
	# the ridge is never climbed
	for cell in seen:
		assert_int(ground.tier_at(Vector2i(cell.x / 2, cell.y / 2))).override_failure_message("the ridge can be climbed at %s" % cell).is_equal(0)
	# what stands in the way does stop the body: the hut, the well
	var space := root.get_world_2d().direct_space_state
	var probe := PhysicsShapeQueryParameters2D.new()
	probe.shape = CircleShape2D.new()
	(probe.shape as CircleShape2D).radius = 6.0
	probe.collision_mask = 1
	for entry in plan.pieces:
		if entry.piece in ["brackens_shepherds_hut", "brackens_drove_well"]:
			probe.transform = Transform2D(0.0, Vector2(entry.at[0], entry.at[1] - 12.0))
			assert_int(space.intersect_shape(probe).size()).override_failure_message("%s does not block" % entry.id).is_greater(0)
	probe.transform = Transform2D(0.0, Vector2(plan.spawns.start[0], plan.spawns.start[1]))
	assert_int(space.intersect_shape(probe).size()).is_equal(0)
