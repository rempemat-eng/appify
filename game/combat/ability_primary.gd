class_name AbilityPrimary
extends RefCounted
## Original E primary branch on canonical snapshots. No actor/HP attachment.
## Includes resources, launch and melee: dispatcher must not replay those separately.

static func release(source: Dictionary) -> Dictionary:
	var state := source.duplicate(true)
	var p: Dictionary = state.player
	var powered := AbilityImpacts._powered(state)
	var angle := atan2(p.actionDirY, p.actionDirX)
	p.combo += 1
	match str(p.id):
		"bramble": AbilitySecondary._launch(state, "arrow", angle, 205, 24 if powered else 22, 2, 0.92, 3 if powered else 0)
		"morel":
			var distance := AbilityImpacts._distance(p, {"x": p.aimX, "y": p.aimY})
			AbilitySecondary._launch(state, "flask", angle, 135, 14, 4, (clampf(distance, 28, 135) - 9) / 135)
		"velvet":
			var counter: bool = p.counterRemaining > 0
			state = AbilityStrikes.arc(state, 49 if counter else 29, 0.42, 35 if counter else 21, 13 if counter else 5)
			p = state.player
			if counter:
				p.counterRemaining = 0
				AbilityImpacts._fx(state, "counter", p.x + 30 * p.actionDirX, p.y + 30 * p.actionDirY, 20, 0.25)
		"cairn":
			state = AbilityStrikes.arc(state, 32, 0.35, 35, 12)
			if powered:
				state = AbilityStrikes.beam(state, 83, 11, 15, true, "shockwave")
		"iona": state = AbilityStrikes.beam(state, 48, 7, 23, true, "spear")
		"tam": state = AbilityStrikes.arc(state, 29, 0.4, 18, 4)
		"brine":
			p.tetherId = null
			p.tetherRemaining = 0
			state.projectiles = state.projectiles.filter(func(shot: Dictionary) -> bool: return shot.kind != "harpoon")
			p.ammo -= 1
			AbilitySecondary._launch(state, "harpoon", angle, 205 if powered else 175, 39 if powered else 29, 3, 0.95, 1 if powered else 0)
			_reload(state, 0.52 if powered else 0.95)
		"pendle":
			if powered:
				AbilitySecondary._launch(state, "rifle", angle, 320, 49, 2, 1, 4)
			else:
				p.ammo -= 1
				AbilitySecondary._launch(state, "bullet", angle, 290, 24, 2, 0.8)
				if p.ammo <= 0:
					_reload(state, 1.35)
		"mirra": AbilitySecondary._launch(state, "water", angle, 170, 21, 4, 1.05)
		"ashe":
			state = AbilityStrikes.arc(state, 32, 0.32, 24, 6)
			if powered:
				AbilitySecondary._launch(state, "flame-crescent", angle, 145, 15, 7, 0.65, 2)
		"clack":
			p.ammo -= 1
			for offset in [-0.09, 0, 0.09] if powered else [0]:
				AbilitySecondary._launch(state, "rocket", angle + offset, 145 if powered else 125, 20 if powered else 40, 4, 1.45, 0, 19 if powered else 23)
			_reload(state, 0.7 if powered else 1.15)
		"nix":
			p.heat = minf(100, p.heat + (12 if powered else 19))
			state = AbilityStrikes.beam(state, 175 if powered else 155, 4.5 if powered else 3, 15 if powered else 12, powered, "laser")
		"rook": AbilitySecondary._launch(state, "pulse", angle, 220, 16, 3, 1)
		"mote":
			for offset in [-0.11, 0, 0.11]:
				AbilitySecondary._launch(state, "glass", angle + offset, 210 if powered else 180, 12 if powered else 9, 2, 0.95, 1 if powered else 0)
			if powered:
				for offset in [-0.22, 0.22]:
					AbilitySecondary._launch(state, "orbit-shard", angle + offset, 190, 10, 2, 0.9, 1)
				AbilityImpacts._fx(state, "orbit", p.x, p.y, 18, 0.32)
	return state

static func _reload(state: Dictionary, duration: float) -> void:
	state.player.reload = duration
	AbilityDefence._event(state, "reload", "Reloading")
