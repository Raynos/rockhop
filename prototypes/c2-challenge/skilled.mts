/** A readable two-beat C2 line, quantized and recorded through the game replay format. */
import { writeFileSync } from 'node:fs';
import { createSim } from '../../harness/lib/sim';
import { recordingHeader } from '../../harness/lib/recording';
import { InputRecorder, iterateFrames, quantizeInput } from '../../src/core/replay';
import { registerTrack } from '../../src/tracks';
import { C2_CHALLENGE } from './candidate';

registerTrack(C2_CHALLENGE);
const rows = [];
for (const bike of ['rookie', 'pro'] as const) for (let k = 0; k < 3; k++) {
  const seed = (C2_CHALLENGE.seed + k) >>> 0;
  const sim = await createSim(C2_CHALLENGE.id, seed, 120, { bike });
  const recorder = new InputRecorder(recordingHeader(sim, 'C2 selected candidate: pier pitch-forward, release and tip-forward over crane barge'));
  let finishTick: number | null = null;
  let firstFault: unknown = null;
  let lip: unknown = null;
  let landing: unknown = null;
  let maxX = 0;
  for (let tick = 0; tick < 80 * sim.hz; tick++) {
    const s = sim.state();
    const x = s.bike.pos.x;
    // Pro requires the earlier pier correction; keep the same simple input on both bikes.
    const pier = x >= 120 && x < 140;
    const craneAir = x >= 308 && x < 322;
    const frame = quantizeInput({ throttle: pier || craneAir ? 0 : 1, brake: 0, lean: pier ? 1 : craneAir ? 0.5 : 0 });
    recorder.push(frame);
    if (!lip && x >= 307) lip = { tick, x: +x.toFixed(2), vx: +s.bike.vel.x.toFixed(2), pitch: +s.bike.angle.toFixed(3) };
    if (!landing && x >= 322) landing = { tick, x: +x.toFixed(2), vx: +s.bike.vel.x.toFixed(2), pitch: +s.bike.angle.toFixed(3) };
    for (const event of sim.step(frame)) {
      if (event.type === 'fault') firstFault ??= { tick: tick + 1, x: +x.toFixed(2), reason: event.reason };
      if (event.type === 'finish') finishTick = tick + 1;
    }
    maxX = Math.max(x, maxX);
    if (finishTick !== null) break;
  }
  const rec = recorder.toRecording();
  const replay = await createSim(C2_CHALLENGE.id, seed, 120, { bike });
  let replayFinishTick: number | null = null;
  let replayTick = 0;
  for (const frame of iterateFrames(rec)) {
    replayTick++;
    if (replay.step(frame).some((event) => event.type === 'finish')) replayFinishTick = replayTick;
  }
  const row = { bike, seed, finishTick, replayFinishTick, faults: sim.faults(), firstFault, lip, landing, maxX: +maxX.toFixed(2), hash: sim.hash(), replayHash: replay.hash(), exact: finishTick === replayFinishTick && sim.hash() === replay.hash() };
  rows.push(row);
  process.stdout.write(`${bike} seed+${k}: ${finishTick ? `CLEAR ${finishTick}` : 'FAIL'} faults=${row.faults} exact=${row.exact} lip=${JSON.stringify(lip)}\n`);
  if (!row.exact) throw new Error(`${bike} seed+${k} replay mismatch`);
  if (k === 0) writeFileSync(new URL(`../../docs/evidence/c2-challenge/${bike}-skilled.json`, import.meta.url), `${JSON.stringify({ magic: 'TRIN', ...rec })}\n`);
}
writeFileSync(new URL('../../docs/evidence/c2-challenge/skilled.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
