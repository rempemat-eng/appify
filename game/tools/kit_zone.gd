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
	ground.lab = bool(plan.get("lab", false))
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
	if plan.has("tiers"):
		var tl := TileMapLayer.new()
		tl.name = "Tiers"
		tl.tile_set = kit.tiers_tileset
		ground.add_child(tl)
		tl.owner = root
		var trows: Array = plan.tiers
		for y in size.y:
			var tr: String = trows[y]
			for x in size.x:
				var tv := int(tr[x]) if tr[x] >= "0" and tr[x] <= "9" else 0
				if tv > 0:
					tl.set_cell(Vector2i(x, y), 0, Vector2i(tv, 0))
	# the pieces, each its library scene at its foot (the ground's shadow pass finds them)
	var props := Node2D.new()
	props.name = "Props"
	props.y_sort_enabled = true
	root.add_child(props)
	props.owner = root
	for pc in plan.get("pieces", []):
		var ps := load("res://kit/props/%s.tscn" % pc.piece) as PackedScene
		if ps == null:
			printerr("kit_zone: no piece scene for '%s'" % pc.piece)
			return 1
		var inst := ps.instantiate() as KitPiece
		inst.name = String(pc.get("id", pc.piece)).replace("/", "_")
		inst.position = Vector2(pc.at[0], pc.at[1])
		if pc.has("variant"):
			inst.variant = pc.variant
		if String(KitPiece.index().get(pc.piece, {}).get("z_sort", "foot")) == "ground":
			inst.z_index = -5
		props.add_child(inst)
		inst.owner = root
	# the gameplay: from another zone's scene (the same doors, spawns, people and camps), or empty
	if plan.has("gameplay_from"):
		var src := (load(plan.gameplay_from) as PackedScene).instantiate()
		for n in ["Actors", "Spawns", "Doors"]:
			var node := src.get_node_or_null(n)
			if node == null:
				continue
			src.remove_child(node)
			node.owner = null
			root.add_child(node)
			_own(node, root, src)
		src.free()
	for n in ["Actors", "Spawns"]:
		if root.get_node_or_null(n) == null:
			var nd := Node2D.new()
			nd.name = n
			nd.y_sort_enabled = n == "Actors"
			root.add_child(nd)
			nd.owner = root
	var spawns := root.get_node("Spawns")
	var sp: Dictionary = plan.get("spawns", {})
	if sp.is_empty() and spawns.get_child_count() == 0:
		sp = {"start": [size.x * kit.cell / 2, size.y * kit.cell / 2]}
	for s_ in sp:
		if spawns.get_node_or_null(NodePath(s_)) != null:
			continue
		var m := Marker2D.new()
		m.name = s_
		m.position = Vector2(sp[s_][0], sp[s_][1])
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

## Give `node` and the nodes it brought from `src` to `root` (instanced sub-scenes keep their own).
func _own(node: Node, root: Node, src: Node) -> void:
	if node.owner == src or node.owner == null:
		node.owner = root
	for c in node.get_children():
		if c.owner == src:
			_own(c, root, src)

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
			var ac := cells.get_cell_atlas_coords(Vector2i(x, y))
			var mats: Array = TerrainKit.shared().manifest.materials
			var id := "" if ac.x < 0 or ac.x >= mats.size() else String(mats[ac.x].id)
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
	var tl := ground.get_node_or_null("Tiers") as TileMapLayer
	if tl != null:
		var trows := []
		for y in ground.grid_size.y:
			var tr := ""
			for x in ground.grid_size.x:
				tr += str(maxi(0, tl.get_cell_atlas_coords(Vector2i(x, y)).x))
			trows.append(tr)
		plan["tiers"] = trows
	var props := root.get_node_or_null("Props")
	if props != null:
		var pieces := []
		for c in props.get_children():
			if c is KitPiece:
				var e := {"id": String(c.name), "piece": c.piece_id, "at": [int(c.position.x), int(c.position.y)]}
				if c.variant != "":
					e["variant"] = c.variant
				pieces.append(e)
		plan["pieces"] = pieces
	var f := FileAccess.open(plan_path, FileAccess.WRITE)
	f.store_string(JSON.stringify(plan, " ", false) + "\n")
	f.close()
	root.free()
	print("kit_zone: wrote ", plan_path)
	return 0
