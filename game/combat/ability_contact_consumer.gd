class_name AbilityContactConsumer
extends RefCounted
## Optional presentation-only consumer of AbilityArenaDriver.player_phase_observed.
## No canonical damage/resource/projectile mutation, actor attachment or inferred art clocks.

var _track := AbilityContactTrack.new()
var _provider := Callable()
var _passive_provider := Callable()
var _passive := AbilityPoseTrack.new()
var _forms := AbilityFormTrack.new()
var _passive_mode := ""
var _passive_key := ""
var _draw := Callable()
var _contact := Callable()
var _token := 0
var _generation := 0
var _action := ""
var _last_tick := -1
var last_error := ""

## provider(after, action) returns manifest, clip, facing, durations and optional aim.
## It must supply the explicit owner-approved schedule, not the art's template clock.
func configure(provider: Callable, draw: Callable, contact: Callable, passive_provider: Callable = Callable()) -> bool:
	if not provider.is_valid() or not draw.is_valid() or not contact.is_valid():
		return false
	cancel()
	_provider = provider
	_passive_provider = passive_provider
	_draw = draw
	_contact = contact
	_last_tick = -1
	last_error = ""
	return true

func cancel() -> void:
	_generation += 1
	_track.cancel()
	_passive.cancel()
	_forms.cancel()
	_passive_mode = ""
	_passive_key = ""
	_action = ""

## Connect this to the driver's fixed player-phase signal. Call cancel on actor
## detach/reset/defeat. Pauses emit no phase signal and therefore consume no drawings.
func observe(before: Dictionary, after: Dictionary, delta: float) -> void:
	if not _provider.is_valid() or not is_finite(delta) or delta <= 0:
		return
	if after.has("tick"):
		if int(after.tick) <= _last_tick:
			return
		_last_tick = int(after.tick)
	var old: Dictionary = before.player
	var current: Dictionary = after.player
	if current.hp <= 0 or before.player.id != current.id:
		cancel()
		return
	if current.blocking:
		if _action != "": cancel()
		_observe_passive(after, delta)
		return
	var committed := ""
	for action in ["primary", "secondary", "special"]:
		if after.statistics.actions[action] > before.statistics.actions[action]:
			committed = action
	# The old action may finish and commit another action during the same fixed tick.
	# Finish its ordered samples first; never infer a new instance from elapsed alone.
	if _action != "":
		if old.action != _action or (current.action != _action and committed == "" and current.action != "idle"):
			cancel()
		else:
			var generation := _generation
			_deliver(_track.advance(delta))
			if generation != _generation:
				return # a presentation callback cancelled/replaced the sequence
			if current.action != _action or committed != "" or _track.is_finished():
				cancel()
	if committed != "":
		_begin(after, committed)
	if _action == "" and current.action in ["idle", "walk"]:
		_observe_passive(after, delta)

func _begin(state: Dictionary, action: String) -> void:
	_passive.cancel()
	_forms.cancel()
	_passive_mode = ""
	_passive_key = ""
	var generation := _generation
	var supplied: Variant = _provider.call(state.duplicate(true), action)
	if generation != _generation:
		return
	if not supplied is Dictionary or not supplied.has_all(["manifest", "clip", "facing", "durations"]):
		last_error = "missing explicit presentation contract"
		return
	var manifest: Variant = supplied.manifest
	var durations: Variant = supplied.durations
	if not manifest is Dictionary or not durations is Array:
		last_error = "invalid presentation contract"
		return
	var clip := str(supplied.clip)
	var clips: Variant = manifest.get("clips")
	if not clips is Dictionary:
		last_error = "missing presentation clips"
		return
	var info: Variant = clips.get(clip)
	if not info is Dictionary:
		last_error = "missing presentation clip"
		return
	var release: Variant = info.get("release_frame")
	if not (release is int or release is float) or not is_finite(float(release)) or release != floor(float(release)) or release < 0 or release >= durations.size():
		last_error = "invalid presentation release drawing"
		return
	var total := 0.0
	var contact_at := 0.0
	for index in durations.size():
		var duration: Variant = durations[index]
		if not (duration is int or duration is float) or not is_finite(float(duration)) or duration <= 0:
			last_error = "invalid presentation duration"
			return
		if index < int(release):
			contact_at += float(duration)
		total += float(duration)
	# Canonical clocks remain authoritative. Reject, rather than silently retime art.
	if absf(total - float(state.player.actionDuration)) > 1.0e-8 or absf(contact_at - AbilityPlayerPhase._release_time(state.player)) > 1.0e-8:
		last_error = "presentation schedule differs from canonical action clock"
		return
	_token += 1
	if not _track.configure(manifest, clip, str(supplied.facing), durations, _token, str(supplied.get("aim", ""))):
		last_error = "missing presentation variant or malformed frames"
		return
	_action = action
	last_error = ""
	_deliver(_track.advance(0.0))

func _deliver(events: Array[Dictionary]) -> void:
	var generation := _generation
	for event in events:
		if generation != _generation:
			return
		if event.kind == "drawing":
			_draw.call(event.sample.duplicate(true))
		else:
			_contact.call(event.sample.duplicate(true))

## The optional provider selects state/clip and supplies approved durations explicitly.
## No passive pose can cover an active action or generate a release/contact callback.
func _observe_passive(state: Dictionary, delta: float) -> void:
	if not _passive_provider.is_valid():
		return
	var generation := _generation
	var supplied: Variant = _passive_provider.call(state.duplicate(true), "")
	if generation != _generation:
		return
	if supplied is Dictionary and supplied.has("plan"):
		_observe_form(supplied, delta)
		return
	if not supplied is Dictionary or not supplied.has_all(["key", "manifest", "clip", "facing", "durations"]):
		last_error = "missing explicit passive presentation contract"
		return
	if not supplied.manifest is Dictionary or not supplied.durations is Array or not supplied.key is String:
		last_error = "invalid passive presentation contract"
		return
	var key: String = supplied.key
	var same_state := key == _passive_key
	if same_state and _passive_mode != "pose":
		last_error = "passive mode change requires a new state key"
		return
	if not _passive.configure(key, supplied.manifest, str(supplied.clip), str(supplied.facing),
			supplied.durations, _token + 1, str(supplied.get("aim", ""))):
		last_error = "invalid passive variant or implicit retiming"
		return
	_token += 1
	_forms.cancel()
	_passive_mode = "pose"
	_passive_key = key
	last_error = ""
	_draw.call(_passive.advance(delta if same_state else 0.0).duplicate(true))

## Explicit finite form plans are passive presentation only. Active actions keep
## their canonical contact timeline; living-actor cancellation still applies.
func _observe_form(supplied: Dictionary, delta: float) -> void:
	if not supplied.has_all(["key", "manifest", "plan", "segment_durations"]) or not supplied.key is String or not supplied.manifest is Dictionary or not supplied.plan is Array or not supplied.segment_durations is Array:
		last_error = "missing explicit form schedule"
		return
	var key: String = supplied.key
	var same_state := key == _passive_key
	if same_state and _passive_mode != "form":
		last_error = "passive mode change requires a new state key"
		return
	if not _forms.configure(key, supplied.manifest, supplied.plan, supplied.segment_durations, _token + 1):
		last_error = "invalid form plan or implicit retiming"
		return
	_token += 1
	_passive.cancel()
	_passive_mode = "form"
	_passive_key = key
	last_error = ""
	_draw.call(_forms.advance(delta if same_state else 0.0).duplicate(true))
