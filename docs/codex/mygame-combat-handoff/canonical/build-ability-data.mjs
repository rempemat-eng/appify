/** Build a source-only port handoff. This is data extraction, not a game runtime. */
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { loadCanonicalCombat } from './reference/adapter.mjs';

const catalogue = JSON.parse(readFileSync(new URL('./reference/catalogue.json', import.meta.url)));
const constants = JSON.parse(readFileSync(new URL('./reference/runtime-constants.json', import.meta.url)));
const original = JSON.parse(readFileSync(new URL('./reference/original-modules.json', import.meta.url)));
const engine = loadCanonicalCombat({ referenceHelpers: true });
const h = engine.__reference;
const hash = value => createHash('sha256').update(value).digest('hex');
if (hash(original.catalogue) !== constants.provenance.catalogueSha256 || hash(original.engine) !== constants.provenance.engineSha256) throw Error('Source module hash changed');

const arc = (reach, minimumDot, damage, knockback) => ({ kind: 'frontal_arc', reach, minimum_direction_dot: minimumDot, damage, knockback });
const lane = (reach, halfWidth, damage, pierces) => ({ kind: 'forward_segment', reach, half_width: halfWidth, damage, pierces });
const hit = {
  bramble: { primary: null, secondary: arc(36, -.1, 26, 25) },
  morel: { primary: null, secondary_fallback_without_reagent: arc(34, 0, 20, 13) },
  velvet: { primary: arc(29, .42, 21, 5), secondary: { ...arc(55, -.05, 9, 0), stun_seconds: .65, tank_stun_seconds: .25, vulnerable_seconds: 2.2 }, counter: arc(49, .42, 35, 13) },
  cairn: { primary: arc(32, .35, 35, 12), powered_extra_primary: lane(83, 11, 15, true) },
  iona: { primary: lane(48, 7, 23, true), secondary: { ...lane(49, 9, 29, true), move_forward: 34, movement_stops_before_enemy_radius_plus_player_radius_plus: 2, hit_knockback: 10 } },
  tam: { primary: arc(29, .4, 18, 4), secondary: lane(100, 8, 24, true) },
  brine: { secondary_fallback: arc(32, .2, 21, 16) },
  pendle: { powered_secondary: lane(44, .5, 22, false) },
  mirra: { secondary: { kind: 'aimed_disc', max_placement_distance: 112, radius: 18, damage: 10, slow_seconds: 1.5 } },
  ashe: { primary: arc(32, .32, 24, 6), secondary: lane(65, 9, 32, true), powered_secondary: lane(65, 9, 38, true), expiry_finisher: lane(98, 13, 34, true) },
  clack: { secondary: arc(43, .05, 25, 37) },
  nix: { primary: lane(155, 3, 12, false), powered_primary: lane(175, 4.5, 15, true) },
  rook: {}, mote: {},
};

