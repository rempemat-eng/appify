extends GdUnitTestSuite
## Synthetic 60-second cycles are test inputs, never production timing.

const CLOCK = preload("res://core/world_clock.gd")

func _clock():
	var clock = CLOCK.new()
	assert_bool(clock.configure(60, [{"id": "day", "at": 0}, {"id": "night", "at": 0.5}], "clear")).is_true()
	return clock

func test_exact_half_open_boundaries_and_days() -> void:
	var clock = _clock()
	assert_str(clock.snapshot().phase).is_equal("day")
	clock.seek(29.999)
	assert_str(clock.snapshot().phase).is_equal("day")
	clock.seek(30)
	assert_str(clock.snapshot().phase).is_equal("night")
	clock.seek(60)
	assert_int(clock.snapshot().day).is_equal(1)
	assert_float(clock.snapshot().time).is_equal(0.0)
	assert_str(clock.snapshot().phase).is_equal("day")

func test_coarse_advance_emits_one_final_state() -> void:
	var clock = _clock()
	var received := []
	clock.changed.connect(func(value): received.append(value))
	assert_bool(clock.advance(60 * 100 + 40)).is_true()
	assert_int(received.size()).is_equal(1)
	assert_int(received[0].day).is_equal(100)
	assert_str(received[0].phase).is_equal("night")

func test_pause_discards_time_without_catch_up() -> void:
	var clock = _clock()
	clock.advance(10)
	clock.set_active(false)
	var before: Dictionary = clock.snapshot()
	assert_bool(clock.advance(1000)).is_true()
	assert_dict(clock.snapshot()).is_equal(before)
	clock.set_active(true)
	clock.advance(5)
	assert_float(clock.snapshot().time).is_equal(15.0)

func test_explicit_weather_and_unchanged_samples_do_not_repeat_hooks() -> void:
	var clock = _clock()
	var received := []
	clock.changed.connect(func(value): received.append(value))
	clock.set_weather("rain")
	clock.set_weather("rain")
	clock.seek(0)
	clock.advance(0)
	clock.set_active(true)
	assert_int(received.size()).is_equal(1)
	assert_str(received[0].weather).is_equal("rain")
	assert_float(received[0].time).is_equal(0.0)

func test_config_input_and_signal_snapshot_are_detached() -> void:
	var clock = _clock()
	var phases := [{"id": "dawn", "at": 0}, {"id": "dusk", "at": 0.25}]
	clock.configure(80, phases, "clouds")
	phases[1].id = "mutated"
	phases[1].at = 0.9
	clock.changed.connect(func(value): value.phase = "listener mutation")
	clock.advance(20)
	assert_str(clock.snapshot().phase).is_equal("dusk")
	var sample: Dictionary = clock.snapshot()
	sample.weather = "mutated"
	assert_str(clock.snapshot().weather).is_equal("clouds")

func test_invalid_configuration_is_atomic() -> void:
	var clock = _clock()
	clock.seek(31)
	var before: Dictionary = clock.snapshot()
	var cases := [[], [{"id": "late", "at": 0.1}], [{"id": "a", "at": 0}, {"id": "b", "at": 0}],
		[{"id": "a", "at": 0}, {"id": "a", "at": 0.5}], [{"id": "a", "at": 0}, {"id": "b", "at": 1}],
		[{"id": "a", "at": 0}, {"id": "b", "at": -0.1}], [{"id": "a", "at": false}],
		[{"id": "a", "at": NAN}], [{"id": " ", "at": 0}], [null], "phases"]
	for phases in cases:
		assert_bool(clock.configure(60, phases, "rain")).is_false()
		assert_dict(clock.snapshot()).is_equal(before)
		assert_str(clock.last_error).is_not_empty()
	for period in [0, -1, NAN, INF, false, "60", null]:
		assert_bool(clock.configure(period, [{"id": "a", "at": 0}], "rain")).is_false()
		assert_dict(clock.snapshot()).is_equal(before)

func test_invalid_time_and_weather_preserve_state_and_hooks() -> void:
	var clock = _clock()
	var received := []
	clock.changed.connect(func(value): received.append(value))
	var before: Dictionary = clock.snapshot()
	for value in [-1, NAN, INF, -INF, false, "1", null, 1.0e300]:
		assert_bool(clock.seek(value)).is_false()
		assert_bool(clock.advance(value)).is_false()
		assert_dict(clock.snapshot()).is_equal(before)
	for weather in ["", " ", null, 1, false]:
		assert_bool(clock.set_weather(weather)).is_false()
		assert_dict(clock.snapshot()).is_equal(before)
	assert_int(received.size()).is_equal(0)

func test_unconfigured_clock_has_no_time_or_hooks() -> void:
	var clock = CLOCK.new()
	assert_dict(clock.snapshot()).is_empty()
	assert_bool(clock.advance(1)).is_false()
	assert_bool(clock.seek(0)).is_false()
	assert_bool(clock.set_weather("rain")).is_false()

func test_explicit_rewind_and_fractional_period() -> void:
	var clock = CLOCK.new()
	assert_bool(clock.configure(2.5, [{"id": "one", "at": 0}, {"id": "two", "at": 0.8}], "clear", 7)).is_true()
	assert_int(clock.snapshot().day).is_equal(2)
	assert_str(clock.snapshot().phase).is_equal("two")
	clock.seek(0)
	assert_int(clock.snapshot().day).is_equal(0)
	assert_str(clock.snapshot().phase).is_equal("one")

func test_extreme_ratios_and_precision_loss_are_refused() -> void:
	var clock = _clock()
	var before: Dictionary = clock.snapshot()
	assert_bool(clock.configure(1.0e-300, [{"id": "one", "at": 0}], "clear", 1.0e300)).is_false()
	assert_dict(clock.snapshot()).is_equal(before)
	assert_bool(clock.seek(60.0 * CLOCK.MAX_EXACT_DAY)).is_false()
	clock.seek(1.0e12)
	before = clock.snapshot()
	assert_bool(clock.advance(1.0e-12)).is_false()
	assert_dict(clock.snapshot()).is_equal(before)

func test_partitioned_advances_match_external_samples() -> void:
	var incremental = _clock()
	var sampled = _clock()
	var rng := RandomNumberGenerator.new()
	rng.seed = 8619
	var total := 0.0
	for i in 200:
		var delta := rng.randi_range(0, 1000) * 0.25
		total += delta
		assert_bool(incremental.advance(delta)).is_true()
		assert_bool(sampled.seek(total)).is_true()
		assert_dict(incremental.snapshot()).is_equal(sampled.snapshot())

func test_failed_reconfiguration_emits_nothing_and_retains_pause() -> void:
	var clock = _clock()
	clock.set_active(false)
	var before: Dictionary = clock.snapshot()
	var received := []
	clock.changed.connect(func(value): received.append(value))
	for weather in ["", " ", null, 3]:
		assert_bool(clock.configure(60, [{"id": "one", "at": 0}], weather)).is_false()
	for elapsed in [-1, INF, NAN, true, "0"]:
		assert_bool(clock.configure(60, [{"id": "one", "at": 0}], "rain", elapsed)).is_false()
	assert_dict(clock.snapshot()).is_equal(before)
	assert_int(received.size()).is_equal(0)
	assert_bool(clock.configure(80, [{"id": "one", "at": 0}], "rain")).is_true()
	assert_bool(clock.snapshot().active).is_false()
	assert_bool(clock.advance(40)).is_true()
	assert_float(clock.snapshot().time).is_equal(0.0)
