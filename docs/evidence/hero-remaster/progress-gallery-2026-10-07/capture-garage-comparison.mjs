/* oxlint-disable eslint/no-undef -- in-page game globals used by the headless harness. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { preview } from 'vite';
import { webkit } from 'playwright';
const [beforeBuild, nowBuild, output] = process.argv.slice(2);
assert(output, 'Supply frozen before build, current build and fresh output');
const out = path.resolve(output);assert(!fs.existsSync(out));fs.mkdirSync(out,{recursive:true});
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const report={kind:'Matched normal Garage playback; before build replayed today',viewport:{width:1280,height:720},fps:12,seconds:6,candidateReplacement:false,clock:'Harness advances the normal authored Garage stage clock at 12 fps; no bone or skin override',captures:[]};
const browser=await webkit.launch({headless:true});
try {
 for(const [label,buildArg] of [['before',beforeBuild],['now',nowBuild]]){
  const build=path.resolve(buildArg), frames=path.join(out,label);fs.mkdirSync(frames);
  const catalog=JSON.parse(fs.readFileSync(path.join(build,'model-catalog.json')));
  const target=catalog.models.find(x=>x.logical==='models/rider-street-mustard.glb');assert(target);
  const server=await preview({configFile:false,root:process.cwd(),build:{outDir:build},preview:{host:'127.0.0.1',port:0},logLevel:'error'});
  const context=await browser.newContext({viewport:report.viewport,deviceScaleFactor:1});
  await context.addInitScript(()=>{localStorage.setItem('rockhop.onboarded','1');window.__garageAudioCount=0;for(const k of ['AudioContext','webkitAudioContext'])window[k]=class{constructor(){window.__garageAudioCount++;throw new Error('Silent capture forbids audio');}};});
  const page=await context.newPage(),errors=[],loaded=[],pending=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.url().endsWith('.glb'))pending.push(r.body().then(b=>loaded.push({url:r.url(),sha256:hash(b),bytes:b.length,status:r.status()})));});
  try{
   await page.goto(server.resolvedUrls.local[0]+'?audio=0&sw=0&outfit=street-mustard&rider=gltf&bike=gltf&physics=v2',{waitUntil:'domcontentloaded'});
   await page.waitForSelector('.menu-screen.live .menu-item[data-id=garage]',{timeout:120000});
   await page.locator('.menu-screen.live .menu-item[data-id=garage]').click();await page.waitForSelector('.garage-screen.live');
   await page.locator('button[data-outfit=street-mustard]').click();
   await page.evaluate(async()=>{const t=window.__rockhop,r=window.__render;t.setQuality('high');await r.whenReady();r.advancePresentation=()=>{};t.render(true);});
   await page.waitForTimeout(500);
   const samples=[];
   for(let i=0;i<72;i++){
    samples.push(await page.evaluate(({i,fps})=>{const t=window.__rockhop,r=window.__render;r.stageTime=i/fps;r.invalidate();t.render(true);const d=r.debugInfo(),c=r.debug.rig.camera;return {i,stageTime:r.stageTime,physicsHash:t.hashState(),heroDoc:d.heroDoc,camera:{position:c.position.toArray(),quaternion:c.quaternion.toArray(),fov:c.fov,zoom:c.zoom},audioContexts:window.__garageAudioCount};},{i,fps:12}));
    await page.screenshot({path:path.join(frames,`${String(i).padStart(4,'0')}.png`)});
   }
   await Promise.all(pending);assert(loaded.some(x=>x.url.endsWith('/'+target.url)&&x.sha256===target.sha256&&x.status===200));assert.deepEqual(errors,[]);assert(samples.every(x=>x.audioContexts===0));
   report.captures.push({label,build,version:JSON.parse(fs.readFileSync(path.join(build,'version.json'))),target,loaded,errors,samples});
  }finally{await context.close();await new Promise((resolve,reject)=>server.httpServer.close(e=>e?reject(e):resolve()));}
 }
 assert.equal(report.captures[0].target.sha256,report.captures[1].target.sha256,'Actual consumed rider is unchanged');
 report.status='NORMAL_GARAGE_UNCHANGED_RIDER_CAPTURED';
}finally{await browser.close();fs.writeFileSync(path.join(out,'capture.json'),JSON.stringify(report,null,2)+'\n');}
console.log(JSON.stringify({status:report.status,frames:144,riderSHA256:report.captures[0]?.target.sha256}));
