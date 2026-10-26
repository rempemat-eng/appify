class_name CastSprite
extends AnimatedSprite2D
## One redrawn cast member (assets/characters/<id>/, imported by tools/import_cast.py): plays
## <clip>_<facing> from its SpriteFrames, but keeps time itself from the manifest's per-drawing
## durations, so gameplay can ask which drawing is showing (release frames) and where its anchors
## are (arrow_tip, hand_R ...), in pixels from the foot pivot. Every facing is drawn from the same
## 3D pose (west, south-west and north-west are relit, not mirrored), so flip_h is never used.
##
## Animation contract v2 (castwork CONTRACT.md): eight facings S, SE, E, NE, N, NW, W, SW for the
## characters whose manifest lists them (Bramble and Velvet first); the others have S, N, E, W and
## a diagonal falls back to the profile on its side (manifest facing_fallback). facing_for picks the
## nearest of the eight with hysteresis. Idle fidgets: after idle has shown for a few seconds the
## sprite plays one of the manifest's idle_fidgets by itself and returns to idle (see _fidget_tick).

const FACINGS := ["S", "N", "E", "W"]
const FACINGS8 := ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
const CARDINAL := {"S": "S", "N": "N", "E": "E", "W": "W", "SE": "E", "NE": "E", "SW": "W", "NW": "W"}
const HYSTERESIS := deg_to_rad(10.0)   ## keep the current facing until the direction is this far past its sector

var manifest := {}
var clip := ""                  ## the clip asked for (idle while a fidget plays)
var facing := "S"               ## the facing asked for (may be a diagonal)
var shown_facing := "S"         ## the facing drawn: facing, or its fallback when the character has only four
var playing := ""               ## the clip drawn: clip, or the fidget playing in its place
var frame_index := 0
var clip_time := 0.0
var finished := false
var fidgets_enabled := true

var _idle_t := 0.0              ## seconds idle has shown without a break
var _next_fidget := 0.0
var _last_fidget := ""

## Loads a character; false when its folder is missing.
func load_character(id: String) -> bool:
	var path := "res://assets/characters/%s/" % id
	var f := FileAccess.open(path + "manifest.json", FileAccess.READ)
	if f == null:
		push_error("CastSprite: no manifest for %s" % id)
		return false
	manifest = JSON.parse_string(f.get_as_text())
	sprite_frames = load(path + "frames.tres")
	centered = false
	var pivot: Array = manifest.foot_pivot
	offset = -Vector2(pivot[0], pivot[1])
	stop()                     # timing comes from advance(), not the player's own clock
	clip = ""
	_reset_idle_clock()
	play_clip("idle", "S")
	return true

## Which of the eight facings a direction reads as (the nearest; ties go to the cardinal).
## `fallback` is the current facing: it is kept for a zero direction, and while the direction is
## within its sector plus HYSTERESIS, so the facing does not flicker on a boundary.
static func facing_for(v: Vector2, fallback := "S") -> String:
	if v.length() < 0.01:
		return fallback
	var a := v.angle()
	if FACINGS8.has(fallback) and absf(angle_difference(a, facing_vector(fallback).angle())) <= PI / 8.0 + HYSTERESIS:
		return fallback
	return _nearest(a)

static func _nearest(a: float) -> String:
	var best := "S"
	var bd := INF
	for fc in FACINGS8:
		var d := absf(angle_difference(a, facing_vector(fc).angle()))
		if d < bd - 0.0001 or (absf(d - bd) <= 0.0001 and fc.length() == 1):
			bd = d
			best = fc
	return best

## The unit vector a facing points along (screen space).
static func facing_vector(fc: String) -> Vector2:
	match fc:
		"E": return Vector2.RIGHT
		"W": return Vector2.LEFT
		"N": return Vector2.UP
		"SE": return Vector2(1, 1).normalized()
		"SW": return Vector2(-1, 1).normalized()
		"NE": return Vector2(1, -1).normalized()
		"NW": return Vector2(-1, -1).normalized()
	return Vector2.DOWN

## The facing this character draws for `fc`: itself when its manifest has it, else the fallback.
func resolve_facing(fc: String) -> String:
	var dirs: Array = manifest.get("directions", FACINGS)
	if dirs.has(fc):
		return fc
	var fb: Dictionary = manifest.get("facing_fallback", CARDINAL)
	return String(fb.get(fc, CARDINAL.get(fc, "S")))

