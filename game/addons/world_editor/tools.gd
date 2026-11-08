@tool
class_name WorldEditorTools
extends RefCounted
## Cell geometry for authoring. This never rotates/mirrors art or changes a piece's rules.

const FACINGS := ["s", "w", "n", "e"]
const ROUTE_SIMPLIFY_DISTANCE := 0.75
## Palette groups, by what a piece is for in a place (round 3, 3 Nov).
const CATEGORIES := ["all", "fences", "farm", "commons", "village", "woodland", "water"]
const SIDES := {"n": Vector2i(0, -1), "e": Vector2i(1, 0), "s": Vector2i(0, 1), "w": Vector2i(-1, 0)}
const OPPOSITE := {"n": "s", "e": "w", "s": "n", "w": "e"}

static func snap(local: Vector2, how: String, cell: int = 24) -> Vector2:
	if cell <= 0:
		return local
	var half := float(cell) / 2.0
	match how:
		"cell":
			# Props stand on half-cell x positions and full-cell ground lines.
			return Vector2(snappedf(local.x, half), snappedf(local.y, float(cell)))
		"half":
			return Vector2(snappedf(local.x, half), snappedf(local.y, half))
		"pixel":
			return local.round()
		_:
			# Schema "free", UI "none" and unknown modes preserve free placement.
			return local

static func next_facing(facing: String, delta: int = 1) -> String:
	var index := FACINGS.find(facing.to_lower())
	return FACINGS[posmod(maxi(index, 0) + delta, FACINGS.size())]

static func brush_cells(center: Vector2i, width: int) -> Array[Vector2i]:
	var size := clampi(width, 1, 3)
	# A two-cell brush covers centre and centre+1; it has no pointer-direction bias.
	var low := center - Vector2i.ONE * floori(float(size - 1) / 2.0)
	return rectangle_cells(low, low + Vector2i.ONE * (size - 1))

static func rectangle_cells(a: Vector2i, b: Vector2i) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	for y in range(mini(a.y, b.y), maxi(a.y, b.y) + 1):
		for x in range(mini(a.x, b.x), maxi(a.x, b.x) + 1):
			result.append(Vector2i(x, y))
	return result

static func line_cells(a: Vector2i, b: Vector2i) -> Array[Vector2i]:
	# Traverse grid crossings, keeping a four-connected stroke even across pointer jumps.
	# Canonical endpoint ordering makes tie choices identical when a stroke is reversed.
	var backwards := _before(b, a)
	var first := b if backwards else a
	var last := a if backwards else b
	var result: Array[Vector2i] = [first]
	var at := first
	var nx := absi(last.x - first.x)
	var ny := absi(last.y - first.y)
	var sx := signi(last.x - first.x)
	var sy := signi(last.y - first.y)
	var ix := 0
	var iy := 0
	while ix < nx or iy < ny:
		if iy == ny or (ix < nx and (1 + 2 * ix) * ny <= (1 + 2 * iy) * nx):
			at.x += sx
			ix += 1
		else:
			at.y += sy
			iy += 1
		result.append(at)
	if backwards:
		result.reverse()
	return result

static func route_cells(points: Array, width: int) -> Array[Vector2i]:
	var path := _cardinal_path(_simplify(points))
	var result: Array[Vector2i] = []
	if path.is_empty():
		return result
	var size := clampi(width, 2, 3)
	var shift := Vector2.ONE * (0.5 if size % 2 == 0 else 0.0)
	var radius := float(size) / 2.0
	var chosen: Dictionary = {}
	# Rasterise a union of rounded capsules. The terrain dual-grid renderer rounds the
	# displayed boundary; these cells define only the route's authored footprint.
	for i in maxi(1, path.size() - 1):
		var a := Vector2(path[i]) + shift
		var b := Vector2(path[mini(i + 1, path.size() - 1)]) + shift
		for cell in rectangle_cells(Vector2i((a.min(b) - Vector2.ONE * radius).floor()), Vector2i((a.max(b) + Vector2.ONE * radius).ceil())):
			if _distance_squared(Vector2(cell), a, b) < radius * radius:
				chosen[cell] = true
	result.assign(chosen.keys())
	result.sort_custom(func(a: Vector2i, b: Vector2i) -> bool: return a.y < b.y or (a.y == b.y and a.x < b.x))
	return result

