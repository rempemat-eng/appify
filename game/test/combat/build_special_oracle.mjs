// node game/test/combat/build_special_oracle.mjs /path/to/original-modules.json
// Hash-check original modules; expose M without rewriting their bodies.
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
  source=source.slice(0,-end.length)+'_e.__special=M;'+end;
 }
 let factory,mid,dependencies;
 vm.runInNewContext(source,{__d:(f,i,d)=>{factory=f;mid=i;dependencies=d;}},{timeout:1000});
 if(mid!==id||JSON.stringify(deps)!==JSON.stringify(dependencies))throw Error('Dependency changed');
 const exports={};factory({},i=>modules.get(i),null,null,{exports},exports,dependencies);modules.set(id,exports);
}
const engine=modules.get(3500),cases=[];
function field(s,kind,x,y){s.fields.push({id:++s.serial,kind,x,y,radius:18,remaining:3,damage:5,tickIn:0.2,source:s.player.id});}
function clean(state){const s=structuredClone(state);for(const f of [...s.fields,...s.effects,...s.projectiles,...s.turrets])delete f.color;return s;}
function base(id='bramble',powered=false){const s=engine.createCombatState(id,1,'encounter');s.time=7.5;s.player.specialRemaining=powered?4:0;s.enemies=s.enemies.map((e,n)=>({...e,x:120+20*n,y:98,hp:100,immortal:false}));return s;}
function add(state,op,args,label) {const initial=clean(state);engine['__'+op](state,...args);cases.push({op,args,label,initial,expected:clean(state)});}
for(const id of engine.ROSTER.map(x=>x.id))for(const powered of [false,true])for(const dir of [[1,0],[0,-1],[Math.SQRT1_2,Math.SQRT1_2]]) {
 const s=base(id,powered);Object.assign(s.player,{actionDirX:dir[0],actionDirY:dir[1],ammo:0,reload:0.6,heat:83,aimX:190,aimY:43});
 s.player.extra={preserved:true};s.extra={untouched:1};
 add(s,'special',[],'all-kits-current-form-and-direction');
}
for(const heat of [0,44.999999,45,45.000001,92,100])for(const powered of [false,true]){
 const s=base('nix',powered);s.player.heat=heat;add(s,'special',[],'nix-cap-not-reset');
}
for(const id of ['brine','clack','pendle'])for(const ammo of [0,1,6])for(const reload of [0,0.000001,1.4]){
 const s=base(id);s.player.ammo=ammo;s.player.reload=reload;add(s,'special',[],'ammo-refill-only-diver-and-launcher');
}
for(const count of [0,2,3,4,5,7])for(const dir of [[-1,0],[0,-1],[1,0]]){
 const s=base('mirra');s.player.x=13;s.player.y=24;s.player.actionDirX=dir[0];s.player.actionDirY=dir[1];
 for(let i=0;i<count;i++)field(s,'seal',100+i,98);field(s,'reagent',120,100);
 add(s,'special',[],'mirra-live-power-seal-cap-clamp');
}
for(const count of [0,1,2,4])for(const x of [12,310]){
 const s=base('rook',true);s.player.x=x;s.player.designatedId=s.enemies[0].id;s.player.designationRemaining=0.8;
 s.turrets=Array.from({length:count},(_,i)=>({id:++s.serial,x:100+i,y:80,radius:5,remaining:2,cooldown:0.3,aimX:1,aimY:2,targetId:3}));
 add(s,'special',[],'rook-replace-pair-retain-designation');
}
for(const id of engine.ROSTER.map(x=>x.id)){
 const s=base(id);s.events=Array.from({length:80},(_,i)=>({time:i,type:'old',text:'old'}));
 add(s,'special',[],'capped-event-order');
 const again=structuredClone(s);add(again,'special',[],'caller-must-dispatch-once');
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
writeFileSync(new URL('./special-oracle.json',import.meta.url),JSON.stringify(exact({engine_sha256:hash(ref.engine),baseline,cases:compact}))+'\n');
console.log(cases.length+' original special snapshots');
