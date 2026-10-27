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
  source=source.slice(0,-end.length)+'_e.oracleExit=X;'+end;
 }
 let factory,mid,dependencies;
 vm.runInNewContext(source,{__d:(f,i,d)=>{factory=f;mid=i;dependencies=d;}},{timeout:1000});
 if(mid!==id||JSON.stringify(deps)!==JSON.stringify(dependencies))throw Error('Dependency changed');
 const exports={};factory({},i=>modules.get(i),null,null,{exports},exports,dependencies);modules.set(id,exports);
}
const engine=modules.get(3500),cases=[];
function clean(state){const s=structuredClone(state);for(const f of [...s.fields,...s.effects,...s.projectiles,...s.turrets])delete f.color;return s;}
function base(id='bramble',powered=false){const s=engine.createCombatState(id,1,'encounter');s.time=7.5;s.player.specialRemaining=powered?4:0;s.enemies=s.enemies.map((e,n)=>({...e,x:120+20*n,y:98,hp:100,immortal:false}));return s;}
function add(state, interrupted, label) {const initial=clean(state);engine.oracleExit(state,interrupted);cases.push({interrupted,label,initial,expected:clean(state)});}
for(const id of engine.ROSTER.map(x=>x.id))for(const interrupted of [false,true])for(const hp of [0,1,160]){
 const s=base(id,true);s.player.hp=hp;s.player.designatedId=2;s.turrets=[{id:70}];add(s,interrupted,'all-kit-exit');
}
for(const dir of [[1,0],[0,1],[-1,0],[0,-1],[Math.SQRT1_2,Math.SQRT1_2]])for(const hp of [1,34,100])for(const immortal of [false,true]){
 const s=base('ashe',true);s.player.dirX=dir[0];s.player.dirY=dir[1];s.player.actionDirX=-dir[1];s.player.actionDirY=dir[0];
 s.enemies=s.enemies.map((e,i)=>({...e,x:s.player.x+dir[0]*(20+30*i),y:s.player.y+dir[1]*(20+30*i),hp,immortal}));add(s,false,'finisher-hit-order');
}
for(const offset of [20.999999,21,21.000001])for(const along of [-8.000001,-8,0,106,106.000001]){
 const s=base('ashe',true);s.enemies=[{...s.enemies[0],x:s.player.x+along,y:s.player.y+offset}];add(s,false,'beam-boundary');
}
{const s=base('ashe',true);s.enemies=[];s.events=Array.from({length:80},(_,i)=>({time:i,type:'old',text:'old'}));s.fields=Array.from({length:10},(_,i)=>({id:40+i,kind:'flame',x:100,y:100}));add(s,false,'cap-and-miss');}
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
writeFileSync(new URL('./form-exit-oracle.json',import.meta.url),JSON.stringify(exact({engine_sha256:hash(ref.engine),baseline,cases:compact}))+'\n');
console.log(cases.length+' original powered-form exit snapshots');
