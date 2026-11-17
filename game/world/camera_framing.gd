class_name CameraFraming
extends RefCounted
## Frames a tall landmark whole while the player stands near it. The library's bell cupola in Crossroads
## (Matt, 13 Nov, decision (d): "bell tower optional, cupola drawn", so that paying visibly changes the
## square) stood above the top of the picture from everywhere in the square: the camera follows Bramble
## 8 world px above the feet, and the cupola's top is 365 texels above the library's door.
##
## A landmark opts in with a hint in data/camera_frames.json, by zone: an `area` (texels) where the hint
## holds and `frame`, the zone scene's paths of the pictures that must fit on screen. The hint holds only
## while at least one of those pictures is drawn (a Conditional can hide them), and its rect is the union
## of the drawn ones.
##
## Near the area game.gd adds `step()`'s offset to the phantom camera's follow offset (the same channel
## the aim look-ahead and the hit shake use), so the camera's centre moves just far enough to fit the rect
## inside MARGIN, and never so far that the feet leave the SAFE insets of the screen: the player always
## wins over the landmark. The centre is then kept inside the zone's camera limits, as the phantom
## camera's own limit clamp keeps it. Last, the centre x is held at or west of one bound that keeps the
## landmark MARGIN right of the HUD's top-left pieces (the quest tracker, ui/hud.gd `top_panels`):
## `hud_cap_x`, one continuous bound on one axis, so it only holds back the look-ahead to the east (the
## #523 audits: the cupola went under the tracker, and then a choice between beside and below flipped).
##
## How much of the fit applies is a weight. Its target is 1 inside the hint's area and falls linearly to
## 0 over a feather outside each side (`feather`: west, north, east, south), so crossing the edge moves
## the camera a little each step instead of all at once (the first audit: 186 texels in one step). The
## weight moves toward that target at most 1 / EASE_TIME a second, so a hint that comes or goes at once
## (a fight starts) still eases over EASE_TIME; the offset is the fit's times the weight (linear, so a
## crossing moves the camera at an even rate), and the HUD bound comes in with the weight and holds in
## full from CAP_FULL. Under reduced motion the weight takes its target at once: walking across the feather moves the camera with the
## feet, and a jump bigger than CUT_STEP, or a block starting or ending while framed, is a cut (`cut`,
## and game.gd teleports the camera there) in place of an ease.
##
## While the player's input is off (the raid's prepare screen), while the player is down, while a raid's
## night runs or while an enemy in the zone is awake the target is 0. During a talk the weight holds where
## it is, so a talk at the library (the bell tower's mark, the notice board) neither swings the camera
## nor cuts it twice. A door changes the zone within one call (core/zones.gd) and `attach()` drops the
## framing at once, so nothing carries over.

const PATH := "res://data/camera_frames.json"
const EASE_TIME := 0.5                      ## seconds from the plain follow to the framed one, and back
const FEATHER := 64.0                       ## texels outside the area's edge over which the target falls to 0 (default)
const CUT_STEP := 0.25                      ## under reduced motion a weight change bigger than this is a cut
const CAP_FULL := 0.5                       ## the HUD bound holds in full from this weight up (linear from 0)
const MARGIN := 12.0                        ## texels kept between the landmark and the screen's edge
const SAFE_LT := Vector2(120.0, 132.0)      ## the feet stay this far inside the left and top edges ...
const SAFE_RB := Vector2(120.0, 60.0)       ## ... and the right and bottom ones (Bramble's body is above the feet)
const CALM := ["idle", "leash", "dormant"]  ## enemy states that are not a fight (home, walking home, asleep)

var hints: Array = []       ## [{id, area: Rect2, nodes: Array}] for the current zone
var weight := 0.0           ## 0 the plain follow, 1 framed
var rect := Rect2()         ## the landmark rect last framed (kept while easing out)
var hint_id := ""           ## the hint last framed, "" when none
var _blocked := ""          ## the block of the last step, talks left out (a talk holds the weight)

