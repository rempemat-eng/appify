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
	get_window().size_changed.connect(fit)
	RenderingServer.set_default_clear_color(Color.BLACK)
	fit()

static func choose_scale(window: Vector2, mode: String) -> float:
	var k := minf(window.x / ART.x, window.y / ART.y)
	var whole := floorf(k + 0.0001)
	if mode == "whole" or absf(k - whole) < 0.0001:
		return maxf(whole, 1.0)
	return k

func fit() -> void:
	var win := Vector2(get_window().size)
	scale_k = choose_scale(win, str(SaveGame.setting("pixel_scale", "fill")))
	exact = absf(scale_k - roundf(scale_k)) < 0.0001
	screen.stretch = false
	screen.size = ART
	screen.scale = Vector2(scale_k, scale_k)
	screen.position = ((win - ART * scale_k) / 2.0).floor()
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
