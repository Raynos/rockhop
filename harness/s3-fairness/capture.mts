/** Silent, played landscape captures of the lower Rookie and upper Pro shelf lines. */
import fs from 'node:fs';
import path from 'node:path';
import { captureClip, describeCamera } from '../capture';
import { tickAtX } from '../clip';
import { loadRecording } from '../lib/recording';

const outDir=path.resolve('docs/evidence/s3-fairness');
const cases=[
  {name:'rookie-lower',file:path.join(outDir,'s3-whiteout-rookie-lower.rec.json')},
  {name:'pro-upper',file:path.resolve('harness/inputs/s3-whiteout/bot-3-pro.json')},
];
const rows=[];
for(const c of cases){
  const recording=loadRecording(c.file);
  const start=await tickAtX(recording,125),end=await tickAtX(recording,158);
  if(start===null||end===null)throw new Error(`${c.name} misses shelf window`);
  const result=await captureClip({recording,outMp4:path.join(outDir,`${c.name}.mp4`),
    fps:30,width:852,height:393,quality:'low',startTick:Math.max(0,start-60),endTick:end+60,
    dev:true,cameraCheck:true});
  const sheet=path.join(outDir,`${c.name}-sheet.jpg`);
  fs.copyFileSync(result.sheet,sheet);
  if(result.sheet!==sheet)fs.unlinkSync(result.sheet);
  rows.push({name:c.name,file:c.file,mp4:result.mp4,sheet,frames:result.frames,camera:describeCamera(result.camera)});
}
fs.writeFileSync(path.join(outDir,'played-clips.json'),JSON.stringify(rows,null,2)+'\n');
console.log(JSON.stringify(rows,null,2));
