extends Node
## Shows the 960 x 540 art grid on any window (game-design.md 11.1, Matt 21 to 25 Oct):
## at the largest scale that fits with the aspect kept, exact nearest-neighbour when that scale is a whole
## number (2x at 1920 x 1080, 4x at 3840 x 2160 with HiDPI on), and sharp bilinear (crisp texels, a
## one-pixel blend at their edges) when it is not, so odd windows fill instead of showing wide black bars.
## The setting "pixel_scale" = "whole" forces the largest whole scale with bars instead.
## The game renders into the SubViewport `Screen/World`; this node only scales and centres it.

const ART := Vector2(960, 540)

var scale_k := 1.0
var exact := true

@onready var screen: SubViewportContainer = $Screen
@onready var shader: Shader = preload("res://main/sharp_bilinear.gdshader")

func _ready() -> void:
	keep_on_screen()
	get_window().size_changed.connect(fit)
	RenderingServer.set_default_clear_color(Color.BLACK)
	pin_camera_frame(get_tree(), Vector2i(ART))
	fit()

## The phantom camera keeps its frame inside the zone's limits with a frame of the manager's `screen_size`,
## and the manager sets that to the root window's size on every resize (addons/phantom_camera/scripts/
## managers/phantom_camera_manager.gd, `_ready`). The game is drawn in the 960 x 540 SubViewport whatever
## the window, so after the first resize (fullscreen on a Mac, a dragged corner) the frame was the window's:
## at 3024 x 1964 the camera's centre was held at y 982 in the 1728-texel woodland and the player walked
## out of the picture (Matt, 16 Nov). This drops the manager's resize hook and keeps the frame at the
## picture's size.
static func pin_camera_frame(tree: SceneTree, size: Vector2i) -> void:
	var manager := tree.root.get_node_or_null(^"PhantomCameraManager")
	if manager == null:
		return
	for c: Dictionary in tree.root.size_changed.get_connections():
		var callable: Callable = c.callable
		if callable.get_object() == manager:
			tree.root.size_changed.disconnect(callable)
	manager.set(&"screen_size", size)

## The window opens at the project's 1920 x 1080 (window_width_override); on a smaller desktop (a 1440 x 900
## screen) that is bigger than the screen. Shrink it, 16:9 kept, to fit the screen's usable area and
## centre it there. A size given with --resolution, fullscreen, phones, the web and headless runs are left alone.
func keep_on_screen() -> void:
	var w := get_window()
	if w.mode != Window.MODE_WINDOWED or OS.has_feature("mobile") or OS.has_feature("web") \
			or DisplayServer.get_name() == "headless" or "--resolution" in OS.get_cmdline_args() \
			or Engine.is_embedded_in_editor():
		return
	var usable := DisplayServer.screen_get_usable_rect(w.current_screen)
	var size := window_size_for(w.size, usable.size)
	if size != w.size:
		w.size = size
		w.position = usable.position + (usable.size - size) / 2

## The window size for `want` on a screen whose usable area is `room`: `want` when it fits, otherwise the
## largest size of the art's aspect within nine tenths of `room` (room for the title bar and the edges).
static func window_size_for(want: Vector2i, room: Vector2i) -> Vector2i:
	if room.x <= 0 or room.y <= 0 or (want.x <= room.x and want.y <= room.y):
		return want
	var k := minf(room.x * 0.9 / ART.x, room.y * 0.9 / ART.y)
	return Vector2i(ART * k)

static func choose_scale(window: Vector2, mode: String) -> float:
	var k := minf(window.x / ART.x, window.y / ART.y)
	var whole := floorf(k + 0.0001)
	if mode == "whole" or absf(k - whole) < 0.0001:
		return maxf(whole, 1.0)
	return k

## Where the picture's top left goes in a window: centred, bars of equal size on both sides (to a pixel).
static func picture_at(window: Vector2, k: float) -> Vector2:
	return ((window - ART * k) / 2.0).floor()

func fit() -> void:
	var win := Vector2(get_window().size)
	scale_k = choose_scale(win, str(SaveGame.setting("pixel_scale", "fill")))
	exact = absf(scale_k - roundf(scale_k)) < 0.0001
	screen.stretch = false
	screen.size = ART
	screen.scale = Vector2(scale_k, scale_k)
	screen.position = picture_at(win, scale_k)
	pin_camera_frame(get_tree(), Vector2i(ART))
	# UI targets use logical display points, independently of the world's art scale.
	# Keep the native display query here; tests/callers can supply explicit ratios.
	var ratio := DisplayServer.screen_get_scale()
	if not is_finite(ratio) or ratio <= 0.0:
		ratio = 1.0
	var safe := Rect2(Vector2.ZERO, win)
	if OS.has_feature("mobile"):
		var display_safe := Rect2(DisplayServer.get_display_safe_area())
		display_safe.position -= Vector2(get_window().position)
		var visible_safe := safe.intersection(display_safe)
		if visible_safe.has_area():
			safe = visible_safe
	get_tree().call_group(&"pause_screen_layout", &"fit_screen", win, scale_k, screen.position, ratio, safe)
	if exact:
		screen.material = null
		screen.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	else:
		var m := ShaderMaterial.new()
		m.shader = shader
		m.set_shader_parameter("scale", scale_k)
		screen.material = m
		screen.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