const rules = {
  bramble: {
    powered_primary: { projectile_damage: 24, pierce_budget: 3, maximum_distinct_targets: 4, root_last_living_target_only: true, root_seconds: .8, tank_root_seconds: .3, clear_previous_arrow_hit_roots: true, powered_flag_captured_on_launch: true },
    source_functions: ['E', 'T'],
  },
  morel: {
    flask: { speed: 135, damage: 14, radius: 4, splash_radius: 16, aimed_distance_min: 28, aimed_distance_max: 135, lifetime_formula: '(clamp(aim_distance,28,135)-9)/135', leaves: { kind: 'reagent', radius: 18, lifetime_seconds: 5, damage_per_tick: 3, initial_tick_seconds: .2, tick_interval_seconds: .6, maximum_active: 4 } },
    catalyst: { select_prepared_reagent_within: 155, fallback_when_none: 'secondary close frontal burst:20 damage', consumes_each_selected_patch_once: true, explosion_extra_radius: 8, damage: 32, powered_damage: 39, knockback: 5, powered_chain_neighbour_distance: 46 },
    powered_flask_impact: { initial_neighbour_search_distance: 40, requires_more_than_one_reagent_patch: true, then_uses_powered_chain: true, powered_flag_captured_on_launch: true },
    source_functions: ['E', 'q', 'Y', 'T', 'G', '_'],
  },
  velvet: {
    lantern_flare_damage_order: { raw_damage: 9, applies_vulnerability_before_damage: true, resulting_damage_on_same_target: 12.15, vulnerability_damage_multiplier: 1.35 },
    successful_powered_frontal_guard: { primes_counter_seconds: 2, any_positive_absorbed_damage: true },
    counter: { next_primary_uses: 'counter hit shape', consumes_counter: true, survives_form_expiry_until_own_clock_expires: true, counter_requires_current_powered_form: false },
    powered_movement_echo: { spawn_interval_seconds: .4, initial_clock: 0, position_behind_actor: 8, radius: 11, lifetime_seconds: 1.15, maximum_active: 4, damage: 0, attracts_live_enemies: true, destroyed_by_one_enemy_projectile_or_melee_hit: true },
    source_functions: ['v', 'E', 'P', 'Y', 'F', 'L', 'X'],
  },
  cairn: {
    boulder: { speed: 115, radius: 7, lifetime_seconds: 1.3, damage: 34, powered_damage: 40, pierce_budget: 0, powered_blast_radius: 30, powered_blast_knockback: 13 },
    powered_primary: { normal_fist_plus_forward_shockwave: true, shockwave: hit.cairn.powered_extra_primary },
    source_functions: ['E', 'q', 'T'],
  },
  iona: {
    secondary_lunge: hit.iona.secondary,
    powered_hit_arc: { to_one_nearest_other_living_enemy: true, max_distance_strictly_less_than: 55, damage: 12, does_not_recursively_trigger_another_arc: true },
    powered_secondary_wake: { kind: 'gust', centred_between_start_and_end_of_lunge: true, radius: 25, lifetime_seconds: 1.5, damage_per_tick: 8, initial_tick_seconds: .2, tick_interval_seconds: .6 },
    source_functions: ['q', 'B', '_'],
  },
  tam: {
    each_eligible_hit: { frost_added: 1, frost_cap: 3, slow_seconds: 1.2, frost_cleared_after_no_hit_seconds: 3 },
    powered_shatter_at_three_frost: { reset_frost_to: 0, extra_damage: 23, root_seconds: .85, tank_root_seconds: .3, no_recursive_frost_from_shatter: true },
    secondary_ridge: { slow_seconds: 2, powered_root_seconds: .6, powered_tank_root_seconds: .22 },
    secondary_ice_field: { forward_placement: 52, radius: 19, lifetime_seconds: 2, damage: 0, refresh_slow_seconds: .7, initial_tick_seconds: .2, tick_interval_seconds: .6 },
    powered_movement_multiplier: 1.28,
    source_functions: ['v', 'q', 'B', 'L', '_'],
  },
  brine: {
    primary: { replaces_previous_harpoon_projectiles_and_tether: true, reload_seconds: .95, powered_reload_seconds: .52 },
    harpoon_hit: { attaches_last_living_hit_target: true, tether_seconds: 3, powered_tether_seconds: 4, powered_flag_captured_on_launch: true },
    secondary_reel: { requires_living_tether_target_within: 185, light_target_pull: 42, powered_light_target_pull: 61, heavy_kinds: ['tank', 'dummy'], heavy_target_pulls_operator_instead: true, stop_gap_formula: 'player_radius+target_radius+3', damage: 15, powered_damage: 23, powered_tether_remaining_after_reel: 2, ordinary_reel_clears_tether: true },
    secondary_without_valid_tether: hit.brine.secondary_fallback,
    activation: { refill_ammo: true, clear_reload: true },
    source_functions: ['E', 'q', 'M', 'T', 'v'],
  },
  pendle: {
    revolver_capacity: 6,
    ordinary_primary: { consume_rounds: 1, reload_on_empty_seconds: 1.35 },
    ordinary_secondary: { shots: 'min(3,current_ammo)', angle_spacing_radians: .11, bullet_damage: 18, speed: 270, radius: 2, lifetime_seconds: .75, reload_after_fan_seconds: 1.4 },
    powered_primary: { rifle_damage: 49, speed: 320, pierce_budget: 4, maximum_distinct_targets: 5, consume_rounds: 0, ignores_ordinary_ammo_reload_gate: true, duration_seconds: .9 },
    powered_secondary: hit.pendle.powered_secondary,
    activation: { does_not_refill_ammo_or_clear_reload: true },
    source_functions: ['w', 'E', 'q', 'M', 'v'],
  },
  mirra: {
    primary_through_seal: { only_if_seal_crossing_precedes_or_ties_first_enemy_collision: true, once_per_projectile: true, damage_after_amplification: 28, radius_after_amplification: 6, pierce_budget_after_amplification: 1, maximum_distinct_targets: 2 },
    secondary_seal: { max_aimed_distance: 112, radius: 18, lifetime_seconds: 6, powered_lifetime_seconds: 8, replacement_threshold: 3, powered_replacement_threshold: 5, insertion_removes_exactly_one_oldest_if_count_at_least_threshold: true, form_expiry_does_not_shrink_existing_five_seals_to_three: true, hit_damage: 10, hit_slow_seconds: 1.5 },
    activation_seal: { forward_placement: 30, radius: 16, lifetime_seconds: 8 },
    powered_current_network: { interval_seconds: .35, initial_clock: 0, ordered_segments: 'player to oldest seal, then each previous seal to next seal', half_width: 6, damage: 10, slow_seconds: .5, once_per_enemy_per_network_tick: true, stops_when_form_expires: true },
    source_functions: ['E', 'q', 'M', 'Y', 'F', '_'],
  },
  ashe: {
    powered_primary_addition: { kind: 'flame-crescent', speed: 145, damage: 15, radius: 7, lifetime_seconds: .65, pierce_budget: 2 },
    powered_secondary_flame: { forward_placement: 42, radius: 15, lifetime_seconds: 2, damage_per_tick: 8, initial_tick_seconds: .2, tick_interval_seconds: .6 },
    natural_expiry_finisher: { hit: hit.ashe.expiry_finisher, uses_current_aim_direction_at_expiry: true, requires_alive: true, suppressed_on_interruption_or_defeat: true, flame: { forward_placement: 52, radius: 16, lifetime_seconds: 1, damage_per_tick: 7 } },
    source_functions: ['E', 'q', 'X', '_'],
  },
  clack: {
    capacity: 1,
    ordinary_primary: { rocket_count: 1, damage_per_rocket: 40, speed: 125, blast_radius: 23, reload_seconds: 1.15 },
    powered_primary: { rocket_count: 3, angle_offsets_radians: [-.09, 0, .09], damage_per_rocket: 20, speed: 145, blast_radius: 19, reload_seconds: .7, mobile_during_salvo: true },
    all_rockets: { radius: 4, lifetime_seconds: 1.45, blast_knockback: 6 },
    secondary_vent: { usable_during_primary_reload: true, hit: hit.clack.secondary },
    activation: { refill_ammo: true, clear_reload: true },
    source_functions: ['E', 'q', 'M', 'w', 'T'],
  },
  nix: {
    heat: { maximum: 100, block_primary_when_at_least: 92, primary_adds: 19, powered_primary_adds: 12, cooling_per_second_during_primary: 4, cooling_per_second_other_powered_actions: 7, cooling_per_second_other_ordinary_actions: 15 },
    secondary_afterimage: { kind: 'hologram', at_action_commitment_origin: true, stationary: true, radius: 7, lifetime_seconds: 3, maximum_active: 1, damage: 0, destroyed_by_one_enemy_projectile_or_melee_hit: true, attracts_live_enemies: true, direct_release_heat_change: 0, normal_per_tick_cooling_continues: true, guarantees_projectile_interception: false },
    activation: { cap_existing_heat_at: 45 },
    source_functions: ['E', 'q', 'M', 'v', 'Y', 'F', 'L'],
  },
  rook: {
    vault: constants.vault,
    vault_direction: 'movement direction if movement length>0.1; otherwise aim direction at commitment',
    carbine_hit: { designates_last_living_target_seconds: 1.2 },
    powered_turrets: { count: 2, lifetime_seconds: 10, initial_offsets: [[-15, -14], [15, -14]], target_follow_offsets: [[-16, -14], [16, -14]], follow_factor_per_fixed_step: 7 / 60, require_designated_living_target_operator_distance_strictly_less_than: 190, require_turret_operator_distance_strictly_less_than: 55, preserves_live_existing_designation_on_activation: true, initial_cooldown_seconds: .18, firing_interval_seconds: .44, projectile: { kind: 'turret-pulse', speed: 205, radius: 2, lifetime_seconds: 1, damage: 7, pierce_budget: 0 }, removed_at_form_expiry_or_defeat: true },
    source_functions: ['v', 'q', 'M', 'T', 'N', 'P', 'X'],
  },
  mote: {
    ordinary_primary: { shards: 3, angle_offsets_radians: [-.11, 0, .11], kind: 'glass', speed: 180, damage: 9, radius: 2, lifetime_seconds: .95, pierce_budget: 0 },
    powered_primary: { main_shards: 3, speed: 210, damage: 12, pierce_budget: 1, extra_shards: { count: 2, kind: 'orbit-shard', angle_offsets_radians: [-.22, .22], speed: 190, damage: 10, radius: 2, lifetime_seconds: .9, pierce_budget: 1 } },
    secondary_gravity: { max_aimed_distance: 100, radius: 32, powered_radius: 39, lifetime_seconds: 1.8, powered_lifetime_seconds: 2.3, damage_per_tick: 4, initial_tick_seconds: .2, tick_interval_seconds: .45, light_pull_units_per_second: 32, heavy_pull_units_per_second: 13, heavy_kinds: ['tank', 'dummy'], refresh_slow_seconds: .2 },
    powered_orbit_visual: { effect_on_activation_seconds: .7, effect_after_primary_seconds: .32, autonomous_damaging_orbit_entities: false },
    source_functions: ['E', 'q', 'M', '_'],
  },
};

