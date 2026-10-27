@tool
class_name KitRelations
extends RefCounted
## Pure placement checks shared with scripts/art/kit/relations.py.
## Source piece JSON supplies placement intent; the generated prop index is not authoritative.
## Feet use texels by default, or explicit coordinate_space="cells". Absent footprints
## use the foot cell, never a sprite-sized guess. Facing does not rotate authored geometry.
## Negative predicates are prohibitions in either list (existing forbids:not_overlap rocks).
## These engineering semantics need Claude's authored design cases; approvals stay separate.
## Under terrain means its full northern boundary is fed by that terrain; under a
## piece or role means an authored overhang covers it. No piece IDs select semantics.

const CELL := 24.0
const EPS := 0.0000001

static func _registry_at(path: String, out: Dictionary) -> void:
	var dir := DirAccess.open(path)
	if dir == null:
		return
	var children := Array(dir.get_directories())
	children.sort()
	for name_ in children:
		_registry_at(path.path_join(name_), out)
	var files := Array(dir.get_files())
	files.sort()
	for name_ in files:
		if not name_.ends_with(".json"):
			continue
		var value = JSON.parse_string(FileAccess.get_file_as_string(path.path_join(name_)))
		if value is Dictionary and value.has("id"):
			out[value.id] = value

static func default_library() -> Dictionary:
	var result := {}
	_registry_at("res://kit/pieces", result)
	return result

static func default_materials() -> Dictionary:
	var result := {}
	var value = JSON.parse_string(FileAccess.get_file_as_string("res://kit/terrain/manifest.json"))
	if value is Dictionary:
		for entry in value.get("materials", []):
			result[entry.id] = entry
	return result

const RELATIONS := ["adjacent", "within", "on", "facing", "near", "under", "at_edge", "at_corner", "on_anchor", "not_on", "not_near", "not_overlap"]
const NEGATIVE := ["not_on", "not_near", "not_overlap"]
const VOCABULARY := ["route", "route_edge", "water", "face", "tier_edge", "zone_edge"]
const DIRECTIONS := {"s": Vector2i(0, 1), "n": Vector2i(0, -1), "e": Vector2i(1, 0), "w": Vector2i(-1, 0)}

static func _text(value: Variant) -> String:
	if value == null:
		return "None"
	if value is bool:
		return "True" if value else "False"
	return str(value)

static func _truth(value: Variant) -> bool:
	if value == null:
		return false
	if value is Dictionary or value is Array or value is String:
		return not value.is_empty()
	return bool(value)

static func _material_spec(value: Dictionary) -> Dictionary:
	return value.get("terrain", value)

static func _number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))

static func _contains_number(values: Array, value: int) -> bool:
	# JSON numbers are floats in Godot. Array.has compares their Variant types,
	# while the schema's integer-valued tier list means numeric equality.
	for item in values:
		if _number(item) and float(item) == float(value):
			return true
	return false

static func _same(left: Variant, right: Variant) -> bool:
	if _number(left) and _number(right):
		return float(left) == float(right)
	return left == right if typeof(left) == typeof(right) else false

static func _position(entry: Dictionary, plan: Dictionary) -> Variant:
	var at = entry.get("at")
	if not at is Array or at.size() != 2 or not _number(at[0]) or not _number(at[1]):
		return null
	var scale := 1.0 if plan.get("coordinate_space", "texels") == "cells" else CELL
	return Vector2(float(at[0]) / scale, float(at[1]) / scale)

static func _foot(position: Vector2) -> Vector2i:
	return Vector2i(floori(position.x), floori(position.y - EPS))

static func _occupied(entry: Dictionary, piece: Dictionary, plan: Dictionary, overhang := false) -> Dictionary:
	var position = _position(entry, plan)
	if position == null:
		return {}
	var geometry: Dictionary = piece.get("geometry", {}) if piece.get("geometry") != null else {}
	var offsets = geometry.get("overhang" if overhang else "footprint")
	if not _truth(offsets) and overhang:
		offsets = geometry.get("footprint")
	if not _truth(offsets):
		return {_foot(position): true}
	var origin := Vector2i(floori(position.x), floori(position.y))
	var cells := {}
	for offset in offsets:
		cells[origin + Vector2i(int(offset[0]), int(offset[1]))] = true
	return cells

