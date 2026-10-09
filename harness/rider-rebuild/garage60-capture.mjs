/** Parent-guarded, silent Metal Garage surface film. No loading/menu frames,
 * Playwright25fps recorder, screenshot sequence, fake clock or asset replacement.
 * Run with pnpm exec tsx (existing browser helper is TypeScript).
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { pathToFileURL,fileURLToPath } from 'node:url';
import { installGarage60Recorder } from './garage60-recorder.mjs';
import { installGarageCaptureMeter } from './garage-capture-meter.mjs';
import { cadence,decodeProof,comparePresentation,parseFrameHashes,requestCoverage } from './garage60-proof.mjs';
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
export const filePin=file=> {
  const resolved=path.resolve(file instanceof URL?fileURLToPath(file):file);
  return {path:resolved,sha256:sha(fs.readFileSync(resolved))};
};
const pin=filePin;
function run(binary,args) {
  const result=spawnSync(binary,args,{encoding:'utf8',maxBuffer:32*1024*1024});
  assert.equal(result.status,0,`${binary}: ${result.stderr}`);return result.stdout;
}
export function probeMovie(file) {
  const probe=JSON.parse(run('ffprobe',['-v','error','-show_streams','-show_frames',
    '-show_entries','stream=codec_type,codec_name,pix_fmt,width,height,avg_frame_rate:frame=media_type,best_effort_timestamp_time',
    '-of','json',file]));
  const hashes=parseFrameHashes(run('ffmpeg',['-v','error','-threads','2','-i',file,'-map','0:v:0',
    '-an','-vf','format=yuv420p','-fps_mode','passthrough','-threads','2','-f','framemd5','-']));
  return {proof:decodeProof(probe,hashes),hashes};
}
export async function main(argv=process.argv.slice(2)) {
  const arg=(name,fallback='')=>argv.find(value=>value.startsWith(`--${name}=`))?.slice(name.length+3)??fallback;
  assert.equal(process.env.TRIALS_BROWSER_BACKEND,'metal','Explicit guarded Metal required; no software fallback');
  const build=arg('build'),source=arg('dev-source'),contractPath=path.resolve(arg('contract'));
  assert(!!build!==!!source,'Choose --build or --dev-source');assert(arg('contract')&&arg('out'));
  const seconds=Number(arg('seconds','18')),bike=arg('bike','rookie');
  assert(seconds>=16&&seconds<=60&&Number.isFinite(seconds));assert(['rookie','pro'].includes(bike));
  const out=path.resolve(arg('out'));assert(!fs.existsSync(out),'Fresh output required');fs.mkdirSync(out,{recursive:true});
  const contract=JSON.parse(fs.readFileSync(contractPath)),expected=contract.specification.meshNames;
  for(const name of ['RiderBody','RiderHoodie','RiderJeans','ActualSelectedGlove.L','ActualSelectedGlove.R','ActualSelectedBoot.L','ActualSelectedBoot.R'])
    assert(Object.values(expected).includes(name),`Selected full outfit required: ${name}`);
  const clip=arg('clip',source?contract.previewClip??'':'');
  const garageSource=fs.readFileSync('src/ui/garage.ts'),sensitivity=garageSource.toString().match(/yawPerPx:\s*\(2 \* Math.PI\) \/ ([\d.]+)/);
  assert(sensitivity);const fullTurnPixels=Number(sensitivity[1]);assert(fullTurnPixels>0&&fullTurnPixels<900);
  const report={status:'UNACCEPTED_GARAGE60_CAPTURE_PENDING',acceptedArt:false,ask:345,requestedFPS:60,
    contract:pin(contractPath),recipe:pin(new URL(import.meta.url)),recorder:pin(new URL('./garage60-recorder.mjs',import.meta.url)),
    meter:pin(new URL('./garage-capture-meter.mjs',import.meta.url)),proofRecipe:pin(new URL('./garage60-proof.mjs',import.meta.url)),
    pointerSensitivitySHA256:sha(garageSource),bike,clip:clip||null,errors:[],requests:[],
    audio:'webdriver;audio=0;mute-audio;video-only stream',
    limits:['Canvas surface and measured HUD only; DOM Garage controls are outside film.',
      'Render submissions and RAF are not GPU completion or encoded FPS.',
      'Headless desktop Metal capture is not physical iPhone acceptance or finished rider art.']};
  let server,launched,page,development;
  try {
    const {createPrivateDevReview}=await import('./private-dev-review.mjs');
    const {preview}=await import('vite');
    if(source) development=await createPrivateDevReview({source,contractPath,
      allowFailedDiagnostic:argv.includes('--allow-failed-diagnostic'),clip});
    const catalog=development?.catalog??JSON.parse(fs.readFileSync(path.join(build,'model-catalog.json')));
    const inputs=development?null:JSON.parse(fs.readFileSync(path.join(build,'rider-rebuild-inputs.json')));
    if(inputs) {assert.equal(inputs.releaseBuild,false);assert.equal(inputs.sourceSHA256,contract.glbSHA256);
      assert.equal(inputs.metadataSHA256,report.contract.sha256);}
    const outfit=inputs?.comparison?.id??'street-mustard';
    const selected=catalog.models.find(row=>row.logical===`models/rider-${outfit}.glb`);
    const selectedBike=catalog.models.find(row=>row.logical===`models/bike-${bike}.glb`);
    assert.equal(selected?.sha256,contract.glbSHA256);assert(selectedBike);
    report.selectedAsset=selected;report.bikeAsset=selectedBike;report.development=development?.receipt??null;
    server=development?.server??await preview({configFile:false,root:process.cwd(),build:{outDir:path.resolve(build)},
      preview:{host:'127.0.0.1',port:0},logLevel:'warn'});
    const {launchBrowser}=await import('../lib/browser.ts');
    launched=await launchBrowser({width:1280,height:720});page=launched.page;
    report.backend={flagSet:launched.flagSet,probe:launched.probe};
    report.webdriver=await page.evaluate(()=>navigator.webdriver);assert.equal(report.webdriver,true);
    assert(/Metal/.test(launched.probe.renderer));
    await launched.context.addInitScript(()=> {
      localStorage.setItem('rockhop.onboarded','1');
      localStorage.setItem('rockhop.economy.v1',JSON.stringify({version:1,wallet:0,medals:{},proOwned:true,equipped:'rookie'}));
    });
    page.on('pageerror',error=>report.errors.push(error.message));
    const responses=[];
    page.on('response',response=> {
      if(new URL(response.url()).pathname.endsWith('.glb')) responses.push((async()=> {
        const row=catalog.models.find(asset=>new URL(asset.url,server.resolvedUrls.local[0]).href===response.url());
        report.requests.push({status:response.status(),url:response.url(),catalogSHA256:row?.sha256??null,
          contentLength:Number((await response.allHeaders())['content-length']??0)});
      })().catch(error=>report.errors.push(error.message)));
    });
    const query=new URLSearchParams({audio:'0',sw:'0'});if(clip)query.set('riderClip',clip);
    await page.goto(server.resolvedUrls.local[0]+'?'+query);
    await page.locator('.menu-screen.live .menu-item[data-id=garage]').click({timeout:120000});
    await page.waitForSelector('.garage-screen.live');
    await page.locator(`button[data-bike=${bike}]`).click();
    await page.locator(`button[data-outfit=${outfit}]`).click();
    await page.evaluate(async()=>globalThis.window.__render.whenReady());
    const inspect=()=>page.evaluate(()=> {
      const owner=globalThis.window.__render,rider=owner.debug.rider;
      return {garage:owner.debugInfo().garage,candidate:structuredClone(rider.debug.candidate),stageTime:owner.stageTime,
        stageClip:rider.debug.stageClip??null,jointIds:[...rider.binding.byId.keys()].sort((a, b) => a < b ? -1 : a > b ? 1 : 0),camera:owner.camera()};
    });
    const validate=value=> {
      assert(value.garage.on);assert.equal(value.candidate.sourceSHA256,contract.glbSHA256);
      assert.deepEqual(value.candidate.authorMeshRoles,expected);
      const visible=new Set(value.candidate.visibleMeshes.filter(row=>row.skinned&&row.triangles>0).map(row=>row.name));
      for(const name of Object.values(expected))assert(visible.has(name),`Missing actual selected outfit part: ${name}`);
      assert.deepEqual(value.jointIds,Object.keys(contract.specification.jointNames).sort((a, b) => a < b ? -1 : a > b ? 1 : 0));assert.equal(value.jointIds.length,75);
      if(clip)assert.equal(value.stageClip,clip);
    };
    report.before=await inspect();validate(report.before);
    report.frameMeter=await page.evaluate(installGarageCaptureMeter);
    report.recorderSupport=await page.evaluate(installGarage60Recorder,{fps:60,bitrate:16000000,expectedSourceSHA256:contract.glbSHA256});
    await page.waitForTimeout(1500); // Unrecorded shader/counter warmup, no film prefix.
    const box=await page.locator('.garage-stage').boundingBox();assert(box);
    const center={x:box.x+box.width*.72,y:box.y+box.height*.45};
    await page.mouse.move(center.x,center.y);await page.mouse.down();
    await page.evaluate(()=> {globalThis.window.__garageCaptureMeter.reset();globalThis.window.__garage60Recorder.arm();});
    await page.waitForFunction(()=>globalThis.window.__garage60Recorder.started(),null,{timeout:10000});
    const start=performance.now();let fraction=0,moves=0,maxStepPx=0;
    while(fraction<1) {
      const previous=fraction;fraction=Math.min(1,(performance.now()-start)/(seconds*1000));
      await page.mouse.move(center.x-fullTurnPixels*fraction,center.y);
      moves++;maxStepPx=Math.max(maxStepPx,(fraction-previous)*fullTurnPixels);
      if(fraction<1)await page.waitForTimeout(8);
    }
    await page.waitForTimeout(100);await page.mouse.up(); // No inherited release inertia.
    report.orbit={requestedSeconds:seconds,actualSeconds:(performance.now()-start)/1000,moves,maxStepPx,
      fullTurnPixels,pointerDegrees:360,driver:'One continuous real held mouse through actual Garage handlers; no camera injection'};
    report.capture=await page.evaluate(()=>globalThis.window.__garage60Recorder.finish());
    report.actualFramePerformance=await page.evaluate(()=>globalThis.window.__garageCaptureMeter.stop());
    report.after=await inspect();validate(report.after);assert(report.after.stageTime>report.before.stageTime);
    await Promise.all(responses);assert.deepEqual(report.errors,[]);
    for(const asset of [selected,selectedBike])assert(report.requests.some(row=>row.status===200&&row.catalogSHA256===asset.sha256));
    const raw=path.join(out,report.capture.mimeType.startsWith('video/mp4')?'garage-canvas-raw.mp4':'garage-canvas-raw.webm');
    for(let index=0;index<report.capture.chunkCount;index++) {
      const bytes=await page.evaluate(index=>globalThis.window.__garage60Recorder.chunk(index),index);
      fs.appendFileSync(raw,Buffer.from(bytes,'base64'));
    }
    assert.equal(fs.statSync(raw).size,report.capture.totalBytes);report.raw=pin(raw);
    await launched.close();launched=null;
    const destination=path.join(out,'garage-rotation.mp4');
    if(report.capture.mimeType.startsWith('video/mp4')) fs.copyFileSync(raw,destination);
    else run('ffmpeg',['-v','error','-y','-threads','2','-i',raw,'-map','0:v:0','-an','-c:v','libx264',
      '-threads','2','-crf','0','-pix_fmt','yuv420p','-fps_mode','passthrough','-movflags','+faststart',destination]);
    const decoded=probeMovie(raw),encoded=probeMovie(destination);
    report.presentationParity=comparePresentation(decoded.proof,encoded.proof,decoded.hashes,encoded.hashes);
    report.sourceVideo=decoded.proof;report.presentationVideo=encoded.proof;report.movie=pin(destination);
    report.actualRenderCadence=cadence(report.capture.actualRenderTimesMs,.001);
    report.actualRafCadence=cadence(report.capture.actualRafTimesMs,.001);
    report.captureRequestCadence=cadence(report.capture.captureRequestTimesMs,.001);
    report.requestCoverage=requestCoverage(encoded.proof,report.capture.captureRequestTimesMs);
    assert(decoded.proof.distinctFraction>=.9,'Decoded film lacks changing real surfaces; inspect for frozen/blank recording');
    const observed60=encoded.proof.nominal60CadenceObserved&&report.requestCoverage.completeRequestSpanObserved;
    report.status=observed60?'UNACCEPTED_REAL_GARAGE_NOMINAL60_CAPTURE_PARENT_PLAYBACK_PENDING':'UNACCEPTED_REAL_GARAGE_CAPTURE_BELOW60_PARENT_REVIEW';
    if(!observed60)process.exitCode=1;
  } catch(error) {report.failure=error.stack;process.exitCode=1;}
  finally {
    if(page)await page.evaluate(()=> {globalThis.window.__garage60Recorder?.dispose();globalThis.window.__garageCaptureMeter?.stop();}).catch(()=>{});
    await launched?.close();
    if(development)await server?.close();else if(server)await new Promise(resolve=>server.httpServer.close(resolve));
    fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({out,status:report.status,recordedFPS:report.presentationVideo?.observedFPS??null,failure:report.failure??null}));
  }
}
if(process.argv[1]&&pathToFileURL(path.resolve(process.argv[1])).href===import.meta.url)await main();
