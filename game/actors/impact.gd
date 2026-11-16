class_name Impact
extends Node2D
## What a shot does where it stops (Matt, 16 Nov, after playing the Mac build: "projectiles should more
## visibly hit things on impact"). One short effect at the contact point, drawn in code as pixel cells on the
## texel grid (whole texels, a dark outline like the cast's), lit from the upper left, in the house ramps
## (art/house-palette.json), and finite: it frees itself after `lifetime_of(kind, reduced)`. Kinds:
##
##   HIT    an arrow that counted on a creature: a warm star of four drawings (FRAME each, 0.2 s), and the
##          arrow stuck in the creature, riding on it, for STUCK, then fading over FADE. The creature's own
##          hurt flash and knock are its own (enemy.gd, enemies/creature_look.gd, bosses/thornback.gd); the
##          world holds for HIT_STOP real seconds (`hit_stop`).
##   CLINK  an arrow that glanced off (enemies/glance.gd, whose spark and word show over the creature): thin
##          cool steel streaks thrown back the way the arrow came, and the arrow bouncing back and falling.
##          Never warm and never a star, so a glance never reads as a hit. No hit-stop.
##   WALL   an arrow stopped by a solid: a puff of dust and two splinters, the arrow stuck in the face.
##   DROP   an arrow at the end of its flight: it falls to the ground, lies there and fades, with a small puff.
##   SPLAT  a creature's shot (the toad's seed, the Thornback's thorn) breaking on the player or on a solid:
##          droplets in the shooter's own colours (`tint`, light and dark).
##
## The node stands on the ground under the contact (as the arrow does) and draws the contact `lift` texels
## above it, over its neighbours (z_index 1, like the other short marks: world/camp_settle.gd). It is a child
## of the shot's own parent, so it goes with its zone, and it stops with the tree when the game is paused.
##
## Reduced motion: no hit-stop and nothing moves. The burst is one still drawing for STILL seconds, an arrow
## stays where it stopped for STUCK and goes without a fade, a dropped arrow is on the ground at once, and a
## glancing arrow does not bounce (it goes with its spark).

enum Kind { HIT, CLINK, WALL, DROP, SPLAT }

const FRAME := 0.05      ## seconds each drawing of a burst shows
const FRAMES := 4
const STILL := 0.1       ## reduced motion: the one still drawing shows this long
const STUCK := 0.32      ## an arrow stays where it stopped this long
const FADE := 0.18       ## then fades over this long
const FALL := 0.12       ## an arrow at the end of its flight falls to the ground in this long
const BOUNCE := 0.26     ## a glancing arrow bounces back and falls in this long
const HIT_STOP := 0.05   ## real seconds the world holds when an arrow counts (3 frames at 60)
const HOLD_SCALE := 0.05 ## the engine's time scale while it holds (as the melee's hit-stop: actors/player.gd)

const INK := Color("#2a1c1a")
## HIT: sand_warm 5, brass_warm 5, 4 and 3 (light to shade)
const WHITE := Color("#fff2db")
const GOLD := Color("#face7a")
const AMBER := Color("#e6b450")
const OCHRE := Color("#ca9933")
## CLINK: the glance's own steel and spark (enemies/glance.gd), slate 4 for the cooling streaks
const STEEL := Color("#d6dae0")
const SPARK := Color("#f4f1e8")
const SLATE := Color("#8e91a1")
## WALL and DROP: path 5, 4, 3 (dust) and timber 4 (splinters)
const DUST_LIT := Color("#d6b187")
const DUST := Color("#c39771")
const DUST_DARK := Color("#a87c60")
const SPLINTER := Color("#a87c52")
## SPLAT tints of the two shots: the toad's seed (earth 4 over its husk) and the Thornback's thorn (sand 3
## over its plum), both from the shots' own pictures.
const SEED_TINT: Array[Color] = [Color("#947b60"), Color("#4a3c2c")]
const THORN_TINT: Array[Color] = [Color("#d4b488"), Color("#82204f")]

const CARDINAL: Array[Vector2] = [Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0), Vector2(0, -1)]
const DIAGONAL: Array[Vector2] = [Vector2(1, 1), Vector2(-1, 1), Vector2(-1, -1), Vector2(1, -1)]