function projectileData(id, powered) {
  const snapshot = constants.characters[id][powered ? 'powered' : 'base'].primaryRelease;
  return snapshot.projectiles.map(p => ({
    kind: p.kind,
    speed: Math.hypot(p.vx, p.vy),
    angle_offset_radians: Number(Math.atan2(p.vy, p.vx).toFixed(12)),
    planar_spawn_forward: 9,
    radius: p.radius,
    lifetime_seconds: id === 'morel' ? null : p.remaining,
    ...(id === 'morel' ? { lifetime_formula: '(clamp(aim_distance,28,135)-9)/135' } : {}),
    damage: p.damage,
    pierce_budget: p.pierce,
    blast_radius: p.blastRadius,
    powered_at_launch: p.powered,
  }));
}

const characters = catalogue.CHARACTER_IDS.map(id => {
  const c = catalogue.ROSTER.find(c => c.id === id);
  const base = engine.createCombatState(id, 1, 'practice');
  const actionData = powered => {
    const state = engine.createCombatState(id, 1, 'practice');
    if (powered) state.player.specialRemaining = constants.formDurations[id] ?? constants.formDurations.default;
    const result = {};
    for (const action of ['primary', 'secondary', 'special']) {
      state.player.action = action;
      state.player.actionDuration = h.duration(state.player, action);
      result[action] = { duration_seconds: state.player.actionDuration, release_seconds: h.releaseTime(state.player), cooldown_seconds: action === 'primary' ? state.player.actionDuration : action === 'special' ? constants.specialCooldown : constants.secondaryCooldowns[id] ?? constants.secondaryCooldowns.default };
    }
    result.block = { raise_seconds: .18, hold_until_released: true, damage_release_event: false };
    return result;
  };
  return {
    id, name: c.name,
    catalogue_prose: { role: c.role, primary: c.primary, secondary: c.secondary, block: c.block, special: c.special },
    planar_speed: constants.planarSpeed[id] ?? constants.planarSpeed.default,
    resources: { ammo_capacity: base.player.maxAmmo, initial_ammo: base.player.ammo, reload_complete_refills_to_capacity: true, initial_heat: base.player.heat },
    base: { actions: actionData(false), primary_projectiles: projectileData(id, false) },
    powered: { actions: actionData(true), primary_projectiles: projectileData(id, true), duration_seconds: constants.formDurations[id] ?? constants.formDurations.default, starts_at_special_release: true },
    hit_shapes: hit[id],
    executed_rules: rules[id],
    art_contract: { release_frame_indices: 'supplied separately by the animation manifest; not inferred from seconds or fixed frame counts', per_facing_screen_anchors: 'new74px art must author these; original planar projectile seed9 is not a screen muzzle anchor', cardinal_aim_quantisation: 'presentation facing only; simulation retains continuous aim' },
  };
});

