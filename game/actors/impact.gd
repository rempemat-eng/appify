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
##   WALL   an arrow stuck in a solid (`sticks`): only one that crossed the solid's south edge, below the top
##          of its drawn face (`impact_face`, texels), when the face is timber or earth (`impact_material`):
##          the timber houses. Dust and two chips, the arrow stuck in it.
##   DROP   an arrow that falls to the ground: at the end of its flight (carried a little on), or off any other
##          solid (a tree, a rock, a prop with only a foot box, a face met on another edge or above its top,
##          knocked back off it, so a house hides it): it falls, lies there and fades, with dust at its feet.
##          On stone (`impact_material` "stone": walls, the library, the vault) the dust is stone grey and
##          chips fly: the arrow never sticks in stone (#509 round 2, S1).
##   SINK   an arrow whose flight ends over water: it falls in, leaves a small ring and is gone. No dust.
##   SPLAT  a creature's shot (the toad's seed, the Thornback's thorn) breaking on the player or on a solid:
##          droplets in the shooter's own colours (`tint`, light and dark), on the ground unless the solid has
##          a face.
##
## The node stands on the ground under the contact (as the arrow does) and y-sorts there with everything
## else: a stuck or dropped arrow, ground dust and a ring are drawn by it, so a roof, a crown or a creature in
## front covers them (#509 round 1, F2). Only a burst up on what was hit (the star, the steel streaks, the
## puff on a face, a splat on the player) is drawn by its child `Burst` at z_index 1, over its neighbours for
## its 0.2 s, like the other short marks (world/camp_settle.gd). It is a child of the shot's own parent, so it
## goes with its zone, and it stops with the tree when the game is paused.
##
## Reduced motion: no hit-stop and nothing moves. The burst is one still drawing for STILL seconds, an arrow
## stays where it stopped for STUCK and goes without a fade, a dropped arrow is on the ground at once, and a
## glancing arrow does not bounce (it goes with its spark).

enum Kind { HIT, CLINK, WALL, DROP, SINK, SPLAT }

const FRAME := 0.05      ## seconds each drawing of a burst shows
const FRAMES := 4
const STILL := 0.1       ## reduced motion: the one still drawing shows this long
const STUCK := 0.32      ## an arrow stays where it stopped this long
const FADE := 0.18       ## then fades over this long
const FALL := 0.12       ## an arrow at the end of its flight falls to the ground in this long
const BOUNCE := 0.26     ## a glancing arrow bounces back and falls in this long
const RING := 0.2       ## SINK: the ring on the water shows this long after the arrow falls in
const HIT_STOP := 0.05   ## real seconds the world holds when an arrow counts (3 frames at 60)
## The engine's time scale while an arrow holds. Not the melee's 0.05 (actors/player.gd `_hitstop`): the arrow's
## restore puts the scale back only while it is still this value and its own hold is the newest, so it never
## ends a melee hold that began during it (#509 round 1, P3).
const HOLD_SCALE := 0.06
const FRONT := 6.0      ## a stuck arrow y-sorts this far south of its house's box (past its drawn feet)
const FACE_TOP := 3.0   ## an arrow sticks only this far or more below the top of the drawn face
const STICKY := ["timber", "earth"]   ## the materials an arrow sticks in; stone sends it down with chips

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
## WALL and DROP: path 5, 4, 3 (dust) and timber 4 (splinters); SINK: a pale crest (sand_warm 5, as the
## star's light) over water 5, so the ring reads on the stream
const FOAM := Color("#92b8c5")
const DUST_LIT := Color("#d6b187")
const DUST := Color("#c39771")
const DUST_DARK := Color("#a87c60")
const SPLINTER := Color("#a87c52")
## stone 5, 4, 3 (dust off a stone face) and stone 2 (its chips)
const STONE_LIT := Color("#c5b8a4")
const STONE := Color("#aba194")
const STONE_DARK := Color("#8e8782")
const STONE_CHIP := Color("#70676a")
## SPLAT tints of the two shots: the toad's seed (its pale flesh, grass 5, over its husk) and the Thornback's
## thorn (sand 3 over its plum), from the shots' own pictures.
const SEED_TINT: Array[Color] = [Color("#cfcf84"), Color("#4a3c2c")]
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
var drift := Vector2.ZERO         ## DROP: how far the falling arrow is carried (on, or back off a solid)
var face_material := ""              ## the face it met: "timber", "earth", "stone" or "" (none: plain dust)
var _rode := true                 ## false once the creature it rode on is gone or freed
var _burst: Node2D                ## draws the burst over its neighbours (z_index 1) when it is up on a thing
var _ci: CanvasItem               ## the canvas the cell helpers draw on

