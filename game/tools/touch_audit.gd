extends SceneTree
## Read-only Y9 audit. Window sizes are physical pixels; dpr converts them to logical points.
## Runs the real pixel-screen scale calculation and measures instantiated pause-menu buttons.

const MIN_POINTS := 44.0

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var screen = load("res://main/pixel_screen.gd")
	root.size = Vector2i(screen.ART)
	var menu: Control = load("res://ui/pause_menu.gd").new()
	root.add_child(menu)
	await process_frame
	await process_frame
	var targets := measure_controls(menu)
	var samples := []
	var complete := not targets.is_empty()
	# Explicit test windows, not measured phone specifications or a device test.
	for spec in [[1920, 1080, 1], [960, 540, 1], [874, 402, 1], [2622, 1206, 3], [667, 375, 1]]:
		for mode in ["fill", "whole"]:
			var result := audit(Vector2(spec[0], spec[1]), spec[2], mode, targets)
			complete = complete and result.ok
			samples.append(result)
	print(JSON.stringify({"complete": complete, "scope": "headless geometry, not rendered or device evidence", "art": [screen.ART.x, screen.ART.y], "target_count": targets.size(), "samples": samples}))
	menu.queue_free()
	await process_frame
	quit(0 if complete else 1)

static func measure_controls(node: Node) -> Array:
	var out := []
	_collect(node, out)
	return out

static func _collect(node: Node, out: Array) -> void:
	if node is Button:
		out.append({"id": str(node.get_path()), "rect": node.get_global_rect()})
	for child in node.get_children():
		_collect(child, out)

## Targets use ART-space rectangles; safe insets are logical left/top/right/bottom points.
## Invalid data returns ok=false. Findings do not make ok false: ok means the audit ran.
static func audit(window_pixels: Variant, dpr: Variant, mode: Variant, targets: Variant, insets: Variant = Vector4.ZERO) -> Dictionary:
	if not window_pixels is Vector2 or not _positive(window_pixels.x) or not _positive(window_pixels.y):
		return _error("window_pixels must be a positive finite Vector2")
	if not _positive(dpr) or not mode in ["fill", "whole"]:
		return _error("dpr must be positive and mode must be fill or whole")
	if not insets is Vector4 or not targets is Array:
		return _error("insets must be Vector4 and targets must be an array")
	for value in [insets.x, insets.y, insets.z, insets.w]:
		if not is_finite(value) or value < 0:
			return _error("insets must be finite nonnegative logical points")
	var logical: Vector2 = window_pixels / float(dpr)
	if not _positive(logical.x) or not _positive(logical.y) or insets.x + insets.z >= logical.x or insets.y + insets.w >= logical.y:
		return _error("safe area must leave positive finite space")
	# Runtime load: -s SceneTree scripts parse before project autoload names exist.
	var screen = load("res://main/pixel_screen.gd")
	var scale: float = screen.choose_scale(window_pixels, mode)
	if not _positive(scale):
		return _error("screen scale is not positive finite")
	var offset: Vector2 = ((window_pixels - screen.ART * scale) / 2.0).floor()
	var art_rect := Rect2(offset, screen.ART * scale)
	var safe := Rect2(Vector2(insets.x, insets.y) * float(dpr), (logical - Vector2(insets.x + insets.z, insets.y + insets.w)) * float(dpr))
	if not offset.is_finite() or not art_rect.end.is_finite() or not safe.position.is_finite() or not safe.end.is_finite():
		return _error("viewport projection overflowed")
	var rows := []
	var ids := {}
	var findings := []
	for target in targets:
		if not target is Dictionary or not target.get("id") is String or target.id.strip_edges().is_empty() or ids.has(target.id) or not target.get("rect") is Rect2:
			return _error("targets need unique nonblank string ids and Rect2 bounds")
		ids[target.id] = true
		var rect: Rect2 = target.rect
		if not rect.position.is_finite() or not rect.end.is_finite() or not _positive(rect.size.x) or not _positive(rect.size.y):
			return _error("target bounds must be finite with positive size")
		var projected := Rect2(offset + rect.position * scale, rect.size * scale)
		if not projected.position.is_finite() or not projected.end.is_finite() or not _positive(projected.size.x) or not _positive(projected.size.y):
			return _error("target projection overflowed or underflowed")
		var visible := projected.intersection(safe)
		var size_points: Vector2 = projected.size / float(dpr)
		var visible_points: Vector2 = visible.size / float(dpr)
		if not size_points.is_finite() or not visible_points.is_finite():
			return _error("logical target projection overflowed")
		var undersized := size_points.x < MIN_POINTS or size_points.y < MIN_POINTS
		var clipped := not safe.encloses(projected)
		if undersized:
			findings.append({"id": target.id, "rule": "touch.minimum", "minimum_points": MIN_POINTS})
		if clipped:
			findings.append({"id": target.id, "rule": "touch.clipped"})
		rows.append({"id": target.id, "width_points": size_points.x, "height_points": size_points.y, "visible_width_points": visible_points.x, "visible_height_points": visible_points.y, "undersized": undersized, "clipped": clipped})
	return {"ok": true, "error": "", "window_pixels": [window_pixels.x, window_pixels.y], "dpr": float(dpr), "mode": mode, "scale": scale, "logical_size": [logical.x, logical.y], "world_clipped": not Rect2(Vector2.ZERO, window_pixels).encloses(art_rect), "target_count": rows.size(), "targets": rows, "findings": findings, "passes": not rows.is_empty() and findings.is_empty()}

static func _positive(value: Variant) -> bool:
	return (value is float or value is int) and is_finite(float(value)) and float(value) > 0

static func _error(message: String) -> Dictionary:
	return {"ok": false, "passes": false, "error": message, "targets": [], "findings": []}
