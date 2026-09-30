/** Install only source-pinned, zero-fault fresh-process Pro candidates; historical bytes must match first. */
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { expandFrames } from '../../../../src/core/replay';
import { createSimFor } from '../../../../harness/lib/sim';
import { loadRecording, saveRecording } from '../../../../harness/lib/recording';
import { srcFingerprint } from '../../../../harness/lib/metrics';

const expectedSrc = 'fd8fe7c2';
const expectedTuning = '9e972b943eb3a49c17caaef20c64e62dc6a15dd43fd23b0778b5b879fa85ef3a';
const sha = (bytes: Uint8Array) => createHash('sha256').update(bytes).digest('hex');
if (srcFingerprint() !== expectedSrc || sha(fs.readFileSync('src/physics/v2/tuning.ts')) !== expectedTuning)
  throw new Error('source changed since independent fresh-process verification');
const rows = [
  ['c1-low-tide', 'docs/evidence/course-remaster/pro-early-goldens/historical/c1-low-tide.bot-3-pro.json', 28.15, '7ebdd3902741b09d'],
  ['c2-crane-hop', '/tmp/rockhop-pro-early-c2-crane-hop-rookie.candidate.json', 24.891666666666666, '2c0081dd610d64bc'],
  ['c3-hull-breach', '/tmp/rockhop-pro-early-c3-hull-breach-tail.candidate.json', 35.25, '2816823aece6ead6'],
  ['a1-sawdust', '/tmp/rockhop-pro-early-a1-sawdust-pro.candidate.json', 27.908333333333335, '7da5b985e2942c50'],
  ['a2-log-jam', '/tmp/rockhop-pro-early-a2-log-jam-tail.candidate.json', 32.6, '823d80bfd55810ef'],
  ['a3-timberline', '/tmp/rockhop-pro-early-a3-timberline-tail.candidate.json', 24.191666666666666, '5a580c0a1cecf41b'],
  ['d1-dust-devil', '/tmp/rockhop-pro-early-d1-dust-devil-tail.candidate.json', 33.06666666666667, 'c6bed1414265ade9'],
  ['d2-conveyor', '/tmp/rockhop-pro-early-d2-conveyor-tail.candidate.json', 40.45, 'e480a9f68d1258fe'],
] as const;
for (const [track, candidate, time, hash] of rows) {
  const target = `harness/inputs/${track}/bot-3-pro.json`;
  const history = `docs/evidence/course-remaster/pro-early-goldens/historical/${track}.bot-3-pro.json`;
  if (sha(fs.readFileSync(target)) !== sha(fs.readFileSync(history))) throw new Error(`original ${track} changed after preservation`);
  const rec = loadRecording(candidate);
  if (rec.header.trackId !== track || rec.header.bike !== 'pro' || rec.header.physics !== 'v2') throw new Error(`${track} candidate identity mismatch`);
  const sim = await createSimFor(rec);
  sim.run(expandFrames(rec));
  if (sim.phase() !== 'finished' || sim.faults() !== 0 || sim.runTime() !== time || sim.hash() !== hash)
    throw new Error(`${track} clean finish changed`);
  rec.header.note = `Pro early ${track === 'c1-low-tide' ? 'restamp' : 'measured input repair'} bike=pro physics=v2 src=${expectedSrc} historical=a415fcb8`;
  saveRecording(target, rec);
  console.log(JSON.stringify({ track, target, source: candidate, src: expectedSrc, finishTime: time, hash, frames: expandFrames(rec).length }));
}
