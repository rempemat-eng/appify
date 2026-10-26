class_name UiStyle
extends RefCounted
## The interface's look on the 960 x 540 art grid (docs/vision/interface.md, Godot section): the pixel
## font, its colours and the panel, shared by the HUD, the pause menu and later the dialogue box.
##
## Pixelify Sans (OFL, ui/fonts/OFL.txt), the app's body font, drawn at 11 px so one glyph pixel is one
## texel: no antialiasing, no hinting, whole-pixel positions and no ligatures (its "fi" ligature reads
## as "A" at this size). Text sits on a one-texel ink shadow down and right, the light's far side.

const FONT_PATH := "res://ui/fonts/PixelifySans-Regular.ttf"
const SIZE := 11                     ## one glyph pixel per texel
const LINE := 12                     ## a text row, in texels
const TEXT := Color("#F3E9D2")       ## cream, lit
const TITLE := Color("#F8DD8F")      ## gold, lit
const DIM := Color("#BFAA86")        ## cream, shade
const INK := Color("#1E1917")        ## the outline (art/materials.json)
const TOUCH := 22                    ## 44 screen px at the 2x a 1080p window shows
const GRID := Vector2(960, 540)      ## the art grid the interface draws on (main/pixel_screen.gd ART)

static var _font: Font

static func font() -> Font:
	if _font == null:
		var file: FontFile = load(FONT_PATH)
		file.antialiasing = TextServer.FONT_ANTIALIASING_NONE
		file.hinting = TextServer.HINTING_NONE
		file.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
		file.generate_mipmaps = false
		file.multichannel_signed_distance_field = false
		var ts := TextServerManager.get_primary_interface()
		var v := FontVariation.new()
		v.base_font = file
		v.spacing_space = 1
		v.opentype_features = {ts.name_to_tag("liga"): 0, ts.name_to_tag("clig"): 0}
		_font = v
	return _font

## A label in the pixel font with the ink shadow; `colour` defaults to the lit cream.
static func label(text := "", colour := TEXT) -> Label:
	var l := Label.new()
	l.text = text
	style_label(l, colour)
	return l

static func style_label(l: Label, colour := TEXT) -> void:
	l.add_theme_font_override("font", font())
	l.add_theme_font_size_override("font_size", SIZE)
	l.add_theme_color_override("font_color", colour)
	l.add_theme_color_override("font_shadow_color", INK)
	l.add_theme_constant_override("shadow_offset_x", 1)
	l.add_theme_constant_override("shadow_offset_y", 1)
	l.add_theme_constant_override("shadow_outline_size", 0)
	l.add_theme_constant_override("outline_size", 0)
	l.add_theme_constant_override("line_spacing", 1)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE

## The dark wood panel (ui/art/panel.png, a 9-slice with 4 texel margins) with `pad` texels inside.
static func panel(pad := 4) -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = load("res://ui/art/panel.png")
	s.set_texture_margin_all(4)
	s.set_content_margin_all(4 + pad)
	s.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_STRETCH
	s.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_STRETCH
	return s

## The key cap behind a prompt's key letter (ui/art/key.png, 3 texel margins).
static func key_cap() -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = load("res://ui/art/key.png")
	s.set_texture_margin_all(3)
	s.content_margin_left = 3
	s.content_margin_right = 3
	s.content_margin_top = 1
	s.content_margin_bottom = 3
	return s

static func icon(name: String) -> TextureRect:
	var t := TextureRect.new()
	t.texture = load("res://ui/art/%s.png" % name)
	t.stretch_mode = TextureRect.STRETCH_KEEP
	t.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return t
