/** Bounded decoded appearance fidelity; no renderer or source construction. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { Vector3 } from 'three';
import { loadRigAt } from '../../../src/render/hero/gltfTestUtils.ts';
import { readGlbChunks } from './metadata.mjs';

const [donorFile, foundationFile, previousFile, candidateFile, outputFile] = process.argv.slice(2);
assert(outputFile && !fs.existsSync(outputFile), 'Need donor/foundation/appearance01/appearance02/fresh-report');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const pins = new Map();
function load(file, expected) {
  const bytes = fs.readFileSync(file); assert.equal(sha(bytes), expected);
  pins.set(file, { sha256: expected, bytes: bytes.length });
  return readGlbChunks(bytes);
}
const donor = load(donorFile, 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754');
const foundation = load(foundationFile, '4092f9aa62c01598888712e7cb879439d9bc8093a82effb2b60a9ec1be85193e');
const previous = load(previousFile, '63f90fb9b5c0e1c7d984f4132643475e27d169bfd4f04be6855dd4cb1d5eb891');
const candidate = load(candidateFile, '5de43580964163bcd5755864543a9a9ab11e32d68af69488e42294e590b8459f');
for (const [file, expected] of [[path.join(path.dirname(previousFile), 'rider.blend'), '249bac21d30d468d15b0b59290d676ecfa3a9e3078ca62e55401cb2a6fa5c4a8'],
  [path.join(path.dirname(candidateFile), 'rider.blend'), '5a4aa0bc6083cb83d3aa1d6b5464c062555f2ac4401c566b4384b7fcb01cb04b']]) {
  const bytes = fs.readFileSync(file); assert.equal(sha(bytes), expected); pins.set(file, { sha256: expected, bytes: bytes.length });
}
function acc(g, index) {
  const a = g.json.accessors[index], v = g.json.bufferViews[a.bufferView];
  assert(!v?.extensions, 'Compressed buffer views require the production decoder');
  const n = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 }[a.type];
  const size = { 5126: 4, 5125: 4, 5123: 2, 5121: 1 }[a.componentType];
  const reader = { 5126: 'readFloatLE', 5125: 'readUInt32LE', 5123: 'readUInt16LE', 5121: 'readUInt8' }[a.componentType];
  assert(n && size && reader);
  const divisor = a.normalized ? { 5125: 4294967295, 5123: 65535, 5121: 255 }[a.componentType] : 1;
  assert(divisor, 'Unsupported normalized component');
  const values = Array.from({ length: a.count }, (_, i) => Array.from({ length: n }, (_, k) => v
    ? g.bin[reader]((v.byteOffset ?? 0) + (a.byteOffset ?? 0) + i * (v.byteStride ?? n * size) + k * size) / divisor : 0));
  if (a.sparse) {
    const s = a.sparse, iv = g.json.bufferViews[s.indices.bufferView], vv = g.json.bufferViews[s.values.bufferView];
    assert(!iv.extensions && !vv.extensions && !iv.byteStride && !vv.byteStride);
    const is = { 5121: 1, 5123: 2, 5125: 4 }[s.indices.componentType];
    const ir = { 5121: 'readUInt8', 5123: 'readUInt16LE', 5125: 'readUInt32LE' }[s.indices.componentType];
    assert(is && ir); let last = -1;
    for (let i = 0; i < s.count; i++) {
      const row = g.bin[ir]((iv.byteOffset ?? 0) + (s.indices.byteOffset ?? 0) + i * is);
      assert(row > last && row < a.count); last = row;
      values[row] = Array.from({ length: n }, (_, k) => g.bin[reader]((vv.byteOffset ?? 0) + (s.values.byteOffset ?? 0) + (i * n + k) * size) / divisor);
    }
  }
  return values;
}
const digest = a => sha(Buffer.from(Float64Array.from(a.flat()).buffer));
const parents = g => new Map(g.json.nodes.flatMap((n, i) => (n.children ?? []).map(c => [c, i])));
function rig(g) {
  assert.equal(g.json.skins.length, 1);
  const s = g.json.skins[0], parent = parents(g);
  return { names: s.joints.map(i => g.json.nodes[i].name),
    joints: s.joints.map(i => {
      const n = g.json.nodes[i];
      return { name: n.name, parent: g.json.nodes[parent.get(i)]?.name,
        matrix: n.matrix ?? null, translation: n.translation ?? [0, 0, 0],
        rotation: n.rotation ?? [0, 0, 0, 1], scale: n.scale ?? [1, 1, 1] };
    }), inverseBinds: acc(g, s.inverseBindMatrices) };
}
const referenceRig = rig(foundation), actualRig = rig(candidate);
assert.equal(actualRig.names.length, 51); assert.deepEqual(actualRig, referenceRig);
assert.deepEqual(rig(previous), referenceRig);
const scopes = candidate.json.nodes.flatMap((n, index) => {
  if (n.skin === undefined) return [];
  let owner = index; const parent = parents(candidate);
  while (owner !== undefined && !Object.hasOwn(candidate.json.nodes[owner].extras ?? {}, 'rockhopRiderSkinConditioned')) owner = parent.get(owner);
  assert(owner !== undefined); assert.equal(candidate.json.nodes[owner].extras.rockhopRiderSkinConditioned, 1);
  return [{ mesh: n.name, owner, ownerName: candidate.json.nodes[owner].name }];
});
assert.equal(scopes.length, 8);
function primitiveSignature(g, p) {
  return { attrs: Object.fromEntries(Object.entries(p.attributes).map(([name, index]) => [name, digest(acc(g, index))])),
    index: digest(acc(g, p.indices)),
    targets: (p.targets ?? []).map(t => Object.fromEntries(Object.entries(t).map(([name, index]) => [name, digest(acc(g, index))]))) };
}
const changes = candidate.json.meshes.map((m, i) => {
  const old = previous.json.meshes[i]; assert.equal(m.name, old.name); assert.equal(m.primitives.length, 1);
  const before = primitiveSignature(previous, old.primitives[0]), after = primitiveSignature(candidate, m.primitives[0]);
  const changed = Object.keys(after.attrs).filter(k => after.attrs[k] !== before.attrs[k]);
  assert.equal(after.index, before.index); assert.deepEqual(after.targets, before.targets);
  if (i !== 7) assert.deepEqual(after, before, 'Unexpected non-boot change');
  else assert(changed.every(k => ['POSITION', 'NORMAL', 'JOINTS_0', 'WEIGHTS_0'].includes(k)));
  return { mesh: m.name, changedAttributes: changed, unchangedIndexAndTargets: true };
});
const garments = [1, 2].map(i => {
  const before = primitiveSignature(foundation, foundation.json.meshes[i].primitives[0]);
  const after = primitiveSignature(candidate, candidate.json.meshes[i].primitives[0]);
  assert.deepEqual(after, before, 'Original corrective garment changed');
  return { mesh: candidate.json.meshes[i].name, signature: after };
});
function image(g, index) {
  const im = g.json.images[index], v = g.json.bufferViews[im.bufferView];
  const bytes = g.bin.subarray(v.byteOffset ?? 0, (v.byteOffset ?? 0) + v.byteLength);
  return { mime: im.mimeType, bytes: bytes.length, sha256: sha(bytes) };
}
assert.deepEqual(candidate.json.images.map((_, i) => image(candidate, i)), previous.json.images.map((_, i) => image(previous, i)));
function material(g, index) {
  const m = structuredClone(g.json.materials[index]); delete m.name;
  function replace(o) {
    for (const [k, v] of Object.entries(o)) {
      if (k.endsWith('Texture')) {
        const tex = g.json.textures[v.index];
        o[k] = { ...v, index: image(g, tex.source), sampler: g.json.samplers?.[tex.sampler] ?? null };
      } else if (v && typeof v === 'object') replace(v);
    }
  }
  replace(m); return m;
}
const materialFidelity = [[1, 6], [2, 4], [3, 5], [4, 3]].map(([di, ci]) => {
  const original = material(donor, di), current = material(candidate, ci);
  return { donorMaterial: di, candidateMaterial: ci, original, current,
    sameBaseColorImageBytes: original.pbrMetallicRoughness.baseColorTexture.index.sha256 === current.pbrMetallicRoughness.baseColorTexture.index.sha256,
    originalSpecularFactor: original.extensions?.KHR_materials_specular?.specularFactor ?? 1,
    currentSpecularFactor: current.extensions?.KHR_materials_specular?.specularFactor ?? 1 };
});
function compareProtectedPart(donorPrimitive, candidateMesh) {
  const a = donor.json.meshes[1].primitives[donorPrimitive], b = candidate.json.meshes[candidateMesh].primitives[0];
  const dp = acc(donor, a.attributes.POSITION), du = acc(donor, a.attributes.TEXCOORD_0), dn = acc(donor, a.attributes.NORMAL);
  const cp = acc(candidate, b.attributes.POSITION), cu = acc(candidate, b.attributes.TEXCOORD_0), cn = acc(candidate, b.attributes.NORMAL);
  const sourceIndex = acc(donor, a.indices).flat(), sourceUsed = new Set(), sourceTriangles = [];
  for (let i = 0; i < sourceIndex.length; i += 3) {
    const t = sourceIndex.slice(i, i + 3);
    if (t.every(id => dp[id][1] >= 1.525)) { sourceTriangles.push(t); t.forEach(id => sourceUsed.add(id)); }
  }
  const buckets = new Map(), key = p => p.map(x => Math.floor(x / 1e-5)).join(',');
  for (const id of sourceUsed) { const k = key(dp[id]), ids = buckets.get(k) ?? []; ids.push(id); buckets.set(k, ids); }
  assert.equal(cp.length, sourceUsed.size);
  let ambiguous = 0, maxPositionM = 0, maxUVDifference = 0, changedOverPointOneDegrees = 0, flipped = 0, maxAngleDegrees = 0;
  const mapping = [], witnesses = [];
  for (let i = 0; i < cp.length; i++) {
    const q = cp[i].map(x => Math.floor(x / 1e-5)), hits = [];
    for (let x = -1; x <= 1; x++) for (let y = -1; y <= 1; y++) for (let z = -1; z <= 1; z++)
      for (const id of buckets.get([q[0] + x, q[1] + y, q[2] + z].join(',')) ?? []) {
        const positionM = Math.hypot(...cp[i].map((v, k) => v - dp[id][k]));
        const uvDifference = Math.hypot(...cu[i].map((v, k) => v - du[id][k]));
        if (positionM < 1e-6 && uvDifference < 1e-7) {
          const dot = dn[id].reduce((sum, v, k) => sum + v * cn[i][k], 0) / (Math.hypot(...dn[id]) * Math.hypot(...cn[i]));
          hits.push({ id, positionM, uvDifference, angleDegrees: Math.acos(Math.max(-1, Math.min(1, dot))) * 180 / Math.PI, dot });
        }
      }
    assert(hits.length, 'Missing protected source position/UV row');
    if (hits.length > 1) ambiguous++;
    // Minimum over indistinguishable position/UV rows is conservative, not an ancestry proof.
    hits.sort((a, b) => a.angleDegrees - b.angleDegrees); const h = hits[0]; mapping.push(h.id);
    maxPositionM = Math.max(maxPositionM, h.positionM); maxUVDifference = Math.max(maxUVDifference, h.uvDifference);
    maxAngleDegrees = Math.max(maxAngleDegrees, h.angleDegrees); if (h.angleDegrees > .1) changedOverPointOneDegrees++;
    if (h.dot < 0) flipped++;
    witnesses.push({ sourceID: h.id, candidateRow: i, angleDegrees: h.angleDegrees, matches: hits.length,
      sourcePosition: dp[h.id], sourceNormal: dn[h.id], candidateNormal: cn[i] });
  }
  let triangleWinding = 'Not certified: duplicate source-position/UV matches remain';
  if (!ambiguous) {
    const order = (a, b) => a.localeCompare(b);
    const triangleKey = t => [t, [t[1], t[2], t[0]], [t[2], t[0], t[1]]].map(x => x.join(',')).sort(order)[0];
    const indices = acc(candidate, b.indices).flat(), triangles = [];
    for (let i = 0; i < indices.length; i += 3) triangles.push(indices.slice(i, i + 3).map(id => mapping[id]));
    assert.deepEqual(triangles.map(triangleKey).sort(order), sourceTriangles.map(triangleKey).sort(order));
    triangleWinding = 'Exact source triangle multiset including orientation';
  }
  witnesses.sort((a, b) => b.angleDegrees - a.angleDegrees);
  return { mesh: candidate.json.meshes[candidateMesh].name, vertices: cp.length, sourceTriangles: sourceTriangles.length,
    sourceUsedIDsSHA256: sha(Buffer.from(Uint32Array.from([...sourceUsed].sort((a, b) => a - b)).buffer)),
    maxPositionM, maxUVDifference, ambiguousSourceMatches: ambiguous, normalsChangedOverPointOneDegrees: changedOverPointOneDegrees,
    maximumNormalAngleDegrees: maxAngleDegrees, oppositeHemisphereNormals: flipped, triangleWinding, witnesses: witnesses.slice(0, 5),
    comparisonFrame: 'Decoded primitive attribute frame; historical donor root/game adapter is deliberately not reapplied.' };
}
const protectedParts = [compareProtectedPart(0, 5), compareProtectedPart(1, 3)];
const loaded = await loadRigAt(pathToFileURL(path.resolve(candidateFile)), true);
loaded.scene.updateMatrixWorld(true); const actualRestClosure = [], point = new Vector3();
loaded.scene.traverse(mesh => {
  if (!mesh.isSkinnedMesh) return;
  mesh.skeleton.update(); const p = mesh.geometry.getAttribute('position');
  let maxResidualM = 0; const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < p.count; i++) {
    mesh.getVertexPosition(i, point).applyMatrix4(mesh.matrixWorld);
    maxResidualM = Math.max(maxResidualM, Math.hypot(point.x - p.getX(i), point.y - p.getY(i), point.z - p.getZ(i)));
    [point.x, point.y, point.z].forEach((v, k) => { min[k] = Math.min(min[k], v); max[k] = Math.max(max[k], v); });
  }
  assert(maxResidualM < 2e-6, 'Actual rest bind does not cancel');
  assert.deepEqual(mesh.skeleton.bones.map(b => b.name), referenceRig.names.map(n => n.replaceAll('.', '')));
  actualRestClosure.push({ mesh: mesh.name, vertices: p.count, maxResidualM, worldBoundsM: [min, max], bindMatrix: mesh.bindMatrix.toArray() });
});
assert.equal(actualRestClosure.length, 8);
const report = { status: 'UNACCEPTED_APPEARANCE02_PROTECTED_NORMAL_MATERIAL_FIDELITY_DRIFT', pins: Object.fromEntries(pins),
  decoderPins: Object.fromEntries(['harness/hero-remaster/user-agent3-2026-10-03/appearance.mjs',
    'harness/hero-remaster/user-agent3-2026-10-03/metadata.mjs', 'src/render/hero/gltfTestUtils.ts'].map(file => [file, sha(fs.readFileSync(file))])),
  skin: { completeJointCount: 51, exactNamedHierarchyRestAndInverseBinds: true, rigSHA256: sha(Buffer.from(JSON.stringify(actualRig))), scopes },
  appearance01To02: { meshes: changes, allEmbeddedImagesUnchanged: true, leatherMetallicFactor: candidate.json.materials[6].pbrMetallicRoughness.metallicFactor },
  garments, protectedParts, materialFidelity, actualRestClosure,
  canonicalSkin: candidate.json.materials[0],
  limits: ['Decoded geometry/material inspection only; no new capture, rendered highlight, skin-color match, whole-rider acceptance or supported contact claim.',
    'Production prepareHero flattens physical/specular extensions; source GLB specular drift is not a measured Garage highlight difference.',
    'Body preservation in the hidden native master remains builder evidence; exported visible body intentionally has a head-interface cut.',
    'Actual GLTFLoader rest-bind check omits images in memory; source PNG bytes and material descriptors inspected separately, not rendered.',
    'Current receipt does not certify ambiguous head-row ancestry, unsampled deformation, dynamic accessory fit, moving native/render parity or mobile LOD.'] };
fs.mkdirSync(path.dirname(outputFile), { recursive: true }); fs.writeFileSync(outputFile, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ status: report.status, joints: 51, protectedParts: protectedParts.map(({ witnesses: _w, ...p }) => p),
  materialFactors: materialFidelity.map(m => [m.donorMaterial, m.originalSpecularFactor, m.currentSpecularFactor]) }));
