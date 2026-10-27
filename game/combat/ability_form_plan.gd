class_name AbilityFormPlan
extends RefCounted
## Explicit, drawing-only form selection. No clocks, canonical state or combat events.
## Segments name exact authored drawing indices; a separate approved schedule must bind them.

const POSES := ["idle", "walk", "primary", "secondary", "special", "guard", "hit", "defeat", "jump", "dodge", "stair_up", "stair_down"]

## harpoon_out is supplied by the runner, never guessed from ammo/tether/animation.
## Powered actions enter/leave through powered_idle 0. Defeat instead exits via 0..3.
static func build(id: String, pose: String, powered: bool, harpoon_out: bool,
		manifest: Dictionary, facing: String, aim: String = "") -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if id != manifest.get("id") or pose not in POSES or facing not in ["S", "N", "E", "W"]:
		return result
	var empty := "_empty" if id == "brine" and harpoon_out else ""
	var clip := pose + empty
	if powered and pose != "special" and pose != "defeat":
		clip = "powered_" + clip
	var requests: Array[Dictionary] = []
	if powered and pose == "defeat":
		requests.append({"clip": "powered_exit" + empty, "indices": [0, 1, 2, 3], "role": "exit"})
	elif powered and pose not in ["idle", "special"]:
		requests.append({"clip": "powered_idle" + empty, "indices": [0], "role": "boundary"})
	requests.append({"clip": clip, "indices": [], "role": "pose"})
	if powered and pose not in ["idle", "special", "defeat"]:
		requests.append({"clip": "powered_idle" + empty, "indices": [0], "role": "boundary"})
	for request in requests:
		var segment := _segment(manifest, request, facing, aim if request.role == "pose" else "")
		if segment.is_empty():
			return [] # no partial transition, missing-clip fallback or invented weapon pose
		result.append(segment)
	return result

static func _segment(manifest: Dictionary, request: Dictionary, facing: String, aim: String) -> Dictionary:
	var clips: Variant = manifest.get("clips")
	if not clips is Dictionary:
		return {}
	var clip: Variant = clips.get(request.clip)
	if not clip is Dictionary:
		return {}
	var facings: Variant = clip.get("facings")
	if not facings is Dictionary:
		return {}
	var variant: Variant = facings.get(facing)
	if not variant is Dictionary:
		return {}
	if aim != "":
		var aims: Variant = variant.get("aims")
		if not aims is Dictionary:
			return {}
		variant = aims.get(aim)
		if not variant is Dictionary:
			return {}
	var frames: Variant = variant.get("frames")
	if not frames is Array or frames.is_empty():
		return {}
	var indices: Array = request.indices.duplicate()
	if indices.is_empty():
		for index in frames.size(): indices.append(index)
	var drawings: Array[Dictionary] = []
	for index in indices:
		if index >= frames.size() or not frames[index] is Dictionary or not frames[index].get("anchors") is Dictionary:
			return {}
		drawings.append(frames[index].duplicate(true))
	return {"clip": request.clip, "facing": facing, "aim": aim, "role": request.role,
		"indices": indices, "frames": drawings}
