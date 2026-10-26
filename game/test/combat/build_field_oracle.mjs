// node game/test/combat/build_impact_oracle.mjs /path/to/original-modules.json
// Hash-check original modules, then expose _/L/Y without rewriting their bodies.
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
  source=source.slice(0,-end.length)+'_e.__fields=_;_e.__statuses=L;_e.__field=Y;'+end;
 }
 let factory,mid,dependencies;
 vm.runInNewContext(source,{__d:(f,i,d)=>{factory=f;mid=i;dependencies=d;}},{timeout:1000});
 if(mid!==id||JSON.stringify(deps)!==JSON.stringify(dependencies))throw Error('Dependency changed');
 const exports={};factory({},i=>modules.get(i),null,null,{exports},exports,dependencies);modules.set(id,exports);
}
const engine=modules.get(3500),cases=[];
function clean(state){const s=structuredClone(state);for(const f of [...s.fields,...s.effects])delete f.color;return s;}
function base(id='bramble',powered=false){const s=engine.createCombatState(id,1,'encounter');s.time=7.5;s.player.specialRemaining=powered?4:0;s.enemies=s.enemies.map((e,n)=>({...e,x:120+20*n,y:98,hp:100,immortal:false}));return s;}
function add(operation,state,ticks=1){const initial=clean(state);for(let i=0;i<ticks;i++){
 if(operation==='fields')engine.__fields(state);
 else if(operation==='statuses')engine.__statuses(state);
 else {state.time+=1/60;state.tick++;engine.__statuses(state);engine.__fields(state);}
}cases.push({operation,ticks,initial,expected:clean(state)});}
for(const id of ['bramble','tam','iona','mirra'])for(const powered of [false,true])for(const kind of ['gravity','ice','flame','gust','reagent','seal','echo','hologram'])for(const tickIn of [0,.2]){
 const s=base(id,powered);engine.__field(s,kind,120,98,18,.01,kind==='ice'?0:4);s.fields[0].tickIn=tickIn;s.enemies[0].frost=2;s.enemies[1].kind='tank';s.enemies[1].vulnerableRemaining=.5;s.enemies[2].hp=0;add('fields',s);
}
for(const id of ['mote','tam','mirra'])for(const powered of [false,true])for(const ticks of [1,13,61,190]){
 const s=base(id,powered);for(const [kind,x,y,radius,damage] of [['gravity',120,98,32,4],['ice',145,98,19,0],['seal',145,98,18,0],['seal',120,125,18,0],['flame',140,100,15,8]])engine.__field(s,kind,x,y,radius,2,damage);add('phases',s,ticks);
}
// Currents follow seal insertion order, damage once per target across shared segments,
// ignore expired seals, and use exact segment thresholds including degenerate segments.
for(const points of [[],[[86,98]],[[145,98],[86,98]],[[110,98],[150,98],[110,98]],[[140,140],[140,60]]])for(const powered of [false,true])for(const timer of [0,.5]){
 const s=base('mirra',powered);s.currentIn=timer;for(const [x,y] of points)engine.__field(s,'seal',x,y,18,3,0);s.enemies[0].y=112;s.enemies[1].y=112.00001;add('fields',s);
}
for(const remaining of [0,1e-8,.01,1/60,1/60+1e-8,.2])for(const age of [3,3.000001])for(const hp of [0,1]){
 const s=base('tam');for(const e of s.enemies){Object.assign(e,{rootRemaining:remaining,slowRemaining:remaining,stunRemaining:remaining,vulnerableRemaining:remaining,phaseRemaining:remaining,frost:2,lastHitAt:s.time-age,hp});}add('statuses',s);
}
// Serial damage/reaction and current de-duplication under lethal and immortal targets.
for(const id of ['tam','iona','mirra'])for(const hp of [1,35])for(const immortal of [false,true]){
 const s=base(id,true);for(const e of s.enemies){e.hp=hp;e.immortal=immortal;e.frost=2;e.vulnerableRemaining=.5;}for(const kind of ['flame','reagent','seal','seal'])engine.__field(s,kind,120,98,60,1,kind==='seal'?0:20);add('fields',s);
}
const baseline=clean(base());
function delta(a,b){const out={};for(const key of Object.keys(b)){
 if(JSON.stringify(a[key])===JSON.stringify(b[key]))continue;
 out[key]=b[key]&&typeof b[key]==='object'&&!Array.isArray(b[key])&&a[key]&&typeof a[key]==='object'&&!Array.isArray(a[key])?delta(a[key],b[key]):b[key];
}return out;}
const compact=cases.map(c=>({...c,initial:delta(baseline,c.initial),expected:delta(c.initial,c.expected)}));
writeFileSync(new URL('./field-oracle.json',import.meta.url),JSON.stringify({engine_sha256:hash(ref.engine),baseline,cases:compact})+'\n');
console.log(cases.length+' original field/status phase snapshots');
