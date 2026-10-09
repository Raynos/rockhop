// Declared sleeve correction proof. Generic graft validation stays separate.
import assert from 'node:assert/strict';
import crypto from 'node:crypto';

export const BASELINE = '585ae314e2b354768a1385e5a85828c142d542b47f8d9fe948f46c7478c112ef';
export const AUTHORING = 'f814b8d7cde87b1e41b45eec75cd55fdea89b915bf9acae0e5a18b40d3a156af';
export const AUTHORING_CONTRACT = '0301087649f7e2b2c442299bb21f61dc1e325c6b5b84afbc3ac5c4a594b72813';
export const PROFILE = '659ff94c1611e0ce95310ab090e94637832ac2bbfbac7f9554f903595bd05972';
export const RAW = '36bc9a83454f6e885bb0a5d6d90b76d2bbe6658d93144d2da55ce068f627d4ff';
export const RUNTIME = '50b9bad4b983e24e9aa946bdfaa1009f2a98b3578bd4c1788e672bc7fdfcf94c';
export const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const hashValue = value => sha(JSON.stringify(value ?? []));
const hash = value => assert.match(value, /^[a-f0-9]{64}$/, 'Exact SHA256 certificate required');
const format = accessor => ({ count: accessor.count, type: accessor.type,
  componentType: accessor.componentType, normalized: accessor.normalized ?? false });
const allowed = new Set(['POSITION', 'NORMAL', 'TANGENT', 'JOINTS_0', 'WEIGHTS_0']);
const nativeRecords = ['nodes', 'skins', 'scenes', 'animations', 'materials', 'textures', 'images', 'samplers'];

export function validateCuffParity(parity, baseline, candidate) {
  assert.equal(parity.schema, 'selected-cuff-source-parity-v1');
  assert.equal(parity.accepted, false);
  assert.equal(parity.baseline.sha256, BASELINE);
  hash(parity.candidate.sha256); assert.notEqual(parity.candidate.sha256, BASELINE);
  for (const flag of ['nativeRigAndAnimationJSONExact', 'protectedNativeAccessorBytesExact',
    'materialsTexturesImagesJSONExact', 'originalBINPayloadPrefixExact',
    'unchangedGloveAccessorBytesExact', 'allOtherAccessorBytesExact']) assert.equal(parity[flag], true, flag);
  assert.equal(candidate.accessors.length, baseline.accessors.length, 'Exact accessor identity domain');
  assert.deepEqual(candidate.bufferViews.slice(0, baseline.bufferViews.length), baseline.bufferViews,
    'Existing storage view and codec declarations stay exact');
  assert.deepEqual(candidate.meshes, baseline.meshes, 'Mesh primitive identities and attribute links unchanged');
  assert.deepEqual(candidate.scene ?? 0, baseline.scene ?? 0);
  assert(baseline.skins.length > 0 && baseline.skins.every(skin => skin.joints.length === 75), 'Native75 skins');
  for (const key of nativeRecords) {
    assert.deepEqual(candidate[key] ?? [], baseline[key] ?? [], `Exact native/material record ${key}`);
    const proof = parity.nativeJSONRecordsExact?.[key];
    assert.equal(proof?.exact, true, `Missing exact ${key} certificate`);
    assert.equal(proof.beforeSHA256, hashValue(baseline[key]));
    assert.equal(proof.afterSHA256, hashValue(candidate[key]));
  }
  const changes = parity.changedAccessors;
  assert(Array.isArray(changes) && changes.length > 0, 'Explicit actual changed streams required');
  const changed = new Map();
  for (const row of changes) {
    assert.equal(row.mesh, 5, 'Only declared selected hoodie mesh may change');
    assert.equal(row.primitive ?? 0, 0);
    assert(allowed.has(row.semantic), `Unknown changed stream ${row.semantic}`);
    assert.equal(row.accessor, baseline.meshes[5].primitives[0].attributes[row.semantic]);
    assert(!changed.has(row.accessor), 'Duplicate changed accessor'); changed.set(row.accessor, row);
    assert.equal(row.count, baseline.accessors[row.accessor].count);
    assert.deepEqual(format(candidate.accessors[row.accessor]), format(baseline.accessors[row.accessor]));
    const metadata = value => Object.fromEntries(Object.entries(value).filter(([key]) =>
      key !== 'bufferView' && !(row.semantic === 'POSITION' && ['min', 'max'].includes(key))));
    assert.deepEqual(metadata(candidate.accessors[row.accessor]), metadata(baseline.accessors[row.accessor]),
      'No undeclared changed accessor metadata');
    assert(Number.isInteger(row.changedRows) && row.changedRows > 0 && row.changedRows <= row.count);
    hash(row.beforeDecodedSHA256); hash(row.afterDecodedSHA256);
    assert.notEqual(row.beforeDecodedSHA256, row.afterDecodedSHA256, 'Changed stream must actually differ');
  }
  assert(changes.some(row => row.semantic === 'POSITION'), 'Actual cuff position correction required');
  const protectedRows = parity.protectedAccessorStreamsExact;
  assert(Array.isArray(protectedRows));
  const protectedById = new Map();
  for (const row of protectedRows) {
    assert(Number.isInteger(row.accessor) && row.accessor >= 0 && row.accessor < baseline.accessors.length);
    assert(!changed.has(row.accessor) && !protectedById.has(row.accessor), 'Exact protected coverage without exclusions');
    assert.deepEqual(candidate.accessors[row.accessor], baseline.accessors[row.accessor]);
    for (const [key, value] of Object.entries(format(baseline.accessors[row.accessor]))) assert.equal(row[key], value);
    assert.equal(row.exact, true); hash(row.beforeDecodedSHA256);
    assert.equal(row.afterDecodedSHA256, row.beforeDecodedSHA256);
    protectedById.set(row.accessor, row);
  }
  assert.equal(protectedById.size + changed.size, baseline.accessors.length, 'Every accessor accounted for');
  const gloveProofs = parity.unchangedGloveAccessorStreamsExact;
  assert(Array.isArray(gloveProofs), 'Complete explicit glove field certificates required');
  let gloveCount = 0;
  for (const mesh of [2, 3]) for (const [primitive, part] of baseline.meshes[mesh].primitives.entries()) {
    for (const [semantic, accessor] of [...Object.entries(part.attributes), ['indices', part.indices]]) {
      const matches = gloveProofs.filter(row => row.mesh === mesh && row.primitive === primitive && row.semantic === semantic);
      assert.equal(matches.length, 1, `Missing/duplicate glove ${mesh}/${primitive}/${semantic}`);
      const row = matches[0], proof = protectedById.get(accessor);
      assert.equal(row.accessor, accessor); assert.equal(row.exact, true);
      assert.equal(row.beforeDecodedSHA256, proof.beforeDecodedSHA256);
      assert.equal(row.afterDecodedSHA256, proof.afterDecodedSHA256);
      for (const [key, value] of Object.entries(format(baseline.accessors[accessor]))) assert.equal(row[key], value);
      gloveCount++;
    }
  }
  assert.equal(gloveCount, gloveProofs.length, 'No unrelated glove certificates');
  const images = parity.imagePayloadsExact;
  assert(Array.isArray(images) && images.length === baseline.images.length, 'Every texture payload certified');
  for (const [image, item] of baseline.images.entries()) {
    const matches = images.filter(row => row.image === image);
    assert.equal(matches.length, 1, 'Exact image coverage');
    const row = matches[0]; assert.equal(row.exact, true); assert.equal(row.bufferView, item.bufferView);
    assert.equal(row.bytes, baseline.bufferViews[item.bufferView].byteLength);
    hash(row.beforeSHA256); assert.equal(row.afterSHA256, row.beforeSHA256);
  }
  return { changedAccessors: changes, protectedAccessors: protectedById.size,
    gloveStreams: gloveCount, imagePayloads: images.length, nativeJoints: 75,
    geometry: candidate.meshes.flatMap(mesh => mesh.primitives).reduce((total, primitive) => ({
      vertices: total.vertices + candidate.accessors[primitive.attributes.POSITION].count,
      triangles: total.triangles + candidate.accessors[primitive.indices].count / 3,
    }), { vertices: 0, triangles: 0 }),
    animationChannels: (baseline.animations ?? []).reduce((n, a) => n + a.channels.length, 0) };
}

