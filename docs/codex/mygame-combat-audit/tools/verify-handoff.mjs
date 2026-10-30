#!/usr/bin/env node
/** Verify extraction fidelity and the rules most likely to be lost during the port. */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { ROOT, deriveCanonical } from './extract-data.mjs';
import { loadCanonicalCombat } from '../reference/adapter.mjs';

let checks = 0;
const check = (condition, message) => { assert.ok(condition, message); checks++; };
const equal = (actual, expected, message) => { assert.deepEqual(actual, expected, message); checks++; };
const near = (actual, expected, message) => check(Math.abs(actual-expected)<1e-8, message);
const canonical = JSON.parse(readFileSync(resolve(ROOT,'data/canonical.json'),'utf8'));
const studio = JSON.parse(readFileSync(resolve(ROOT,'data/studio-reference.json'),'utf8'));
const expected = deriveCanonical();
equal(canonical, expected, 'Canonical data must equal fresh execution from the pinned modules');
const ids = Object.keys(expected.characters);
equal(Object.keys(studio.characters), ids, 'All fourteen studio identities must match the canonical roster');
equal(ids.length, 14, 'Fourteen characters');

let clips = 0;
for (const [id,entry] of Object.entries(studio.characters)) {
  equal(entry.view,'E',`${id}: no fabricated directional coverage`);
  equal(entry.redraw_facings,{S:null,N:null,E:null,W:null},`${id}: new anchors await authoring`);
  for (const [name,clip] of Object.entries(entry.clips)) {
    clips++;
    equal(clip.frame_count,clip.durations.length,`${id}/${name}: frame count`);
    check(clip.durations.every((n)=>Number.isFinite(n)&&n>0),`${id}/${name}: positive finite holds`);
    near(clip.duration,clip.durations.reduce((a,b)=>a+b,0),`${id}/${name}: total time`);
    if (clip.release_frame!==null) {
      check(Number.isInteger(clip.release_frame)&&clip.release_frame>=0&&clip.release_frame<clip.frame_count,`${id}/${name}: zero-based release frame`);
      near(clip.release_time,clip.durations.slice(0,clip.release_frame).reduce((a,b)=>a+b,0),`${id}/${name}: release at frame start`);
    }
  }
}
equal(clips,239,'All239 published clips included');

const engine=loadCanonicalCombat({referenceHelpers:true});
const dt=1/60;
for (const id of ids) for (const powered of [false,true]) {
  let state=engine.createCombatState(id,1,'practice');
  if(powered)engine.__reference.activateForm(state);
  state=engine.stepCombat(state,{primary:true,aimX:220,aimY:98},dt);
  const target=canonical.characters[id].modes[powered?'powered':'base'].actions.primary;
  let ticks=0;
  while(!state.player.actionReleased&&ticks++<100)state=engine.stepCombat(state,{primary:true,aimX:220,aimY:98},dt);
  check(ticks<100,`${id}/${powered}: primary actually releases`);
  check(state.player.actionElapsed+1e-8>=target.release_seconds&&state.player.actionElapsed<target.release_seconds+dt+1e-8,`${id}/${powered}: public fixed-step event matches extracted time`);
}

for (const [id,damage] of [['morel',20],['brine',21]]) {
  near(canonical.characters[id].modes.base.secondary_contact_probe.damage_dealt_at_release,damage,`${id}: no-resource fallback remains live`);
}
equal(canonical.characters.pendle.modes.powered.secondary_release_probe.projectiles.length,0,'Powered Pendle secondary is not fan fire');
near(canonical.characters.pendle.modes.powered.secondary_contact_probe.damage_dealt_at_release,22,'Powered Pendle rifle-stock damage');
equal(canonical.characters.pendle.modes.base.secondary_release_probe.projectiles.length,3,'Pendle fans at most three of six rounds');
near(canonical.characters.pendle.modes.base.secondary_release_probe.player_state.ammo,3,'Pendle retains three rounds until reload ends');

