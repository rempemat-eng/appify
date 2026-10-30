#!/usr/bin/env node
/** Deterministic extraction from the archived pure engine and exact PR241 manifests. */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { canonicalProvenance, loadCanonicalCombat } from '../reference/adapter.mjs';

export const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const STUDIO_SHA = '4d7efc7085786c897fc0c50f7151a0ae7e62f0c2';
const plain = (value) => JSON.parse(JSON.stringify(value));
const sha = (value) => createHash('sha256').update(value).digest('hex');
export const encode = (value) => JSON.stringify(value, null, 2) + '\n';

function releaseProbe(engine, id, powered, action, contact = false) {
  const state = engine.createCombatState(id, 1, 'practice');
  if (powered) engine.__reference.activateForm(state);
  state.effects = [];
  if (contact) {
    state.enemies[0].x = state.player.x + 20;
    state.enemies[0].y = state.player.y;
    state.enemies.slice(1).forEach((enemy, index) => { enemy.x = 300; enemy.y = 24 + index * 140; });
  }
  const before = state.statistics.damageDealt;
  state.player.action = action;
  state.player.actionDuration = engine.__reference.duration(state.player, action);
  engine.__reference[action === 'primary' ? 'primary' : 'secondary'](state, action);
  const relative = (item) => {
    const out = plain(item);
    delete out.id;
    if ('x' in out) { out.offset_x = out.x - state.player.actionOriginX; delete out.x; }
    if ('y' in out) { out.offset_y = out.y - state.player.actionOriginY; delete out.y; }
    if ('fromX' in out) { out.from_offset_x = out.fromX - state.player.actionOriginX; delete out.fromX; }
    if ('fromY' in out) { out.from_offset_y = out.fromY - state.player.actionOriginY; delete out.fromY; }
    return out;
  };
  return plain({
    scenario: contact ? 'one stationary dummy 20 simulation units ahead; others distant' : 'default practice enemies; no travel step after release',
    damage_dealt_at_release: state.statistics.damageDealt - before,
    player_displacement_at_release: [state.player.x - state.player.actionOriginX, state.player.y - state.player.actionOriginY],
    projectiles: state.projectiles.map(relative),
    fields: state.fields.map(relative),
    effects: state.effects.map(relative),
    player_state: { ammo:state.player.ammo, reload:state.player.reload, heat:state.player.heat, tether_remaining:state.player.tetherRemaining, vault_remaining:state.player.vaultRemaining },
  });
}

export function deriveCanonical() {
  const engine = loadCanonicalCombat({ referenceHelpers:true });
  const annotationsBytes = readFileSync(resolve(ROOT, 'reference/source-rules.json'));
  const annotations = JSON.parse(annotationsBytes);
  const characters = {};
  for (const identity of engine.ROSTER) {
    const id = identity.id;
    const modes = {};
    for (const [mode, powered] of [['base', false], ['powered', true]]) {
      const state = engine.createCombatState(id, 1, 'practice');
      if (powered) engine.__reference.activateForm(state);
      const actions = {};
      for (const action of ['primary','secondary','special']) {
        state.player.action = action;
        state.player.actionDuration = engine.__reference.duration(state.player, action);
        actions[action] = {
          duration_seconds:state.player.actionDuration,
          release_seconds:engine.__reference.releaseTime(state.player),
          release_frame0:null,
        };
      }
      modes[mode] = {
        actions,
        primary_release_probe:releaseProbe(engine, id, powered, 'primary'),
        secondary_release_probe:releaseProbe(engine, id, powered, 'secondary'),
        primary_contact_probe:releaseProbe(engine, id, powered, 'primary', true),
        secondary_contact_probe:releaseProbe(engine, id, powered, 'secondary', true),
      };
    }
    characters[id] = {identity:plain(identity),source_derived_rules:annotations.characters[id],modes};
  }
  return plain({
    schema_version:1,
    authority:'Archived desktop combat simulation; numeric timings are independent of PR241 studio drawing cadence. This is extraction for the later agreed Godot port, not a production integration.',
    provenance:canonicalProvenance,
    units:{time:'seconds',distance:'original 320x180 simulation coordinates',angles:'radians',art_anchor_origin:null,target_grid:'960x540 logical pixels',conversion:'pending integration-owner decision; no factor-three distance conversion or factor-74/96 body conversion applied'},
    annotation_sha256:sha(annotationsBytes),
    annotation_method:'Global and per-character rule annotations transcribed from the pinned source; action clocks and release/contact probes executed from the original pure module.',
    global_source_derived_rules:annotations.global,
    characters,
  });
}

