/** Tiny in-memory fixtures only. No private GLB reads, output or browser work. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { appendAnimation, rigIdentity, CLIP, TIMES } from './append-clip.mjs';

function fixture() {
  const nodes = Array.from({ length: 75 }, (_, i) => ({ name: 'Native'+i,
    translation: [0, i/100, 0], rotation: [0, 0, 0, 1], scale: [1, 1, 1],
    ...(i < 74 ? { children: [i+1] } : {}) }));
  const document = { asset: { version: '2.0' }, scene: 0, scenes: [{ nodes: [0] }], nodes,
    skins: [{ joints: Array.from({ length: 75 }, (_, i) => 74-i), inverseBindMatrices: 0 }],
    materials: [{ name: 'Original' }], meshes: [{ weights: [0], primitives: [{ targets: [{ POSITION: 0 }] }] }],
    accessors: [{ bufferView: 0, componentType: 5126, count: 75, type: 'MAT4' }],
    bufferViews: [{ buffer: 0, byteOffset: 0, byteLength: 4800 }], buffers: [{ byteLength: 4800 }] };
  const contract = { specification: { jointNames: Object.fromEntries(nodes.map(n => [n.name, n.name])) },
    nativeRest: { bones: nodes.map((n, i) => ({ name: n.name, parent: i ? nodes[i-1].name : null })) } };
  const author = { boneLocalTRS: nodes.map((n, i) => ({ id: n.name, translation: [1, i/100, 2],
    rotationXYZW: [0, Math.sin(.1), 0, Math.cos(.1)], scale: [1, 1, 1] })) };
  return { document, contract, author };
}
test('preserves native inventory/materials/morphs and appends only 225 TRS channels', () => {
  const { document, contract, author } = fixture(), before = structuredClone(document);
  const identity = rigIdentity(document, contract); assert.equal(identity[0].name, 'Native74');
  const result = appendAnimation(document, author, identity, 4800), clip = result.animation;
  assert.equal(clip.name, CLIP); assert.equal(clip.channels.length, 225); assert.equal(clip.samplers.length, 225);
  assert(clip.channels.every(c => ['translation', 'rotation', 'scale'].includes(c.target.path)));
  for (const field of ['nodes', 'skins', 'materials', 'meshes']) assert.deepEqual(document[field], before[field]);
  const read = index => {
    const a = document.accessors[index], v = document.bufferViews[a.bufferView];
    return Array.from({ length: v.byteLength/4 }, (_, i) => result.tail.readFloatLE(v.byteOffset-4800+i*4));
  };
  assert.deepEqual(read(clip.samplers[0].input), TIMES);
  const position = read(clip.samplers[0].output), rest = before.nodes[74].translation.map(Math.fround), key = author.boneLocalTRS[74].translation.map(Math.fround);
  assert.deepEqual(position, [rest, rest, key, key, rest, rest].flat());
  assert.equal(document.buffers[0].byteLength, 4800+result.tail.length);
  assert.throws(() => appendAnimation(document, author, identity, 4800), /already exists/);
});
test('rejects parent drift and missing authored native identity', () => {
  const { document, contract, author } = fixture();
  contract.nativeRest.bones[1].parent = null; assert.throws(() => rigIdentity(document, contract), /Native parent/);
  contract.nativeRest.bones[1].parent = 'Native0'; const identity = rigIdentity(document, contract);
  author.boneLocalTRS.pop(); assert.throws(() => appendAnimation(document, author, identity, 4800));
});
