class_name AbilityActionDriver
extends RefCounted
## Player-facing protocol. Subclasses own action timing/presentation/effects, never
## Player input reading, terrain collision or a second movement integration.
## This boundary deliberately installs no canonical/world driver yet.

func character_changed(_id: String) -> void:
	pass

func is_busy() -> bool:
	return false

func request(_action: String, _direction: Vector2) -> bool:
	return false

## active=false carries released controls: freeze combat time and clear held input.
## context.position is the post-collision actor position, in actor texels.
## guard has no new default binding; the existing InputMap must supply it explicitly.
func tick(_controls: Dictionary, _context: Dictionary, _delta: float) -> void:
	pass

func cancel(_reason: String) -> void:
	pass
