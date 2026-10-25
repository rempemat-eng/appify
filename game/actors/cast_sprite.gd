class_name CastSprite
extends AnimatedSprite2D
## One redrawn cast member (assets/characters/<id>/, imported by tools/import_cast.py): plays
## <clip>_<facing> from its SpriteFrames, but keeps time itself from the manifest's per-drawing
## durations, so gameplay can ask which drawing is showing (release frames) and where its anchors
## are (arrow_tip, hand_R ...), in pixels from the foot pivot. Facings: S, N, E, W, each drawn
## from the same pose (west is relit, not mirrored), so flip_h is never used.

const FACINGS := ["S", "N", "E", "W"]

var manifest := {}
var clip := ""
var facing := "S"
var frame_index := 0
var clip_time := 0.0
var finished := false

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
	play_clip("idle", "S")
	return true

## Which of S, N, E, W a direction reads as (the larger axis wins; a tie faces S or N).
static func facing_for(v: Vector2, fallback := "S") -> String:
	if v.length() < 0.01:
		return fallback
	if absf(v.x) > absf(v.y):
		return "E" if v.x > 0.0 else "W"
	return "S" if v.y > 0.0 else "N"

## The unit vector a facing points along (screen space).
static func facing_vector(fc: String) -> Vector2:
	match fc:
		"E": return Vector2.RIGHT
		"W": return Vector2.LEFT
		"N": return Vector2.UP
	return Vector2.DOWN

func has_clip(name: String) -> bool:
	return manifest.get("clips", {}).has(name)

func clip_info(name: String = "") -> Dictionary:
	return manifest.clips[name if name != "" else clip]

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
	var keep_phase: bool = name == clip and bool(clip_info(name).loop) and not restart
	clip = name
	facing = fc
	animation = "%s_%s" % [name, fc]
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
	clip_time += delta
	if info.loop:
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
	return entered

## An anchor of the drawing on screen, in pixels from the foot pivot (Vector2.ZERO if absent).
func anchor(name: String, index: int = -1) -> Vector2:
	var frames: Array = clip_info().facings[facing].frames
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