## The hints of `zone` from `defs` (data/camera_frames.json parsed), with their nodes found.
static func hints_for(zone: Node, defs: Dictionary) -> Array:
	var out: Array = []
	if zone == null or not "zone_id" in zone:
		return out
	for h: Dictionary in defs.get(String(zone.zone_id), []):
		var a: Array = h.get("area", [])
		if a.size() != 4:
			continue
		var nodes: Array = []
		for p: String in h.get("frame", []):
			var n := zone.get_node_or_null(NodePath(p)) as CanvasItem
			if n != null:
				nodes.append(n)
		var fe: Array = h.get("feather", [FEATHER, FEATHER, FEATHER, FEATHER])
		if not nodes.is_empty() and fe.size() == 4:
			out.append({"id": String(h.get("id", "")), "area": Rect2(float(a[0]), float(a[1]), float(a[2]), float(a[3])),
				"feather": [float(fe[0]), float(fe[1]), float(fe[2]), float(fe[3])], "nodes": nodes})
	return out

static func load_defs() -> Dictionary:
	if not FileAccess.file_exists(PATH):
		return {}
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	return d if d is Dictionary else {}

## The union of the drawn pictures among `nodes` (Sprite2D, in global texels); an empty Rect2 when none is drawn.
static func drawn_rect(nodes: Array) -> Rect2:
	var r := Rect2()
	var any := false
	for n: Variant in nodes:
		if not is_instance_valid(n):
			continue
		var s := n as Sprite2D
		if s == null or not s.is_inside_tree() or not s.is_visible_in_tree() or s.texture == null:
			continue
		var g: Rect2 = s.get_global_transform() * s.get_rect()
		r = g if not any else r.merge(g)
		any = true
	return r if any else Rect2()

## The camera centre that fits `landmark` on a `screen`-sized frame, starting from the plain centre
## `centre`, keeping `feet` inside the safe insets and the frame inside `limits` (all in texels).
## Each axis: the nearest centre to `centre` that fits the landmark with MARGIN (its middle when it is
## bigger than the screen), then pulled back into the feet's safe range, then into the limits.
static func fit_centre(centre: Vector2, feet: Vector2, landmark: Rect2, screen: Vector2, limits: Rect2) -> Vector2:
	var half := screen / 2.0
	var c := centre
	for i in 2:
		var lo := landmark.end[i] + MARGIN - half[i]
		var hi := landmark.position[i] - MARGIN + half[i]
		c[i] = clampf(c[i], lo, hi) if lo <= hi else (lo + hi) / 2.0
		c[i] = _keep(c[i], i, feet, screen, limits)
	return c

## The highest camera centre x that keeps `landmark` MARGIN to the right of every HUD rect in `avoid` on
## the left half of the picture (the quest tracker, the meters): INF when there is none. One continuous
## bound on one axis: it moves with the panels' right edge (a wider tracker, a pixel at a time) and only
## ever holds back the look-ahead to the east. Rows are not compared: a wrap that makes the tracker taller
## changes nothing, and the bound holds wherever the landmark is drawn.
static func hud_cap_x(landmark: Rect2, screen: Vector2, avoid: Array) -> float:
	var cap := INF
	for a: Variant in avoid:
		var r := a as Rect2
		if r.position.x < screen.x / 2.0:
			cap = minf(cap, landmark.position.x + screen.x / 2.0 - (r.end.x + MARGIN))
	return cap

## `v` on axis `i` pulled into the feet's safe range, then into the limits.
static func _keep(v: float, i: int, feet: Vector2, screen: Vector2, limits: Rect2) -> float:
	var half := screen / 2.0
	v = clampf(v, feet[i] - half[i] + SAFE_RB[i], feet[i] + half[i] - SAFE_LT[i])
	if limits.size[i] > 0.0:
		var l0 := limits.position[i] + half[i]
		var l1 := limits.end[i] - half[i]
		v = clampf(v, l0, l1) if l0 <= l1 else (l0 + l1) / 2.0
	return v

## Why framing may not apply now ("" when it may): a talk, the input off, downed, a raid's night, a fight.
## `enemy_states` holds the state of each live enemy in the zone.
static func block_reason(talk: bool, input_on: bool, downed: bool, raid_night: bool, enemy_states: Array) -> String:
	if talk:
		return "talk"
	if not input_on:
		return "input off"
	if downed:
		return "downed"
	if raid_night:
		return "raid"
	for st: Variant in enemy_states:
		if not String(st) in CALM:
			return "fight"
	return ""

## The block reason of the running game for `player` in the current zone.
static func game_block_reason(player: Node2D) -> String:
	var states: Array = []
	for e in player.get_tree().get_nodes_in_group("enemy"):
		# the Thornback (bosses/thornback.gd) has no `dead` as the other enemies have, so only a true value
		# counts; a node in the group with no `state` is not a fight
		var st: Variant = e.get("state")
		if st != null and e.is_inside_tree() and e.get("dead") != true and Zones.current != null \
				and is_instance_valid(Zones.current) and Zones.current.is_ancestor_of(e):
			states.append(str(st))
	var input_on: bool = player.get("input_enabled") != false
	var downed: bool = player.has_method("is_defeated") and player.is_defeated()
	return block_reason(Dialogue.busy, input_on, downed, Raids.running(), states)

