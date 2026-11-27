// node game/test/combat/build_projectile_phase_oracle.mjs /path/to/original-modules.json
// Hash-check original modules, then expose F without rewriting their bodies.
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
  source=source.slice(0,-end.length)+'_e.oracleFlight=F;'+end;
 }
 let factory,mid,dependencies;
 vm.runInNewContext(source,{__d:(f,i,d)=>{factory=f;mid=i;dependencies=d;}},{timeout:1000});
 if(mid!==id||JSON.stringify(deps)!==JSON.stringify(dependencies))throw Error('Dependency changed');
 const exports={};factory({},i=>modules.get(i),null,null,{exports},exports,dependencies);modules.set(id,exports);
}
const engine=modules.get(3500),cases=[];
function clean(state){const s=structuredClone(state);for(const f of [...s.fields,...s.effects,...s.projectiles,...s.turrets])delete f.color;return s;}
function base(id='bramble',powered=false){const s=engine.createCombatState(id,1,'encounter');s.time=7.5;s.player.specialRemaining=powered?4:0;s.enemies=s.enemies.map((e,n)=>({...e,x:120+20*n,y:98,hp:100,immortal:false}));return s;}
function shot(sample,id=99){const s=structuredClone(sample);s.id=id;s.x=s.position[0];s.y=s.position[1];s.vx=s.velocity[0];s.vy=s.velocity[1];s.hitIds=s.hit_ids;s.blastRadius=s.blast_radius;s.launchHeight=s.launch_height;s.flightDuration=s.flight_duration;for(const k of ['position','velocity','hit_ids','blast_radius','launch_height','flight_duration'])delete s[k];return s;}
function add(state,ticks=1,label='launch'){const initial=clean(state);for(let i=0;i<ticks;i++)engine.oracleFlight(state);cases.push({ticks,label,initial,expected:clean(state)});}
const launches=JSON.parse(readFileSync(new URL('./projectile-oracle.json',import.meta.url))).cases;
for(const sample of launches)for(const ticks of [1,30]){
 const s=base(sample.id,sample.powered);s.projectiles=sample.expected.map((v,n)=>shot(v,100+n));s.serial=110;add(s,ticks);
}
// Whole-phase dependencies: later shots must see earlier kills, root transfers, seals and reactions.
for(const id of ['bramble','morel','mirra','clack','rook','brine','mote'])for(const powered of [false,true])for(const hp of [1,100]){
 const sample=launches.find(c=>c.id===id&&c.powered===powered&&c.action==='primary'&&c.angle===0);
 const s=base(id,powered);s.enemies[0].hp=hp;s.enemies[0].frost=2;
 s.projectiles=[0,1].map(n=>({...shot(sample.expected[0],100+n),vx:6000,vy:0}));s.serial=110;
 s.fields=[{id:80,kind:'seal',x:110,y:98,radius:1,remaining:1,damage:0,tickIn:0.2,source:id},{id:81,kind:'reagent',x:140,y:98,radius:18,remaining:1,damage:3,tickIn:0.2,source:id}];add(s,1,'synchronous');
}
// Existing root transfers and equal-distance contact order. Expiry/outside blasts and no new timer phases.
for(const x of [-1,0,319,320,321])for(const kind of ['flask','boulder','arrow']){
 const sample=launches.find(c=>c.id===(kind==='flask'?'morel':kind==='boulder'?'cairn':'bramble')&&c.action===(kind==='boulder'?'secondary':'primary')&&c.powered);
 const s=base(sample.id,true);s.projectiles=[{...shot(sample.expected[0]),kind,x,y:98,vx:0,vy:0,remaining:0,blastRadius:kind==='boulder'?23:0}];s.serial=100;add(s,1,'expiry');
}
// Sub-texel boundary inputs must preserve discrete collision/bounds outcomes.
for(const x of [-0.000001,0,320,320.000001]){const s=base();s.enemies=[];s.projectiles=[{...shot(launches[0].expected[0]),x,y:98,vx:0,vy:0,remaining:1}];add(s,1,'strict-bounds');}
for(const gap of [9.999999,10,10.000001]){const s=base();s.enemies=s.enemies.slice(0,1);s.projectiles=[{...shot(launches[0].expected[0]),x:120,y:98+gap,vx:0,vy:0,remaining:1}];add(s,1,'strict-contact');}
for(const status of ['playing','victory','defeat']){const s=base();s.status=status;s.projectiles=[shot(launches[0].expected[0])];add(s,1,'status');}
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
writeFileSync(new URL('./projectile-phase-oracle.json',import.meta.url),JSON.stringify(exact({engine_sha256:hash(ref.engine),baseline,cases:compact}))+'\n');
console.log(cases.length+' original full player-projectile phase snapshots');
