/** Matched A2/A3 full/log/beam/fault against supplied immutable URL and SHA, never local dist. */
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { captureClip } from '../../harness/capture';
import { loadRecording } from '../../harness/lib/recording';
import { frozenSource } from '../../assets/blender/course-kits/alpine-trees/frozen-source.mts';
import { HookClient } from '../../harness/lib/hook';
const cases = [
  {
    "name": "a2-full",
    "input": "harness/inputs/a2-log-jam/bot-3.json",
    "inputSHA": "8ff1785f871b040e130b873b35274030599f7b7b4f40bfab62f56253c5fc8633",
    "fps": 12,
    "start": 0,
    "end": undefined
  },
  {
    "name": "a2-log",
    "input": "harness/inputs/a2-log-jam/bot-3.json",
    "inputSHA": "8ff1785f871b040e130b873b35274030599f7b7b4f40bfab62f56253c5fc8633",
    "fps": 20,
    "start": 2646,
    "end": 3252
  },
  {
    "name": "a3-full",
    "input": "harness/inputs/a3-timberline/bot-3.json",
    "inputSHA": "ed5af2eaf96b2c277e5168581d74243984f3c9a7784b2b6116ecbd2b474cc6cf",
    "fps": 12,
    "start": 0,
    "end": undefined
  },
  {
    "name": "a3-beam",
    "input": "harness/inputs/a3-timberline/bot-3.json",
    "inputSHA": "ed5af2eaf96b2c277e5168581d74243984f3c9a7784b2b6116ecbd2b474cc6cf",
    "fps": 20,
    "start": 1644,
    "end": 2232
  },
  {
    "name": "a3-fault",
    "input": "harness/inputs/a3-timberline/stranger-a3-timberline-20260929-010154.json",
    "inputSHA": "94ded7d25bfcc99e6ede45c9dbfba77234bb7d169f2f74fe7942978b9cf27bf1",
    "fps": 20,
    "start": 2364,
    "end": 2724
  }
] as const;
const hash=(file:string)=>createHash('sha256').update(readFileSync(file)).digest('hex');
if(process.argv[2]==='--describe') {
  console.log(JSON.stringify({backend:'metal',tier:'low',width:852,height:392,cameraCheck:true,cases},null,2));
} else {
  const [outRoot,onlyCase]=process.argv.slice(2);
  const url=process.env.A1_CAPTURE_URL,sha=process.env.A1_CAPTURE_SHA,indexSHA=process.env.A1_CAPTURE_INDEX_SHA;
  if(!outRoot||!url||!sha||!indexSHA) throw new Error('A1_CAPTURE_URL/SHA/INDEX_SHA required; tsx a1-frozen-capture.mts <out-dir> [full|flume-fault|fault-restart]');
  if(process.env.TRIALS_BROWSER_BACKEND!=='metal') throw new Error('Matched A1 trial requires TRIALS_BROWSER_BACKEND=metal');
  if(onlyCase && !cases.some(c=>c.name===onlyCase)) throw new Error('Unknown case');
  const source=await frozenSource(url,sha,indexSHA);
  const expectMount=process.env.A1_EXPECT_MOUNT==='1';
  let entry: unknown;
  const originalLoad=HookClient.prototype.loadTrack;
  // Adapt only this process's harness entry wait; shared source files remain untouched.
  HookClient.prototype.loadTrack=async function(id,seed) {
    const ok=await originalLoad.call(this,id,seed);
    if(!ok) return false;
    await this.page.waitForFunction(()=>window.__rockhop!.info().render.entering===false,undefined,{timeout:30000});
    entry=await this.page.evaluate(()=>{
      const gl=(document.querySelector('canvas') as HTMLCanvasElement).getContext('webgl2')!;
      const debug=gl.getExtension('WEBGL_debug_renderer_info');
      return {render:window.__rockhop!.info().render,renderer:String(gl.getParameter(debug?debug.UNMASKED_RENDERER_WEBGL:gl.RENDERER))};
    });
    const check=entry as {render:{courseAssetsEnabled?:boolean;courseAssetsMounted?:number};renderer:string};
    if(!/Metal/.test(check.renderer)) throw new Error(`Capture game renderer is not Metal: ${check.renderer}`);
    if((expectMount&&check.render.courseAssetsEnabled!==true)||check.render.courseAssetsMounted!==(expectMount?1:0)) {
      throw new Error(`A2/A3 startup mount failed: ${JSON.stringify(check.render)}`);
    }
    return true;
  };
  for(const c of cases) {
    if(onlyCase&&c.name!==onlyCase) continue;
    if(hash(c.input)!==c.inputSHA) throw new Error(`${c.name}: matched input bytes changed`);
    const dest=path.join(path.resolve(outRoot),c.name);mkdirSync(dest,{recursive:true});
    const result=await captureClip({recording:loadRecording(c.input),outMp4:path.join(dest,'clip.mp4'),
      fps:c.fps,width:852,height:392,quality:'low',tailSeconds:0,startTick:c.start,
      ...(c.end===undefined?{}:{endTick:c.end}),url,expectSha:sha,cameraCheck:true});
    const afterSource=await frozenSource(url,sha,indexSHA);
    writeFileSync(path.join(dest,'capture.json'),JSON.stringify({input:c.input,inputSha256:c.inputSHA,
      source,afterSource,entry,expectMount,backend:'metal',strictBackendVerifier:'harness/lib/browser.ts',quality:'low',
      viewport:{width:852,height:392},window:[c.start,c.end??null],
      ...result,clipSha256:hash(result.mp4)},null,2)+'\n');
    if(!result.camera?.pass) throw new Error(`${c.name}: camera check failed`);
    console.log(c.name,result.frames,result.seconds,result.finalHash);
  }
}
