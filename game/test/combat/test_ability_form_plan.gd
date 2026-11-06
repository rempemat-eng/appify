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
		for facing in manifest.clips.idle.facings:
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

func _eight_facing_manifest() -> Dictionary:
	var manifest := _manifest()
	for clip in manifest.clips.values():
		for facing in ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]:
			var variant: Dictionary = clip.facings.W.duplicate(true)
			# A distinct authored anchor makes a cardinal fallback observable.
			var facing_index: int = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"].find(facing)
			for frame in variant.frames:
				frame.anchors.hand_R = [10 + facing_index * 3, -20 - facing_index]
			clip.facings[facing] = variant
	manifest.clips.powered_primary.loop = false
	manifest.clips.powered_primary.release_frame = 1
	return manifest

func test_authored_diagonal_forms_use_exact_variants_and_empty_state() -> void:
	var manifest := _eight_facing_manifest()
	for facing in manifest.clips.idle.facings:
		for pose in ["walk", "primary", "guard", "defeat"]:
			for out in [false, true]:
				var plan := AbilityFormPlan.build("brine", pose, true, out, manifest, facing)
				assert_array(plan).is_not_empty()
				for segment in plan:
					assert_str(segment.facing).is_equal(facing)
					for index in segment.indices.size():
						assert_dict(segment.frames[index]).is_equal(manifest.clips[segment.clip].facings[facing].frames[segment.indices[index]])

func test_missing_diagonal_pose_boundary_or_exit_never_falls_back() -> void:
	for missing in ["powered_primary", "powered_idle", "powered_exit", "defeat"]:
		var manifest := _eight_facing_manifest()
		manifest.clips[missing].facings.erase("NE")
		var pose := "defeat" if missing in ["powered_exit", "defeat"] else "primary"
		assert_array(AbilityFormPlan.build("brine", pose, true, false, manifest, "NE")).is_empty()
	assert_array(AbilityFormPlan.build("brine", "idle", false, false, _eight_facing_manifest(), "")).is_empty()

func test_diagonal_form_playback_keeps_phase_and_rejects_bad_replacement() -> void:
	var manifest := _eight_facing_manifest()
	var track := AbilityFormTrack.new()
	var clocks := [[0.1], [0.1, 0.1, 0.1, 0.1, 0.1, 0.1], [0.1]]
	var plan := AbilityFormPlan.build("brine", "walk", true, false, manifest, "NE")
	assert_bool(track.configure("walk", manifest, plan, clocks, 1)).is_true()
	assert_str(track.advance(0.35).facing).is_equal("NE")
	var next := AbilityFormPlan.build("brine", "walk", true, false, manifest, "SW")
	assert_bool(track.configure("walk", manifest, next, clocks, 2)).is_true()
	assert_str(track.sample().facing).is_equal("SW")
	assert_int(track.sample().index).is_equal(2)
	assert_dict(track.sample().frame).is_equal(manifest.clips.powered_walk.facings.SW.frames[2])
	var before := track.sample()
	for facing in ["", "unavailable", 42]:
		var bad := next.duplicate(true)
		bad[0].facing = facing
		assert_bool(track.configure("walk", manifest, bad, clocks, 3)).is_false()
		assert_dict(track.sample()).is_equal(before)

func test_diagonal_powered_contact_keeps_exact_clock_and_authored_anchor() -> void:
	var manifest := _eight_facing_manifest()
	var plan := AbilityFormPlan.build("brine", "primary", true, false, manifest, "NW")
	var clocks := [[0.05], [0.14, 0.052, 0.052, 0.052, 0.052, 0.052], [0.05]]
	var track := AbilityContactTrack.new()
	assert_bool(track.configure_form(manifest, plan, clocks, 1, 0.5, 0.19)).is_true()
	var release := track.advance(0.19)
	assert_str(release[-2].kind).is_equal("drawing")
	assert_str(release[-1].kind).is_equal("contact")
	assert_str(release[-1].sample.facing).is_equal("NW")
	assert_int(release[-1].sample.index).is_equal(1)
	assert_dict(release[-1].sample.frame).is_equal(manifest.clips.powered_primary.facings.NW.frames[1])
	var finish := track.advance(1.0)
	assert_str(finish[-1].sample.clip).is_equal("powered_idle")
	assert_str(finish[-1].sample.facing).is_equal("NW")
	assert_int(finish.filter(func(event: Dictionary) -> bool: return event.kind == "contact").size()).is_equal(0)

func test_diagonal_terminal_playback_exits_before_exact_empty_defeat() -> void:
	var manifest := _eight_facing_manifest()
	var plan := AbilityFormPlan.build("brine", "defeat", true, true, manifest, "SE")
	var track := AbilityDefeatPlayback.new()
	var clocks := [[0.05, 0.05, 0.05, 0.05], [0.05, 0.05, 0.05, 0.05, 0.05, 0.05]]
	assert_bool(track.configure({"id": "brine", "powered": true, "harpoon_out": true,
		"manifest": manifest, "facing": "SE", "segment_durations": clocks}, 1)).is_true()
	var events := track.advance(1.0)
	assert_int(events.size()).is_equal(10)
	for index in 4:
		assert_str(events[index].clip).is_equal("powered_exit_empty")
		assert_int(events[index].index).is_equal(index)
	for index in 6:
		assert_str(events[index + 4].clip).is_equal("defeat_empty")
		assert_str(events[index + 4].facing).is_equal("SE")
		assert_dict(events[index + 4].frame).is_equal(plan[1].frames[index])
	assert_bool(track.finished()).is_true()
