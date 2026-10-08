/** Exact small bike contact geometry only; no rider loading or pose fitting. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { Matrix4 } from 'three';
import { load, mesh, pinned, sha } from '../selected-ankle-contact02/surface.mjs';
const source = { path: 'docs/evidence/rider-rebuild/selected-authoring-motion11/bike-context01.json', sha256: '3762e8e00ba0d4ce0a78e3a8fdb56a5f9798129d6faa02866d60209492a4f9e5' };
const context = JSON.parse(pinned(source));
const gripPath = 'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/bike-grip-surface02/report.json';
const gripBytes = fs.readFileSync(gripPath), grips = JSON.parse(gripBytes);
assert.equal(sha(gripBytes), '65a910f11f4b008b93baade11008119d7781fbf1126f0fdd00487b9f06d4b394');
const output = process.argv[2]; assert(output && !fs.existsSync(output));
const bikes = [];
for (const bike of context.bikes) {
  const raw = await load(bike.bike), frame = new Matrix4().makeTranslation(...bike.frameOriginFile.map(v => -v));
  const pegs = mesh(raw, 'pegs', frame), bar = mesh(raw, 'handlebar', frame);
  const measured = grips.results.find(r => r.sourceSHA256 === bike.bike.sha256); assert(measured);
  const triangles = (m, ids) => ids.map((rows, index) => ({ sourceRows: rows, sourceOrdinal: index, pointsBike: rows.map(i => m.point(i).toArray()) }));
  bikes.push({ name: bike.name, bike: bike.bike, saddle: bike.saddle,
    pegs: triangles(pegs, Array.from({length: pegs.indices.count/3}, (_, i) => [0,1,2].map(k => pegs.indices.get(i*3+k)))),
    grips: Object.fromEntries(['left','right'].map(side => {
      const old = measured.grips.find(g => g.side === (side === 'left' ? 'R' : 'L')); assert(old);
      return [side, triangles(bar, old.sourceMeshSurface.triangles)];
    })) });
}
fs.writeFileSync(output, JSON.stringify({ accepted:false, status:'EXACT_FINITE_BIKE_SURFACES_UNACCEPTED', context:source,
  gripSelection:{path:gripPath,sha256:sha(gripBytes)}, recipeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),bikes })+'\n',{flag:'wx'});
console.log(JSON.stringify({output,sha256:sha(fs.readFileSync(output)),bikes:bikes.map(b=>({name:b.name,pegTriangles:b.pegs.length,gripTriangles:Object.fromEntries(Object.entries(b.grips).map(([s,t])=>[s,t.length]))}))}));
