extends GdUnitTestSuite
## EDITOR-PERSISTENCE/r1: source candidate; engine/import/tests NOT RUN.
## Requires a lead-allocated copied engine, imported disposable project and private XDG roots.
## Failures retain disk files in that private user directory for collection.
const Tool := preload("res://tools/kit_zone.gd")
const FIXTURE := "res://test/fixtures/editor_persistence.json"

func _plan() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))

func _disk(root: Node2D, label_: String) -> Node2D:
	var path := "user://persistence_%s_%s.tscn" % [label_, Time.get_ticks_usec()]
	var packed := PackedScene.new()
	assert_int(packed.pack(root)).is_equal(OK)
	assert_int(ResourceSaver.save(packed, path)).is_equal(OK)
	var reopened := ResourceLoader.load(path, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE) as PackedScene
	assert_object(reopened).is_not_null()
	if reopened == null:
		return null
	var result := reopened.instantiate() as Node2D
	auto_free(result)
	# Keep actual input/reopened scenes even on failure; outer collector owns disposal.
	print("persistence evidence: ", path)
	return result

func test_minimal_authored_zone_survives_disk_export_and_rebuild() -> void:
	var expected := _plan()
	assert_str(Tool.plan_error(expected)).is_empty()
	var root := Tool.scene_from_plan(expected)
	assert_object(root).is_not_null()
	if root == null:
		return
	auto_free(root)
	var reopened := _disk(root, "canary")
	if reopened == null:
		return
	var exported := Tool.plan_from_scene(reopened)
	assert_str(Tool.canonical(exported)).is_equal(Tool.canonical(expected))
	var rebuilt := Tool.scene_from_plan(exported)
	assert_object(rebuilt).is_not_null()
	if rebuilt == null:
		return
	auto_free(rebuilt)
	var again := _disk(rebuilt, "rebuilt")
	if again != null:
		assert_str(Tool.canonical(Tool.plan_from_scene(again))).is_equal(Tool.canonical(expected))

func test_native_deletions_and_literal_ids_survive_two_saved_generations() -> void:
	var expected := _plan()
	var root := Tool.scene_from_plan(expected)
	assert_object(root).is_not_null()
	if root == null:
		return
	auto_free(root)
	var spawns := root.get_node("Spawns")
	for child in spawns.get_children():
		if child.get_meta(&"kit_zone_id", "") == "remove":
			child.free()
	expected.spawns.erase("remove")
	var doors := root.get_node("Doors")
	for child in doors.get_children():
		if child.get_meta(&"kit_zone_entry", {}).get("id", "") == "a_b":
			child.free()
	expected.doors.remove_at(1)
	root.get_node("Ground/Flow").free()
	expected.erase("flow")
	var reopened := _disk(root, "deleted")
	if reopened == null:
		return
	var exported := Tool.plan_from_scene(reopened)
	assert_str(Tool.canonical(exported)).is_equal(Tool.canonical(expected))
	assert_int(reopened.get_node("Spawns").get_child_count()).is_equal(2)
	assert_int(reopened.get_node("Doors").get_child_count()).is_equal(1)
	var rebuilt := Tool.scene_from_plan(exported)
	assert_object(rebuilt).is_not_null()
	if rebuilt == null:
		return
	auto_free(rebuilt)
	var again := _disk(rebuilt, "deleted_rebuilt")
	if again != null:
		assert_str(Tool.canonical(Tool.plan_from_scene(again))).is_equal(Tool.canonical(expected))