func attach(zone: Node, defs: Dictionary = {}) -> void:
	hints = hints_for(zone, defs if not defs.is_empty() else load_defs())
	weight = 0.0
	rect = Rect2()
	hint_id = ""

## The target weight at `feet` for an area: 1 inside it, falling linearly to 0 over the feather outside
## each side (`fe`: west, north, east, south, texels); the lower of the two axes at a corner.
static func feather(area: Rect2, feet: Vector2, fe: Array = [FEATHER, FEATHER, FEATHER, FEATHER]) -> float:
	var wx := 1.0
	if feet.x < area.position.x:
		wx = 1.0 - (area.position.x - feet.x) / maxf(float(fe[0]), 1.0)
	elif feet.x > area.end.x:
		wx = 1.0 - (feet.x - area.end.x) / maxf(float(fe[2]), 1.0)
	var wy := 1.0
	if feet.y < area.position.y:
		wy = 1.0 - (area.position.y - feet.y) / maxf(float(fe[1]), 1.0)
	elif feet.y > area.end.y:
		wy = 1.0 - (feet.y - area.end.y) / maxf(float(fe[3]), 1.0)
	return clampf(minf(wx, wy), 0.0, 1.0)

## The hint with the highest target at `feet` whose landmark is drawn now: {id, rect, w}, or {} for none.
func hint_at(feet: Vector2) -> Dictionary:
	var best := {}
	for h: Dictionary in hints:
		var w := feather(h.area as Rect2, feet, h.get("feather", [FEATHER, FEATHER, FEATHER, FEATHER]))
		if w > 0.0 and w > float(best.get("w", 0.0)):
			var r := drawn_rect(h.nodes)
			if r.has_area():
				best = {"id": h.id, "rect": r, "w": w}
	return best

## One frame: the offset to add to the follow offset, and `cut` when reduced motion changed it at once.
## `centre` is the plain camera centre (feet plus the follow offset without framing); `avoid` the HUD's
## top pieces on the picture. The offset is the fit's times the weight; then the centre x
## is held at or west of the HUD bound (hud_cap_x), the bound coming in linearly with the weight up to
## CAP_FULL, so from that weight up the landmark is clear of the tracker however far the fit has come,
## and below it the bound fades (no snap when the weight first rises from 0, where the plain follow has
## the landmark wherever it is on main). The bound never moves the feet out of their safe range or the
## frame out of the limits.
func step(delta: float, feet: Vector2, centre: Vector2, screen: Vector2, limits: Rect2, reduced: bool,
		blocked: String, avoid: Array = []) -> Dictionary:
	var want := weight              # a talk holds the weight where it is
	var block_changed := false
	if blocked != "talk":
		block_changed = blocked != _blocked
		_blocked = blocked
		var h := {} if blocked != "" else hint_at(feet)
		want = 0.0
		if not h.is_empty():
			rect = h.rect
			hint_id = h.id
			want = float(h.w)
	var was := weight
	weight = want if reduced else move_toward(weight, want, delta / EASE_TIME)
	# under reduced motion a block that starts or ends while framed is a cut, as is any other jump
	var cut := reduced and (absf(weight - was) > CUT_STEP or (block_changed and maxf(weight, was) > 0.0))
	if weight <= 0.0 or not rect.has_area():
		weight = 0.0
		rect = Rect2()
		hint_id = ""
		return {"offset": Vector2.ZERO, "cut": cut, "weight": 0.0}
	var s := weight      # linear: the feather's own ramp, so crossing it moves the camera at an even rate
	var off := (fit_centre(centre, feet, rect, screen, limits) - centre) * s
	var cap := hud_cap_x(rect, screen, avoid)
	var cx := centre.x + off.x
	if cx > cap:
		var floor_x := _keep(-INF, 0, feet, screen, limits)     # the westmost centre the feet and limits allow
		var held := maxf(cap, floor_x)
		if cx > held:
			off.x -= (cx - held) * clampf(weight / CAP_FULL, 0.0, 1.0)
	return {"offset": off, "cut": cut, "weight": s}
