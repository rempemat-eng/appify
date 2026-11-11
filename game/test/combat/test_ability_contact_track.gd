extends GdUnitTestSuite

func _manifest() -> Dictionary:
	var frames := [
		{"path": "windup.png", "anchors": {"hand_L": [-2.0, -8.0]}},
		{"path": "contact.png", "anchors": {"hand_L": [-17.5, -31.0], "arrow_tip": [-22.0, -30.5]}},
		{"path": "recovery.png", "anchors": {"hand_L": [-3.0, -12.0]}}]
	return {"foot_pivot": [80, 136], "clips": {"primary": {
		"loop": false, "duration": 99.0, "durations": [33.0, 33.0, 33.0],
		"release_frame": 1, "facings": {"W": {"frames": frames,
		"aims": {"p22": {"frames": [
			{"anchors": {"arrow_tip": [-1.0, -2.0]}},
			{"anchors": {"arrow_tip": [-40.0, -50.0]}},
			{"anchors": {"arrow_tip": [-3.0, -4.0]}}]}}}}}}}

func _track() -> AbilityContactTrack:
	var track := AbilityContactTrack.new()
	assert_bool(track.configure(_manifest(), "primary", "W", [0.125, 0.25, 0.125], 1)).is_true()
	return track

func _contacts(events: Array[Dictionary]) -> Array[Dictionary]:
	return events.filter(func(event: Dictionary) -> bool: return event.kind == "contact")

func test_exact_boundary_displays_contact_before_delivering_it_once() -> void:
	var track := _track()
	assert_int(track.advance(0.0).size()).is_equal(1)
	assert_int(_contacts(track.advance(0.124)).size()).is_equal(0)
	var events := track.advance(0.001)
	assert_int(events.size()).is_equal(2)
	assert_str(events[0].kind).is_equal("drawing")
	assert_str(events[1].kind).is_equal("contact")
	assert_int(events[0].sample.index).is_equal(1)
	assert_int(_contacts(track.advance(0.0)).size()).is_equal(0)

func test_coarse_step_retains_authored_contact_instead_of_final_recovery_anchor() -> void:
	var track := _track()
	var events := track.advance(20.0)
	assert_int(events.size()).is_equal(4)
	assert_int(events[0].sample.index).is_equal(0)
	assert_int(events[1].sample.index).is_equal(1)
	assert_str(events[2].kind).is_equal("contact")
	assert_int(events[3].sample.index).is_equal(2)
	assert_vector(AbilityContactTrack.anchor(events[2].sample, "hand_L").offset).is_equal(Vector2(-17.5, -31.0))
	assert_vector(AbilityContactTrack.anchor(track.sample(), "hand_L").offset).is_equal(Vector2(-3.0, -12.0))
	assert_bool(track.is_finished()).is_true()
	assert_int(track.advance(20.0).size()).is_equal(0)

func test_fine_and_coarse_steps_have_identical_order_and_canonical_boundaries() -> void:
	var fine := _track()
	var coarse := _track()
	var events: Array[Dictionary] = []
	for step in 8:
		events.append_array(fine.advance(0.0625))
	assert_array(events).is_equal(coarse.advance(0.5))
	assert_float(_contacts(events)[0].sample.starts_at).is_equal(0.125)

func test_explicit_aim_variant_preserves_screen_coordinates_without_mirroring_or_scale() -> void:
	var track := AbilityContactTrack.new()
	assert_bool(track.configure(_manifest(), "primary", "W", [0.125, 0.25, 0.125], 1, "p22")).is_true()
	var contact: Dictionary = _contacts(track.advance(0.5))[0].sample
	assert_str(contact.aim).is_equal("p22")
	assert_str(contact.facing).is_equal("W")
	assert_vector(AbilityContactTrack.anchor(contact, "arrow_tip").offset).is_equal(Vector2(-40.0, -50.0))
	assert_dict(AbilityContactTrack.anchor(contact, "hand_L")).is_empty()

func test_cancelled_action_cannot_contact_and_old_tokens_cannot_replay() -> void:
	var track := _track()
	track.advance(0.0625)
	track.cancel()
	assert_int(track.advance(1.0).size()).is_equal(0)
	assert_dict(track.sample()).is_empty()
	assert_bool(track.configure(_manifest(), "primary", "W", [0.125, 0.25, 0.125], 1)).is_false()
	assert_bool(track.configure(_manifest(), "primary", "W", [0.125, 0.25, 0.125], 2)).is_true()
	var contact: Dictionary = _contacts(track.advance(0.5))[0].sample
	assert_int(contact.token).is_equal(2)

