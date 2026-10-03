/** Check the local band after the actual physical-body spawn pose, before solving. */
/* oxlint-disable eslint/no-undef, typescript/no-extraneous-class -- silent headless page. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { preview } from 'vite';
import { webkit } from 'playwright';
const [buildArg,handoffFile,outFile]=process.argv.slice(2);assert(outFile&&!fs.existsSync(outFile));
const build=path.resolve(buildArg),sha=b=>crypto.createHash('sha256').update(b).digest('hex'),handoffBytes=fs.readFileSync(handoffFile),handoff=JSON.parse(handoffBytes);
assert.equal(sha(handoffBytes),'7a3514711c0cc04bb0505ba6deca4de58d2591f9d007e46abe9153d3e2aab60a');
const server=await preview({configFile:false,root:process.cwd(),build:{outDir:build},preview:{host:'127.0.0.1',port:0},logLevel:'warn'}),browser=await webkit.launch({headless:true}),context=await browser.newContext({viewport:{width:960,height:640}});
await context.addInitScript(()=>{localStorage.setItem('rockhop.onboarded','1');window.__agent3AudioCount=0;for(const k of ['AudioContext','webkitAudioContext'])window[k]=class{constructor(){window.__agent3AudioCount++;throw new Error('Silent preflight');}};});
const page=await context.newPage(),report={status:'UNACCEPTED_ACTUAL_SPAWN_PREFLIGHT_PENDING',handoffSHA256:sha(handoffBytes),errors:[]};page.on('pageerror',e=>report.errors.push(e.message));
try{
  await page.goto(server.resolvedUrls.local[0]+'?harness=1&audio=0&sw=0&outfit=street-mustard&physics=v2&hz=120');await page.waitForFunction(()=>window.__rockhop?.ready,null,{timeout:120000});
  report.spawn=await page.evaluate(async handoff=>{
    const t=window.__rockhop,r=window.__render;t.setQuality('high');await r.whenReady();await t.loadTrack('b1-first-ride',0);t.skipCountdown();t.render(true);
    const module=await import('/agent3-cloth/solver.js'),d=r.debug,targets=module.liveSleeveTargets(d,handoff),clearance=module.sleeveClearance(targets.cloth,targets.body,handoff);
    return{actualPhysicalPose:d.rider.debug.physicalPose,stance:d.rider.debug.stance.on,stateHash:t.hashState(),tick:t.getState().tick,
      skinTemplate:targets.skinTemplate,clearance,cloth:targets.cloth.map(p=>p.toArray()),body:targets.body.map(p=>p.toArray()),audioContexts:window.__agent3AudioCount,webdriver:navigator.webdriver};
  },handoff);
  assert(report.spawn.actualPhysicalPose&&report.spawn.stance&&report.spawn.webdriver&&report.spawn.audioContexts===0);assert.deepEqual(report.errors,[]);
  report.pass=report.spawn.clearance.finite&&report.spawn.clearance.minUnsignedM>=.002&&report.spawn.clearance.minLocalNormalM>=.002;
  report.status=report.pass?'UNACCEPTED_ACTUAL_SPAWN_LOCAL_CLEARANCE_PREFLIGHT_PASSED':'STOPPED_BEFORE_SOLVER_ACTUAL_SPAWN_LOCAL_CLEARANCE_FAILED';
  report.limits=['Native rest qualification does not automatically qualify the skinned riding spawn.',
    'Vertex/centroid local face proxies only; complete triangle/self contacts remain unmeasured.',
    'No solver initialized, no simulated/pushed-out rest or pose mutation. This result is a preflight, not moving cloth evidence.'];
}catch(e){report.failure=String(e);process.exitCode=1;}
finally{fs.mkdirSync(path.dirname(outFile),{recursive:true});fs.writeFileSync(outFile,JSON.stringify(report,null,2)+'\n');await context.close();await browser.close();await new Promise(resolve=>server.httpServer.close(resolve));console.log(JSON.stringify({status:report.status,pass:report.pass,clearance:report.spawn?.clearance,failure:report.failure}));}
