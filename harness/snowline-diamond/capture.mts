/** Played, silent landscape windows around the authored optional Snowline shelves. */
import fs from 'node:fs';
import path from 'node:path';
import { captureClip, describeCamera } from '../capture';
import { tickAtX } from '../clip';
import { loadRecording } from '../lib/recording';

const id=process.argv[2]==='S3'?'s3-whiteout':'s1-lift-line';
const xs=id==='s1-lift-line'?[262,307]:[125,158];
const outDir=path.resolve('docs/evidence/snowline-diamond');
const rows=[];
for(const bike of ['rookie','pro'].filter(b=>!process.argv[3]||process.argv[3]===b)){
  const file=path.join(outDir,`${id}-${bike}.rec.json`);
  const recording=loadRecording(file);
  const start=await tickAtX(recording,xs[0]!);
  const end=await tickAtX(recording,xs[1]!);
  if(start===null||end===null)throw new Error(`${bike} misses x window`);
  const startTick=Math.max(0,start-60),endTick=end+60;
  const name=`${id}-${bike}`;
  const result=await captureClip({recording,outMp4:path.join(outDir,`${name}.mp4`),fps:30,width:852,height:393,
    quality:'low',startTick,endTick,dev:true,cameraCheck:true});
  const sheet=path.join(outDir,`${name}-sheet.jpg`);
  fs.copyFileSync(result.sheet,sheet);
  if(result.sheet!==sheet)fs.unlinkSync(result.sheet);
  rows.push({name,file,startTick,endTick,frames:result.frames,camera:describeCamera(result.camera),mp4:result.mp4,sheet});
  console.log(`${name}: ${result.frames} frames, ${describeCamera(result.camera)}`);
}
fs.writeFileSync(path.join(outDir,`${id}-played-clips.json`),`${JSON.stringify(rows,null,2)}\n`);
