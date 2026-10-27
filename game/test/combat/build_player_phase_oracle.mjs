// node game/test/combat/build_player_phase_oracle.mjs /path/to/original-modules.json
// Hash-check original modules; wrap the contiguous player timer/guard/commitment prefix of v.
// Only the phase boundary is instrumented; every called original helper is unchanged.
import {readFileSync, writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
const ref=JSON.parse(readFileSync(process.argv[2]));
const hash=s=>createHash('sha256').update(s).digest('hex');
if(hash(ref.engine)!=='21aa782577f3d2fc51389efdd80c4c61a1a7ddd48d128e01eb318daa75d6bc10'||hash(ref.catalogue)!=='8b2dc37132bc29f9e9f184b42abc209933a2ba98f35ef46e9c1061838492ad6f')throw Error('Wrong oracle');
const modules=new Map();
for(const [key,id,deps] of [['catalogue',3501,[]],['engine',3500,[3501]]]){
 let source=ref[key];
 if(key==='engine'){
  const end='},3500,[3501]);';if(!source.endsWith(end))throw Error('Boundary changed');
  const begin=source.indexOf('function v(i,d){')+'function v(i,d){'.length;
  const finish=source.indexOf('const k=o(d.moveX,d.moveY);',begin);
  if(begin<0||finish<0)throw Error('Player-phase boundary changed');
  const prefix=source.slice(begin,finish);
  source=source.slice(0,-end.length)+'_e.__playerphase=function(i,d){'+prefix+'};_e.oracleDuration=R;_e.oracleReleaseTime=D;'+end;
 }
 let factory,mid,dependencies;
 vm.runInNewContext(source,{__d:(f,i,d)=>{factory=f;mid=i;dependencies=d;}},{timeout:1000});
 if(mid!==id||JSON.stringify(deps)!==JSON.stringify(dependencies))throw Error('Dependency changed');
 const exports={};factory({},i=>modules.get(i),null,null,{exports},exports,dependencies);modules.set(id,exports);
}
const engine=modules.get(3500),cases=[];
function clean(state){const s=structuredClone(state);for(const f of [...s.fields,...s.effects,...s.projectiles,...s.turrets])delete f.color;return s;}
function base(id='bramble',powered=false){const s=engine.createCombatState(id,1,'encounter');s.time=7.5;s.player.specialRemaining=powered?4:0;s.enemies=s.enemies.map((e,n)=>({...e,x:120+20*n,y:98,hp:100,immortal:false}));return s;}
function add(state,op,args,label) {const initial=clean(state);engine['__'+op](state,...args);cases.push({op,args,label,initial,expected:clean(state)});}
const idle={moveX:0,moveY:0,aimX:220,aimY:98,primary:false,secondary:false,special:false,block:false};
function tick(s,input={},label='playerphase'){add(s,'playerphase',[{...idle,...input}],label);}
for(const id of engine.ROSTER.map(x=>x.id))for(const powered of [false,true])for(const action of ['idle','walk','primary','secondary','special','hit','block'])for(const elapsed of [0,0.04,0.17,0.27999999,0.49,0.7]){
 const s=base(id,powered);Object.assign(s.player,{action,actionElapsed:elapsed,actionDuration:action==='special'?0.65:0.48,actionReleased:false,actionDirX:0.6,actionDirY:0.8});
 tick(s,{primary:true,secondary:true,special:true,moveX:1,moveY:1},'all-kits-releases-commitment');
}
for(const id of engine.ROSTER.map(x=>x.id))for(const powered of [false,true])for(const action of ['primary','secondary','special'])for(const offset of [-1e-7,0,1e-7]){
 const s=base(id,powered);s.player.action=action;s.player.actionDuration=engine.oracleDuration(s.player,action);s.player.actionElapsed=engine.oracleReleaseTime(s.player)-1/60-1e-8+offset;s.player.actionReleased=false;
 tick(s,{},'exact-release-epsilon');
}
for(const power of [0,1e-12,1e-8,1.0001e-8])for(const id of ['pendle','clack']){
 const s=base(id);s.player.specialRemaining=power;tick(s,{primary:true},'positive-power-duration-versus-epsilon-eligibility');
}
for(const id of ['velvet','rook','ashe','nix'])for(const remaining of [0,1e-12,1e-8,1.0001e-8,1/60,1/60+1e-8,0.1])for(const block of [false,true])for(const guard of [0,0.1,0.100001,100]){
 const s=base(id,true);Object.assign(s.player,{specialRemaining:remaining,guard,action:'primary',actionElapsed:0.45,actionDuration:0.48,actionReleased:false,heat:92,designatedId:s.enemies[0].id});
 s.turrets=[{id:++s.serial,remaining:1}];tick(s,{block,primary:true,aimX:s.player.x,aimY:s.player.y},'expiry-before-guard-before-release');
}
for(const id of ['pendle','brine','clack','nix'])for(const ammo of [0,1,6])for(const reload of [0,1e-12,1/60,1/60+1e-8,0.5])for(const powered of [false,true]){
 const s=base(id,powered);Object.assign(s.player,{ammo,reload,heat:92.1});tick(s,{primary:true},'reload-and-heat-before-eligibility');
}
for(const queuedAction of [null,'primary','secondary','special'])for(const queueRemaining of [0,1/60,1/60+1e-8,0.5])for(const previous of [false,true])for(const block of [false,true]){
 const s=base('rook');s.queuedAction=queuedAction;s.queueRemaining=queueRemaining;s.previous={primary:previous,secondary:previous,special:previous,block:previous};
 Object.assign(s.player,{action:'secondary',actionElapsed:0.1,actionDuration:0.55,actionReleased:true,vaultRemaining:0.4});
 tick(s,{primary:true,secondary:true,special:true,block,moveX:0.1,moveY:0},'queue-rising-priority-rook-vault');
}
for(const id of ['bramble','velvet','nix'])for(const timer of [0,1e-12,1e-8,1/60,1/60+1e-8,0.2])for(const live of [false,true]){
 const s=base(id);Object.assign(s.player,{guardBroken:timer,guardRecovery:timer,guard:99.9,counterRemaining:timer,designationRemaining:timer,designatedId:s.enemies[0].id,tetherRemaining:timer,tetherId:live?s.enemies[0].id:999});
 tick(s,{block:true},'guard-identity-timer-boundaries');
}
for(const id of ['rook','nix','pendle','ashe','velvet']){
 const s=base(id,true);s.extra={preserved:true};s.player.extra={untouched:1};
 for(let n=0;n<90;n++){
  tick(s,{primary:n%7<3,secondary:n%17<2,special:n===30,block:n%19<4,moveX:0.6,moveY:0.8,aimX:n%2?500:-20,aimY:n%3?98:-100},'repeated-player-only-phase');
  // Previous input belongs to the later dispatcher, set explicitly between isolated phases.
  s.previous={primary:n%7<3,secondary:n%17<2,special:n===30,block:n%19<4};
 }
}
const baseline=clean(base());
function delta(a,b){const out={};for(const key of Object.keys(b)){
 if(JSON.stringify(a[key])===JSON.stringify(b[key]))continue;
 out[key]=b[key]&&typeof b[key]==='object'&&!Array.isArray(b[key])&&a[key]&&typeof a[key]==='object'&&!Array.isArray(a[key])?delta(a[key],b[key]):b[key];
}return out;}
const compact=cases.map(c=>({...c,initial:delta(baseline,c.initial),expected:delta(c.initial,c.expected)}));
function exact(value){
 if(typeof value==='number'&&!Number.isInteger(value)){const b=Buffer.alloc(8);b.writeDoubleLE(value);return {__f64le:b.toString('hex')};}
 if(Array.isArray(value))return value.map(exact);
 if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,exact(v)]));
 return value;
}
writeFileSync(new URL('./player-phase-oracle.json',import.meta.url),JSON.stringify(exact({engine_sha256:hash(ref.engine),baseline,cases:compact}))+'\n');
console.log(cases.length+' original player-phase snapshots');
