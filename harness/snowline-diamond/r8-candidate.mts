import fs from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { createSimFor } from '../lib/sim';

for(const file of process.argv.slice(2)){
  const rec=decodeJSON(fs.readFileSync(file,'utf8'));
  const sim=await createSimFor(rec);
  let firstFault=null;
  for(const [i,f] of expandFrames(rec).entries()){
    const events=sim.step(f);
    if(firstFault===null&&events.some(e=>e.type==='fault'))firstFault={tick:i+1,x:sim.state().bike.pos.x};
  }
  const proof=sim.rules.counters().diamondRouteCrossed===true;
  console.log(JSON.stringify({file,phase:sim.phase(),faults:sim.faults(),firstFault,proof,
    medal:medalFor(sim.runTime(),sim.faults(),sim.track.meta?.targetTimeS,sim.bike,proof),
    finishS:sim.state().finishTime,hash:sim.hash(),finalX:sim.state().bike.pos.x}));
}