static var _hold_token := 0       ## the newest arrow hold; an older hold's restore leaves the scale alone

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
	fx.drift = (fx.dir * 6.0).round() if with_shaft else Vector2.ZERO   # a shot's ring is where it ended
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

## The drawn face of `body`: {"height": texels from its foot to the top of the face as drawn (0: none),
## "material": "timber", "earth" or "stone", "stone_below": the top of a stone plinth under a timber or earth
## wall (0: none), "no_stick": the windows, Rect2s of (x from the box's centre, lift) where nothing sticks}.
## Written by the zone generators as the metas `impact_face`, `impact_material`, `impact_stone_below` and
## `impact_no_stick` (tools/gen_blockout.py `solid(face=...)`), or answered by a method `impact_face()`.
static func face_of(body: Node) -> Dictionary:
	if body == null or not is_instance_valid(body):
		return {"height": 0.0, "material": "", "stone_below": 0.0, "no_stick": []}
	if body.has_method("impact_face"):
		return body.call("impact_face")
	return {"height": float(body.get_meta("impact_face", 0.0)), "material": String(body.get_meta("impact_material", "")),
		"stone_below": float(body.get_meta("impact_stone_below", 0.0)), "no_stick": body.get_meta("impact_no_stick", [])}

## What a shot whose ground point was at `from` one step before it met `body`, flying `lift` texels up, does
## there: "stick" (in a timber or earth face, see below), "stone" (it met stone: a stone face, or the stone
## plinth under a timber wall, at or below its top), "window" (a window of a timber wall: nothing to stick in)
## or "drop" (no face, another edge, or above the face's top). Only "stick" leaves the arrow stuck.
## It sticks only when it crossed the body's south edge (it was south of the box's bottom and within its
## width; no body declares a side face) and meets the face at least FACE_TOP below the face's drawn top
## (#509 round 2, F1b); then the plinth and the windows decide (#509 follow-up, 16 Nov).
static func face_hit(body: Node, from: Vector2, lift: float) -> String:
	var face := face_of(body)
	var height := float(face.height)
	if height <= 0.0:
		return "drop"
	var box := box_of(body)
	var south := box.size != Vector2.ZERO and from.y > box.end.y and from.x >= box.position.x and from.x <= box.end.x
	if not south or lift > height - FACE_TOP:
		return "drop"
	if not STICKY.has(String(face.material)) or lift <= float(face.stone_below):
		return "stone"
	var at := Vector2(from.x - box.get_center().x, lift)
	for window: Variant in face.no_stick:
		if window is Rect2 and (window as Rect2).has_point(at):
			return "window"
	return "stick"

## True when a shot sticks in `body` (`face_hit` says "stick").
static func sticks(body: Node, from: Vector2, lift: float) -> bool:
	return face_hit(body, from, lift) == "stick"

