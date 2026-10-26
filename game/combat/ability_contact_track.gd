class_name AbilityContactTrack
extends RefCounted
## Presentation sequence only: the caller supplies an approved canonical duration per drawing.
## A contact is a presentation boundary, never a second damage/resource/launch command.

var _token := 0
var _clip := ""
var _facing := ""
var _aim := ""
var _frames: Array = []
var _starts: Array[float] = []
var _duration := 0.0
var _elapsed := 0.0
var _release := -1
var _entered := -1
var _cancelled := true

## Reject a missing variant or unapproved schedule without disturbing the current sequence.
## Tokens identify action instances and must increase, including after cancellation.
func configure(manifest: Dictionary, clip: String, facing: String, durations: Array,
		token: int, aim_tag: String = "") -> bool:
	if token <= _token:
		return false
	var clips: Variant = manifest.get("clips")
	if not clips is Dictionary or not clips.get(clip) is Dictionary:
		return false
	var info: Dictionary = clips[clip]
	if info.get("loop", true) != false:
		return false
	var facings: Variant = info.get("facings")
	if not facings is Dictionary or not facings.get(facing) is Dictionary:
		return false
	var selected: Dictionary = facings[facing]
	if aim_tag != "":
		var aims: Variant = selected.get("aims")
		if not aims is Dictionary or not aims.get(aim_tag) is Dictionary:
			return false
		selected = aims[aim_tag]
	var frames: Variant = selected.get("frames")
	var release: Variant = info.get("release_frame")
	if not frames is Array or frames.is_empty() or frames.size() != durations.size():
		return false
	if not _number(release) or release != floor(float(release)) or release < 0 or release >= frames.size():
		return false
	var starts: Array[float] = []
	var total := 0.0
	for index in frames.size():
		if not frames[index] is Dictionary or not frames[index].get("anchors") is Dictionary:
			return false
		var seconds: Variant = durations[index]
		if not _number(seconds) or seconds <= 0:
			return false
		starts.append(total)
		total += float(seconds)
		if not is_finite(total):
			return false
	_token = token
	_clip = clip
	_facing = facing
	_aim = aim_tag
	_frames = frames.duplicate(true)
	_starts = starts
	_duration = total
	_release = int(release)
	_elapsed = 0.0
	_entered = -1
	_cancelled = false
	return true

## Emit every newly entered drawing in order, immediately followed by contact on its drawing.
## At an exact boundary the new drawing owns the time. Coarse steps retain the contact sample
## even if sample() now shows recovery. A zero step enters drawing zero once (release zero too).
func advance(delta: float, active: bool = true) -> Array[Dictionary]:
	var events: Array[Dictionary] = []
	if _cancelled or not active or not is_finite(delta) or delta < 0:
		return events
	_elapsed = minf(_duration, _elapsed + delta)
	var index := _index_at(_elapsed)
	for next in range(_entered + 1, index + 1):
		var drawing := _sample(next)
		events.append({"kind": "drawing", "sample": drawing})
		if next == _release:
			events.append({"kind": "contact", "sample": drawing.duplicate(true)})
	_entered = index
	return events

func cancel() -> void:
	_cancelled = true

func sample() -> Dictionary:
	return {} if _cancelled else _sample(_index_at(_elapsed))

func is_finished() -> bool:
	return not _cancelled and _elapsed >= _duration

## Coordinates are authored source texels relative to the foot pivot, already screen-oriented.
## Do not mirror W, multiply by combat's factor3, add the pivot, or guess missing anchors as zero.
static func anchor(drawing: Dictionary, name: String) -> Dictionary:
	var frame: Variant = drawing.get("frame")
	if not frame is Dictionary or not frame.get("anchors") is Dictionary:
		return {}
	var point: Variant = frame.anchors.get(name)
	if not point is Array or point.size() != 2 or not _number(point[0]) or not _number(point[1]):
		return {}
	return {"offset": Vector2(float(point[0]), float(point[1]))}

func _index_at(time: float) -> int:
	var index := 0
	while index + 1 < _starts.size() and time >= _starts[index + 1]:
		index += 1
	return index

func _sample(index: int) -> Dictionary:
	return {"token": _token, "clip": _clip, "facing": _facing, "aim": _aim,
		"index": index, "starts_at": _starts[index], "frame": _frames[index].duplicate(true)}

static func _number(value: Variant) -> bool:
	return (value is float or value is int) and is_finite(float(value))
