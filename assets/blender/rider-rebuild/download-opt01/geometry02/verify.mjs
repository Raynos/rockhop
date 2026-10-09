// Independent complete vertex/remapped-triangle and bounded precision proof.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { MeshoptDecoder as ThreeDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { openGlb, viewBytes, accessorBytes, indexValues, sha, fileSha, readAt } from '../geometry01/glb.mjs';

const [originalPath, packedPath, packPath, proofPath] = process.argv.slice(2);
assert(originalPath && packedPath && packPath && proofPath);
const start = performance.now(), original = openGlb(originalPath), packed = openGlb(packedPath);
const a = original.json, b = packed.json, recipe = JSON.parse(fs.readFileSync(packPath));
assert.equal(fileSha(originalPath), recipe.source.sha256);
assert.equal(fileSha(packedPath), recipe.output.sha256);
const accessorMap = recipe.accessorMap, viewMap = recipe.viewMap;
const expected = structuredClone(a);
for (const m of expected.meshes) for (const p of m.primitives) {
  p.indices = accessorMap[p.indices];
  for (const semantic of Object.keys(p.attributes)) {
    if (['_NATIVE_ID', '_SOURCE_VERTEX_ID', '_REGION_ID'].includes(semantic)) delete p.attributes[semantic];
    else p.attributes[semantic] = accessorMap[p.attributes[semantic]];
  }
}
for (const skin of expected.skins) skin.inverseBindMatrices = accessorMap[skin.inverseBindMatrices];
for (const animation of expected.animations) for (const sampler of animation.samplers) {
  sampler.input = accessorMap[sampler.input]; sampler.output = accessorMap[sampler.output];
}
for (const image of expected.images) image.bufferView = viewMap[image.bufferView];
const storageKeys = new Set(['buffers', 'bufferViews', 'accessors', 'extensionsUsed', 'extensionsRequired']);
const metadata = {};
for (const key of Object.keys(expected).filter(k => !storageKeys.has(k))) {
  assert.deepEqual(expected[key], b[key], `Metadata changed: ${key}`);
  metadata[key] = { identicalAfterStorageReferenceRemap: true, sha256: sha(Buffer.from(JSON.stringify(b[key]))) };
}
const proof = { schema: 'rider-runtime-bounded-parity/v1', pass: false,
  source: recipe.source, output: recipe.output, metadata, primitives: [],
  unchangedAccessors: [], images: [], productionDecoderViews: [],
  omittedProvenance: recipe.provenance,
  thresholds: recipe.constraints };

