extends SceneTree
## A kit zone's JSON plan <-> its Godot scene (docs/world-editor.md, "Zone authoring").
##
##   $GODOT --headless --path game -s tools/kit_zone.gd -- --plan=res://kit/zones/kitlab.json
##       writes the plan's scene (res://zones/<zone>/<zone>.tscn unless --out=): a Zone root, the
##       TerrainGround with its Cells layer painted from the plan's rows, Actors and Spawns.
##   $GODOT --headless --path game -s tools/kit_zone.gd -- --export=res://zones/kitlab/kitlab.tscn [--out=<json>]
##       writes the scene's cells back into its plan (rows in the plan's legend), so a zone painted
##       in the editor and a zone written as JSON are the same data.
## The prototype handles terrain and spawns; props, tiers, water and doors join it with the rest
## of the editor (Codex package W2, docs/world-editor.md).

func _initialize() -> void:
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2, a.find("=") - 2)] = a.substr(a.find("=") + 1)
	var code := 1
	if args.has("plan"):
		code = _build(args.plan, args.get("out", ""))
	elif args.has("export"):
		code = _export(args.export, args.get("out", ""))
	else:
		printerr("kit_zone: --plan=<json> or --export=<tscn>")
	quit(code)

func _plan(path: String) -> Dictionary:
	var p = JSON.parse_string(FileAccess.get_file_as_string(path))
	return p if p is Dictionary else {}

func _build(path: String, out: String) -> int:
	var plan := _plan(path)
	if plan.is_empty():
		printerr("kit_zone: cannot read ", path)
		return 1
	var kit := TerrainKit.shared()
	var zone_id: String = plan.zone
	var rows: Array = plan.rows
	var legend: Dictionary = plan.legend
	var size := Vector2i(rows[0].length(), rows.size())
	var root := Node2D.new()
	root.name = zone_id.capitalize().replace(" ", "")
	root.set_script(load("res://world/zone.gd"))
	root.set("zone_id", zone_id)
	root.set("bounds", Rect2(Vector2.ZERO, Vector2(size * kit.cell)))
	root.y_sort_enabled = true
	var ground := TerrainGround.new()
	ground.name = "Ground"
	ground.grid_size = size
	ground.z_index = -10
	root.add_child(ground)
	ground.owner = root
	var cells := TileMapLayer.new()
	cells.name = "Cells"
	cells.tile_set = kit.tileset
	ground.add_child(cells)
	cells.owner = root
	for y in size.y:
		var row: String = rows[y]
		for x in size.x:
			var id: String = legend.get(row[x], "")
			if id == "":
				continue
			var ac := kit.atlas_coords(id)
			if ac.x < 0:
				printerr("kit_zone: '%s' is not a kit material" % id)
				return 1
			cells.set_cell(Vector2i(x, y), 0, ac)
	var actors := Node2D.new()
	actors.name = "Actors"
	actors.y_sort_enabled = true
	root.add_child(actors)
	actors.owner = root
	var spawns := Node2D.new()
	spawns.name = "Spawns"
	root.add_child(spawns)
	spawns.owner = root
	var sp: Dictionary = plan.get("spawns", {"start": [size.x * kit.cell / 2, size.y * kit.cell / 2]})
	for s in sp:
		var m := Marker2D.new()
		m.name = s
		m.position = Vector2(sp[s][0], sp[s][1])
		spawns.add_child(m)
		m.owner = root
	var scene := PackedScene.new()
	scene.pack(root)
	if out == "":
		out = "res://zones/%s/%s.tscn" % [zone_id, zone_id]
	DirAccess.make_dir_recursive_absolute(out.get_base_dir())
	var err := ResourceSaver.save(scene, out)
	root.free()
	print("kit_zone: wrote ", out, " (", size.x, " x ", size.y, " cells)")
	return 0 if err == OK else 1

func _export(path: String, out: String) -> int:
	var scene := load(path) as PackedScene
	var root := scene.instantiate()
	var ground := root.get_node("Ground") as TerrainGround
	var cells := ground.get_node("Cells") as TileMapLayer
	var zone_id: String = root.get("zone_id")
	var plan_path := out if out != "" else "res://kit/zones/%s.json" % zone_id
	var plan := _plan(plan_path)
	var legend: Dictionary = plan.get("legend", {})
	var back := {}
	for k in legend:
		back[legend[k]] = k
	var rows := []
	for y in ground.grid_size.y:
		var row := ""
		for x in ground.grid_size.x:
			var td := cells.get_cell_tile_data(Vector2i(x, y))
			var id := "" if td == null else String(td.get_custom_data("material"))
			if id == "":
				row += " "
				continue
			if not back.has(id):
				var free := "abcdefghijklmnopqrstuvwxyz0123456789"
				for ch in free:
					if not legend.has(ch):
						legend[ch] = id
						back[id] = ch
						break
			row += back[id]
		rows.append(row)
	plan["zone"] = zone_id
	plan["legend"] = legend
	plan["rows"] = rows
	var f := FileAccess.open(plan_path, FileAccess.WRITE)
	f.store_string(JSON.stringify(plan, " ", false) + "\n")
	f.close()
	root.free()
	print("kit_zone: wrote ", plan_path)
	return 0
