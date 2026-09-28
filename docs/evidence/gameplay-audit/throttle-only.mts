/** Audit probe: constant GO, no brake/lean/hop/restart, deterministic default track seed. */
import { writeFileSync } from 'node:fs';
import { createSim } from '../../../harness/lib/sim';
import { medalFor } from '../../../src/game/rules';
import { ROCKHOP_ALL } from '../../../src/tracks';

const frame = { throttle: 1, brake: 0, lean: 0, hop: false, restart: false } as const;
const capSeconds = 600;
const rows = [];
for (const track of ROCKHOP_ALL) {
  for (const bike of ['rookie', 'pro'] as const) {
    const sim = await createSim(track.id, track.seed, 120, { bike });
    let firstFault: { reason: string; x: number; checkpoint: number; time: number } | null = null;
    let maxX = sim.state().bike.pos.x;
    let faultEvents = 0;
    let checkpointEvents = 0;
    let finishTime: number | null = null;
    for (let tick = 0; tick < capSeconds * sim.hz; tick++) {
      const events = sim.step(frame);
      const state = sim.state();
      maxX = Math.max(maxX, state.bike.pos.x);
      for (const event of events) {
        if (event.type === 'fault') {
          faultEvents++;
          firstFault ??= { reason: event.reason, x: +state.bike.pos.x.toFixed(2), checkpoint: state.checkpoint, time: +(sim.runTime()).toFixed(2) };
        }
        if (event.type === 'checkpoint') checkpointEvents++;
        if (event.type === 'finish') finishTime = sim.runTime();
      }
      if (finishTime !== null) break;
    }
    const target = track.meta?.targetTimeS ?? null;
    const row = {
      id: track.id,
      bike,
      seed: track.seed,
      finishX: track.finishX,
      targetS: target,
      cleared: finishTime !== null,
      timeS: finishTime === null ? null : +finishTime.toFixed(3),
      medal: finishTime === null ? null : medalFor(finishTime, sim.faults(), target, bike),
      faults: sim.faults(),
      faultEvents,
      checkpointEvents,
      maxX: +maxX.toFixed(2),
      maxPct: +(100 * maxX / track.finishX).toFixed(1),
      firstFault,
      hash: sim.hash(),
      simulatedS: +Math.min(capSeconds, sim.totalTicks() / sim.hz).toFixed(3),
    };
    rows.push(row);
    process.stdout.write(`${track.id.padEnd(20)} ${bike.padEnd(6)} ${row.cleared ? `CLEAR ${String(row.timeS).padStart(7)}s ${row.medal}` : `FAIL ${String(row.maxPct).padStart(5)}%`} faults=${row.faults} checkpointEvents=${checkpointEvents}\n`);
  }
}
writeFileSync(new URL('./throttle-only.json', import.meta.url), `${JSON.stringify({ method: 'constant throttle=1, brake=lean=0, hop=restart=false; default seed; RunRules auto-respawn', capSeconds, rows }, null, 2)}\n`);
