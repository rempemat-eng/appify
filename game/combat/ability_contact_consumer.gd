class_name AbilityContactConsumer
extends RefCounted
## Optional presentation-only consumer of AbilityArenaDriver.player_phase_observed.
## No canonical damage/resource/projectile mutation, actor attachment or inferred art clocks.

var _track := AbilityContactTrack.new()
var _provider := Callable()
var _draw := Callable()
var _contact := Callable()
var _token := 0
var _generation := 0
var _action := ""
var _last_tick := -1
var last_error := ""

## provider(after, action) returns manifest, clip, facing, durations and optional aim.
## It must supply the explicit owner-approved schedule, not the art's template clock.
func configure(provider: Callable, draw: Callable, contact: Callable) -> bool:
	if not provider.is_valid() or not draw.is_valid() or not contact.is_valid():
		return false
	cancel()
	_provider = provider
	_draw = draw
	_contact = contact
	_last_tick = -1
	last_error = ""
	return true

func cancel() -> void:
	_generation += 1
	_track.cancel()
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
	if current.hp <= 0 or current.blocking or before.player.id != current.id:
		cancel()
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

func _begin(state: Dictionary, action: String) -> void:
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
