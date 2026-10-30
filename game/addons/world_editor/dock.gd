@tool
extends VBoxContainer
## Palette and authoring controls. Placement and validation verdicts belong to operations.gd.

const Tools := preload("res://addons/world_editor/tools.gd")

var plugin
var zone: Node
var ground: TerrainGround
var mats: ItemList
var pieces: ItemList
var variants: ItemList
var card: RichTextLabel
var status: Label
var tool_select: OptionButton
var brush_select: SpinBox
var route_select: OptionButton
var facing_select: OptionButton
var piece_variant_select: OptionButton
var stage_select: OptionButton
var zone_label: Label
var approval_label: Label
var validate_button: Button
var bake_button: Button
var _materials := {}
var _pieces := {}
var _manifest := {}
var _palette_image: Image
var _building := false
var _last_lab := false
var _last_facing := ""
var _shown_piece := ""
var _hovered_key := ""
var _content: VBoxContainer

static func snap(local: Vector2, how: String) -> Vector2:
	return Tools.snap(local, how)

func _ready() -> void:
	custom_minimum_size = Vector2(320, 0)
	var scroll := ScrollContainer.new()
	scroll.name = "ControlsScroll"
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	add_child(scroll)
	_content = VBoxContainer.new()
	_content.name = "Controls"
	_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_content)
	_content.add_child(_label("World editor: kit and library"))
	zone_label = _label("Select a kit zone")
	_content.add_child(zone_label)
	approval_label = _label("")
	approval_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_content.add_child(approval_label)
	var refresh := Button.new()
	refresh.text = "Refresh library"
	refresh.pressed.connect(refresh_palette)
	_content.add_child(refresh)

	tool_select = OptionButton.new()
	tool_select.name = "ToolMode"
	for mode in ["brush", "rectangle", "route"]:
		tool_select.add_item(_text(mode).capitalize())
		tool_select.set_item_metadata(tool_select.item_count - 1, mode)
	tool_select.item_selected.connect(_tool_selected)
	_content.add_child(_row("Terrain tool", tool_select))
	brush_select = SpinBox.new()
	brush_select.name = "BrushSize"
	brush_select.min_value = 1
	brush_select.max_value = 3
	brush_select.step = 1
	brush_select.suffix = "cells"
	brush_select.value_changed.connect(_brush_changed)
	_content.add_child(_row("Brush width", brush_select))
	route_select = OptionButton.new()
	route_select.name = "RouteWidth"
	for width in [2, 3]:
		route_select.add_item("%d cells" % width)
		route_select.set_item_metadata(route_select.item_count - 1, width)
	route_select.item_selected.connect(_route_selected)
	_content.add_child(_row("Route width", route_select))

	_content.add_child(_label("Terrain: select a swatch to paint"))
	mats = _list("Materials", 145, Vector2i(48, 48))
	mats.max_columns = 0
	mats.icon_mode = ItemList.ICON_MODE_TOP
	mats.item_selected.connect(_material_selected)
	mats.gui_input.connect(func(event: InputEvent) -> void: _palette_hover(event, mats, "material"))
	_content.add_child(mats)
	_content.add_child(_label("Surface variant brush (auto lets the bake choose)"))
	variants = _list("SurfaceVariants", 100, Vector2i.ZERO)
	variants.item_selected.connect(_surface_selected)
	_content.add_child(variants)

	_content.add_child(_label("Pieces: place the foot on the soft grid"))
	pieces = _list("Pieces", 240, Vector2i(40, 40))
	pieces.item_selected.connect(_piece_selected)
	pieces.gui_input.connect(func(event: InputEvent) -> void: _palette_hover(event, pieces, "piece"))
	_content.add_child(pieces)
	facing_select = OptionButton.new()
	facing_select.name = "Facing"
	for direction in ["n", "e", "s", "w"]:
		facing_select.add_item(_text(direction).to_upper())
		facing_select.set_item_metadata(facing_select.item_count - 1, direction)
	facing_select.tooltip_text = "Placement facing metadata. Sprite art is never rotated or mirrored."
	facing_select.item_selected.connect(_facing_selected)
	_content.add_child(_row("Facing", facing_select))
	piece_variant_select = OptionButton.new()
	piece_variant_select.name = "PieceVariant"
	piece_variant_select.item_selected.connect(_piece_variant_selected)
	_content.add_child(_row("Piece variant", piece_variant_select))
	stage_select = OptionButton.new()
	stage_select.name = "PieceStage"
	stage_select.item_selected.connect(_stage_selected)
	_content.add_child(_row("Stage", stage_select))

	card = RichTextLabel.new()
	card.name = "PieceCard"
	card.bbcode_enabled = true
	card.custom_minimum_size = Vector2(0, 240)
	card.size_flags_vertical = Control.SIZE_EXPAND_FILL
	card.text = "Select or hover a swatch to inspect its definition."
	_content.add_child(card)
	validate_button = Button.new()
	validate_button.text = "Validate zone"
	validate_button.pressed.connect(_validate)
	_content.add_child(validate_button)
	bake_button = Button.new()
	bake_button.text = "Bake ground (the painters)"
	bake_button.pressed.connect(_bake)
	_content.add_child(bake_button)
	status = Label.new()
	status.name = "Diagnostics"
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_content.add_child(status)
	_sync_controls()
	refresh_palette()
	if Engine.is_editor_hint():
		var fs := EditorInterface.get_resource_filesystem()
		if not fs.filesystem_changed.is_connected(refresh_palette):
			fs.filesystem_changed.connect(refresh_palette)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--we-show="):
			show_piece(argument.substr(10))

