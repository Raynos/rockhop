/** Find a simple Pro correction at the second pier while preserving the shared crane-hop line. */
import { createSim } from '../../harness/lib/sim';
import { registerTrack } from '../../src/tracks';
import { makeCandidate } from './candidate';

const track = makeCandidate(18, 1.8);
registerTrack(track);
const sim = await createSim(track.id, track.seed, 120, { bike: 'pro' });
const rows = [];
for (const from of [120, 125, 130, 135, 140]) for (const to of [140, 145, 150, 155, 160]) for (const lean of [0, 0.5, 1]) {
  if (to <= from) continue;
  sim.reload();
  let finished = false, maxX = 0, firstFault: unknown = null;
  for (let tick = 0; tick < 65 * 120; tick++) {
    const s = sim.state();
    const x = s.bike.pos.x;
    const correction = x >= from && x < to;
    const hopCorrection = x >= 308 && x < 322;
    const frame = { throttle: correction || hopCorrection ? 0 : 1, brake: 0, lean: correction ? lean : hopCorrection ? 0.5 : 0, hop: false, restart: false };
    for (const e of sim.step(frame)) {
      if (e.type === 'fault') firstFault ??= { x: +x.toFixed(1), time: +sim.runTime().toFixed(2) };
      if (e.type === 'finish') finished = true;
    }
    maxX = Math.max(x, maxX);
    if (finished) break;
  }
  rows.push({ from,to,lean,finished,faults:sim.faults(),time:sim.runTime(),firstFault,maxX:+maxX.toFixed(1) });
}
rows.sort((a,b)=>Number(b.finished)-Number(a.finished)||a.faults-b.faults||b.maxX-a.maxX||a.time-b.time);
for (const r of rows.slice(0,30)) process.stdout.write(`${JSON.stringify(r)}\n`);
