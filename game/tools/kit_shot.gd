extends SceneTree
## Capture the live terrain shader, its piece shadows and edge dressing at one image pixel per
## terrain texel. Baked ground, prop pictures, actors, UI and cameras never enter the viewport.
##
## Run with a real renderer (for example xvfb-run -a $GODOT --display-driver x11
## --rendering-method gl_compatibility --rendering-driver opengl3 --audio-driver Dummy
## --path game --script res://tools/kit_shot.gd -- --scene=res://zones/kitlab/kitlab.tscn
## --out=/tmp/kitlab.png --compare=res://test/fixtures/kit/kitlab.png).
## --plan=<json> also works. --headless normally selects the dummy renderer and is an error,
## not a successful blank screenshot. The static capture/compare methods can be used by tests
## without instantiating this SceneTree script or running the CLI.

static func _failure(message: String) -> Dictionary:
	return {"ok": false, "error": message}


static func renderer_info() -> Dictionary:
	return {"display": DisplayServer.get_name(),
		"adapter": RenderingServer.get_video_adapter_name(),
		"method": RenderingServer.get_current_rendering_method()}


static func _plan_stage(path: String) -> Dictionary:
	var parser := JSON.new()
	var err := parser.parse(FileAccess.get_file_as_string(path))
	if err != OK or not parser.data is Dictionary:
		return _failure("cannot read plan %s: %s" % [path, parser.get_error_message()])
	var plan: Dictionary = parser.data
	var units: Variant = plan.get("coordinate_space", "texels")
	if units not in ["texels", "cells"]:
		return _failure("coordinate_space must be texels or cells: " + path)
	var rows: Variant = plan.get("rows")
	var legend: Variant = plan.get("legend")
	if not rows is Array or rows.is_empty() or not rows[0] is String or rows[0].is_empty() or not legend is Dictionary:
		return _failure("plan needs nonempty string rows and a material legend: " + path)
	var kit := TerrainKit.shared()
	var size := Vector2i(rows[0].length(), rows.size())
	for row in rows:
		if not row is String or row.length() != size.x:
			return _failure("plan rows have different widths: " + path)
		for symbol in row:
			if not legend.has(symbol) or (str(legend[symbol]) != "" and kit.material_id(str(legend[symbol])) == 0):
				return _failure("plan has an unknown material at symbol '%s': %s" % [symbol, path])
	var tiers: Variant = plan.get("tiers", [])
	if not tiers is Array or (not tiers.is_empty() and tiers.size() != size.y):
		return _failure("plan tiers must match the material rows: " + path)
	for row in tiers:
		if not row is String or row.length() != size.x:
			return _failure("plan tier rows have different widths: " + path)
		for symbol in row:
			if symbol < "0" or symbol > "9":
				return _failure("plan tiers must contain digits: " + path)
	var stage := Node2D.new()
	stage.name = "KitCapture"
	var ground := TerrainGround.new()
	ground.name = "Ground"
	ground.grid_size = size
	ground.z_index = -10
	ground.lab = true
	var cells := TileMapLayer.new()
	cells.name = "Cells"
	cells.tile_set = kit.tileset
	ground.add_child(cells)
	stage.add_child(ground)
	for y in size.y:
		for x in size.x:
			var id := str(legend[rows[y][x]])
			if id != "":
				cells.set_cell(Vector2i(x, y), 0, kit.atlas_coords(id))
	if not tiers.is_empty():
		var layer := TileMapLayer.new()
		layer.name = "Tiers"
		layer.tile_set = kit.tiers_tileset
		ground.add_child(layer)
		for y in size.y:
			for x in size.x:
				var tier := int(tiers[y][x])
				if tier > 0:
					layer.set_cell(Vector2i(x, y), 0, Vector2i(tier, 0))
	var props := Node2D.new()
	props.name = "Props"
	stage.add_child(props)
	var entries: Variant = plan.get("pieces", [])
	if not entries is Array:
		stage.free()
		return _failure("plan pieces must be an array: " + path)
	var unit := float(kit.cell) if units == "cells" else 1.0
	for entry in entries:
		if not entry is Dictionary or not entry.get("at") is Array or entry.at.size() != 2 or not KitPiece.index().has(str(entry.get("piece", ""))):
			stage.free()
			return _failure("plan has an invalid piece or foot: " + path)
		for coordinate in entry.at:
			if typeof(coordinate) not in [TYPE_INT, TYPE_FLOAT] or not is_finite(float(coordinate)) or absf(float(coordinate) * unit) > 3.402823466e38:
				stage.free()
				return _failure("piece foot must contain finite coordinates in range: " + path)
		# Only a KitPiece's metadata and shadow are needed. No sprite or gameplay is instanced.
		var piece := KitPiece.new()
		piece.piece_id = str(entry.piece)
		piece.position = Vector2(float(entry.at[0]) * unit, float(entry.at[1]) * unit)
		piece.variant = str(entry.get("variant", ""))
		props.add_child(piece)
	return {"ok": true, "stage": stage, "ground": ground}