static func _context(plan: Dictionary, materials: Dictionary) -> Variant:
	var rows = plan.get("rows")
	var legend = plan.get("legend")
	if not rows is Array or rows.is_empty() or not legend is Dictionary:
		return null
	for glyph in legend:
		if not glyph is String or glyph.length() != 1 or not legend[glyph] is String:
			return null
	for row in rows:
		if not row is String:
			return null
		for glyph in row:
			if glyph != " " and not legend.has(glyph):
				return null
	var width: int = rows[0].length()
	if width == 0:
		return null
	for row in rows:
		if row.length() != width:
			return null
	var tier_rows = plan.get("tiers")
	if not plan.has("tiers"):
		tier_rows = []
		for row in rows:
			tier_rows.append("0".repeat(width))
	if not tier_rows is Array or tier_rows.size() != rows.size():
		return null
	for row in tier_rows:
		if not row is String or row.length() != width:
			return null
		for ch in row:
			if ch not in "0123456789":
				return null
	var anchors = plan.get("anchors", [])
	if not anchors is Array:
		return null
	for anchor in anchors:
		if not anchor is Dictionary or _position(anchor, plan) == null:
			return null
		if (anchor.has("id") and not anchor.id is String) or (anchor.has("kind") and not anchor.kind is String):
			return null
	var grid := {}
	var tiers := {}
	for y in rows.size():
		for x in width:
			grid[Vector2i(x, y)] = legend.get(rows[y][x], "")
			tiers[Vector2i(x, y)] = int(tier_rows[y][x])
	var faces := []
	for key in materials:
		if _truth(_material_spec(materials[key]).get("face")):
			faces.append(key)
	faces.sort()
	if not faces.is_empty():
		var face_id: String = faces[0]
		var height := int(_material_spec(materials[face_id]).face.get("height_cells", 2))
		for y in range(rows.size() - 1):
			for x in width:
				var delta: int = tiers[Vector2i(x, y)] - tiers[Vector2i(x, y + 1)]
				for step in range(1, maxi(0, height * delta) + 1):
					if y + step < rows.size() and tiers[Vector2i(x, y + step)] < tiers[Vector2i(x, y)]:
						grid[Vector2i(x, y + step)] = face_id
	return {"grid": grid, "tiers": tiers, "width": width, "height": rows.size()}

static func _tokens(raw: String) -> Array:
	var split := raw.find(":")
	return [raw.substr(0, split), raw.substr(split + 1)] if split >= 0 else ["", raw]

static func _known(what: String, library: Dictionary, materials: Dictionary, plan: Dictionary) -> bool:
	var token := _tokens(what)
	var prefix: String = token[0]
	var name_: String = token[1]
	var roles := {}
	var surfaces := {}
	var anchors := {}
	for piece in library.values():
		roles[piece.get("placement", {}).get("role")] = true
	for material in materials.values():
		surfaces[_material_spec(material).get("surface")] = true
	for anchor in plan.get("anchors", []):
		if anchor is Dictionary:
			for anchor_key in [anchor.get("kind"), anchor.get("id")]:
				if anchor_key != null:
					anchors[anchor_key] = true
	match prefix:
		"piece": return library.has(name_)
		"role": return roles.has(name_)
		"material": return materials.has(name_)
		"surface": return surfaces.has(name_)
		"anchor": return anchors.has(name_)
		"": return name_ in VOCABULARY or library.has(name_) or roles.has(name_) or materials.has(name_) or surfaces.has(name_) or anchors.has(name_)
	return false

static func _matches_material(what: String, id: String, materials: Dictionary) -> bool:
	var material := _material_spec(materials.get(id, {}))
	if what.begins_with("material:"):
		return id == what.substr(9)
	if what.begins_with("surface:"):
		return material.get("surface") == what.substr(8)
	if ":" in what:
		return false
	match what:
		"route": return _truth(material.get("route"))
		"water": return material.get("water") != null or material.get("surface") == "water"
		"face": return _truth(material.get("face"))
	return id == what or material.get("surface") == what

static func _matches_piece(what: String, piece_id: Variant, piece: Dictionary) -> bool:
	var role = piece.get("placement", {}).get("role")
	if what.begins_with("piece:"):
		return piece_id == what.substr(6)
	if what.begins_with("role:"):
		return role == what.substr(5)
	return ":" not in what and (piece_id == what or role == what)

static func _known_ground(what: Variant, materials: Dictionary) -> bool:
	if not what is String:
		return false
	if what in ["route", "water", "face"]:
		return true
	if what.begins_with("material:"):
		return materials.has(what.substr(9))
	if what.begins_with("surface:"):
		for m in materials.values():
			if _material_spec(m).get("surface") == what.substr(8):
				return true
		return false
	if ":" in what:
		return false
	if materials.has(what):
		return true
	for m in materials.values():
		if _material_spec(m).get("surface") == what:
			return true
	return false

