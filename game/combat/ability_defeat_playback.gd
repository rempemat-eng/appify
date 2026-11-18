class_name AbilityDefeatPlayback
extends RefCounted
## Terminal presentation only. The provider explicitly supplies form state and clocks.
## Does not apply damage, alter canonical state, emit contacts or heal the actor.

var _timeline: Dictionary = {}
var _elapsed := 0.0
var _cursor := 0

func configure(contract: Dictionary, token: int) -> bool:
	if not contract.has_all(["id", "powered", "harpoon_out", "manifest", "facing", "segment_durations"]):
		return false
	if not contract.id is String or not contract.powered is bool or not contract.harpoon_out is bool or not contract.manifest is Dictionary or not contract.facing is String or not contract.segment_durations is Array:
		return false
	var plan := AbilityFormPlan.build(contract.id, "defeat", contract.powered,
		contract.harpoon_out, contract.manifest, contract.facing)
	var candidate := AbilityFormTrack.new()
	if not candidate.configure("defeat", contract.manifest, plan, contract.segment_durations, token):
		return false
	_timeline = candidate.timeline()
	_elapsed = 0.0
	_cursor = 0
	return true

## Include every crossed drawing, even when one tick spans the entire exit and fall.
func advance(delta: float) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if _timeline.is_empty() or not is_finite(delta) or delta < 0.0:
		return result
	var next := _elapsed + delta
	if not is_finite(next): return result
	_elapsed = next
	while _cursor < _timeline.starts.size() and _timeline.starts[_cursor] <= _elapsed + 1.0e-10:
		result.append(_timeline.samples[_cursor].duplicate(true))
		_cursor += 1
	return result

func finished() -> bool:
	return not _timeline.is_empty() and _elapsed >= float(_timeline.duration)

func held_for() -> float:
	return maxf(0.0, _elapsed - float(_timeline.duration)) if not _timeline.is_empty() else 0.0

func cancel() -> void:
	_timeline = {}
