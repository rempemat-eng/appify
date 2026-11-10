extends RefCounted
## Where the player's body can stand in the running zone, asked of the physics itself (the walls on
## layer 1), on a grid of CELL texels. The play driver (tools/play_driver.gd) plans its walks on it and
## test/test_reach.gd uses it to prove that every talk area, door and spawn can be walked to.
##
## A cell is free when the player's body circle, centred on the cell, touches no wall. Cells are probed
## on demand and remembered; call `forget()` after something solid appears or goes (a Conditional).
## Physics queries only see bodies after a physics frame has run, so wait one after loading a zone.

const CELL := 6.0
const BODY_RADIUS := 9.0             ## actors/player.tscn: the body circle ...
const BODY_OFFSET := Vector2(0, -4)  ## ... and where it sits above the feet
const WALLS := 1                     ## physics layer 1
const MAX_EXPANDED := 250000

var bounds := Rect2()
var probes := 0

var _space: PhysicsDirectSpaceState2D
var _query := PhysicsShapeQueryParameters2D.new()
var _free := {}

func _init(world: World2D, zone_bounds: Rect2, margin := 1.0) -> void:
	_space = world.direct_space_state
	bounds = zone_bounds
	var shape := CircleShape2D.new()
	shape.radius = BODY_RADIUS + margin
	_query.shape = shape
	_query.collision_mask = WALLS
	_query.collide_with_bodies = true
	_query.collide_with_areas = false

func forget() -> void:
	_free.clear()

static func cell_of(p: Vector2) -> Vector2i:
	return Vector2i(floori(p.x / CELL), floori(p.y / CELL))

static func point_of(c: Vector2i) -> Vector2:
	return (Vector2(c) + Vector2(0.5, 0.5)) * CELL

## True when the player's feet can be at the middle of cell `c`.
func is_free(c: Vector2i) -> bool:
	if _free.has(c):
		return _free[c]
	var p := point_of(c)
	var ok := bounds.size == Vector2.ZERO or bounds.has_point(p)
	if ok:
		probes += 1
		_query.transform = Transform2D(0.0, p + BODY_OFFSET)
		ok = _space.intersect_shape(_query, 1).is_empty()
	_free[c] = ok
	return ok

## The free cell nearest to `p` within `reach` texels, or (-9999, -9999).
func nearest_free(p: Vector2, reach := 60.0) -> Vector2i:
	var c0 := cell_of(p)
	if is_free(c0):
		return c0
	var best := Vector2i(-9999, -9999)
	var best_d := INF
	var n := ceili(reach / CELL)
	for dy in range(-n, n + 1):
		for dx in range(-n, n + 1):
			var c := c0 + Vector2i(dx, dy)
			var d := point_of(c).distance_to(p)
			if d <= reach and d < best_d and is_free(c):
				best = c
				best_d = d
	return best

## True when every cell on the straight line between the two points is free.
func clear_line(a: Vector2, b: Vector2) -> bool:
	var steps := maxi(ceili(a.distance_to(b) / (CELL * 0.5)), 1)
	for i in steps + 1:
		if not is_free(cell_of(a.lerp(b, float(i) / steps))):
			return false
	return true

const _NEIGHBOURS: Array[Vector2i] = [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1),
	Vector2i(1, 1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(-1, -1)]

## Every free cell that can be walked to from `from` (a flood over the eight neighbours; a diagonal
## step needs both of its sides free, as a round body does).
func reachable(from: Vector2) -> Dictionary:
	var start := nearest_free(from)
	var seen := {}
	if start.x == -9999:
		return seen
	var stack: Array[Vector2i] = [start]
	seen[start] = true
	while not stack.is_empty():
		var c: Vector2i = stack.pop_back()
		for d in _NEIGHBOURS:
			var n := c + d
			if seen.has(n) or not is_free(n):
				continue
			if d.x != 0 and d.y != 0 and not (is_free(c + Vector2i(d.x, 0)) and is_free(c + Vector2i(0, d.y))):
				continue
			seen[n] = true
			stack.append(n)
	return seen

## A walk from `from` to within `tol` texels of `to` as points (A* over the free cells), empty when
## there is none.
func path(from: Vector2, to: Vector2, tol := 12.0) -> PackedVector2Array:
	var out := PackedVector2Array()
	var start := nearest_free(from)
	if start.x == -9999:
		return out
	var open: Array = [[_h(start, to, tol), 0.0, start]]   # a binary heap of [f, g, cell]
	var g := {start: 0.0}
	var came := {}
	var closed := {}
	var expanded := 0
	while not open.is_empty():
		var top: Array = _pop(open)
		var c: Vector2i = top[2]
		if closed.has(c):
			continue
		closed[c] = true
		if point_of(c).distance_to(to) <= tol:
			var cells: Array[Vector2i] = [c]
			while came.has(c):
				c = came[c]
				cells.append(c)
			cells.reverse()
			for cell in cells:
				out.append(point_of(cell))
			return out
		expanded += 1
		if expanded > MAX_EXPANDED:
			break
		for d in _NEIGHBOURS:
			var n := c + d
			if closed.has(n) or not is_free(n):
				continue
			var diagonal := d.x != 0 and d.y != 0
			if diagonal and not (is_free(c + Vector2i(d.x, 0)) and is_free(c + Vector2i(0, d.y))):
				continue
			var cost: float = g[c] + (1.41421 if diagonal else 1.0)
			if cost < g.get(n, INF):
				g[n] = cost
				came[n] = c
				_push(open, [cost + _h(n, to, tol), cost, n])
	return out

static func _h(c: Vector2i, to: Vector2, tol: float) -> float:
	return maxf(point_of(c).distance_to(to) - tol, 0.0) / CELL

static func _push(heap: Array, item: Array) -> void:
	heap.append(item)
	var i := heap.size() - 1
	while i > 0:
		var parent := (i - 1) >> 1
		if heap[parent][0] <= heap[i][0]:
			break
		var t: Array = heap[parent]
		heap[parent] = heap[i]
		heap[i] = t
		i = parent

static func _pop(heap: Array) -> Array:
	var top: Array = heap[0]
	var last: Array = heap.pop_back()
	if not heap.is_empty():
		heap[0] = last
		var i := 0
		while true:
			var l := 2 * i + 1
			var r := l + 1
			var m := i
			if l < heap.size() and heap[l][0] < heap[m][0]:
				m = l
			if r < heap.size() and heap[r][0] < heap[m][0]:
				m = r
			if m == i:
				break
			var t: Array = heap[m]
			heap[m] = heap[i]
			heap[i] = t
			i = m
	return top