var kind: Kind = Kind.HIT
var dir := Vector2.RIGHT          ## the way the shot was flying
var lift := 0.0                   ## the contact's height above the node, texels
var shaft := false                ## draw the arrow where it stopped
var follow: Node2D                ## a creature the stuck arrow rides on
var tint: Array[Color] = [GOLD, OCHRE]
var reduced := false
var _offset := Vector2.ZERO
var _t := 0.0
var _rode := true                 ## false once the creature it rode on is gone or freed

## The effect for a shot that stopped: added to `host` (the shot's parent) with its ground point at `at`.
static func spawn(host: Node, what: Kind, at: Vector2, height: float, along: Vector2, with_shaft := false,
		on: Node2D = null, colours: Array[Color] = []) -> Impact:
	if host == null or not is_instance_valid(host):
		return null
	var fx := Impact.new()
	fx.kind = what
	fx.lift = height
	fx.dir = along.normalized() if along.length() > 0.01 else Vector2.RIGHT
	fx.shaft = with_shaft
	fx.follow = on
	if colours.size() == 2:
		fx.tint = colours
	host.add_child(fx)
	fx.global_position = at
	if on != null:
		fx._offset = at - on.global_position
	return fx

## How high above its feet a shot meets `body`, for a shot flying `height` texels up: the middle of the body
## as drawn (a placeholder Sprite2D's frame, or half the cast's `body_height_target`), never higher than the
## shot. The arrow flies at the bow's height, over a mossling's back: its mark belongs on the creature, not in
## the air above it (seen in the first pictures, 16 Nov). A body with an `impact_lift()` says so itself.
static func body_lift(body: Node, height: float) -> float:
	if body == null or not is_instance_valid(body):
		return height
	if body.has_method("impact_lift"):
		return clampf(float(body.call("impact_lift")), 0.0, height)
	var s: Variant = body.get("sprite")
	if s is Sprite2D:
		var spr := s as Sprite2D
		return clampf(-(spr.position.y + spr.get_rect().get_center().y * spr.scale.y), 0.0, height)
	for c in body.get_children():
		if c is CreatureLook and (c as CreatureLook).sprite != null:
			var tall := float((c as CreatureLook).sprite.manifest.get("body_height_target", 0.0))
			if tall > 0.0:
				return clampf(tall * 0.5, 0.0, height)
	return height

## Seconds the effect lives before it frees itself.
static func lifetime_of(what: Kind, still: bool, with_shaft := true) -> float:
	var burst := STILL if still else FRAME * FRAMES
	if not with_shaft:
		return burst
	match what:
		Kind.HIT, Kind.WALL:
			return maxf(burst, STUCK if still else STUCK + FADE)
		Kind.DROP:
			return maxf(burst, STUCK if still else FALL + STUCK + FADE)
		Kind.CLINK:
			return burst if still else maxf(burst, BOUNCE + FADE)
	return burst

## Holds the world still for HIT_STOP real seconds: the arrow's weight on a hit that counted. Nothing under
## reduced motion, and nothing while another hold (the melee's) is under way. Returns whether it held.
static func hit_stop(tree: SceneTree) -> bool:
	if tree == null or SaveGame.setting("reduced_motion", false) or Engine.time_scale < 1.0:
		return false
	Engine.time_scale = HOLD_SCALE
	tree.create_timer(HIT_STOP, true, false, true).timeout.connect(func() -> void:
		if is_equal_approx(Engine.time_scale, HOLD_SCALE):
			Engine.time_scale = 1.0)
	return true

func _ready() -> void:
	z_index = 1
	reduced = bool(SaveGame.setting("reduced_motion", false))

func lifetime() -> float:
	return lifetime_of(kind, reduced, shaft)

func _process(delta: float) -> void:
	_t += delta
	if _t >= lifetime():
		queue_free()
		return
	if follow != null:
		if is_instance_valid(follow) and not _gone(follow):
			global_position = follow.global_position + _offset
		else:
			_rode = false
			follow = null
	queue_redraw()

## True for a creature that has been freed (its own fade and leaving take over: no arrow rides on it).
static func _gone(n: Node) -> bool:
	return n.get("dead") == true or n.get("freed") == true

