/* Silent headless browser and Node proof for the candidate recording. */
import fs from 'node:fs';
import path from 'node:path';
import { expandFrames } from '../../../src/core/replay';
import { createSimFor } from '../../../harness/lib/sim';
import { loadRecording } from '../../../harness/lib/recording';
import { BrowserVerifier } from '../../../harness/lib/verify';

const dir = path.resolve('docs/evidence/c3-clean-reference');
const file = process.argv[2] || path.join(dir, 'rookie-zero-fault.rec.json');
const expectFinish = !process.argv.includes('--prefix');
const recording = loadRecording(file);
const sim = await createSimFor(recording);
const node = sim.run(expandFrames(recording));
const nodeFaultEvents = node.events.filter(event => event.type === 'fault').length;
const verifier = new BrowserVerifier({ dev: true });
try {
  const browser = [await verifier.run(recording), await verifier.run(recording)];
  const exact = sim.phase() === (expectFinish ? 'finished' : 'riding') && sim.faults() === 0 && nodeFaultEvents === 0 && browser.every(run =>
    run.faults === 0 && run.events.every(event => event.type !== 'fault') && run.hash === node.hash
    && run.finishTime === node.state.finishTime && run.state.tick === node.state.tick);
  const result = {
    recording: path.basename(file), expectFinish,
    node: { phase: sim.phase(), faults: sim.faults(), faultEvents: nodeFaultEvents, finishTime: node.state.finishTime,
      hash: node.hash, ticks: node.ticks, stateTick: node.state.tick },
    browser: browser.map(run => ({ faults: run.faults, faultEvents: run.events.filter(event => event.type === 'fault').length,
      finishTime: run.finishTime, hash: run.hash, stateTick: run.state.tick })),
    exact,
  };
  fs.writeFileSync(path.join(dir, expectFinish ? 'verification.json' : 'prefix-verification.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result));
  if (!exact) process.exitCode = 1;
} finally {
  await verifier.close();
}
