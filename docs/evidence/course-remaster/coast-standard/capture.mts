/** Full played Coast comparison from one frozen output per phase; silent Metal only. */
import { preview } from 'vite';
import { createHash } from 'node:crypto';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { captureClip } from '../../../../harness/capture';
import { HookClient } from '../../../../harness/lib/hook';
import { loadRecording } from '../../../../harness/lib/recording';
import { frozenSource } from '../../../../assets/blender/course-kits/alpine-trees/frozen-source.mts';
const [distDir, outDir] = process.argv.slice(2);
if (!distDir || !outDir || process.env.TRIALS_BROWSER_BACKEND !== 'metal') throw Error('Metal capture requires <frozen-dist> <out-dir>');
const version = JSON.parse(readFileSync(path.join(distDir, 'version.json'),'utf8')) as {sha:string};
const html=readFileSync(path.join(distDir,'index.html'),'utf8');
const entry=html.match(/data-entry="([^"]+)"/)![1]!;
const digest=(data:Buffer)=>createHash('sha256').update(data).digest('hex');
const indexSHA=digest(readFileSync(path.join(distDir,entry)));
const server=await preview({root:process.cwd(),configFile:path.resolve('vite.config.ts'),logLevel:'warn',build:{outDir:path.resolve(distDir)},preview:{host:'127.0.0.1',port:0}});
const url=server.resolvedUrls!.local[0]!;
const original=HookClient.prototype.loadTrack;
HookClient.prototype.loadTrack=async function(id,seed) {
 const ok=await original.call(this,id,seed);
 if(ok) await this.page.waitForFunction(()=>window.__rockhop!.info().render.entering===false,undefined,{timeout:30000});
 return ok;
};
try {
 for(const c of [
  {name:'full',file:'harness/inputs/c1-low-tide/bot-3.json',start:0,end:undefined,fps:12},
  {name:'deck-fault',file:'docs/evidence/c1-crash-feedback/held-go.json',start:2040,end:2460,fps:20},
 ]) {
  const dest=path.join(outDir,c.name);mkdirSync(dest,{recursive:true});
  const source=await frozenSource(url,version.sha,indexSHA);
  const result=await captureClip({recording:loadRecording(c.file),outMp4:path.join(dest,'clip.mp4'),fps:c.fps,width:852,height:392,quality:'low',tailSeconds:0,startTick:c.start,...(c.end===undefined?{}:{endTick:c.end}),url,expectSha:version.sha,cameraCheck:true});
  const afterSource=await frozenSource(url,version.sha,indexSHA);
  writeFileSync(path.join(dest,'capture.json'),JSON.stringify({source,afterSource,input:c.file,inputSHA256:digest(readFileSync(c.file)),backend:'Metal',...result},null,2)+'\n');
  if(!result.camera?.pass)throw Error('camera bounds failed');
  console.log(c.name,result.frames,result.finishTime,result.finalHash);
 }
} finally { await new Promise<void>((resolve,reject)=>server.httpServer.close(err=>err?reject(err):resolve())); }
