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
## wins over the landmark. The landmark is also kept MARGIN clear of the HUD's drawn top pieces (the quest
## tracker, ui/hud.gd `top_panels`) where the camera can do that and keep the feet safe. The centre is
## then kept inside the zone's camera limits, as the phantom camera's own limit clamp keeps it.
##
## How much of that offset applies is a weight with two parts. Its target follows the feet's distance
## into the area, with a FEATHER on each side of the area's edge (0 at FEATHER outside, 1 at FEATHER
## inside), so crossing the edge moves the camera a little each step instead of all at once (the #523
## audit: up to 186 texels in one step). The weight itself moves toward that target at most 1 / EASE_TIME
## a second, so a hint that comes or goes at once (a fight starts) still eases over EASE_TIME; the offset
## is the full offset times the smoothstep of the weight. Under reduced motion the weight takes its
## target at once: walking across the feather still moves the camera with the feet, step by step, and a
## jump bigger than CUT_STEP (a block starting or ending) is a cut (`cut`, and game.gd teleports the
## camera there) in place of an ease.
##
## While the player's input is off (the raid's prepare screen), while the player is down, while a raid's
## night runs or while an enemy in the zone is awake the target is 0. During a talk the weight holds where
## it is, so a talk at the library (the bell tower's mark, the notice board) neither swings the camera
## nor cuts it twice. A door changes the zone within one call (core/zones.gd) and `attach()` drops the
## framing at once, so nothing carries over.

const PATH := "res://data/camera_frames.json"
const EASE_TIME := 0.5                      ## seconds from the plain follow to the framed one, and back
const FEATHER := 32.0                       ## texels each side of the area's edge over which the target goes 0 to 1
const CUT_STEP := 0.25                      ## under reduced motion a weight change bigger than this is a cut
const MARGIN := 12.0                        ## texels kept between the landmark and the screen's edge
const SAFE_LT := Vector2(120.0, 132.0)      ## the feet stay this far inside the left and top edges ...
const SAFE_RB := Vector2(120.0, 60.0)       ## ... and the right and bottom ones (Bramble's body is above the feet)
const CALM := ["idle", "leash", "dormant"]  ## enemy states that are not a fight (home, walking home, asleep)

var hints: Array = []       ## [{id, area: Rect2, nodes: Array}] for the current zone
var weight := 0.0           ## 0 the plain follow, 1 framed (smoothstepped on use)
var rect := Rect2()         ## the landmark rect last framed (kept while easing out)
var hint_id := ""           ## the hint last framed, "" when none

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
		if not nodes.is_empty():
			out.append({"id": String(h.get("id", "")), "area": Rect2(float(a[0]), float(a[1]), float(a[2]), float(a[3])),
				"nodes": nodes})
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
## `avoid` holds HUD rects on the picture (screen texels): when the landmark would lie under one (grown
## by MARGIN), the centre moves on one axis to the nearest place that puts it beside, below or above the
## rect, among those that keep the feet safe, the frame in the limits, the landmark on screen and clear
## of every rect; when there is none, it stays (the player first, then the limits, then the HUD).
static func fit_centre(centre: Vector2, feet: Vector2, landmark: Rect2, screen: Vector2, limits: Rect2,
		avoid: Array = []) -> Vector2:
	var half := screen / 2.0
	var c := centre
	for i in 2:
		var lo := landmark.end[i] + MARGIN - half[i]
		var hi := landmark.position[i] - MARGIN + half[i]
		c[i] = clampf(c[i], lo, hi) if lo <= hi else (lo + hi) / 2.0
		c[i] = _keep(c[i], i, feet, screen, limits)
	if avoid.is_empty() or _clear(c, landmark, screen, avoid):
		return c
	var best := c
	var best_d := INF
	for a: Variant in avoid:
		var p := (a as Rect2).grow(MARGIN)
		for cand: Vector2 in [Vector2(landmark.position.x + half.x - p.end.x, c.y),   # right of it
				Vector2(landmark.end.x + half.x - p.position.x, c.y),                    # left of it
				Vector2(c.x, landmark.position.y + half.y - p.end.y),                    # below it
				Vector2(c.x, landmark.end.y + half.y - p.position.y)]:                   # above it
			var d := cand.distance_to(c)
			if d < best_d and _clear(cand, landmark, screen, avoid) and _allowed(cand, feet, landmark, screen, limits):
				best = cand
				best_d = d
	return best