static func _targets(what: String, plan: Dictionary, library: Dictionary, materials: Dictionary, context: Dictionary, index: int, under := false) -> Dictionary:
	var grid: Dictionary = context.grid
	var tiers: Dictionary = context.tiers
	var cells := {}
	if what == "route_edge":
		var route := {}
		for c in grid:
			if _matches_material("route", grid[c], materials):
				route[c] = true
		for c in route:
			for direction in DIRECTIONS.values():
				if not route.has(c + direction):
					cells[c] = true
					break
	elif what == "tier_edge":
		for c in tiers:
			for direction in DIRECTIONS.values():
				if tiers.get(c + direction, tiers[c]) != tiers[c]:
					cells[c] = true
					break
	elif what == "zone_edge":
		for c in grid:
			if c.x in [0, context.width - 1] or c.y in [0, context.height - 1]:
				cells[c] = true
	else:
		for c in grid:
			if _matches_material(what, grid[c], materials):
				cells[c] = true
	if under and _known_ground(what, materials):
		return cells
	var entries: Array = plan.get("pieces", [])
	for other_index in entries.size():
		if other_index == index or not entries[other_index] is Dictionary:
			continue
		var entry: Dictionary = entries[other_index]
		if not entry.get("piece") is String:
			continue
		var piece: Dictionary = library.get(entry.get("piece"), {})
		if _matches_piece(what, entry.get("piece"), piece):
			cells.merge(_occupied(entry, piece, plan, under))
	for anchor in plan.get("anchors", []):
		if not anchor is Dictionary:
			continue
		var name_ := what.substr(7) if what.begins_with("anchor:") else what
		if name_ in [anchor.get("kind"), anchor.get("id")]:
			var position = _position(anchor, plan)
			if position != null:
				cells[_foot(position)] = true
	return cells

static func _intersects(a: Dictionary, b: Dictionary) -> bool:
	for cell in a:
		if b.has(cell):
			return true
	return false

static func _distance(a: Dictionary, b: Dictionary) -> float:
	var result := INF
	for left in a:
		for right in b:
			result = minf(result, maxf(absf(left.x - right.x), absf(left.y - right.y)))
	return result

static func _in_front(position: Vector2, targets: Dictionary, facing: String) -> bool:
	var direction: Vector2i = DIRECTIONS.get(facing, Vector2i.ZERO)
	for cell in targets:
		var delta := Vector2(cell) + Vector2(0.5, 0.5) - position
		var dot := delta.x * direction.x + delta.y * direction.y
		var cross := delta.x * direction.y - delta.y * direction.x
		if dot > EPS and absf(cross) <= dot + EPS:
			return true
	return false

static func _predicate(relation: Dictionary, entry: Dictionary, occupied: Dictionary, targets: Dictionary, plan: Dictionary, terrain_under := false) -> bool:
	var rel: String = relation.rel
	if rel == "facing" or _truth(relation.get("facing", false)):
		var visible := {}
		for c in targets:
			if _in_front(_position(entry, plan), {c: true}, _text(entry.get("facing", "s")).to_lower()):
				visible[c] = true
		targets = visible
	var distance := _distance(occupied, targets)
	var radius := float(relation.get("cells", 1))
	var result := false
	if rel == "under" and terrain_under:
		var top := 0
		if not occupied.is_empty():
			top = occupied.keys()[0].y
			for cell in occupied:
				top = mini(top, cell.y)
		top -= 1
		var north := {}
		for cell in occupied:
			north[Vector2i(cell.x, top)] = true
		result = not north.is_empty()
		for cell in north:
			if not targets.has(cell):
				result = false
	elif rel in ["on", "under", "on_anchor"]:
		result = _intersects(occupied, targets)
	elif rel in ["not_on", "not_overlap"]:
		result = not _intersects(occupied, targets)
	elif rel in ["within", "near"]:
		result = distance <= radius + EPS
	elif rel == "not_near":
		result = distance > radius + EPS
	elif rel == "adjacent":
		result = EPS < distance and distance <= radius + EPS
	elif rel in ["at_edge", "at_corner"]:
		var directions := {}
		for cell in occupied:
			for direction in DIRECTIONS.values():
				for step in range(1, floori(radius + EPS) + 1):
					if targets.has(cell + direction * step):
						directions[direction] = true
		result = not _intersects(occupied, targets) and not directions.is_empty()
		if rel == "at_corner":
			var corner := false
			for a in directions:
				for b in directions:
					if a.x * b.x + a.y * b.y == 0:
						corner = true
			result = result and corner
	elif rel == "facing":
		result = not targets.is_empty() and (distance <= radius + EPS if relation.has("cells") else true)
	else:
		return false
	return result

