/** Read-only selected jeans / actual finite saddle measurement from played Garage TRS.
 * node harness/rider-rebuild/seat-contact-review.mjs --build-inputs=JSON --contract=JSON
 *   --components=JSON --rookie-report=JSON --pro-report=JSON --out=FRESH_JSON
 * Optional --regional-lineage=JSON from seat-regional-lineage.py adds the exact existing pelvis-rear region.
 * No controller, pose, geometry, image or physics writes. Parent executes under lease.
 */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { Quaternion, Vector3 } from 'three';
import { load, mesh, triangle, finiteSupport, M, V, sha, pinned } from '../../assets/blender/rider-rebuild/selected-ankle-contact02/surface.mjs';

const arg = name => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3);
const file = name => { const path = arg(name); assert(path, `Missing --${name}`); const bytes = fs.readFileSync(path); return { pin: { path, sha256: sha(bytes) }, value: JSON.parse(bytes) }; };
const build = file('build-inputs'), contractFile = file('contract'), components = file('components');
const contract = contractFile.value, inputs = build.value;
assert.equal(contractFile.pin.sha256, inputs.metadataSHA256);
assert.equal(contract.glbSHA256, inputs.sourceSHA256);
const sourcePin = { path: inputs.source, sha256: inputs.sourceSHA256 };
const raw = await load(sourcePin), document = raw.document;
const jeansName = contract.specification.meshNames.jeans ?? 'RiderJeans';
assert(Object.values(contract.specification.meshNames).includes(jeansName));
const jeans = mesh(raw, jeansName), jeansNode = raw.node(jeansName);
const skin = document.skins[jeansNode.value.skin]; assert.equal(skin.joints.length, 75);
const primitive = document.meshes[jeansNode.value.mesh].primitives[0];
const joints = raw.read(primitive.attributes.JOINTS_0), weights = raw.read(primitive.attributes.WEIGHTS_0);
const inverse = raw.read(skin.inverseBindMatrices);
const inverseBinds = skin.joints.map((_, index) => M().fromArray(inverse.row(index)));
assert(inputs.poseCalibration, 'Pin the actual build pose calibration');
const calibration = JSON.parse(pinned(inputs.poseCalibration));
assert.equal(calibration.sourceSHA256, sourcePin.sha256);
assert.deepEqual(calibration.driver, inputs.poseCalibration.driver, 'Embedded build driver differs from pinned calibration');
const driver = { ...contract.driver, ...calibration.driver };
const placement = M().makeRotationFromQuaternion(new Quaternion().fromArray(driver.assetToBikeQuaternionXYZW));
const ids = Object.keys(contract.specification.jointNames).sort();
let regionalLineage = null, regionalRows = null;
if (arg('regional-lineage')) {
  regionalLineage = file('regional-lineage'); const lineage = regionalLineage.value;
  assert.equal(lineage.region, 'pelvis-rear'); assert.equal(lineage.object, jeansName);
  assert.equal(lineage.regionalReceiverNativePositionsAndFaceMembershipExact, true);
  const context = JSON.parse(pinned(lineage.sourceContext)), report = JSON.parse(pinned(lineage.sourceReport));
  assert.deepEqual(lineage.sourceNative, context.native); assert.deepEqual(lineage.sourceNative, report.resultNative);
  const capture = report.capture.find(row => row.region === 'pelvis-rear');
  assert.equal(capture.sha256, lineage.directCapture.sha256); assert.equal(capture.path, lineage.directCapture.path);
  assert(capture.passed);
  const sourcePositions = new Map(lineage.nativeRestPositions);
  for (let row = 0; row < jeans.position.count; row++) {
    const expected = sourcePositions.get(jeans.nativeID(row)); if (!expected) continue;
    const actual = jeans.position.row(row), exported = [expected[0], expected[2], -expected[1]];
    assert(actual.every((value, axis) => value === exported[axis]), 'Regional native rest positions changed');
  }
  const key = ids => [...ids].sort((a, b) => a - b).join(',');
  const sourceTriangles = new Map(lineage.nativeTriangles.map(row => [key(row.nativeVertexIDs), row]));
  assert.equal(sourceTriangles.size, lineage.nativeTriangles.length);
  const seen = new Set(); regionalRows = [];
  for (let row = 0; row < jeans.indices.count / 3; row++) {
    const nativeIDs = [0, 1, 2].map(axis => jeans.nativeID(jeans.indices.get(row * 3 + axis)));
    const identity = key(nativeIDs), original = sourceTriangles.get(identity); if (!original) continue;
    assert(!seen.has(identity), 'Duplicate current native regional triangle'); seen.add(identity);
    assert([0, 1, 2].some(offset => nativeIDs.every((id, axis) => id === original.nativeVertexIDs[(axis + offset) % 3])), 'Regional triangle winding changed');
    regionalRows.push(row);
  }
  assert.equal(seen.size, sourceTriangles.size, 'Original regional native triangles missing from current GLB');
}
const restLocal = document.nodes.map(node => node.matrix ? M().fromArray(node.matrix)
  : M().compose(V(node.translation ?? [0, 0, 0]), new Quaternion().fromArray(node.rotation ?? [0, 0, 0, 1]), V(node.scale ?? [1, 1, 1])));
