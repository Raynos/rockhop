/** Record the registered C2 line with a gentle Pier 2 correction and release-only crane landing. */
import fs from 'node:fs';
import path from 'node:path';
import { createSim } from './lib/sim';
import { recordingHeader } from './lib/recording';
import { InputRecorder, expandFrames, quantizeInput } from '../src/core/replay';

const trackId = 'c2-crane-hop';
const seed = 3733111498;
for (const bike of ['rookie', 'pro'] as const) {
  const sim = await createSim(trackId, seed, 120, { bike });
  const recorder = new InputRecorder(recordingHeader(sim, 'C2 registered: gentle Pier 2 correction, release-only crane landing'));
  let finishTick: number | null = null;
  for (let tick = 0; tick < 90 * sim.hz; tick++) {
    const x = sim.state().bike.pos.x;
    const pier = x >= 112 && x < 140;
    const craneAir = x >= 308 && x < 322;
    const frame = quantizeInput({ throttle: pier || craneAir ? 0 : 1, brake: 0, lean: pier ? 0.4 : 0 });
    recorder.push(frame);
    if (sim.step(frame).some((event) => event.type === 'finish')) { finishTick = tick + 1; break; }
  }
  const rec = recorder.toRecording();
  const replay = await createSim(trackId, seed, 120, { bike });
  replay.run(expandFrames(rec));
  if (finishTick === null || sim.faults() !== 0 || replay.hash() !== sim.hash()) throw new Error(`${bike}: release line failed`);
  const file = path.resolve(`harness/inputs/c2-crane-hop/bot-3${bike === 'pro' ? '-pro' : ''}.json`);
  fs.writeFileSync(file, `${JSON.stringify({ magic: 'TRIN', ...rec })}\n`);
  process.stdout.write(`${bike} tick=${finishTick} faults=${sim.faults()} hash=${sim.hash()} file=${file}\n`);
}