static func _finding(check: String, message: String, at: Variant) -> Dictionary:
	return {"check": check, "message": message, "at": at.duplicate(true) if at is Array or at is Dictionary else at}

static func check_zone(plan: Variant, library: Variant = null, materials: Variant = null) -> Array:
	library = default_library() if library == null else library
	materials = default_materials() if materials == null else materials
	if not plan is Dictionary:
		return [_finding("rules.plan", "zone: invalid plan", [])]
	if plan.get("coordinate_space", "texels") not in ["texels", "cells"]:
		return [_finding("rules.plan", "zone: unknown coordinate space", [])]
	var context = _context(plan, materials)
	if context == null or not plan.get("pieces", []) is Array:
		return [_finding("rules.plan", "zone: invalid cells or tiers", [])]
	var grid: Dictionary = context.grid
	var tiers: Dictionary = context.tiers
	var unknown := {}
	for id in grid.values():
		if _truth(id) and not materials.has(id):
			unknown[id] = true
	if not unknown.is_empty():
		var ids := unknown.keys()
		ids.sort()
		var findings := []
		for id in ids:
			findings.append(_finding("rules.unknown_piece", id + ": material is not in the library", []))
		return findings
	var out := []
	var entries: Array = plan.get("pieces", [])
	for index in entries.size():
		if not entries[index] is Dictionary:
			out.append(_finding("rules.plan", "zone: invalid piece instance", []))
			continue
		var entry: Dictionary = entries[index]
		var pid = entry.get("piece")
		var eid := _text(entry.get("id", pid))
		var at = entry.get("at", [])
		if not pid is String or (entry.has("id") and not entry.id is String):
			out.append(_finding("rules.plan", "zone: invalid piece id", at))
			continue
		var piece = library.get(pid)
		if piece == null:
			out.append(_finding("rules.unknown_piece", eid + ": piece is not in the library", at))
			continue
		var position = _position(entry, plan)
		if position == null:
			out.append(_finding("rules.position", eid + ": invalid foot position", at))
			continue
		var occupied := _occupied(entry, piece, plan)
		var placement: Dictionary = piece.get("placement", {}) if piece.get("placement") != null else {}
		for cell in occupied:
			if cell.x < 0 or cell.y < 0 or cell.x >= context.width or cell.y >= context.height:
				out.append(_finding("rules.bounds", eid + ": footprint is outside the zone", at))
				break
		var snap: String = placement.get("snap", "free")
		var step := Vector2(0.5, 1.0) if snap == "cell" else Vector2(0.5, 0.5)
		if snap not in ["cell", "half", "free"] or (snap != "free" and (absf(position.x / step.x - roundf(position.x / step.x)) > EPS or absf(position.y / step.y - roundf(position.y / step.y)) > EPS)):
			out.append(_finding("rules.off_grid", eid + ": foot is off the soft grid", at))
		var facing := _text(entry.get("facing", "s")).to_lower()
		var orientations: Array = placement.get("orientations", [])
		if not DIRECTIONS.has(facing) or (not orientations.is_empty() and "any" not in orientations and facing not in orientations):
			out.append(_finding("rules.orientation", eid + ": orientation is not allowed", at))
		var stage = entry.get("stage", plan.get("stage", ""))
		if _truth(placement.get("stages")) and stage not in placement.stages:
			out.append(_finding("rules.stage", eid + ": stage is not allowed", at))
		var here := {}
		for cell in occupied:
			here[grid.get(cell, "")] = true
		var allowed: Array = placement.get("ground", {}).get("allow", [])
		var denied: Array = placement.get("ground", {}).get("deny", [])
		var unknown_ground := []
		for target in allowed + denied:
			if not _known_ground(target, materials) and target not in unknown_ground:
				unknown_ground.append(target)
				out.append(_finding("rules.ground", eid + ": unknown ground target " + _text(target), at))
		var bad_ground := false
		var denied_ground := false
		if unknown_ground.is_empty():
			for mid in here:
				var matches := false
				for target in allowed:
					matches = matches or _matches_material(target, mid, materials)
				if not allowed.is_empty() and not matches:
					bad_ground = true
				for target in denied:
					denied_ground = denied_ground or _matches_material(target, mid, materials)
		if bad_ground:
			out.append(_finding("rules.ground", eid + ": ground is not allowed", at))
		if denied_ground:
			out.append(_finding("rules.ground", eid + ": ground is denied", at))
		if _truth(placement.get("tiers")):
			for cell in occupied:
				if not _contains_number(placement.tiers, int(tiers.get(cell, -1))):
					out.append(_finding("rules.tiers", eid + ": tier is not allowed", at))
					break
		for field in ["requires", "forbids"]:
			for relation in placement.get(field, []):
				var rel = relation.get("rel", "")
				var what = relation.get("what", "")
				if rel not in RELATIONS or not what is String or not _known(what, library, materials, plan) or not _number(relation.get("cells", 1)) or float(relation.get("cells", 1)) < 0:
					out.append(_finding("rules.relation", "%s: unknown relation or target %s %s" % [eid, _text(rel), _text(what)], at))
					continue
				var targets := _targets(what, plan, library, materials, context, index, rel == "under")
				var verdict := _predicate(relation, entry, occupied, targets, plan, rel == "under" and _known_ground(what, materials))
				var violation := not verdict if field == "requires" or rel in NEGATIVE else verdict
				if violation:
					var check: String = "rules.seating" if placement.get("role") == "seat" and what in ["route", "route_edge"] else "rules." + field
					var verb: String = "violates" if field == "forbids" and rel in NEGATIVE else field
					var message := "%s: %s %s %s" % [eid, verb, rel, what]
					if _truth(relation.get("note")):
						message += ": " + relation.note
					out.append(_finding(check, message, at))
		var clearance = placement.get("clearance", 0)
		if _number(clearance) and clearance > 0:
			for other_index in entries.size():
				if other_index == index or not entries[other_index] is Dictionary:
					continue
				var other: Dictionary = entries[other_index]
				if not other.get("piece") is String:
					continue
				var other_piece = library.get(other.get("piece"))
				if other_piece != null and _distance(occupied, _occupied(other, other_piece, plan)) <= clearance + EPS:
					var other_id := _text(other.get("id", other.get("piece")))
					out.append(_finding("rules.clearance", eid + ": clearance overlaps " + other_id, at))
	var pids: Array = library.keys()
	pids.sort()
	for pid in pids:
		var limits: Dictionary = library[pid].get("placement", {}).get("per_zone", {})
		var count := 0
		for entry in entries:
			if entry is Dictionary and _same(entry.get("piece"), pid):
				count += 1
		if limits.has("min") and count < limits.min:
			out.append(_finding("rules.count", pid + ": fewer than per-zone minimum", []))
		if limits.has("max") and count > limits.max:
			out.append(_finding("rules.count", pid + ": exceeds per-zone maximum", []))
	return out