func _exit_tree() -> void:
	if Engine.is_editor_hint():
		var fs := EditorInterface.get_resource_filesystem()
		if fs.filesystem_changed.is_connected(refresh_palette):
			fs.filesystem_changed.disconnect(refresh_palette)

func _process(_delta: float) -> void:
	# Inspector edits to lab status and keyboard facing changes must not leave stale controls.
	if mats == null:
		return
	if _last_lab != _is_lab():
		refresh_palette()
	if is_instance_valid(plugin):
		var current := _text(plugin.get("facing")).to_lower()
		if current != _last_facing:
			_select_metadata(facing_select, current)
			_last_facing = current

func _label(text: String) -> Label:
	var label := Label.new()
	label.text = text
	return label

func _row(text: String, control: Control) -> HBoxContainer:
	var row := HBoxContainer.new()
	var label := _label(text)
	label.custom_minimum_size.x = 100
	row.add_child(label)
	control.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(control)
	return row

func _list(node_name: String, height: int, icon_size: Vector2i) -> ItemList:
	var list := ItemList.new()
	list.name = node_name
	list.custom_minimum_size = Vector2(0, height)
	list.fixed_icon_size = icon_size
	list.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	return list

func _is_lab() -> bool:
	return is_instance_valid(ground) and ground.lab

func _ops() -> Object:
	if not is_instance_valid(plugin):
		return null
	var value: Variant = plugin.get("operations")
	return value if value is Object else null

func _allowed(entry: Dictionary) -> bool:
	var approval: Variant = entry.get("approval", "")
	var state := _text(approval.get("state", "")) if approval is Dictionary else _text(approval)
	return state == "approved" or (_is_lab() and state in ["candidate", "gated"])

