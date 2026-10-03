import test from 'node:test';
import assert from 'node:assert/strict';
import { verifyMetadataDerivative } from './metadata.mjs';

const definition = { asset: { version: '2.0' }, nodes: [{ name: 'owner', children: [1] }, { skin: 0 }], skins: [{ joints: [2, 3] }] };
const encode = (json, bin = Buffer.alloc(4)) => {
  const text = JSON.stringify(json), raw = Buffer.from(text + ' '.repeat((4 - text.length % 4) % 4));
  const head = Buffer.alloc(20), binHead = Buffer.alloc(8);
  head.writeUInt32LE(0x46546c67, 0); head.writeUInt32LE(2, 4);
  head.writeUInt32LE(28 + raw.length + bin.length, 8);
  head.writeUInt32LE(raw.length, 12); head.writeUInt32LE(0x4e4f534a, 16);
  binHead.writeUInt32LE(bin.length, 0); binHead.writeUInt32LE(0x004e4942, 4);
  return Buffer.concat([head, raw, binHead, bin]);
};
const tagged = () => {
  const d = structuredClone(definition); d.nodes[0].extras = { rockhopRiderSkinConditioned: 1 }; return d;
};

await test('one exact owner metadata delta preserves complete binary and rig', () => {
  const r = verifyMetadataDerivative(encode(definition), encode(tagged()), 0);
  assert.deepEqual(r.jointOrders, [[2, 3]]); assert.equal(r.scopes[0].nearestDeclaringNodeIndex, 0);
});
await test('changed weights/BIN, rig order or unrelated extras are refused', () => {
  assert.throws(() => verifyMetadataDerivative(encode(definition), encode(tagged(), Buffer.from([1, 0, 0, 0])), 0));
  for (const change of [d => d.skins[0].joints.reverse(), d => { d.nodes[0].extras.other = true; }]) {
    const d = tagged(); change(d); assert.throws(() => verifyMetadataDerivative(encode(definition), encode(d), 0));
  }
});
await test('a closer declaration cannot be masked by an ancestor flag', () => {
  const d = structuredClone(definition); d.nodes[1].extras = { rockhopRiderSkinConditioned: 0 };
  const t = structuredClone(d); t.nodes[0].extras = { rockhopRiderSkinConditioned: 1 };
  assert.throws(() => verifyMetadataDerivative(encode(d), encode(t), 0));
});