// A linear skin applies the exact same joints/weights to original and derivative.
// For any translation or rotation of each native joint, vertex error is bounded
// by sum(weight * ||jointLinear * inverseBindLinear||) * position error.
// Products of local max scale magnitudes bound every rotation of the hierarchy.
const parent = new Map();
for (const [i, node] of a.nodes.entries()) for (const child of node.children ?? []) parent.set(child, i);
const maxScale = a.nodes.map(node => Math.max(...(node.scale ?? [1, 1, 1]).map(Math.abs)));
for (const animation of a.animations) {
  for (const channel of animation.channels) {
    if (channel.target.path !== 'scale') continue;
    const sampler = animation.samplers[channel.sampler];
    assert.equal(sampler.interpolation ?? 'LINEAR', 'LINEAR', 'Scale spline needs a separate bound');
    const bytes = await accessorBytes(original, sampler.output);
    const values = new Float32Array(bytes.buffer, bytes.byteOffset, bytes.length / 4);
    for (const value of values) maxScale[channel.target.node] = Math.max(maxScale[channel.target.node], Math.abs(value));
  }
}
const bind = await accessorBytes(original, a.skins[0].inverseBindMatrices);
const bindFloats = new Float32Array(bind.buffer, bind.byteOffset, bind.length / 4);
const jointBounds = a.skins[0].joints.map((nodeIndex, joint) => {
  let hierarchyScale = 1, current = nodeIndex;
  while (current !== undefined) {
    assert(!a.nodes[current].matrix, 'Matrix nodes require an explicit spectral bound');
    hierarchyScale *= maxScale[current]; current = parent.get(current);
  }
  let squaredFrobenius = 0;
  for (const k of [0, 1, 2, 4, 5, 6, 8, 9, 10]) squaredFrobenius += bindFloats[joint * 16 + k] ** 2;
  return { joint, nodeIndex, name: a.nodes[nodeIndex].name,
    hierarchyScaleBound: hierarchyScale,
    inverseBindLinearFrobenius: Math.sqrt(squaredFrobenius),
    linearOperatorBound: hierarchyScale * Math.sqrt(squaredFrobenius) };
});
const geometryAccessors = new Set();
let worstSkinBound = 0, totalVertices = 0, totalCorners = 0;
for (const row of recipe.primitives) {
  const pA = a.meshes[row.mesh].primitives[row.primitive], pB = b.meshes[row.mesh].primitives[row.primitive];
  const mapPath = path.join(path.dirname(packedPath), row.sourceRemap.file);
  const mapBytes = fs.readFileSync(mapPath);
  assert.equal(sha(mapBytes), row.sourceRemap.sha256);
  const remap = new Uint32Array(mapBytes.buffer, mapBytes.byteOffset, mapBytes.length / 4);
  const ixA = indexValues(await accessorBytes(original, pA.indices), a.accessors[pA.indices]);
  const ixB = indexValues(await accessorBytes(packed, pB.indices), b.accessors[pB.indices]);
  assert.equal(ixA.length, ixB.length);
  for (let i = 0; i < ixA.length; i++) assert.equal(remap[ixA[i]], ixB[i], 'Triangle corner mapping changed');
  geometryAccessors.add(pA.indices);
  const result = { mesh: row.mesh, primitive: row.primitive, name: row.name,
    originalVertices: remap.length, runtimeVertices: row.uniqueVertices,
    triangleCount: ixA.length / 3, cornerOrderPreserved: true,
    indicesMappedExactly: true, attributes: [], maxSkinErrorBoundMeters: 0 };
  let positionErrors;
  for (const [semantic, oldIndex] of Object.entries(pA.attributes)) {
    if (semantic.startsWith('_')) continue;
    geometryAccessors.add(oldIndex);
    const newIndex = pB.attributes[semantic], oldAc = a.accessors[oldIndex], newAc = b.accessors[newIndex];
    const before = await accessorBytes(original, oldIndex), after = await viewBytes(packed, newAc.bufferView);
    const beforeData = new DataView(before.buffer, before.byteOffset, before.byteLength);
    const afterData = new DataView(after.buffer, after.byteOffset, after.byteLength);
    const width = { VEC2: 2, VEC3: 3, VEC4: 4 }[oldAc.type];
    const oldStride = before.length / oldAc.count;
    const newStride = b.bufferViews[newAc.bufferView].byteStride ?? after.length / newAc.count;
    let maxError = 0;
    if (semantic === 'POSITION') positionErrors = new Float64Array(remap.length);
    for (let v = 0; v < remap.length; v++) {
      assert(remap[v] < newAc.count);
      if (semantic === 'JOINTS_0' || semantic === 'WEIGHTS_0') {
        assert(before.subarray(v * oldStride, (v + 1) * oldStride)
          .equals(after.subarray(remap[v] * newStride, (remap[v] + 1) * newStride)), `Skin field changed: ${semantic}`);
        continue;
      }
      let errorSquared = 0, dot = 0, beforeSquared = 0, afterSquared = 0;
      for (let k = 0; k < width; k++) {
        const x = beforeData.getFloat32(v * oldStride + k * 4, true);
        const offset = remap[v] * newStride;
        const y = newAc.componentType === 5126 ? afterData.getFloat32(offset + k * 4, true)
          : newAc.componentType === 5122 ? Math.max(-1, afterData.getInt16(offset + k * 2, true) / 32767)
          : afterData.getUint16(offset + k * 2, true) / 65535;
        assert(Number.isFinite(y));
        errorSquared += (y - x) ** 2;
        dot += x * y; beforeSquared += x * x; afterSquared += y * y;
      }
      const error = semantic === 'NORMAL' && beforeSquared && afterSquared
        ? Math.acos(Math.min(1, Math.max(-1, dot / Math.sqrt(beforeSquared * afterSquared)))) * 180 / Math.PI
        : Math.sqrt(errorSquared);
      maxError = Math.max(maxError, error);
      if (positionErrors) {
        if (semantic === 'POSITION') positionErrors[v] = error;
      }
    }
    if (semantic === 'POSITION') assert(maxError < 0.00005);
    if (semantic === 'NORMAL') assert(maxError < 0.1);
    if (semantic === 'TEXCOORD_0') assert(maxError * 4096 < 0.25);
    result.attributes.push({ semantic, sourceAccessor: oldIndex, runtimeAccessor: newIndex,
      allSourceVerticesChecked: true, maxError,
      ...(semantic === 'TEXCOORD_0' ? { maxTexelErrorAt4096: maxError * 4096 } : {}),
      ...(semantic === 'JOINTS_0' || semantic === 'WEIGHTS_0' ? { exactBytesThroughRemap: true } : {}) });
  }
  const joints = await accessorBytes(original, pA.attributes.JOINTS_0);
  const weightsBytes = await accessorBytes(original, pA.attributes.WEIGHTS_0);
  const weights = new Float32Array(weightsBytes.buffer, weightsBytes.byteOffset, weightsBytes.length / 4);
  for (let v = 0; v < remap.length; v++) {
    let bound = 0;
    for (let slot = 0; slot < 4; slot++) {
      assert(weights[v * 4 + slot] >= 0);
      bound += weights[v * 4 + slot] * jointBounds[joints[v * 4 + slot]].linearOperatorBound;
    }
    result.maxSkinErrorBoundMeters = Math.max(result.maxSkinErrorBoundMeters, bound * positionErrors[v]);
  }
  assert(result.maxSkinErrorBoundMeters < 0.00005);
  worstSkinBound = Math.max(worstSkinBound, result.maxSkinErrorBoundMeters);
  proof.primitives.push(result); totalVertices += remap.length; totalCorners += ixA.length;
  console.log(JSON.stringify({ verifiedMesh: row.mesh, primitive: row.primitive,
    skinErrorBoundMeters: result.maxSkinErrorBoundMeters }));
}
for (const [oldString, newIndex] of Object.entries(accessorMap)) {
  const oldIndex = Number(oldString);
  if (geometryAccessors.has(oldIndex)) continue;
  const oldAc = structuredClone(a.accessors[oldIndex]);
  oldAc.bufferView = viewMap[oldAc.bufferView];
  assert.deepEqual(oldAc, b.accessors[newIndex]);
  const bytesA = await accessorBytes(original, oldIndex), bytesB = await accessorBytes(packed, newIndex);
  assert(bytesA.equals(bytesB), `Non-geometry accessor changed: ${oldIndex}`);
  proof.unchangedAccessors.push({ sourceAccessor: oldIndex, runtimeAccessor: newIndex,
    bytes: bytesA.length, sha256: sha(bytesA), exactByteEquality: true });
}
for (const [i, image] of a.images.entries()) {
  const before = await viewBytes(original, image.bufferView), after = await viewBytes(packed, b.images[i].bufferView);
  assert(before.equals(after)); proof.images.push({ image: i, bytes: before.length,
    sha256: sha(before), exactByteEquality: true });
}
await ThreeDecoder.ready;
for (const [viewIndex, view] of b.bufferViews.entries()) {
  const ext = view.extensions?.EXT_meshopt_compression;
  if (!ext) continue;
  const expectedBytes = await viewBytes(packed, viewIndex), decoded = Buffer.alloc(view.byteLength);
  ThreeDecoder.decodeGltfBuffer(decoded, ext.count, ext.byteStride,
    readAt(packed.fd, ext.byteLength, packed.binOffset + ext.byteOffset), ext.mode, ext.filter);
  assert(expectedBytes.equals(decoded));
  proof.productionDecoderViews.push({ view: viewIndex, bytes: view.byteLength, exactByteEquality: true });
}
proof.skinBound = { kind: 'Complete native joint hierarchy linear-operator upper bound',
  allSourceVertices: totalVertices, allOrderedTriangleCorners: totalCorners,
  allNativeJoints: jointBounds.length, joints: jointBounds,
  maxPositionDeformationErrorMeters: worstSkinBound,
  covers: 'Any native driver joint rotations/translations with original scales, plus source authored LINEAR scale tracks and their interpolation',
  excluded: 'Unmeasured alternate assets or future drivers that increase bone scales beyond the recorded per-node bound',
  nativeDriverSource: 'src/render/hero/selected/rider.mjs uses rest-scale reset and rotation/translation only' };
proof.pass = true; proof.elapsedSeconds = (performance.now() - start) / 1000;
proof.peakRssBytes = process.resourceUsage().maxRSS * 1024;
fs.writeFileSync(proofPath, `${JSON.stringify(proof, null, 2)}\n`);
fs.closeSync(original.fd); fs.closeSync(packed.fd);
console.log(JSON.stringify({ pass: true, skinBoundMeters: worstSkinBound,
  elapsedSeconds: proof.elapsedSeconds, peakRssBytes: proof.peakRssBytes }));