## Always rebuild: a lab palette must never survive selection of an ordinary zone.
func refresh_palette() -> void:
	if mats == null or _building:
		return
	_building = true
	if is_instance_valid(plugin) and plugin.has_method("refresh_library"):
		plugin.call("refresh_library")
	var previous := _text(plugin.get("brush")) if is_instance_valid(plugin) else ""
	mats.clear()
	pieces.clear()
	variants.clear()
	_materials.clear()
	_pieces.clear()
	_hovered_key = ""
	_last_lab = _is_lab()
	zone_label.text = "Zone: %s" % zone.name if is_instance_valid(zone) else "Select a kit zone"
	approval_label.text = "Lab: approved, candidate and gated pieces. Concepts are never placeable." if _last_lab else "Approved pieces only. Candidates and gated pieces are available in labs."
	validate_button.disabled = not is_instance_valid(zone)
	bake_button.disabled = not is_instance_valid(zone)
	var backend := _ops()
	if backend == null or not backend.has_method("catalog"):
		_clear_selection()
		say("Library unavailable: the editor operations backend is required.")
		_building = false
		return
	var result: Variant = backend.call("catalog")
	if not (result is Dictionary) or not bool(result.get("ok", false)):
		_clear_selection()
		say(_message(result, "Library unavailable; no pieces may be selected."))
		_building = false
		return
	_load_swatches()
	for entry in result.get("materials", []):
		if not (entry is Dictionary) or not _allowed(entry):
			continue
		var id := _text(entry.get("id", ""))
		if id == "":
			continue
		_materials[id] = entry
		var index := mats.add_item(_entry_label(entry), _material_swatch(entry))
		mats.set_item_metadata(index, id)
		mats.set_item_tooltip(index, _entry_label(entry))
	for entry in result.get("pieces", []):
		if not (entry is Dictionary) or not _allowed(entry):
			continue
		var id := _text(entry.get("id", ""))
		if id == "":
			continue
		_pieces[id] = entry
		var index := pieces.add_item(_entry_label(entry), _piece_swatch(entry))
		pieces.set_item_metadata(index, id)
		pieces.set_item_tooltip(index, _entry_label(entry))
	_fill_surface_variants()
	var restored := false
	if previous.begins_with("material:"):
		restored = _select_list(mats, previous.substr(9))
		if restored:
			_show_material(previous.substr(9))
	elif previous.begins_with("piece:"):
		restored = _select_list(pieces, previous.substr(6))
		if restored:
			show_piece(previous.substr(6))
	elif previous.begins_with("variant:"):
		restored = _select_list(variants, previous.substr(8))
	if not restored:
		_clear_selection()
		card.text = "Select or hover a swatch to inspect its definition."
	if mats.item_count == 0 and pieces.item_count == 0:
		say("No eligible pieces in this zone. Every current piece still awaits approval; use an explicit lab to review candidates.")
	else:
		say("%d terrain materials; %d pieces. %s" % [mats.item_count, pieces.item_count, "Lab review only." if _last_lab else "Approved library only."])
	_building = false

func _fill() -> void:
	refresh_palette()

func _entry_label(entry: Dictionary) -> String:
	var approval: Variant = entry.get("approval", "")
	var state := _text(approval.get("state", "")) if approval is Dictionary else _text(approval)
	return "%s [%s]" % [_text(entry.get("name", entry.get("id", ""))), state]

func _clear_selection() -> void:
	if is_instance_valid(plugin):
		plugin.set("brush", "")
		plugin.set("selected_variant", "")
		plugin.set("selected_stage", "")
	_shown_piece = ""
	piece_variant_select.clear()
	piece_variant_select.disabled = true
	stage_select.clear()
	stage_select.disabled = true

func _load_swatches() -> void:
	_manifest.clear()
	_palette_image = null
	if not FileAccess.file_exists(TerrainKit.MANIFEST):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(TerrainKit.MANIFEST))
	if not (parsed is Dictionary):
		return
	_manifest = parsed
	var path := TerrainKit.DIR + _text(_manifest.get("palette", "palette.png"))
	if ResourceLoader.exists(path):
		var texture := load(path) as Texture2D
		if texture != null:
			_palette_image = texture.get_image()
			if _palette_image != null and _palette_image.is_compressed():
				_palette_image.decompress()

func _material_swatch(entry: Dictionary) -> Texture2D:
	if _palette_image == null:
		return _piece_swatch(entry)
	var materials: Array = _manifest.get("materials", [])
	var cell := int(_manifest.get("cell", 24))
	for index in materials.size():
		if _text(materials[index].get("id", "")) == _text(entry.get("id", "")):
			var rect := Rect2i(index * cell, 0, cell, cell)
			if Rect2i(Vector2i.ZERO, _palette_image.get_size()).encloses(rect):
				return ImageTexture.create_from_image(_palette_image.get_region(rect))
	return null

