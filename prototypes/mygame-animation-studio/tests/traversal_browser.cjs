/* Final exported Godot traversal/ability checks through real user input only.
 * Snapshot reads and passive camera sampling are observability, never state writes.
 */
const { chromium }=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const ROOT=path.resolve(__dirname,'..'),WEB=path.join(ROOT,'web'),OUT=path.join(ROOT,'captures','traversal-browser');
const pckSha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(WEB,'index.pck'))).digest('hex');
const IDS=['bramble','morel','velvet','cairn','iona','tam','brine','pendle','mirra','ashe','clack','nix','rook','mote'];
const MIME={'.html':'text/html','.js':'application/javascript','.wasm':'application/wasm','.pck':'application/octet-stream','.png':'image/png'};
fs.mkdirSync(OUT,{recursive:true});
const server=http.createServer((req,res)=>{
 const requested=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
 const file=path.resolve(WEB,'.'+(requested==='/'?'/index.html':requested));
 if(!file.startsWith(WEB+path.sep)){res.writeHead(403).end();return;}
 fs.readFile(file,(e,b)=>{if(e){res.writeHead(404).end();return;}res.writeHead(200,{'Content-Type':MIME[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});res.end(b);});
});
let browser,page,baseline;
const mode=process.argv.includes('--course-only')?'course':'full';
const checks=[],coverage=[],errors=[];
function check(name,value,detail){assert.ok(value,name+(detail?': '+JSON.stringify(detail):''));checks.push(name);console.log('PASS '+name);}
function camera(s){return Object.fromEntries(Object.entries(s).filter(([k])=>k.startsWith('camera_')));}
function write(extra={}){fs.writeFileSync(path.join(OUT,mode==='full'?'results.json':'results-course.json'),JSON.stringify({mode,pckSha256,checks,passed:checks.length,coverage,runtimeErrors:errors,uninterrupted_run:true,input_method:'actual canvas keyboard and focus controls; read-only snapshots',...extra},null,2));}
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--no-sandbox','--disable-dev-shm-usage','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows']});
 page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});page.setDefaultTimeout(30000);
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error'&&!/favicon/.test(m.text()))errors.push(m.text());});
 const state=()=>page.evaluate(()=>window.rosterStudy);
 const wait=(predicate,arg,timeout=30000)=>page.waitForFunction(predicate,arg,{timeout});
 const press=k=>page.keyboard.press(k);
 const snapshot=async(name)=>{await page.locator('canvas').screenshot({path:path.join(OUT,name+'.png')});};
 const select=async id=>{for(let n=0;n<IDS.length;n++){const s=await state();if(s.id===id)return;await press(']');await wait(i=>window.rosterStudy.selected===i,(s.selected+1)%IDS.length);}throw Error('Selection failed '+id);};
 const reset=async()=>{await press('r');await wait(()=>window.rosterStudy.events===0&&window.rosterStudy.hits===0&&window.rosterStudy.study&&!window.rosterStudy.powered&&!window.rosterStudy.paused&&window.rosterStudy.traversal==='');};
 const moveUntil=async(key,predicate,arg)=>{await page.keyboard.down(key);try{await wait(predicate,arg);}finally{await page.keyboard.up(key);}};
 const stableCamera=async name=>check(name,JSON.stringify(camera(await state()))===JSON.stringify(baseline));
 await page.goto('http://127.0.0.1:'+server.address().port+'/',{waitUntil:'networkidle'});
 await wait(()=>window.rosterStudy?.loaded===14&&window.rosterStudy.available&&'traversal'in window.rosterStudy,undefined,90000);
 await page.bringToFront();await page.locator('canvas').focus();baseline=camera(await state());
 await page.evaluate(()=>{window.traversalCameraSamples=[];const sample=()=>{const s=window.rosterStudy;if(s)window.traversalCameraSamples.push(Object.fromEntries(Object.entries(s).filter(([k])=>k.startsWith('camera_'))));window.traversalCameraHandle=requestAnimationFrame(sample);};sample();});
 check('new traversal snapshot is available',(await state()).loaded===14);

 // Every supplied held form is entered, used and exited through the real controls.
 if(mode==='full')for(const id of IDS){
  await select(id);await reset();
  await press('j');await wait(()=>window.rosterStudy.events===1&&window.rosterStudy.state==='');
  await press('q');await wait(()=>window.rosterStudy.events===2&&window.rosterStudy.state===''&&window.rosterStudy.traversal==='');
  check(id+' base primary and secondary each release once',(await state()).events===2);
  await reset();await press('e');
  await wait(v=>window.rosterStudy.id===v&&window.rosterStudy.powered&&window.rosterStudy.state===''&&window.rosterStudy.clip==='powered_idle',id);
  const held=await state();
  check(id+' special enters a held equipment state',held.events===1&&held.powered);
  await page.waitForTimeout(180);
  check(id+' held state survives activation recovery',(await state()).powered&&(await state()).clip==='powered_idle');
  if(id==='rook')check('Rook retains exactly two separate turrets',held.turrets===2&&(await state()).turrets===2);
  if(id==='mote')check('Mote retains three separate nonattacking orbiting shards',held.orbit_shards===3&&(await state()).orbit_shards===3&&held.turrets===0);
  await press('k');await press('Shift');await press('t');await press('q');
  const gated=await state();check(id+' unavailable powered traversal and secondary stay gated',gated.powered&&!gated.terrain&&gated.traversal===''&&gated.events===1);
  await page.keyboard.down('d');await wait(x=>window.rosterStudy.clip==='powered_walk'&&window.rosterStudy.frame>0&&window.rosterStudy.x>x+8,held.x);await page.keyboard.up('d');
  const walked=await state();check(id+' powered walk moves on flat ground with gear retained',walked.x>held.x+8&&Math.abs(walked.y-held.y)<1&&walked.powered&&walked.ground_height===0);
  await wait(()=>window.rosterStudy.clip==='powered_idle');
  await page.keyboard.down(' ');await wait(()=>window.rosterStudy.clip==='powered_guard'&&window.rosterStudy.phase==='BRACED');await page.keyboard.up(' ');
  await wait(()=>window.rosterStudy.clip==='powered_idle');
  check(id+' powered brace returns to held gear',true);
  await press('j');await wait(()=>window.rosterStudy.clip==='powered_primary');
  await wait(()=>window.rosterStudy.events===2&&window.rosterStudy.state===''&&window.rosterStudy.powered);
  check(id+' powered primary releases once then retains gear',(await state()).clip==='powered_idle');
  await snapshot(id+'-powered');
  await press('e');await wait(()=>!window.rosterStudy.powered&&window.rosterStudy.state===''&&window.rosterStudy.clip==='idle');
  const exited=await state();check(id+' authored exit restores base without a second release',exited.events===2&&exited.turrets===0&&exited.orbit_shards===0);
  // Jump uses the contact-driven runtime, not a study strip.
  const beforeJump=exited.landings;await press('k');await wait(()=>window.rosterStudy.traversal==='air'&&window.rosterStudy.jump_height>5);
  const air=await state();check(id+' airborne shadow stays on supporting ground',Math.abs(air.shadow_position[0]-air.x)<=1&&Math.abs(air.shadow_position[1]-(air.y-air.ground_height))<=1&&air.shadow_scale<1&&air.shadow_scale>=0.5);
  await wait(n=>window.rosterStudy.landings===n+1&&window.rosterStudy.traversal===''&&window.rosterStudy.grounded,beforeJump);
  const landed=await state();check(id+' jump lands once and restores grounded idle',landed.jump_height===0&&landed.clip==='idle'&&landed.events===2);
  coverage.push({id,baseActions:['primary','secondary'],powered:['special','powered_idle','powered_walk','powered_guard','powered_primary','powered_exit'],jump:true});write({completed:false});
 }
 if(mode==='full')check('all fourteen enter use and exit their supplied powered states',coverage.length===14);
 await stableCamera('all powered equipment and jumps preserve camera');

 // Interrupt airborne movement with actual pause and browser focus transitions.
 await select('nix');await reset();await press('k');await wait(()=>window.rosterStudy.traversal==='air'&&window.rosterStudy.jump_height>10);
 await press('p');await wait(()=>window.rosterStudy.paused);const frozen=await state();await page.waitForTimeout(220);
 const still=await state();check('pause freezes airborne height and drawing',still.jump_height===frozen.jump_height&&still.frame===frozen.frame&&still.x===frozen.x);
 await press('p');await wait(()=>!window.rosterStudy.paused);
 await press('j');await press('k');
 await wait(n=>window.rosterStudy.landings===n+1&&window.rosterStudy.traversal==='',frozen.landings);
 check('airborne attack and repeated jump create no late action',(await state()).events===0&&(await state()).jump_height===0);
 await press('k');await wait(()=>window.rosterStudy.traversal==='air'&&window.rosterStudy.jump_height>10);
 await page.locator('canvas').evaluate(c=>c.blur());await wait(()=>window.rosterStudy.focus);const blur=await state();await page.waitForTimeout(200);
 check('real canvas blur freezes airborne physics',(await state()).jump_height===blur.jump_height&&(await state()).traversal===blur.traversal);
 await page.locator('canvas').focus();await wait(()=>!window.rosterStudy.focus);await wait(()=>window.rosterStudy.traversal==='');
 await press('k');await wait(()=>window.rosterStudy.traversal==='air');await reset();
 check('reset clears an active jump',(await state()).jump_height===0&&(await state()).render_height===0);

 // The course is separate from the combat practice room and uses tagged support.
 await press('t');await wait(()=>window.rosterStudy.terrain&&Math.abs(window.rosterStudy.x-150)<1&&!window.rosterStudy.study);
 const courseOrigin=await state();
 await moveUntil('d',()=>window.rosterStudy.x>245&&window.rosterStudy.clip==='stair_up'&&window.rosterStudy.ground_height>8);
 const onStair=await state();await page.waitForTimeout(200);const stop=await state();
 check('stairs raise support without an airborne jump',onStair.grounded&&onStair.jump_height===0&&onStair.ground_height>8);
 check('stopping on stairs keeps the same supporting height',Math.abs(stop.x-onStair.x)<2&&Math.abs(stop.ground_height-onStair.ground_height)<1);
 await snapshot('stairs-stop');
 await moveUntil('a',()=>window.rosterStudy.clip==='stair_down'&&window.rosterStudy.x<240);
 check('reversing on the same flight selects descent',(await state()).jump_height===0);
 await moveUntil('d',()=>window.rosterStudy.x>340&&window.rosterStudy.ground_height===32);
 const plateau=await state();await page.waitForTimeout(180);check('upper landing holds the 32-pixel support',(await state()).ground_height===32&&plateau.grounded);
 await snapshot('upper-landing');
 await moveUntil('d',()=>window.rosterStudy.x>530&&window.rosterStudy.clip==='stair_down'&&window.rosterStudy.ground_height<20);
 await moveUntil('d',()=>window.rosterStudy.x>595&&window.rosterStudy.ground_height===0);
 check('opposite stairs return to ground elevation',(await state()).jump_height===0);
 await moveUntil('d',()=>window.rosterStudy.blocked_step&&window.rosterStudy.x<631);
 const blocked=await state();check('a tall side face rejects ordinary walking',blocked.x>610&&blocked.x<631&&blocked.ground_height===0);await snapshot('ledge-blocked');
 const landings=blocked.landings;await page.keyboard.down('d');await press('k');
 try{await wait(n=>window.rosterStudy.landings===n+1&&window.rosterStudy.ground_height===16&&window.rosterStudy.traversal==='',landings);}finally{await page.keyboard.up('d');}
 check('jump can land on an approved raised ledge',(await state()).x>630&&(await state()).ground_height===16);await snapshot('ledge-landed');

 // Reset and route to the lower test lane with real walking input.
 await reset();await press('b');await wait(()=>!window.rosterStudy.study&&window.rosterStudy.x===300);
 await moveUntil('s',()=>window.rosterStudy.y>=398);await moveUntil('d',()=>window.rosterStudy.surface==='wood'&&window.rosterStudy.x>390);
 const bridge=await state();check('wood bridge supplies support above the void footprint',bridge.grounded&&bridge.jump_height===0&&bridge.surface==='wood');await snapshot('bridge');
 await moveUntil('d',()=>window.rosterStudy.x>485);await moveUntil('d',()=>window.rosterStudy.surface==='water'&&window.rosterStudy.x>540);
 check('shallow water changes contact surface without granting swimming',(await state()).grounded&&(await state()).jump_height===0);await snapshot('water');
 // Route above the existing practice crate; it remains a real solid obstacle.
 await moveUntil('w',()=>window.rosterStudy.y<390);
 await moveUntil('d',()=>window.rosterStudy.surface==='ice'&&window.rosterStudy.x>695);
 check('ice remains a declared ground surface',(await state()).grounded);await snapshot('ice');
 await reset();await press('b');await wait(()=>window.rosterStudy.x===300&&!window.rosterStudy.study);
 await moveUntil('a',()=>window.rosterStudy.x<190);await moveUntil('s',()=>window.rosterStudy.surface==='mud');
 check('mud supplies a distinct grounded contact response',(await state()).grounded);await snapshot('mud');
 await reset();await press('b');await wait(()=>window.rosterStudy.x===300&&!window.rosterStudy.study);
 await moveUntil('d',()=>window.rosterStudy.x>405);await page.keyboard.down('s');
 try{await wait(()=>window.rosterStudy.traversal==='fall');await page.keyboard.up('s');await wait(p=>Math.abs(window.rosterStudy.x-p.x)<1&&Math.abs(window.rosterStudy.y-p.y)<1&&window.rosterStudy.traversal==='',{x:courseOrigin.x,y:courseOrigin.y});}finally{await page.keyboard.up('s');}
 check('unsupported pit fall returns to the explicit studio checkpoint',(await state()).grounded&&(await state()).events===0);await snapshot('pit-checkpoint');
 await press('t');await wait(()=>!window.rosterStudy.terrain);

 // Two state-dependent secondaries that previously produced misleading outcomes.
 await select('brine');await reset();await press('q');await wait(()=>window.rosterStudy.events===1&&window.rosterStudy.state==='');
 check('empty reel creates no phantom melee hit',(await state()).hits===0&&(await state()).tether===0);
 await reset();await press('j');await wait(()=>window.rosterStudy.tether>0&&window.rosterStudy.tether_target===0);await wait(()=>window.rosterStudy.state==='');
 const tethered=await state();await press('q');await wait(()=>window.rosterStudy.events===2&&window.rosterStudy.state==='');
 check('reel uses the attached target without an extra strike',(await state()).target_hits[0]===1&&tethered.tether_target===0);
 await select('rook');await reset();await press('b');await wait(()=>!window.rosterStudy.study&&window.rosterStudy.x===300);
 const vaultStart=await state();await press('q');await wait(()=>window.rosterStudy.clip==='secondary'&&window.rosterStudy.traversal==='air'&&window.rosterStudy.jump_height>5);
 const vaultAir=await state();check('Rook vault lifts the real body with a supporting-ground shadow',!vaultAir.grounded&&vaultAir.shadow_scale<1&&vaultAir.events===1&&Math.abs(vaultAir.shadow_position[1]-vaultAir.y)<=1);
 await wait(n=>window.rosterStudy.landings===n+1&&window.rosterStudy.traversal===''&&window.rosterStudy.grounded,vaultStart.landings);
 const vaultEnd=await state();check('Rook vault lands once after actual forward travel',vaultEnd.events===1&&vaultEnd.x>vaultStart.x+40&&vaultEnd.x<vaultStart.x+75&&vaultEnd.jump_height===0);
 await select('pendle');await reset();await press('q');await wait(()=>window.rosterStudy.state==='reload'&&window.rosterStudy.clip==='reload'&&window.rosterStudy.frame>0);
 const reload=await state();check('Pendle fan starts an authored reload before refill',reload.ammo===0&&reload.reload>0&&reload.events===1);
 await press('p');await wait(()=>window.rosterStudy.paused);const reloadPause=await state();await page.waitForTimeout(180);
 check('pausing reload cannot refill ammunition',(await state()).ammo===0&&(await state()).frame===reloadPause.frame);
 await press('p');await wait(()=>!window.rosterStudy.paused);await wait(()=>window.rosterStudy.ammo===6&&window.rosterStudy.reload===0&&window.rosterStudy.state==='');
 check('six-round refill occurs only after authored reload completion',(await state()).events===1);
 await stableCamera('terrain contacts and ability edge cases preserve camera');
 const samples=await page.evaluate(()=>{cancelAnimationFrame(window.traversalCameraHandle);return window.traversalCameraSamples;});
 check('every sampled camera transform stays fixed',samples.length>50&&samples.every(s=>JSON.stringify(s)===JSON.stringify(baseline)));
 check('final traversal export has no runtime errors',errors.length===0,errors);
 write({completed:true,cameraSamples:samples.length,baseline});console.log(JSON.stringify({passed:checks.length,characters:coverage.length,cameraSamples:samples.length,runtimeErrors:errors}));
})().catch(async e=>{console.error(e.stack||e);if(page){console.error('LAST STATE',await page.evaluate(()=>window.rosterStudy).catch(()=>null));await page.locator('canvas').screenshot({path:path.join(OUT,'failure.png')}).catch(()=>{});}write({completed:false,failure:e.stack||String(e)});process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();server.close();});
