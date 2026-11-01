class_name CastSprite
extends AnimatedSprite2D
## One redrawn cast member (assets/characters/<id>/, imported by tools/import_cast.py): plays
## <clip>_<facing> from its SpriteFrames, but keeps time itself from the manifest's per-drawing
## durations, so gameplay can ask which drawing is showing (release frames) and where its anchors
## are (arrow_tip, hand_R ...), in pixels from the foot pivot. Every facing is drawn from the same
## 3D pose (west, south-west and north-west are relit, not mirrored), so flip_h is never used.
##
## Animation contract v2 (castwork CONTRACT.md): the body has four facings S, N, E, W (Matt, 26 Oct:
## "4 directions if its smooth enough ... like eastward"); facing_for picks the nearest with
## hysteresis. Weapon clips (manifest aim_clips) are also drawn at aims within the facing, every
## 22.5 degrees: play_clip shows <clip>_<F>_<tag> for the aim set by set_aim (or read from the
## parent's _shot_dir / aim), and anchor() reads that aim's drawings, so a projectile leaves from
## the aimed arrow tip. Turns are smooth (Matt, 26 Oct, after Eastward's gameplay): a facing change
## shows the stored three-quarter drawing between the two facings (manifest turn_inbetweens) for a
## short beat, keeping the drawing index and clip time, and a weapon's aim steps through the aims
## in between instead of jumping (see _turn_to, _ease_aim). A manifest with eight directions
## (stored 3/4 work) still plays them. Idle
## fidgets: after idle has shown for a few seconds the sprite plays one of the manifest's
## idle_fidgets by itself and returns to idle (see _fidget_tick).

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
var aim_vector := Vector2.ZERO  ## the weapon's aim (screen space); zero = read it from the parent
var aim_tag := ""               ## the aim drawn within the facing ("" when the clip has no aims)

var turn_path: Array[String] = []   ## in-between facings still to show before `shown_facing`
var _turn_t := 0.0
var _turn_step := 0.07           ## the hold of each in-between of the current turn
var _aim_t := 0.0

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

## Which of S, N, E, W a direction reads as (the nearest; a tie goes to S or N). `fallback` is the
## current facing: it is kept for a zero direction, and while the direction is within its quarter
## plus HYSTERESIS, so the facing does not flicker on a boundary. (8-facing manifests: facing_for8.)
static func facing_for(v: Vector2, fallback := "S") -> String:
	if v.length() < 0.01:
		return fallback
	var a := v.angle()
	if FACINGS.has(fallback) and absf(angle_difference(a, facing_vector(fallback).angle())) <= PI / 4.0 + HYSTERESIS:
		return fallback
	return _nearest(a, FACINGS)

static func facing_for8(v: Vector2, fallback := "S") -> String:
	if v.length() < 0.01:
		return fallback
	var a := v.angle()
	if FACINGS8.has(fallback) and absf(angle_difference(a, facing_vector(fallback).angle())) <= PI / 8.0 + HYSTERESIS:
		return fallback
	return _nearest(a, FACINGS8)

static func _nearest(a: float, set: Array) -> String:
	var best := "S"
	var bd := INF
	for fc in set:
		var d := absf(angle_difference(a, facing_vector(fc).angle()))
		if d < bd - 0.0001 or (absf(d - bd) <= 0.0001 and (fc == "S" or fc == "N")):
			bd = d
			best = fc
	return best

## The weapon's aim for the next weapon clip (screen space). Zero: read the parent's.
func set_aim(v: Vector2) -> void:
	aim_vector = v

func _aim_now() -> Vector2:
	if aim_vector.length() > 0.01:
		return aim_vector
	var p := get_parent()
	if p != null and "_shot_dir" in p and p.has_method("is_shooting") and bool(p.call("is_shooting")):
		return p.get("_shot_dir")
	if p != null and "aim" in p:
		return p.get("aim")
	return facing_vector(shown_facing)

## The aim tag within the facing nearest the direction v (the facing's aims), "" without aims.
func aim_tag_for(name: String, fc: String, v: Vector2) -> String:
	var fe: Dictionary = clip_info(name).facings.get(fc, {})
	var aims: Dictionary = fe.get("aims", {})
	if aims.is_empty():
		return ""
	var rel := rad_to_deg(angle_difference(facing_vector(fc).angle(), v.angle()))
	var best := ""
	var bd := INF
	for tag in aims:
		var d := absf(float(aims[tag].deg) - rel)
		if d < bd:
			bd = d
			best = tag
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
	var before := shown_facing
	var had_clip := clip != ""
	clip = name
	playing = name
	facing = fc
	shown_facing = resolve_facing(fc)
	aim_tag = aim_tag_for(name, shown_facing, _aim_now())
	_aim_t = 0.0
	turn_path.clear()
	if had_clip and has_turns(name):
		turn_path = turn_steps(before, shown_facing, _turn_hint())
	_turn_step = _turn_hold()
	_turn_t = _turn_step
	if not keep_phase:          # turning while walking keeps the stride phase
		clip_time = 0.0
		finished = false
	_show()
	_sync()

