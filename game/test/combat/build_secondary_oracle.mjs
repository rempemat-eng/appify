// node game/test/combat/build_strike_oracle.mjs /path/to/original-modules.json
// Hash-check original modules; expose q without rewriting their bodies.
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
  source=source.slice(0,-end.length)+'_e.__secondary=q;'+end;
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
for(const id of engine.ROSTER.map(x=>x.id))for(const powered of [false,true])for(const dir of [[1,0],[0,-1],[Math.SQRT1_2,Math.SQRT1_2]])for(const hp of [100,1]){
 const s=base(id,powered);const p=s.player;p.x=100;p.y=98;p.actionDirX=dir[0];p.actionDirY=dir[1];p.aimX=220;p.aimY=145;p.actionOriginX=80;p.actionOriginY=76;p.vaultHeight=17;
 s.enemies=s.enemies.map((e,i)=>({...e,x:p.x+dir[0]*(18+i*21),y:p.y+dir[1]*(18+i*21),hp,frost:2}));
 add(s,'secondary',[],'all-kits-directions-lethality');
}
function field(s,kind,x,y){s.fields.push({id:++s.serial,kind,x,y,radius:18,remaining:3,damage:5,tickIn:0.2,source:s.player.id});}
for(const powered of [false,true]){
 for(const distance of [0,25,155,155.000001,180])for(const kind of ['reagent','seal']){
  const s=base('morel',powered);field(s,kind,s.player.x+distance,s.player.y);field(s,'reagent',s.player.x+200,s.player.y);add(s,'secondary',[],'morel-patches');
 }
 for(const kind of ['tank','dummy','rusher'])for(const distance of [0,20,120,185,185.000001])for(const hp of [100,1]){
  const s=base('brine',powered);s.enemies=[{...s.enemies[0],kind,hp,x:s.player.x+distance,y:s.player.y}];s.player.tetherId=s.enemies[0].id;add(s,'secondary',[],'brine-reel');
 }
 for(const ammo of [0,1,2,3,6]){
  const s=base('pendle',powered);s.player.ammo=ammo;s.player.reload=0.7;add(s,'secondary',[],'pendle-partial-fan');
 }
 for(const id of ['mirra','nix','mote'])for(const aim of [[-1000,-1000],[1000,1000],[90,90]]){
  const s=base(id,powered);s.player.aimX=aim[0];s.player.aimY=aim[1];
  for(let i=0;i<12;i++)field(s,id==='mirra'?'seal':id==='nix'?'hologram':'gravity',100+i,98);
  add(s,'secondary',[],'field-caps-and-clamps');
 }
 for(const id of ['iona','tam','velvet','clack']){
  const s=base(id,powered);s.enemies=s.enemies.map((e,i)=>({...e,x:s.player.x+15+i*2,y:s.player.y,hp:20,immortal:true,kind:i?'rusher':'tank',frost:2}));add(s,'secondary',[],'passive-and-heavy');
 }
}
for(const id of engine.ROSTER.map(x=>x.id)){
 const s=base(id,true);s.enemies=[];s.events=Array.from({length:80},(_,i)=>({time:i,type:'old',text:'old'}));add(s,'secondary',[],'empty-capped-events');
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
writeFileSync(new URL('./secondary-oracle.json',import.meta.url),JSON.stringify(exact({engine_sha256:hash(ref.engine),baseline,cases:compact}))+'\n');
console.log(cases.length+' original secondary snapshots');
