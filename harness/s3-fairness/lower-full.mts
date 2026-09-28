/** Continue promising lower window controls through the entire source recording. */
import fs from 'node:fs';
import { decodeJSON, expandFrames, quantizeInput, InputRecorder, encodeJSON } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';
import { recordingHeader } from '../lib/recording';

const source = decodeJSON(fs.readFileSync('docs/evidence/snowline-diamond/s3-whiteout-rookie.rec.json','utf8'));
const frames = expandFrames(source);
const sweep = JSON.parse(fs.readFileSync('docs/evidence/s3-fairness/lower-sweep.json','utf8'));
const candidates = sweep.top.filter((r: {alive:boolean,maxBikeY:number,frontContacts:number}) =>
  r.alive && r.maxBikeY < 3 && r.frontContacts === 0);
const sim = await createSimFor(source);
const parse = (name:string) => {
  if(name==='source') return null;
  const m=name.match(/^t(0|0\.5|1)l(-1|0|1)$/);
  if(!m)throw new Error(name);
  return quantizeInput({throttle:Number(m[1]),lean:Number(m[2])});
};
const rows=[];
for(const c of candidates){
  sim.reload();
  const rec=new InputRecorder(recordingHeader(sim,'s3 rookie lower visual trial'));
  let maxBikeY=-Infinity,maxFrontY=-Infinity;
  for(const f of frames){
    if(sim.phase()==='finished')break;
    const x=sim.state().bike.pos.x;
    const input=x<112?f:x<125?(parse(c.pre)??f):x<132?(parse(c.launch)??f):
      x<152?(parse(c.flight)??f):f;
    sim.step(input);rec.push(input);
    const s=sim.state();
    if(s.wheels.front.pos.x>=144&&s.wheels.front.pos.x<=152){
      maxBikeY=Math.max(maxBikeY,s.bike.pos.y);
      maxFrontY=Math.max(maxFrontY,s.wheels.front.pos.y);
    }
  }
  const row={pre:c.pre,launch:c.launch,flight:c.flight,phase:sim.phase(),faults:sim.faults(),
    finishS:sim.phase()==='finished'?sim.runTime():null,proof:sim.rules.counters().diamondRouteCrossed,
    x:sim.state().bike.pos.x,maxBikeY,maxFrontY,hash:sim.hash()};
  rows.push(row);
  if(row.phase==='finished'&&row.faults===0&&!row.proof&&row.maxBikeY<3){
    const recording=rec.toRecording();
    recording.header.routeProof={goalId:sim.track.diamondGoal!.id,crossed:false};
    fs.writeFileSync('docs/evidence/s3-fairness/s3-whiteout-rookie-lower.rec.json',encodeJSON(recording)+'\n');
    break;
  }
}
fs.writeFileSync('docs/evidence/s3-fairness/lower-full.json',JSON.stringify(rows,null,2)+'\n');
console.log(JSON.stringify(rows,null,2));
