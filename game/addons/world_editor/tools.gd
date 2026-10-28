@tool
class_name WorldEditorTools
extends RefCounted
## Cell geometry for authoring. This never rotates/mirrors art or changes a piece's rules.

const FACINGS := ["s", "w", "n", "e"]
const ROUTE_SIMPLIFY_DISTANCE := 0.75

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
