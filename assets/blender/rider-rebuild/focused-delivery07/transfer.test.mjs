// Metadata-proof parser tests only; no candidate, decode job or browser.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { openGlb } from '../download-opt01/geometry01/glb.mjs';
import { BASELINE, AUTHORING, AUTHORING_CONTRACT, PROFILE, RAW, RUNTIME,
  sha, validateCuffParity, validateCuffTransfer } from './transfer.mjs';

const glb = openGlb('harness/out/rider-rebuild/mobile-textures02/combined01/rider.glb');
const baseline = glb.json; fs.closeSync(glb.fd);
const candidate = structuredClone(baseline);
const changed = ['POSITION', 'NORMAL', 'TANGENT'].map(semantic => {
  const accessor = baseline.meshes[5].primitives[0].attributes[semantic];
  candidate.accessors[accessor].bufferView = candidate.bufferViews.length;
  candidate.bufferViews.push(structuredClone(baseline.bufferViews[baseline.accessors[accessor].bufferView]));
  return { mesh: 5, semantic, accessor, count: baseline.accessors[accessor].count,
    changedRows: 1, beforeDecodedSHA256: 'a'.repeat(64), afterDecodedSHA256: 'b'.repeat(64) };
});
const protectedRows = baseline.accessors.flatMap((accessor, index) => changed.some(row => row.accessor === index) ? [] : [{
  accessor: index, count: accessor.count, type: accessor.type, componentType: accessor.componentType,
  normalized: accessor.normalized ?? false, exact: true,
  beforeDecodedSHA256: 'c'.repeat(64), afterDecodedSHA256: 'c'.repeat(64),
}]);
const protectedMap = new Map(protectedRows.map(row => [row.accessor, row]));
const fixture = { schema: 'selected-cuff-source-parity-v1', accepted: false,
  baseline: { sha256: BASELINE }, candidate: { sha256: 'd'.repeat(64) },
  nativeRigAndAnimationJSONExact: true, protectedNativeAccessorBytesExact: true,
  materialsTexturesImagesJSONExact: true, originalBINPayloadPrefixExact: true,
  unchangedGloveAccessorBytesExact: true, allOtherAccessorBytesExact: true,
  nativeJSONRecordsExact: Object.fromEntries(['nodes', 'skins', 'scenes', 'animations', 'materials', 'textures', 'images', 'samplers']
    .map(key => [key, { exact: true, beforeSHA256: sha(JSON.stringify(baseline[key] ?? [])),
      afterSHA256: sha(JSON.stringify(candidate[key] ?? [])) }])),
  changedAccessors: changed, protectedAccessorStreamsExact: protectedRows,
  unchangedGloveAccessorStreamsExact: [2, 3].flatMap(mesh => baseline.meshes[mesh].primitives.flatMap((primitive, index) =>
    [...Object.entries(primitive.attributes), ['indices', primitive.indices]].map(([semantic, accessor]) =>
      ({ ...protectedMap.get(accessor), mesh, primitive: index, semantic })))),
  imagePayloadsExact: baseline.images.map((image, index) => ({ image: index, bufferView: image.bufferView,
    bytes: baseline.bufferViews[image.bufferView].byteLength, exact: true,
    beforeSHA256: 'e'.repeat(64), afterSHA256: 'e'.repeat(64) })),
};
const rejects = change => { const proof = structuredClone(fixture); change(proof);
  assert.throws(() => validateCuffParity(proof, baseline, candidate)); };

test('complete declared metadata proof has exact full coverage', () => {
  const result = validateCuffParity(fixture, baseline, candidate);
  assert.equal(result.nativeJoints, 75); assert.equal(result.gloveStreams, 14);
  assert.equal(result.protectedAccessors + result.changedAccessors.length, baseline.accessors.length);
});
test('reject missing texture payload certificate', () => rejects(proof => proof.imagePayloadsExact.pop()));
test('reject missing glove field certificate', () => rejects(proof => proof.unchangedGloveAccessorStreamsExact.pop()));
test('reject mismatched glove certificate hash', () => rejects(proof => proof.unchangedGloveAccessorStreamsExact[0].afterDecodedSHA256 = 'f'.repeat(64)));
test('reject wrong baseline lineage hash', () => rejects(proof => proof.baseline.sha256 = 'f'.repeat(64)));
test('reject unknown changed stream', () => rejects(proof => proof.changedAccessors[0].semantic = 'TEXCOORD_0'));
test('reject omitted protected accessor', () => rejects(proof => proof.protectedAccessorStreamsExact.pop()));
test('reject altered native records despite true exact flags', () => {
  const corrupted = structuredClone(candidate); corrupted.nodes[0].translation = [9, 9, 9];
  assert.throws(() => validateCuffParity(fixture, baseline, corrupted));
});
test('reject altered texture metadata despite payload flags', () => {
  const corrupted = structuredClone(candidate); corrupted.images[0].bufferView++;
  assert.throws(() => validateCuffParity(fixture, baseline, corrupted));
});

const wrapper = () => {
  const parity = structuredClone(fixture);
  parity.sourcePatch = { report: { path: 'unit-fixture-report', bytes: 1, sha256: 'f'.repeat(64) },
    patch: { path: 'unit-fixture-patch', bytes: 1, sha256: 'f'.repeat(64) } };
  const bytes = JSON.stringify(parity);
  return { schema: 'selected-cuff-profile-transfer-v1', accepted: false, pass: true,
    baseline: { sha256: BASELINE, rawContractSHA256: RAW, normalizedRuntimeSHA256: RUNTIME },
    candidate: parity.candidate,
    profileAuthoring: { sourceSHA256: AUTHORING, contractSHA256: AUTHORING_CONTRACT, profileSHA256: PROFILE },
    baselineProfileTransferReceipt: { sha256: '9'.repeat(64) }, parity,
    sourcePatch: parity.sourcePatch, parityReceipt: { sha256: sha(bytes) }, parityReceiptBytes: bytes,
    verification: { sourceSHA256: parity.candidate.sha256, actualDecodedAccessorHashesChecked: true,
      actualOriginalBINPrefixChecked: true, actualImagePayloadHashesChecked: true } };
};
const expected = { sourceSHA256: fixture.candidate.sha256, profileSHA256: PROFILE, baselineTransferSHA256: '9'.repeat(64) };
test('wrapper preserves distinct authoring baseline and application lineage', () => {
  assert.equal(validateCuffTransfer(wrapper(), expected, baseline, candidate).gloveStreams, 14);
});
test('wrapper rejects wrong profile authoring contract', () => {
  const proof = wrapper(); proof.profileAuthoring.contractSHA256 = '0'.repeat(64);
  assert.throws(() => validateCuffTransfer(proof, expected, baseline, candidate));
});
test('wrapper rejects wrong application source hash', () => {
  assert.throws(() => validateCuffTransfer(wrapper(), { ...expected, sourceSHA256: '0'.repeat(64) }, baseline, candidate));
});
test('wrapper rejects altered embedded parity receipt bytes', () => {
  const proof = wrapper(); proof.parityReceiptBytes += ' ';
  assert.throws(() => validateCuffTransfer(proof, expected, baseline, candidate));
});