static func _simplify(values: Array) -> Array[Vector2i]:
	var points: Array[Vector2i] = []
	for value in values:
		if value is not Vector2i and value is not Vector2:
			continue
		var p := Vector2i(value)
		if points.is_empty() or points.back() != p:
			points.append(p)
	# Resolve sampling ties in the same direction for a reversed stroke, including loops.
	for i in floori(float(points.size()) / 2.0):
		var mirrored := points.size() - 1 - i
		if points[i] != points[mirrored]:
			if _before(points[mirrored], points[i]):
				points.reverse()
			break
	if points.size() < 3:
		return points
	# Remove pointer-sampling staircases without erasing deliberate longer bends.
	var retained: Dictionary = {0: true, points.size() - 1: true}
	var spans: Array[Vector2i] = [Vector2i(0, points.size() - 1)]
	while not spans.is_empty():
		var span: Vector2i = spans.pop_back()
		var furthest := -1
		var distance := ROUTE_SIMPLIFY_DISTANCE * ROUTE_SIMPLIFY_DISTANCE
		for i in range(span.x + 1, span.y):
			var d := _distance_squared(Vector2(points[i]), Vector2(points[span.x]), Vector2(points[span.y]))
			if d > distance:
				distance = d
				furthest = i
		if furthest >= 0:
			retained[furthest] = true
			spans.append(Vector2i(span.x, furthest))
			spans.append(Vector2i(furthest, span.y))
	var result: Array[Vector2i] = []
	for i in points.size():
		if retained.has(i):
			result.append(points[i])
	return result

static func _cardinal_path(points: Array[Vector2i]) -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	for point in points:
		if not result.is_empty():
			var previous: Vector2i = result.back()
			if previous.x != point.x and previous.y != point.y:
				# A slant becomes long cardinal runs, never a one-cell diagonal staircase.
				# Use the same elbow for either traversal direction.
				var first: Vector2i = point if _before(point, previous) else previous
				var last: Vector2i = previous if _before(point, previous) else point
				result.append(Vector2i(last.x, first.y) if absi(last.x - first.x) >= absi(last.y - first.y) else Vector2i(first.x, last.y))
		result.append(point)
	return result

static func _distance_squared(point: Vector2, a: Vector2, b: Vector2) -> float:
	var span := b - a
	var t := clampf((point - a).dot(span) / span.length_squared(), 0.0, 1.0) if not span.is_zero_approx() else 0.0
	return point.distance_squared_to(a + span * t)

static func _before(a: Vector2i, b: Vector2i) -> bool:
	return a.x < b.x or (a.x == b.x and a.y < b.y)

## The palette group of a piece: fences (anything with a placement.boundary), the farmyard, the
## village commons, the rest of the village, the woods and the water's pieces.
static func piece_category(id: String, definition: Dictionary) -> String:
	var placement: Variant = definition.get("placement", {})
	if (placement is Dictionary and placement.has("boundary")) or id.begins_with("fence_"):
		return "fences"
	if id.begins_with("farm_") or id.begins_with("garden_"):
		return "farm"
	if id.begins_with("commons_"):
		return "commons"
	if id.begins_with("waterfall") or id.begins_with("footbridge") or id.begins_with("stepping_stones"):
		return "water"
	if id.begins_with("woodland_") or id.begins_with("log_steps"):
		return "woodland"
	return "village"

## Whether a palette entry shows under a category and a search: every word of the query must
## appear in its id, name, role or purpose.
static func palette_matches(id: String, name: String, definition: Dictionary, query: String, category: String) -> bool:
	if category != "" and category != "all" and piece_category(id, definition) != category:
		return false
	var words := query.strip_edges().to_lower().split(" ", false)
	if words.is_empty():
		return true
	var placement: Variant = definition.get("placement", {})
	var role := String(placement.get("role", "")) if placement is Dictionary else ""
	var purpose := String(placement.get("purpose", "")) if placement is Dictionary else ""
	var haystack := " ".join([id, name, role, purpose]).to_lower()
	for word in words:
		if not haystack.contains(word):
			return false
	return true

## The soft-grid cell a fence piece stands in: its foot is the middle of the cell's south line.
static func fence_cell(foot: Vector2, cell: int = 24) -> Vector2i:
	return Vector2i(floori(foot.x / cell), roundi(foot.y / cell) - 1)

## A fence cell piece's foot.
static func fence_foot(at: Vector2i, cell: int = 24) -> Vector2:
	return Vector2(at.x * cell + cell / 2.0, (at.y + 1) * cell)

