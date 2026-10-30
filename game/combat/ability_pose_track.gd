class_name AbilityPoseTrack
extends RefCounted
## Drawing-only timeline for explicitly selected locomotion, guard and form poses.
## The caller owns state/clip selection and approved durations. No contact or combat events.

var _key := ""
var _clip := ""
var _facing := ""
var _aim := ""
var _frames: Array = []
var _starts: Array[float] = []
var _durations: Array = []
var _duration := 0.0
var _elapsed := 0.0
var _loop := false
var _active := false
var _token := 0

## A new state key restarts at drawing zero. Facing/aim changes in the same state
## retain phase only when clip, loop rule and approved durations remain identical.
## Invalid replacement never disturbs a valid sequence or consumes its token.
func configure(key: String, manifest: Dictionary, clip: String, facing: String,
		durations: Array, token: int, aim: String = "") -> bool:
	if key.is_empty() or token <= _token:
		return false
	var clips: Variant = manifest.get("clips")
	if not clips is Dictionary:
		return false
	var info: Variant = clips.get(clip)
	if not info is Dictionary or not info.get("loop") is bool:
		return false
	var facings: Variant = info.get("facings")
	if not facings is Dictionary:
		return false
	var selected: Variant = facings.get(facing)
	if not selected is Dictionary:
		return false
	if aim != "":
		var aims: Variant = selected.get("aims")
		if not aims is Dictionary:
			return false
		selected = aims.get(aim)
		if not selected is Dictionary:
			return false
	var frames: Variant = selected.get("frames")
	if not frames is Array or frames.is_empty() or frames.size() != durations.size():
		return false
	var starts: Array[float] = []
	var total := 0.0
	for index in frames.size():
		if not frames[index] is Dictionary or not frames[index].get("anchors") is Dictionary:
			return false
		var seconds: Variant = durations[index]
		if not (seconds is int or seconds is float) or not is_finite(float(seconds)) or seconds <= 0:
			return false
		starts.append(total)
		total += float(seconds)
		if not is_finite(total):
			return false
	var same_state := _active and key == _key
	if same_state and (clip != _clip or info.loop != _loop or durations != _durations):
		return false # a state transition needs a new key; never retime the live state
	if not same_state:
		_elapsed = 0.0
	_key = key
	_clip = clip
	_facing = facing
	_aim = aim
	_frames = frames.duplicate(true)
	_starts = starts
	_durations = durations.duplicate(true)
	_duration = total
	_loop = info.loop
	_token = token
	_active = true
	return true

## Passive poses need only the current drawing; skipped loops never replay contacts.
## Finite exits hold their last drawing until the caller explicitly changes state.
func advance(delta: float, active: bool = true) -> Dictionary:
	if not _active:
		return {}
	if active and is_finite(delta) and delta >= 0:
		# Reduce the delta before addition to avoid overflow on long coarse steps.
		if _loop:
			var remainder := fmod(delta, _duration)
			var until_wrap := _duration - _elapsed
			_elapsed = remainder - until_wrap if remainder >= until_wrap else _elapsed + remainder
		else:
			_elapsed += minf(delta, _duration - _elapsed)
	return sample()

func sample() -> Dictionary:
	if not _active:
		return {}
	var index := 0
	while index + 1 < _starts.size() and _elapsed >= _starts[index + 1]:
		index += 1
	return {"token": _token, "clip": _clip, "facing": _facing, "aim": _aim,
		"index": index, "starts_at": _starts[index], "frame": _frames[index].duplicate(true)}

func is_finished() -> bool:
	return _active and not _loop and _elapsed >= _duration

func cancel() -> void:
	_active = false
	_key = ""
