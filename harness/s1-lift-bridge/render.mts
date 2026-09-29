/** Geometry budget and visual collision contract for the S1 lift-station bridge. */
import fs from 'node:fs';
import type * as THREE from 'three';
import { compileTrack, getTrack, hashColliders } from '../../src/tracks';
import { MaterialLibrary } from '../../src/render/materials/library';
import { buildObstacles } from '../../src/render/world/obstacles';

const track = compileTrack(getTrack('s1-lift-line')!);
const placed = track.placed.filter((p) =>
  (p.kind === 'open-platform' && p.pos.x === 288) || (p.kind === 'plank' && p.pos.x === 298));
if (placed.length !== 2) throw new Error(`expected station deck and exit; found ${placed.length}`);
const ids = new Set(placed.flatMap((p) => p.colliderIds));
const isolated = { ...track, placed, colliders: track.colliders.filter((c) => ids.has(c.id)), hazards: [] };
const hash = hashColliders(track.colliders);
const lib = new MaterialLibrary(1);
const bridge = buildObstacles(isolated, lib);
const generic = buildObstacles({ ...isolated, def: { ...track.def, id: 'generic-station' } }, lib);
if (hashColliders(track.colliders) !== hash) throw new Error('render altered authored colliders');
if (bridge.triangles > 2500 || bridge.drawCalls > generic.drawCalls + 1) {
  throw new Error(`station model too expensive: ${bridge.triangles} triangles, ${bridge.drawCalls} calls`);
}
let maxTopOverrun = -Infinity;
let lowerIntrusions = 0;
for (const mesh of bridge.group.children as THREE.Mesh[]) {
  const p = mesh.geometry.getAttribute('position');
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    if (x < 288 - 1e-6 || x > 306 + 1e-6) continue;
    const top = x <= 298 ? 4.6 : 4.6 + (x - 298) * Math.tan(-15 * Math.PI / 180);
    maxTopOverrun = Math.max(maxTopOverrun, y - top);
    if (x > 288.5 && x < 305.5 && Math.abs(z) < 1.55 && y < top - 0.7) lowerIntrusions++;
  }
}
if (maxTopOverrun > 0.005 || lowerIntrusions !== 0) {
  throw new Error(`decor intersects riding envelopes: overrun=${maxTopOverrun}, lower intrusions=${lowerIntrusions}`);
}
const report = { collisionHash: hash, stationSegments: placed.length,
  generic: { triangles: generic.triangles, drawCalls: generic.drawCalls },
  bridge: { triangles: bridge.triangles, drawCalls: bridge.drawCalls }, maxTopOverrun, lowerIntrusions };
fs.mkdirSync('docs/evidence/s1-lift-bridge', { recursive: true });
fs.writeFileSync('docs/evidence/s1-lift-bridge/render.json', `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify(report));
