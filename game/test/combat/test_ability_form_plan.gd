extends GdUnitTestSuite

func _manifest(id: String = "brine") -> Dictionary:
	var clips := {}
	for name in ["idle", "walk", "primary", "secondary", "guard", "defeat", "special", "powered_idle", "powered_walk", "powered_primary", "powered_guard", "powered_exit"]:
		for suffix in ["", "_empty"]:
			var frames: Array = []
			for index in 6: frames.append({"anchors": {"hand_R": [-index - 1, -12]}})
			clips[name + suffix] = {"facings": {"W": {"frames": frames}}}
	return {"id": id, "clips": clips}

func test_powered_action_has_exact_idle_zero_boundaries() -> void:
	var plan := AbilityFormPlan.build("brine", "primary", true, false, _manifest(), "W")
	assert_int(plan.size()).is_equal(3)
	assert_str(plan[0].clip).is_equal("powered_idle")
	assert_array(plan[0].indices).is_equal([0])
	assert_str(plan[1].clip).is_equal("powered_primary")
	assert_array(plan[1].indices).is_equal([0, 1, 2, 3, 4, 5])
	assert_dict(plan[2]).is_equal(plan[0])
	assert_array(plan[1].frames[4].anchors.hand_R).is_equal([-5, -12])

func test_powered_defeat_plays_exit_zero_to_three_then_unpowered_defeat() -> void:
	var plan := AbilityFormPlan.build("brine", "defeat", true, true, _manifest(), "W")
	assert_int(plan.size()).is_equal(2)
	assert_str(plan[0].clip).is_equal("powered_exit_empty")
	assert_array(plan[0].indices).is_equal([0, 1, 2, 3])
	assert_str(plan[1].clip).is_equal("defeat_empty")
	assert_str(plan[1].role).is_equal("pose")
	assert_bool(plan[0].has("durations")).is_false()

func test_empty_selection_uses_explicit_runner_flag_and_only_brine() -> void:
	for pose in ["idle", "walk", "guard", "special", "defeat"]:
		var normal := AbilityFormPlan.build("brine", pose, false, false, _manifest(), "W")
		var empty := AbilityFormPlan.build("brine", pose, false, true, _manifest(), "W")
		assert_str(normal[0].clip).is_equal(pose)
		assert_str(empty[0].clip).is_equal(pose + "_empty")
	var other := AbilityFormPlan.build("nix", "idle", true, true, _manifest("nix"), "W")
	assert_str(other[0].clip).is_equal("powered_idle")

func test_missing_variant_or_exit_rejects_entire_plan_without_fallback() -> void:
	var manifest := _manifest()
	manifest.clips.powered_exit.facings.W.frames.resize(3)
	assert_array(AbilityFormPlan.build("brine", "defeat", true, false, manifest, "W")).is_empty()
	manifest = _manifest()
	manifest.clips.erase("powered_primary")
	assert_array(AbilityFormPlan.build("brine", "primary", true, false, manifest, "W")).is_empty()
	for args in [["foreign", "idle", "W", ""], ["brine", "unknown", "W", ""], ["brine", "idle", "E", ""], ["brine", "idle", "W", "missing"]]:
		assert_array(AbilityFormPlan.build(args[0], args[1], false, false, _manifest(), args[2], args[3])).is_empty()

func test_plans_are_isolated_and_do_not_mutate_source_or_share_boundaries() -> void:
	var manifest := _manifest()
	var original := manifest.duplicate(true)
	var plan := AbilityFormPlan.build("brine", "guard", true, false, manifest, "W")
	plan[0].frames[0].anchors.clear()
	plan[1].indices.clear()
	assert_dict(manifest).is_equal(original)
	assert_dict(plan[2].frames[0].anchors).is_not_empty()

func test_real_authored_forms_and_empty_variants_preserve_source_frames() -> void:
	for id in ["bramble", "iona", "pendle", "cairn", "morel", "velvet", "tam", "mirra", "brine", "ashe", "clack", "nix", "rook", "mote"]:
		var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/characters/%s/manifest.json" % id))
		for facing in ["S", "N", "E", "W"]:
			for powered in [false, true]:
				for out in ([false, true] if id == "brine" else [false]):
					for pose in ["idle", "walk", "guard", "defeat"]:
						var plan := AbilityFormPlan.build(id, pose, powered, out, manifest, facing)
						assert_array(plan).is_not_empty()
						for segment in plan:
							for index in segment.indices.size():
								assert_dict(segment.frames[index]).is_equal(manifest.clips[segment.clip].facings[facing].frames[segment.indices[index]])

func test_powered_walk_also_has_idle_zero_boundaries() -> void:
	var plan := AbilityFormPlan.build("brine", "walk", true, true, _manifest(), "W")
	assert_int(plan.size()).is_equal(3)
	assert_str(plan[0].clip).is_equal("powered_idle_empty")
	assert_array(plan[0].indices).is_equal([0])
	assert_str(plan[1].clip).is_equal("powered_walk_empty")
	assert_dict(plan[2]).is_equal(plan[0])
