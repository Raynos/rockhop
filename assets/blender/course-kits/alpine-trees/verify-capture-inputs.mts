/** Node-only check of the three exact video-tail states; never starts a server/browser. */
import { readFileSync } from 'node:fs';
import { createSim } from '../../../../harness/lib/sim';
import { decodeJSON, expandFrames } from '../../../../src/core/replay';
const cases = [
  { file:'harness/inputs/a1-sawdust/bot-3.json', ticks:3650, expected:'397beb1fcd345e2d' },
  { file:'assets/blender/course-kits/alpine-trees/a1-held-go.rec.json', ticks:3156, expected:'9b8c25c5404681b3' },
  { file:'docs/evidence/alpine-retarget/a1-sawdust-rookie-restart.rec.json', ticks:3035, expected:'4b9a060e15075b4a' },
];
for(const spec of cases) {
  const rec=decodeJSON(readFileSync(spec.file,'utf8')),frames=expandFrames(rec);
  const sim=await createSim(rec.header.trackId,rec.header.seed,rec.header.physicsHz,{bike:'rookie'});
  for(let tick=0;tick<spec.ticks;tick++) sim.step(frames[tick]??frames.at(-1)!);
  if(sim.hash()!==spec.expected) throw new Error(`${spec.file}: current ${sim.hash()} differs from historical ${spec.expected}`);
  console.log(JSON.stringify({file:spec.file,ticks:spec.ticks,hash:sim.hash(),phase:sim.phase(),finishTime:sim.state().finishTime,faults:sim.faults()}));
}
