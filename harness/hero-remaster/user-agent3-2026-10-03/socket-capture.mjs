/** Played actual physical-body pose with private geometry-derived sockets. */
/* oxlint-disable eslint/no-undef, typescript/no-extraneous-class -- headless page and silent AudioContext trap. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { decodeJSON, expandFrames } from '../../../src/core/replay.ts';
const [buildArg,fixtureFile,sourceReceipt,outArg]=process.argv.slice(2);assert(outArg&&!fs.existsSync(outArg));
const build=path.resolve(buildArg),out=path.resolve(outArg),sha=b=>crypto.createHash('sha256').update(b).digest('hex');fs.mkdirSync(out,{recursive:true});
const source=JSON.parse(fs.readFileSync(sourceReceipt)),fixtures=JSON.parse(fs.readFileSync(fixtureFile)),manifest=JSON.parse(fs.readFileSync(path.join(build,'hero-review.json')));
const candidate=manifest.models.find(m=>m.logical==='models/rider-street-mustard.glb');assert.equal(candidate.sha256,source.derivativeSHA256);
const cases=fixtures.cases.filter(c=>c.bike==='rookie'&&['maximum-forward-lean','maximum-backward-lean'].includes(c.kind));assert.equal(cases.length,2);
const report={status:'UNACCEPTED_SOCKET_PHYSICAL_BRANCH_PENDING',candidate,sourceReceiptSHA256:sha(fs.readFileSync(sourceReceipt)),captureSHA256:sha(fs.readFileSync(new URL(import.meta.url))),
  physicsSourceSHA256:sha(fs.readFileSync('src/physics/v2/engine.ts')),engineSourceSHA256:sha(fs.readFileSync('src/render/hero/GltfRider.ts')),errors:[],loaded:[],cases:[],
  limits:['Current05 wardrobe remains human rejected. Socket centroid positions are diagnostic proposals, not fit/contact acceptance.',
    'Normal actual recorded inputs, rider.update and live bike; no pose/physics injection or garment registration.',
    'The named grip sockets enable authoritative COM/angle branch. Sole sockets still measure only; sole IK offset and load-bearing support remain open.',
    'Full candidate only, no candidateLOD, closed-volume collision proof or physical iPhone result.']};
const server=await preview({configFile:false,root:process.cwd(),build:{outDir:build},preview:{host:'127.0.0.1',port:0},logLevel:'warn'}),browser=await webkit.launch({headless:true}),context=await browser.newContext({viewport:{width:960,height:640}});
await context.addInitScript(()=>{localStorage.setItem('rockhop.onboarded','1');window.__agent3AudioCount=0;for(const k of ['AudioContext','webkitAudioContext'])window[k]=class{constructor(){window.__agent3AudioCount++;throw new Error('Silent socket control');}};});
const page=await context.newPage(),responses=[];page.on('pageerror',e=>report.errors.push(e.message));page.on('response',r=>{if(r.url().endsWith('.glb'))responses.push(r.body().then(b=>report.loaded.push({sha256:sha(b),status:r.status()})));});
try{
  await page.goto(server.resolvedUrls.local[0]+'?harness=1&audio=0&sw=0&outfit=street-mustard&physics=v2&hz=120');await page.waitForFunction(()=>window.__rockhop?.ready,null,{timeout:120000});
  await page.addStyleTag({content:'#ui,#ui *,.hud,.touch-controls{visibility:hidden!important} #agent3-label{position:fixed;z-index:99999;top:8px;left:10px;color:white;background:#101820e8;padding:8px;font:14px monospace;white-space:pre;visibility:visible!important}'});
  for(const c of cases){
    const bytes=fs.readFileSync(path.join(path.dirname(fixtureFile),c.recording));assert.equal(sha(bytes),c.sourceSHA256);const recording=decodeJSON(bytes.toString()),inputs=expandFrames(recording);
    await page.evaluate(async header=>{const t=window.__rockhop,r=window.__render;t.setBike(header.bike??'rookie');await r.whenReady();await t.loadTrack(header.trackId,header.seed);t.setQuality('high');await r.whenReady();t.skipCountdown();t.render(true);},recording.header);
    const folder=path.join(out,c.id);fs.mkdirSync(folder);const samples=[],trace=[];let previous=0,frame=0;
    const ticks=[...new Set([...Array.from({length:19},(_,i)=>c.window.startInputTick+i*10),...c.matchedSamples.map(s=>s.inputTick)])].sort((a,b)=>a-b);
    for(const tick of ticks){
      const sample=await page.evaluate(({inputs,start,tick,id})=>{
        const t=window.__rockhop,r=window.__render,d=r.debug,T=d.THREE,a=d.rider,trace=[];
        for(let i=0;i<inputs.length;i++){t.setInput(inputs[i]);t.step(1);t.render(true);trace.push({inputTick:start+i,stateHash:t.hashState(),tick:t.getState().tick,phase:t.phase(),runTime:t.runTime(),finishTime:t.getState().finishTime,physicalPose:a.debug.physicalPose});}
        const p=a.scene.getObjectByName('pelvis').getWorldPosition(new T.Vector3());p.y+=.1;r.setCameraOverride({mode:'orbit',yaw:.6,pitch:.1,dist:6,x:p.x,y:p.y,screenX:.5,screenY:.5});
        let label=document.getElementById('agent3-label');if(!label){label=document.createElement('div');label.id='agent3-label';document.body.append(label);}label.textContent=`REJECTED05 WARDROBE | PRIVATE SOCKET CONTRACT\n${id} | input tick ${tick}\nNormal riderBody COM/angle pose | markers are proposals`;
        r.invalidate();t.render(true);
        const points=Object.fromEntries(['gripSocketL','gripSocketR','soleSocketL','soleSocketR'].map(name=>{const o=a.scene.getObjectByName(name);if(!o)throw new Error('Missing runtime '+name);return[name,{world:o.getWorldPosition(new T.Vector3()).toArray(),quaternion:o.getWorldQuaternion(new T.Quaternion()).toArray()}];}));
        return{inputTick:tick,stateHash:t.hashState(),phase:t.phase(),trace,debug:structuredClone(a.debug),points,poseInjection:false,audioContexts:window.__agent3AudioCount,webdriver:navigator.webdriver};
      },{inputs:inputs.slice(previous,tick),start:previous+1,tick,id:c.id});previous=tick;
      assert(sample.webdriver&&sample.audioContexts===0&&sample.phase==='riding'&&sample.debug.physicalPose&&sample.debug.stance.on);const witness=c.matchedSamples.find(s=>s.inputTick===tick);if(witness)assert.equal(sample.stateHash,witness.stateHash);
      trace.push(...sample.trace);delete sample.trace;samples.push(sample);await page.screenshot({path:path.join(folder,String(frame++).padStart(4,'0')+'.png')});
    }
    assert.equal(trace.length,c.window.endInputTick);assert(trace.every(t=>t.physicalPose));fs.writeFileSync(path.join(folder,'tick-trace.ndjson'),trace.map(t=>JSON.stringify(t)).join('\n')+'\n');
    const movie=path.join(folder,'played.mp4'),ff=spawnSync('ffmpeg',['-v','error','-y','-framerate','12','-i',path.join(folder,'%04d.png'),'-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p','-an','-movflags','+faststart',movie],{encoding:'utf8'});assert.equal(ff.status,0,ff.stderr);
    report.cases.push({id:c.id,recordingSHA256:sha(bytes),everyInputTickCount:trace.length,everyInputTraceSHA256:sha(fs.readFileSync(path.join(folder,'tick-trace.ndjson'))),samples,clip:{sha256:sha(fs.readFileSync(movie)),frames:frame,fps:12}});
  }
  await Promise.all(responses);assert(report.loaded.some(r=>r.status===200&&r.sha256===candidate.sha256));assert.deepEqual(report.errors,[]);report.status='UNACCEPTED_ACTUAL_PHYSICAL_BODY_BRANCH_CAPTURED';
}catch(e){report.failure=String(e);process.exitCode=1;}
finally{fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');await context.close();await browser.close();await new Promise(resolve=>server.httpServer.close(resolve));console.log(JSON.stringify({status:report.status,cases:report.cases.length,failure:report.failure}));}
