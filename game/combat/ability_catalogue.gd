class_name AbilityCatalogue
extends RefCounted
## Canonical kit data stays in canonical units. Convert only at the world/physics boundary.
## Do not recursively scale JSON numbers: damage, timers, angles and resource counts are distinct.

const IDS := ["bramble", "morel", "velvet", "cairn", "iona", "tam", "brine", "pendle",
	"mirra", "ashe", "clack", "nix", "rook", "mote"]
const ROOT := "res://data/abilities/"

static func read_json(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed = JSON.parse_string(file.get_as_text())
	return parsed if parsed is Dictionary else {}

static func kit(id: String) -> Dictionary:
	return read_json(ROOT + id + ".json") if id in IDS else {}

static func shared() -> Dictionary:
	return read_json(ROOT + "canonical-shared.json")

static func units() -> Dictionary:
	return read_json(ROOT + "units.json")

static func actor_distance(value: float) -> float:
	return value * float(units().canonical_to_actor)

static func hitbox_distance(value: float, id: String, manifest: Dictionary) -> float:
	var converted := actor_distance(value)
	if id == "cairn":
		# Follow the actual authored height, not a guessed 1.2 multiplier or texture canvas size.
		assert(float(manifest.get("body_height_target", 0.0)) > 0.0)
		converted *= float(manifest.body_height_target) / float(units().adult_manifest_height)
	return converted

static func action(id: String, name: String, powered: bool = false) -> Dictionary:
	var data := kit(id)
	if data.is_empty():
		return {}
	return data["powered" if powered else "base"].actions.get(name, {}).duplicate(true)