func _piece_swatch(entry: Dictionary) -> Texture2D:
	var direct: Variant = entry.get("texture")
	if direct is Texture2D:
		return direct
	var path := _text(entry.get("png", ""))
	var built: Variant = entry.get("variants", {})
	if built is Dictionary and not built.is_empty():
		var keys: Array = built.keys()
		keys.sort()
		var first: Variant = built[keys[0]]
		if first is Dictionary:
			path = _text(first.get("png", path))
	elif built is Array and not built.is_empty() and built[0] is Dictionary:
		path = _text(built[0].get("png", path))
	if path.begins_with("res://") and ResourceLoader.exists(path):
		return load(path) as Texture2D
	return null

func _fill_surface_variants() -> void:
	if _materials.is_empty():
		return
	var index := variants.add_item("auto (the bake's choice)")
	variants.set_item_metadata(index, ".")
	var families: Dictionary = _manifest.get("surface_variants", {})
	for family in families:
		var eligible := false
		for id in _materials:
			var definition := _definition(_text(id))
			var paint: Dictionary = definition.get("terrain", {}).get("paint", {})
			var fn := _text(paint.get("fn", ""))
			if _text(id) == _text(family) or (family == "dirt" and fn in ["dirt", "path"]):
				eligible = true
		if not eligible:
			continue
		for letter in families[family]:
			var choice: Variant = families[family][letter]
			var description := _text(choice[0]) if choice is Array and not choice.is_empty() else _text(letter)
			var item := variants.add_item("%s: %s (%s)" % [family, description, letter])
			variants.set_item_metadata(item, letter)

func _select_list(list: ItemList, value: String) -> bool:
	for index in list.item_count:
		if _text(list.get_item_metadata(index)) == value:
			list.select(index)
			return true
	return false

func _select_metadata(select: OptionButton, value: String) -> void:
	for index in select.item_count:
		if _text(select.get_item_metadata(index)).to_lower() == value.to_lower():
			select.select(index)
			return

func _sync_controls() -> void:
	if not is_instance_valid(plugin):
		return
	_building = true
	var mode := _text(plugin.get("tool_mode"))
	_select_metadata(tool_select, mode)
	brush_select.value = clampi(int(plugin.get("brush_size")), 1, 3)
	_select_metadata(route_select, str(plugin.get("route_width")))
	_last_facing = _text(plugin.get("facing")).to_lower()
	_select_metadata(facing_select, _last_facing)
	brush_select.editable = mode == "brush"
	route_select.disabled = mode != "route"
	_building = false

func _tool_selected(index: int) -> void:
	if _building or not is_instance_valid(plugin):
		return
	plugin.set("tool_mode", _text(tool_select.get_item_metadata(index)))
	_sync_controls()
	_refresh_overlay()

func _brush_changed(value: float) -> void:
	if not _building and is_instance_valid(plugin):
		plugin.set("brush_size", clampi(int(value), 1, 3))
		_refresh_overlay()

func _route_selected(index: int) -> void:
	if not _building and is_instance_valid(plugin):
		plugin.set("route_width", int(route_select.get_item_metadata(index)))
		_refresh_overlay()

func _facing_selected(index: int) -> void:
	if not _building and is_instance_valid(plugin):
		plugin.set("facing", _text(facing_select.get_item_metadata(index)))
		_last_facing = _text(plugin.get("facing"))
		_refresh_overlay()

func _piece_variant_selected(index: int) -> void:
	if not _building and is_instance_valid(plugin):
		plugin.set("selected_variant", _text(piece_variant_select.get_item_metadata(index)))
		_refresh_overlay()

func _stage_selected(index: int) -> void:
	if not _building and is_instance_valid(plugin):
		plugin.set("selected_stage", _text(stage_select.get_item_metadata(index)))
		_refresh_overlay()

func _material_selected(index: int) -> void:
	if not is_instance_valid(plugin):
		return
	pieces.deselect_all()
	variants.deselect_all()
	_clear_piece_options()
	var id := _text(mats.get_item_metadata(index))
	plugin.set("brush", "material:" + id)
	_show_material(id)
	say("Terrain brush: %s" % id)
	_refresh_overlay()

