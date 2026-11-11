class_name AbilityRunner
extends RefCounted
## Simulation binding only. Release commands are not world hits; the later effect bridge
## must present contact first and capture launch state. This never touches world HP or art.

var clock := AbilityClock.new()
var resources := AbilityResources.new()
var _release_commands: Array[Dictionary] = []
var _last_release_instance := -1

func configure(id: String) -> bool:
	if AbilityCatalogue.kit(id).is_empty():
		return false
	clock.configure(id)
	resources.configure(id)
	clock.can_commit = resources.eligible
	clock.next_boundary = resources.next_boundary
	clock.time_slice = resources.advance
	clock.on_release = _release
	_release_commands.clear()
	_last_release_instance = -1
	return true

func commit(action: String) -> bool:
	return clock.commit(action)

func input(primary: bool, secondary: bool, special: bool, guard: bool) -> void:
	clock.input(primary, secondary, special, guard)

func advance(delta: float, active: bool = true) -> void:
	clock.advance(delta, active)

func cancel(reason: String = "interrupted") -> void:
	clock.cancel(reason)

func drain_release_commands() -> Array[Dictionary]:
	var commands := _release_commands
	_release_commands = []
	return commands

func _release(event: Dictionary) -> void:
	if int(event.instance) <= _last_release_instance:
		return
	_last_release_instance = int(event.instance)
	var command := event.duplicate(true)
	command["rounds"] = resources.release(str(event.action), bool(event.powered_at_release))
	_release_commands.append(command)
