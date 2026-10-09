/** Read-only original37/59/62 source constraints; never imports a simplifier. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { topology, pinned, sha } from '../selected-production-constructor37/construct.mjs';
import { protectFans, fanRetention } from '../selected-boot-fan59/construct.mjs';
import { fanClosure } from '../selected-boot-closure62/closure.mjs';

const m = JSON.parse(fs.readFileSync(process.argv[2])), data = fs.readFileSync(m.binary), a = {};
for (const p of m.helpers) pinned(p);
for (const [name, r] of Object.entries(m.layout)) {
  const C = r.dtype === '<f4' ? Float32Array : r.dtype === '<i4' ? Int32Array : Uint32Array;
  a[name] = new C(data.buffer, data.byteOffset + r.byteOffset, r.count);
}
a.names = m.names; a.uv = m.uv.map((name, i) => ({ name, values: a['uv'+i] }));
a.triangles = Uint32Array.from(a.triangles);
const sourceSHA = sha(data);
try {
const t = topology(a), protection = fanClosure(a, m.centers), fan = protectFans(a, t, protection);
const exactSourceFan = fanRetention(a, a.triangles, protection);
assert(exactSourceFan.passed); assert.equal(sha(data), sourceSHA);
console.log(JSON.stringify({ sourcePreconditionsPassed: true, topology: t.report, semanticAndSingularFans: fan,
  exactSourceFanReproduction: exactSourceFan,
  allocationPreconditions: { exactFanFaces: protection.requiredSourceFaceIds.length,
    lockedVertexTriangleLowerBound: Math.ceil(fan.totalLockedVertices / 3),
    full8000: protection.requiredSourceFaceIds.length <= 8000 && Math.ceil(fan.totalLockedVertices / 3) <= 8000,
    lod3500: protection.requiredSourceFaceIds.length <= 3500 && Math.ceil(fan.totalLockedVertices / 3) <= 3500 },
  candidateAttempts: 0, sourceGeometryOrFieldsMutated: false }));
} catch (error) {
  assert.equal(sha(data), sourceSHA);
  console.log(JSON.stringify({ sourcePreconditionsPassed: false, failure: String(error.stack || error),
    candidateAttempts: 0, sourceGeometryOrFieldsMutated: false }));
}
