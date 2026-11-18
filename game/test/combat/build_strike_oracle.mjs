// node game/test/combat/build_strike_oracle.mjs /path/to/original-modules.json
// Hash-check original modules; expose O/S/C without rewriting their bodies.
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
  source=source.slice(0,-end.length)+'_e.__arc=O;_e.__beam=S;_e.__dash=C;'+end;
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
for(const id of engine.ROSTER.map(x=>x.id))for(const powered of [false,true])for(const op of ['arc','beam','dash']){
 const s=base(id,powered);s.player.x=100;s.player.y=98;s.player.actionDirX=1;s.player.actionDirY=0;
 s.enemies=s.enemies.map((e,i)=>({...e,x:120+12*i,y:98,hp:20,frost:2}));
 add(s,op,op==='arc'?[60,0.5,19,9]:op==='beam'?[98,13,34,true,'lunge']:[80],'all-kits');
}
for(const offset of [20.999999,21,21.000001])for(const along of [-8.000001,-8,0,106,106.000001])for(const pierce of [false,true]){
 const s=base();s.enemies=[{...s.enemies[0],x:s.player.x+along,y:s.player.y+offset}];add(s,'beam',[98,13,34,pierce,'beam'],'beam-boundary');
}
for(const angle of [0.499999999,0.5,0.500000001])for(const distance of [67.999999,68,68.000001]){
 const s=base();s.enemies=[{...s.enemies[0],x:s.player.x+distance*angle,y:s.player.y+distance*Math.sqrt(1-angle*angle)}];add(s,'arc',[60,0.5,11,0],'arc-boundary');
}
for(const side of [14.999999,15,15.000001])for(const along of [-1,0,0.000001,16,40,110]){
 const s=base();s.player.radius=7;s.enemies=[{...s.enemies[0],radius:8,x:s.player.x+along,y:s.player.y+side}];add(s,'dash',[80],'dash-clearance');
}
for(const op of ['arc','beam','dash'])for(const dir of [[0,1],[-1,0],[0,-1],[Math.SQRT1_2,Math.SQRT1_2],[0,0]]){
 const s=base('iona',true);s.player.actionDirX=dir[0];s.player.actionDirY=dir[1];s.enemies=s.enemies.map((e,i)=>({...e,x:s.player.x+dir[0]*(20+i*10),y:s.player.y+dir[1]*(20+i*10)}));
 add(s,op,op==='arc'?[60,-0.5,19,9]:op==='beam'?[98,13,34,false,'lunge']:[800],'direction-and-arena');
}
for(const pierce of [false,true]){const s=base('rook');s.enemies=[...s.enemies.slice(0,1),...s.enemies.slice(0,1)].map((e,i)=>({...e,id:10+i,x:s.player.x+20,y:s.player.y+(i===0?4:-4)}));add(s,'beam',[80,8,40,pierce,'beam'],'stable-equal-distance');}
for(const op of ['arc','beam','dash']){
 const s=base();s.enemies=[];s.events=Array.from({length:80},(_,i)=>({time:i,type:'old',text:'old'}));add(s,op,op==='arc'?[60,0.5,19,9]:op==='beam'?[98,13,34,false,'lunge']:[800],'miss-cap-and-empty');
 const d=base();d.enemies=d.enemies.map(e=>({...e,hp:0}));add(d,op,op==='arc'?[60,0.5,19,9]:op==='beam'?[98,13,34,false,'lunge']:[800],'dead-excluded');
}
for(const op of ['arc','beam']){const s=base('tam',true);s.enemies=s.enemies.map(e=>({...e,x:s.player.x+20,y:s.player.y,hp:1,immortal:true,frost:2}));add(s,op,op==='arc'?[60,0.5,19,9]:[98,13,34,true,'beam'],'immortal-passives');}
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
writeFileSync(new URL('./strike-oracle.json',import.meta.url),JSON.stringify(exact({engine_sha256:hash(ref.engine),baseline,cases:compact}))+'\n');
console.log(cases.length+' original arc/beam/dash snapshots');