func has_clip(name: String) -> bool:
	return manifest.get("clips", {}).has(name)

func clip_info(name: String = "") -> Dictionary:
	return manifest.clips[name if name != "" else playing]

func duration(name: String = "") -> float:
	return float(clip_info(name).duration)

func release_frame(name: String = "") -> int:
	var r = clip_info(name).get("release_frame")
	return -1 if r == null else int(r)

func walk_speed() -> float:
	var s = manifest.get("walk_speed")
	return 0.0 if s == null else float(s)

## Starts a clip in a facing. Restarting the same clip and facing is a no-op unless restart.
func play_clip(name: String, fc: String, restart := false) -> void:
	if name == clip and fc == facing and not restart:
		return
	var keep_phase: bool = name == clip and playing == clip and bool(clip_info(name).loop) and not restart
	if name != clip or restart or playing != clip:
		_reset_idle_clock()
	clip = name
	playing = name
	facing = fc
	shown_facing = resolve_facing(fc)
	animation = "%s_%s" % [name, shown_facing]
	if not keep_phase:          # turning while walking keeps the stride phase
		clip_time = 0.0
		finished = false
	_sync()

## Advances the clip; returns the drawings entered during this step (for release events).
func advance(delta: float) -> Array[int]:
	var entered: Array[int] = []
	var info := clip_info()
	var total := float(info.duration)
	var before := frame_index
	var wrapped := false
	clip_time += delta
	if info.loop:
		wrapped = clip_time >= total
		clip_time = fmod(clip_time, total)
	elif clip_time >= total:
		clip_time = total
		finished = true
	_sync()
	if frame_index != before:
		var n: int = info.frame_count
		var i := before
		while i != frame_index:
			i = (i + 1) % n
			entered.append(i)
	_fidget_tick(delta, wrapped)
	return entered

## Idle fidgets (CONTRACT V2.5): after `after` seconds of idle, at idle drawing 0, play one fidget
## (random, never the same twice running), then idle again; the next after a random `every` span.
## A fidget starts and ends on idle drawing 0, so neither cut pops. Any play_clip cancels it.
func _fidget_tick(delta: float, wrapped: bool) -> void:
	var cfg: Dictionary = manifest.get("idle_fidgets", {})
	if cfg.is_empty() or not fidgets_enabled or clip != "idle":
		return
	if playing != "idle":                       # a fidget is playing: back to idle at its end
		if finished:
			playing = "idle"
			animation = "idle_%s" % shown_facing
			clip_time = 0.0
			finished = false
			_idle_t = 0.0
			_next_fidget = _rand_every(cfg)
			_sync()
		return
	_idle_t += delta
	if _idle_t >= _next_fidget and wrapped:
		var pool: Array = cfg.get("clips", []).filter(func(c): return c != _last_fidget and has_clip(c))
		if pool.is_empty():
			return
		var pick: String = pool[randi() % pool.size()]
		_last_fidget = pick
		playing = pick
		animation = "%s_%s" % [pick, shown_facing]
		clip_time = 0.0
		finished = false
		_sync()

func is_fidgeting() -> bool:
	return clip == "idle" and playing != "idle"

func _reset_idle_clock() -> void:
	_idle_t = 0.0
	_next_fidget = float(manifest.get("idle_fidgets", {}).get("after", 4.0))

func _rand_every(cfg: Dictionary) -> float:
	var e: Array = cfg.get("every", [6.0, 10.0])
	return randf_range(float(e[0]), float(e[1]))

## An anchor of the drawing on screen, in pixels from the foot pivot (Vector2.ZERO if absent).
func anchor(name: String, index: int = -1) -> Vector2:
	var frames: Array = clip_info().facings[shown_facing].frames
	var fr: Dictionary = frames[frame_index if index < 0 else index]
	var a = fr.anchors.get(name)
	return Vector2.ZERO if a == null else Vector2(a[0], a[1])

func _sync() -> void:
	var durs: Array = clip_info().durations
	var t := 0.0
	frame_index = durs.size() - 1
	for i in durs.size():
		t += float(durs[i])
		if clip_time < t - 0.00001:
			frame_index = i
			break
	frame = frame_index
