/** Whole-rider full candidate on live Rookie/Pro recorded-input windows. */
/* oxlint-disable eslint/no-undef, typescript/no-extraneous-class -- headless browser globals and silent AudioContext trap. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { decodeJSON, expandFrames } from '../../../src/core/replay.ts';
import { correctiveWeights } from './runtime-corrective.mjs';
import { installContactProposals } from './contact-proposals.mjs';
const [buildArg,expandedFile,controllerFile,fixturesFile,outArg]=process.argv.slice(2);assert(outArg&&!fs.existsSync(outArg));
const build=path.resolve(buildArg),out=path.resolve(outArg);fs.mkdirSync(out,{recursive:true});const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const expandedBytes=fs.readFileSync(expandedFile),expanded=JSON.parse(expandedBytes),controllerBytes=fs.readFileSync(controllerFile),controller=JSON.parse(controllerBytes);
assert.equal(sha(expandedBytes),'ddced495c7ae0218c7ae83f5b47c1d007da137e8d7f05e37e08ae65a9c15d457');assert.deepEqual(controller.configs,expanded.configs);
const fixtureBytes=fs.readFileSync(fixturesFile),fixtures=JSON.parse(fixtureBytes),manifestBytes=fs.readFileSync(path.join(build,'hero-review.json')),manifest=JSON.parse(manifestBytes);
const candidate=manifest.models.find(m=>m.logical==='models/rider-street-mustard.glb');assert.equal(candidate.sha256,controller.candidateGLBSHA256);
assert(!manifest.newRiderAdapter&&!manifest.newRiderSeam&&!manifest.newRiderHipCorrective);
const patchesFile='docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/contact-surfaces05/surfaces.json',patchBytes=fs.readFileSync(patchesFile),patches=JSON.parse(patchBytes);
assert.equal(sha(patchBytes),'48d1379f0ebce75c328b22ea7fdbc35fc4f42bbd8c67531b821cfb18947dd209');assert.equal(patches.candidateGLBSHA256,candidate.sha256);
const targetFile='docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/bike-target-bindings04/source-components.json',targetBytes=fs.readFileSync(targetFile),targetInventory=JSON.parse(targetBytes);
const cases=fixtures.cases.filter(c=>['maximum-forward-lean','maximum-backward-lean','front-landing-recovery','rear-landing-recovery'].includes(c.kind));assert.equal(cases.length,8);
const report={status:'UNACCEPTED_RECORDED_INPUT_INTEGRATION_PENDING',build,candidate,sourceMasterSHA256:controller.candidateMasterSHA256,controllerSHA256:sha(controllerBytes),expandedSHA256:sha(expandedBytes),fixturesSHA256:sha(fixtureBytes),manifestSHA256:sha(manifestBytes),
  riderPatchesFile:patchesFile,riderPatchesSHA256:sha(patchBytes),targetFile,targetInventorySHA256:sha(targetBytes),contactCodeSHA256:sha(fs.readFileSync(new URL('contact-proposals.mjs',import.meta.url))),
  captureCodeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),controllerCodeSHA256:sha(fs.readFileSync(new URL('runtime-corrective.mjs',import.meta.url))),errors:[],loaded:[],cases:[],clips:[],
  limits:['Actual normal game rider update and live bike, no bone/pose/physics injection. Private local-angle morph controller only.',
    'Full candidate high tier only; no candidate LOD supplied. Headless WebKit is not physical iOS or desktop approval.',
    'Every input tick is rendered and traced. Screenshots sample ticks every10 plus three exact fixture witnesses; unrecorded visual instants remain unreviewed.',
    'All five contact acceptance statuses remain UNMEASURED pending parent review of automatic rider masks and detailed support subsets. Separate proposal measurements are numeric samples, never socket booleans or a contact pass.',
    'Whole-body framing and deterministic physics do not establish art, collision, continuous clearance or support acceptance.']};
const server=await preview({configFile:false,root:process.cwd(),build:{outDir:build},preview:{host:'127.0.0.1',port:0},logLevel:'warn'});
const browser=await webkit.launch({headless:true}),context=await browser.newContext({viewport:{width:960,height:640},deviceScaleFactor:1});
await context.addInitScript(()=>{localStorage.setItem('rockhop.onboarded','1');window.__agent3AudioCount=0;for(const k of['AudioContext','webkitAudioContext'])window[k]=class{constructor(){window.__agent3AudioCount++;throw new Error('Silent recorded-input capture');}};});
const page=await context.newPage(),responses=[];page.on('pageerror',e=>report.errors.push(e.message));
page.on('response',r=>{if(r.url().endsWith('.glb'))responses.push(r.body().then(b=>report.loaded.push({url:r.url(),sha256:sha(b),status:r.status()})));});
try{
  await page.goto(server.resolvedUrls.local[0]+'?harness=1&audio=0&sw=0&outfit=street-mustard&physics=v2&hz=120');
  await page.waitForFunction(()=>window.__rockhop?.ready,null,{timeout:120000});
  await page.waitForFunction(()=>!document.querySelector('#loader')||document.querySelector('#loader').getAttribute('data-done')==='1',null,{timeout:120000});
  await page.addStyleTag({content:'#ui,#ui *,.hud,.touch-controls{visibility:hidden!important} #agent3-label{position:fixed;z-index:99999;top:8px;left:10px;color:white;background:#101820e8;padding:8px;font:14px monospace;white-space:pre;visibility:visible!important}'});
  await page.addScriptTag({content:`window.__agent3CorrectiveWeights=${correctiveWeights.toString()};`});
  for(const c of cases){
    const file=path.join(path.dirname(fixturesFile),c.recording),bytes=fs.readFileSync(file);assert.equal(sha(bytes),c.sourceSHA256);
    const recording=decodeJSON(bytes.toString()),inputs=expandFrames(recording);assert.equal(recording.header.bike??'rookie',c.bike);
    await page.evaluate(async({header})=>{const t=window.__rockhop,r=window.__render;t.setBike(header.bike??'rookie');await r.whenReady();await t.loadTrack(header.trackId,header.seed);t.setQuality('high');await r.whenReady();t.skipCountdown();t.render(true);},{header:recording.header});
    const loader=await page.evaluate(({controller,expanded})=>{
      const d=window.__render.debug,rider=d.rider,source=rider.source.parser.json;
      if(source.nodes[59]?.extras?.rockhopAppearanceCandidate!=='unaccepted appearance05 zero-rest defaults')throw new Error('Not frozen05 source');
      const bones=new Map();for(const[o,a]of rider.source.parser.associations){if(!o.isBone||a.nodes===undefined)continue;const name=source.nodes[a.nodes].name,m=rider.scene.getObjectsByProperty('name',o.name);if(m.length!==1)throw new Error('Bone ambiguity');bones.set(name,m[0]);}
      if(bones.size!==51)throw new Error('Complete51 skin missing');
      const meshes=rider.sleeveGeometry.map(i=>i.mesh),entries=controller.configs.map(config=>{
        const parts=meshes.filter(m=>config.keys.every(k=>Number.isInteger(m.morphTargetDictionary?.[k])));if(parts.length!==(config.region==='cloth'?2:1))throw new Error('Target part mismatch');
        const rest=new Map(config.joints.map(name=>{const q=rider.restLocalQ.get(name);if(!q)throw new Error('Missing local rest '+name);return[name,q.clone().normalize().invert()];}));return{config,parts,rest};
      });
      const snap=meshes.map(m=>{const entry=rider.sleeveGeometry.find(i=>i.mesh===m);let owner=m;while(owner&&owner.userData.rockhopRiderSkinConditioned===undefined)owner=owner.parent;if(owner?.userData.rockhopRiderSkinConditioned!==1||entry.authored!==entry.riding)throw new Error('Conditioning drift');const mats=Array.isArray(m.material)?m.material:[m.material];return{mesh:m.name,vertices:m.geometry.attributes.position.count,targets:m.morphTargetDictionary??{},authoredEqualsRiding:true,owner:owner.name,materials:mats.map(mat=>({name:mat.name,type:mat.type,roughness:mat.roughness,metalness:mat.metalness,color:mat.color?.toArray(),side:mat.side,mapSize:mat.map?[mat.map.image?.width,mat.map.image?.height]:null,mapColorSpace:mat.map?.colorSpace}))};});
      const original=rider.update.bind(rider);if(rider.__agent3OriginalUpdate)rider.update=rider.__agent3OriginalUpdate;else rider.__agent3OriginalUpdate=original;
      const a={rider,bones,meshes,entries,expanded,coefficients:[],apply(){this.coefficients=[];for(const e of entries){const basis=Object.fromEntries(e.config.joints.map(name=>{const b=bones.get(name);if(!b?.matrixAutoUpdate)throw new Error('Authored pose injection detected');const q=e.rest.get(name).clone().multiply(b.quaternion).normalize();return[name,[q.w,q.x,q.y,q.z]];}));const values=window.__agent3CorrectiveWeights(e.config,basis,expanded.centers[e.config.region]);for(const m of e.parts){m.morphTargetInfluences.fill(0);for(let k=0;k<e.config.keys.length;k++)m.morphTargetInfluences[m.morphTargetDictionary[e.config.keys[k]]]=values[k];}this.coefficients.push({region:e.config.region,values,parts:e.parts.map(m=>m.name)});}rider.scene.updateMatrixWorld(true);for(const m of meshes)m.skeleton.update();}};
      rider.update=function(...args){rider.__agent3OriginalUpdate(...args);a.apply();};window.__agent3Ride=a;
      let label=document.getElementById('agent3-label');if(!label){label=document.createElement('div');label.id='agent3-label';document.body.append(label);}
      return{completeBones:51,meshes:snap,normalGamePose:true,privateMorphOnly:true,stage:false};
    },{controller,expanded});
    const bikeSource=targetInventory.reports.find(r=>r.logical===`models/bike-${c.bike}.glb`);assert(bikeSource);
    const model=manifest.models.find(m=>m.logical===bikeSource.logical);assert.equal(model.sha256,bikeSource.assetSHA256);
    const contactBinding=await installContactProposals(page,patches,bikeSource);
    const folder=path.join(out,c.id);fs.mkdirSync(folder);const samples=[],tickTrace=[];let previous=0,filmFrame=0;
    const captureTicks=[...new Set([...Array.from({length:Math.floor((c.window.endInputTick-c.window.startInputTick)/10)+1},(_,i)=>c.window.startInputTick+i*10),...c.matchedSamples.map(s=>s.inputTick)])].sort((a,b)=>a-b);
    for(const inputTick of captureTicks){
      const sample=await page.evaluate(({input,firstTick,inputTick,id})=>{
        const t=window.__rockhop,r=window.__render,d=r.debug,T=d.THREE,a=window.__agent3Ride,trace=[];
        for(let i=0;i<input.length;i++){t.setInput(input[i]);t.step(1);t.render(true);trace.push({inputTick:firstTick+i,stateHash:t.hashState(),tick:t.getState().tick,phase:t.phase(),runTime:t.runTime(),finishTime:t.getState().finishTime,coefficients:structuredClone(a.coefficients)});}
        const p=a.bones.get('pelvis').getWorldPosition(new T.Vector3());p.y+=.1;
        r.setCameraOverride({mode:'orbit',yaw:.6,pitch:.1,dist:6,x:p.x,y:p.y,screenX:.5,screenY:.5});
        document.getElementById('agent3-label').textContent=`UNACCEPTED RECORDED RIDING | ${id}\nLive bike + normal51-joint game pose | private local morph driver\nInput tick${inputTick} | colored patch proposals / support measurements`;
        r.invalidate();t.render(true);
        const bounds={minX:Infinity,minY:Infinity,maxX:-Infinity,maxY:-Infinity},v=new T.Vector3();for(const m of a.meshes){m.skeleton.update();for(let i=0;i<m.geometry.attributes.position.count;i++){m.getVertexPosition(i,v).applyMatrix4(m.matrixWorld).project(d.rig.camera);const x=(v.x+1)*480,y=(1-v.y)*320;bounds.minX=Math.min(bounds.minX,x);bounds.maxX=Math.max(bounds.maxX,x);bounds.minY=Math.min(bounds.minY,y);bounds.maxY=Math.max(bounds.maxY,y);}}
        return{inputTick,tick:t.getState().tick,stateHash:t.hashState(),phase:t.phase(),trace,wholeRiderPixelBounds:bounds,
          coefficients:structuredClone(a.coefficients),poseInjection:false,bikeVisible:d.bike.root.visible,stage:r.debugInfo().garage.on,
          riderWrapperWorld:a.rider.scene.matrixWorld.toArray(),bikeFrameWorld:d.bike.frame.matrixWorld.toArray(),cameraWorld:d.rig.camera.matrixWorld.toArray(),cameraProjection:d.rig.camera.projectionMatrix.toArray(),
          proposalMeasurements:window.__agent3ProposalContacts.measure(),
          contacts:Object.fromEntries(['hand.L','hand.R','foot.L','foot.R','saddle'].map(k=>[k,{status:'unmeasured',reason:'Automatic rider masks and detailed support subsets await parent review'}])),socketDebug:structuredClone(a.rider.debug),audioContexts:window.__agent3AudioCount,webdriver:navigator.webdriver};
      },{input:inputs.slice(previous,inputTick),firstTick:previous+1,inputTick,id:c.id});previous=inputTick;
      assert(sample.webdriver&&sample.audioContexts===0&&sample.phase==='riding'&&!sample.stage&&sample.bikeVisible);
      const witness=c.matchedSamples.find(s=>s.inputTick===inputTick);if(witness)assert.equal(sample.stateHash,witness.stateHash,'Actual candidate physics witness mismatch');
      const b=sample.wholeRiderPixelBounds;assert(b.minX>=0&&b.maxX<=960&&b.minY>=80&&b.maxY<=640,'Whole rider clipping or label overlap '+JSON.stringify(b));
      for(const tick of sample.trace)for(const row of tick.coefficients)assert(row.values.every(v=>Number.isFinite(v)&&v>=0)&&row.values.reduce((s,v)=>s+v,0)<=1+1e-12);
      tickTrace.push(...sample.trace);delete sample.trace;samples.push(sample);await page.screenshot({path:path.join(folder,String(filmFrame++).padStart(4,'0')+'.png')});
    }
    assert.equal(tickTrace.length,c.window.endInputTick);
    const traceBytes=Buffer.from(tickTrace.map(t=>JSON.stringify(t)).join('\n')+'\n');fs.writeFileSync(path.join(folder,'tick-trace.ndjson'),traceBytes);
    const movie=path.join(folder,'played.mp4'),ff=spawnSync('ffmpeg',['-v','error','-y','-framerate','12','-i',path.join(folder,'%04d.png'),'-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p','-an','-movflags','+faststart',movie],{encoding:'utf8'});assert.equal(ff.status,0,ff.stderr);
    report.clips.push({path:movie,sha256:sha(fs.readFileSync(movie)),frames:filmFrame,fps:12,audio:false});report.cases.push({id:c.id,bike:c.bike,recordingSHA256:sha(bytes),window:c.window,loader,contactBinding,samples,everyTickTraceSHA256:sha(traceBytes),everyTickCount:tickTrace.length,fixtureWitnessesExact:true});
  }
  await Promise.all(responses);assert(report.loaded.some(l=>l.sha256===candidate.sha256&&l.status===200));assert.deepEqual(report.errors,[]);report.status='UNACCEPTED_RECORDED_INPUT_INTEGRATION_CAPTURED';
}catch(e){report.failure=String(e);process.exitCode=1;}
finally{fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');await context.close();await browser.close();await new Promise(resolve=>server.httpServer.close(resolve));console.log(JSON.stringify({status:report.status,cases:report.cases.length,clips:report.clips.length,failure:report.failure}));}
