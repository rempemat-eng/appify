class_name AbilityResources
extends RefCounted
## Resource part of the recovered engine (w/E/q/M/v). No damage or presentation.
## Runner must check eligible BEFORE clock commitment, advance at clock boundaries,
## and call release once per action token, using powered state at RELEASE (oracle E/q).

var character := ""
var kit := {}
var ammo := 0
var heat := 0.0
var reload_remaining := 0.0

func configure(id: String) -> bool:
	var data := AbilityCatalogue.kit(id)
	if data.is_empty():
		return false
	character = id
	kit = data
	ammo = int(kit.resources.initial_ammo)
	heat = float(kit.resources.initial_heat)
	reload_remaining = 0.0
	return true

func eligible(action: String, powered: bool) -> bool:
	if kit.is_empty() or action not in ["primary", "secondary", "special"]:
		return false
	if character == "nix" and action == "primary":
		return heat < float(kit.executed_rules.heat.block_primary_when_at_least)
	var needs_ammo := action == "primary" or (action == "secondary" and character == "pendle")
	if not needs_ammo or int(kit.resources.ammo_capacity) == 0:
		return true
	if character == "pendle" and powered:
		return true # both rifle and stock ignore ordinary revolver reload
	return reload_remaining <= 0.00000001 and ammo > 0

## Called only at the actual release. Cancelled preparation consumes nothing.
## Returns rounds emitted so the effect handler cannot invent a full three-shot fan.
func release(action: String, powered: bool) -> int:
	if kit.is_empty():
		return 0
	var rules: Dictionary = kit.executed_rules
	if action == "special":
		if character in ["brine", "clack"]:
			ammo = int(kit.resources.ammo_capacity)
			reload_remaining = 0.0
		elif character == "nix":
			heat = minf(heat, float(rules.activation.cap_existing_heat_at))
		return 0
	if character == "pendle":
		if powered:
			return 1 if action == "primary" else 0
		if action == "primary":
			ammo -= int(rules.ordinary_primary.consume_rounds)
			if ammo <= 0:
				reload_remaining = float(rules.ordinary_primary.reload_on_empty_seconds)
			return 1
		if action == "secondary":
			var shots := mini(3, ammo)
			ammo -= shots
			reload_remaining = float(rules.ordinary_secondary.reload_after_fan_seconds)
			return shots
	if action != "primary":
		return 0 # Nix afterimage / Clack vent do not clear heat or reload
	if character == "brine":
		ammo -= 1
		reload_remaining = float(rules.primary.powered_reload_seconds if powered else rules.primary.reload_seconds)
		return 1
	if character == "clack":
		ammo -= 1
		var spec: Dictionary = rules.powered_primary if powered else rules.ordinary_primary
		reload_remaining = float(spec.reload_seconds)
		return int(spec.rocket_count)
	if character == "nix":
		heat = minf(float(rules.heat.maximum), heat + float(rules.heat.powered_primary_adds if powered else rules.heat.primary_adds))
	return 0

## The caller splits time at action/release/form boundaries; passing inactive time freezes all.
func advance(delta: float, action: String, powered: bool, active: bool = true) -> void:
	if not active or delta <= 0.0 or kit.is_empty():
		return
	if reload_remaining > 0.0:
		reload_remaining = maxf(0.0, reload_remaining - delta)
		if reload_remaining <= 0.00000001:
			reload_remaining = 0.0
			ammo = int(kit.resources.ammo_capacity)
	if character == "nix":
		var rules: Dictionary = kit.executed_rules.heat
		var rate := float(rules.cooling_per_second_during_primary) if action == "primary" else float(rules.cooling_per_second_other_powered_actions if powered else rules.cooling_per_second_other_ordinary_actions)
		heat = maxf(0.0, heat - delta * rate)
