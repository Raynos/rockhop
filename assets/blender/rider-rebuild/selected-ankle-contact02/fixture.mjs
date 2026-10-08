/** One source-normal-derived ankle pitch, not an angle search or runtime correction. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { Group, Matrix3, Quaternion, Vector3 } from 'three';
import { loadRigAt } from '../../../../src/render/hero/gltfTestUtils.ts';
import { FrameBuilder } from '../../../../src/render/frame.ts';
import { makeRiderRigPose, riderRigFromCOM } from '../../../../src/core/riderGeometry.ts';
import { createPrivateRiderClass } from '../../../../harness/rider-rebuild/private-rider.mjs';
import { resetHumanoidPose } from '../../../../harness/rider-rebuild/new-humanoid-contract.mjs';
import { invertAnthropometricCOM, measureAnthropometricCOM } from '../../../../harness/rider-rebuild/anthropometric-inverse.mjs';
import { V, M, pinned, load, mesh, triangle, finiteSupport } from './surface.mjs';

const arg = name => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3);
const inputPath = arg('input') ?? 'assets/blender/rider-rebuild/selected-ankle-contact02/inputs.json';
const input = JSON.parse(fs.readFileSync(inputPath));
for (const row of input.dependencies) pinned(row);
const metadata = JSON.parse(pinned(input.contract)), calibration = JSON.parse(pinned(input.calibration));
const report = JSON.parse(pinned(input.baseline)), sample = report.samples[input.sampleIndex];
assert(sample.debug.physicalPose && sample.state.faulted === null);
assert.equal(sample.debug.candidate.sourceSHA256, input.source.sha256);
Object.assign(metadata.driver, calibration.driver);
metadata.sourceSHA256 = input.source.sha256;
assert.equal(calibration.sourceSHA256, input.source.sha256);
const raw = await load(input.source), loaded = await loadRigAt(pathToFileURL(input.source.path), true);
const Rider = createPrivateRiderClass(metadata), rider = new Rider(loaded, { complete() {} });
const frame = new Group(); frame.updateWorldMatrix(true, true); rider.attach({ frame });
const f = new FrameBuilder().frame; f.riderBody.present = true; f.rider.lean = sample.state.rider.lean;
const recorded = sample.debug.anthropometry, com = V(recorded.requestedCOM);
const p = { ...riderRigFromCOM(com.x, com.y, recorded.carrierAngle, makeRiderRigPose()), requestedCOM: com };
const flex = recorded.spineFlexRadians;
const suffix = side => side === 'left' ? 'Left' : 'Right';
const normal = (value, matrix) => value.clone().applyMatrix3(new Matrix3().getNormalMatrix(matrix)).normalize();
const fromPoint = matrix => new Vector3().setFromMatrixPosition(matrix);
const foot = side => rider.bone(rider.role('foot' + suffix(side)));
const pose = hips => {
  resetHumanoidPose(rider.binding); rider.poseFromHips(f, p, hips, flex);
  rider.scene.updateWorldMatrix(true, true);
  return measureAnthropometricCOM(rider, rider.anthropometry);
};
const diagnostics = () => ({ gripErrM: [...rider.debug.gripErr], soleErrM: [...rider.debug.soleErr],
  armDemand: [...rider.debug.armStretch], legDemand: [...rider.debug.legStretch],
  measuredCOM: measureAnthropometricCOM(rider, rider.anthropometry).toArray(),
  residualXYZM: measureAnthropometricCOM(rider, rider.anthropometry).sub(com).toArray(),
  all75Finite: rider.binding.byId.size === 75 && [...rider.binding.byId.values()].every(bone =>
    [...bone.position.toArray(), ...bone.quaternion.toArray(), ...bone.scale.toArray(), ...bone.matrixWorld.elements].every(Number.isFinite)) });
const originals = new Map([...rider.soleFrames].map(([side, row]) => [side,
  { ...row, local: row.local.clone(), targetQ: row.targetQ.clone(), selectedPeg: [...row.selectedPeg] }]));
const lateralSource = raw.node(metadata.specification.jointNames[rider.role('footLeft')]).point.clone()
  .sub(raw.node(metadata.specification.jointNames[rider.role('footRight')]).point).normalize();
const sourceToBike = new Quaternion().fromArray(metadata.driver.assetToBikeQuaternionXYZW);
const boots = new Map();
const toeRest = new Map(['left', 'right'].map(side => {
  const bone = rider.bone(rider.role('toe' + suffix(side)));
  return [side, [...bone.position.toArray(), ...bone.quaternion.toArray(), ...bone.scale.toArray()]];
}));
const extent = values => values.reduce(([minimum, maximum], value) => [Math.min(minimum, value), Math.max(maximum, value)], [Infinity, -Infinity]);
for (const side of ['left', 'right']) {
  const footName = metadata.specification.jointNames[rider.role('foot' + suffix(side))];
  const sourceFoot = raw.node(footName), boot = mesh(raw, 'ActualSelectedBoot.' + (side === 'left' ? 'L' : 'R'), sourceFoot.world.clone().invert());
  const vertices = Array.from({ length: boot.position.count }, (_, index) => boot.point(index));
  const rigid = vertices.map((_, index) => { const fields = boot.fields(index); return fields.length === 1 && fields[0][0] === footName && fields[0][1] === 1; });
  boots.set(side, { sourceFoot, boot, vertices, rigid });
}
const result = { accepted: false, inputs: input, sample: { index: input.sampleIndex, tick: sample.tick, time: sample.state.time,
  recordedPhysicalPose: sample.debug.physicalPose, recordedFault: sample.state.faulted, requestedCOM: com.toArray(),
  fixedCarrierAngle: p.torsoAngle, fixedSpineFlexRadians: flex, recordedHips: recorded.hips }, bikes: [],
  construction: 'One signed pitch aligns the selected source-normal projection to the actual peg normal about the anatomical ankle and source bilateral ankle axis projected into that peg plane. Ankle fore-aft position stays fixed during pitch; whole rigid-foot triangles then settle vertically to first finite mesh support and derive the new bearing point. No angle bound or search.',
  limits: 'Unaccepted geometric fixture. Only own-foot weight=1 triangles and upward peg height surfaces are certified. Mixed/toe/shin regions, other bike collisions, anatomical ankle range, moving art and global feasibility remain unqualified. XY mass-proxy inverse; actual lateral COM is reported. No runtime/physics/source geometry changes.' };

for (const bikeInput of input.bikes) {
  const bike = await load(bikeInput), audit = JSON.parse(pinned(bikeInput.audit));
  const shift = bike.node('attach_frame_origin').point, chassisOffset = shift.clone().sub(bike.node('attach_chassis_com').point);
  const bikeMesh = mesh(bike, 'pegs', M().makeTranslation(-shift.x, -shift.y, -shift.z));
  const pegVertices = Array.from({ length: bikeMesh.position.count }, (_, index) => bikeMesh.point(index));
  const pegs = Array.from({ length: bikeMesh.indices.count / 3 }, (_, row) =>
    triangle(pegVertices, [0, 1, 2].map(axis => bikeMesh.indices.get(row * 3 + axis)), row)).filter(row => row.normal.y > 1e-9);
  const angle = sample.state.bike.angle, worldQ = new Quaternion().setFromAxisAngle(V([0, 0, 1]), angle);
  const translation = chassisOffset.clone().applyQuaternion(worldQ).add(V([sample.state.bike.pos.x, sample.state.bike.pos.y, 0]));
  const recordedBikeWorld = M().compose(translation, worldQ, V([1, 1, 1]));
  for (const [side, original] of originals) rider.soleFrames.set(side, { ...original, local: original.local.clone(), targetQ: original.targetQ.clone() });
  pose(recorded.hips);
  const row = { bike: bikeInput.name, fixtureFrame: 'bike asset frame after actual attach_frame_origin shift',
    worldFrame: { matrix: recordedBikeWorld.toArray(), source: 'GltfBike.placeFromChassis; recorded state bike pose and actual frame_origin - chassis_com markers',
      note: bikeInput.name === 'pro' ? 'Failing recorded Pro state' : 'Same Pro state applied to Rookie geometry; not a recorded Rookie sample' },
    reconstructedBaseline: diagnostics(), recordedBaseline: { gripErrM: sample.debug.gripErr, soleErrM: sample.debug.soleErr }, sides: [] };
  for (const side of ['left', 'right']) {
    const { sourceFoot, boot, vertices, rigid } = boots.get(side), original = originals.get(side);
    const witness = audit.boots.find(row => row.side === side), sourceWitness = witness.supportPointSource;
    const ids = sourceWitness.decodedVertexRows;
    assert(ids.every(index => rigid[index]), 'Selected original witness must be rigid own-foot geometry');
    assert.deepEqual(ids.map(index => boot.nativeID(index)), sourceWitness.nativeVertexIDs);
    const localPoint = ids.reduce((sum, index, axis) => sum.addScaledVector(vertices[index], sourceWitness.barycentric[axis]), new Vector3());
    const sourceNormal = V(sourceWitness.normal), localNormal = normal(sourceNormal, sourceFoot.world.clone().invert());
    const originalTarget = M().compose(V(original.selectedPeg), original.targetQ, V([1, 1, 1])).multiply(original.local.clone().invert());
    const pegNormal = V(witness.finitePegPoint.normal), axis = lateralSource.clone().applyQuaternion(sourceToBike);
    axis.addScaledVector(pegNormal, -axis.dot(pegNormal)).normalize(); assert(axis.lengthSq() > 0.99);
    const currentNormal = normal(localNormal, originalTarget), wanted = pegNormal.clone().negate();
    const a = currentNormal.clone().addScaledVector(axis, -currentNormal.dot(axis)).normalize();
    const b = wanted.clone().addScaledVector(axis, -wanted.dot(axis)).normalize();
    const pitch = Math.atan2(axis.dot(new Vector3().crossVectors(a, b)), a.dot(b));
    const rotation = M().makeRotationAxis(axis, pitch), pivot = fromPoint(originalTarget);
    const proposed = M().makeTranslation(...pivot.toArray()).multiply(rotation)
      .multiply(M().makeTranslation(...pivot.clone().negate().toArray())).multiply(originalTarget);
    const sidePegs = pegs.filter(peg => peg.points.every(point => Math.sign(point.z) === metadata.driver.sideZ[side]));
    const support = finiteSupport(boot, vertices.map(point => point.clone().applyMatrix4(proposed)), rigid, sidePegs);
    const settleY = -support.minimum.gapM; proposed.elements[13] += settleY;
    const contactLocal = support.minimum.bootVertexRows.reduce((sum, index, axis) =>
      sum.addScaledVector(vertices[index], support.minimum.bootBarycentric[axis]), new Vector3());
    const contactBike = V(support.minimum.pegPoint), newLocal = original.local.clone().setPosition(contactLocal);
    const newSoleBike = proposed.clone().multiply(newLocal);
    rider.soleFrames.set(side, { ...original, local: newLocal, selectedPeg: contactBike.toArray(),
      targetQ: new Quaternion().setFromRotationMatrix(newSoleBike).normalize() });
    const tangent = raw.node(metadata.specification.jointNames[rider.role('toe' + suffix(side))]).point.clone().sub(sourceFoot.point);
    tangent.addScaledVector(sourceNormal, -tangent.dot(sourceNormal)).normalize();
    const sourcePoints = vertices.map(point => point.clone().applyMatrix4(sourceFoot.world));
    const progress = points => points.map(point => point.clone().sub(sourceFoot.point).dot(tangent));
    const full = progress(sourcePoints), own = progress(sourcePoints.filter((_, index) => rigid[index]));
    row.sides.push({ side, rigidVertexCount: rigid.filter(Boolean).length, excludedVertexCount: rigid.filter(value => !value).length,
      originalWitness: { ...sourceWitness, pointInFoot: localPoint.toArray(), localResidualM: localPoint.distanceTo(fromPoint(original.local)),
        ankleRadiusM: localPoint.length(), soleTangentSource: tangent.toArray(), tangentProgressM: progress([V(sourceWitness.point)])[0],
        toeHeadProgressM: progress([raw.node(metadata.specification.jointNames[rider.role('toe' + suffix(side))]).point])[0],
        fullBootProgressExtentM: extent(full), rigidBootProgressExtentM: extent(own),
        label: 'Measured longitudinal coordinates only; no anatomical arch/toe classification' },
      pitchAxisBike: axis.toArray(), pitchRadians: pitch, settleYM: settleY, finiteSupportBeforeSettlement: support,
      newContactFields: support.minimum.bootVertexRows.map(index => boot.fields(index)),
      newContactNormalsOpposition: -V(support.minimum.bootNormal).dot(V(support.minimum.pegNormal)),
      proposed: { ankleBike: proposed.toArray(), ankleRecordedWorld: recordedBikeWorld.clone().multiply(proposed).toArray(),
        contactPointInFoot: contactLocal.toArray(), contactPointBike: contactBike.toArray(), soleInFoot: newLocal.toArray(),
        soleFrameBike: newSoleBike.toArray(), originalWitnessTransportedBike: localPoint.clone().applyMatrix4(proposed).toArray(),
        normalBike: normal(localNormal, proposed).toArray(), normalOpposition: normal(localNormal, proposed).dot(wanted) } });
  }
  const inverse = invertAnthropometricCOM(pose, com, recorded.hips, 8); pose(inverse.hips);
  row.realized = { inverseXY: inverse, ...diagnostics(), sides: row.sides.map(proposal => {
    const side = proposal.side, bone = foot(side), toe = rider.bone(rider.role('toe' + suffix(side)));
    const { boot, vertices, rigid } = boots.get(side);
    const actual = bone.matrixWorld.clone(), requested = M().fromArray(proposal.proposed.ankleBike);
    const sidePegs = pegs.filter(peg => peg.points.every(point => Math.sign(point.z) === metadata.driver.sideZ[side]));
    const toeTRS = [...toe.position.toArray(), ...toe.quaternion.toArray(), ...toe.scale.toArray()];
    assert.deepEqual(toeTRS, toeRest.get(side), 'Toe follows foot with unchanged authored local TRS');
    let support;
    try { support = finiteSupport(boot, vertices.map(point => point.clone().applyMatrix4(actual)), rigid, sidePegs); }
    catch (error) { if (!error.message.includes('footprints do not overlap')) throw error; support = { overlap: false, reason: error.message }; }
    return { side, ankleBike: actual.toArray(), ankleRecordedWorld: recordedBikeWorld.clone().multiply(actual).toArray(),
      ankleLocalToParent: bone.matrix.toArray(), requestedAnkleLocalToRealizedParent: bone.parent.matrixWorld.clone().invert().multiply(requested).toArray(),
      anklePositionErrorM: fromPoint(actual).distanceTo(fromPoint(requested)),
      finiteSupport: support,
      toeLocalTRS: { position: toe.position.toArray(), quaternion: toe.quaternion.toArray(), scale: toe.scale.toArray() },
      toeParentIsFoot: toe.parent === bone, actualSoleFrameBike: actual.clone().multiply(rider.soleFrames.get(side).local).toArray() };
  }) };
  result.bikes.push(row);
}
const output = arg('out'); assert(output && !fs.existsSync(output), 'Use a fresh --out= receipt path');
fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({ accepted: false, output, bikes: result.bikes.map(row => ({ bike: row.bike,
  pitchRadians: row.sides.map(side => side.pitchRadians), realized: row.realized })) }));
