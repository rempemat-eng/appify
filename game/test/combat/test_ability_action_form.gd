extends "res://test/combat/test_ability_contact_consumer.gd"
## Synthetic approved schedules prove clock alignment, not production art retiming.

func _contract(state: Dictionary, _action: String) -> Dictionary:
	var frames := [{"anchors": {"tip": [-1, -2]}},
		{"anchors": {"tip": [-22.0, -30.5]}}, {"anchors": {"tip": [-3, -4]}}]
	var manifest := {"id": "bramble", "clips": {
		"powered_idle": {"loop": true, "facings": {"W": {"frames": [frames[0]]}}},
		"powered_primary": {"loop": false, "release_frame": 1, "facings": {"W": {"frames": frames}}}}}
	var release := AbilityPlayerPhase._release_time(state.player)
	var duration := float(state.player.actionDuration)
	var durations := [[0.05], [release - 0.05, (duration - release) / 2, (duration - release) / 2 - 0.05], [0.05]]
	return {"manifest": manifest, "plan": AbilityFormPlan.build("bramble", "primary", true, false, manifest, "W"),
		"segment_durations": durations}

func _form_draw(sample: Dictionary) -> void:
	events.append({"kind": "draw", "clip": sample.clip, "index": sample.index, "token": sample.token})
	if cancel_on_drawing: consumer.cancel()

func _form_contact(sample: Dictionary) -> void:
	events.append({"kind": "contact", "clip": sample.clip, "index": sample.index, "token": sample.token})

func test_plan_boundaries_share_canonical_clock_and_contact_uses_actual_pose() -> void:
	var c := _contract(_state("primary"), "primary")
	var t := AbilityContactTrack.new()
	assert_bool(t.configure_form(c.manifest, c.plan, c.segment_durations, 1, 0.5, 0.19)).is_true()
	var start := t.advance(0.0)
	assert_str(start[0].sample.clip).is_equal("powered_idle")
	var release := t.advance(0.19)
	assert_str(release[-2].kind).is_equal("drawing")
	assert_str(release[-1].kind).is_equal("contact")
	assert_str(release[-1].sample.clip).is_equal("powered_primary")
	assert_int(release[-1].sample.index).is_equal(1)
	assert_vector(AbilityContactTrack.anchor(release[-1].sample, "tip").offset).is_equal(Vector2(-22, -30.5))
	var finish := t.advance(0.31)
	assert_str(finish[-1].sample.clip).is_equal("powered_idle")
	assert_int(finish[-1].sample.index).is_equal(0)
	assert_bool(t.is_finished()).is_true()
	assert_array(t.advance(1.0)).is_empty()

func test_invalid_boundary_source_schedule_and_canonical_clocks_preserve_live_track() -> void:
	var c := _contract(_state("primary"), "primary")
	var t := AbilityContactTrack.new()
	assert_bool(t.configure_form(c.manifest, c.plan, c.segment_durations, 1, 0.5, 0.19)).is_true()
	t.advance(0.1)
	var before := t.sample()
	for fault in ["source", "clock", "contact", "duration", "loop", "shape"]:
		var bad := c.duplicate(true)
		if fault == "source": bad.plan[0].frames[0].anchors.clear()
		if fault == "clock": bad.segment_durations[0][0] += 0.01
		if fault == "loop": bad.manifest.clips.powered_primary.loop = true
		if fault == "shape": bad.plan = [{}, {}, {}]
		assert_bool(t.configure_form(bad.manifest, bad.plan, bad.segment_durations, 2,
			0.51 if fault == "duration" else 0.5, 0.20 if fault == "contact" else 0.19)).is_false()
		assert_dict(t.sample()).is_equal(before)
	assert_bool(t.configure_form(c.manifest, c.plan, c.segment_durations, 1, 0.5, 0.19)).is_false()

func test_pause_cancel_reconfigure_and_snapshot_isolation() -> void:
	var c := _contract(_state("primary"), "primary")
	var t := AbilityContactTrack.new()
	assert_bool(t.configure_form(c.manifest, c.plan, c.segment_durations, 1, 0.5, 0.19)).is_true()
	assert_array(t.advance(1.0, false)).is_empty()
	for delta in [-1.0, NAN, INF]: assert_array(t.advance(delta)).is_empty()
	var sample := t.sample()
	sample.frame.anchors.clear()
	assert_dict(t.sample().frame.anchors).is_not_empty()
	t.cancel()
	assert_array(t.advance(1.0)).is_empty()
	var legacy := _provide(_state("primary"), "primary")
	assert_bool(t.configure(legacy.manifest, legacy.clip, legacy.facing, legacy.durations, 2)).is_true()
	assert_str(t.advance(0.0)[0].sample.clip).is_equal("primary")

func test_optional_consumer_recommit_orders_end_boundary_before_new_instance() -> void:
	consumer.configure(_contract, _form_draw, _form_contact)
	_commit()
	consumer.observe(_state("primary", 0, 1), _state("primary", 0, 2), 0.5)
	assert_int(events.filter(func(e: Dictionary) -> bool: return e.kind == "contact").size()).is_equal(1)
	assert_str(events[-2].clip).is_equal("powered_idle")
	assert_str(events[-1].clip).is_equal("powered_idle")
	assert_int(events[-2].token).is_equal(1)
	assert_int(events[-1].token).is_equal(2)

func test_reentrant_cancel_blocks_release_and_trailing_boundary() -> void:
	consumer.configure(_contract, _form_draw, _form_contact)
	_commit()
	cancel_on_drawing = true
	consumer.observe(_state("primary", 0, 1), _state("idle", 0, 1), 0.5)
	assert_int(events.size()).is_equal(2)
	assert_int(events.filter(func(e: Dictionary) -> bool: return e.kind == "contact").size()).is_equal(0)

func test_timeline_export_is_detached_from_validated_form() -> void:
	var c := _contract(_state("primary"), "primary")
	var t := AbilityFormTrack.new()
	assert_bool(t.configure("form", c.manifest, c.plan, c.segment_durations, 1)).is_true()
	var exported := t.timeline()
	exported.samples[0].frame.anchors.clear()
	exported.starts.clear()
	assert_dict(t.sample().frame.anchors).is_not_empty()
	assert_int(t.timeline().starts.size()).is_equal(5)