func _surface_selected(index: int) -> void:
	if not is_instance_valid(plugin):
		return
	mats.deselect_all()
	pieces.deselect_all()
	_clear_piece_options()
	plugin.set("brush", "variant:" + _text(variants.get_item_metadata(index)))
	say("Surface variant brush: " + variants.get_item_text(index))
	_refresh_overlay()

func _piece_selected(index: int) -> void:
	if not is_instance_valid(plugin):
		return
	mats.deselect_all()
	variants.deselect_all()
	var id := _text(pieces.get_item_metadata(index))
	plugin.set("brush", "piece:" + id)
	show_piece(id)
	say("Piece: %s. Move over the zone to preview placement." % id)
	_refresh_overlay()

func _refresh_overlay() -> void:
	if not is_instance_valid(plugin):
		return
	if plugin.has_method("refresh_preview"):
		plugin.call("refresh_preview")
	elif plugin.has_method("update_overlays"):
		plugin.call("update_overlays")

func _clear_piece_options() -> void:
	piece_variant_select.clear()
	piece_variant_select.disabled = true
	stage_select.clear()
	stage_select.disabled = true
	_shown_piece = ""
	plugin.set("selected_variant", "")
	plugin.set("selected_stage", "")

func _definition(id: String) -> Dictionary:
	var backend := _ops()
	if backend == null or not backend.has_method("definition"):
		return {}
	var raw: Variant = backend.call("definition", id)
	return raw if raw is Dictionary else {}

func _show_material(id: String) -> void:
	_show_definition(id)

func show_piece(id: String) -> void:
	_show_definition(id)
	if is_instance_valid(plugin) and _text(plugin.get("brush")) == "piece:" + id and _pieces.has(id):
		_fill_piece_options(id)

func _show_definition(id: String) -> void:
	var definition := _definition(id)
	if definition.is_empty():
		card.text = _bb("%s: complete library definition unavailable." % id)
		return
	var text := "[b]%s[/b]\n%s · %s\n" % [_bb(definition.get("name", id)), _bb(id), _bb(definition.get("kind", ""))]
	var approval: Variant = definition.get("approval", {})
	text += "Approval: %s\n" % _bb(approval.get("state", "unknown") if approval is Dictionary else approval)
	for field in ["geometry", "terrain", "placement", "function", "story", "gameplay", "rendering"]:
		var section: Variant = definition.get(field)
		if section != null and (not (section is Dictionary) or not section.is_empty()):
			text += "\n[b]%s[/b]\n%s\n" % [_text(field).capitalize(), _bb(JSON.stringify(section, "  "))]
	card.text = text

func _fill_piece_options(id: String) -> void:
	var previous_variant := _text(plugin.get("selected_variant")) if _shown_piece == id else ""
	var previous_stage := _text(plugin.get("selected_stage")) if _shown_piece == id else ""
	_shown_piece = id
	_building = true
	piece_variant_select.clear()
	var entry: Dictionary = _pieces[id]
	var built: Variant = entry.get("variants", {})
	var ids: Array = []
	if built is Dictionary:
		ids = built.keys()
	elif built is Array:
		for variant in built:
			if variant is Dictionary:
				ids.append(_text(variant.get("id", "")))
	ids.sort()
	for variant_id in ids:
		piece_variant_select.add_item(_text(variant_id))
		piece_variant_select.set_item_metadata(piece_variant_select.item_count - 1, variant_id)
	piece_variant_select.disabled = ids.is_empty()
	if not ids.is_empty():
		_select_metadata(piece_variant_select, previous_variant)
		plugin.set("selected_variant", _text(piece_variant_select.get_item_metadata(piece_variant_select.selected)))
	else:
		plugin.set("selected_variant", "")
	stage_select.clear()
	stage_select.add_item("Default stage")
	stage_select.set_item_metadata(0, "")
	var definition := _definition(id)
	for stage in definition.get("placement", {}).get("stages", []):
		stage_select.add_item(_text(stage))
		stage_select.set_item_metadata(stage_select.item_count - 1, stage)
	stage_select.disabled = stage_select.item_count <= 1
	_select_metadata(stage_select, previous_stage)
	plugin.set("selected_stage", _text(stage_select.get_item_metadata(stage_select.selected)))
	_building = false