## The cells a gate spans (three along its run) and the sides its ends join, as {cell: [sides]}.
static func gate_ends(foot_cell: Vector2i, joins: Array) -> Dictionary:
	if "e" in joins or "w" in joins:
		return {foot_cell + Vector2i(-1, 0): ["w"], foot_cell: [], foot_cell + Vector2i(1, 0): ["e"]}
	return {foot_cell + Vector2i(0, -1): ["n"], foot_cell: [], foot_cell + Vector2i(0, 1): ["s"]}

## The fence piece every cell of a run needs, chosen by its neighbours: each cell joins every side
## where another fence cell lies (a gate's cell only on the side its end opens). `fixed` holds the
## cells pieces already decide (gates): {cell: [sides it joins]}. A cell with no neighbour gets "".
static func fence_pieces(style: String, cells: Array, fixed: Dictionary = {}) -> Dictionary:
	var taken := {}
	for c in cells:
		taken[Vector2i(c)] = true
	var out := {}
	for c in cells:
		var at := Vector2i(c)
		if fixed.has(at):
			continue
		var joins := ""
		for side in ["n", "e", "s", "w"]:
			var next: Vector2i = at + SIDES[side]
			if fixed.has(next):
				if OPPOSITE[side] in fixed[next]:
					joins += side
			elif taken.has(next):
				joins += side
		out[at] = "fence_%s_%s" % [style, joins] if joins != "" else ""
	return out

## A stable value in [0, 1) for a cell (the scatter brush's per-cell seed): the same cell and seed
## always give the same choice, so a stroke repainted after an undo lands the same pieces.
static func cell_hash(cell: Vector2i, seed: int, salt: int = 0) -> float:
	var v := sin(float(cell.x) * 12.9898 + float(cell.y) * 78.233 + float(seed) * 37.719 + float(salt) * 4.581) * 43758.5453
	return v - floor(v)

## The next variant in a piece's list after the current one (the variant cycle).
static func next_variant(variants: Array, current: String) -> String:
	if variants.is_empty():
		return ""
	var i := variants.find(current)
	return String(variants[(i + 1) % variants.size()])

## The short name of a finding's rule, for the live overlay's label.
static func short_rule(check: String) -> String:
	return check.trim_prefix("rules.").replace("_", " ")

## Door paths (Matt, 4 Nov; scripts/art/kit/thresholds.py rules.door_path): a route stroke that
## reaches the row before a door snaps to the door's centre line. The stroke's cells in the two rows
## before the door (within a cell of its opening) become a run centred on the opening, as wide as the
## stroke was there (one wider when the door's centre needs the other parity: a cell's centre takes
## an odd run, a cell's edge an even one), so the path leaves the door centred and straight for a
## cell. `door` holds the opening's x0, x1 and the door's foot y (ground texels). A stroke that does
## not touch the door's own row is left as it is.
static func door_path_cells(cells: Array, door: Dictionary, cell: int = 24) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	var x0 := float(door.x0)
	var x1 := float(door.x1)
	var row := ceili(float(door.y) / cell - 0.000001)
	var lo := floori(x0 / cell) - 1
	var hi := floori((x1 - 0.000001) / cell) + 1
	var counts := {row: 0, row + 1: 0}
	for value in cells:
		var c := Vector2i(value)
		if counts.has(c.y) and c.x >= lo and c.x <= hi:
			counts[c.y] += 1
		elif c not in out:
			out.append(c)
	if counts[row] == 0:
		out.clear()
		for value in cells:
			if Vector2i(value) not in out:
				out.append(Vector2i(value))
		return out
	var width := maxi(counts[row], counts[row + 1])
	var centre := (x0 + x1) / 2.0
	var odd := absf(fposmod(centre, float(cell)) - cell / 2.0) <= cell / 4.0
	if odd != (width % 2 == 1):
		width += 1
	var start := roundi(centre / cell - width / 2.0)
	for r in [row, row + 1]:
		for k in width:
			var c := Vector2i(start + k, r)
			if c not in out:
				out.append(c)
	return out

## Gates on paths (rules.gate_path): of the spans a gate could take on a run, the one centred on the
## path that crosses it. `spans` are the candidate centres' positions along the run (texels), `path`
## the crossing path's centre; with no crossing (path is NAN) the first span is kept.
static func centred_span(spans: Array, path: float) -> int:
	if spans.is_empty():
		return -1
	if is_nan(path):
		return 0
	var best := 0
	for i in spans.size():
		if absf(float(spans[i]) - path) < absf(float(spans[best]) - path) - 0.001:
			best = i
	return best
