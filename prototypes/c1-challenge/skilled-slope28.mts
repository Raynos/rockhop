/** Simple, player-readable line: brake to ~14 at girder; gas + forward lean up bow; release on crest. */
import { writeFileSync } from 'node:fs';
import { createSim } from '../../harness/lib/sim';
import { recordingHeader } from '../../harness/lib/recording';
import { InputRecorder, iterateFrames, quantizeInput } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { registerTrack } from '../../src/tracks';
import { makeSlope } from './candidate-slope';
const C1_CHALLENGE = makeSlope('c1-low-tide', 28, 2.8);

registerTrack(C1_CHALLENGE);
const rows = [];
for (const bike of ['rookie', 'pro'] as const) {
  for (let k = 0; k < 3; k++) {
    const seed = (C1_CHALLENGE.seed + k) >>> 0;
    const sim = await createSim(C1_CHALLENGE.id, seed, 120, { bike });
    const recorder = new InputRecorder(recordingHeader(sim, 'standalone-c1-challenge girder-brake-bow-lean'));
    let finishTime = null;
    let firstFault = null;
    let speedAtMarker = null;
    let speedAtFoot = null;
    for (let tick = 0; tick < 90 * sim.hz; tick++) {
      const s = sim.state();
      const x = s.bike.pos.x;
      const v = s.bike.vel.x;
      if (speedAtMarker === null && x >= 192) speedAtMarker = v;
      if (speedAtFoot === null && x >= 208) speedAtFoot = v;
      let throttle = 1, brake = 0, lean = 0;
      if (x >= 192 && x < 208) {
        if (v > 15) { throttle = 0; brake = 1; }
        else if (v > 14) throttle = 0;
      }
      if (x >= 208 && x < 215) { throttle = 1; lean = 1; }
      if (x >= 215 && x < 221) throttle = 0;
      const frame = quantizeInput({ throttle, brake, lean });
      recorder.push(frame);
      for (const e of sim.step(frame)) {
        if (e.type === 'fault') firstFault ??= { x: +s.bike.pos.x.toFixed(2), reason: e.reason, time: sim.runTime() };
        if (e.type === 'finish') finishTime = sim.runTime();
      }
      if (finishTime !== null) break;
    }
    const row = { bike, seed, clear: finishTime !== null, finishTime, medal: finishTime === null ? null : medalFor(finishTime, sim.faults(), C1_CHALLENGE.meta?.targetTimeS ?? 50, bike), faults: sim.faults(), firstFault, speedAtMarker, speedAtFoot, hash: sim.hash() };
    rows.push(row);
    process.stdout.write(`${bike} seed+${k} ${row.clear ? `CLEAR ${finishTime?.toFixed(3)} ${row.medal}` : 'FAIL'} faults=${row.faults} marker=${speedAtMarker?.toFixed(2)} foot=${speedAtFoot?.toFixed(2)}\n`);
    if (k === 0 && finishTime !== null) {
      const rec = recorder.toRecording();
      writeFileSync(new URL(`../../docs/evidence/c1-challenge/${bike}-skilled-slope28.json`, import.meta.url), `${JSON.stringify({ magic: 'TRIN', ...rec })}\n`);
      const replay = await createSim(C1_CHALLENGE.id, seed, 120, { bike });
      let replayFinish = null;
      for (const f of iterateFrames(rec)) for (const e of replay.step(f)) if (e.type === 'finish') replayFinish = replay.runTime();
      if (replayFinish !== finishTime || replay.hash() !== sim.hash()) throw new Error(`${bike} replay mismatch`);
      process.stdout.write(`  exact replay ${replayFinish.toFixed(6)} ${replay.hash()}\n`);
    }
  }
}
writeFileSync(new URL('../../docs/evidence/c1-challenge/skilled-slope28.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