export function deriveStudio(studioRoot) {
  const canonical = deriveCanonical();
  const characters = {};
  for (const id of Object.keys(canonical.characters)) {
    const path = resolve(studioRoot, 'assets/animated', id, 'manifest.json');
    const bytes = readFileSync(path);
    const manifest = JSON.parse(bytes);
    const clips = {};
    for (const [name, clip] of Object.entries(manifest.clips)) {
      clips[name] = Object.fromEntries(['frame_count','durations','duration','loop','release_frame','release_time','release_anchor','contact_reach','hand_anchors','thruster_anchors','baked_effects','hold_frame'].filter((key) => key in clip).map((key) => [key,clip[key]]));
    }
    characters[id] = {
      manifest_sha256:sha(bytes),
      manifest_url:`https://github.com/rempemat-eng/appify/blob/${STUDIO_SHA}/prototypes/mygame-animation-studio/assets/animated/${id}/manifest.json`,
      view:manifest.view,frame_size:manifest.frame_size,foot_pivot:manifest.foot_pivot,body_height_target:manifest.body_height_target,fit_factor:manifest.fit_factor,
      clips,
      redraw_facings:{S:null,N:null,E:null,W:null},
      redraw_aim_poses:null,
      redraw_anchors_status:'pending Claude A authored per-facing anchors at the new approximately 74px body scale; no mirrored or inferred coordinates',
    };
  }
  const mismatches = [];
  for (const [id, entry] of Object.entries(characters)) {
    for (const [clipName, mode, action] of [['primary','base','primary'],['secondary','base','secondary'],['special','base','special'],['powered_primary','powered','primary']]) {
      const clip = entry.clips[clipName];
      const simulation = canonical.characters[id].modes[mode].actions[action];
      if (Math.abs(clip.duration - simulation.duration_seconds)>1e-8 || Math.abs(clip.release_time-simulation.release_seconds)>1e-8) mismatches.push({id,clip:clipName,studio_duration_seconds:clip.duration,canonical_duration_seconds:simulation.duration_seconds,studio_release_seconds:clip.release_time,canonical_release_seconds:simulation.release_seconds,resolution:'retime new art to canonical simulation event; author the new release frame explicitly'});
    }
  }
  return {
    schema_version:1,source_commit:STUDIO_SHA,
    authority:'Reference-only east-facing v3 drawing cadence and anchors. Never use these study mechanics as the canonical combat model.',
    units:{coordinates:'original studio logical image pixels',anchor_origin:'relative to each manifest foot pivot, +x right, +y down',canonical_simulation_coordinates:'separate 320x180 simulation domain; conversion pending'},
    characters,
    timing_mismatches:mismatches,
    semantic_mismatches:[
      'Studio E toggles an indefinite powered equipment review. Canonical special begins on release, expires after 8s (Nix7/Rook10), has25s cooldown and no manual toggle exit.',
      'Studio gates powered secondaries and traversal. Canonical powered secondaries remain available, and Rook can aim/fire during vault.',
      'Studio Morel rejects catalyst without marks; canonical has a close-range catalyst burst fallback.',
      'Studio Brine rejects untethered Q; canonical uses a gun-butt sweep.',
      'Studio Pendle fans all remaining rounds; canonical fans at most3, then reloads. Powered Q is a rifle-stock strike.',
      'Studio guard is an animation interruption/hold. Canonical guard has frontal geometry,100 meter, drain, absorption, recovery and guard break.',
      'Studio has cosmetic or simplified fields/turrets/heat. The recovered canonical engine defines actual status, field damage, heat, designated turret targets and finite lifecycles.',
      'Studio attacks emit east. Canonical action direction is a continuous committed vector with a cardinal presentation facing.',
      'Canonical Iona lunge is a clipped34-unit advance followed by a line strike. Studio uses a timed dash/contact sweep; preserve the canonical reference and agree world-collision adaptation during the port.',
      'Canonical reload timers are simulation-owned and can overlap movement/other permitted actions; studio Pendle has a blocking1.11s reload study. New art must not extend the rule timer.',
      'Old v3 audit claim that Brine gun-butt/Morel close burst were defects is superseded by recovered canonical source.',
      'New four-facing74px art and density3 world are not supplied by these manifests. Anchor and gameplay-unit conversion needs explicit integration agreement.'
    ],
  };
}

if (import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const index = process.argv.indexOf('--studio-root');
  if (index<0 || !process.argv[index+1]) throw new Error('Usage: node tools/extract-data.mjs --studio-root <exact PR241 prototype root> [--check]');
  const outputs = {'canonical.json':deriveCanonical(),'studio-reference.json':deriveStudio(process.argv[index+1])};
  mkdirSync(resolve(ROOT,'data'),{recursive:true});
  for (const [name,data] of Object.entries(outputs)) {
    const path = resolve(ROOT,'data',name);
    if (process.argv.includes('--check')) {
      if (readFileSync(path,'utf8')!==encode(data)) throw new Error(`${name}: data differs from deterministic extraction`);
    } else writeFileSync(path,encode(data));
    console.log(`${process.argv.includes('--check')?'PASS':'WROTE'}: ${name}`);
  }
}
