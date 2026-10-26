class_name AbilityActionDriver
extends RefCounted
## Player-facing protocol. Subclasses own action timing/presentation/effects, never
## Player input reading, terrain collision or a second movement integration.
## This boundary deliberately installs no canonical/world driver yet.

## Opt in only when tick will call context.move_actor for each fixed simulation step.
func plans_movement() -> bool:
	return false

func character_changed(_id: String) -> void:
	pass

func is_busy() -> bool:
	return false

func request(_action: String, _direction: Vector2) -> bool:
	return false

## active=false carries released controls: freeze combat time and clear held input.
## context.position is the current actor position, in actor texels; planned drivers
## apply their ordered targets through context.move_actor, otherwise Player already moved.
## guard has no new default binding; the existing InputMap must supply it explicitly.
func tick(_controls: Dictionary, _context: Dictionary, _delta: float) -> void:
	pass

func cancel(_reason: String) -> void:
	pass
