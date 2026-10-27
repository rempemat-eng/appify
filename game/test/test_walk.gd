extends GdUnitTestSuite
## W4's real TileMap metadata, exact walk/collision coverage and physics contract.

const Walk := preload("res://world/terrain/walk.gd")

class StubPiece extends KitPiece:
	var metadata: Dictionary
	func data() -> Dictionary:
		return metadata

func _fixture(size := Vector2i(5, 4), authored_walk := false) -> Dictionary:
	var root := Node2D.new()
	root.position = Vector2(37, 19)
	var ground := TerrainGround.new()
	ground.name = "Ground"
	ground.grid_size = size
	ground.position = Vector2(24, 48)
	ground.lab = true
	var cells := TileMapLayer.new()
	cells.name = "Cells"
	ground.add_child(cells)
	var tiers := TileMapLayer.new()
	tiers.name = "Tiers"
	ground.add_child(tiers)
	if authored_walk:
		var walk := Walk.new()
		walk.name = "Walk"
		ground.add_child(walk)
	root.add_child(ground)
	add_child(auto_free(root))
	for y in size.y:
		for x in size.x:
			ground.paint_cell(Vector2i(x, y), "lawn")
	await get_tree().process_frame
	await get_tree().physics_frame
	return {"root": root, "ground": ground}

func _piece(fixture: Dictionary, at: Vector2, metadata: Dictionary) -> KitPiece:
	var parent := Node2D.new()
	parent.position = Vector2(-31, 11)
	fixture.root.add_child(parent)
	var piece := StubPiece.new()
	piece.metadata = metadata
	parent.add_child(piece)
	piece.global_position = fixture.ground.to_global(at)
	return piece

func _install(ground: TerrainGround) -> KitWalk:
	var walk := Walk.new()
	ground.add_child(walk)
	assert_bool(walk.rebuild(ground)).is_true()
	return walk

func test_water_footprint_and_face_block_exact_cells() -> void:
	var fixture := await _fixture()
	var ground: TerrainGround = fixture.ground
	ground.paint_cell(Vector2i(0, 0), "water")
	ground.paint_tier(Vector2i(3, 0), 1)
	_piece(fixture, Vector2(48, 72), {"blocks_move": true, "footprint": [[0, 0]]})
	var walk := _install(ground)
	assert_array(Array(walk.rows)).is_equal([
		"##...####.", "##...####.", "......##..", "......##..",
		"......##..", "......##..", "....##....", "....##...."])
	assert_int(walk.rows.size()).is_equal(8)
	assert_int(walk.rows[0].length()).is_equal(10)

func test_tile_custom_walkability_is_authoritative_in_same_step() -> void:
	var fixture := await _fixture(Vector2i(2, 1))
	var ground: TerrainGround = fixture.ground
	var cells := ground.get_cells_layer()
	cells.tile_set = cells.tile_set.duplicate(true)
	var atlas := cells.tile_set.get_source(0) as TileSetAtlasSource
	var tile := atlas.get_tile_data(ground.kit.atlas_coords("lawn"), 0)
	tile.set_custom_data("walkable", false)
	assert_array(Array(Walk.derive(ground))).is_equal(["####", "####"])

func test_precise_collision_precedes_coarse_footprint_and_clips() -> void:
	var fixture := await _fixture(Vector2i(3, 2))
	_piece(fixture, Vector2(0, 0), {"blocks_move": true,
		"collision": [-6, -6, 19, 19], "footprint": [[2, 1]]})
	_piece(fixture, Vector2(-60, 0), {"blocks_move": true, "collision": [0, 0, 12, 12]})
	_piece(fixture, Vector2(0, -60), {"blocks_move": true, "collision": [0, 0, 12, 12]})
	_piece(fixture, Vector2(0, 36), {"blocks_move": false, "collision": [0, 0, 72, 12]})
	assert_array(Array(Walk.derive(fixture.ground))).is_equal([
		"##....", "##....", "......", "......"])

func test_deck_opens_water_but_not_a_solid_on_the_deck() -> void:
	var fixture := await _fixture(Vector2i(3, 2))
	var ground: TerrainGround = fixture.ground
	ground.paint_cell(Vector2i(1, 0), "water")
	_piece(fixture, Vector2(24, 0), {"blocks_move": false, "deck": [0, 0, 24, 24]})
	_piece(fixture, Vector2(24, 0), {"blocks_move": true, "collision": [0, 0, 12, 12]})
	assert_array(Array(Walk.derive(ground))).is_equal([
		"..#...", "......", "......", "......"])

func test_deck_quarter_cell_threshold_and_translated_piece_parent() -> void:
	var fixture := await _fixture(Vector2i(2, 1))
	var ground: TerrainGround = fixture.ground
	ground.paint_cell(Vector2i(0, 0), "water")
	ground.paint_cell(Vector2i(1, 0), "water")
	_piece(fixture, Vector2.ZERO, {"deck": [0, 0, 12, 12]})
	_piece(fixture, Vector2(24, 0), {"deck": [0, 0, 11, 12]})
	assert_array(Array(Walk.derive(ground))).is_equal(["..##", "..##"])

