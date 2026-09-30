/** Matched A2/A3 full/log/beam/fault against supplied immutable URL and SHA, never local dist. */
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { captureClip } from '../../harness/capture';
import { loadRecording } from '../../harness/lib/recording';
import { frozenSource } from '../../assets/blender/course-kits/alpine-trees/frozen-source.mts';
import { HookClient } from '../../harness/lib/hook';
const cases = [
 {name:'s1-pro-full',input:'docs/evidence/course-remaster/pro-envelope/s1-pro-upper.replay.json',inputSHA:'f71ff5217223c761bd14d406046212638a9c0f3404fe9f0704be332a9fc9c500',fps:12,start:0,end:undefined},
 {name:'s1-pro-approach',input:'docs/evidence/course-remaster/pro-envelope/s1-pro-upper.replay.json',inputSHA:'f71ff5217223c761bd14d406046212638a9c0f3404fe9f0704be332a9fc9c500',fps:20,start:1894,end:2434},
 {name:'s1-pro-fault',input:'prototypes/s1-landing-sightline-v1/s1-held-go-retry.json',inputSHA:'5f65947f0e8243c1bdab0d934d39d4920653749b17852c7e87234f8c2db42747',fps:20,start:1894,end:undefined},
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