const names = new Map(document.nodes.map((node, index) => [node.name, index]));
const output = { accepted: false, recipeSHA256: sha(fs.readFileSync(new URL(import.meta.url))),
  inputs: { build: build.pin, contract: contractFile.pin, source: sourcePin, components: components.pin,
    calibration: { path: inputs.poseCalibration.path, sha256: inputs.poseCalibration.sha256 },
    surfaceHelper: { path: 'assets/blender/rider-rebuild/selected-ankle-contact02/surface.mjs', sha256: sha(fs.readFileSync(new URL('../../assets/blender/rider-rebuild/selected-ankle-contact02/surface.mjs', import.meta.url))) } },
  method: 'Recorded native75 local TRS; decoded source FOUR skinning; exact selected saddle component triangles; downward jeans/upward saddle finite XZ footprint extrema.',
  regionalLineage: regionalLineage ? { receipt: regionalLineage.pin, sourceNative: regionalLineage.value.sourceNative,
    directCapture: regionalLineage.value.directCapture, originalPolygonIDs: regionalLineage.value.originalPolygonIDs,
    currentDecodedTriangleRows: regionalRows, exactNativeTriangleWindingAndRestPositions: true,
    classification: regionalLineage.value.classification } : null,
  classification: 'All downward selected jeans triangles over the finite saddle are candidates. Posterior/buttock identity requires parent review of explicit source/native triangle witnesses; no bone label establishes support.',
  limits: ['Five captured poses per bike, not continuous motion or cloth dynamics.',
    'Signed bike-up gap and projected overlap are geometry only; no support force/contact-area or seated-art acceptance.',
    'Vertical faces/projection degeneracies follow the existing finiteSupport helper. No closed-volume/global collision proof.',
    'No pose correction, source mesh change, root offset, limb stretching or physical COM mutation.'], bikes: [] };

function posedVertices(snapshot) {
  assert.equal(snapshot.boneLocalTRS.length, 75);
  assert.deepEqual(snapshot.boneLocalTRS.map(row => row.id).sort(), ids);
  assert(snapshot.attachedToBikeFrame); assert.deepEqual(snapshot.placementBike, [0, 0, 0]);
  assert.equal(snapshot.debug.candidate.sourceSHA256, sourcePin.sha256);
  const locals = restLocal.slice(), world = [];
  for (const row of snapshot.boneLocalTRS) {
    for (const [key, size] of [['translation', 3], ['rotationXYZW', 4], ['scale', 3]]) {
      assert.equal(row[key].length, size); assert(row[key].every(Number.isFinite));
    }
    const index = names.get(contract.specification.jointNames[row.id]); assert.notEqual(index, undefined);
    locals[index] = M().compose(V(row.translation), new Quaternion().fromArray(row.rotationXYZW), V(row.scale));
  }
  const walk = (index, parent) => { world[index] = parent.clone().multiply(locals[index]);
    for (const child of document.nodes[index].children ?? []) walk(child, world[index]); };
  for (const index of document.scenes[document.scene ?? 0].nodes) walk(index, M());
  const role = name => { const value = contract.specification.roles[name]; return Array.isArray(value) ? value[0] : value; };
  const boneMatrix = id => placement.clone().multiply(world[names.get(contract.specification.jointNames[id])]);
  const point = matrix => new Vector3().setFromMatrixPosition(matrix);
  const carrier = point(boneMatrix(role('pelvis'))), hips = snapshot.debug.anthropometry.hips;
  // Existing native-rest head qualification and physical XY tests use 1e-5m.
  // Compare reconstruction to saved carrier/sole diagnostics, without a broader epsilon.
  const toleranceM = 1e-5, carrierResidualM = carrier.distanceTo(V([hips[0], hips[1], 0]));
  assert(carrierResidualM < toleranceM, 'Reconstructed carrier differs from recorded inverse hips');
  const skeletalWitnesses = { toleranceM, carrierBike: carrier.toArray(), carrierResidualM, sides: [] };
  for (const [index, side] of ['left', 'right'].entries()) {
    const suffix = side === 'left' ? 'Left' : 'Right', foot = boneMatrix(role('foot' + suffix));
    const sole = point(foot.clone().multiply(M().fromArray(driver.selectedSoleInFoot[side])));
    const residualM = sole.distanceTo(V(driver.selectedPegSurfaceBike[side]));
    assert(Math.abs(residualM - snapshot.debug.soleErr[index]) < toleranceM, 'Reconstructed sole differs from saved diagnostic');
    const palmName = contract.specification.hands[side].socketNodeName;
    skeletalWitnesses.sides.push({ side, hipBike: point(boneMatrix(role('thigh' + suffix))).toArray(),
      ankleBike: point(foot).toArray(), palmBike: point(placement.clone().multiply(world[names.get(palmName)])).toArray(),
      selectedSoleBike: sole.toArray(), reconstructedSoleErrM: residualM, recordedSoleErrM: snapshot.debug.soleErr[index] });
  }
  // glTF inverse binds map primitive POSITION directly into each joint frame.
  // Parent placement then maps the reconstructed source scene to actual bike space.
  const matrices = skin.joints.map((index, slot) => placement.clone().multiply(world[index]).multiply(inverseBinds[slot]));
  const vertices = Array.from({ length: jeans.position.count }, (_, index) => {
    const position = V(jeans.position.row(index)), result = new Vector3(); let sum = 0;
    for (let slot = 0; slot < 4; slot++) {
      const weight = weights.get(index, slot); assert(Number.isFinite(weight) && weight >= 0);
      if (!weight) continue;
      const joint = joints.get(index, slot); assert(Number.isInteger(joint) && matrices[joint]);
      result.addScaledVector(position.clone().applyMatrix4(matrices[joint]), weight); sum += weight;
    }
    assert(Math.abs(sum - 1) < 2e-5); assert(result.toArray().every(Number.isFinite)); return result;
  });
  return { vertices, skeletalWitnesses };
}