## Puts a stuck arrow's ground point just south of the face it is stuck in (FRONT texels past the box), raising
## its lift by as much, so it is drawn where it was and y-sorts in front of the house it is in (the house sorts
## by its drawn feet, at or a little past its box: an arrow met 1 texel inside the north cottages' box was drawn
## behind them, seen in the follow-up's pictures, 16 Nov).
static func in_front_of(fx: Impact, body: Node) -> void:
	var box := box_of(body)
	if fx == null or box.size == Vector2.ZERO:
		return
	var d := box.end.y + FRONT - fx.global_position.y
	if d > 0.0:
		fx.global_position.y += d
		fx.lift += d

## The global rectangle of a body's first rectangle shape (unrotated), or an empty Rect2.
static func box_of(body: Node) -> Rect2:
	if not body is CollisionObject2D:
		return Rect2()
	var co := body as CollisionObject2D
	for owner_id in co.get_shape_owners():
		var cs := co.shape_owner_get_owner(owner_id) as CollisionShape2D
		if cs != null and cs.shape is RectangleShape2D:
			var size := (cs.shape as RectangleShape2D).size * cs.global_scale.abs()
			return Rect2(cs.global_position - size * 0.5, size)
	return Rect2()

## What lies under a flight's end at `at` (global texels): "water" (low terrain the zone generator marks
## `impact_water`, tools/gen_zone.py), "low" (any other low solid: a bench, a stump, a bush, a drop) or
## "ground". Asked in the physics step, never in a contact callback.
static func ground_at(space: PhysicsDirectSpaceState2D, at: Vector2) -> String:
	var q := PhysicsPointQueryParameters2D.new()
	q.position = at
	q.collision_mask = Arrow.LOW
	var what := "ground"
	for hit in space.intersect_point(q, 8):
		var body := hit.collider as CollisionObject2D
		if body == null or not Arrow.is_low(body):
			continue
		if body.get_meta("impact_water", false):
			return "water"
		var owner_node: Variant = body.shape_owner_get_owner(body.shape_find_owner(int(hit.shape)))
		if owner_node is Node and (owner_node as Node).get_meta("impact_water", false):
			return "water"
		what = "low"
	return what

## Seconds the effect lives before it frees itself.
static func lifetime_of(what: Kind, still: bool, with_shaft := true) -> float:
	var burst := STILL if still else FRAME * FRAMES
	if not with_shaft:
		return (STILL if still else RING) if what == Kind.SINK else burst   # a shot's ring, from its start
	match what:
		Kind.HIT, Kind.WALL:
			return maxf(burst, STUCK if still else STUCK + FADE)
		Kind.DROP:
			return maxf(burst, STUCK if still else FALL + STUCK + FADE)
		Kind.SINK:
			return STILL if still else FALL + RING
		Kind.CLINK:
			return burst if still else maxf(burst, BOUNCE + FADE)
	return burst

## Holds the world still for HIT_STOP real seconds: the arrow's weight on a hit that counted. Nothing under
## reduced motion, and nothing while another hold (the melee's) is under way. Returns the real-time timer
## that ends the hold (it counts HIT_STOP and ignores the time scale), or null when it did not hold.
static func hit_stop(tree: SceneTree) -> SceneTreeTimer:
	if tree == null or SaveGame.setting("reduced_motion", false) or Engine.time_scale < 1.0:
		return null
	Engine.time_scale = HOLD_SCALE
	_hold_token += 1
	var mine := _hold_token
	var timer := tree.create_timer(HIT_STOP, true, false, true)
	timer.timeout.connect(func() -> void: release_hold(mine))
	return timer

## The newest arrow hold's token (0 before any).
static func hold_token() -> int:
	return _hold_token

## Ends the arrow hold `token`: the scale goes back to 1 only while that hold is the newest and the scale is
## still the arrow's own (never a melee hold, never a newer arrow hold).
static func release_hold(token: int) -> void:
	if token == _hold_token and Engine.time_scale == HOLD_SCALE:
		Engine.time_scale = 1.0

func _ready() -> void:
	reduced = bool(SaveGame.setting("reduced_motion", false))
	_burst = Node2D.new()
	_burst.name = "Burst"
	_burst.z_index = 1
	add_child(_burst)
	_burst.draw.connect(_draw_burst_on_top)

