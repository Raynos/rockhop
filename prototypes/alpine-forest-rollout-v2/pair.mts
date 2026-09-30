/** Parent review delivery: validate matched raw captures, then encode before-left / after-right. */
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { resolveFfmpeg, probeVideo } from '../../harness/lib/ffmpeg';
const root=path.resolve(process.argv[2]??'prototypes/alpine-forest-rollout-v2/out/pair');
const hash=(file:string)=>createHash('sha256').update(readFileSync(file)).digest('hex');
for(const name of ['a2-full','a2-log','a3-full','a3-beam','a3-fault']) {
  const before=JSON.parse(readFileSync(path.join(root,'before',name,'capture.json'),'utf8'));
  const after=JSON.parse(readFileSync(path.join(root,'after',name,'capture.json'),'utf8'));
  for(const key of ['inputSha256','frames','finalHash','finishTime','quality','backend']) {
    if(JSON.stringify(before[key])!==JSON.stringify(after[key])) throw new Error(`${name}: mismatch ${key}`);
  }
  if(JSON.stringify(before.window)!==JSON.stringify(after.window)||!before.camera?.pass||!after.camera?.pass) throw new Error(`${name}: unmatched window/camera`);
  if(before.clipSha256!==hash(before.mp4)||after.clipSha256!==hash(after.mp4)) throw new Error(`${name}: raw clip bytes changed`);
  const output=path.join(root,`${name}-compare.mp4`);
  execFileSync(resolveFfmpeg(),['-y','-hide_banner','-loglevel','error','-i',before.mp4,'-i',after.mp4,
    '-filter_complex','[0:v]setsar=1[l];[1:v]setsar=1[r];[l][r]hstack=inputs=2[v]',
    '-map','[v]','-an','-c:v','libx264','-preset','fast','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',output]);
  const metadata={name,left:'before',right:'after',input:before.input,inputSha256:before.inputSha256,
    window:before.window,frames:before.frames,finalHash:before.finalHash,finishTime:before.finishTime,
    quality:before.quality,backend:before.backend,camera:{before:before.camera,after:after.camera},
    beforeSource:before.source,afterSource:after.source,beforeEntry:before.entry,afterEntry:after.entry,
    rawClipSHA256:{before:before.clipSha256,after:after.clipSha256},output,outputSHA256:hash(output),probe:await probeVideo(output),
    dirtyTreeConfounder:'Both phases use the same frozen full source/public snapshot; only the recorded biomeKit forest hook differs. Quarry paint changes are included identically and pinned in the manifest. No timing qualification or physical-device acceptance.'};
  writeFileSync(output.replace('.mp4','.json'),JSON.stringify(metadata,null,2)+'\n');
  console.log(output,metadata.outputSHA256);
}