func test_tier_side_wall_is_in_mask_and_deck_connects_it() -> void:
	var fixture := await _fixture(Vector2i(3, 1))
	var ground: TerrainGround = fixture.ground
	ground.paint_tier(Vector2i(0, 0), 1)
	assert_array(Array(Walk.derive(ground))).is_equal([".##...", ".##..."])
	_piece(fixture, Vector2.ZERO, {"deck": [0, 0, 48, 24]})
	assert_array(Array(Walk.derive(ground))).is_equal(["......", "......"])

func test_merge_matches_gen_zone_and_partitions_mask_without_overlap() -> void:
	var mask := PackedStringArray(["##..#", "##..#", ".####", "..##."])
	var rects := Walk.merge_blocked(mask)
	assert_array(rects).is_equal([
		Rect2i(0, 0, 2, 2), Rect2i(4, 0, 1, 2),
		Rect2i(1, 2, 4, 1), Rect2i(2, 3, 2, 1)])
	var coverage := {}
	for rect in rects:
		for y in range(rect.position.y, rect.end.y):
			for x in range(rect.position.x, rect.end.x):
				var cell := Vector2i(x, y)
				assert_bool(coverage.has(cell)).is_false()
				coverage[cell] = true
	for y in mask.size():
		for x in mask[y].length():
			assert_bool(coverage.has(Vector2i(x, y))).is_equal(mask[y][x] == "#")
	assert_array(Walk.merge_blocked(PackedStringArray())).is_empty()

func test_export_writes_gen_zone_rows_and_final_newline() -> void:
	var fixture := await _fixture(Vector2i(2, 1))
	fixture.ground.paint_cell(Vector2i(1, 0), "water")
	var walk := _install(fixture.ground)
	var path := "user://w4-walk.txt"
	assert_int(walk.write_walk(path)).is_equal(OK)
	assert_str(FileAccess.get_file_as_string(path)).is_equal("..##\n..##\n")
	assert_str(walk.walk_text()).is_equal("..##\n..##\n")
	DirAccess.remove_absolute(path)
	var empty: KitWalk = auto_free(Walk.new())
	assert_int(empty.write_walk(path)).is_equal(ERR_UNCONFIGURED)

func test_authored_child_installs_after_parent_and_rejects_duplicate_owner() -> void:
	var fixture := await _fixture(Vector2i(2, 1), true)
	await get_tree().process_frame
	var ground: TerrainGround = fixture.ground
	assert_int(ground.get_node("Blocked").collision_layer).is_equal(0)
	assert_int(ground.get_node("WalkBlocked").collision_layer).is_equal(1)
	var duplicate: KitWalk = auto_free(Walk.new())
	assert_bool(duplicate.rebuild(ground)).is_false()
	var bodies := 0
	for child in ground.get_children(true):
		if child is StaticBody2D and child.collision_layer != 0:
			bodies += 1
	assert_int(bodies).is_equal(1)

func test_reparented_piece_regains_its_original_collision_layer() -> void:
	var fixture := await _fixture(Vector2i(3, 2))
	var piece := _piece(fixture, Vector2(24, 0), {"blocks_move": true, "collision": [0, 0, 24, 24]})
	var legacy := StaticBody2D.new()
	legacy.name = "Solid"
	legacy.collision_layer = 5
	piece.add_child(legacy)
	var walk := _install(fixture.ground)
	assert_int(legacy.collision_layer).is_equal(0)
	var elsewhere := Node2D.new()
	add_child(auto_free(elsewhere))
	piece.reparent(elsewhere)
	assert_bool(walk.rebuild()).is_true()
	assert_int(legacy.collision_layer).is_equal(5)

func test_transfer_between_walk_owners_preserves_layer_in_both_rebuild_orders() -> void:
	for destination_first in [false, true]:
		var from := await _fixture(Vector2i(3, 2))
		var to := await _fixture(Vector2i(3, 2))
		var piece := _piece(from, Vector2(24, 0), {"blocks_move": true, "collision": [0, 0, 24, 24]})
		var legacy := StaticBody2D.new()
		legacy.name = "Solid"
		legacy.collision_layer = 5
		piece.add_child(legacy)
		var source_walk := _install(from.ground)
		var destination_walk := _install(to.ground)
		piece.reparent(to.root)
		piece.global_position = to.ground.to_global(Vector2(24, 0))
		if destination_first:
			assert_bool(destination_walk.rebuild()).is_true()
			assert_int(legacy.collision_layer).is_equal(0)
			assert_bool(source_walk.rebuild()).is_true()
		else:
			assert_bool(source_walk.rebuild()).is_true()
			assert_int(legacy.collision_layer).is_equal(5)
			assert_bool(destination_walk.rebuild()).is_true()
		assert_int(legacy.collision_layer).is_equal(0)
		assert_str(source_walk.rows[0]).is_equal("......")
		assert_str(destination_walk.rows[0]).is_equal("..##..")
		destination_walk.free()
		assert_int(legacy.collision_layer).is_equal(5)
		source_walk.free()
		assert_int(legacy.collision_layer).is_equal(5)