let rook=engine.createCombatState('rook',1,'practice');
for(let n=0;n<8;n++)rook=engine.stepCombat(rook,{secondary:n===0,aimX:220,aimY:98},dt);
check(rook.player.vaultRemaining>0,'Rook vault is in flight');
rook=engine.stepCombat(rook,{primary:true,aimX:86,aimY:20},dt);
equal(rook.player.action,'primary','Rook can start firing while vaulting');
check(rook.player.vaultRemaining>0&&rook.player.dirY<0,'Rook can aim separately during vault');
const vaultHp=rook.player.hp;
near(engine.applyCombatDamage(rook,20,rook.player.x+20,rook.player.y,'melee').player.hp,vaultHp,'Airborne vault avoids ground melee');
near(engine.applyCombatDamage(rook,20,rook.player.x+20,rook.player.y,'projectile').player.hp,vaultHp-20,'Airborne vault still takes projectiles');

let nix=engine.createCombatState('nix',1,'practice');
const origin=[nix.player.x,nix.player.y];
for(let n=0;n<8;n++)nix=engine.stepCombat(nix,{secondary:n===0,moveX:1,aimX:220,aimY:98},dt);
const hologram=nix.fields.find((field)=>field.kind==='hologram');
equal([hologram.x,hologram.y],origin,'Nix decoy stays at commitment origin');
check(nix.player.x>origin[0],'Nix moves freely while decoy is placed');

let guard=engine.createCombatState('bramble',1,'practice');
guard=engine.stepCombat(guard,{block:true,aimX:220,aimY:98},dt);
near(engine.applyCombatDamage(guard,20,guard.player.x+30,guard.player.y).player.hp,160,'Frontal guard absorbs damage');
near(engine.applyCombatDamage(guard,20,guard.player.x-30,guard.player.y).player.hp,140,'Guard does not absorb rear damage');

let clack=engine.createCombatState('clack',1,'practice');
clack.player.reload=1;clack.player.ammo=0;
clack=engine.stepCombat(clack,{secondary:true,aimX:220,aimY:98},dt);
equal(clack.player.action,'secondary','Clack vent remains available during rocket reload');

for(const id of ids) {
  let state=engine.createCombatState(id,1,'practice');
  engine.__reference.activateForm(state);
  near(state.player.specialDuration,id==='rook'?10:id==='nix'?7:8,`${id}: finite form duration`);
  if(id==='rook')equal(state.turrets.length,2,'Exactly two Rook turrets');
  state.player.specialRemaining=0.001;
  state=engine.stepCombat(state,{aimX:220,aimY:98},dt);
  near(state.player.specialRemaining,0,`${id}: automatic form expiry`);
  if(id==='rook')equal(state.turrets.length,0,'Turrets removed on form expiry');
  if(id==='ashe')check(state.effects.some((effect)=>effect.kind==='fire-finisher'),'Ashe natural expiry fires finisher');
}
const interruptedAshe=engine.createCombatState('ashe',1,'practice');
engine.__reference.activateForm(interruptedAshe);interruptedAshe.effects=[];
engine.__reference.endForm(interruptedAshe,true);
check(!interruptedAshe.effects.some((effect)=>effect.kind==='fire-finisher'),'Ashe interrupted expiry does not fire finisher');

const corrupt=structuredClone(canonical);
corrupt.characters.nix.modes.base.actions.primary.release_seconds+=0.1;
assert.throws(()=>assert.deepEqual(corrupt,deriveCanonical()),'Stale/modified canonical data must be rejected');checks++;
const badClip=structuredClone(studio.characters.cairn.clips.primary);badClip.durations[0]+=0.01;
assert.throws(()=>assert.ok(Math.abs(badClip.duration-badClip.durations.reduce((a,b)=>a+b,0))<1e-8),'Corrupt frame timing must be rejected');checks++;

console.log(JSON.stringify({result:'PASS',checks,characters:ids.length,studio_clips:clips,timing_mismatches:studio.timing_mismatches.length,coverage:'source extraction and original pure simulation probes; no Godot4.7.2, new pixel art, native device or integration test'},null,2));
