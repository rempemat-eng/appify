extends GdUnitTestSuite
## The terrain kit in Godot (docs/world-editor.md): the kit loads, the kit lab zone's cells carry the
## material metadata the validator and the walk mask read, painting a cell redraws the ground, and
## the cells match the zone's JSON plan (scripts/art/kit/test_kit.py holds the shader to compose.py).

const LAB := "res://zones/kitlab/kitlab.tscn"
const SHOT = preload("res://tools/kit_shot.gd")
const REFERENCES := "res://test/fixtures/kit/"
const PALETTE_INPUTS := ["art/house-palette.json", "scripts/art/native/accents.json"]

## check.sh runs GdUnit with the dummy headless driver. Launch a real offscreen GL process
## for image tests; never credit a dummy/blank viewport or a missing X server as a pixel pass.
func _shot(source: String, reference: String, label: String) -> Dictionary:
	var output := "user://kit-parity/%s.png" % label
	var args := PackedStringArray([
		"--rendering-method", "gl_compatibility", "--rendering-driver", "opengl3",
		"--audio-driver", "Dummy", "--path", ProjectSettings.globalize_path("res://"),
		"--script", "res://tools/kit_shot.gd", "--",
		("--plan=" if source.ends_with(".json") else "--scene=") + source,
		"--out=" + output, "--compare=" + reference])
	var executable := OS.get_executable_path()
	if OS.get_name() == "Linux":
		args = PackedStringArray(["--display-driver", "x11"]) + args
		if OS.get_environment("DISPLAY").is_empty():
			args = PackedStringArray(["-a", executable]) + args
			executable = OS.get_environment("KIT_SHOT_XVFB")
			if executable.is_empty():
				executable = "xvfb-run"
	var lines: Array = []
	var code := OS.execute(executable, args, lines, true)
	var log := "\n".join(lines)
	var result: Dictionary = {"exit": code, "log": log, "comparison": {}}
	for line in log.split("\n"):
		if line.begins_with("KIT_SHOT_RESULT "):
			var parsed: Variant = JSON.parse_string(line.trim_prefix("KIT_SHOT_RESULT "))
			if parsed is Dictionary:
				result.comparison = parsed
	return result

func _assert_parity(source: String, reference: String, label: String) -> void:
	var result := _shot(source, reference, label)
	assert_int(result.exit).override_failure_message(result.log).is_equal(0)
	var comparison: Dictionary = result.comparison
	assert_bool(comparison.get("ok", false)).override_failure_message(result.log).is_true()
	assert_bool(comparison.get("equal", false)).override_failure_message(result.log).is_true()
	assert_int(int(comparison.get("different_pixels", -1))).is_equal(0)

func test_live_kitlab_matches_python_ground_shadows_and_dressing() -> void:
	_assert_parity(LAB, REFERENCES + "kitlab.png", "kitlab-scene")

func test_lab_plan_and_scene_both_match_the_python_reference() -> void:
	_assert_parity("res://kit/zones/kitlab.json", REFERENCES + "kitlab.png", "kitlab-plan")

func test_three_material_corner_matches_python() -> void:
	_assert_parity(REFERENCES + "three_materials.json", REFERENCES + "three_materials.png", "three-materials")

func test_shifted_profile_hash_is_rejected_by_real_render_comparison() -> void:
	var result := _shot(REFERENCES + "three_materials.json",
		REFERENCES + "three_materials_shifted_profile.png", "shifted-profile")
	assert_int(result.exit).override_failure_message(result.log).is_equal(1)
	var comparison: Dictionary = result.comparison
	# A missing renderer/reference is an infrastructure failure, not proof of the negative test.
	assert_bool(comparison.get("ok", false)).override_failure_message(result.log).is_true()
	assert_bool(comparison.get("equal", true)).override_failure_message(result.log).is_false()
	assert_int(int(comparison.get("different_pixels", 0))).is_greater(0)

func test_exact_comparison_rejects_one_channel_one_pixel_and_size_changes() -> void:
	var image := Image.create_empty(2, 2, false, Image.FORMAT_RGBA8)
	image.fill(Color8(40, 50, 60, 255))
	assert_bool(SHOT.compare(image, image).equal).is_true()
	var changed := image.duplicate() as Image
	changed.set_pixel(1, 0, Color8(41, 50, 60, 255))
	var comparison: Dictionary = SHOT.compare(image, changed)
	assert_bool(comparison.equal).is_false()
	assert_int(comparison.different_pixels).is_equal(1)
	assert_int(comparison.max_channel_delta).is_equal(1)
	assert_that(comparison.first_difference).is_equal(Vector2i(1, 0))
	assert_bool(SHOT.compare(image, Image.create_empty(1, 2, false, Image.FORMAT_RGBA8)).equal).is_false()