function overlapPolygon(a, b) {
  const cross = (p, q, r) => (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]);
  const clip = b.points.map(point => [point.x, point.z]), orientation = Math.sign(cross(...clip));
  let polygon = a.points.map(point => [point.x, point.z]);
  for (let edge = 0; edge < 3 && polygon.length; edge++) {
    const start = clip[edge], end = clip[(edge + 1) % 3], input = polygon; polygon = [];
    for (let index = 0; index < input.length; index++) {
      const p = input[index], q = input[(index + 1) % input.length];
      const dp = orientation * cross(start, end, p), dq = orientation * cross(start, end, q);
      if (dp >= 0) polygon.push(p);
      if ((dp < 0) !== (dq < 0)) { const t = dp / (dp - dq); polygon.push([p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])]); }
    }
  }
  const area = Math.abs(polygon.reduce((sum, p, index) => { const q = polygon[(index + 1) % polygon.length]; return sum + p[0] * q[1] - p[1] * q[0]; }, 0)) / 2;
  return { polygonXZ: polygon, projectedAreaM2: area };
}

function witnessRecord(witness, vertices, upward) {
  const cloth = triangle(vertices, witness.bootVertexRows, witness.bootTriangleRow);
  const target = upward.find(row => row.row === witness.pegTriangleRow); assert(target);
  return { jeansTriangleRow: witness.bootTriangleRow, jeansDecodedVertexRows: witness.bootVertexRows,
    jeansNativeVertexIDs: witness.bootNativeIDs, jeansBarycentric: witness.bootBarycentric,
    jeansPointBike: witness.bootPoint, jeansNormalBike: witness.bootNormal,
    jeansNamedFOUR: witness.bootVertexRows.map(index => jeans.fields(index)),
    saddleTriangleRow: witness.pegTriangleRow, saddleDecodedVertexRows: witness.pegVertexRows,
    saddleBarycentric: witness.pegBarycentric, saddlePointBike: witness.pegPoint, saddleNormalBike: witness.pegNormal,
    normalsOpposition: -V(witness.bootNormal).dot(V(witness.pegNormal)),
    ...overlapPolygon(cloth, target), posteriorClassification: 'PARENT_REVIEW_REQUIRED' };
}

