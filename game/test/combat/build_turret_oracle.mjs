// node game/test/combat/build_turret_oracle.mjs /path/to/original-modules.json
// Hash-check original modules, then expose N without rewriting their bodies.
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
  source=source.slice(0,-end.length)+'_e.__turrets=N;'+end;
 }
 let factory,mid,dependencies;
 vm.runInNewContext(source,{__d:(f,i,d)=>{factory=f;mid=i;dependencies=d;}},{timeout:1000});
 if(mid!==id||JSON.stringify(deps)!==JSON.stringify(dependencies))throw Error('Dependency changed');
 const exports={};factory({},i=>modules.get(i),null,null,{exports},exports,dependencies);modules.set(id,exports);
}
const engine=modules.get(3500),cases=[];
function clean(state){const s=structuredClone(state);for(const f of [...s.fields,...s.effects,...s.projectiles,...s.turrets])delete f.color;return s;}
function base(){const s=engine.createCombatState('rook',1,'encounter');s.time=7.5;s.player.specialRemaining=4;s.player.designatedId=1;s.enemies=s.enemies.map((e,n)=>({...e,x:120+20*n,y:98,hp:100,immortal:false}));s.turrets=[-1,1].map(sign=>({id:++s.serial,x:s.player.x+15*sign,y:s.player.y-14,radius:5,remaining:4,cooldown:.18,aimX:s.player.aimX,aimY:s.player.aimY,targetId:null}));return s;}
function add(state,ticks=1){const initial=clean(state);for(let i=0;i<ticks;i++)engine.__turrets(state);cases.push({ticks,initial,expected:clean(state)});}
for(const target of [null,1,999])for(const hp of [0,100])for(const cooldown of [0,.18,.44])for(const ticks of [1,12,28,150]){
 const s=base();s.player.designatedId=target;s.enemies[0].hp=hp;for(const turret of s.turrets)turret.cooldown=cooldown;add(s,ticks);
}
// Strict designated-target range measured from player, not turret. Just inside/outside.
for(const distance of [189.999999,190,190.000001])for(const dy of [0,30]){
 const s=base();s.enemies[0].x=s.player.x+Math.sqrt(distance*distance-dy*dy);s.enemies[0].y=s.player.y+dy;for(const t of s.turrets)t.cooldown=0;add(s);
}
// Leash checked AFTER formation interpolation; final-expiring turrets act once before removal.
for(const distance of [54.99999,55,55.00001,200])for(const remaining of [0,.001,1/60,1/60+1e-8,2]){
 const s=base();for(const [i,t] of s.turrets.entries()){const goal=s.player.x+(i===0?-16:16);const after=s.player.x+distance;t.x=(after-goal*(7/60))/(53/60);t.y=s.player.y+14*(7/60)/(53/60);t.cooldown=1/60;t.remaining=remaining;}add(s);
}
for(const id of ['rook','nix'])for(const power of [0,1e-8,1e-8+1e-12,4])for(const hp of [0,100]){const s=base();Object.assign(s.player,{id,specialRemaining:power,hp});add(s);}
// Coincident aim fallback, reordered survivors, negative cooldown, designation timer not owned here.
for(const count of [0,1,2,3])for(const ticks of [1,2,40]){
 const s=base();s.turrets=s.turrets.slice(0,count);if(count===3)s.turrets.push({...s.turrets[0],id:++s.serial});s.player.designationRemaining=0;
 for(const [index,t] of s.turrets.entries()){t.cooldown=-.2;t.x=s.player.x+(index===0?-16:16);t.y=s.player.y-14;}s.enemies[0].x=s.player.x-16;s.enemies[0].y=s.player.y-14;add(s,ticks);
}
const baseline=clean(base());
function delta(a,b){const out={};for(const key of Object.keys(b)){
 if(JSON.stringify(a[key])===JSON.stringify(b[key]))continue;
 out[key]=b[key]&&typeof b[key]==='object'&&!Array.isArray(b[key])&&a[key]&&typeof a[key]==='object'&&!Array.isArray(a[key])?delta(a[key],b[key]):b[key];
}return out;}
const compact=cases.map(c=>({...c,initial:delta(baseline,c.initial),expected:delta(c.initial,c.expected)}));
// Godot's decimal parser/literals truncate long fractions. Preserve IEEE-754 doubles
// at strict lifetime/range boundaries instead of widening gameplay tolerances.
function exact(value){
 if(typeof value==='number'&&!Number.isInteger(value)){const b=Buffer.alloc(8);b.writeDoubleLE(value);return {__f64le:b.toString('hex')};}
 if(Array.isArray(value))return value.map(exact);
 if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,exact(v)]));
 return value;
}
writeFileSync(new URL('./turret-oracle.json',import.meta.url),JSON.stringify(exact({engine_sha256:hash(ref.engine),baseline,cases:compact}))+'\n');
console.log(cases.length+' original turret phase snapshots');
