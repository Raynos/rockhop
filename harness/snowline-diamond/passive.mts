import fs from 'node:fs';
import { quantizeInput } from '../../src/core/replay';
import { createSim } from '../lib/sim';

const id=process.argv[2]==='S3'?'s3-whiteout':'s1-lift-line';
const go=quantizeInput({throttle:1});
const rows=[];
for(const bike of ['rookie','pro'] as const)for(const seed of [undefined,1,2]){
  const sim=await createSim(id,seed,120,{bike});
  const events=[];
  let lastBand=-1;
  let ticks=0,maxX=sim.state().bike.pos.x;
  for(let tick=0;tick<72000&&sim.phase()!=='finished';tick++){
    sim.step(go);
    ticks++;
    const state=sim.state();
    maxX=Math.max(maxX,state.bike.pos.x);
    const band=state.bike.pos.x>=260&&state.bike.pos.x<=320?Math.floor(state.bike.pos.x/3):-1;
    if(band!==-1&&band!==lastBand){events.push({tick:tick+1,x:state.bike.pos.x,y:state.bike.pos.y,rearY:state.wheels.rear.pos.y,proof:sim.rules.counters().diamondRouteCrossed,phase:sim.phase(),faults:sim.faults()});lastBand=band;}
    if(state.bike.pos.x<200)lastBand=-1;
  }
  rows.push({id,bike,seed:sim.seed,ticks,maxX,phase:sim.phase(),faults:sim.faults(),proof:sim.rules.counters().diamondRouteCrossed,finishS:sim.state().finishTime,
    featurePasses:events.filter(e=>e.x>=280&&e.x<=310).slice(0,12)});
}
fs.mkdirSync('docs/evidence/snowline-diamond',{recursive:true});
fs.writeFileSync(`docs/evidence/snowline-diamond/${id}-passive.json`,`${JSON.stringify(rows,null,2)}\n`);
console.log(JSON.stringify(rows.map(({bike,seed,phase,faults,maxX})=>({bike,seed,phase,faults,maxX})),null,2));