export function validateCuffTransfer(transfer, expected, baseline, candidate) {
  assert.equal(transfer.schema, 'selected-cuff-profile-transfer-v1');
  assert.equal(transfer.accepted, false); assert.equal(transfer.pass, true);
  assert.equal(transfer.baseline.sha256, BASELINE);
  assert.equal(transfer.candidate.sha256, expected.sourceSHA256);
  assert.equal(transfer.profileAuthoring.sourceSHA256, AUTHORING);
  assert.equal(transfer.profileAuthoring.contractSHA256, AUTHORING_CONTRACT);
  assert.equal(transfer.profileAuthoring.profileSHA256, PROFILE);
  assert.equal(expected.profileSHA256, PROFILE);
  assert.equal(transfer.baseline.rawContractSHA256, RAW);
  assert.equal(transfer.baseline.normalizedRuntimeSHA256, RUNTIME);
  assert.equal(transfer.baselineProfileTransferReceipt.sha256, expected.baselineTransferSHA256);
  assert.equal(transfer.parity.candidate.sha256, transfer.candidate.sha256);
  assert.deepEqual(transfer.sourcePatch, transfer.parity.sourcePatch, 'Exact source patch lineage');
  assert.deepEqual(Object.keys(transfer.sourcePatch).sort(), ['patch', 'report']);
  for (const record of Object.values(transfer.sourcePatch)) {
    hash(record.sha256); assert(Number.isInteger(record.bytes) && record.bytes > 0);
    assert.equal(typeof record.path, 'string');
  }
  assert.equal(transfer.verification.sourceSHA256, transfer.candidate.sha256);
  assert.equal(transfer.verification.actualDecodedAccessorHashesChecked, true, 'Admitted compiler decoded proof required');
  assert.equal(transfer.verification.actualOriginalBINPrefixChecked, true);
  assert.equal(transfer.verification.actualImagePayloadHashesChecked, true);
  assert.equal(transfer.parityReceipt.sha256, sha(transfer.parityReceiptBytes));
  assert.deepEqual(JSON.parse(transfer.parityReceiptBytes), transfer.parity);
  return validateCuffParity(transfer.parity, baseline, candidate);
}
