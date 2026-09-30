/** Parent-run full C1 perf from immutable private output. No build or shared dist replacement. */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import path, { dirname } from 'node:path';
import { preview } from 'vite';
import { loadavg } from 'node:os';
import { createHash } from 'node:crypto';
import { launchBrowser } from '../../../../harness/lib/browser';
import { HookClient, openGame, readHeap } from '../../../../harness/lib/hook';
import { decodeJSON, expandFrames } from '../../../../src/core/replay';
import { percentile } from '../../../../harness/lib/report';
import { frozenSource } from '../../../../assets/blender/course-kits/alpine-trees/frozen-source.mts';

const [distDir,output,tier='low'] = process.argv.slice(2);
if(!distDir||!output||process.env.TRIALS_BROWSER_BACKEND!=='metal')throw Error('Require Metal and <frozen-dist> <output.json> [low|medium|high]');
if(tier!=='low'&&tier!=='medium'&&tier!=='high')throw Error('Unknown tier');
const frozenSHA=JSON.parse(readFileSync(path.join(distDir,'version.json'),'utf8')).sha as string;
const entryPath=readFileSync(path.join(distDir,'index.html'),'utf8').match(/data-entry="([^"]+)"/)![1]!;
const frozenIndex=createHash('sha256').update(readFileSync(path.join(distDir,entryPath))).digest('hex');
const previewServer=await preview({root:process.cwd(),configFile:path.resolve('vite.config.ts'),logLevel:'warn',build:{outDir:path.resolve(distDir)},preview:{host:'127.0.0.1',port:0}});
const frozenURL=previewServer.resolvedUrls!.local[0]!;
const source=await frozenSource(frozenURL,frozenSHA,frozenIndex);
const hostBefore=loadavg();
const input = 'harness/inputs/c1-low-tide/bot-3.json';
const inputBytes = readFileSync(input);
const recording = decodeJSON(inputBytes.toString());
const frames = expandFrames(recording);
const fps = 20, width = 852, height = 392, tpf = recording.header.physicsHz / fps;
if (!Number.isInteger(tpf)) throw new Error('Recording Hz must divide selected fps');
const browser = await launchBrowser({ width, height });
try {
  const errors:string[]=[];browser.page.on('pageerror',error=>errors.push(error.message));
  await openGame(browser.page, frozenURL);
  const hook = new HookClient(browser.page);
  await hook.setQuality(tier);
  if (!(await hook.loadTrack(recording.header.trackId, recording.header.seed))) throw new Error('Track load failed');
  await hook.resize(width, height); await hook.setQuality(tier);
  await browser.page.waitForFunction(()=>window.__rockhop!.info().render.entering===false,undefined,{timeout:30000});
  const entry=await browser.page.evaluate(()=>window.__rockhop!.info().render);
  const mount=entry as {courseAssetsEnabled?:boolean;courseAssetsMounted?:number};
  if(process.env.COAST_EXPECT_MOUNT&&(mount.courseAssetsEnabled!==true||mount.courseAssetsMounted!==Number(process.env.COAST_EXPECT_MOUNT))) {
    throw new Error(`Coast perf startup mount failed: ${JSON.stringify(entry)}`);
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
    candidate:true,source,entry,afterSource:await frozenSource(frozenURL,frozenSHA,frozenIndex),errors,host:{loadBefore:hostBefore,loadAfter:loadavg(),limits:'Shared host run; physical-phone and isolated timing attribution not established.'},
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
} finally { await browser.close();await new Promise<void>((resolve,reject)=>previewServer.httpServer.close(error=>error?reject(error):resolve())); }
