/** Decoded sparse accessor and semantic source fidelity utilities. */
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
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

function primitiveSignature(g, p) {
  return { attrs: Object.fromEntries(Object.entries(p.attributes).map(([name, index]) => [name, digest(acc(g, index))])),
    index: digest(acc(g, p.indices)),
    targets: (p.targets ?? []).map(t => Object.fromEntries(Object.entries(t).map(([name, index]) => [name, digest(acc(g, index))]))) };
}

function image(g, index) {
  const im = g.json.images[index], v = g.json.bufferViews[im.bufferView];
  const bytes = g.bin.subarray(v.byteOffset ?? 0, (v.byteOffset ?? 0) + v.byteLength);
  return { mime: im.mimeType, bytes: bytes.length, sha256: sha(bytes) };
}

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

export { acc, digest, rig, parents, primitiveSignature, image, material };