## True when the burst is on the ground (dust where an arrow lies, a ring, a splat at a solid's foot): it is
## then drawn in the y-sort with the arrow, not over everything.
func burst_on_ground() -> bool:
	return kind == Kind.DROP or kind == Kind.SINK or lift <= 0.0

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
	_burst.queue_redraw()

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
	_ci = self
	var o := Vector2(0, -lift).round()
	if shaft:
		_draw_shaft(o)
	if kind == Kind.SINK:
		_draw_ring()
	elif burst_on_ground():
		_draw_burst(o)

func _draw_burst_on_top() -> void:
	if burst_on_ground():
		return
	_ci = _burst
	_draw_burst(Vector2(0, -lift).round())

func _draw_burst(o: Vector2) -> void:
	var f := burst_frame()
	if f < 0:
		return
	match kind:
		Kind.HIT:
			_draw_star(o, f)
		Kind.CLINK:
			_draw_streaks(o, f)
		Kind.WALL:
			_draw_dust(o, f, 3, _chip())
		Kind.DROP:
			_draw_dust(drift, f, 3 if face_material == "stone" else 2, _chip())
		Kind.SPLAT:
			_draw_splat(o, f)

# --- the arrow where it stopped ---------------------------------------------------------------------------
func _shaft_alpha(from: float) -> float:
	if reduced:
		return 1.0 if _t < STUCK else 0.0
	return clampf(1.0 - (_t - from) / FADE, 0.0, 1.0)

func _draw_shaft(o: Vector2) -> void:
	match kind:
		Kind.HIT, Kind.WALL:
			if kind == Kind.HIT and not _rode:
				return
			# the head is in the creature or the face: only the shaft and the fletching show
			Arrow.draw_arrow(self, o, dir, false, _shaft_alpha(STUCK))
		Kind.DROP:
			var k := 1.0 if reduced else clampf(_t / FALL, 0.0, 1.0)
			var at := Vector2(0, -lift * (1.0 - k * k)).round() + (drift * k).round()
			Arrow.draw_arrow(self, at, dir, true, _shaft_alpha(FALL + STUCK))
		Kind.SINK:
			if reduced or _t >= FALL:
				return
			var k := clampf(_t / FALL, 0.0, 1.0)
			var at := Vector2(0, -lift * (1.0 - k * k)).round() + (drift * k).round()
			Arrow.draw_arrow(self, at, dir, true, 1.0 - k * 0.5)
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
			_ci.draw_rect(Rect2((p - half).round() - Vector2.ONE, Vector2(size + 2, size + 2)), INK)
	for i in points.size():
		_ci.draw_rect(Rect2((points[i] - half).round(), Vector2(size, size)), colours[mini(i, colours.size() - 1)])

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
			_cells([o], 5, [GOLD])
			_cells([o], 1, [WHITE], false)
		1:
			for v in CARDINAL:
				for r: float in [4.0, 6.0, 8.0, 10.0]:
					pts.append(o + v * r)
					cols.append(WHITE if r >= 10.0 else _lit(v, GOLD, AMBER))
			for v in DIAGONAL:
				pts.append(o + v.normalized() * 5.0)
				cols.append(_lit(v, GOLD, AMBER))
			_cells(pts, 2, cols)
			_cells([o], 3, [GOLD])
			_cells([o], 1, [WHITE], false)
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
## The chips a face throws: timber splinters, grey stone; none for earth, or off a solid with no face.
func _chip() -> Color:
	match face_material:
		"timber":
			return SPLINTER
		"stone":
			return STONE_CHIP
	return Color(0, 0, 0, 0)

