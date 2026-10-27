class_name AbilityFormTrack
extends RefCounted
## Finite drawing-only plan playback. Every segment duration is injected explicitly.
## No template clocks, loops, state selection, contacts or simulation mutations.

var _key := ""
var _signature: Array = []
var _samples: Array[Dictionary] = []
var _starts: Array[float] = []
var _duration := 0.0
var _elapsed := 0.0
var _token := 0
var _active := false

## Validate the entire replacement before committing it. A stable key permits a
## facing/aim change at the same phase, never a different plan or implicit retime.
func configure(key: String, manifest: Dictionary, plan: Array, segment_durations: Array, token: int) -> bool:
	if key.is_empty() or token <= _token or plan.is_empty() or plan.size() != segment_durations.size():
		return false
	var samples: Array[Dictionary] = []
	var starts: Array[float] = []
	var signature: Array = []
	var total := 0.0
	for part in plan.size():
		var segment: Variant = plan[part]
		var durations: Variant = segment_durations[part]
		if not segment is Dictionary or not segment.has_all(["clip", "indices", "frames", "role", "facing", "aim"]):
			return false
		if not segment.indices is Array or not segment.frames is Array or not durations is Array or segment.indices.is_empty() or segment.indices.size() != durations.size():
			return false
		if segment.role not in ["boundary", "pose", "exit"] or segment.facing not in ["S", "N", "E", "W"]:
			return false
		for index in segment.indices:
			if not (index is int or index is float) or not is_finite(float(index)) or index < 0 or index != floor(float(index)):
				return false
		var authored := AbilityFormPlan._segment(manifest, segment, str(segment.facing), str(segment.aim))
		if authored != segment:
			return false # no forged anchors, missing variants or stale source frames
		signature.append([segment.clip, segment.role, segment.indices.duplicate(), durations.duplicate()])
		var clip_start := total
		for drawing in durations.size():
			var seconds: Variant = durations[drawing]
			if not (seconds is int or seconds is float) or not is_finite(float(seconds)) or seconds <= 0:
				return false
			starts.append(total)
			samples.append({"token": token, "clip": segment.clip, "facing": segment.facing,
				"aim": segment.aim, "index": segment.indices[drawing], "starts_at": total - clip_start,
				"frame": segment.frames[drawing].duplicate(true), "segment": part, "role": segment.role})
			total += float(seconds)
			if not is_finite(total): return false
	var same_state := _active and key == _key
	if same_state and signature != _signature:
		return false
	if not same_state: _elapsed = 0.0
	_key = key
	_signature = signature
	_samples = samples
	_starts = starts
	_duration = total
	_token = token
	_active = true
	return true

func advance(delta: float, active: bool = true) -> Dictionary:
	if not _active: return {}
	if active and is_finite(delta) and delta >= 0:
		_elapsed += minf(delta, _duration - _elapsed)
	return sample()

func sample() -> Dictionary:
	if not _active: return {}
	var index := 0
	while index + 1 < _starts.size() and _elapsed >= _starts[index + 1]: index += 1
	return _samples[index].duplicate(true)

func is_finished() -> bool:
	return _active and _elapsed >= _duration

func cancel() -> void:
	_active = false
	_key = ""
