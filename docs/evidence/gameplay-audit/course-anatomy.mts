/** Data-only context for the throttle probe's first fault and authored skill. */
import { readFileSync, writeFileSync } from 'node:fs';
import { compileTrack, ROCKHOP_ALL } from '../../../src/tracks';

const probe = JSON.parse(readFileSync(new URL('./throttle-only.json', import.meta.url), 'utf8')) as {
  rows: { id: string; bike: string; cleared: boolean; firstFault: { reason: string; x: number; checkpoint: number; time: number } | null }[];
};
const rows = ROCKHOP_ALL.map((track) => {
  const compiled = compileTrack(track);
  const results = probe.rows.filter((r) => r.id === track.id).map((r) => {
    const fault = r.firstFault;
    const near = fault ? compiled.placed.map((o) => ({ kind: o.kind, x: o.pos.x, distance: Math.abs(o.pos.x - fault.x) })).sort((a, b) => a.distance - b.distance)[0] : null;
    return { bike: r.bike, cleared: r.cleared, firstFault: fault ? { ...fault, nearestPlaced: near && near.distance <= 10 ? { kind: near.kind, x: +near.x.toFixed(2), distance: +near.distance.toFixed(2) } : null } : null };
  });
  return { id: track.id, tier: track.tier, technique: track.meta?.technique ?? '', demands: track.meta?.demands ?? '', finishX: track.finishX, checkpoints: track.checkpoints.map((c) => c.x), colliders: compiled.colliders.length, hazards: compiled.hazards.length, placed: compiled.placed.length, results };
});
writeFileSync(new URL('./course-anatomy.json', import.meta.url), `${JSON.stringify({ rows }, null, 2)}\n`);
