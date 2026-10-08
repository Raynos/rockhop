/** Append a glTF morph while retaining every original binary byte and attribute. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { BufferGeometry, Float32BufferAttribute, Quaternion, Vector3 } from 'three';
import { load, pinned, sha } from '../selected-ankle-contact02/surface.mjs';
export async function exportMorph(source, deltas, filename) {
  const bytes = pinned(source), raw = await load(source), document = raw.document, jsonLength = bytes.readUInt32LE(12);
  const chunks = [bytes.subarray(28 + jsonLength)]; let length = chunks[0].length;
  const attribute = (values, type, bounds = false) => {
    const array = new Float32Array(values); assert([...array].every(Number.isFinite));
    const buffer = Buffer.from(array.buffer), view = document.bufferViews.length;
    document.bufferViews.push({ buffer: 0, byteOffset: length, byteLength: buffer.length, target: 34962 });
    chunks.push(buffer); length += buffer.length;
    const accessor = { bufferView: view, componentType: 5126, count: values.length / 3, type };
    if (bounds) { accessor.min = [0, 1, 2].map(k => Math.min(...values.filter((_, i) => i % 3 === k))); accessor.max = [0, 1, 2].map(k => Math.max(...values.filter((_, i) => i % 3 === k))); }
    document.accessors.push(accessor); return document.accessors.length - 1;
  };
  for (const [name, rows] of Object.entries(deltas)) {
    const lookup = new Map(rows.map(r => [r.nativeID, r.deltaGLTF])), node = raw.node(name).value, mesh = document.meshes[node.mesh];
    assert(mesh && !mesh.weights && mesh.primitives.every(p => !p.targets), 'Existing morphs require an explicit composition recipe');
    for (const p of mesh.primitives) {
      const native = raw.read(p.attributes._NATIVE_ID), positions = raw.read(p.attributes.POSITION), normals = raw.read(p.attributes.NORMAL), indices = raw.read(p.indices);
      const delta = [], target = [], basePosition = [], baseNormal = [];
      for (let i = 0; i < native.count; i++) { const d = lookup.get(native.get(i)) ?? [0, 0, 0]; delta.push(...d); basePosition.push(...positions.row(i)); target.push(...positions.row(i).map((v, k) => v + d[k])); baseNormal.push(...normals.row(i)); }
      const faceRows = Array.from({ length: indices.count }, (_, i) => indices.get(i));
      const geometry = new BufferGeometry(); geometry.setAttribute('position', new Float32BufferAttribute(target, 3)); geometry.setIndex(faceRows); geometry.computeVertexNormals();
      const base = new BufferGeometry(); base.setAttribute('position', new Float32BufferAttribute(basePosition, 3)); base.setIndex(faceRows); base.computeVertexNormals();
      const generated = geometry.attributes.normal, normalDelta = [], authoredTargetNormals = [];
      for (let i = 0; i < native.count; i++) {
        const before = new Vector3().fromBufferAttribute(base.attributes.normal, i).normalize(), after = new Vector3().fromBufferAttribute(generated, i).normalize();
        const authored = new Vector3(...normals.row(i)), moved = authored.clone().applyQuaternion(new Quaternion().setFromUnitVectors(before, after));
        authoredTargetNormals.push(moved); normalDelta.push(...moved.clone().sub(authored).toArray());
      }
      const morph = { POSITION: attribute(delta, 'VEC3', true), NORMAL: attribute(normalDelta, 'VEC3') };
      if (p.attributes.TANGENT !== undefined) {
        const tangent = raw.read(p.attributes.TANGENT), values = [];
        for (let i = 0; i < native.count; i++) {
          const a = new Vector3(...normals.row(i)).normalize(), b = authoredTargetNormals[i].clone().normalize(), t = new Vector3(...tangent.row(i).slice(0, 3));
          values.push(...t.clone().applyQuaternion(new Quaternion().setFromUnitVectors(a, b)).sub(t).toArray());
        }
        morph.TANGENT = attribute(values, 'VEC3');
      }
      p.targets = [morph]; geometry.dispose(); base.dispose();
    }
    mesh.weights = [0]; mesh.extras = { ...mesh.extras, targetNames: ['SelectedSeatedCorrective06'] };
  }
  document.buffers[0].byteLength = length;
  const json = Buffer.from(JSON.stringify(document)), padded = Buffer.concat([json, Buffer.alloc((4 - json.length % 4) % 4, 32)]), binary = Buffer.concat(chunks);
  const output = Buffer.alloc(28 + padded.length + binary.length);
  output.write('glTF'); output.writeUInt32LE(2, 4); output.writeUInt32LE(output.length, 8); output.writeUInt32LE(padded.length, 12); output.writeUInt32LE(0x4e4f534a, 16); padded.copy(output, 20);
  output.writeUInt32LE(binary.length, 20 + padded.length); output.writeUInt32LE(0x004e4942, 24 + padded.length); binary.copy(output, 28 + padded.length);
  assert(binary.subarray(0, chunks[0].length).equals(chunks[0]), 'Original binary changed'); fs.writeFileSync(filename, output);
  return { sha256: sha(output), originalBinaryPreserved: true, defaultWeight: 0 };
}
