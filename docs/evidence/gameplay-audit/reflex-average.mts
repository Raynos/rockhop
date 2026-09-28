/** Human-limited controller sweep, outputs only to this audit directory. */
import { writeFileSync } from 'node:fs';
import { createSim } from '../../../harness/lib/sim';
import { playReflex } from '../../../harness/reflex/play';
import { ROCKHOP_ALL } from '../../../src/tracks';

const rows = [];
const only = process.env.AUDIT_ONLY?.split(',').filter(Boolean) ?? null;
for (const track of ROCKHOP_ALL) {
  if (only && !only.includes(track.id)) continue;
  for (const bike of ['rookie', 'pro'] as const) {
    for (let k = 0; k < 3; k++) {
      const seed = (track.seed + k) >>> 0;
      const sim = await createSim(track.id, seed, 120, { bike });
      const res = playReflex(sim, { skill: 'average', seed, attemptsCap: 50, maxSimSeconds: track.tier === 'extreme' ? 600 : 300 });
      const row = { id: track.id, bike, seed, outcome: res.outcome, attempts: res.attempts, finishTime: res.finishTime, maxPct: +(100 * res.maxX / track.finishX).toFixed(1), faults: res.faults.length, firstFault: res.faults[0] ? { reason: res.faults[0].reason, x: +res.faults[0].x.toFixed(2), rule: res.faults[0].rule } : null, finalHash: res.finalHash };
      rows.push(row);
      process.stdout.write(`${row.id.padEnd(20)} ${bike.padEnd(6)} seed+${k} ${row.outcome.padEnd(11)} attempts=${String(row.attempts).padStart(2)} max=${String(row.maxPct).padStart(5)}%\n`);
    }
  }
}
writeFileSync(new URL('./reflex-average.json', import.meta.url), `${JSON.stringify({ method: 'reflex average; 180–220ms reaction, 25Hz glance, binary controls; three seeds per course and bike; 50-attempt, 300s cap (600s extreme)', rows }, null, 2)}\n`);