static func _clear_owners(node: Node) -> void:
	node.owner = null
	for child in node.get_children():
		_clear_owners(child)


static func _scene_stage(path: String) -> Dictionary:
	var packed := load(path) as PackedScene
	if packed == null:
		return _failure("cannot load scene: " + path)
	# The source zone stays outside the tree: its actors, doors, camera and zone script never run.
	var source := packed.instantiate()
	var ground := source.get_node_or_null("Ground") as TerrainGround
	if ground == null:
		source.free()
		return _failure("scene has no TerrainGround named Ground: " + path)
	var stage := Node2D.new()
	stage.name = "KitCapture"
	ground.get_parent().remove_child(ground)
	_clear_owners(ground)
	stage.add_child(ground)
	var props := source.get_node_or_null("Props")
	if props != null:
		# Recreate metadata-only instances so custom prop scripts and pictures cannot draw.
		var plain_props := Node2D.new()
		plain_props.name = "Props"
		stage.add_child(plain_props)
		for child in props.get_children():
			if child is KitPiece:
				var piece := KitPiece.new()
				piece.piece_id = child.piece_id
				piece.variant = child.variant
				piece.position = child.position
				plain_props.add_child(piece)
	source.free()
	return {"ok": true, "stage": stage, "ground": ground}


## Await a real SubViewport readback. `shader_override` is only for negative parity fixtures;
## it changes this capture's private material, never the shared shader or the saved zone.
static func capture(tree: SceneTree, source: String, options: Dictionary = {}) -> Dictionary:
	var renderer := renderer_info()
	if renderer.display == "headless" or str(renderer.adapter).is_empty() or "dummy" in str(renderer.adapter).to_lower():
		return _failure("pixel capture requires a real renderer; dummy/headless rendering has no pixels (use Xvfb with OpenGL)")
	if not TerrainKit.ready_to_load():
		return _failure("terrain kit textures are not imported; run the Godot editor import first")
	var built := _plan_stage(source) if source.get_extension() == "json" else _scene_stage(source)
	if not built.ok:
		return built
	var stage: Node2D = built.stage
	var ground: TerrainGround = built.ground
	if ground.position != Vector2.ZERO or ground.scale != Vector2.ONE or ground.rotation != 0.0:
		stage.free()
		return _failure("TerrainGround must have an identity transform for 1:1 parity")
	ground.baked = null
	ground.show_cells = false
	var extent := ground.grid_size * TerrainKit.shared().cell
	if extent.x <= 0 or extent.y <= 0:
		stage.free()
		return _failure("terrain has an empty extent")
	var viewport := SubViewport.new()
	viewport.name = "KitPixelCapture"
	viewport.size = extent
	viewport.disable_3d = true
	viewport.world_2d = World2D.new()
	viewport.transparent_bg = true
	viewport.use_hdr_2d = false
	viewport.msaa_2d = Viewport.MSAA_DISABLED
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	viewport.snap_2d_transforms_to_pixel = true
	viewport.snap_2d_vertices_to_pixel = true
	viewport.render_target_clear_mode = SubViewport.CLEAR_MODE_ALWAYS
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	tree.root.add_child(viewport)
	viewport.add_child(stage)
	await tree.process_frame
	ground._rebuild()
	ground.rebuild_shadows()
	if options.has("shader_override"):
		ground._mat.shader = options.shader_override
	if not bool(options.get("dressing", true)):
		ground._dressing().visible = false
	await RenderingServer.frame_post_draw
	await tree.process_frame
	await RenderingServer.frame_post_draw
	var image := viewport.get_texture().get_image()
	if image == null or image.is_empty() or image.get_size() != extent:
		viewport.free()
		return _failure("renderer returned no complete viewport image")
	image.convert(Image.FORMAT_RGBA8)
	var pixels := image.get_data()
	var has_opaque := false
	for i in range(3, pixels.size(), 4):
		if pixels[i] != 0:
			has_opaque = true
			break
	viewport.free()
	if not has_opaque:
		return _failure("renderer returned a blank transparent image")
	return {"ok": true, "error": "", "image": image, "size": extent,
		"renderer": renderer, "scale": 1, "baked": false, "prop_sprites": false,
		"dressing": bool(options.get("dressing", true))}


