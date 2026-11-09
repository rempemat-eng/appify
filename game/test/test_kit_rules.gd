extends GdUnitTestSuite
## W6 runs the production Python validator from the Godot test gate. It needs
## only Python's standard library; no renderer or substituted validation stub.

const CASES := "res://test/fixtures/kit/validation.cases.json"
const CHECK_CASE := "import json,sys; sys.path.insert(0,sys.argv[1]); from scripts.review.kit_scene import check_zone; c=json.load(open(sys.argv[2])); fs=check_zone(c['plan'],c.get('library'),c.get('materials'),c.get('size_guide')); print(json.dumps({'findings':fs})); sys.exit(1 if any(f.get('severity','fault')=='fault' for f in fs) else 0)"

func _repo() -> String:
	return ProjectSettings.globalize_path("res://").trim_suffix("/").get_base_dir()

func _python(args: PackedStringArray) -> Dictionary:
	var output := []
	var binary := OS.get_environment("PYTHON")
	if binary.is_empty():
		binary = "python3"
	var code := OS.execute(binary, args, output, true)
	var value = JSON.parse_string("".join(output))
	assert_bool(value is Dictionary).override_failure_message("Python validator did not emit JSON: %s" % output).is_true()
	return {"code": code, "value": value if value is Dictionary else {}}

func test_shared_cell_native_positive_and_negative_cases() -> void:
	var envelope = JSON.parse_string(FileAccess.get_file_as_string(CASES))
	assert_bool(envelope is Dictionary).is_true()
	if not envelope is Dictionary:
		return
	var cases: Array = envelope.get("cases", [])
	assert_int(cases.size()).is_greater(1)
	for entry in cases:
		var path := ProjectSettings.globalize_path("user://w6_validation_case.json")
		var file := FileAccess.open(path, FileAccess.WRITE)
		file.store_string(JSON.stringify(entry))
		file.close()
		var result := _python(["-c", CHECK_CASE, _repo(), path])
		DirAccess.remove_absolute(path)
		var checks := []
		for finding in result.value.get("findings", []):
			if finding.get("severity", "fault") == "fault" and finding.check not in checks:
				checks.append(finding.check)
		checks.sort()
		var expected: Array = entry.get("expected_checks", []).duplicate()
		expected.sort()
		assert_that(checks).override_failure_message("W6 case %s: %s" % [entry.get("id"), result.value]).is_equal(expected)
		assert_int(result.code).is_equal(0 if expected.is_empty() else 1)

func test_actual_godot_scene_export_passes_python_cli() -> void:
	var path := ProjectSettings.globalize_path("user://w6_kitlab_export.json")
	# The editor base's pre-W2 exporter uses its destination as the template.
	# Retain the real lab's approval context; W2 separately tests fresh-path export.
	var template := FileAccess.open(path, FileAccess.WRITE)
	template.store_string(FileAccess.get_file_as_string("res://kit/zones/kitlab.json"))
	template.close()
	var output := []
	var code := OS.execute(OS.get_executable_path(), ["--headless", "--audio-driver", "Dummy", "--path",
		ProjectSettings.globalize_path("res://"), "-s", "res://tools/kit_zone.gd", "--",
		"--export=res://zones/kitlab/kitlab.tscn", "--out=" + path], output, true)
	assert_int(code).override_failure_message("Godot kit export failed: %s" % output).is_equal(0)
	assert_bool(FileAccess.file_exists(path)).is_true()
	if not FileAccess.file_exists(path):
		return
	var script := "import sys; sys.path.insert(0,sys.argv[1]); from scripts.review.kit_scene import main; sys.exit(main(sys.argv[2:]))"
	var result := _python(["-c", script, _repo(), path, "--check", "--json"])
	DirAccess.remove_absolute(path)
	assert_int(result.code).override_failure_message(str(result.value)).is_equal(0)
	assert_bool(result.value.has("findings")).is_true()
