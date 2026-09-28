/** Held throttle for ten minutes per bike/seed on the unchanged S3 geometry. */
import fs from 'node:fs';
import { quantizeInput } from '../../src/core/replay';
import { createSim } from '../lib/sim';

const go=quantizeInput({throttle:1});
const rows=[];
for(const bike of ['rookie','pro'] as const)for(const seed of [undefined,1,2]){
  const sim=await createSim('s3-whiteout',seed,120,{bike});
  let maxX=sim.state().bike.pos.x,ticks=0;
  for(;ticks<72000&&sim.phase()!=='finished';ticks++){
    sim.step(go);maxX=Math.max(maxX,sim.state().bike.pos.x);
  }
  rows.push({bike,seed:sim.seed,ticks,phase:sim.phase(),faults:sim.faults(),
    maxX,proof:sim.rules.counters().diamondRouteCrossed===true,
    finishS:sim.state().finishTime});
}
fs.writeFileSync('docs/evidence/s3-fairness/passive.json',JSON.stringify(rows,null,2)+'\n');
console.log(JSON.stringify(rows,null,2));
if(rows.some(r=>r.phase==='finished'))process.exitCode=1;
