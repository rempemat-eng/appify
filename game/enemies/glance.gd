class_name Glance
extends RefCounted
## The mark for an arrow that does no harm (Matt, 11 Nov: keep the rule, make it unmistakable). A creature
## that cannot come for the archer (it is walking home, or the archer stands outside the ground it keeps
## to; the Thornback asleep or walking while the archer is outside its arena) cannot be hurt from there.
## The arrow glances off with a short metal spark and the word "clink" in steel grey: nothing like a hit,
## which flashes the creature white and knocks it back. Finite (TIME seconds); under reduced motion the
## spark stands still at its full size instead of flying out.
##
## Sound: the game has none yet. `clink(at)` is the one hook the sound work fills: every glance calls it,
## and it plays whatever `on_clink` is set to (nothing today).

const TIME := 0.4
const WORD := "clink"
const INK := Color("#2a1c1a")
const STEEL := Color("#d6dae0")
const SPARK := Color("#f4f1e8")
const RAYS := [Vector2(-1.0, -0.35), Vector2(-0.45, -1.0), Vector2(0.3, -1.0), Vector2(1.0, -0.5), Vector2(0.85, 0.25)]
const RAY := 9.0        ## texels, a ray's full length

## The sound hook: set by the sound work, e.g. `Glance.on_clink = func(at): $Player.play()`.
static var on_clink: Callable

## Called once for every arrow that glances off, at the glance's place (global texels).
static func clink(at: Vector2) -> void:
	if on_clink.is_valid():
		on_clink.call(at)

## What the mark shows `left` seconds before it ends: the length of each spark ray (0 once over) and the
## word. Reduced motion: the rays stand at full length from the first frame to the last.
static func parts(left: float, reduced: bool) -> Dictionary:
	if left <= 0.0:
		return {"ray": 0.0, "word": ""}
	var k := clampf(1.0 - left / TIME, 0.0, 1.0)
	var ray := RAY if reduced else RAY * clampf(0.35 + k * 1.6, 0.0, 1.0)
	return {"ray": ray, "word": WORD}

## Draws the mark on `ci` centred on `at` (texels, local); `left` is the seconds it still shows.
static func draw(ci: CanvasItem, at: Vector2, left: float) -> void:
	var p := parts(left, bool(SaveGame.setting("reduced_motion", false)))
	if p.word == "":
		return
	var o := (at / 3.0).round() * 3.0
	var r: float = p.ray
	for pass_ in 2:
		for v: Vector2 in RAYS:
			var a := o + v.normalized() * 3.0
			var b := o + v.normalized() * (3.0 + r)
			ci.draw_line(a, b, INK if pass_ == 0 else SPARK, 4.0 if pass_ == 0 else 2.0)
	ci.draw_rect(Rect2(o - Vector2(2, 2), Vector2(4, 4)), SPARK)
	var font := UiStyle.font()
	var at_word := o + Vector2(8, -9)
	ci.draw_string(font, at_word + Vector2(1, 1), WORD, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, INK)
	ci.draw_string(font, at_word, WORD, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, STEEL)