func _palette_hover(event: InputEvent, list: ItemList, kind: String) -> void:
	if not event is InputEventMouseMotion:
		return
	var index := list.get_item_at_position(event.position, true)
	if index < 0:
		return
	var id := _text(list.get_item_metadata(index))
	var key := kind + ":" + id
	if key != _hovered_key:
		_hovered_key = key
		_show_definition(id)

func set_zone(z: Node, g: TerrainGround) -> void:
	zone = z
	ground = g
	if mats != null:
		refresh_palette()

func say(text: String) -> void:
	if status != null:
		status.text = text

func hover(cell: Vector2i, local: Vector2) -> void:
	if not is_instance_valid(ground):
		return
	var material_id := ground.material_at(cell)
	var material: Dictionary = ground.kit.by_material.get(material_id, {})
	var text := "Cell %s: %s" % [cell, _text(material.get("id", "empty"))]
	if is_instance_valid(plugin) and _text(plugin.get("brush")).begins_with("piece:"):
		var id := _text(plugin.get("brush")).substr(6)
		var result := _preview(id, local)
		text += "\n" + _message(result, "Placement preview unavailable; placement is refused.")
	say(text)

func _preview(id: String, at: Vector2) -> Dictionary:
	if not is_instance_valid(plugin) or not plugin.has_method("preview_piece"):
		return {"ok": false, "message": "Relation engine unavailable; placement is refused."}
	var result: Variant = plugin.call("preview_piece", id, at)
	return result if result is Dictionary else {"ok": false, "message": "Invalid placement verdict; placement is refused."}

## Compatibility adapter for callers that still ask for a refusal string.
func refusal(id: String, at: Vector2) -> String:
	var result := _preview(id, at)
	return "" if bool(result.get("ok", false)) else _message(result, "Placement refused.")

func _message(result: Variant, fallback: String) -> String:
	if not result is Dictionary:
		return fallback
	var lines: PackedStringArray = []
	for diagnostic in result.get("diagnostics", []):
		if diagnostic is Dictionary:
			var rule := _text(diagnostic.get("rule", diagnostic.get("code", "")))
			var detail := _text(diagnostic.get("message", ""))
			if detail != "":
				lines.append((rule + ": " if rule != "" else "") + detail)
		elif str(diagnostic) != "":
			lines.append(str(diagnostic))
	if not lines.is_empty():
		return "\n".join(lines)
	var message := _text(result.get("message", ""))
	if message != "":
		return message
	return "Ready: placement checks pass." if bool(result.get("ok", false)) else fallback

func _bake() -> void:
	if not is_instance_valid(zone):
		say("Select a kit zone first.")
		return
	if not is_instance_valid(plugin) or not plugin.has_method("bake_zone"):
		say("Bake unavailable: the editor backend is required.")
		return
	bake_button.disabled = true
	say("Bake: save, export and render the selected zone.")
	var result: Variant = plugin.call("bake_zone")
	if result is Dictionary and bool(result.get("ok", false)) and _text(result.get("message", "")) == "":
		result = result.duplicate(true)
		result["message"] = "Bake completed."
	say(_message(result, "Bake failed; no output was accepted."))
	bake_button.disabled = not is_instance_valid(zone)

func _validate() -> void:
	if not is_instance_valid(zone):
		say("Select a kit zone first.")
		return
	if not is_instance_valid(plugin) or not plugin.has_method("validate_zone"):
		say("Validation unavailable: the complete validator backend is required.")
		return
	var result: Variant = plugin.call("validate_zone")
	if result is Dictionary and bool(result.get("ok", false)) and _text(result.get("message", "")) == "":
		result = result.duplicate(true)
		result["message"] = "Validation passed."
	say(_message(result, "Validation failed; no verdict was returned."))

static func _text(value: Variant) -> String:
	return "" if value == null else str(value)

static func _bb(value: Variant) -> String:
	var escaped := ""
	for character in str(value):
		if character == "[":
			escaped += "[lb]"
		elif character == "]":
			escaped += "[rb]"
		else:
			escaped += character
	return escaped
