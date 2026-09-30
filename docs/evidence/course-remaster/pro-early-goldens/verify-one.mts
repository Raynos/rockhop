/** Fresh-process, source-pinned proof for one Pro recording. */
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { expandFrames } from '../../../../src/core/replay';
import { createSimFor } from '../../../../harness/lib/sim';
import { loadRecording } from '../../../../harness/lib/recording';
import { srcFingerprint } from '../../../../harness/lib/metrics';

const file = process.argv[2];
if (!file) throw new Error('usage: verify-one.mts recording');
const tuningSha256 = createHash('sha256').update(fs.readFileSync('src/physics/v2/tuning.ts')).digest('hex');
const src = srcFingerprint();
if (tuningSha256 !== '9e972b943eb3a49c17caaef20c64e62dc6a15dd43fd23b0778b5b879fa85ef3a' || src !== 'fd8fe7c2')
  throw new Error(`physics changed: tuning=${tuningSha256} src=${src}`);
const bytes = fs.readFileSync(file);
const recording = loadRecording(file);
if (recording.header.bike !== 'pro' || recording.header.physics !== 'v2') throw new Error('not a Pro v2 recording');
const frames = expandFrames(recording);
const sim = await createSimFor(recording);
sim.run(frames);
const row = { file, track: recording.header.trackId, seed: recording.header.seed, src, tuningSha256,
  inputSha256: createHash('sha256').update(bytes).digest('hex'), frames: frames.length,
  phase: sim.phase(), faults: sim.faults(), finishTime: sim.runTime(), hash: sim.hash() };
if (row.phase !== 'finished' || row.faults !== 0) throw new Error(`not a clean finish: ${JSON.stringify(row)}`);
console.log(JSON.stringify(row));
