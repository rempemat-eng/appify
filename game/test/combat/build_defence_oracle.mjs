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
  source=source.slice(0,-end.length)+'_e.__flight=F;_e.__damage=P;'+end;
 }
 let factory,mid,dependencies;
 vm.runInNewContext(source,{__d:(f,i,d)=>{factory=f;mid=i;dependencies=d;}},{timeout:1000});
 if(mid!==id||JSON.stringify(deps)!==JSON.stringify(dependencies))throw Error('Dependency changed');
 const exports={};factory({},i=>modules.get(i),null,null,{exports},exports,dependencies);modules.set(id,exports);
}
const engine=modules.get(3500),cases=[];
function clean(state){const s=structuredClone(state);for(const f of [...s.fields,...s.effects,...s.projectiles,...s.turrets])delete f.color;return s;}
function base(id='bramble',powered=false){const s=engine.createCombatState(id,1,'encounter');s.time=7.5;s.player.specialRemaining=powered?4:0;s.enemies=s.enemies.map((e,n)=>({...e,x:120+20*n,y:98,hp:100,immortal:false}));return s;}
function add(state,op,args=[],ticks=1,label='damage') {const initial=clean(state);for(let i=0;i<ticks;i++)op==='damage'?engine.__damage(state,...args):engine.__flight(state);cases.push({op,args,ticks,label,initial,expected:clean(state)});}
for(const id of engine.ROSTER.map(x=>x.id))for(const powered of [false,true])for(const guard of [0,15,30,100])for(const amount of [10,20,200]){
 const s=base(id,powered);s.player.blocking=true;s.player.guard=guard;s.queuedAction='special';s.queueRemaining=0.5;add(s,'damage',[amount,130,98]);
}
for(const kind of ['projectile','melee','field'])for(const airborne of [false,true])for(const from of [[130,98],[40,98],[86,98],[86,130],[86+0.25,98+Math.sqrt(1-0.25**2)],[86+0.249999,98+Math.sqrt(1-0.249999**2)]]){
 const s=base('velvet',true);s.player.blocking=true;s.player.airborne=airborne;add(s,'damage',[20,...from,kind]);
}
for(const guardBroken of [0,1e-8,1.000001e-8])for(const hp of [0,1,160]){const s=base('rook',true);s.player.guardBroken=guardBroken;s.player.blocking=true;s.player.hp=hp;s.player.guard=0;s.player.vaultRemaining=0.2;s.player.airborne=true;s.player.designatedId=2;s.turrets=[{id:70}];s.fields=[{id:80,kind:'echo'}];s.projectiles=[{id:90}];add(s,'damage',[200,130,98]);}
// Defeat interruption must never emit Ashe's normal-expiry finisher.
{const s=base('ashe',true);s.player.hp=1;add(s,'damage',[200,130,98]);}
// Each generated shot has canonical full metadata, plus future unknown fields.
function bolt(overrides={}){return {id:90,kind:'enemy-bolt',owner:'enemy',source:'enemy',x:120,y:98,vx:-3000,vy:0,radius:3,remaining:1,damage:12,pierce:0,hitIds:[],blastRadius:0,powered:false,launchHeight:0,age:0,flightDuration:1,future:{flag:1},...overrides};}
for(const id of ['velvet','rook','ashe','bramble'])for(const hp of [1,160])for(const blocking of [false,true])for(const decoys of [0,1,2]){
 const s=base(id,true);s.player.hp=hp;s.player.blocking=blocking;s.player.guard=15;s.projectiles=[bolt(),bolt({id:91}),bolt({id:92,owner:'player',kind:'arrow',source:'bramble',vx:6000,x:90,damage:22})];
 s.fields=Array.from({length:decoys},(_,i)=>({id:70+i,kind:i?'hologram':'echo',x:100,y:98,radius:8,remaining:1,damage:0,tickIn:0.2,source:id}));add(s,'flight',[],1,'mixed-decoy');
}
for(const remaining of [0,1e-8,1/60,0.02])for(const y of [107.999999,108,108.000001,15.999999,16,180,180.000001]){
 const s=base();s.projectiles=[bolt({x:86,y,vx:0,remaining})];add(s,'flight',[],2,'expiry-contact');
}
// Death must clear a previously retained projectile as well as all later shots.
{const s=base('rook',true);s.player.hp=1;s.projectiles=[bolt({x:250,y:150,vx:0}),bolt(),bolt({id:92})];add(s,'flight',[],1,'defeat-clears-survivors');}
// Event history cap is applied for each event, not at end of phase.
{const s=base();s.events=Array.from({length:80},(_,i)=>({time:i,type:'old',text:'old'}));s.player.blocking=true;s.player.guard=15;add(s,'damage',[200,130,98]);}
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
writeFileSync(new URL('./defence-oracle.json',import.meta.url),JSON.stringify(exact({engine_sha256:hash(ref.engine),baseline,cases:compact}))+'\n');
console.log(cases.length+' original defence/enemy-projectile snapshots');
