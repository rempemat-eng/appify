// node game/test/combat/build_movement_oracle.mjs /path/to/original-modules.json
// Hash-check original modules; wrap the contiguous movement slice of v before L.
// The trailing if condition is closed with an empty body at this test-only phase boundary.
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
  const begin=source.indexOf("const k=o(d.moveX,d.moveY);",source.indexOf('function v('));
  const finish=source.indexOf(',L(i),',begin);
  if(begin<0||finish<0)throw Error('Movement boundary changed');
  // Exact contiguous original movement subphase, before enemy/status/projectile phases.
  const movement=source.slice(begin,finish)+'){}';
  source=source.slice(0,-end.length)+'_e.__movement=function(i,d){const f=i.player;'+movement+'};'+end;
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
for(const id of engine.ROSTER.map(x=>x.id))for(const powered of [false,true])for(const action of ['idle','walk','hit','special','primary','secondary'])for(const move of [[0,0],[0.08,0],[0.0800001,0],[0.6,0.8],[1,1],[-1,-1]]){
 const s=base(id,powered);Object.assign(s.player,{action,x:100,y:98,dirX:0.6,dirY:0.8});
 add(s,'movement',[{moveX:move[0],moveY:move[1]}],'all-kits-action-speeds');
}
for(const remaining of [0,1e-10,1e-8,1.0001e-8,0.001,1/60,1/60+1e-9,0.27,0.55])for(const pos of [[86,98],[12,23],[308,168],[218,65]])for(const airborne of [false,true]){
 const s=base('rook');Object.assign(s.player,{x:pos[0],y:pos[1],vaultRemaining:remaining,vaultDirX:0.6,vaultDirY:0.8,airborne,vaultHeight:11});
 add(s,'movement',[{moveX:1,moveY:-1}],'vault-landing-edges-overlap');
}
for(const powered of [false,true])for(const blocking of [false,true])for(const pos of [[0,0],[320,180],[100,98]]){
 const s=base('velvet',powered);Object.assign(s.player,{x:pos[0],y:pos[1],blocking});
 s.enemies=s.enemies.map((e,i)=>({...e,x:s.player.x+(i===0?0:4),y:s.player.y,hp:i===2?0:100}));
 s.echoIn=1/60;s.fields=Array.from({length:4},()=>({id:++s.serial,kind:'echo',remaining:1}));
 add(s,'movement',[{moveX:1,moveY:1}],'ordered-separation-echo-cap');
}
for(const mx of [0,1]){
 const s=base('velvet',true);s.enemies=[];s.extra={untouched:true};s.player.extra={preserved:1};
 for(let n=0;n<90;n++)add(s,'movement',[{moveX:mx,moveY:0}],'repeated-echo-clock');
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
writeFileSync(new URL('./movement-oracle.json',import.meta.url),JSON.stringify(exact({engine_sha256:hash(ref.engine),baseline,cases:compact}))+'\n');
console.log(cases.length+' original movement snapshots');