## The animation for the current state: an in-between facing while turning, else the facing (and
## the weapon's aim within it).
func _show() -> void:
	if not turn_path.is_empty():
		animation = "%s_%s" % [playing, turn_path[0]]
	elif aim_tag != "":
		animation = "%s_%s_%s" % [playing, shown_facing, aim_tag]
	else:
		animation = "%s_%s" % [playing, shown_facing]

## True when the clip has the turn in-betweens (manifest turn_inbetweens; contract V2.9).
func has_turns(name: String) -> bool:
	return has_clip(name) and clip_info(name).has("turns")

## The facings shown on the way from `from` to `to` (both of S N E W), not counting `to`: the
## three-quarter drawing between them for a quarter turn; for a reversal the side the input `hint`
## rotates toward (the S side when it gives none): diagonal, the cardinal between, diagonal.
static func turn_steps(from: String, to: String, hint := Vector2.ZERO) -> Array[String]:
	var out: Array[String] = []
	if from == to or not FACINGS.has(from) or not FACINGS.has(to):
		return out
	var a := facing_vector(from)
	var b := facing_vector(to)
	if absf(a.dot(b)) < 0.5:                        # a quarter turn
		out.append(_nearest((a + b).angle(), FACINGS8))
		return out
	var s := signf(a.cross(hint)) if hint.length() > 0.01 else 0.0
	if s == 0.0:                                    # an exact reversal: through the S side (E, W) or E (N, S)
		s = signf(a.cross(Vector2.DOWN)) if from == "E" or from == "W" else (1.0 if from == "N" else -1.0)
	var mid := a.rotated(s * PI / 2.0)
	out.append(_nearest((a + mid).angle(), FACINGS8))
	out.append(_nearest(mid.angle(), FACINGS))
	out.append(_nearest((mid + b).angle(), FACINGS8))
	return out

func _turn_hold() -> float:
	var ti: Dictionary = manifest.get("turn_inbetweens", {})
	return float(ti.get("hold_180" if turn_path.size() > 1 else "hold", 0.07))

## Which way the input points when the facing changes (the parent's movement, else its aim).
func _turn_hint() -> Vector2:
	var p := get_parent()
	if p != null and "velocity" in p:
		var v: Vector2 = p.get("velocity")
		if v.length() > 1.0:
			return v
	return _aim_now()

## Advances the clip; returns the drawings entered during this step (for release events).
func advance(delta: float) -> Array[int]:
	var entered: Array[int] = []
	var info := clip_info()
	var total := float(info.duration)
	var before := frame_index
	var wrapped := false
	clip_time += delta
	_turn_tick(delta)
	_ease_aim(delta)
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

func _turn_tick(delta: float) -> void:
	if turn_path.is_empty():
		return
	_turn_t -= delta
	while _turn_t <= 0.0 and not turn_path.is_empty():
		turn_path.pop_front()
		_turn_t += _turn_step
	_show()

## A weapon clip whose aim changes mid-clip steps one aim per manifest aim_step toward it.
func _ease_aim(delta: float) -> void:
	if aim_tag == "" or playing != clip:
		return
	var target := aim_tag_for(clip, shown_facing, _aim_now())
	if target == aim_tag or target == "":
		_aim_t = 0.0
		return
	_aim_t += delta
	var step := float(manifest.get("turn_inbetweens", {}).get("aim_step", 0.04))
	if _aim_t < step:
		return
	_aim_t = 0.0
	var aims: Dictionary = clip_info().facings[shown_facing].get("aims", {})
	var cur := float(aims[aim_tag].deg)
	var goal := float(aims[target].deg)
	var best := aim_tag
	var bd := INF
	for tag in aims:                                # the next aim from the current one toward the goal
		var d := float(aims[tag].deg)
		if (d - cur) * (goal - cur) > 0.0 and absf(d - cur) < bd:
			bd = absf(d - cur)
			best = tag
	aim_tag = best
	_show()

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
			aim_tag = ""
			_show()
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
		aim_tag = ""
		turn_path.clear()
		_show()
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
	var fe: Dictionary = clip_info().facings[shown_facing]
	var frames: Array = fe.aims[aim_tag].frames if aim_tag != "" and fe.has("aims") else fe.frames
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
