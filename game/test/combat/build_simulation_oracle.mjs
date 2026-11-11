// Hash-verified, unmodified original stepCombat. No phase-boundary instrumentation.
// Live legacy AI is outside this port; cases use original encounter/practice modes.
import {readFileSync, writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
import {gzipSync} from 'node:zlib';
const ref=JSON.parse(readFileSync(process.argv[2]));
const hash=s=>createHash('sha256').update(s).digest('hex');
if(hash(ref.engine)!=='21aa782577f3d2fc51389efdd80c4c61a1a7ddd48d128e01eb318daa75d6bc10'||hash(ref.catalogue)!=='8b2dc37132bc29f9e9f184b42abc209933a2ba98f35ef46e9c1061838492ad6f')throw Error('Wrong oracle');
const modules=new Map();
for(const [key,id,deps] of [['catalogue',3501,[]],['engine',3500,[3501]]]){
 let source=ref[key];
 let factory,mid,dependencies;
 vm.runInNewContext(source,{__d:(f,i,d)=>{factory=f;mid=i;dependencies=d;}},{timeout:1000});
 if(mid!==id||JSON.stringify(deps)!==JSON.stringify(dependencies))throw Error('Dependency changed');
 const exports={};factory({},i=>modules.get(i),null,null,{exports},exports,dependencies);modules.set(id,exports);
}
const engine=modules.get(3500),cases=[];
function clean(state){const s=structuredClone(state);for(const f of [...s.fields,...s.effects,...s.projectiles,...s.turrets])delete f.color;return s;}
function base(id='bramble',powered=false,mode='encounter'){
 const s=engine.createCombatState(id,1,mode);s.time=7.5;s.player.specialRemaining=powered?4:0;
 s.enemies=s.enemies.map((e,n)=>({...e,x:120+20*n,y:98,hp:100,immortal:false}));return s;
}
function add(state,input,dt,label){const initial=clean(state);const next=engine.stepCombat(state,input,dt);cases.push({input,dt,label,initial,expected:clean(next)});return next;}
const idle={moveX:0,moveY:0,aimX:220,aimY:98,primary:false,secondary:false,special:false,block:false};
for(const id of engine.ROSTER.map(x=>x.id))for(const powered of [false,true]){
 let s=base(id,powered);s.extra={preserved:true};s.player.extra={untouched:1};
 for(let n=0;n<180;n++)s=add(s,{...idle,primary:n%23<18,secondary:n%47<2,special:n===90,block:n%59>51,moveX:n%2?.6:-.3,moveY:.8},n%3===0?.1:1/60,'all-kits-sequence');
}
for(const status of ['playing','victory','defeat'])for(const accumulator of [0,1e-12,1/60-2e-8,1/60-1e-8,1/60])for(const dt of [-1,0,1e-12,.008,.016666666666666666,.1,.5]){
 const s=base('rook',true);s.status=status;s.accumulator=accumulator;s.effects=[{id:++s.serial,kind:'test',remaining:1/60+1e-8,duration:1}];
 add(s,idle,dt,'accumulator-terminal-and-clamp');
}
for(const input of [{},{active:false},{active:0},{moveX:3,moveY:-5,aimX:'bad',aimY:null,primary:[],special:{}},{primary:'',secondary:1,block:'yes'},{moveX:true,moveY:'2',aimX:999,aimY:-22}])add(base(),input,.1,'input-coercion');
for(const id of engine.ROSTER.map(x=>x.id))for(const mode of ['practice','encounter'])for(const hp of [0,1e-9,1e-8,1e-7]){
 const s=base(id,true,mode);s.enemies.forEach(e=>e.hp=hp);Object.assign(s.player,{blocking:true,action:'block',vaultRemaining:.4,vaultHeight:8,airborne:true});
 s.fields=[{id:++s.serial,kind:'ice',source:'tam',x:300,y:180,radius:10,remaining:2,duration:2,tickIn:.5,damage:0}];
 s.projectiles=[{id:++s.serial,kind:'enemy-bolt',owner:'enemy',x:300,y:100,vx:1,vy:0,radius:3,remaining:2,damage:12,pierce:0,hitIds:[],blastRadius:0,source:'enemy',powered:false,launchHeight:0,age:0,flightDuration:1}];
 add(s,idle,1/60,'wave-settlement-epsilon-practice');
}
for(const id of ['rook','ashe','mirra','morel','tam','nix'])for(const hp of [0,1,100])for(const power of [1/60,1/60+1e-8,1]){
 const s=base(id,true);s.player.hp=hp;s.player.specialRemaining=power;s.player.action='primary';s.player.actionDuration=.48;s.player.actionElapsed=.45;s.player.actionReleased=false;
 s.projectiles=[{id:++s.serial,kind:'enemy-bolt',owner:'enemy',x:s.player.x-1,y:s.player.y,vx:60,vy:0,radius:3,remaining:1,damage:200,pierce:0,hitIds:[],blastRadius:0,source:'enemy',powered:false,launchHeight:0,age:0,flightDuration:1}];
 add(s,{...idle,primary:true},.1,'death-and-expiry-order');
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
writeFileSync(new URL('./simulation-oracle.json.gz',import.meta.url),gzipSync(JSON.stringify(exact({engine_sha256:hash(ref.engine),baseline,cases:compact}))+'\n',{level:9}));
console.log(cases.length+' original full stepCombat snapshots; original modules unmodified');
