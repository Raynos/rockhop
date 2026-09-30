/** Rebuild the audit table from preserved originals and installed goldens. */
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { expandFrames } from '../../../../src/core/replay';
import { createSimFor } from '../../../../harness/lib/sim';
import { loadRecording } from '../../../../harness/lib/recording';
import { srcFingerprint } from '../../../../harness/lib/metrics';

const dir = 'docs/evidence/course-remaster/pro-early-goldens';
const ids = ['c1-low-tide', 'c2-crane-hop', 'c3-hull-breach', 'a1-sawdust', 'a2-log-jam', 'a3-timberline', 'd1-dust-devil', 'd2-conveyor'];
const sha = (file: string) => createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const proof1 = fs.readFileSync(`${dir}/fresh-process-1.jsonl`, 'utf8');
const proof2 = fs.readFileSync(`${dir}/fresh-process-2.jsonl`, 'utf8');
if (proof1 !== proof2) throw new Error('fresh processes did not produce byte-identical reports');
const proofs = proof1.trim().split('\n').map(line => JSON.parse(line) as { track: string; inputSha256: string; finishTime: number; hash: string; src: string });
const searchJson = (name: string) => JSON.parse(fs.readFileSync(`${dir}/search/${name}.json`, 'utf8'));
const trials: Record<string, { count: number; method: string }> = {
  'c1-low-tide': { count: 0, method: 'Unchanged old input, replayed clean and restamped' },
  'c2-crane-hop': { count: searchJson('c2-window').tested, method: 'Rookie source on Pro, bounded single control window at crane' },
  'c3-hull-breach': { count: searchJson('c3-hull-breach-repair').rounds.reduce((n: number, r: { tested: number }) => n + r.tested, 0) + searchJson('c3-hull-breach-tail').rows.length, method: 'Five greedy first-fault repairs, then measured clean tail' },
  'a1-sawdust': { count: searchJson('a1-window').tested, method: 'Old Pro source, bounded single control window at flume' },
  'a2-log-jam': { count: searchJson('a2-log-jam-repair').rounds.reduce((n: number, r: { tested: number }) => n + r.tested, 0) + searchJson('a2-log-jam-tail').rows.length, method: 'Five greedy first-fault repairs, then measured clean tail' },
  'a3-timberline': { count: searchJson('a3-timberline-repair').rounds.reduce((n: number, r: { tested: number }) => n + r.tested, 0) + searchJson('a3-timberline-tail').rows.length, method: 'Five greedy first-fault repairs, then measured clean tail' },
  'd1-dust-devil': { count: searchJson('d1-dust-devil-repair').rounds.reduce((n: number, r: { tested: number }) => n + r.tested, 0) + searchJson('d1-dust-devil-tail').rows.length, method: 'Four greedy first-fault repairs, then measured clean tail' },
  'd2-conveyor': { count: searchJson('d2-first-repair').rounds.reduce((n: number, r: { tested: number }) => n + r.tested, 0) + searchJson('d2-first-tail').rows.length + searchJson('d2-second-repair').rounds.reduce((n: number, r: { tested: number }) => n + r.tested, 0) + searchJson('d2-second-tail').rows.length, method: 'Five greedy repairs, first measured tail, one further repair, second measured clean tail' },
};
const rows = [];
for (const track of ids) {
  const oldFile = `${dir}/historical/${track}.bot-3-pro.json`;
  const newFile = `harness/inputs/${track}/bot-3-pro.json`;
  const old = loadRecording(oldFile);
  const next = loadRecording(newFile);
  const oldSim = await createSimFor(old);
  const newSim = await createSimFor(next);
  oldSim.run(expandFrames(old));
  newSim.run(expandFrames(next));
  const proof = proofs.find(p => p.track === track);
  if (!proof || proof.inputSha256 !== sha(newFile) || proof.finishTime !== newSim.runTime() || proof.hash !== newSim.hash() || proof.src !== srcFingerprint())
    throw new Error(`${track} installed replay differs from fresh-process proof`);
  if (newSim.phase() !== 'finished' || newSim.faults()) throw new Error(`${track} installed replay is not a clean finish`);
  rows.push({ track, seed: old.header.seed, historical: { file: oldFile, sha256: sha(oldFile), phase: oldSim.phase(), terminalTimeS: oldSim.runTime(), faults: oldSim.faults(), attempts: oldSim.faults() + 1, hash: oldSim.hash(), frames: expandFrames(old).length },
    replacement: { file: newFile, sha256: sha(newFile), phase: newSim.phase(), finishTimeS: newSim.runTime(), faults: newSim.faults(), attempts: 1, hash: newSim.hash(), frames: expandFrames(next).length, src: proof.src },
    search: trials[track] });
}
const report = { title: 'Pro early-course golden regeneration', sourceFingerprint: srcFingerprint(),
  tuningSha256: sha('src/physics/v2/tuning.ts'),
  independentFreshProcesses: { runs: 2, byteIdentical: true, files: [`${dir}/fresh-process-1.jsonl`, `${dir}/fresh-process-2.jsonl`] },
  rows,
  affectedPins: [{ file: 'harness/gate/expected.json', key: 'c2-crane-hop:pro', oldExpected: { finishTimeS: 25.833333333333332, hash: '64ec5d60318654fd' }, current: { finishTimeS: 24.891666666666666, hash: '2c0081dd610d64bc', ticks: 2987 } }],
  limits: ['Node-only proof; browser and visual clip verification remain for the parent after the shared dist lane is released.', 'The fingerprint becomes stale if physics, tracks, core replay or rules change.', 'These are Pro reference inputs on levels 1-8; they do not prove Rookie difficulty or human attempts-to-clear.'] };
fs.writeFileSync(`${dir}/report.json`, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ src: report.sourceFingerprint, tracks: rows.length, zeroFaultFinishes: rows.filter(r => r.replacement.phase === 'finished' && !r.replacement.faults).length, trials: rows.reduce((n, r) => n + r.search.count, 0) }));
