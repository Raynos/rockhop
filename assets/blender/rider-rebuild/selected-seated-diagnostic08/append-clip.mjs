/** Source-only handoff. Parent runs under CPU2 guard; append native TRS motion. */
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pipeline } from 'node:stream/promises';
import { Transform } from 'node:stream';
import { fileURLToPath } from 'node:url';
import { Matrix4, Quaternion, Vector3 } from 'three';

const ROOT = fileURLToPath(new URL('../../../../', import.meta.url));
export const CLIP = 'DiagnosticRestKey';
export const TIMES = [0, 1, 2, 4, 5, 6];
const base = 'harness/out/rider-rebuild/';
const PINS = {
  rider: [base+'selected-seated-corrective06/constructed02/rider.glb', '2e1b46948be713ede443bc9f159301f876c09aadc331ac25bf477c0d5124cf1a'],
  contract: [base+'selected-seated-corrective06/constructed02/rider-contract.json', '94a2d4b3e6449bc914f22082eeaac247bca1420002af6261faebc76e81fd9c88'],
  author: [base+'selected-seated-author04/authored01/rookie.json', '9d59ba63e99c8d017e7f8c8c4dfbfde0859aafd3ea6d2383c734dec259ec5f8a'],
  corrective: [base+'selected-seated-corrective06/constructed02/corrective.json', 'a9b78bd1e5b038db5d196149da71e027a84e77134928e961148a098d8abfdf52'],
  engineContract: [base+'selected-complete-engine01/engine05/rider-contract.json', '2aa39bc8c15738b4ecbd2aac08fd61375e0aa8fd45a0ee2ac3046f577b019728'],
  engineRider: [base+'selected-complete-engine01/engine05/rider.glb', '72b90e8790f8490743a75f8b70791aa21edfee6234cec609093e9b62e08d4bfd'],
};
async function sha(filename, range = {}) {
  const hash = crypto.createHash('sha256');
  for await (const block of fs.createReadStream(filename, range)) hash.update(block);
  return hash.digest('hex');
}
async function bytes(filename, offset, length) {
  const file = await fsp.open(filename, 'r');
  try {
    const result = Buffer.alloc(length); let read = 0;
    while (read < length) { const row = await file.read(result, read, length-read, offset+read); assert(row.bytesRead); read += row.bytesRead; }
    return result;
  } finally { await file.close(); }
}
async function glb(filename) {
  const header = await bytes(filename, 0, 20), size = (await fsp.stat(filename)).size;
  assert.equal(header.toString('ascii', 0, 4), 'glTF'); assert.equal(header.readUInt32LE(4), 2);
  assert.equal(header.readUInt32LE(8), size); assert.equal(header.readUInt32LE(16), 0x4e4f534a);
  const jsonLength = header.readUInt32LE(12); assert(jsonLength < 16*1024*1024 && jsonLength%4 === 0);
  const document = JSON.parse(await bytes(filename, 20, jsonLength));
  const binHeader = await bytes(filename, 20+jsonLength, 8), binLength = binHeader.readUInt32LE(0);
  assert.equal(binHeader.readUInt32LE(4), 0x004e4942); assert.equal(28+jsonLength+binLength, size);
  assert.equal(document.buffers.length, 1); assert(!document.buffers[0].uri);
  assert(document.buffers[0].byteLength <= binLength && binLength%4 === 0);
  return { filename, document, binOffset: 28+jsonLength, binLength };
}
export function rigIdentity(document, contract) {
  assert.equal(document.skins.length, 1); const skin = document.skins[0];
  assert.equal(skin.joints.length, 75); assert.equal(new Set(skin.joints).size, 75);
  const parents = new Map();
  document.nodes.forEach((node, index) => (node.children ?? []).forEach(child => {
    assert(!parents.has(child)); parents.set(child, index);
  }));
  const jointSet = new Set(skin.joints), native = new Map(contract.nativeRest.bones.map(row => [row.name, row]));
  const declared = Object.values(contract.specification.jointNames);
  assert.equal(native.size, 75); assert.equal(declared.length, 75);
  const rows = skin.joints.map(nodeIndex => {
    const node = document.nodes[nodeIndex]; assert(!node.matrix, 'Native joint must expose source TRS');
    let ancestor = parents.get(nodeIndex);
    while (ancestor !== undefined && !jointSet.has(ancestor)) ancestor = parents.get(ancestor);
    const parent = ancestor === undefined ? null : document.nodes[ancestor].name;
    assert.equal(native.get(node.name)?.parent, parent, `Native parent ${node.name}`);
    return { nodeIndex, name: node.name, parent };
  });
  assert.deepEqual(rows.map(row => row.name).sort(), [...declared].sort()); return rows;
}
async function inverseBinds(source) {
  const a = source.document.accessors[source.document.skins[0].inverseBindMatrices];
  const view = source.document.bufferViews[a.bufferView];
  assert.equal(a.type, 'MAT4'); assert.equal(a.count, 75); assert.equal(a.componentType, 5126);
  assert(!a.sparse && !view.extensions && (!view.byteStride || view.byteStride === 64));
  assert.equal(view.buffer, 0);
  const result = await bytes(source.filename, source.binOffset+(view.byteOffset ?? 0)+(a.byteOffset ?? 0), 75*64);
  for (let i = 0; i < result.length; i += 4) assert(Number.isFinite(result.readFloatLE(i)));
  return result;
}
export function appendAnimation(document, author, identity, binLength) {
  const original = structuredClone(document), rows = new Map(author.boneLocalTRS.map(row => [row.id, row]));
  assert.equal(rows.size, 75); assert.equal(author.boneLocalTRS.length, 75);
  assert.deepEqual([...rows.keys()].sort(), identity.map(row => row.name).sort());
  assert(!(document.animations ?? []).some(row => row.name === CLIP), 'Diagnostic clip already exists');
  document.animations ??= []; const chunks = []; let length = binLength, maximumFloat32Residual = 0;
  const attribute = (values, type, width, time = false) => {
    assert(values.length%width === 0 && values.every(Number.isFinite));
    const buffer = Buffer.alloc(values.length*4);
    values.forEach((value, index) => { buffer.writeFloatLE(value, index*4); maximumFloat32Residual = Math.max(maximumFloat32Residual, Math.abs(value-buffer.readFloatLE(index*4))); });
    const view = document.bufferViews.length;
    document.bufferViews.push({ buffer: 0, byteOffset: length, byteLength: buffer.length });
    const accessor = { bufferView: view, componentType: 5126, count: values.length/width, type };
    if (time) Object.assign(accessor, { min: [0], max: [6] });
    document.accessors.push(accessor); chunks.push(buffer); length += buffer.length;
    return document.accessors.length-1;
  };
  const input = attribute(TIMES, 'SCALAR', 1, true), animation = { name: CLIP, samplers: [], channels: [],
    extras: { accepted: false, qualification: 'FAILED_CORRECTIVE_GATES', diagnostic: 'Source rest to saved author04 key; pose-local morph activation only' } };
  for (const { nodeIndex, name } of identity) {
    const node = document.nodes[nodeIndex], key = rows.get(name);
    for (const [target, field, type, width, fallback] of [
      ['translation', 'translation', 'VEC3', 3, [0, 0, 0]],
      ['rotation', 'rotationXYZW', 'VEC4', 4, [0, 0, 0, 1]],
      ['scale', 'scale', 'VEC3', 3, [1, 1, 1]],
    ]) {
      const rest = node[target] ?? fallback, saved = key[field];
      assert.equal(rest.length, width); assert.equal(saved.length, width);
      if (target === 'rotation') for (const q of [rest, saved]) assert(Math.abs(Math.hypot(...q)-1) < 1e-5);
      const values = [rest, rest, saved, saved, rest, rest].flat();
      const output = attribute(values, type, width), sampler = animation.samplers.length;
      animation.samplers.push({ input, output, interpolation: 'LINEAR' });
      animation.channels.push({ sampler, target: { node: nodeIndex, path: target } });
    }
  }
  assert.equal(animation.channels.length, 225); document.animations.push(animation);
  document.buffers[0].byteLength = length;
  for (const [key, value] of Object.entries(original)) {
    if (['buffers', 'bufferViews', 'accessors', 'animations'].includes(key)) continue;
    assert.deepEqual(document[key], value, `Protected document ${key}`);
  }
  assert.deepEqual(document.accessors.slice(0, original.accessors.length), original.accessors);
  assert.deepEqual(document.bufferViews.slice(0, original.bufferViews.length), original.bufferViews);
  assert.deepEqual(document.animations.slice(0, original.animations?.length ?? 0), original.animations ?? []);
  return { tail: Buffer.concat(chunks), maximumFloat32Residual, animation };
}
export function endpointActivation(document, identity, author, activation, contract) {
  const saved = new Map(author.boneLocalTRS.map(row => [row.id, row])), role = name => {
    const id = contract.specification.roles[name]; return contract.specification.jointNames[Array.isArray(id) ? id[0] : id];
  };
  return [false, true].map(key => {
    const worlds = new Map();
    const visit = (index, parent = new Matrix4()) => {
      const n = document.nodes[index], row = key ? saved.get(n.name) : undefined;
      const round = a => a.map(Math.fround);
      const local = n.matrix ? new Matrix4().fromArray(n.matrix) : new Matrix4().compose(
        new Vector3().fromArray(round(row?.translation ?? n.translation ?? [0, 0, 0])),
        new Quaternion().fromArray(round(row?.rotationXYZW ?? n.rotation ?? [0, 0, 0, 1])),
        new Vector3().fromArray(round(row?.scale ?? n.scale ?? [1, 1, 1])));
      const world = parent.clone().multiply(local); worlds.set(index, world);
      for (const child of n.children ?? []) visit(child, world);
    };
    for (const index of document.scenes[document.scene ?? 0].nodes) visit(index);
    const worldQ = name => {
      const index = identity.find(row => row.name === name).nodeIndex;
      const q = new Quaternion(); worlds.get(index).decompose(new Vector3(), q, new Vector3()); return q.normalize();
    };
    const pelvis = worldQ(role('pelvis')), distances = ['Left', 'Right'].map((side, i) => {
      const flex = pelvis.clone().invert().multiply(worldQ(role('thigh'+side)))
        .multiply(new Quaternion().fromArray(activation.restRelativeXYZW[i]).invert());
      return flex.normalize().angleTo(new Quaternion().fromArray(activation.keyXYZW[i]).normalize());
    });
    const x = Math.hypot(...distances)/activation.radiusRadians, weight = Math.max(0, 1-x)**4*(4*x+1);
    assert(Math.abs(weight-(key ? 1 : 0)) < 1e-5, `Actual float32 endpoint activation ${key}: ${weight}`);
    return { endpoint: key ? 'authored-key' : 'source-rest', weight, distancesRadians: distances };
  });
}
async function main() {
  const output = process.argv.find(value => value.startsWith('--out=')); assert(output, 'Pass fresh --out=');
  const out = path.resolve(output.slice(6)), allowed = path.join(ROOT, base, 'selected-seated-diagnostic08');
  assert(out.startsWith(allowed+path.sep) && !fs.existsSync(out), 'Fresh ignored diagnostic output required');
  for (const [filename, digest] of Object.values(PINS)) assert.equal(await sha(path.join(ROOT, filename)), digest, filename);
  const json = async name => JSON.parse(await fsp.readFile(path.join(ROOT, PINS[name][0]), 'utf8'));
  const [contract, engineContract, author, corrective] = await Promise.all(['contract', 'engineContract', 'author', 'corrective'].map(json));
  assert.equal(contract.accepted, false); assert.equal(contract.qualificationState, 'FAILED_CORRECTIVE_GATES');
  assert.equal(author.accepted, false); assert.equal(author.status, 'FAILED_AUTHORING_PROXY');
  assert.equal(corrective.accepted, false); assert.equal(corrective.status, 'FAILED_CORRECTIVE_GATES');
  assert.deepEqual(contract.corrective, corrective.activation); assert.equal(contract.glbSHA256, PINS.rider[1]);
  assert.deepEqual(contract.nativeRest, engineContract.nativeRest);
  assert.deepEqual(contract.specification.jointNames, engineContract.specification.jointNames);
  assert.equal(engineContract.glbSHA256, PINS.engineRider[1]);
  const source = await glb(path.join(ROOT, PINS.rider[0])), engine = await glb(path.join(ROOT, PINS.engineRider[0]));
  const identity = rigIdentity(source.document, engineContract);
  assert.deepEqual(identity, rigIdentity(engine.document, engineContract));
  assert.deepEqual(source.document.nodes, engine.document.nodes); assert.deepEqual(source.document.skins, engine.document.skins);
  const inverse = await inverseBinds(source); assert(inverse.equals(await inverseBinds(engine)), 'All 75 inverse binds exact');
  const endpoints = endpointActivation(source.document, identity, author, contract.corrective, contract);
  const { tail, maximumFloat32Residual } = appendAnimation(source.document, author, identity, source.binLength);
  const raw = Buffer.from(JSON.stringify(source.document)), padded = Buffer.concat([raw, Buffer.alloc((4-raw.length%4)%4, 32)]);
  const header = Buffer.alloc(20); header.write('glTF'); header.writeUInt32LE(2, 4);
  header.writeUInt32LE(28+padded.length+source.binLength+tail.length, 8); header.writeUInt32LE(padded.length, 12); header.writeUInt32LE(0x4e4f534a, 16);
  const binHeader = Buffer.alloc(8); binHeader.writeUInt32LE(source.binLength+tail.length); binHeader.writeUInt32LE(0x004e4942, 4);
  await fsp.mkdir(out, { recursive: true }); const target = path.join(out, 'rider.glb');
  await fsp.writeFile(target, Buffer.concat([header, padded, binHeader]), { flag: 'wx' });
  const binHash = crypto.createHash('sha256');
  await pipeline(fs.createReadStream(source.filename, { start: source.binOffset, end: source.binOffset+source.binLength-1 }),
    new Transform({ transform(block, encoding, callback) { binHash.update(block); callback(null, block); } }), fs.createWriteStream(target, { flags: 'a' }));
  await fsp.appendFile(target, tail);
  const originalBinarySHA256 = binHash.digest('hex');
  assert.equal(await sha(target, { start: 28+padded.length, end: 28+padded.length+source.binLength-1 }), originalBinarySHA256);
  const targetSHA = await sha(target), before = structuredClone(contract);
  const report = { accepted: false, status: 'FAILED_CORRECTIVE_GATES', previewClip: CLIP, durationSeconds: 6,
    timesSeconds: TIMES, schedule: ['rest', 'rest', 'authored-key', 'authored-key', 'rest', 'rest'],
    sourcePins: Object.fromEntries(Object.entries(PINS).map(([name, [filename, sha256]]) => [name, { path: filename, sha256 }])),
    recipeSHA256: await sha(fileURLToPath(import.meta.url)), outputSHA256: targetSHA, originalBinarySHA256,
    originalBinaryBytesPreserved: source.binLength, appendedAnimationBytes: tail.length, maximumFloat32Residual,
    jointIdentity: identity, inverseBindSHA256: crypto.createHash('sha256').update(inverse).digest('hex'),
    endpointActivation: endpoints, channels: 225, weightChannels: 0, correctiveReceipt: corrective, authorReceipt: author,
    limits: ['Failed diagnostic only; no contact, generic motion, moving-art or human acceptance.',
      'Actual Garage clip/helper/render/video verification remains parent-run. No runtime pose or camera injection.'] };
  contract.glbSHA256 = targetSHA; contract.previewClip = CLIP; contract.diagnosticMotion = report;
  for (const [key, value] of Object.entries(before)) if (key !== 'glbSHA256') assert.deepEqual(contract[key], value);
  await fsp.writeFile(path.join(out, 'rider-contract.json'), JSON.stringify(contract, null, 2)+'\n');
  await fsp.writeFile(path.join(out, 'diagnostic.json'), JSON.stringify(report, null, 2)+'\n');
  console.log(JSON.stringify({ status: report.status, glbSHA256: targetSHA, previewClip: CLIP, out }));
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
