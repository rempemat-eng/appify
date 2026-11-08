@tool
extends RefCounted
## Transport only. Placement and full physical findings remain W5/W6 outputs.
const Relations := preload("res://world/terrain/relations.gd")
const VALIDATE := "import json,sys; sys.path.insert(0,sys.argv[1]); from scripts.review.kit_scene import check_zone; p=json.load(open(sys.argv[2])); fs=check_zone(p['plan'],p['library'],p['materials']); print(json.dumps({'findings':fs})); sys.exit(1 if any(f.get('severity','fault')=='fault' for f in fs) else 0)"
static var _sequence := 0

static func failure(check: String, message: String) -> Dictionary:
	return {"ok": false, "diagnostics": [{"check": check, "message": message, "severity": "fault"}], "message": message}

static func placement(plan: Dictionary, candidate: Dictionary, library: Dictionary) -> Dictionary:
	var findings: Array = Relations.check_placement(plan, candidate, library, Relations.default_materials())
	return findings_result(findings)

static func findings_result(findings: Array) -> Dictionary:
	var ok := true
	for finding in findings:
		if not finding is Dictionary:
			return failure("editor.validator_protocol", "The shared validator returned a malformed finding.")
		if String(finding.get("severity", "fault")) == "fault":
			ok = false
	return {"ok": ok, "diagnostics": findings.duplicate(true)}

static func python_binary() -> String:
	var binary := OS.get_environment("PYTHON")
	return "python3" if binary.is_empty() else binary

static func validate_plan(plan: Dictionary, library: Dictionary) -> Dictionary:
	var directory := ProjectSettings.globalize_path("user://world_editor_validation")
	if DirAccess.make_dir_recursive_absolute(directory) != OK:
		return failure("editor.validator_io", "The validation scratch folder could not be created.")
	_sequence += 1
	var path := directory.path_join("%d_%d_%d.json" % [OS.get_process_id(), Time.get_ticks_usec(), _sequence])
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return failure("editor.validator_io", "The current scene could not be sent to the validator.")
	file.store_string(JSON.stringify({"plan": plan, "library": library, "materials": Relations.default_materials()}))
	file.close()
	var output: Array = []
	var repo := ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()
	var code := OS.execute(python_binary(), ["-c", VALIDATE, repo, path], output, true)
	DirAccess.remove_absolute(path)
	var parser := JSON.new()
	var parsed := parser.parse("".join(output))
	if parsed != OK or not parser.data is Dictionary or not parser.data.get("findings") is Array:
		return failure("editor.validator_failed", "The full zone validator did not return findings (exit %d): %s" % [code, "".join(output).left(1600)])
	var result := findings_result(parser.data.findings)
	if code not in [0, 1] or (code == 1 and bool(result.ok)):
		return failure("editor.validator_failed", "The full zone validator exited unexpectedly (%d)." % code)
	return result