## The drawing of the burst showing now: 0 to FRAMES - 1, or -1 when it is over (or not begun).
func burst_frame() -> int:
	var t := _t - (FALL if kind == Kind.DROP and not reduced else 0.0)
	if t < 0.0:
		return -1
	if reduced:
		return 1 if t < STILL else -1
	var f := int(t / FRAME)
	return f if f < FRAMES else -1

func _draw() -> void:
	var o := Vector2(0, -lift).round()
	if shaft:
		_draw_shaft(o)
	var f := burst_frame()
	if f < 0:
		return
	match kind:
		Kind.HIT:
			_draw_star(o, f)
		Kind.CLINK:
			_draw_streaks(o, f)
		Kind.WALL:
			_draw_dust(o, f, 3, true)
		Kind.DROP:
			_draw_dust(Vector2.ZERO + _drop_ahead(), f, 2, false)
		Kind.SPLAT:
			_draw_splat(o, f)

# --- the arrow where it stopped ---------------------------------------------------------------------------
func _shaft_alpha(from: float) -> float:
	if reduced:
		return 1.0 if _t < STUCK else 0.0
	return clampf(1.0 - (_t - from) / FADE, 0.0, 1.0)

func _drop_ahead() -> Vector2:
	return (dir * 6.0).round()

func _draw_shaft(o: Vector2) -> void:
	match kind:
		Kind.HIT, Kind.WALL:
			if kind == Kind.HIT and not _rode:
				return
			# the head is in the creature or the face: only the shaft and the fletching show
			Arrow.draw_arrow(self, o, dir, false, _shaft_alpha(STUCK))
		Kind.DROP:
			var k := 1.0 if reduced else clampf(_t / FALL, 0.0, 1.0)
			var at := Vector2(0, -lift * (1.0 - k * k)).round() + (_drop_ahead() * k).round()
			Arrow.draw_arrow(self, at, dir, true, _shaft_alpha(FALL + STUCK))
		Kind.CLINK:
			if reduced:
				return
			var k := clampf(_t / BOUNCE, 0.0, 1.0)
			# back the way it came, a little up and then down to the ground, turning over as it goes
			var back := -dir * 14.0 * k
			var hop := Vector2(0, -lift * (1.0 - k) - 8.0 * sin(PI * k))
			var turn := dir.rotated((1.0 if dir.x >= 0.0 else -1.0) * 2.2 * k)
			Arrow.draw_arrow(self, (back + hop).round(), turn, true, _shaft_alpha(BOUNCE))

# --- cells ------------------------------------------------------------------------------------------------
## Square cells of `size` texels centred on each point, snapped to whole texels, under a one-texel outline.
func _cells(points: Array, size: int, colours: Array, ink := true) -> void:
	var half := Vector2(size, size) * 0.5
	if ink:
		for p in points:
			draw_rect(Rect2((p - half).round() - Vector2.ONE, Vector2(size + 2, size + 2)), INK)
	for i in points.size():
		draw_rect(Rect2((points[i] - half).round(), Vector2(size, size)), colours[mini(i, colours.size() - 1)])

## Lit from the upper left: a point up and to the left of the contact takes the light colour.
static func _lit(v: Vector2, light: Color, shade: Color) -> Color:
	return light if v.x + v.y < 0.0 else shade

## A warm star: a white core that throws four long and four short gold rays, which break off and fade.
func _draw_star(o: Vector2, f: int) -> void:
	var pts := []
	var cols := []
	match f:
		0:
			for v in CARDINAL:
				pts.append(o + v * 5.0)
				cols.append(_lit(v, WHITE, GOLD))
			_cells(pts, 2, cols)
			_cells([o], 5, [WHITE])
		1:
			for v in CARDINAL:
				for r: float in [4.0, 6.0, 8.0, 10.0]:
					pts.append(o + v * r)
					cols.append(WHITE if r >= 10.0 else _lit(v, GOLD, AMBER))
			for v in DIAGONAL:
				pts.append(o + v.normalized() * 5.0)
				cols.append(_lit(v, GOLD, AMBER))
			_cells(pts, 2, cols)
			_cells([o], 3, [WHITE])
		2:
			for v in CARDINAL:
				for r: float in [10.0, 12.0]:
					pts.append(o + v * r)
					cols.append(_lit(v, GOLD, AMBER))
			for v in DIAGONAL:
				pts.append(o + v.normalized() * 8.0)
				cols.append(_lit(v, AMBER, OCHRE))
			_cells(pts, 2, cols)
		3:
			for v in CARDINAL:
				pts.append(o + v * 13.0)
				cols.append(_lit(v, AMBER, OCHRE))
			_cells(pts, 1, cols)