func test_exact_comparison_checks_alpha_and_rgb_beneath_transparency() -> void:
	var image := Image.create_empty(1, 1, false, Image.FORMAT_RGBA8)
	image.set_pixel(0, 0, Color8(40, 50, 60, 0))
	var changed := Image.create_empty(1, 1, false, Image.FORMAT_RGBA8)
	changed.set_pixel(0, 0, Color8(41, 50, 60, 0))
	assert_bool(SHOT.compare(image, changed).equal).is_false()
	changed.set_pixel(0, 0, Color8(40, 50, 60, 1))
	assert_bool(SHOT.compare(image, changed).equal).is_false()

func test_empty_images_are_a_comparison_failure() -> void:
	assert_bool(SHOT.compare(Image.new(), Image.new()).ok).is_false()

## Detect changes in Python, the kit and shadow inputs even on CI hosts without Python's
## scientific packages. Regenerate with fixtures/kit/generate.py and review both renderers.
func test_python_references_match_current_inputs_and_decoded_pixels() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(REFERENCES + "references.json"))
	assert_str(data.schema).is_equal("napattack.kit-render-fixtures/1")
	assert_int(int(data.scale)).is_equal(1)
	assert_int(int(data.feature_pixels.shadows)).is_greater(0)
	assert_int(int(data.feature_pixels.dressing)).is_greater(0)
	var root := ProjectSettings.globalize_path("res://").path_join("..").simplify_path()
	assert_array(_fixture_input_errors(data.source_sha256, root)).is_empty()
	for reference in data.cases:
		assert_str(FileAccess.get_sha256(root.path_join(reference.plan))).is_equal(reference.plan_sha256)
		var image := Image.new()
		assert_int(image.load_png_from_buffer(FileAccess.get_file_as_bytes(REFERENCES + reference.expected))).is_equal(OK)
		image.convert(Image.FORMAT_RGBA8)
		assert_that(image.get_size()).is_equal(Vector2i(reference.size[0], reference.size[1]))
		assert_str(_rgba_hash(image)).is_equal(reference.rgba_sha256)
	var negative := Image.new()
	assert_int(negative.load_png_from_buffer(FileAccess.get_file_as_bytes(REFERENCES + data.negative.file))).is_equal(OK)
	negative.convert(Image.FORMAT_RGBA8)
	assert_str(_rgba_hash(negative)).is_equal(data.negative.rgba_sha256)

func _rgba_hash(image: Image) -> String:
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(image.get_data())
	return context.finish().hex_encode()

func _fixture_input_errors(sources: Dictionary, root: String) -> PackedStringArray:
	var errors := PackedStringArray()
	for path in PALETTE_INPUTS:
		if not sources.has(path):
			errors.append("Missing Python fixture input: " + path)
	for path in sources:
		if FileAccess.get_sha256(root.path_join(path)) != sources[path]:
			errors.append("Stale Python fixture input: " + path)
	return errors

func test_palette_sources_cannot_be_omitted_or_changed_without_refreshing_references() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(REFERENCES + "references.json"))
	var sources: Dictionary = data.source_sha256
	var root := ProjectSettings.globalize_path("res://").path_join("..").simplify_path()
	var copied_root := ProjectSettings.globalize_path("user://kit-parity/palette-inputs-%d" % Time.get_ticks_usec())
	var copied_hashes := {}
	for path in PALETTE_INPUTS:
		assert_bool(sources.has(path)).override_failure_message("Palette source omitted from references: " + path).is_true()
		copied_hashes[path] = sources.get(path, "")
		var copy_path := copied_root.path_join(path)
		assert_int(DirAccess.make_dir_recursive_absolute(copy_path.get_base_dir())).is_equal(OK)
		assert_int(DirAccess.copy_absolute(root.path_join(path), copy_path)).is_equal(OK)
	assert_array(_fixture_input_errors(copied_hashes, copied_root)).is_empty()
	for path in PALETTE_INPUTS:
		var omitted := copied_hashes.duplicate()
		omitted.erase(path)
		assert_array(_fixture_input_errors(omitted, copied_root)).is_equal(PackedStringArray(["Missing Python fixture input: " + path]))
		# Change only the copy; valid JSON with extra whitespace still needs new provenance.
		var copy_path := copied_root.path_join(path)
		var file := FileAccess.open(copy_path, FileAccess.WRITE)
		file.store_buffer(FileAccess.get_file_as_bytes(root.path_join(path)) + " ".to_utf8_buffer())
		file.close()
		assert_array(_fixture_input_errors(copied_hashes, copied_root)).is_equal(PackedStringArray(["Stale Python fixture input: " + path]))
		assert_int(DirAccess.copy_absolute(root.path_join(path), copy_path)).is_equal(OK)
	for path in PALETTE_INPUTS:
		DirAccess.remove_absolute(copied_root.path_join(path))
	for path in ["scripts/art/native", "scripts/art", "scripts", "art", ""]:
		DirAccess.remove_absolute(copied_root.path_join(path))

