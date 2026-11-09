extends GdUnitTestSuite
## Both placement engines consume exactly the same input and expected output records.

const Relations := preload("res://world/terrain/relations.gd")
const CASES := "res://kit/schema/relations.cases.json"

func test_shared_relation_cases_have_identical_verdicts_and_messages() -> void:
	var fixture = JSON.parse_string(FileAccess.get_file_as_string(CASES))
	assert_bool(fixture is Dictionary).is_true()
	if not fixture is Dictionary:
		return
	assert_int(int(fixture.version)).is_equal(1)
	assert_int(fixture.cases.size()).is_greater_equal(30)
	var ids := {}
	for entry in fixture.cases:
		assert_bool(ids.has(entry.id)).is_false()
		ids[entry.id] = true
		var before := JSON.stringify(entry, "", true)
		var actual: Array
		if entry.get("mode", "zone") == "placement":
			actual = Relations.check_placement(entry.plan, entry.candidate, entry.library, entry.materials)
		else:
			actual = Relations.check_zone(entry.plan, entry.library, entry.materials)
		assert_that(actual).override_failure_message("Shared relation case %s: actual %s; expected %s" % [entry.id, JSON.stringify(actual), JSON.stringify(entry.expected)]).is_equal(entry.expected)
		assert_str(JSON.stringify(entry, "", true)).is_equal(before)

func test_source_registry_and_manifest_load_without_terrain_textures() -> void:
	var library := Relations.default_library()
	assert_bool(library.has("woodland_forest_bench")).is_true()
	assert_str(library.woodland_forest_bench.placement.role).is_equal("seat")
	var materials := Relations.default_materials()
	assert_bool(materials.has("path")).is_true()
	assert_bool(materials.path.route).is_true()

func test_real_kit_labs_satisfy_the_source_placement_relations() -> void:
	var library := Relations.default_library()
	var materials := Relations.default_materials()
	for id in ["kitlab", "kitlab_tiers"]:
		var plan = JSON.parse_string(FileAccess.get_file_as_string("res://kit/zones/%s.json" % id))
		var findings := Relations.check_zone(plan, library, materials)
		assert_that(findings).override_failure_message("%s source placement findings: %s" % [id, JSON.stringify(findings)]).is_equal([])
