/** Find a clean full Rookie clear from a measured under-shelf S3 approach. */
import fs from 'node:fs';
import { decodeJSON, encodeJSON, expandFrames, InputRecorder, quantizeInput } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';
import { recordingHeader } from '../lib/recording';
import { configFor, playTrack } from '../bot/play';
import { DEFAULT_WEIGHTS } from '../bot/score';

const source=decodeJSON(fs.readFileSync('docs/evidence/snowline-diamond/s3-whiteout-rookie.rec.json','utf8'));
const frames=expandFrames(source);
const sim=await createSimFor(source);
const prefix=[];
for(const frame of frames){
  const x=sim.state().bike.pos.x;
  const input=x<112?frame:x<125?quantizeInput({throttle:0,lean:0}):
    x<132?quantizeInput({throttle:0,lean:1}):x<152?frame:frame;
  sim.step(input);prefix.push(input);
  if(sim.faults())throw new Error(`prefix fault at x=${sim.state().bike.pos.x}`);
  if(sim.state().bike.pos.x>=160)break;
}
const prefixState={x:sim.state().bike.pos.x,phase:sim.phase(),faults:sim.faults(),
  proof:sim.rules.counters().diamondRouteCrossed,maxTick:prefix.length};
const result=playTrack(sim,{skill:'oracle',config:configFor('oracle',1000),weights:DEFAULT_WEIGHTS,
  limits:{maxAttempts:40,maxRewinds:400,maxSimSeconds:120,maxWallMs:150000}});
const recorder=new InputRecorder(recordingHeader(sim,'s3 rookie visually lower under snow-cat shelf'));
for(const frame of [...prefix,...result.frames])recorder.push(frame);
const recording=recorder.toRecording();
recording.header.routeProof={goalId:sim.track.diamondGoal!.id,crossed:sim.rules.counters().diamondRouteCrossed===true};
const fresh=await createSimFor(recording);fresh.run(expandFrames(recording));
const row={prefixState,phase:sim.phase(),faults:sim.faults(),proof:sim.rules.counters().diamondRouteCrossed,
  finishS:sim.phase()==='finished'?sim.runTime():null,hash:sim.hash(),outcome:result.outcome,
  maxX:result.maxX,rewinds:result.rewinds,wallMs:result.wallMs,
  replay:{phase:fresh.phase(),faults:fresh.faults(),proof:fresh.rules.counters().diamondRouteCrossed,
    finishS:fresh.phase()==='finished'?fresh.runTime():null,hash:fresh.hash()}};
fs.writeFileSync('docs/evidence/s3-fairness/continue-lower.json',JSON.stringify(row,null,2)+'\n');
if(row.phase==='finished'&&row.faults===0&&!row.proof&&row.hash===row.replay.hash)
  fs.writeFileSync('docs/evidence/s3-fairness/s3-whiteout-rookie-lower.rec.json',encodeJSON(recording)+'\n');
console.log(JSON.stringify(row,null,2));
if(row.phase!=='finished'||row.faults!==0||row.proof||row.hash!==row.replay.hash)process.exitCode=1;
