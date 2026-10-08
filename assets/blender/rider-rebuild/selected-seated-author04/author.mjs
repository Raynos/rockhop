/** Parent-run offline author: node --import tsx <this-file> --out=FRESH_DIRECTORY
 * Selected immutable engine05 and native75 driver. No Blender/render/browser/job launch.
 */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../../../src/render/hero/gltfTestUtils.ts';
import { FrameBuilder } from '../../../../src/render/frame.ts';
import { RIDER_PROFILE } from '../../../../src/core/riderGeometry.ts';
import { createPrivateRiderClass } from '../../../../harness/rider-rebuild/private-rider.mjs';
import { resetHumanoidPose } from '../../../../harness/rider-rebuild/new-humanoid-contract.mjs';
import { load, mesh, M, pinned, sha } from '../selected-ankle-contact02/surface.mjs';
import { EPS, surface, moment, xz, nearest, support, crossings } from './geometry.mjs';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const configPath = path.join(HERE, 'input.json'), input = JSON.parse(fs.readFileSync(configPath));
const outputPath = process.argv.find(v => v.startsWith('--out='))?.slice(6);
assert(outputPath, 'Use --out=FRESH_DIRECTORY');
const out = path.resolve(outputPath), root = path.resolve(HERE, '../../../..');
assert.equal(process.cwd(), root, 'Run from repository root');
assert(out.startsWith(path.join(root, 'harness/out/rider-rebuild/selected-seated-author04/')));
assert(!fs.existsSync(out), 'Refuse to overwrite prior authoring');
for (const row of Object.values(input.pins)) pinned(row);
const read = name => JSON.parse(pinned(input.pins[name]));
const definitions = read('definitions'), patches = read('patches'), measurement = read('measurement');
assert.equal(patches.definitionSHA256, input.pins.definitions.sha256);
const metadata = read('contract'), calibration = read('calibration');
assert.equal(metadata.glbSHA256, input.pins.rider.sha256);
assert.equal(calibration.sourceSHA256, input.pins.rider.sha256);
assert.deepEqual(measurement.bikes.map(b => b.bike), calibration.bikes);
metadata.sourceSHA256 = input.pins.rider.sha256;
metadata.driver.nearSimilarityTolerance = 1e-4; // Existing measured native-rest qualification, no rest edit.
Object.assign(metadata.driver, calibration.driver);
const loaded = await loadRigAt(pathToFileURL(path.resolve(input.pins.rider.path)), true);
const Rider = createPrivateRiderClass(metadata), rider = new Rider(loaded, { complete() {} });
const bikeFrame = new THREE.Group(); bikeFrame.name = 'actual-bike-local-frame';
// Geometry below subtracts the actual file-frame attach_frame_origin, exactly as GltfBike.
rider.attach({ frame: bikeFrame }); rider.setStage(true); rider.setStageTime(0);
bikeFrame.updateMatrixWorld(true);
const frame = new FrameBuilder().frame, neutral = rider.physicsTarget(frame);
assert.equal(rider.binding.byId.size, 75);
const band = definitions.offlineSupportProxies.gapBandM;
const sanitize = name => THREE.PropertyBinding.sanitizeNodeName(name);
const allMeshes = rider.binding.meshes.map(({ role, mesh }) => ({ role, mesh }));
const findMeshes = role => allMeshes.filter(r => r.role === role || r.role.startsWith(role + '.primitive')).map(r => r.mesh);
const jeanMeshes = findMeshes('RiderJeans'), bodyMeshes = findMeshes('RiderBody');
assert.equal(jeanMeshes.length, 1); assert.equal(bodyMeshes.length, 4);
const jeans = jeanMeshes[0];
const key = ids => [...ids].sort((a, b) => a - b).join(',');
function rowsFor(mesh, primitive = 0, offset = 0) {
  const g = mesh.geometry, native = g.getAttribute('_native_id'); assert(native && g.index);
  return Array.from({ length: g.index.count / 3 }, (_, row) => {
    const ids = [0, 1, 2].map(k => g.index.getX(row * 3 + k));
    return { row: row + offset, primitive, primitiveTriangleRow: row, ids, nativeIDs: ids.map(id => native.getX(id)) };
  });
}
const jeansRows = rowsFor(jeans), bodyRows = [];
let bodyOffset = 0;
for (const [i, mesh] of bodyMeshes.entries()) { const rows = rowsFor(mesh, i, bodyOffset); bodyRows.push(rows); bodyOffset += rows.length; }
const byTriangle = new Map(jeansRows.map(row => [key(row.nativeIDs), row]));
const nativeRows = new Map();
for (let i = 0; i < jeans.geometry.attributes.position.count; i++) {
  const id = jeans.geometry.attributes._native_id.getX(i), list = nativeRows.get(id) ?? [];
  list.push(i); nativeRows.set(id, list);
}
const selected = {};
for (const side of ['left', 'right']) {
  selected[side] = {};
  assert.deepEqual([...definitions[side].corePolygonIds].sort((a, b) => a - b), patches.patches[side].core.originalPolygonIds);
  for (const kind of ['core', 'context']) {
    const source = patches.patches[side][kind];
    selected[side][kind] = source.triangles.map(t => {
      const row = byTriangle.get(key(t.nativeVertexIDs)); assert(row, 'Frozen triangle missing');
      assert([0, 1, 2].some(offset => row.nativeIDs.every((id, k) => id === t.nativeVertexIDs[(k + offset) % 3])), 'Winding changed');
      return { ...row, sourcePolygon: t.originalPolygonID };
    });
    for (const v of source.nativeVertices) for (const row of nativeRows.get(v.id) ?? []) {
      const p = new THREE.Vector3().fromBufferAttribute(jeans.geometry.attributes.position, row).toArray();
      assert.deepEqual(p, [v.sourceXYZ[0], v.sourceXYZ[2], -v.sourceXYZ[1]], 'Frozen source position changed');
      const expected = new Map(v.namedFour.map(([name, weight]) => [sanitize(name), weight]));
      let sum = 0;
      for (let slot = 0; slot < 4; slot++) {
        const w = jeans.geometry.attributes.skinWeight.getComponent(row, slot);
        if (!w) continue;
        const name = jeans.skeleton.bones[jeans.geometry.attributes.skinIndex.getComponent(row, slot)].name;
        assert(Math.abs(w - (expected.get(name) ?? 0)) < 2e-5, 'Selected source FOUR changed'); sum += w;
      }
      assert(Math.abs(sum - 1) < 2e-5);
    }
  }
}
const subsetIds = [...new Set(Object.values(selected).flatMap(s => s.context.flatMap(t => t.ids)))];
function points(mesh, ids) {
  const vertices = new Map();
  // Actual Three.js attached-mode bind order, including mesh world and bike inverse.
  const toBike = bikeFrame.matrixWorld.clone().invert();
  for (const id of ids) vertices.set(id, mesh.getVertexPosition(id, new THREE.Vector3()).applyMatrix4(mesh.matrixWorld).applyMatrix4(toBike));
  return vertices;
}
const triangles = (rows, vertices) => rows.map(row => surface(row.ids.map(id => vertices.get(id)), row));
function pose(control, breathing = 0) {
  resetHumanoidPose(rider.binding); bikeFrame.updateMatrixWorld(true);
  rider.poseFromHips(frame, { ...neutral, torsoAngle: control[2] }, control.slice(0, 2), control[3] + breathing);
  bikeFrame.updateMatrixWorld(true); // Refresh attached bindMatrixInverse after bone pose.
  assert([...rider.binding.byId.values()].every(b => b.matrixWorld.elements.every(Number.isFinite)));
  const vertices = points(jeans, subsetIds);
  return Object.fromEntries(['left', 'right'].map(side => [side, Object.fromEntries(['core', 'context'].map(kind => [kind, triangles(selected[side][kind], vertices)]))]));
}
function contacts() {
  const limbRows = [...rider.limbs].map(([name, l]) => ({ name, sourceLengthsM: l.lengths,
    measuredLengthsM: [rider.position(l.upper).distanceTo(rider.position(l.lower)), rider.position(l.lower).distanceTo(rider.position(l.end))] }));
  return { gripErrM: [...rider.debug.gripErr], soleErrM: [...rider.debug.soleErr], gripAngleErrRadians: [...rider.debug.gripAngleErr],
    armDemand: [...rider.debug.armStretch], legDemand: [...rider.debug.legStretch], limbRows,
    maxLengthResidualM: Math.max(...limbRows.flatMap(l => l.measuredLengthsM.map((v, i) => Math.abs(v - l.sourceLengthsM[i])))) };
}
function metrics(pose, saddle) {
  const cores = Object.fromEntries(['left', 'right'].map(side => [side, support(pose[side].core, saddle, band)]));
  const centers = Object.values(cores).map(c => c.bandCentroidXZ);
  const centered = centers.every(Boolean) && centers[0][1] * centers[1][1] < 0 && Math.abs((centers[0][1] + centers[1][1]) / 2) <= band;
  return { cores, centered, contacts: contacts(), passesSupportProxy: centered && Object.values(cores).every(c =>
    c.downwardProjectionFraction >= input.minimumDownwardProjectionFraction
    && c.overlapFraction >= definitions.offlineSupportProxies.minimumCoreFootprintOverlapFraction
    && c.bandFraction >= definitions.offlineSupportProxies.minimumOverlapAreaInGapBandFraction
    && c.centroidInsideCoreAndSaddle && c.projectedFoldAreaM2 <= EPS && c.minimum.gapM >= -1e-9) };
}
function localSolve(initial, evaluate, bounds, scales) {
  // One deterministic damped Gauss-Newton trajectory; no population/grid/restarts.
  let x = initial.map((v, i) => Math.max(bounds[i][0], Math.min(bounds[i][1], v))), current = evaluate(x);
  let evaluations = 1, damping = 1e-2;
  const history = [], cost = r => r.reduce((s, v) => s + v * v, 0) / 2;
  const solve4 = (a, b) => {
    const rows = a.map((r, i) => [...r, b[i]]);
    for (let k = 0; k < 4; k++) {
      let pivot = k; for (let j = k + 1; j < 4; j++) if (Math.abs(rows[j][k]) > Math.abs(rows[pivot][k])) pivot = j;
      [rows[k], rows[pivot]] = [rows[pivot], rows[k]]; const d = rows[k][k]; assert(Math.abs(d) > 1e-18);
      for (let j = k; j <= 4; j++) rows[k][j] /= d;
      for (let i = 0; i < 4; i++) if (i !== k) { const q = rows[i][k]; for (let j = k; j <= 4; j++) rows[i][j] -= q * rows[k][j]; }
    }
    return rows.map(r => r[4]);
  };
  for (let iteration = 0; iteration < input.solver.maxIterations; iteration++) {
    if (evaluations + 10 > input.solver.maxEvaluations) break;
    const derivatives = [];
    for (let k = 0; k < 4; k++) {
      const step = scales[k] * 1e-4, trial = [...x];
      trial[k] = x[k] + step <= bounds[k][1] ? x[k] + step : x[k] - step;
      const r = evaluate(trial); evaluations++;
      derivatives.push(r.map((v, j) => (v - current[j]) * scales[k] / (trial[k] - x[k])));
    }
    const normal = derivatives.map((a, i) => derivatives.map((b, j) => a.reduce((s, v, k) => s + v * b[k], 0) + (i === j ? damping : 0)));
    const gradient = derivatives.map(a => -a.reduce((s, v, k) => s + v * current[k], 0));
    let step = solve4(normal, gradient), norm = Math.hypot(...step);
    if (norm > input.solver.maxNormalizedStep) step = step.map(v => v * input.solver.maxNormalizedStep / norm);
    let accepted = false, prior = cost(current);
    for (let line = 0; line < 6; line++) {
      const trial = x.map((v, k) => Math.max(bounds[k][0], Math.min(bounds[k][1], v + scales[k] * step[k] * 2 ** -line)));
      const r = evaluate(trial); evaluations++;
      if (cost(r) < prior) { x = trial; current = r; accepted = true; break; }
    }
    history.push({ iteration, controls: x, cost: cost(current), accepted, damping, evaluations });
    damping = accepted ? Math.max(1e-6, damping / 2) : damping * 10;
    if ((accepted && prior - cost(current) < 1e-7) || damping > 1e10) break;
  }
  return { controls: x, cost: cost(current), evaluations, history };
}
function fullDiagnostic(pose, saddleAll) {
  const jv = points(jeans, Array.from({ length: jeans.geometry.attributes.position.count }, (_, i) => i));
  const jt = triangles(jeansRows, jv), bt = bodyMeshes.flatMap((mesh, i) => triangles(bodyRows[i],
    points(mesh, [...new Set(bodyRows[i].flatMap(t => t.ids))]))), neighborhood = new THREE.Box3();
  for (const t of [...saddleAll, ...pose.left.context, ...pose.right.context]) neighborhood.union(t.box);
  const localJ = jt.filter(t => t.box.intersectsBox(neighborhood)), localB = bt.filter(t => t.box.intersectsBox(neighborhood));
  const degenerates = (name, ts) => ts.filter(t => t.area <= 5e-15).map(t => ({ mesh: name, row: t.row, nativeIDs: t.nativeIDs }));
  return { neighborhoodBike: { min: neighborhood.min.toArray(), max: neighborhood.max.toArray() },
    scope: 'All jeans/body versus all saddle triangles; jeans/body and jeans self only in actual saddle-plus-context bounds. No global or closed-volume proof.',
    jeansTriangles: jt.length, bodyTriangles: bt.length, localJeansTriangles: localJ.length, localBodyTriangles: localB.length,
    degenerates: [...degenerates('jeans', localJ), ...degenerates('body', localB), ...degenerates('saddle', saddleAll)],
    jeansSaddle: crossings(jt, saddleAll), bodySaddle: crossings(bt, saddleAll),
    neighboringJeansBody: crossings(localJ, localB), neighboringJeansSelf: crossings(localJ, localJ, true) };
}