for (const bikeName of ['rookie', 'pro']) {
  const played = file(`${bikeName}-report`), report = played.value;
  assert.equal(report.requestedBike, bikeName); assert.equal(report.requestedClip, null); assert.deepEqual(report.errors, []);
  assert.equal(report.contract.sha256, contractFile.pin.sha256); assert.equal(report.snapshots.length, 5);
  const logical = `models/bike-${bikeName}.glb`;
  const inventory = components.value.reports.find(row => row.logical === logical); assert(inventory);
  assert.equal(inventory.assetSHA256, report.bikeAsset.sha256);
  const source = inventory.sources.find(row => row.sourceNodeName === 'bodywork'); assert(source);
  const saddle = source.components.find(row => row.component === 3); assert(saddle);
  const bikePin = { path: `public/${logical}`, sha256: inventory.assetSHA256 }, bike = await load(bikePin);
  const shift = bike.node('attach_frame_origin').point;
  assert.deepEqual(shift.toArray(), inventory.frameOriginFileFrameM);
  const bodyworkNode = bike.node('bodywork');
  assert.deepEqual(bodyworkNode.world.toArray(), source.sourceNodeMatrixWorld);
  const bodywork = mesh(bike, 'bodywork', M().makeTranslation(-shift.x, -shift.y, -shift.z));
  const bikeVertices = Array.from({ length: bodywork.position.count }, (_, index) => bodywork.point(index));
  const saddleRows = saddle.sourceTriangleOrdinals.map(row => triangle(bikeVertices,
    [0, 1, 2].map(axis => bodywork.indices.get(row * 3 + axis)), row));
  const upward = saddleRows.filter(row => row.normal.y > 1e-9);
  const bikeResult = { name: bikeName, report: played.pin, bike: bikePin, saddleSource: {
    component: 3, node: 'bodywork', nodeIndex: source.nodeIndex, sourceMeshIndex: source.sourceMeshIndex,
    primitiveIndex: source.primitiveIndex, sourceTriangleOrdinals: saddle.sourceTriangleOrdinals,
    allTriangles: saddleRows.length, upwardTriangles: upward.length,
    classification: 'Previously parent-selected saddle shell; source hash exactly matches this played bike.' }, snapshots: [] };
  for (const snapshot of report.snapshots) {
    const { vertices, skeletalWitnesses } = posedVertices(snapshot), all = new Array(vertices.length).fill(true);
    let measured;
    try { measured = finiteSupport(jeans, vertices, all, upward); }
    catch (error) { if (!error.message.includes('footprints do not overlap')) throw error;
      bikeResult.snapshots.push({ name: snapshot.name, riderStageTime: snapshot.riderStageTime, skeletalWitnesses, overlap: false }); continue; }
    const witness = measured.minimum;
    let regionalPosterior = null;
    if (regionalRows) {
      const surface = { ...jeans, indices: { count: regionalRows.length * 3,
        get: index => jeans.indices.get(regionalRows[Math.floor(index / 3)] * 3 + index % 3) } };
      try {
        const measured = finiteSupport(surface, vertices, all, upward);
        measured.minimum.bootTriangleRow = regionalRows[measured.minimum.bootTriangleRow];
        regionalPosterior = { overlap: true, minimumSignedBikeUpGapM: measured.minimum.gapM,
          comparedTrianglePairs: measured.compared, downwardRegionalTriangles: measured.downwardRigidTriangles,
          witness: witnessRecord(measured.minimum, vertices, upward),
          classification: 'Exact existing pelvis-rear transfer region; actual posterior support patch remains parent-reviewed.' };
      } catch (error) { if (!error.message.includes('footprints do not overlap')) throw error;
        regionalPosterior = { overlap: false, classification: 'No downward existing pelvis-rear triangle overlaps the finite upward saddle footprint.' }; }
    }
    bikeResult.snapshots.push({ name: snapshot.name, riderStageTime: snapshot.riderStageTime, skeletalWitnesses, overlap: true,
      comparedTrianglePairs: measured.compared, downwardJeansTriangles: measured.downwardRigidTriangles,
      minimumSignedBikeUpGapM: witness.gapM,
      witness: witnessRecord(witness, vertices, upward), regionalPosterior,
      existingContactDiagnostics: { gripErrM: snapshot.debug.gripErr, soleErrM: snapshot.debug.soleErr,
        anthropometry: snapshot.debug.anthropometry } });
  }
  output.bikes.push(bikeResult);
}
const out = arg('out'); assert(out && !fs.existsSync(out), 'Use fresh --out');
fs.writeFileSync(out, JSON.stringify(output, null, 2) + '\n');
console.log(JSON.stringify({ out, accepted: false, bikes: output.bikes.map(bike => ({ name: bike.name,
  snapshots: bike.snapshots.map(row => ({ name: row.name, gapM: row.minimumSignedBikeUpGapM, overlap: row.overlap })) })) }));