## `v` on axis `i` pulled into the feet's safe range, then into the limits.
static func _keep(v: float, i: int, feet: Vector2, screen: Vector2, limits: Rect2) -> float:
	var half := screen / 2.0
	v = clampf(v, feet[i] - half[i] + SAFE_RB[i], feet[i] + half[i] - SAFE_LT[i])
	if limits.size[i] > 0.0:
		var l0 := limits.position[i] + half[i]
		var l1 := limits.end[i] - half[i]
		v = clampf(v, l0, l1) if l0 <= l1 else (l0 + l1) / 2.0
	return v

## True when centre `c` keeps the feet safe, stays in the limits and has the landmark on screen within MARGIN.
static func _allowed(c: Vector2, feet: Vector2, landmark: Rect2, screen: Vector2, limits: Rect2) -> bool:
	for i in 2:
		if absf(_keep(c[i], i, feet, screen, limits) - c[i]) > 0.01:
			return false
	return Rect2(c - screen / 2.0, screen).grow(-MARGIN + 0.01).encloses(landmark)

## True when, with the camera centred at `c`, the landmark is MARGIN clear of every rect in `avoid`.
static func _clear(c: Vector2, landmark: Rect2, screen: Vector2, avoid: Array) -> bool:
	var on := Rect2(landmark.position - (c - screen / 2.0), landmark.size)
	for a: Variant in avoid:
		if on.intersects((a as Rect2).grow(MARGIN - 0.01)):
			return false
	return true

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

## The target weight at `feet` for an area: the feet's signed distance into it (negative outside),
## FEATHER either side of its edge mapped to 0..1.
static func feather(area: Rect2, feet: Vector2) -> float:
	var d := minf(minf(feet.x - area.position.x, area.end.x - feet.x), minf(feet.y - area.position.y, area.end.y - feet.y))
	return clampf((d + FEATHER) / (2.0 * FEATHER), 0.0, 1.0)

## The hint with the highest target at `feet` whose landmark is drawn now: {id, rect, w}, or {} for none.
func hint_at(feet: Vector2) -> Dictionary:
	var best := {}
	for h: Dictionary in hints:
		var w := feather(h.area as Rect2, feet)
		if w > 0.0 and w > float(best.get("w", 0.0)):
			var r := drawn_rect(h.nodes)
			if r.has_area():
				best = {"id": h.id, "rect": r, "w": w}
	return best

## One frame: the offset to add to the follow offset, and `cut` when reduced motion changed it at once.
## `centre` is the plain camera centre (feet plus the follow offset without framing); `avoid` the HUD's
## top pieces on the picture.
func step(delta: float, feet: Vector2, centre: Vector2, screen: Vector2, limits: Rect2, reduced: bool,
		blocked: String, avoid: Array = []) -> Dictionary:
	var want := weight              # a talk holds the weight where it is
	if blocked != "talk":
		var h := {} if blocked != "" else hint_at(feet)
		want = 0.0
		if not h.is_empty():
			rect = h.rect
			hint_id = h.id
			want = float(h.w)
	var was := weight
	weight = want if reduced else move_toward(weight, want, delta / EASE_TIME)
	var cut := reduced and absf(weight - was) > CUT_STEP
	if weight <= 0.0 or not rect.has_area():
		weight = 0.0
		rect = Rect2()
		hint_id = ""
		return {"offset": Vector2.ZERO, "cut": cut, "weight": 0.0}
	var target := fit_centre(centre, feet, rect, screen, limits, avoid) - centre
	var s := smoothstep(0.0, 1.0, weight)
	return {"offset": target * s, "cut": cut, "weight": s}
