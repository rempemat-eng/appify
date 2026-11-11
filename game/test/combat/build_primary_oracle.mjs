// node game/test/combat/build_primary_oracle.mjs /path/to/original-modules.json
// Hash-check original modules; expose E without rewriting their bodies.
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
  source=source.slice(0,-end.length)+'_e.__primary=E;'+end;
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
 const s=base(id,powered);const p=s.player;Object.assign(p,{x:100,y:98,actionDirX:dir[0],actionDirY:dir[1],aimX:220,aimY:145,vaultHeight:17,combo:2});
 s.enemies=s.enemies.map((e,i)=>({...e,x:p.x+dir[0]*(18+i*21),y:p.y+dir[1]*(18+i*21),hp,frost:2}));
 add(s,'primary',['primary'],'all-kits-directions-lethality');
}
for(const powered of [false,true]){
 for(const id of ['brine','pendle','clack'])for(const ammo of [0,1,2,6])for(const reload of [0,0.7]){
  const s=base(id,powered);s.player.ammo=ammo;s.player.reload=reload;s.player.tetherId=s.enemies[0].id;s.player.tetherRemaining=2;
  s.projectiles=[{id:++s.serial,kind:'harpoon'},{id:++s.serial,kind:'bullet'},{id:++s.serial,kind:'harpoon',owner:'enemy'}];
  add(s,'primary',['primary'],'resource-and-single-harpoon-order');
 }
 for(const counter of [0,1e-12,0.1,2])for(const hp of [1,100]){
  const s=base('velvet',powered);s.player.counterRemaining=counter;s.enemies=s.enemies.map((e,i)=>({...e,x:s.player.x+12+i*10,y:s.player.y,hp}));
  add(s,'primary',['primary'],'independent-counter-expiry');
 }
 for(const heat of [0,81,88,92,99,100]){const s=base('nix',powered);s.player.heat=heat;add(s,'primary',['primary'],'heat-mutates-before-beam');}
 for(const distance of [0,9,28,28.000001,134.999999,135,200]){
  const s=base('morel',powered);s.player.aimX=s.player.x+distance;s.player.aimY=s.player.y;add(s,'primary',['primary'],'flask-life-clamp');
 }
 for(const id of ['iona','tam','cairn','ashe','nix'])for(const kind of ['tank','rusher'])for(const immortal of [false,true]){
  const s=base(id,powered);s.enemies=s.enemies.map((e,i)=>({...e,kind,immortal,hp:25,x:s.player.x+15+i*8,y:s.player.y,frost:2}));
  add(s,'primary',['primary'],'passive-and-ordered-followup');
 }
}
for(const id of engine.ROSTER.map(x=>x.id)){
 const s=base(id,true);s.enemies=[];s.extra={untouched:true};s.player.extra={preserved:1};
 s.events=Array.from({length:80},(_,i)=>({time:i,type:'old',text:'old'}));add(s,'primary',['primary'],'empty-capped-events-unknown-fields');
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
writeFileSync(new URL('./primary-oracle.json',import.meta.url),JSON.stringify(exact({engine_sha256:hash(ref.engine),baseline,cases:compact}))+'\n');
console.log(cases.length+' original primary snapshots');
