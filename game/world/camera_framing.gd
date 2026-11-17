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
## While the player's feet are in the area, game.gd adds `step()`'s offset to the phantom camera's
## follow offset (the same channel the aim look-ahead and the hit shake use), so the camera's centre
## moves just far enough to fit the rect inside MARGIN, and never so far that the feet leave the SAFE
## insets of the screen: the player always wins over the landmark. The centre is then kept inside the
## zone's camera limits, as the phantom camera's own limit clamp keeps it. The offset eases in and out
## over EASE_TIME with a smoothstep, a finite move; under reduced motion it cuts (`cut` is true on the
## step where it changes, and game.gd teleports the camera there). It never applies while a talk is
## open, while the player's input is off (the raid's prepare screen), while the player is down, while a
## raid's night runs or while an enemy in the zone is awake: those ease it out. A door changes the zone
## within one call (core/zones.gd) and `attach()` drops the framing at once, so nothing carries over.

const PATH := "res://data/camera_frames.json"
const EASE_TIME := 0.5                      ## seconds from the plain follow to the framed one, and back
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
static func fit_centre(centre: Vector2, feet: Vector2, landmark: Rect2, screen: Vector2, limits: Rect2) -> Vector2:
	var half := screen / 2.0
	var c := centre
	for i in 2:
		var lo := landmark.end[i] + MARGIN - half[i]
		var hi := landmark.position[i] - MARGIN + half[i]
		c[i] = clampf(c[i], lo, hi) if lo <= hi else (lo + hi) / 2.0
		c[i] = clampf(c[i], feet[i] - half[i] + SAFE_RB[i], feet[i] + half[i] - SAFE_LT[i])
		if limits.size[i] > 0.0:
			var l0 := limits.position[i] + half[i]
			var l1 := limits.end[i] - half[i]
			c[i] = clampf(c[i], l0, l1) if l0 <= l1 else (l0 + l1) / 2.0
	return c

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

## The hint whose area holds `feet` and whose landmark is drawn now: {id, rect}, or {} for none.
func hint_at(feet: Vector2) -> Dictionary:
	for h: Dictionary in hints:
		if (h.area as Rect2).has_point(feet):
			var r := drawn_rect(h.nodes)
			if r.has_area():
				return {"id": h.id, "rect": r}
	return {}

## One frame: the offset to add to the follow offset, and `cut` when reduced motion changed it at once.
## `centre` is the plain camera centre (feet plus the follow offset without framing).
func step(delta: float, feet: Vector2, centre: Vector2, screen: Vector2, limits: Rect2, reduced: bool,
		blocked: String) -> Dictionary:
	var h := {} if blocked != "" else hint_at(feet)
	if not h.is_empty():
		rect = h.rect
		hint_id = h.id
	var want := 0.0 if h.is_empty() else 1.0
	var was := weight
	weight = want if reduced else move_toward(weight, want, delta / EASE_TIME)
	if weight <= 0.0:
		rect = Rect2()
		hint_id = ""
		return {"offset": Vector2.ZERO, "cut": reduced and was != weight, "weight": 0.0}
	var target := fit_centre(centre, feet, rect, screen, limits) - centre
	var s := smoothstep(0.0, 1.0, weight)
	return {"offset": target * s, "cut": reduced and was != weight, "weight": s}
