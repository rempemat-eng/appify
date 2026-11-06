// node game/test/combat/build_impact_oracle.mjs /path/to/original-modules.json
// Hash-check original modules, then expose T/B/Y/G without rewriting their bodies.
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
  source=source.slice(0,-end.length)+'_e.oracleImpact=T;_e.oracleDamage=B;_e.oracleField=Y;_e.oracleReact=G;'+end;
 }
 let factory,mid,dependencies;
 vm.runInNewContext(source,{__d:(f,i,d)=>{factory=f;mid=i;dependencies=d;}},{timeout:1000});
 if(mid!==id||JSON.stringify(deps)!==JSON.stringify(dependencies))throw Error('Dependency changed');
 const exports={};factory({},i=>modules.get(i),null,null,{exports},exports,dependencies);modules.set(id,exports);
}
const engine=modules.get(3500),cases=[];
// Colour is a presentation responsibility. All gameplay fields, effect ordering/IDs and events remain.
function clean(s){const c=structuredClone(s);for(const f of [...c.fields,...c.effects])delete f.color;return c;}
function base(id,powered=false){const s=engine.createCombatState(id,1,'encounter');s.time=7.5;s.player.specialRemaining=powered?4:0;s.enemies=s.enemies.map((e,n)=>({...e,x:120+20*n,y:98,hp:100,immortal:false}));return s;}
function add(operation,state,args){const initial=clean(state);if(operation==='impact')engine.oracleImpact(state,args.shot,state.enemies.find(e=>e.id===args.target_id));if(operation==='damage')engine.oracleDamage(state,state.enemies.find(e=>e.id===args.target_id),args.amount,args.knockback);if(operation==='field')engine.oracleField(state,...args);if(operation==='react')engine.oracleReact(state,args.ids,args.chained);cases.push({operation,initial,args,expected:clean(state)});}
const launches=JSON.parse(readFileSync(new URL('./projectile-oracle.json',import.meta.url))).cases;
for(const sample of launches){for(const initial of sample.expected.slice(0,1)){
 const shot={...initial,x:120,y:98,hitIds:[2],blastRadius:initial.blast_radius};
 for(const target of [1,null]){const s=base(sample.id,sample.powered);s.enemies[1].rootRemaining=.8;add('impact',s,{shot,target_id:target});}
}}
for(const id of ['tam','iona','bramble'])for(const powered of [false,true])for(const hp of [5,100])for(const kind of ['grunt','tank','dummy']){
 const s=base(id,powered);s.enemies[0].hp=hp;s.enemies[0].kind=kind;s.enemies[0].frost=2;s.enemies[0].vulnerableRemaining=1;s.player.tetherId=1;add('damage',s,{target_id:1,amount:20,knockback:13});
}
for(const kind of ['reagent','seal','echo','hologram','other'])for(const powered of [false,true])for(const count of [0,1,3,4,5,10]){
 const s=base('mirra',powered);for(let n=0;n<count;n++)engine.oracleField(s,kind,90+n,100,10,5,3);add('field',s,[kind,-90,900,18,5,3]);
}
for(const chained of [false,true])for(const ids of [[4],[4,4,5,999],[999]]){
 const s=base('morel');for(const x of [115,155,195,241.001])engine.oracleField(s,'reagent',x,98,18,5,3);add('react',s,{ids,chained});
}
for(const powered of [false,true]){
 const s=base('morel',powered);for(const x of [115,155,195])engine.oracleField(s,'reagent',x,98,18,5,3);
 add('impact',s,{shot:{kind:'flask',x:120,y:98,damage:17,powered,blastRadius:0,source:'morel',hitIds:[]},target_id:null});
}
// Dead/zero damage, immortal clamp, coincident knockback, event cap, survivor-only statuses.
for(const amount of [0,-2,999])for(const immortal of [false,true]){
 const s=base('bramble');s.enemies[0].immortal=immortal;s.enemies[0].x=s.player.x;s.enemies[0].y=s.player.y;s.events=Array.from({length:80},()=>({time:0,type:'old',text:'old'}));add('damage',s,{target_id:1,amount,knockback:500});
}
for(const kind of ['harpoon','arrow','water','pulse'])for(const hp of [1,100]){
 const s=base(kind==='pulse'?'rook':'bramble');s.enemies[0].hp=hp;s.enemies[1].rootRemaining=.8;
 add('impact',s,{shot:{kind,x:120,y:98,damage:20,powered:true,blastRadius:0,source:kind==='pulse'?'rook':'bramble',hitIds:[2]},target_id:1});
}
// Inherited nested-shatter lethal edge: original B records defeat twice. Preserve, flag to owner.
{const s=base('tam',true);s.enemies[0].hp=35;s.enemies[0].frost=2;s.enemies[0].vulnerableRemaining=1;add('damage',s,{target_id:1,amount:20,knockback:0});}
// Store shared state once; patches replace arrays and recurse only through objects.
const baseline=clean(base('bramble'));
function delta(a,b){const out={};for(const key of Object.keys(b)){
 if(JSON.stringify(a[key])===JSON.stringify(b[key]))continue;
 out[key]=b[key]&&typeof b[key]==='object'&&!Array.isArray(b[key])&&a[key]&&typeof a[key]==='object'&&!Array.isArray(a[key])?delta(a[key],b[key]):b[key];
}return out;}
const compact=cases.map(c=>({...c,initial:delta(baseline,c.initial),expected:delta(c.initial,c.expected)}));
writeFileSync(new URL('./impact-oracle.json',import.meta.url),JSON.stringify({engine_sha256:hash(ref.engine),baseline,cases:compact})+'\n');
console.log(cases.length+' original T/B/Y/G snapshots');
