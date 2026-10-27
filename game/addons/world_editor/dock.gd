@tool
extends VBoxContainer
## The dock's palette, hover card and rule checks (addons/world_editor/plugin.gd).

var plugin
var zone: Node
var ground: TerrainGround
var mats: ItemList
var pieces: ItemList
var card: RichTextLabel
var status: Label

static func snap(local: Vector2, how: String) -> Vector2:
	match how:
		"cell":   # the foot on the cell's centre or its half across, on the cell line down (4 / 8 world px)
			return Vector2(roundf(local.x / 12.0) * 12.0, roundf(local.y / 24.0) * 24.0)
		"half":
			return Vector2(roundf(local.x / 12.0) * 12.0, roundf(local.y / 12.0) * 12.0)
	return local.round()

func _ready() -> void:
	custom_minimum_size = Vector2(320, 0)
	var title := Label.new()
	title.text = "World editor: kit and library"
	add_child(title)
	add_child(_label("Terrain (paint cells)"))
	mats = ItemList.new()
	mats.custom_minimum_size = Vector2(0, 150)
	mats.max_columns = 0
	mats.icon_mode = ItemList.ICON_MODE_TOP
	mats.fixed_icon_size = Vector2i(48, 48)
	add_child(mats)
	add_child(_label("Pieces (place on the soft grid)"))
	pieces = ItemList.new()
	pieces.custom_minimum_size = Vector2(0, 260)
	pieces.fixed_icon_size = Vector2i(40, 40)
	add_child(pieces)
	card = RichTextLabel.new()
	card.bbcode_enabled = true
	card.fit_content = true
	card.custom_minimum_size = Vector2(0, 220)
	add_child(card)
	var v := Button.new()
	v.text = "Validate zone"
	v.pressed.connect(_validate)
	add_child(v)
	status = Label.new()
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	add_child(status)
	# the kit's pictures may still be importing (a fresh checkout, a rebuilt kit): fill the palette
	# once the editor's file system is ready
	_fill()
	mats.item_selected.connect(func(i: int) -> void:
		pieces.deselect_all()
		plugin.brush = "material:" + String(mats.get_item_metadata(i))
		_show_material(String(mats.get_item_metadata(i))))
	pieces.item_selected.connect(func(i: int) -> void:
		mats.deselect_all()
		plugin.brush = "piece:" + String(pieces.get_item_metadata(i))
		show_piece(String(pieces.get_item_metadata(i))))
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--we-show="):
			show_piece(a.substr(10))
			for i in pieces.item_count:
				if pieces.get_item_metadata(i) == a.substr(10):
					pieces.select(i)
					pieces.ensure_current_is_visible()

func _label(t: String) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_color_override("font_color", Color(0.75, 0.8, 0.7))
	return l

func _fill() -> void:
	if mats.item_count > 0:
		return
	var fs := EditorInterface.get_resource_filesystem()
	if fs.is_scanning() or not TerrainKit.ready_to_load():
		if not fs.filesystem_changed.is_connected(_fill):
			fs.filesystem_changed.connect(_fill)
		return
	if fs.filesystem_changed.is_connected(_fill):
		fs.filesystem_changed.disconnect(_fill)
	var kit: TerrainKit = TerrainKit.fresh()
	var pal := (load("res://kit/terrain/palette.png") as Texture2D).get_image()
	var ms: Array = kit.manifest.materials
	for i in ms.size():
		var img := pal.get_region(Rect2i(i * kit.cell, 0, kit.cell, kit.cell))
		var idx := mats.add_item(String(ms[i].id), ImageTexture.create_from_image(img))
		mats.set_item_metadata(idx, ms[i].id)
		mats.set_item_tooltip(idx, "%s: %s, %s" % [ms[i].id, ms[i].surface, ms[i].approval])
	var ids := KitPiece.index().keys()
	ids.sort()
	for id in ids:
		var e: Dictionary = KitPiece.index()[id]
		var v: Dictionary = e.variants.values()[0]
		var tex := load(v.png) as Texture2D
		var idx := pieces.add_item("%s  [%s]" % [id, e.approval], tex)
		pieces.set_item_metadata(idx, id)

func set_zone(z: Node, g: TerrainGround) -> void:
	zone = z
	ground = g
	say("Zone: %s" % (z.name if z != null else "none"))

