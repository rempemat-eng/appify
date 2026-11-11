extends GdUnitTestSuite

func _manifest() -> Dictionary:
	var frames := [{"anchors": {"hand_R": [-3, -8]}}, {"anchors": {"hand_R": [-9, -14]}}, {"anchors": {"hand_R": [-4, -7]}}]
	var variant := {"frames": frames, "aims": {"p22": {"frames": frames.duplicate(true)}}}
	return {"clips": {"walk": {"loop": true, "facings": {"W": variant, "N": variant.duplicate(true)}},
		"guard": {"loop": true, "facings": {"W": variant.duplicate(true)}},
		"powered_exit": {"loop": false, "facings": {"W": variant.duplicate(true)}}}}

func _track(clip: String = "walk") -> AbilityPoseTrack:
	var track := AbilityPoseTrack.new()
	assert_bool(track.configure("state1", _manifest(), clip, "W", [0.125, 0.25, 0.125], 1)).is_true()
	return track

func test_loop_boundaries_wrap_without_a_release_contract_or_events() -> void:
	var track := _track()
	assert_int(track.sample().index).is_equal(0)
	assert_int(track.advance(0.125).index).is_equal(1)
	assert_int(track.advance(0.25).index).is_equal(2)
	assert_int(track.advance(0.125).index).is_equal(0)
	assert_bool(track.is_finished()).is_false()
	assert_bool(track.sample().has("kind")).is_false()

func test_fine_and_coarse_steps_choose_same_drawing_after_many_loops() -> void:
	var fine := _track()
	var coarse := _track()
	for step in 103: fine.advance(0.0625)
	assert_dict(fine.sample()).is_equal(coarse.advance(6.4375))
	assert_int(coarse.advance(1.0e300).index).is_between(0, 2)

func test_guard_and_finite_exit_use_supplied_clock_and_hold_last_drawing() -> void:
	var guard := _track("guard")
	assert_int(guard.advance(0.125).index).is_equal(1)
	var exit := _track("powered_exit")
	assert_int(exit.advance(0.5).index).is_equal(2)
	assert_bool(exit.is_finished()).is_true()
	assert_dict(exit.advance(10.0)).is_equal(exit.sample())
	# The track never guesses the following idle/defeat state.
	assert_str(exit.sample().clip).is_equal("powered_exit")

func test_facing_and_aim_changes_keep_phase_without_mirroring_anchors() -> void:
	var track := _track()
	track.advance(0.25)
	assert_bool(track.configure("state1", _manifest(), "walk", "N", [0.125, 0.25, 0.125], 2, "p22")).is_true()
	assert_int(track.sample().index).is_equal(1)
	assert_str(track.sample().aim).is_equal("p22")
	assert_vector(AbilityContactTrack.anchor(track.sample(), "hand_R").offset).is_equal(Vector2(-9, -14))
	assert_bool(track.configure("state2", _manifest(), "guard", "W", [0.125, 0.25, 0.125], 3)).is_true()
	assert_int(track.sample().index).is_equal(0)

func test_pause_and_invalid_delta_freeze_and_cancellation_rejects_old_tokens() -> void:
	var track := _track()
	track.advance(0.125)
	var sample := track.sample()
	assert_dict(track.advance(2.0, false)).is_equal(sample)
	for delta in [-1.0, INF, NAN]: assert_dict(track.advance(delta)).is_equal(sample)
	track.cancel()
	assert_dict(track.advance(1.0)).is_empty()
	assert_bool(track.is_finished()).is_false()
	assert_bool(track.configure("state1", _manifest(), "walk", "W", [0.125, 0.25, 0.125], 1)).is_false()
	assert_bool(track.configure("state1", _manifest(), "walk", "W", [0.125, 0.25, 0.125], 2)).is_true()
	assert_int(track.sample().index).is_equal(0)

func test_bad_replacement_and_implicit_retiming_preserve_valid_state() -> void:
	var track := _track()
	track.advance(0.125)
	var before := track.sample()
	for durations in [[], [0.1], [0.1, 0, 0.1], [0.1, NAN, 0.1], [0.1, true, 0.1]]:
		assert_bool(track.configure("new", _manifest(), "walk", "W", durations, 2)).is_false()
	assert_bool(track.configure("state1", _manifest(), "guard", "W", [0.125, 0.25, 0.125], 2)).is_false()
	assert_bool(track.configure("state1", _manifest(), "walk", "W", [0.25, 0.125, 0.125], 2)).is_false()
	for args in [["walk", "E", ""], ["walk", "W", "missing"], ["missing", "W", ""]]:
		assert_bool(track.configure("new", _manifest(), args[0], args[1], [0.125, 0.25, 0.125], 2, args[2])).is_false()
	var invalid := _manifest()
	invalid.clips.walk.loop = "true"
	assert_bool(track.configure("new", invalid, "walk", "W", [0.125, 0.25, 0.125], 2)).is_false()
	assert_dict(track.sample()).is_equal(before)

func test_manifest_schedule_and_sample_mutation_cannot_change_live_pose() -> void:
	var manifest := _manifest()
	var durations := [0.125, 0.25, 0.125]
	var track := AbilityPoseTrack.new()
	assert_bool(track.configure("empty1", manifest, "guard", "W", durations, 1)).is_true()
	manifest.clips.guard.facings.W.frames[0].anchors.hand_R[0] = 999
	durations[0] = 999
	var sample := track.sample()
	sample.frame.anchors.clear()
	assert_vector(AbilityContactTrack.anchor(track.sample(), "hand_R").offset).is_equal(Vector2(-3, -8))
	assert_int(track.advance(0.125).index).is_equal(1)

func test_malformed_manifest_containers_fail_closed() -> void:
	for manifest in [{}, {"clips": null}, {"clips": []}, {"clips": {"walk": {"loop": true, "facings": []}}}]:
		assert_bool(AbilityPoseTrack.new().configure("x", manifest, "walk", "W", [0.1], 1)).is_false()
	var manifest := _manifest()
	manifest.clips.walk.facings.W.aims = null
	assert_bool(AbilityPoseTrack.new().configure("x", manifest, "walk", "W", [0.125, 0.25, 0.125], 1, "p22")).is_false()

func test_authored_passive_and_form_variants_keep_their_exact_drawing_data() -> void:
	# These are explicitly supplied fixture clocks, not approval to use template timings
	# for canonical attacks or a production state-selection policy.
	for id in ["bramble", "iona", "pendle", "cairn", "morel", "velvet", "tam", "mirra", "brine", "ashe", "clack", "nix", "rook", "mote"]:
		var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/characters/%s/manifest.json" % id))
		var clips := ["idle", "walk", "guard", "powered_idle", "powered_exit"]
		if id == "brine": clips.append_array(["idle_empty", "walk_empty", "guard_empty", "powered_idle_empty"])
		for clip in clips:
			var info: Dictionary = manifest.clips[clip]
			for facing in ["S", "N", "E", "W"]:
				var track := AbilityPoseTrack.new()
				assert_bool(track.configure("explicit", manifest, clip, facing, info.durations, 1)).is_true()
				assert_dict(track.sample().frame).is_equal(info.facings[facing].frames[0])
				track.advance(100.0)
				assert_bool(track.is_finished()).is_equal(not info.loop)
				assert_str(track.sample().clip).is_equal(clip)
