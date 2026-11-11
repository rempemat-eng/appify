class_name AbilitySpecial
extends RefCounted
## Original M activation on a canonical snapshot. Caller owns eligibility/contact/once-only delivery.
## Includes resource refill/heat cap: do not apply AbilityResources' special release again.

static func activate(source: Dictionary) -> Dictionary:
	var state := source.duplicate(true)
	var player: Dictionary = state.player
	var kit := AbilityCatalogue.kit(str(player.id))
	player.specialDuration = kit.powered.duration_seconds
	player.specialRemaining = player.specialDuration
	AbilityImpacts._fx(state, "special", player.x, player.y, 22, 0.65)
	var special: String = kit.catalogue_prose.special
	AbilityDefence._event(state, "special-start", special.split(" — ")[0])
	if player.id in ["brine", "clack"]:
		player.reload = 0
		player.ammo = player.maxAmmo
	if player.id == "nix":
		player.heat = minf(player.heat, 45)
	if player.id == "mirra":
		# Power is already live here, so the shared field helper uses the powered seal cap.
		AbilityImpacts._field(state, "seal", player.x + 30 * player.actionDirX,
			player.y + 30 * player.actionDirY, 16, 8, 0)
	if player.id == "rook":
		# Replace the previous pair; preserve canonical left/right serial order and current aim.
		state.turrets = []
		for side in [-1, 1]:
			state.serial += 1
			state.turrets.append({"id": state.serial, "x": player.x + 15 * side,
				"y": player.y - 14, "radius": 5, "remaining": player.specialDuration,
				"cooldown": 0.18, "aimX": player.aimX, "aimY": player.aimY, "targetId": null})
	if player.id == "mote":
		AbilityImpacts._fx(state, "orbit", player.x, player.y, 18, 0.7)
	return state
