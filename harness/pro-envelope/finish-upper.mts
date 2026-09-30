/** Commit a proven local upper route, then ask the committed skill-3 rider to finish it. */
import fs from 'node:fs';
import { decodeJSON, encodeJSON, expandFrames, InputRecorder, quantizeInput } from '../../src/core/replay';
import type { InputFrame } from '../../src/core/types';
import { createSimFor } from '../lib/sim';
import { playTrack, configFor } from '../bot/play';
import { DEFAULT_WEIGHTS } from '../bot/score';

const dir = '/tmp/rockhop-pro-envelope-audit';
fs.mkdirSync(dir, { recursive: true });
const key = process.argv[2] ?? 't0l-1/source';
const skill = process.argv[3] === 'oracle' ? 'oracle' : 3;
const [preCode, flightCode] = key.split('/');
const sourceRec = decodeJSON(fs.readFileSync('docs/evidence/course-remaster/pro-envelope/s3-pro-lower-approach.replay.json', 'utf8'));
const source = expandFrames(sourceRec);
const sim = await createSimFor(sourceRec);
const frames: InputFrame[] = [];
const choose = (code: string | undefined, fallback: InputFrame): InputFrame => {
  if (!code || code === 'source') return fallback;
  const match = /^t([\d.]+)l(-?[\d.]+)$/.exec(code);
  if (!match) throw Error(`bad action ${code}`);
  return quantizeInput({ throttle: Number(match[1]), lean: Number(match[2]) });
};
let index = 0;
while (index < source.length && sim.state().bike.pos.x < 125) { const frame = source[index++]!; sim.step(frame); frames.push(frame); }
while (index < source.length && sim.state().bike.pos.x < 160 && sim.phase() === 'riding' && !sim.faults()) {
  const x = sim.state().bike.pos.x;
  const frame = x < 132 ? choose(preCode, source[index]!) : x < 152 ? choose(flightCode, source[index]!) : source[index]!;
  sim.step(frame); frames.push(frame); index++;
}
const proofAt160 = sim.rules.counters().diamondRouteCrossed === true;
if (!proofAt160 || sim.faults() || sim.state().bike.pos.x < 160) throw Error(`upper candidate not alive at 160, ${key}`);
const upperX = sim.state().bike.pos.x;
const result = playTrack(sim, { skill, config: { ...configFor(3), budgetTicks: 900_000 }, weights: DEFAULT_WEIGHTS,
  limits: { maxAttempts: 10, maxRewinds: 100, maxSimSeconds: 600, maxWallMs: 240_000 } });
frames.push(...result.frames);
const report = { key, skill, upperX, proofAt160, outcome: result.outcome, faults: result.faults.map((f) => ({ x: f.x, reason: f.reason })),
  finishTime: result.finishTime, attempts: result.attempts, routeProof: sim.rules.counters().diamondRouteCrossed, hash: sim.hash(),
  frames: frames.length, wallMs: result.wallMs, simTicks: sim.totalTicks(), rewinds: result.rewinds };
const slug = `${key.replaceAll('/', '_').replaceAll('-', 'm').replaceAll('.', 'p')}-${skill}`;
fs.writeFileSync(`${dir}/s3-upper-finish-${slug}.json`, `${JSON.stringify(report, null, 2)}\n`);
if (result.outcome === 'finished') {
  const rec = new InputRecorder({ ...sourceRec.header, note: `Pro envelope upper route ${key}` });
  for (const frame of frames) rec.push(frame);
  fs.writeFileSync(`${dir}/s3-upper-finish-${slug}.replay.json`, encodeJSON(rec.toRecording()));
}
console.log(JSON.stringify(report));
