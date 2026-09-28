/** Search a clean C2 line that also respects the permanent R7 rider-pose band. */
import { createSim } from './lib/sim';
import { quantizeInput } from '../src/core/replay';

const runs = [
  { pierStart: 120, pierEnd: 140, pierLean: 1, craneStart: 308, craneEnd: 322, craneLean: 0, craneThrottle: 0 },
  ...[112, 116, 120, 124, 128].flatMap((pierStart) =>
    [128, 132, 136, 140].filter((pierEnd) => pierEnd > pierStart).flatMap((pierEnd) =>
      [0.4, 0.6, 0.8, 1].map((pierLean) => ({ pierStart, pierEnd, pierLean, craneStart: 308, craneEnd: 322, craneLean: 0, craneThrottle: 0 })))),
  ...[0, 0.2, 0.4, 0.5].flatMap((craneLean) => [312, 316, 320].map((craneEnd) =>
    ({ pierStart: 120, pierEnd: 140, pierLean: 1, craneStart: 308, craneEnd, craneLean, craneThrottle: craneLean > 0 ? 1 : 0 }))),
];
for (const bike of ['rookie', 'pro'] as const) {
  const rows = [];
  for (const r of runs) {
    const sim = await createSim('c2-crane-hop', 3733111498, 120, { bike });
    const world = sim.world as unknown as { F: Float64Array };
    let riding = 0;
    let outside = 0;
    const zones = [0, 0, 0, 0];
    for (let tick = 0; tick < 90 * sim.hz; tick++) {
      const x = sim.state().bike.pos.x;
      const pier = x >= r.pierStart && x < r.pierEnd;
      const crane = x >= r.craneStart && x < r.craneEnd;
      const frame = quantizeInput({ throttle: pier ? 0 : crane ? r.craneThrottle : 1,
        brake: 0, lean: pier ? r.pierLean : crane ? r.craneLean : 0 });
      sim.step(frame);
      const s = sim.state();
      if (sim.phase() === 'riding' && s.riderBody) {
        riding++;
        if (Math.abs(s.riderBody.angle - s.bike.angle - world.F[8]!) > 0.35) {
          outside++;
          const zone = x < 120 ? 0 : x < 220 ? 1 : x < 300 ? 2 : 3;
          zones[zone] = (zones[zone] ?? 0) + 1;
        }
      }
      if (sim.phase() === 'finished') break;
    }
    if (sim.phase() === 'finished' && sim.faults() === 0) {
      rows.push({ r, tick: sim.runTicks(), psi: outside / riding, outside, riding, zones, hash: sim.hash() });
    }
  }
  rows.sort((a, b) => a.psi - b.psi);
  process.stdout.write(`${bike}: ${rows.length} clean lines\n${JSON.stringify(rows.slice(0, 12), null, 2)}\n`);
}
