/** Replay exact native sample matrices through installed Three.js four-slot CPU skin. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import crypto from 'node:crypto';
import { Matrix3, Matrix4, Vector3 } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { compareThreeWays } from '../hero-remaster/user-agent3-2026-10-03/compare.mjs';
const [glbPath, nativeDirectory, mappingPath, output] = process.argv.slice(2);
assert(output && !fs.existsSync(output), 'Usage export-check.mjs FOUR.glb NATIVE_DIRECTORY MAPPING.json NEW.json');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const read = name => fs.readFileSync(path.join(nativeDirectory, name));
const reportBytes = read('report.json'), native = JSON.parse(reportBytes);
const restBytes = read(native.rest.path); assert.equal(sha(restBytes), native.rest.sha256);
const rest = JSON.parse(zlib.gunzipSync(restBytes)), bytes = fs.readFileSync(glbPath), mappingBytes = fs.readFileSync(mappingPath), mapping = JSON.parse(mappingBytes);
assert.equal(mapping.glbSHA256, sha(bytes));
assert.equal(mapping.nativeSourceSHA256, Object.values(native.sourcePins)[0]);
const document = JSON.parse(bytes.subarray(20, 20 + bytes.readUInt32LE(12)));
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
loader.register(parser => { parser.loadTexture = async () => null; return { name: 'CPU_ONLY_NO_TEXTURE_DECODE' }; });
const gltf = await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
gltf.scene.updateMatrixWorld(true);
const byNode = new Map();
for (const [object, association] of gltf.parser.associations) if (association.nodes !== undefined) byNode.set(association.nodes, object);
const bones = new Map();
for (const skin of document.skins) for (const node of skin.joints) {
  const name = document.nodes[node].name; assert(byNode.get(node)?.isBone); bones.set(name, byNode.get(node));
}
assert.deepEqual([...bones.keys()].sort((a, b) => a.localeCompare(b)), rest.jointOrder.slice().sort((a, b) => a.localeCompare(b)));
const meshes = [];
gltf.scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
assert(mapping.regions.body && mapping.regions.head, 'Body and separate head mapping mandatory');
const declared = Object.entries(mapping.regions).map(([region, declaration]) => {
  const objects = meshes.filter(m => document.nodes[gltf.parser.associations.get(m)?.nodes]?.name === declaration.exportName);
  assert.equal(objects.length, 1, `Ambiguous/missing ${region} export`);
  const mesh = objects[0], ids = mesh.geometry.getAttribute('_native_id');
  assert(ids && ids.itemSize === 1 && !ids.normalized || declaration.nativeVertexIDs, 'Unique derivative _NATIVE_ID or independently pinned exact mapping required; original ancestry -1 is not mapping');
  const nativeIDs = ids ? Array.from({ length: ids.count }, (_, i) => ids.getX(i)) : declaration.nativeVertexIDs;
  assert.equal(nativeIDs.length, mesh.geometry.getAttribute('position').count);
  assert(nativeIDs.every(i => Number.isInteger(i) && i >= 0 && i < rest.parts[region].xyz.length));
  const cornerIDs = mesh.geometry.getAttribute('_corner_id');
  if (cornerIDs) assert(cornerIDs.count === nativeIDs.length && cornerIDs.itemSize === 1);
  return { region, mesh, nativeIDs, cornerIDs, protectedIDs: new Set(declaration.protectedNativeVertexIDs ?? []) };
});
assert.equal(declared.length, meshes.length, 'No unmeasured exported skinned partner');
const C = new Matrix4().set(1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1);
const nativeToFile = xyz => xyz.flatMap(([x, y, z]) => [x, z, -y]);
const matRows = rows => new Matrix4().set(...rows.flat());
const scratch = new Vector3(), records = [];
for (const pin of native.samples) {
  const raw = read(pin.path); assert.equal(sha(raw), pin.sha256); const sample = JSON.parse(zlib.gunzipSync(raw));
  const wanted = new Map([...bones].map(([name, bone]) => [bone, C.clone().multiply(matRows(sample.boneWorldNativeRows[name]))]));
  for (const [bone, matrix] of wanted) {
    const parent = wanted.get(bone.parent) ?? bone.parent.matrixWorld;
    bone.matrixAutoUpdate = false; bone.matrix.copy(parent.clone().invert().multiply(matrix));
  }
  gltf.scene.updateMatrixWorld(true);
  const comparisons = [];
  for (const { region, mesh, nativeIDs, cornerIDs, protectedIDs } of declared) {
    mesh.skeleton.update();
    const xyz = new Float64Array(nativeIDs.length * 3);
    for (let i = 0; i < nativeIDs.length; i++) { mesh.getVertexPosition(i, scratch); scratch.applyMatrix4(mesh.matrixWorld); scratch.toArray(xyz, i * 3); }
    const full = Float64Array.from(nativeToFile(sample.parts[region].full.xyzWorld)), four = Float64Array.from(nativeToFile(sample.parts[region].four.xyzWorld));
    const result = compareThreeWays(full, four, xyz, nativeIDs);
    let normalParity = { status: 'UNMEASURED', reason: 'Export lacks exact derivative _CORNER_ID; coincident normals are not correspondence.' };
    if (cornerIDs) {
      const attribute = mesh.geometry.getAttribute('normal'), skinIndex = mesh.geometry.getAttribute('skinIndex'), weight = mesh.geometry.getAttribute('skinWeight');
      let maximum = 0, worst = null, protectedMaximum = 0, protectedWorst = null, protectedRows = 0;
      for (let i = 0; i < nativeIDs.length; i++) {
        const corner = cornerIDs.getX(i); assert(Number.isInteger(corner) && corner >= 0 && corner < rest.parts[region].cornerVertices.length);
        assert.equal(rest.parts[region].cornerVertices[corner], nativeIDs[i]);
        const blended = new Matrix4(); blended.elements.fill(0);
        for (let k = 0; k < 4; k++) {
          const bone = skinIndex.getComponent(i, k), w = weight.getComponent(i, k);
          for (let j = 0; j < 16; j++) blended.elements[j] += w * mesh.skeleton.boneMatrices[bone * 16 + j];
        }
        const transform = mesh.bindMatrixInverse.clone().multiply(blended).multiply(mesh.bindMatrix);
        const actual = new Vector3().fromBufferAttribute(attribute, i).applyMatrix3(new Matrix3().setFromMatrix4(transform)).applyMatrix3(new Matrix3().getNormalMatrix(mesh.matrixWorld)).normalize();
        const [x, y, z] = sample.parts[region].four.normalWorldCorners[corner], expected = new Vector3(x, z, -y);
        const error = actual.distanceTo(expected); if (error > maximum) { maximum = error; worst = { exportRow: i, nativeCorner: corner, vectorError: error, actual: actual.toArray(), expected: expected.toArray() }; }
        if (protectedIDs.has(nativeIDs[i])) {
          protectedRows++;
          if (error > protectedMaximum) { protectedMaximum = error; protectedWorst = { exportRow: i, nativeVertex: nativeIDs[i], nativeCorner: corner, vectorError: error, actual: actual.toArray(), expected: expected.toArray() }; }
        }
      }
      normalParity = { status: 'SAMPLED_CPU_SHADER_FORMULA_NORMAL_COMPARISON', maximumVectorError: maximum, worst, protectedHeadSubset: protectedIDs.size ? { status: 'SAMPLED', protectedRows, maximumVectorError: protectedMaximum, worst: protectedWorst } : { status: 'UNDECLARED' }, gpuReadback: false };
    }
    comparisons.push({ region, ...result, normalParity });
  }
  records.push({ index: sample.index, case: sample.case, comparisons });
}
fs.writeFileSync(output, JSON.stringify({ status: 'UNACCEPTED_NATIVE_TO_INSTALLED_THREE_CPU_COMPARISON', glbSHA256: sha(bytes), nativeReportSHA256: sha(reportBytes), mappingSHA256: sha(mappingBytes), records,
  limits: ['Installed GLTFLoader and SkinnedMesh four-slot consumption; texture decoding deliberately omitted. No material/actual browser/GPU parity claim.', 'Native evaluated full/four positions and normals stay distinct reference fields.', 'A CPU skin/formula comparison does not qualify coverage, contact, support, moving art or device performance.'] }, null, 2) + '\n');