## Compare every RGBA8 channel, including RGB beneath transparent pixels. No tolerance,
## resampling, palette remapping, alpha masking or image-format-specific byte comparison.
static func compare(actual: Image, expected: Image) -> Dictionary:
	if actual == null or expected == null or actual.is_empty() or expected.is_empty():
		return {"ok": false, "equal": false, "error": "cannot compare an empty image"}
	if actual.get_size() != expected.get_size():
		return {"ok": true, "equal": false, "error": "image dimensions differ",
			"actual_size": actual.get_size(), "expected_size": expected.get_size()}
	var left := actual.duplicate() as Image
	var right := expected.duplicate() as Image
	if left.is_compressed() and left.decompress() != OK:
		return {"ok": false, "equal": false, "error": "cannot decompress actual image"}
	if right.is_compressed() and right.decompress() != OK:
		return {"ok": false, "equal": false, "error": "cannot decompress expected image"}
	left.convert(Image.FORMAT_RGBA8)
	right.convert(Image.FORMAT_RGBA8)
	var a := left.get_data()
	var b := right.get_data()
	var result := {"ok": true, "equal": a == b, "error": "", "size": left.get_size(),
		"different_pixels": 0, "different_channels": 0, "max_channel_delta": 0,
		"first_difference": Vector2i(-1, -1)}
	if a == b:
		return result
	for pixel in left.get_width() * left.get_height():
		var differs := false
		for channel in 4:
			var delta := absi(int(a[pixel * 4 + channel]) - int(b[pixel * 4 + channel]))
			if delta > 0:
				differs = true
				result.different_channels += 1
				result.max_channel_delta = maxi(result.max_channel_delta, delta)
		if differs:
			result.different_pixels += 1
			if result.first_difference == Vector2i(-1, -1):
				result.first_difference = Vector2i(pixel % left.get_width(), pixel / left.get_width())
	return result


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := {}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--") and "=" in argument:
			var split := argument.find("=")
			var key := argument.substr(2, split - 2)
			if args.has(key):
				printerr("kit_shot: duplicate option --", key)
				quit(1)
				return
			args[key] = argument.substr(split + 1)
		else:
			printerr("kit_shot: expected --name=value, got ", argument)
			quit(1)
			return
	for key in args:
		if key not in ["scene", "plan", "out", "compare"]:
			printerr("kit_shot: unknown option --", key)
			quit(1)
			return
	if args.has("scene") == args.has("plan") or not args.has("out"):
		printerr("kit_shot: exactly one --scene=<tscn> or --plan=<json>, plus --out=<png> required")
		quit(1)
		return
	var result := await capture(self, str(args.get("scene", args.get("plan", ""))))
	if not result.ok:
		print("KIT_SHOT_RESULT ", JSON.stringify({"ok": false, "equal": false, "different_pixels": -1, "error": result.error}))
		printerr("kit_shot: ", result.error)
		quit(1)
		return
	var image: Image = result.image
	var path := str(args.out)
	var err := DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path.get_base_dir()))
	if err != OK and err != ERR_ALREADY_EXISTS:
		printerr("kit_shot: cannot create output directory: ", error_string(err))
		quit(1)
		return
	err = image.save_png(path)
	if err != OK:
		printerr("kit_shot: cannot write ", path, ": ", error_string(err))
		quit(1)
		return
	print("kit_shot: wrote %s (%s, 1:1, live shader + shadows + dressing)" % [path, image.get_size()])
	if args.has("compare"):
		var reference := Image.new()
		var reference_bytes := FileAccess.get_file_as_bytes(str(args.compare))
		var loaded := reference.load_png_from_buffer(reference_bytes) if not reference_bytes.is_empty() else ERR_FILE_NOT_FOUND
		if loaded != OK:
			print("KIT_SHOT_RESULT ", JSON.stringify({"ok": false, "equal": false, "different_pixels": -1, "error": "cannot load reference PNG: " + str(args.compare)}))
			printerr("kit_shot: cannot load reference PNG: ", args.compare)
			quit(1)
			return
		var comparison := compare(image, reference)
		print("KIT_SHOT_RESULT ", JSON.stringify(comparison))
		if not comparison.ok or not comparison.equal:
			printerr("kit_shot: exact pixel comparison failed")
			quit(1)
			return
	else:
		print("KIT_SHOT_RESULT ", JSON.stringify({"ok": true, "equal": null, "different_pixels": -1, "error": "", "width": image.get_width(), "height": image.get_height()}))
	quit(0)
