/** Matched A2/A3 full/log/beam/fault against supplied immutable URL and SHA, never local dist. */
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { captureClip } from '../../harness/capture';
import { loadRecording } from '../../harness/lib/recording';
import { frozenSource } from '../../assets/blender/course-kits/alpine-trees/frozen-source.mts';
import { HookClient, openGame } from '../../harness/lib/hook';
import {launchBrowser} from '../../harness/lib/browser';
import {createSimFor} from '../../harness/lib/sim';
import {expandFrames} from '../../src/core/replay';
const cases = [
 {name:'d3-pro-cart',input:'docs/evidence/course-remaster/pro-envelope/d3-pro-upper.replay.json',inputSHA:'3af4447ea36f6914f97ad1bcf93cc2ce88956fa4467f3ef855325571f359d50c',fps:20,start:940,end:1380},
 {name:'d3-pro-fault',input:'prototypes/d3-pro-landing-lesson-v1/d3-held-go-retry.json',inputSHA:'13e54fe51679d8b7c5ced844079f3ec591dc1db1ed9a50fb19f29e8e5cf7b1f0',fps:20,start:1000,end:undefined},
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
  if(onlyCase==='d3-pro-cart') {
    const recording=loadRecording(cases[0].input);const sim=await createSimFor(recording);sim.run(expandFrames(recording));
    const browser=await launchBrowser({width:852,height:392});
    try {
      const page=browser.page;await openGame(page,url);
      const client=new HookClient(page);const replay=await client.runRecording(readFileSync(cases[0].input,'utf8'));
      const node={hash:sim.hash(),time:sim.runTime(),faults:sim.faults(),phase:sim.phase()};
      const match=replay.hash===node.hash&&replay.runTime===node.time&&replay.faults===node.faults;
      writeFileSync(path.join(path.resolve(outRoot),'full-replay.json'),JSON.stringify({source,node,browser:replay,match},null,2)+'\n');
      if(!match)throw new Error('Full Node/browser replay differs');console.log('full-replay',node);
    } finally {await browser.close();}
  }
}