## Thin steel streaks thrown back the way the arrow came (and a little up), from a small cross.
func _draw_streaks(o: Vector2, f: int) -> void:
	var back := (-dir + Vector2(0, -0.6)).normalized()
	var ways: Array[Vector2] = [back, back.rotated(0.6), back.rotated(-0.6)]
	var pts := []
	var cols := []
	match f:
		0:
			for v in CARDINAL:
				pts.append(o + v * 2.0)
				cols.append(STEEL)
			pts.append(o)
			cols.append(SPARK)
		1:
			for v in ways:
				for r in range(2, 9):
					pts.append(o + v * r)
					cols.append(SPARK if r >= 7 else STEEL)
		2:
			for v in ways:
				for r in range(7, 12):
					pts.append(o + v * r)
					cols.append(STEEL if r >= 10 else SLATE)
		3:
			for v in ways:
				pts.append(o + v * 13.0)
				cols.append(SLATE)
	_cells(pts, 1, cols)

## A puff of dust from the contact, rising and spreading; with `splinters`, two chips of wood flying off.
func _draw_dust(o: Vector2, f: int, clumps: int, splinters: bool) -> void:
	var side := dir.orthogonal().normalized()
	var radius: Array[float] = [2.0, 3.0, 3.0, 2.0]
	var rise: Array[float] = [0.0, 1.0, 3.0, 5.0]
	var spread: Array[float] = [2.0, 3.0, 5.0, 6.0]
	var r := radius[f] if clumps > 2 else radius[f] - 1.0
	for c in clumps:
		var across := (float(c) - float(clumps - 1) * 0.5) * spread[f]
		var centre := (o - dir * 3.0 + side * across + Vector2(0, -rise[f] - absf(across) * 0.3)).round()
		_disc(centre, r, 0.65 if f == 3 else 1.0)
	if splinters and f < 3:
		var pts := []
		var cols := []
		for s: float in [-1.0, 1.0]:
			var away := (-dir + side * s * 1.2 + Vector2(0, -0.5)).normalized()
			pts.append(o + away * (3.0 + 3.0 * f))
			cols.append(SPLINTER)
		_cells(pts, 2, cols)

## A round clump of dust, its upper left lit and its lower right in shade, no outline (dust is soft).
func _disc(c: Vector2, r: float, a: float) -> void:
	var n := int(ceil(r))
	for y in range(-n, n + 1):
		for x in range(-n, n + 1):
			var v := Vector2(x, y)
			if v.length() > r + 0.25:
				continue
			var col := DUST
			if x + y <= -n:
				col = DUST_LIT
			elif x + y >= n:
				col = DUST_DARK
			col.a = a
			draw_rect(Rect2(c + v, Vector2.ONE), col)

## The shot breaking: a blob in its colours, then droplets flying out and falling.
func _draw_splat(o: Vector2, f: int) -> void:
	var light: Color = tint[0]
	var dark: Color = tint[1]
	var pts := []
	var cols := []
	match f:
		0:
			_cells([o], 5, [light])
			draw_rect(Rect2(o.round() + Vector2(-2, 1), Vector2(5, 1)), dark)
		1:
			for i in 6:
				var v := Vector2.RIGHT.rotated(TAU * i / 6.0 + 0.3)
				pts.append(o + v * 5.0)
				cols.append(_lit(v, light, dark))
			_cells(pts, 2, cols)
		2:
			for i in 6:
				var v := Vector2.RIGHT.rotated(TAU * i / 6.0 + 0.3)
				pts.append(o + v * 8.0 + Vector2(0, 1))
				cols.append(_lit(v, light, dark))
			_cells(pts, 1, cols)
		3:
			for i in 3:
				var v := Vector2.RIGHT.rotated(TAU * i / 3.0 + 0.8)
				pts.append(o + v * 10.0 + Vector2(0, 3))
				cols.append(dark)
			_cells(pts, 1, cols)