const document = {
  schema_version: 1,
  status: 'recovered_numeric_contract_for_owner_review',
  source: { repository: 'rempemat-eng/appify', commit: '1cd2a03d3dedb86061c5e32f53836cc284cbf6ab', reference_path: 'prototypes/mygame-world-preview/reference/', ...constants.provenance, recovery_kind: 'compiled original catalogue and pure engine; original TypeScript not recovered' },
  units: { distance: 'original canonical planar units', time: 'seconds', angle: 'radians', original_arena: constants.arena, rendering_density_changes_balance: false, port_scale_decision: 'unresolved: agree original-unit to foundation-world conversion; density3 does not by itself authorise multiplying reach/speed/radius', screen_anchors: 'separate source texels relative to each facing foot pivot' },
  simulation: { fixed_step_seconds: constants.fixedStep, maximum_step_input_seconds: constants.maxStepInput, epsilon: constants.epsilon, inactive_input_freezes_simulation: true, input: constants.actionInput, queue: { slots: 1, lifetime_seconds: .7, latest_eligible_rising_edge_overwrites_slot: true, simultaneous_eligible_rising_edges_prefer: 'special', slot_consumed_when_commit_is_attempted: true }, commit_priority: ['block', 'queued_slot', 'held_primary'], special_cooldown_starts_on_commitment: true, damage_is_not_emitted_by_drawing_preview: true },
  shared_hit_rules: { damage_values_are_raw_before_vulnerability: true, arc_target_test: 'distance<=reach+target_radius and (relative_x*aim_x+relative_y*aim_y)/max(1,distance)>=minimum_direction_dot', segment_target_test: 'projection between -target_radius and reach+target_radius, and point-to-segment distance<=half_width+target_radius', vulnerable_damage_multiplier: 1.35, heavy_knockback_multiplier: .25, heavy_kinds: ['tank', 'dummy'] },
  common_field_insertion: { default_replacement_threshold: 10, removes_exactly_one_oldest_same_kind_before_append_if_count_at_least_threshold: true, threshold_is_not_a_truncate_all_hard_cap: true },
  guard: { ...constants.guard, recovery_condition: 'not blocking and guardRecovery<=epsilon and guardBroken<=epsilon; action need not be idle', idleRecoveryPerSecond_is_a_legacy_extraction_label_not_an_idle_gate: true },
  movement_multipliers: constants.speedMultipliers,
  common_projectile_metadata: { planar_seed_forward: 9, flight_duration_formula: 'clamp((current_aim_distance-9)/speed,0.05,lifetime_seconds)', launch_height_captured_from_player_vault_height: true, simulation_travel_is_planar: true, turret_pulses_use_own_turret_origin_and_launch_height_zero: true },
  common_form_rules: { active_if_remaining_greater_than_epsilon: true, start_at_special_release: true, ordinary_duration_seconds: 8, nix_duration_seconds: 7, rook_duration_seconds: 10, cooldown_seconds: 25, expiry_does_not_clear_existing_projectiles_or_fields: true, exceptions: ['Rook turrets and designation removed on form end', 'Ashe natural live expiry emits aimed finisher; interruption suppresses it', 'Defeat clears all projectiles/fields/turrets and vault', 'Non-practice wave victory clears projectiles/fields/turrets/vault and sets formRemaining0 directly, bypassing Ashe finisher'], engine_performs_no_general_powered_exit_action_lock: true },
  characters,
  unresolved_for_foundation_owner: [
    'Original planar-unit to new foundation-world conversion; preserve time/damage/ammo independently of art density.',
    'New74px per-facing muzzle/contact/held-prop/nozzle anchors and release-frame indices; old generated art is reference only.',
    'Production wall/terrain/deck collision rules and collision groups. The original arena engine has no authored wall/stair map contract.',
    'Confirm intentional differences before porting v4 studio extensions such as autonomous Mote orbiters or a counter restricted to current powered mode.',
  ],
};

writeFileSync(new URL('./abilities-v1.json', import.meta.url), JSON.stringify(document, null, 2) + '\n');
console.log(JSON.stringify({ characters: characters.length, actions: characters.reduce((n,c) => n + Object.keys(c.base.actions).length + Object.keys(c.powered.actions).length, 0), output: 'abilities-v1.json', bytes: Buffer.byteLength(JSON.stringify(document, null, 2) + '\n') }));
