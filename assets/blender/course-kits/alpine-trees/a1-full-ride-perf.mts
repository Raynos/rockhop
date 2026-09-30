/** Parent-run matched A1 perf recipe. No build; freezes the existing dist for this run. */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { launchBrowser } from '../../../../harness/lib/browser';
import { HookClient, openGame, readHeap } from '../../../../harness/lib/hook';
import { startServer, distIsStale } from '../../../../harness/lib/server';
import { decodeJSON, expandFrames } from '../../../../src/core/replay';
import { percentile } from '../../../../harness/lib/report';
import { frozenSource } from './frozen-source.mts';

const output = process.argv[2];
if (!output) throw new Error('usage: pnpm exec tsx assets/blender/course-kits/alpine-trees/a1-full-ride-perf.mts <output.json> [low|medium|high]');
const tier = process.argv[3] ?? 'low';
if (tier !== 'low' && tier !== 'medium' && tier !== 'high') throw new Error('unknown tier');
const frozenURL=process.env.A1_CAPTURE_URL,frozenSHA=process.env.A1_CAPTURE_SHA,frozenIndex=process.env.A1_CAPTURE_INDEX_SHA;
if(frozenURL&&!frozenSHA) throw new Error('Frozen URL perf requires A1_CAPTURE_SHA');
if(!frozenURL&&distIsStale().stale) throw new Error('Existing dist is stale or missing; parent must build/freeze before capturing. This recipe never builds.');
const source=frozenURL ? await frozenSource(frozenURL,frozenSHA!,frozenIndex) : {kind:'frozen-local-dist'};
const input = 'harness/inputs/a1-sawdust/bot-3.json';
const inputBytes = readFileSync(input);
const recording = decodeJSON(inputBytes.toString());
const frames = expandFrames(recording);
const fps = 20, width = 852, height = 392, tpf = recording.header.physicsHz / fps;
if (!Number.isInteger(tpf)) throw new Error('Recording Hz must divide selected fps');
const server = frozenURL ? null : await startServer({ forceBuild: false, freeze: true });
const browser = await launchBrowser({ width, height });
try {
  const errors:string[]=[];browser.page.on('pageerror',error=>errors.push(error.message));
  await openGame(browser.page, frozenURL ?? server!.url);
  const hook = new HookClient(browser.page);
  if (!(await hook.loadTrack(recording.header.trackId, recording.header.seed))) throw new Error('Track load failed');
  await hook.resize(width, height); await hook.setQuality(tier);
  await browser.page.waitForFunction(()=>window.__rockhop!.info().render.entering===false,undefined,{timeout:30000});
  const entry=await browser.page.evaluate(()=>window.__rockhop!.info().render);
  const mount=entry as {courseAssetsEnabled?:boolean;courseAssetsMounted?:number};
  if(process.env.A1_EXPECT_MOUNT==='1'&&(mount.courseAssetsEnabled!==true||mount.courseAssetsMounted!==1)) {
    throw new Error(`A1 perf startup mount failed: ${JSON.stringify(entry)}`);
  }
  for (let i=0;i<5;i++) await hook.render();
  const heapBefore = await readHeap(browser.page);
  const samples = [];
  for (let tick=0;tick<frames.length;tick+=tpf) {
    const batch=frames.slice(tick,tick+tpf);
    const timing = await browser.page.evaluate(inputs=>{
      const h=window.__rockhop!;
      const start=performance.now();
      for(const input of inputs) { h.setInput(input);h.step(1); }
      const physicsMs=performance.now()-start;
      const submitMs=h.render(false),syncedMs=h.render(true);
      const state=h.getState();
      return {tick:state.tick,x:state.bike.pos.x,physicsMs,submitMs,syncedMs,camera:h.camera(),phase:h.phase()};
    },batch);
    samples.push({...timing,...await hook.stats()});
  }
  const heapAfter=await readHeap(browser.page),state=await hook.getState();
  const summary=(field: keyof typeof samples[number])=>{
    const values=samples.map(s=>Number(s[field])).sort((a,b)=>a-b);
    return {p50:percentile(values,50),p95:percentile(values,95),max:values.at(-1)};
  };
  const report={
    candidate:true,source,entry,afterSource:frozenURL?await frozenSource(frozenURL,frozenSHA!,frozenIndex):null,errors,
    backend:process.env.TRIALS_BROWSER_BACKEND??'swiftshader',
    camera:{frames:samples.length,outOfBoxRiding:samples.filter(s=>s.phase==='riding'&&(s.camera.bikeScreenX<.2||s.camera.bikeScreenX>.8||s.camera.bikeScreenY<.2||s.camera.bikeScreenY>.8)).length,maxAbsRoll:Math.max(...samples.map(s=>Math.abs(s.camera.roll??0)))},
    input,inputSHA256:createHash('sha256').update(inputBytes).digest('hex'),config:{tier,fps,width,height,physicsHz:recording.header.physicsHz,ticksPerFrame:tpf},
    webgl:browser.probe,summary:{calls:summary('calls'),triangles:summary('triangles'),submitMs:summary('submitMs'),syncedMs:summary('syncedMs'),physicsMs:summary('physicsMs')},
    finalHash:await hook.hashState(),finishTime:state.finishTime,finalTick:state.tick,
    heap:{before:heapBefore.jsHeapUsed,after:heapAfter.jsHeapUsed,growth:heapAfter.jsHeapUsed-heapBefore.jsHeapUsed},samples,
  };
  mkdirSync(dirname(output),{recursive:true});writeFileSync(output,JSON.stringify(report,null,2)+'\n');
  if(errors.length) process.exitCode=1;
  console.log(JSON.stringify({output,summary:report.summary,finalHash:report.finalHash,finishTime:report.finishTime}));
} finally { await browser.close();await server?.close(); }