func test_destination_owns_transferred_body_when_source_exits_first() -> void:
	var from := await _fixture(Vector2i(3, 2))
	var to := await _fixture(Vector2i(3, 2))
	var piece := _piece(from, Vector2(24, 0), {"blocks_move": true, "collision": [0, 0, 24, 24]})
	var legacy := StaticBody2D.new()
	legacy.name = "Solid"
	legacy.collision_layer = 5
	piece.add_child(legacy)
	var source_walk := _install(from.ground)
	var destination_walk := _install(to.ground)
	piece.reparent(to.root)
	piece.global_position = to.ground.to_global(Vector2(24, 0))
	assert_bool(destination_walk.rebuild()).is_true()
	source_walk.free()
	assert_int(legacy.collision_layer).is_equal(0)
	destination_walk.free()
	assert_int(legacy.collision_layer).is_equal(5)

func test_return_transfer_reclaims_body_before_old_owner_cleanup() -> void:
	var from := await _fixture(Vector2i(3, 2))
	var to := await _fixture(Vector2i(3, 2))
	var piece := _piece(from, Vector2(24, 0), {"blocks_move": true, "collision": [0, 0, 24, 24]})
	var legacy := StaticBody2D.new()
	legacy.name = "Solid"
	legacy.collision_layer = 5
	piece.add_child(legacy)
	var source_walk := _install(from.ground)
	var destination_walk := _install(to.ground)
	piece.reparent(to.root)
	assert_bool(destination_walk.rebuild()).is_true()
	# Return before either owner's previous tracking entry has been cleaned up.
	piece.reparent(from.root)
	assert_bool(source_walk.rebuild()).is_true()
	destination_walk.free()
	assert_int(legacy.collision_layer).is_equal(0)
	source_walk.free()
	assert_int(legacy.collision_layer).is_equal(5)
	assert_bool(legacy.has_meta(Walk.BODY_OWNER_META)).is_false()
	assert_bool(legacy.has_meta(Walk.BODY_LAYER_META)).is_false()

func test_deleted_owned_body_is_safe_to_release() -> void:
	var fixture := await _fixture(Vector2i(3, 2))
	var piece := _piece(fixture, Vector2(24, 0), {"blocks_move": true, "collision": [0, 0, 24, 24]})
	var legacy := StaticBody2D.new()
	legacy.name = "Solid"
	piece.add_child(legacy)
	var walk := _install(fixture.ground)
	piece.free()
	assert_bool(walk.rebuild()).is_true()
	assert_str(walk.rows[0]).is_equal("......")
	walk.free()

func test_install_replaces_only_generated_bodies_and_restores_them() -> void:
	var fixture := await _fixture(Vector2i(3, 2))
	var ground: TerrainGround = fixture.ground
	var piece := _piece(fixture, Vector2(24, 0), {"blocks_move": true, "collision": [0, 0, 24, 24]})
	var legacy := StaticBody2D.new()
	legacy.name = "Solid"
	legacy.collision_layer = 5
	piece.add_child(legacy)
	var authored := StaticBody2D.new()
	authored.name = "AuthoredWall"
	ground.add_child(authored)
	var old := ground.get_node("Blocked") as StaticBody2D
	var walk := _install(ground)
	assert_int(old.collision_layer).is_equal(0)
	assert_int(legacy.collision_layer).is_equal(0)
	assert_int(authored.collision_layer).is_equal(1)
	assert_bool(walk.rebuild()).is_true()
	assert_int(ground.get_node("WalkBlocked").get_child_count()).is_equal(1)
	walk.free()
	await get_tree().process_frame
	assert_int(old.collision_layer).is_equal(1)
	assert_int(legacy.collision_layer).is_equal(5)
	assert_bool(ground.has_node("WalkBlocked")).is_false()

func test_player_physics_cannot_enter_metadata_walls_and_cells_can_reopen() -> void:
	var fixture := await _fixture(Vector2i(5, 4))
	var ground: TerrainGround = fixture.ground
	for y in ground.grid_size.y:
		ground.paint_cell(Vector2i(2, y), "water")
	var walk := _install(ground)
	var player: Player = load("res://actors/player.tscn").instantiate()
	player.input_enabled = false
	ground.add_child(player)
	player.position = Vector2(18, 60)
	await get_tree().physics_frame
	await get_tree().physics_frame
	var collision := player.move_and_collide(Vector2(90, 0))
	assert_object(collision).is_not_null()
	assert_float(player.position.x).is_less(48.0)
	for y in ground.grid_size.y:
		ground.paint_cell(Vector2i(2, y), "lawn")
	assert_bool(walk.rebuild()).is_true()
	await get_tree().process_frame
	await get_tree().physics_frame
	await get_tree().physics_frame
	player.position = Vector2(18, 60)
	assert_object(player.move_and_collide(Vector2(90, 0))).is_null()
	assert_float(player.position.x).is_equal(108.0)
	assert_str(walk.rows[0]).is_equal("..........")
