import { writeFileSync } from 'node:fs';
import { createSim } from '../../harness/lib/sim';
import { recordingHeader } from '../../harness/lib/recording';
import { playReflex } from '../../harness/reflex/play';
import { InputRecorder, iterateFrames } from '../../src/core/replay';
import { medalFor } from '../../src/game/rules';
import { registerTrack } from '../../src/tracks';
import { C1_CHALLENGE } from './candidate';

registerTrack(C1_CHALLENGE);
const rows = [];
for (const bike of ['rookie', 'pro'] as const) {
  for (let k = 0; k < 3; k++) {
    const seed = C1_CHALLENGE.seed + k;
    const sim = await createSim(C1_CHALLENGE.id, seed, 120, { bike });
    const trace = [];
    const r = playReflex(sim, { skill: 'average', seed, attemptsCap: 50, maxSimSeconds: 600,
      onTick(tick, intent, keys) {
        const s = sim.state();
        if (k === 0 && s.bike.pos.x >= 200 && s.bike.pos.x <= 280 && tick % 12 === 0) trace.push({ tick, x: +s.bike.pos.x.toFixed(2), v: +s.bike.vel.x.toFixed(2), angle: +(s.bike.angle * 180 / Math.PI).toFixed(1), keys, rule: intent.rule });
      },
    });
    const medal = r.finishTime === null ? null : medalFor(r.finishTime, r.faults.length, C1_CHALLENGE.meta?.targetTimeS ?? 50, bike);
    const row = { bike, seed, outcome: r.outcome, attempts: r.attempts, finishTime: r.finishTime, medal, maxX: r.maxX, faults: r.faults.length, firstFault: r.faults[0], hash: r.finalHash, rules: r.rules };
    rows.push(row);
    process.stdout.write(`${bike} seed+${k} ${r.outcome} attempts=${r.attempts} time=${r.finishTime} medal=${medal} first=${r.faults[0]?.x.toFixed(1)}\n`);
    if (k === 0 && r.outcome === 'finished') {
      const recorder = new InputRecorder(recordingHeader(sim, 'standalone-c1-challenge reflex-average'));
      for (const f of r.frames) recorder.push(f);
      const rec = recorder.toRecording();
      writeFileSync(new URL(`../../docs/evidence/c1-challenge/${bike}-clear.json`, import.meta.url), `${JSON.stringify({ magic: 'TRIN', ...rec })}\n`);
      writeFileSync(new URL(`../../docs/evidence/c1-challenge/${bike}-trace.json`, import.meta.url), `${JSON.stringify(trace, null, 2)}\n`);
      const check = await createSim(C1_CHALLENGE.id, seed, 120, { bike });
      let replayFinish = null;
      for (const frame of iterateFrames(rec)) for (const event of check.step(frame)) if (event.type === 'finish') replayFinish = check.runTime();
      if (replayFinish !== r.finishTime || check.hash() !== r.finalHash) throw new Error(`${bike} replay mismatch`);
      process.stdout.write(`  exact replay ${replayFinish.toFixed(6)} ${check.hash()}\n`);
    }
  }
}
writeFileSync(new URL('../../docs/evidence/c1-challenge/reflex.json', import.meta.url), `${JSON.stringify(rows, null, 2)}\n`);