static func check_placement(plan: Dictionary, candidate: Dictionary, library: Variant = null, materials: Variant = null) -> Array:
	var previous := check_zone(plan, library, materials)
	var trial := plan.duplicate(true)
	var entries: Array = trial.get("pieces", [])
	if candidate.has("id"):
		entries = entries.filter(func(entry: Variant) -> bool: return not entry is Dictionary or not _same(entry.get("id"), candidate.id))
	entries.append(candidate.duplicate(true))
	trial["pieces"] = entries
	var after := check_zone(trial, library, materials)
	var eid := _text(candidate.get("id", candidate.get("piece")))
	var pid = candidate.get("piece")
	var old_count := 0
	var new_count := 0
	for entry in plan.get("pieces", []):
		if entry is Dictionary and _same(entry.get("piece"), pid):
			old_count += 1
	for entry in entries:
		if entry is Dictionary and _same(entry.get("piece"), pid):
			new_count += 1
	var out := []
	for finding in after:
		if finding.check == "rules.count" and finding.message.ends_with(": fewer than per-zone minimum"):
			continue
		var local: bool = finding.message.begins_with(eid + ": ") and finding.at == candidate.get("at", [])
		var structural: bool = finding.check == "rules.plan" or (finding.check == "rules.unknown_piece" and not _truth(finding.at))
		var worsening_count: bool = finding.check == "rules.count" and finding.message == _text(pid) + ": exceeds per-zone maximum" and new_count > old_count
		if local or structural or worsening_count or finding not in previous:
			out.append(finding)
	return out

static func evaluate(plan: Dictionary, candidate: Dictionary, library: Variant = null, materials: Variant = null) -> Array:
	return check_placement(plan, candidate, library, materials)