func _draw_dust(o: Vector2, f: int, clumps: int, chip: Color) -> void:
	var splinters := chip.a > 0.0
	var side := dir.orthogonal().normalized()
	var radius: Array[float] = [3.0, 4.0, 4.0, 3.0]
	var rise: Array[float] = [0.0, 2.0, 4.0, 6.0]
	var spread: Array[float] = [3.0, 5.0, 7.0, 8.0]
	var r := radius[f] if clumps > 2 else radius[f] - 1.0
	for c in clumps:
		var across := (float(c) - float(clumps - 1) * 0.5) * spread[f]
		var centre := (o - dir * 3.0 + side * across + Vector2(0, -rise[f] - absf(across) * 0.3)).round()
		_disc(centre, r, 0.65 if f == 3 else 1.0)
	if splinters and f < 3:
		var pts := []
		var cols := []
		for s: float in [-1.0, 1.0]:
			# a chip two texels long, flying back off the face and turning as it goes
			var away := (-dir + side * s * 1.2 + Vector2(0, -0.5)).normalized()
			var at := o + away * (4.0 + 4.0 * f)
			pts.append(at)
			pts.append(at + (away.orthogonal() if f == 1 else away).round())
			cols.append(chip)
			cols.append(chip)
		_cells(pts, 1, cols)

## A round clump of dust, its upper left lit and its lower right in shade, no outline (dust is soft).
func _disc(c: Vector2, r: float, a: float) -> void:
	var n := int(ceil(r))
	for y in range(-n, n + 1):
		for x in range(-n, n + 1):
			var v := Vector2(x, y)
			if v.length() > r + 0.25:
				continue
			var stone := face_material == "stone"
			var col := STONE if stone else DUST
			if x + y <= -n:
				col = STONE_LIT if stone else DUST_LIT
			elif x + y >= n:
				col = STONE_DARK if stone else DUST_DARK
			col.a = a
			_ci.draw_rect(Rect2(c + v, Vector2.ONE), col)

## The shot breaking: a blob in its colours, then droplets flying out and falling.
func _draw_splat(o: Vector2, f: int) -> void:
	var light: Color = tint[0]
	var dark: Color = tint[1]
	var pts := []
	var cols := []
	match f:
		0:
			var blob := Rect2(o.round() - Vector2(3, 2), Vector2(7, 5))
			_ci.draw_rect(blob.grow(1.0), INK)
			_ci.draw_rect(blob, light)
			_ci.draw_rect(Rect2(blob.position + Vector2(0, 4), Vector2(7, 1)), dark)
		1:
			for i in 6:
				var v := Vector2.RIGHT.rotated(TAU * i / 6.0 + 0.3)
				pts.append(o + v * 7.0)
				cols.append(light)
			_cells(pts, 3, cols)
		2:
			for i in 6:
				var v := Vector2.RIGHT.rotated(TAU * i / 6.0 + 0.3)
				pts.append(o + v * 10.0 + Vector2(0, 1))
				cols.append(_lit(v, light, dark))
			_cells(pts, 2, cols)
		3:
			for i in 4:
				var v := Vector2.RIGHT.rotated(TAU * i / 4.0 + 0.8)
				pts.append(o + v * 12.0 + Vector2(0, 3))
				cols.append(dark)
			_cells(pts, 1, cols)

## SINK: the ring where the arrow went into the water, two texels thick, widening (still under reduced motion).
func _draw_ring() -> void:
	var t := _t if reduced or not shaft else _t - FALL
	if t < 0.0:
		return
	var k := 0.5 if reduced else clampf(t / RING, 0.0, 1.0)   # a shot's ring (no arrow) starts at once
	var rx := roundf(3.0 + 5.0 * k)
	var ry := roundf(rx * 0.5)
	var c := (drift).round()
	var a := 1.0 if reduced else 1.0 - k * 0.6
	for i in 16:
		var ang := TAU * i / 16.0
		var p := (c + Vector2(cos(ang) * rx, sin(ang) * ry)).round()
		_ci.draw_rect(Rect2(p, Vector2(2, 1)), Color(WHITE if ang > PI else FOAM, a))