func test_inactive_invalid_and_negative_steps_freeze_without_consuming_drawings() -> void:
	var track := _track()
	for time in [1.0, INF, NAN, -1.0]:
		assert_int(track.advance(time, false).size()).is_equal(0)
	for time in [INF, NAN, -1.0]:
		assert_int(track.advance(time).size()).is_equal(0)
	assert_int(track.sample().index).is_equal(0)
	assert_int(_contacts(track.advance(0.125)).size()).is_equal(1)

func test_invalid_schedules_and_variants_preserve_live_sequence_and_do_not_spend_token() -> void:
	var track := _track()
	for durations in [[], [0.1], [0.1, 0.0, 0.1], [0.1, -1.0, 0.1], [0.1, NAN, 0.1], [0.1, true, 0.1]]:
		assert_bool(track.configure(_manifest(), "primary", "W", durations, 2)).is_false()
	for request in [["missing", "W", ""], ["primary", "E", ""], ["primary", "W", "missing"]]:
		assert_bool(track.configure(_manifest(), request[0], request[1], [0.125, 0.25, 0.125], 2, request[2])).is_false()
	assert_int(_contacts(track.advance(0.5))[0].sample.token).is_equal(1)
	assert_bool(track.configure(_manifest(), "primary", "W", [0.125, 0.25, 0.125], 2)).is_true()

func test_loop_missing_frame_and_invalid_release_are_rejected_without_guessing() -> void:
	for release in [-1, 3, 1.5, NAN, true]:
		var manifest := _manifest()
		manifest.clips.primary.release_frame = release
		assert_bool(AbilityContactTrack.new().configure(manifest, "primary", "W", [0.125, 0.25, 0.125], 1)).is_false()
	var loop := _manifest()
	loop.clips.primary.loop = true
	assert_bool(AbilityContactTrack.new().configure(loop, "primary", "W", [0.125, 0.25, 0.125], 1)).is_false()
	var broken := _manifest()
	broken.clips.primary.facings.W.frames[1] = {}
	assert_bool(AbilityContactTrack.new().configure(broken, "primary", "W", [0.125, 0.25, 0.125], 1)).is_false()

func test_first_drawing_release_is_delivered_once_even_at_zero_time() -> void:
	var manifest := _manifest()
	manifest.clips.primary.release_frame = 0
	var track := AbilityContactTrack.new()
	assert_bool(track.configure(manifest, "primary", "W", [0.125, 0.25, 0.125], 1)).is_true()
	assert_int(_contacts(track.advance(0.0)).size()).is_equal(1)
	assert_int(_contacts(track.advance(1.0)).size()).is_equal(0)

func test_input_samples_and_contact_events_are_independent_snapshots() -> void:
	var manifest := _manifest()
	var track := AbilityContactTrack.new()
	assert_bool(track.configure(manifest, "primary", "W", [0.125, 0.25, 0.125], 1)).is_true()
	manifest.clips.primary.facings.W.frames[1].anchors.hand_L[0] = 999
	var events := track.advance(0.125)
	events[1].sample.frame.anchors.hand_L[0] = 888
	var contact: Dictionary = _contacts(events)[0].sample
	assert_vector(AbilityContactTrack.anchor(contact, "hand_L").offset).is_equal(Vector2(-17.5, -31.0))
	contact.frame.anchors.hand_L[0] = 777
	assert_vector(AbilityContactTrack.anchor(track.sample(), "hand_L").offset).is_equal(Vector2(-17.5, -31.0))

func test_missing_malformed_and_zero_anchors_remain_distinguishable() -> void:
	assert_dict(AbilityContactTrack.anchor({}, "tip")).is_empty()
	for point in [[], [0], [0, 0, 0], [NAN, 0], [true, 0], "0,0"]:
		assert_dict(AbilityContactTrack.anchor({"frame": {"anchors": {"tip": point}}}, "tip")).is_empty()
	assert_vector(AbilityContactTrack.anchor({"frame": {"anchors": {"tip": [0, 0]}}}, "tip").offset).is_equal(Vector2.ZERO)
