/** Parent-run A1 full/fault/restart against supplied immutable URL and SHA, never local dist. */
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { captureClip } from '../../../../harness/capture';
import { loadRecording } from '../../../../harness/lib/recording';
import { frozenSource } from './frozen-source.mts';
import { HookClient } from '../../../../harness/lib/hook';
const cases = [
  {name:'full',input:'harness/inputs/a1-sawdust/bot-3.json',inputSHA:'611795e3f00fb504902d5a5b1ca44490206229144fbaaf0e03ce573316f6ef8f',fps:12,start:0,end:undefined,expectedHash:'397beb1fcd345e2d'},
  {name:'flume-fault',input:'assets/blender/course-kits/alpine-trees/a1-held-go.rec.json',inputSHA:'87acb68ce81eedfe9cb6b97faf226658c412064ad028bd0f82cc01d46f05e71f',fps:20,start:2520,end:3156,expectedHash:'9b8c25c5404681b3'},
  {name:'fault-restart',input:'docs/evidence/alpine-retarget/a1-sawdust-rookie-restart.rec.json',inputSHA:'9cd1baa6ded132ef7f9b797a61f0cb09d693c7786bb279e838235e63bcffdb01',fps:120,start:2910,end:3035,expectedHash:'4b9a060e15075b4a'},
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
    if(expectMount&&(check.render.courseAssetsEnabled!==true||check.render.courseAssetsMounted!==1)) {
      throw new Error(`A1 startup mount failed: ${JSON.stringify(check.render)}`);
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
      viewport:{width:852,height:392},window:[c.start,c.end??null],expectedHash:c.expectedHash,
      ...result,clipSha256:hash(result.mp4)},null,2)+'\n');
    if(!result.camera?.pass) throw new Error(`${c.name}: camera check failed`);
    if(result.finalHash!==c.expectedHash) throw new Error(`${c.name}: physics tail ${result.finalHash} != ${c.expectedHash}`);
    console.log(c.name,result.frames,result.seconds,result.finalHash);
  }
}