fs.mkdirSync(out, { recursive: true });
const result = { accepted: false, status: 'OFFLINE_AUTHORING_NOT_PLAYED', inputSHA256: sha(fs.readFileSync(configPath)),
  pins: input.pins, controlOrder: ['pelvisXMetres', 'pelvisYMetres', 'pelvisTiltRadians', 'spinalFlexRadians'],
  frozenSourcePolygonIds: Object.fromEntries(['left', 'right'].map(s => [s, definitions[s].corePolygonIds])),
  sourceGeometryAndFields: 'Pinned source opened read-only; no geometry/FOUR edits. Exact frozen core/context position, winding, and FOUR checked. Full mesh parity is not a new gate in this harness.',
  bikes: [], limits: input.limits };
for (const bike of measurement.bikes) {
  const raw = await load(bike.bike), shift = raw.node('attach_frame_origin').point;
  const actual = mesh(raw, bike.saddleSource.node, M().makeTranslation(-shift.x, -shift.y, -shift.z));
  const saddleAll = bike.saddleSource.sourceTriangleOrdinals.map(row => {
    const ids = [0, 1, 2].map(k => actual.indices.get(row * 3 + k));
    return surface(ids.map(id => actual.point(id)), { row, ids, nativeIDs: ids });
  });
  const saddle = saddleAll.filter(t => t.normal.y > 1e-9); assert.equal(saddle.length, 48);
  const saddleArea = saddle.reduce((s, t) => s + moment(t.points.map(xz)).area, 0);
  const saddleCenter = saddle.reduce((sum, t) => {
    const m = moment(t.points.map(xz)); return sum.add(new THREE.Vector3(m.centroid[0], 0, m.centroid[1]).multiplyScalar(m.area / saddleArea));
  }, new THREE.Vector3());
  const saddleBox = new THREE.Box3(); for (const t of saddle) saddleBox.union(t.box);
  const initialRow = bike.snapshots[0].existingContactDiagnostics.anthropometry;
  const initial = [...initialRow.hips, initialRow.carrierAngle, initialRow.spineFlexRadians];
  console.log(JSON.stringify({ bike: bike.name, phase: 'baseline', controls: initial }));
  const initialPose = pose(initial), baseline = metrics(initialPose, saddle);
  const savedWitness = bike.snapshots[0].regionalPosterior.witness;
  const witnessVertices = points(jeans, savedWitness.jeansDecodedVertexRows);
  const witnessPoint = savedWitness.jeansDecodedVertexRows.reduce((sum, id, k) =>
    sum.addScaledVector(witnessVertices.get(id), savedWitness.jeansBarycentric[k]), new THREE.Vector3());
  const playedReadbackResidualM = witnessPoint.distanceTo(new THREE.Vector3(...savedWitness.jeansPointBike));
  assert(playedReadbackResidualM < 1e-5, 'Existing played witness disagrees with actual-driver CPU skinning');
  const baselineDiagnostics = fullDiagnostic(initialPose, saddleAll);
  const initialPelvis = new THREE.Vector3(initial[0], initial[1], 0);
  const radius = Math.max(...Object.values(initialPose).flatMap(s => s.core.flatMap(t => t.points.map(p => p.distanceTo(initialPelvis)))));
  const legLength = Math.max(...[...rider.limbs].filter(([k]) => k.startsWith('leg')).map(([, l]) => l.lengths[0] + l.lengths[1]));
  const flex = metadata.driver.maxSpineFlexRadians;
  const bounds = [[saddleBox.min.x - radius, saddleBox.max.x + radius], [saddleBox.min.y, saddleBox.max.y + radius],
    [0, Math.PI / 2], [-flex + input.breathingRadians, flex - input.breathingRadians]];
  const evaluate = controls => {
    const posed = pose(controls), residuals = [];
    for (const side of ['left', 'right']) {
      const sourceArea = patches.patches[side].core.sourceAreaM2;
      for (const t of posed[side].core) {
        const original = patches.patches[side].core.triangles.find(s => s.originalPolygonID === t.sourcePolygon && key(s.nativeVertexIDs) === key(t.nativeIDs));
        assert(original);
        const sourcePoints = original.nativeVertexIDs.map(id => patches.patches[side].core.nativeVertices.find(v => v.id === id).sourceXYZ);
        const originalArea = new THREE.Triangle(...sourcePoints.map(p => new THREE.Vector3(...p))).getArea();
        const weight = Math.sqrt(originalArea / sourceArea / 3);
        // Degree-two triangle quadrature, all frozen core faces contribute; no minimum witness fit.
        for (let k = 0; k < 3; k++) {
          const p = t.points.reduce((sum, p, i) => sum.addScaledVector(p, i === k ? 2 / 3 : 1 / 6), new THREE.Vector3());
          const nearestSurface = nearest(p, saddle), wanted = nearestSurface.point.clone(); wanted.y += band / 2;
          residuals.push(...p.sub(wanted).toArray().map(v => weight * v / band));
        }
        residuals.push(Math.max(0, t.normal.y) * 10);
      }
      const context = support(posed[side].context, saddle, band);
      residuals.push(2 * Math.min(0, context.minimum?.gapM ?? 0) / band);
    }
    const coreCenter = Object.values(posed).reduce((sum, s) => {
      const area = s.core.reduce((n, t) => n + t.area, 0);
      return s.core.reduce((v, t) => v.addScaledVector(t.shape.getMidpoint(new THREE.Vector3()), t.area / area / 2), sum);
    }, new THREE.Vector3());
    residuals.push(coreCenter.z / band, .2 * (coreCenter.x - saddleCenter.x) / (saddleBox.max.x - saddleBox.min.x));
    residuals.push(...[...rider.debug.gripErr, ...rider.debug.soleErr].map(v => 10 * v / band));
    residuals.push(.01 * controls[3] / flex);
    assert(residuals.every(Number.isFinite)); return residuals;
  };
  const fit = localSolve(initial, evaluate, bounds, [legLength, legLength, 1, 1]);
  const finalPose = pose(fit.controls), final = metrics(finalPose, saddle), diagnostics = fullDiagnostic(finalPose, saddleAll);
  for (const name of ['jeansSaddle', 'bodySaddle', 'neighboringJeansBody', 'neighboringJeansSelf']) {
    const old = new Set(baselineDiagnostics[name].pairs.map(p => p.join(',')));
    diagnostics[name].newPairsSinceBaseline = diagnostics[name].pairs.filter(p => !old.has(p.join(',')));
  }
  const breaths = [-input.breathingRadians, 0, input.breathingRadians].map(breathing => ({ breathingRadians: breathing,
    ...metrics(pose(fit.controls, breathing), saddle) }));
  pose(fit.controls);
  const boneLocalTRS = [...rider.binding.byId].map(([id, bone]) => ({ id, translation: bone.position.toArray(),
    rotationXYZW: bone.quaternion.toArray(), scale: bone.scale.toArray() }));
  const firstSnapshot = JSON.stringify(boneLocalTRS);
  pose(fit.controls);
  assert.equal(JSON.stringify([...rider.binding.byId].map(([id, bone]) => ({ id, translation: bone.position.toArray(),
    rotationXYZW: bone.quaternion.toArray(), scale: bone.scale.toArray() }))), firstSnapshot, 'Repeated pose must be byte-identical');
  const contactPass = r => Math.max(...r.contacts.gripErrM, ...r.contacts.soleErrM) <= band && r.contacts.maxLengthResidualM < 1e-5;
  const numeric = breaths.every(r => r.passesSupportProxy && contactPass(r));
  const collision = !diagnostics.degenerates.length && ['jeansSaddle', 'bodySaddle', 'neighboringJeansBody', 'neighboringJeansSelf'].every(name => diagnostics[name].count === 0);
  const record = { name: bike.name, accepted: false, status: numeric && collision ? 'UNACCEPTED_NUMERICAL_CANDIDATE' : 'FAILED_AUTHORING_PROXY',
    bike: bike.bike, frameOriginFile: shift.toArray(), saddleSource: bike.saddleSource,
    frames: { palms: ['left', 'right'].map(side => ({ side, position: [RIDER_PROFILE.grip.x, RIDER_PROFILE.grip.y, rider.driver.sideZ[side] * RIDER_PROFILE.grip.z],
      rotationXYZW: rider.handTargets.get(side).toArray() })), soles: calibration.driver.selectedPegSurfaceBike,
      soleRotationXYZW: calibration.driver.soleQuaternionBike, soleInFoot: calibration.driver.selectedSoleInFoot },
    controls: fit.controls, headAngleRadians: neutral.headAngle, breathingRadians: input.breathingRadians,
    bounds, boundsRationale: 'XY from finite saddle bounds and measured posed core/carrier radius; carrier in upright-to-forward quadrant; flex inside existing 20-degree envelope with breathing margin.',
    fit, baseline, playedReadbackResidualM, final, baselineDiagnostics, diagnostics, breaths, numericalSupportAndContactPass: numeric,
    localCrossingDiagnosticsPass: collision, boneLocalTRS, deterministicPoseRepeat: true };
  result.bikes.push(record);
  fs.writeFileSync(path.join(out, `${bike.name}.json`), JSON.stringify(record, null, 2) + '\n');
  console.log(JSON.stringify({ bike: bike.name, status: record.status, controls: fit.controls, evaluations: fit.evaluations,
    cores: Object.fromEntries(Object.entries(final.cores).map(([s, c]) => [s, { overlapFraction: c.overlapFraction, bandFraction: c.bandFraction, minimumGapM: c.minimum?.gapM }])),
    gripErrM: final.contacts.gripErrM, soleErrM: final.contacts.soleErrM }));
}
fs.writeFileSync(path.join(out, 'authoring.json'), JSON.stringify(result, null, 2) + '\n');
if (result.bikes.some(b => b.status !== 'UNACCEPTED_NUMERICAL_CANDIDATE')) process.exitCode = 2;
