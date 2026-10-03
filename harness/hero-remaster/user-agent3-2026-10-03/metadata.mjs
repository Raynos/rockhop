/** Admit only one explicit owning-container metadata delta, never changed art. */
import assert from 'node:assert/strict';
import crypto from 'node:crypto';

const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
export function readGlbChunks(bytes) {
  assert(bytes.length >= 28 && bytes.readUInt32LE(0) === 0x46546c67);
  assert.equal(bytes.readUInt32LE(4), 2); assert.equal(bytes.readUInt32LE(8), bytes.length);
  const chunks = [];
  for (let offset = 12; offset < bytes.length;) {
    assert(offset + 8 <= bytes.length);
    const length = bytes.readUInt32LE(offset), type = bytes.readUInt32LE(offset + 4);
    assert(length % 4 === 0 && offset + 8 + length <= bytes.length);
    chunks.push({ type, bytes: bytes.subarray(offset + 8, offset + 8 + length) });
    offset += length + 8;
  }
  assert.equal(chunks.length, 2); assert.equal(chunks[0].type, 0x4e4f534a);
  assert.equal(chunks[1].type, 0x004e4942);
  return { json: JSON.parse(chunks[0].bytes.toString('utf8')), bin: chunks[1].bytes };
}

export function verifyMetadataDerivative(original, derivative, ownerNodeIndex) {
  const base = readGlbChunks(original), tagged = readGlbChunks(derivative);
  assert.deepEqual(base.bin, tagged.bin, 'Metadata derivative changed BIN bytes');
  assert(Number.isInteger(ownerNodeIndex) && base.json.nodes[ownerNodeIndex], 'Missing explicit owner node');
  const flag = 'rockhopRiderSkinConditioned';
  assert(!Object.hasOwn(base.json.nodes[ownerNodeIndex].extras ?? {}, flag), 'Owner already declares conditioning');
  const expected = structuredClone(base.json);
  (expected.nodes[ownerNodeIndex].extras ??= {})[flag] = 1;
  assert.deepEqual(tagged.json, expected, 'Derivative contains another JSON delta');
  const parents = new Map();
  tagged.json.nodes.forEach((node, index) => {
    for (const child of node.children ?? []) {
      assert(!parents.has(child), 'Ambiguous node parent'); parents.set(child, index);
    }
  });
  const scopes = tagged.json.nodes.flatMap((node, index) => {
    if (node.skin === undefined) return [];
    const seen = new Set(); let current = index, nearest = null;
    while (current !== undefined) {
      assert(!seen.has(current), 'Cyclic node hierarchy'); seen.add(current);
      if (Object.hasOwn(tagged.json.nodes[current].extras ?? {}, flag)) { nearest = current; break; }
      current = parents.get(current);
    }
    assert.equal(nearest, ownerNodeIndex, 'Flag does not own every skinned mesh by nearest declaration');
    return [{ meshNodeIndex: index, nearestDeclaringNodeIndex: nearest }];
  });
  assert(scopes.length > 0, 'No skinned meshes checked');
  return { status: 'METADATA_ONLY_VERIFIED_UNACCEPTED', originalSHA256: sha(original),
    derivativeSHA256: sha(derivative), identicalBINSHA256: sha(base.bin),
    ownerNodeIndex, ownerName: expected.nodes[ownerNodeIndex].name, scopes,
    exactOtherJSON: true, jointOrders: expected.skins.map(s => s.joints),
    limits: ['Preserving artist weights does not certify their deformation, clearance or contact.'] };
}