func test_kit_loads() -> void:
	var kit := TerrainKit.shared()
	assert_int(kit.cell).is_equal(24)
	assert_bool(kit.by_id.has("lawn")).is_true()
	assert_bool(kit.by_id.has("path")).is_true()
	assert_object(kit.fills_tex).is_not_null()
	assert_object(kit.over_tex).is_not_null()
	assert_int(kit.material_id("lawn")).is_equal(1)
	assert_int(kit.material_id("path")).is_equal(2)

func test_lab_cells_carry_metadata() -> void:
	var lab := (load(LAB) as PackedScene).instantiate()
	add_child(lab)
	var ground := lab.get_node("Ground") as TerrainGround
	var cells := ground.get_cells_layer()
	assert_int(ground.material_at(Vector2i(0, 0))).is_equal(1)   # lawn in the corner
	assert_int(ground.material_at(Vector2i(2, 2))).is_equal(2)   # the path's first run
	var td := cells.get_cell_tile_data(Vector2i(2, 2))
	assert_bool(td.get_custom_data("walkable")).is_true()
	assert_bool(td.get_custom_data("route")).is_true()
	assert_str(String(td.get_custom_data("surface"))).is_equal("earth")
	assert_int(ground.material_at(Vector2i(-1, 0))).is_equal(0)  # outside the zone
	assert_that(ground.size_px()).is_equal(Vector2i(960, 552))
	lab.queue_free()

func test_painting_updates_the_ground() -> void:
	var lab := (load(LAB) as PackedScene).instantiate()
	add_child(lab)
	var ground := lab.get_node("Ground") as TerrainGround
	ground.paint_cell(Vector2i(0, 0), "path")
	assert_int(ground.material_at(Vector2i(0, 0))).is_equal(2)
	ground._rebuild()
	# the image the shader's cells texture is updated from (the headless renderer keeps no pixels)
	assert_int(ground._cells_img.get_pixel(0, 0).r8).is_equal(2)
	assert_object((ground._picture.material as ShaderMaterial).get_shader_parameter("cells_tex")).is_not_null()
	ground.paint_cell(Vector2i(0, 0), "")
	assert_int(ground.material_at(Vector2i(0, 0))).is_equal(0)
	lab.queue_free()

func test_rows_round_trip() -> void:
	var lab := (load(LAB) as PackedScene).instantiate()
	add_child(lab)
	var ground := lab.get_node("Ground") as TerrainGround
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://kit/zones/kitlab.json"))
	var kit := TerrainKit.shared()
	var rows := ground.cell_rows()
	for y in rows.size():
		var row: String = plan.rows[y]
		for x in row.length():
			assert_int(rows[y][x]).is_equal(kit.material_id(plan.legend[row[x]]))
	lab.queue_free()

func test_tiers_faces_and_stairs() -> void:
	var lab := (load("res://zones/kitlab_tiers/kitlab_tiers.tscn") as PackedScene).instantiate()
	add_child(lab)
	await get_tree().process_frame
	var ground := lab.get_node("Ground") as TerrainGround
	var kit := TerrainKit.shared()
	assert_int(ground.tier_at(Vector2i(5, 5))).is_equal(1)
	assert_int(ground.ground_at(Vector2i(5, 10))).is_equal(kit.face_material)   # a face under the plateau's rim
	assert_int(ground.ground_at(Vector2i(5, 12))).is_equal(kit.material_id("lawn"))
	var decks := ground.deck_cells()
	assert_bool(decks.has(Vector2i(19, 10))).is_true()                            # the log steps over the face
	assert_bool(decks.has(Vector2i(20, 11))).is_true()
	assert_bool(ground._blocked_cell(Vector2i(5, 10))).is_true()
	lab.queue_free()

func test_walk_mask_from_metadata() -> void:
	var z := (load("res://zones/woodland_kit/woodland_kit.tscn") as PackedScene).instantiate()
	add_child(z)
	await get_tree().process_frame
	await get_tree().process_frame
	var ground := z.get_node("Ground") as TerrainGround
	var blocked := ground.get_node_or_null("Blocked") as StaticBody2D
	assert_object(blocked).is_not_null()
	assert_int(blocked.get_child_count()).is_greater(0)
	# the river is blocked, the footbridge's deck over it is not
	assert_bool(ground._blocked_cell(Vector2i(30, 37))).is_true()
	assert_bool(ground._blocked_cell(Vector2i(15, 37))).is_false()
	z.queue_free()
