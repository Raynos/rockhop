/** Source-only ancestry proof and isolated calibration03 comparison contract.
 * node --max-old-space-size=256 prepare-gameplay-calibrated09.mjs INPUT.json FRESH_OUT
 * Streams original BIN hashes; does not decode meshes or load a browser/Blender.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('../../', import.meta.url));
const FIELDS = ['selectedSoleInFoot', 'selectedPegSurfaceBike', 'soleQuaternionBike', 'maxSpineFlexRadians'];
async function hash(filename, options = {}) {
  const h = crypto.createHash('sha256');
  for await (const bytes of fs.createReadStream(filename, { highWaterMark: 1024 * 1024, ...options })) h.update(bytes);
  return h.digest('hex');
}
async function pin(filename) { return { path: path.relative(ROOT, filename), sha256: await hash(filename) }; }
async function pinned(row) {
  assert(row && Object.keys(row).sort().join(',') === 'path,sha256' && /^[0-9a-f]{64}$/.test(row.sha256));
  assert(!path.isAbsolute(row.path) && !row.path.split('/').includes('..'));
  const filename = path.resolve(ROOT, row.path); assert(filename.startsWith(ROOT));
  assert.equal(await hash(filename), row.sha256, row.path); return filename;
}
function glbHeader(filename) {
  const fd = fs.openSync(filename, 'r');
  try {
    const header = Buffer.alloc(20); assert.equal(fs.readSync(fd, header), 20);
    assert.equal(header.toString('ascii', 0, 4), 'glTF'); assert.equal(header.readUInt32LE(4), 2);
    assert.equal(header.readUInt32LE(8), fs.statSync(filename).size); assert.equal(header.readUInt32LE(16), 0x4e4f534a);
    const length = header.readUInt32LE(12); assert(length < 1024 * 1024, 'Only a bounded source header is needed');
    const bytes = Buffer.alloc(length); assert.equal(fs.readSync(fd, bytes), length);
    const document = JSON.parse(bytes), bin = Buffer.alloc(8); assert.equal(fs.readSync(fd, bin), 8);
    assert.equal(bin.readUInt32LE(4), 0x004e4942);
    return { document, offset: length + 28, length: bin.readUInt32LE(0) };
  } finally { fs.closeSync(fd); }
}

const [inputName, outputName] = process.argv.slice(2); assert(inputName && outputName);
const inputPath = path.resolve(inputName), out = path.resolve(outputName), input = JSON.parse(fs.readFileSync(inputPath));
assert.equal(input.accepted, false);
assert(out.startsWith(path.join(ROOT, 'harness/out/rider-rebuild/selected-authoring-motion11/')) && !fs.existsSync(out));
assert.deepEqual(Object.keys(input.pins).sort(), ['ancestorContract', 'baselineContract', 'calibration', 'playedPacket', 'transportReceipt', 'weightContract']);
const data = {};
for (const [name, row] of Object.entries(input.pins)) data[name] = JSON.parse(fs.readFileSync(await pinned(row)));
const { ancestorContract: ancestor, baselineContract: baseline, calibration, playedPacket: packet,
  transportReceipt: transport, weightContract: weight } = data;
assert.equal(baseline.qualificationState, 'UNACCEPTED_GAMEPLAY_LEAN_REVIEW');
assert.equal(baseline.accepted, false); assert(!baseline.previewClip && !baseline.corrective && !baseline.nativeAuthoringMotion);
assert.equal(weight.weightDerivative.kind, 'native-regional-weight-only');
assert.equal(weight.weightDerivative.object, 'RiderJeans');
assert.equal(weight.weightDerivative.protectedRestGeometryUVMapsAnd75InverseBindsExact, true);
assert.equal(weight.weightDerivative.untouchedGLBFieldsExactlyOriginal, true);
assert.deepEqual(baseline.weightDerivative, weight.weightDerivative);
assert.deepEqual(baseline.specification, weight.specification); assert.deepEqual(weight.specification, ancestor.specification);
assert.deepEqual(baseline.nativeRest, weight.nativeRest); assert.deepEqual(weight.nativeRest, ancestor.nativeRest);
assert.deepEqual(baseline.driver, weight.driver);
assert.equal(baseline.glbSHA256, weight.glbSHA256); assert.equal(transport.glb.sha256, weight.glbSHA256);
assert.deepEqual(transport.contract, input.pins.weightContract);
assert.deepEqual(transport.sourcePins.engineContract, input.pins.ancestorContract);
assert.equal(calibration.sourceSHA256, transport.sourcePins.engineRider.sha256);
assert.equal(packet.sourceSHA256, calibration.sourceSHA256); assert.equal(packet.contractSHA256, input.pins.ancestorContract.sha256);
assert.deepEqual(packet.calibration, input.pins.calibration); assert.equal(packet.accepted, false);
assert.equal(calibration.accepted, false); assert.deepEqual(Object.keys(calibration.driver).sort(), [...FIELDS].sort());
assert.equal(calibration.driver.maxSpineFlexRadians, Math.PI / 9);
assert(!Object.hasOwn(calibration.driver, 'gripSocketQuaternionBike') && !Object.hasOwn(baseline.driver, 'gripSocketQuaternionBike'));
for (const row of calibration.bikes) await pinned(row);
for (const row of baseline.gameplayLeanReview.sourcePins) await pinned(row);
const originalFile = await pinned(transport.sourcePins.engineRider), selectedFile = await pinned(transport.glb);
const original = glbHeader(originalFile), selected = glbHeader(selectedFile), a = original.document, b = selected.document;
for (const key of ['nodes', 'skins', 'materials', 'images', 'textures', 'samplers', 'scenes', 'scene']) assert.deepEqual(a[key], b[key], key);
for (const key of ['accessors', 'bufferViews']) assert.deepEqual(a[key], b[key].slice(0, a[key].length), key);
assert.equal(a.meshes.length, 7); assert.equal(b.meshes.length, 7);
const jeansNode = a.nodes.find(node => node.name === 'RiderJeans'); assert(jeansNode && Number.isInteger(jeansNode.mesh));
const restoredMeshes = structuredClone(b.meshes);
for (const [index, mesh] of a.meshes.entries()) {
  if (index !== jeansNode.mesh) { assert.deepEqual(mesh, b.meshes[index]); continue; }
  assert.equal(mesh.primitives.length, b.meshes[index].primitives.length);
  for (let i = 0; i < mesh.primitives.length; i++) {
    for (const field of ['JOINTS_0', 'WEIGHTS_0']) {
      assert(b.meshes[index].primitives[i].attributes[field] >= a.accessors.length);
      restoredMeshes[index].primitives[i].attributes[field] = mesh.primitives[i].attributes[field];
    }
  }
}
assert.deepEqual(restoredMeshes, a.meshes, 'Only declared jeans joint/weight accessor references may differ');
assert.equal(original.length, transport.originalBinaryBytesPreserved);
assert(selected.length >= original.length);
const originalBinary = await hash(originalFile, { start: original.offset, end: original.offset + original.length - 1 });
assert.equal(await hash(selectedFile, { start: selected.offset, end: selected.offset + original.length - 1 }), originalBinary);
assert.equal(originalBinary, weight.weightDerivative.originalBinarySHA256);
const result = structuredClone(baseline);
for (const field of FIELDS) { assert(!Object.hasOwn(result.driver, field)); result.driver[field] = structuredClone(calibration.driver[field]); }
result.gameplayLeanReview.calibrationComparison = { accepted: false, kind: 'source-compatible-calibration03-private-comparison',
  source: input.pins.calibration, ancestorGLB: transport.sourcePins.engineRider, currentGLB: transport.glb,
  baselineContract: input.pins.baselineContract, addedDriverFields: FIELDS,
  gripOrientationInjected: false, input: await pin(inputPath), recipe: await pin(fileURLToPath(import.meta.url)),
  limits: ['Restore the prior limited private calibration on exact preserved boot/rest ancestry; contact and moving art remain unaccepted.',
    'pi/9 is the existing evaluated solver envelope, not an anatomical range acceptance.',
    'No grip quaternion is supplied by calibration03; retain the existing canonical hand-axis fallback.',
    'Use actual coasting neutral/forward/backward/return inputs and compare both bikes against the frozen baseline.'] };
const check = structuredClone(result); delete check.gameplayLeanReview.calibrationComparison;
for (const field of FIELDS) delete check.driver[field]; assert.deepEqual(check, baseline, 'No unrelated contract change');
fs.mkdirSync(out); const contractPath = path.join(out, 'rider-contract.json');
fs.writeFileSync(contractPath, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
const receipt = { accepted: false, status: 'CALIBRATION03_ANCESTRY_PASS_ACTUAL_GAMEPLAY_COMPARISON_PENDING',
  input: await pin(inputPath), recipe: await pin(fileURLToPath(import.meta.url)), sourcePins: input.pins,
  selectedGLB: transport.glb, native: weight.weightDerivative.native, contract: await pin(contractPath),
  originalBinaryBytesVerified: original.length, originalBinarySHA256: originalBinary,
  protectedGLTFFieldsExact: ['nodes', 'skins', 'materials', 'images', 'textures', 'samplers', 'scenes', 'scene', 'original accessors and bufferViews'],
  unchangedMeshes: a.meshes.filter((_, i) => i !== jeansNode.mesh).map(mesh => mesh.name),
  changedAncestorPrimitiveFields: ['RiderJeans.JOINTS_0', 'RiderJeans.WEIGHTS_0'],
  addedDriverFields: FIELDS, gripOrientationInjected: false, baselineFileUnchanged: true,
  priorParentJudgment: packet.parentJudgment, limits: result.gameplayLeanReview.calibrationComparison.limits };
for (const row of Object.values(input.pins)) await pinned(row);
fs.writeFileSync(path.join(out, 'receipt.json'), JSON.stringify(receipt, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ out, status: receipt.status, contract: receipt.contract, originalBinaryBytesVerified: original.length,
  addedDriverFields: FIELDS, gripOrientationInjected: false }));
