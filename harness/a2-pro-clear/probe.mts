/** Replay a candidate A2 Pro input against the current solver before browser selection. */
import { readFileSync } from 'node:fs';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';
import { srcFingerprint } from '../lib/metrics';

const file = process.argv[2] ?? 'docs/evidence/alpine-retarget/a2-log-jam-pro-bot.rec.json';
const rec = decodeJSON(readFileSync(file, 'utf8'));
if (rec.header.trackId !== 'a2-log-jam' || rec.header.bike !== 'pro') throw new Error('expected A2 Pro input');
const sim = await createSimFor(rec);
let tick = 0;
let firstFinishTick: number | null = null;
let firstFaultTick: number | null = null;
let maxX = -Infinity;
for (const frame of expandFrames(rec)) {
  tick++;
  const events = sim.step(frame);
  maxX = Math.max(maxX, sim.state().bike.pos.x);
  if (firstFinishTick === null && events.some((event) => event.type === 'finish')) firstFinishTick = tick;
  if (firstFaultTick === null && events.some((event) => event.type === 'fault')) firstFaultTick = tick;
}
console.log(JSON.stringify({ file, src: srcFingerprint(), ticks: tick, firstFinishTick, firstFaultTick, phase: sim.phase(), faults: sim.faults(), runTime: sim.runTime(), maxX, hash: sim.hash() }, null, 2));