func say(t: String) -> void:
	if status != null:
		status.text = t

func _show_material(id: String) -> void:
	var m: Dictionary = TerrainKit.shared().by_id[id]
	card.text = "[b]%s[/b]  (material %d)\nsurface %s, walkable %s, route %s\npriority %d, approval [i]%s[/i]" % [
		id, int(m.material_id), m.surface, m.walkable, m.get("route", false), int(m.priority), m.approval]

func show_piece(id: String) -> void:
	var e: Dictionary = KitPiece.index().get(id, {})
	if e.is_empty():
		return
	var t := "[b]%s[/b]  %s, [i]%s[/i]\n" % [e.name, e.kind, e.approval]
	if e.get("size_cells") != null:
		t += "size %s cells, foot %s, snap %s\n" % [str(e.size_cells), str(e.foot), e.snap]
	t += "role: %s\n" % str(e.get("role"))
	for r in e.get("requires", []):
		t += "[color=#9c9]needs[/color] %s %s%s\n" % [r.rel, r.what, (" within %s cells" % str(r.cells)) if r.has("cells") else ""]
	for r in e.get("forbids", []):
		t += "[color=#c99]never[/color] %s %s\n" % [r.rel, r.what]
	var f: Dictionary = e.get("function", {})
	if f.get("interact") != null:
		t += "use: %s\n" % str(f.interact.get("verb"))
	var s: Dictionary = e.get("story", {})
	if s.get("owner") != null:
		t += "belongs to %s\n" % s.owner
	t += "blocks movement: %s, shadow: %s" % [e.blocks_move, "yes" if e.shadow != null else "baked/none"]
	card.text = t

func hover(cell: Vector2i, _local: Vector2) -> void:
	if ground == null:
		return
	var mid := ground.material_at(cell)
	var name := "-" if mid == 0 else String(TerrainKit.shared().by_material[mid].id)
	status.text = "cell %s: %s" % [cell, name]

## Why a piece may not stand at `at` (texels in the zone), or "" when it may.
func refusal(id: String, at: Vector2) -> String:
	var e: Dictionary = KitPiece.index().get(id, {})
	if e.is_empty():
		return "%s is not in the library" % id
	if e.approval != "approved" and not ground.lab:
		return "%s has not passed the library gate (%s); only a lab zone may place it" % [id, e.approval]
	var cell := Vector2i(floori(at.x / 24.0), floori((at.y - 1.0) / 24.0))
	var kit := TerrainKit.shared()
	var here := ground.material_at(cell)
	var m: Dictionary = kit.by_material.get(here, {})
	for r in e.get("forbids", []):
		if r.rel == "on" and r.what == "route" and bool(m.get("route", false)):
			return "%s never stands on a route (ground-rules 4)" % id
		if r.rel == "on" and r.what == "water" and m.get("water") != null:
			return "%s never stands in water" % id
	for r in e.get("requires", []):
		if r.what == "route_edge" or (r.rel == "at_edge" and r.what == "route"):
			var n := int(r.get("cells", 1))
			var found := false
			for dy in range(-n, n + 1):
				for dx in range(-n, n + 1):
					var mm: Dictionary = kit.by_material.get(ground.material_at(cell + Vector2i(dx, dy)), {})
					if bool(mm.get("route", false)):
						found = true
			if not found:
				return "%s needs a route edge within %d cells (ground-rules 6)" % [id, n]
	return ""

func _validate() -> void:
	if zone == null:
		say("Select a kit zone first")
		return
	var faults := []
	var cand := 0
	for p in ground.pieces():
		var e: Dictionary = p.data()
		if e.get("approval", "") != "approved":
			cand += 1
		var cell := Vector2i(floori(p.position.x / 24.0), floori((p.position.y - 1.0) / 24.0))
		var m: Dictionary = TerrainKit.shared().by_material.get(ground.material_at(cell), {})
		if bool(e.get("blocks_move", false)) and bool(m.get("route", false)) and e.get("role") != "bridge":
			faults.append("%s stands on a route" % p.name)
	say("%d faults%s; %d pieces not yet approved. Full checks: python3 -m scripts.review.kit_rules" % [
		faults.size(), (": " + ", ".join(faults)) if faults.size() > 0 else "", cand])
