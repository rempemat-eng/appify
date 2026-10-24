/* Real exported Godot input checks. No injected game state or mock renderer. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const ROOT=path.resolve(__dirname,'..'), WEB=path.join(ROOT,'web'), OUT=path.join(ROOT,'captures','roster-browser');
const pckSha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(WEB,'index.pck'))).digest('hex');
const IDS=['bramble','morel','velvet','cairn','iona','tam','brine','pendle','mirra','ashe','clack','nix','rook','mote'];
const characterArg=process.argv.find(v=>v.startsWith('--character='));
const requestedCharacter=characterArg?.split('=')[1];
if(requestedCharacter&&!IDS.includes(requestedCharacter))throw Error('Unknown character '+requestedCharacter);
const CLIPS=['idle','walk','primary','secondary','special','guard','hit','defeat','jump','stair_up','stair_down','dodge','powered_idle','powered_walk','powered_primary','powered_guard','powered_exit'];
const LOOPED=new Set(['idle','walk','stair_up','stair_down','powered_idle','powered_walk']);
const MIME={'.html':'text/html','.js':'application/javascript','.wasm':'application/wasm','.pck':'application/octet-stream','.png':'image/png'};
fs.mkdirSync(OUT,{recursive:true});
const server=http.createServer((req,res)=>{
 const requested=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
 const file=path.resolve(WEB,'.'+(requested==='/'?'/index.html':requested));
 if(!file.startsWith(WEB+path.sep)){res.writeHead(403).end();return;}
 fs.readFile(file,(error,bytes)=>{if(error){res.writeHead(404).end();return;}res.writeHead(200,{'Content-Type':MIME[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});res.end(bytes);});
});
const checks=[],coverage=[],runtimeErrors=[];
let browser,page,baseline,sampleCount=0;
const mode=requestedCharacter?'character-'+requestedCharacter:process.argv.includes('--controls-only')?'controls':process.argv.includes('--roster-only')?'roster':'full';
function check(name,value,detail){assert.ok(value,name+(detail?': '+JSON.stringify(detail):''));checks.push(name);console.log('PASS '+name);}
function cam(s){return Object.fromEntries(Object.entries(s).filter(([key])=>key.startsWith('camera_')));}
function result(extra={}){fs.writeFileSync(path.join(OUT,'results-'+mode+'.json'),JSON.stringify({mode,pckSha256,passed:checks.length,checks,coverage,runtimeErrors,sampleCount,baseline,focus_method:'real canvas blur()/focus()',uninterrupted_run:true,...extra},null,2));}
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows']});
 page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 page.setDefaultTimeout(30000);
 page.on('pageerror',e=>runtimeErrors.push(e.message));
 page.on('console',m=>{if(m.type()==='error'&&!/favicon/.test(m.text()))runtimeErrors.push(m.text());});
 const state=()=>page.evaluate(()=>window.rosterStudy);
 const wait=(fn,arg,timeout=30000)=>page.waitForFunction(fn,arg,{timeout});
 const press=async key=>{let timer;try{return await Promise.race([page.keyboard.press(key),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Keyboard dispatch exceeded 20 seconds: '+key)),20000);})]);}finally{clearTimeout(timer);}};
 const focus=async()=>{await page.bringToFront();await page.locator('canvas').focus();};
 const stable=async name=>check(name,JSON.stringify(cam(await state()))===JSON.stringify(baseline));
 const select=async id=>{
  for(let i=0;i<IDS.length;i++){
   const s=await state();if(s.id===id)return s;
   const next=(s.selected+1)%IDS.length;
   await press(']');await wait(value=>window.rosterStudy?.selected===value,next);
  }throw new Error('Selection failed: '+id);
 };
 const reset=async()=>{await press('r');await wait(()=>window.rosterStudy?.events===0&&window.rosterStudy.hits===0&&window.rosterStudy.study&&!window.rosterStudy.paused&&window.rosterStudy.x===360);};
 await page.goto('http://127.0.0.1:'+server.address().port+'/',{waitUntil:'networkidle'});
 await wait(()=>window.rosterStudy?.loaded===14&&window.rosterStudy.available,undefined,90000);
 await focus();
 const initial=await state();baseline=cam(initial);
 check('all fourteen resources load',initial.loaded===14&&initial.count===14&&initial.available);
 check('initial camera is unrotated and has no offset',initial.camera_rotation===0&&initial.camera_offset.every(v=>v===0));
 await page.evaluate(()=>{
  window.animationCameraSamples=[];window.animationFrameSamples={};
  const sample=()=>{
   const s=window.rosterStudy;
   if(s){
    window.animationCameraSamples.push(Object.fromEntries(Object.entries(s).filter(([key])=>key.startsWith('camera_'))));
    const key=s.id+'/'+s.clip;
    const frames=window.animationFrameSamples[key]||(window.animationFrameSamples[key]=[]);
    if(!frames.includes(s.frame))frames.push(s.frame);
   }
   window.animationCameraHandle=requestAnimationFrame(sample);
  };sample();
 });
 // Real focus is tested first.
 await press('b');await wait(()=>!window.rosterStudy.study);
 const start=await state();await page.keyboard.down('d');await wait(x=>window.rosterStudy.x>x+10,start.x);
 await page.locator('canvas').evaluate(canvas=>canvas.blur());await wait(()=>window.rosterStudy.focus);
 const stopped=await state();await page.waitForTimeout(300);
 check('actual canvas blur suspends without drift',(await state()).x===stopped.x&&(await state()).y===stopped.y);
 await page.keyboard.up('d');await focus();await wait(()=>!window.rosterStudy.focus);
 const resumed=await state();await page.waitForTimeout(300);
 check('refocus clears held movement',Math.abs((await state()).x-resumed.x)<1);
 await stable('focus preserves camera');await reset();
 if(mode!=='roster'){
  await press('2');await wait(()=>window.rosterStudy.clip==='walk'&&window.rosterStudy.frame>0);
  await press('p');await wait(()=>window.rosterStudy.paused);
  const frozen=await state();await page.waitForTimeout(300);
  check('pause freezes drawing and position',(await state()).frame===frozen.frame&&(await state()).x===frozen.x);
  await press('.');await wait(v=>window.rosterStudy.frame===(v.frame+1)%v.frame_count,frozen);
  await press(',');await wait(v=>window.rosterStudy.frame===v.frame,frozen);
  check('paused frame controls step both ways',true);
  await press('p');await wait(()=>!window.rosterStudy.paused);
  await press('v');await wait(()=>window.rosterStudy.speed===0.5);
  await press('v');await wait(()=>window.rosterStudy.speed===1);
  check('playback speed toggles and returns',true);
  await press('c');await wait(()=>window.rosterStudy.inspector);
  await press('c');await wait(()=>!window.rosterStudy.inspector);
  check('inspector opens and closes',true);
  await press('3');await wait(()=>window.rosterStudy.clip==='primary'&&!window.rosterStudy.loop);
  await page.mouse.click(1010,971);await wait(()=>window.rosterStudy.loop);
  const loop=await state();await wait(frame=>window.rosterStudy.clip==='primary'&&window.rosterStudy.frame!==frame,loop.frame);
  await page.mouse.click(1010,971);await wait(()=>!window.rosterStudy.loop);
  check('canvas loop control repeats and stops clip',true);
  await stable('review controls preserve camera');await reset();
 }
 if(mode!=='controls'){
  await select(IDS[0]);
  const roster=requestedCharacter?[requestedCharacter]:IDS;
  for(const id of roster){
   const loaded=await select(id);
   check(id+' resource selects',loaded.available&&loaded.id===id&&loaded.loaded===14);
   const clips=id==='pendle'?[...CLIPS,'reload']:CLIPS;
   for(let index=0;index<clips.length;index++){
    const clip=clips[index];if(process.env.BROWSER_TRACE)console.log('PLAY '+id+' / '+clip);await press(index===0?'1':'n');
    let observed=await wait(v=>{
     const s=window.rosterStudy;
     return s?.id===v.id&&s.clip===v.clip&&s.study&&!s.paused&&s.frame_count>=4&&s.frame>0&&s.clock>0?s:false;
    },{id,clip});
    if(!LOOPED.has(clip))observed=await wait(v=>{
     const s=window.rosterStudy;
     return s?.id===v.id&&s.clip===v.clip&&s.frame===s.frame_count-1?s:false;
    },{id,clip});
    // Retain the state that satisfied the predicate; looping frames may wrap
    // between it and another browser read.
    const played=await observed.jsonValue();
    coverage.push({id,clip,frameCount:played.frame_count,reachedFrame:played.frame,clock:played.clock,completedOneShot:!LOOPED.has(clip)});
    check(id+' / '+clip+' plays'+(!LOOPED.has(clip)?' and completes':''),played.frame>0&&played.events===0);
   }
   await press('2');await wait(v=>window.rosterStudy.id===v&&window.rosterStudy.clip==='walk'&&window.rosterStudy.frame>0,id);
   await press('p');await wait(()=>window.rosterStudy.paused);
   await page.locator('canvas').screenshot({path:path.join(OUT,id+'.png')});
   await press('p');await wait(()=>!window.rosterStudy.paused);result({completed:false});
  }
  const expected=roster.reduce((total,id)=>total+CLIPS.length+(id==='pendle'?1:0),0);
  check('all'+expected+' character/clip combinations exercised',coverage.length===expected&&new Set(coverage.map(v=>v.id+'/'+v.clip)).size===expected);
  await stable('all roster clips preserve camera');
 }
 if(mode!=='roster'){
  await select('nix');await reset();await press('j');
  await wait(()=>window.rosterStudy.id==='nix'&&window.rosterStudy.events===1&&window.rosterStudy.hits>=1);
  await wait(()=>window.rosterStudy.state==='');
  const hit=await state();await page.waitForTimeout(250);
  check('Nix primary releases once and hits actual first target',hit.target_hits[0]===1&&(await state()).events===1);
  const activation=await state();
  await press('q');await wait(()=>window.rosterStudy.decoy>0);
  const ghost=await state();await page.keyboard.down('a');await wait(x=>window.rosterStudy.x<x-10,ghost.x);await page.keyboard.up('a');
  check('Afterimage captures activation origin and stays there',Math.abs(ghost.decoy_origin[0]-activation.x)<1&&Math.abs(ghost.decoy_origin[1]-activation.y)<1&&JSON.stringify((await state()).decoy_origin)===JSON.stringify(ghost.decoy_origin));
  await select('cairn');await reset();await press('j');
  await wait(()=>window.rosterStudy.id==='cairn'&&window.rosterStudy.events===1&&window.rosterStudy.hits>=1);
  await wait(()=>window.rosterStudy.state==='');
  check('Cairn releases once and strikes reachable target',(await state()).target_hits[0]===1);
  await page.keyboard.down(' ');await wait(()=>window.rosterStudy.clip==='guard'&&window.rosterStudy.phase==='BRACED');
  await page.keyboard.up(' ');await wait(()=>window.rosterStudy.clip==='idle');
  check('held guard enters and releases cleanly',true);
  await stable('practice combat preserves camera');await reset();
  await press('Tab');await wait(()=>window.rosterStudy.demo&&window.rosterStudy.demo_clock>2);
  await press('Tab');await wait(()=>!window.rosterStudy.demo&&window.rosterStudy.events===0);
  check('demonstration advances and returns control',(await state()).loaded===14);
 }
 const samples=await page.evaluate(()=>{
  cancelAnimationFrame(window.animationCameraHandle);
  return {camera:window.animationCameraSamples,frames:window.animationFrameSamples};
 });
 sampleCount=samples.camera.length;
 for(const entry of coverage)entry.observedFrames=samples.frames[entry.id+'/'+entry.clip]||[];
 check('all sampled camera transforms are fixed',sampleCount>10&&samples.camera.every(v=>JSON.stringify(v)===JSON.stringify(baseline)));
 check('no browser or Godot runtime errors',runtimeErrors.length===0,runtimeErrors);
 result({completed:true});console.log(JSON.stringify({passed:checks.length,clipCoverage:coverage.length,sampleCount,runtimeErrors}));
})().catch(async error=>{
 console.error(error.stack||error);
 if(page){
  console.error('LAST STATE',await page.evaluate(()=>window.rosterStudy).catch(()=>null));
  await page.locator('canvas').screenshot({path:path.join(OUT,'failure-'+mode+'.png')}).catch(()=>{});
 }
 result({completed:false,failure:error.stack||String(error)});process.exitCode=1;
}).finally(async()=>{if(browser)await browser.close();server.close();});

