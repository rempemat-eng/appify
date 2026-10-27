extends GdUnitTestSuite
## The terrain kit in Godot (docs/world-editor.md): the kit loads, the kit lab zone's cells carry the
## material metadata the validator and the walk mask read, painting a cell redraws the ground, and
## the cells match the zone's JSON plan (scripts/art/kit/test_kit.py holds the shader to compose.py).

const LAB := "res://zones/kitlab/kitlab.tscn"

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
