/** Scripted learning proxy: held GO to a crane fault, one-tick restart, then the learned line. */
import { writeFileSync } from 'node:fs';
import { createSim } from '../../harness/lib/sim';
import { InputRecorder, iterateFrames, quantizeInput } from '../../src/core/replay';
import { recordingHeader } from '../../harness/lib/recording';
import { registerTrack } from '../../src/tracks';
import { C2_CHALLENGE } from './candidate';

registerTrack(C2_CHALLENGE);
const rows = [];
for (const bike of ['rookie', 'pro'] as const) {
  const sim = await createSim(C2_CHALLENGE.id, C2_CHALLENGE.seed, 120, { bike });
  const recorder = new InputRecorder(recordingHeader(sim, 'C2 scripted learn: GO crane fault, tap restart, release/tip-forward line'));
  const GO = quantizeInput({ throttle: 1, brake: 0, lean: 0 });
  let firstCraneFaultTick = -1;
  let faultAtFirstCrane = 0;
  let beforeX = 0;
  for (let tick = 0; tick < 90 * 120; tick++) {
    beforeX = sim.state().bike.pos.x;
    recorder.push(GO);
    const events = sim.step(GO);
    if (beforeX > 280 && events.some((e) => e.type === 'fault')) {
      firstCraneFaultTick = tick + 1;
      faultAtFirstCrane = sim.faults();
      break;
    }
  }
  if (firstCraneFaultTick < 0) throw new Error(`${bike} no crane fault`);
  const restart = { ...GO, restart: true };
  recorder.push(restart);
  sim.step(restart);
  const restartTick = firstCraneFaultTick + 1;
  const restartX = sim.state().bike.pos.x;
  let finishTick: number | null = null;
  let nextFault: unknown = null;
  for (let tick = restartTick; tick < restartTick + 90 * 120; tick++) {
    const x = sim.state().bike.pos.x;
    const air = x >= 308 && x < 322;
    const frame = quantizeInput({ throttle: air ? 0 : 1, brake: 0, lean: air ? 0.5 : 0 });
    recorder.push(frame);
    for (const e of sim.step(frame)) {
      if (e.type === 'fault') nextFault ??= { tick: tick + 1, x: +x.toFixed(2) };
      if (e.type === 'finish') finishTick = tick + 1;
    }
    if (finishTick !== null) break;
  }
  const rec = recorder.toRecording();
  const replay = await createSim(C2_CHALLENGE.id, C2_CHALLENGE.seed, 120, { bike });
  let replayFinishTick: number | null = null;
  let replayTick = 0;
  for (const frame of iterateFrames(rec)) {
    replayTick++;
    if (replay.step(frame).some((event) => event.type === 'finish')) replayFinishTick = replayTick;
  }
  const row = { bike, firstCraneFaultTick, faultAtFirstCrane, restartTick, restartX: +restartX.toFixed(2), finishTick,
    ticksFromRestartToClear: finishTick === null ? null : finishTick - restartTick, attemptsToClear: finishTick === null ? null : sim.faults() + 1,
    faultsAtFinish: sim.faults(), nextFault, hash: sim.hash(), replayHash: replay.hash(), exact: finishTick === replayFinishTick && sim.hash() === replay.hash() };
  rows.push(row);
  process.stdout.write(`${bike} ${JSON.stringify(row)}\n`);
  if (!row.exact) throw new Error(`${bike} attempt replay mismatch`);
  writeFileSync(new URL(`../../docs/evidence/c2-challenge/${bike}-learned.json`, import.meta.url), `${JSON.stringify({ magic: 'TRIN', ...rec })}\n`);
}
writeFileSync(new URL('../../docs/evidence/c2-challenge/attempts.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
