/** Real input pins and binary layouts for the surface67 successor. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, pinned, sha } from '../selected-production-constructor37/construct.mjs';
export { ROOT, pinned, sha };
export const ACTUAL62 = { path: 'harness/out/rider-rebuild/selected-boot-closure62/candidate01/constructor.json', sha256: 'e264a3df52483c996b0f298b6174a5730766ea2ef07465bf36293fddf199fc52' };
export const FINDING66 = { path: 'docs/evidence/rider-rebuild/selected-boot-face66/finding.json', sha256: '4fe77385f9b912c26ebe6448ad800f90bc94d82a695f74605fbcbaf4ed77bbae' };
export const REFERENCE = { path: 'docs/evidence/rider-rebuild/selected-boot-surface67/native-reference.json', sha256: '108803b54e065e2625dcc00ae524e254365bd8c5e27147462bf65b1c854a37ae' };
export const ANCESTRY = [
  ['selected-production-constructor37/construct.mjs', '3d7ec9faa6d8f10140591c4303012f9ecba69c8d7dd6284d3b851052bbe3d741'],
  ['selected-boot-fan59/construct.mjs', 'ff1328930687d5eb8e7b1c0e7f5961e2fac11f911e88d0e4224fa5e37f1c571f'],
  ['selected-boot-closure62/closure.mjs', '89cb51a5d9587a0c6726ab65d7678b9e0072756d16973dab3263e96e849ce294'],
].map(([p, sha256]) => ({ path: `assets/blender/rider-rebuild/${p}`, sha256 }));
export function verifyImports() { ANCESTRY.forEach(pinned); }
export function readJSON(pin) { return JSON.parse(pinned(pin).data); }
export function arrays(pin) {
  const { data } = pinned(pin), out = {}; let offset = 0;
  for (const [name, row] of Object.entries(pin.layout)) {
    const count = row.count ?? row.shape.reduce((a, b) => a * b, 1);
    assert(Number.isSafeInteger(count) && count >= 0 && row.byteOffset === offset && row.byteLength === count * 4);
    const C = { '<f4': Float32Array, '<i4': Int32Array, '<u4': Uint32Array }[row.dtype]; assert(C);
    out[name] = new C(data.buffer, data.byteOffset + offset, count); offset += row.byteLength;
  }
  assert.equal(offset, data.length); return out;
}
export const filePin = file => ({ path: path.relative(ROOT, file), sha256: sha(fs.readFileSync(file)) });
export function actualInput() {
  verifyImports(); const receipt = readJSON(ACTUAL62), source = arrays(receipt.sourceArrayPackage), candidate = arrays(receipt.candidate);
  const returned = arrays(receipt.returnedOriginalIndices).triangles;
  assert.equal(receipt.targetTriangles, 26528); assert.equal(returned.length, 26528 * 3);
  assert.deepEqual(Uint32Array.from(candidate.triangles, i => candidate.originalVertexIds[i]), returned);
  const a = { positions: source.positions, triangles: Uint32Array.from(source.triangles), normals: source.vertexNormals };
  return { receipt, a, candidate, returned };
}
