/** Parent-run bounded posed-surface authoring. Produces only ignored candidates. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../../../src/render/hero/gltfTestUtils.ts';
import { load, mesh, M, pinned, sha } from '../selected-ankle-contact02/surface.mjs';
import { EPS, surface, support, crossings } from '../selected-seated-author04/geometry.mjs';
import { V, rotation, triangleFrame, index, closest, inside, reconstruct, relativeFlex, activation, anatomicalCageMember } from './deform.mjs';
import { exportMorph } from './export-morph.mjs';

const HERE = path.dirname(new URL(import.meta.url).pathname), input = JSON.parse(fs.readFileSync(path.join(HERE, 'input.json')));
const out = process.argv.find(v => v.startsWith('--out='))?.slice(6);
assert(out && !fs.existsSync(out), 'Use a fresh --out=DIRECTORY');
assert(path.resolve(out).startsWith(path.resolve('harness/out/rider-rebuild/selected-seated-corrective06') + path.sep));
let phase = 'pinned source readback', failureWitness = null;
try {
for (const row of Object.values(input.pins)) pinned(row);
const read = name => JSON.parse(pinned(input.pins[name]));
const metadata = read('contract'), receipt = read('receipt'), patches = read('patches'), definitions = read('definitions');
Object.assign(metadata.driver, { nearSimilarityTolerance: 1e-4 }, read('calibration').driver);
const gltf = await loadRigAt(pathToFileURL(path.resolve(input.pins.rider.path)), true), placement = new THREE.Group();
placement.quaternion.fromArray(metadata.driver.assetToBikeQuaternionXYZW); placement.add(gltf.scene); placement.updateMatrixWorld(true);
const deadline = Date.now() + input.maximumMilliseconds, Q = () => new THREE.Quaternion();
const bone = id => gltf.scene.getObjectByName(THREE.PropertyBinding.sanitizeNodeName(metadata.specification.jointNames[id]));
const role = name => { const id = metadata.specification.roles[name]; return bone(Array.isArray(id) ? id[0] : id); };
const restTRS = new Map(receipt.boneLocalTRS.map(row => { const b = bone(row.id); return [row.id, { p: b.position.clone(), q: b.quaternion.clone(), s: b.scale.clone() }]; }));
const restRelative = ['Left', 'Right'].map(side => role('pelvis').getWorldQuaternion(Q()).invert().multiply(role('thigh' + side).getWorldQuaternion(Q())));
const hipY = ['Left', 'Right'].reduce((s, side) => s + role('thigh' + side).getWorldPosition(new THREE.Vector3()).y / 2, 0);
const kneeY = ['Left', 'Right'].reduce((s, side) => s + role('shin' + side).getWorldPosition(new THREE.Vector3()).y / 2, 0);
function gather(name) {
  const node = gltf.scene.getObjectByName(name), meshes = node.getObjectsByProperty('isSkinnedMesh', true), vertices = [], byNative = new Map(), faces = [], rawRows = [];
  assert(meshes.length, `Missing selected ${name}`);
  for (const mesh of meshes) {
    const g = mesh.geometry, ids = g.getAttribute('_native_id'), rows = [];
    const restWorld = mesh.matrixWorld.clone();
    for (let row = 0; row < ids.count; row++) {
      const nativeID = ids.getX(row), local = new THREE.Vector3().fromBufferAttribute(g.attributes.position, row), rest = local.clone().applyMatrix4(restWorld);
      let id = byNative.get(nativeID);
      if (id === undefined) { id = vertices.length; byNative.set(nativeID, id); vertices.push({ nativeID, local, rest, restWorld, mesh, row }); }
      else assert(rest.distanceTo(vertices[id].rest) < 1e-9 && local.distanceTo(vertices[id].local) < 1e-9, 'Native seam copies disagree');
      rows.push(id);
    }
    for (let row = 0; row < g.index.count / 3; row++) faces.push([0, 1, 2].map(k => rows[g.index.getX(row * 3 + k)]));
    rawRows.push({ mesh, rows });
  }
  return { name, vertices, faces, byNative, rawRows };
}
const jeans = gather('RiderJeans'), body = gather('RiderBody');
const roleIds = name => { const ids = metadata.specification.roles[name]; return Array.isArray(ids) ? ids : [ids]; };
const bodyCageBones = new Set([...['pelvis', 'thighLeft', 'thighRight'].flatMap(roleIds), ...input.additionalPelvisJointIDs].map(id => {
  const joint = bone(id); assert(joint?.isBone, `Missing declared pelvic/thigh joint ${id}`); return joint.name;
}));
const protectedArmBones = new Set();
for (const side of ['Left', 'Right']) role('shoulder' + side).traverse(joint => { if (joint.isBone) protectedArmBones.add(joint.name); });
for (const v of body.vertices) {
  v.namedFour = [0, 1, 2, 3].map(slot => ({
    joint: v.mesh.skeleton.bones[v.mesh.geometry.attributes.skinIndex.getComponent(v.row, slot)].name,
    weight: v.mesh.geometry.attributes.skinWeight.getComponent(v.row, slot) })).filter(row => row.weight > 0);
  v.bodyCageMember = anatomicalCageMember(v.namedFour, bodyCageBones, protectedArmBones);
  v.protectedArm = v.namedFour.some(row => protectedArmBones.has(row.joint));
}
function applyPose(t) {
  for (const row of receipt.boneLocalTRS) {
    const b = bone(row.id), rest = restTRS.get(row.id);
    b.position.copy(rest.p).lerp(V(row.translation), t); b.quaternion.copy(rest.q).slerp(Q().fromArray(row.rotationXYZW), t); b.scale.copy(rest.s).lerp(V(row.scale), t);
  }
  placement.updateMatrixWorld(true);
}
function localToBike(v) {
  const { mesh, row } = v, sum = new THREE.Matrix4(); sum.elements.fill(0);
  for (let k = 0; k < 4; k++) {
    const weight = mesh.geometry.attributes.skinWeight.getComponent(row, k); if (!weight) continue;
    const id = mesh.geometry.attributes.skinIndex.getComponent(row, k), m = mesh.skeleton.bones[id].matrixWorld.clone().multiply(mesh.skeleton.boneInverses[id]);
    for (let j = 0; j < 16; j++) sum.elements[j] += weight * m.elements[j];
  }
  // Three's Vector3 CPU skin path keeps an implicit homogeneous coordinate of 1.
  sum.elements[3] = sum.elements[7] = sum.elements[11] = 0; sum.elements[15] = 1;
  return mesh.matrixWorld.clone().multiply(mesh.bindMatrixInverse).multiply(sum).multiply(mesh.bindMatrix);
}
const surfaces = (part, positions) => part.faces.map((ids, row) => surface(ids.map(i => positions[i]), { row, ids, nativeIDs: ids.map(i => part.vertices[i].nativeID) }));
applyPose(1);
for (const part of [jeans, body]) for (const v of part.vertices) {
  v.skin = localToBike(v); v.posed = v.local.clone().applyMatrix4(v.skin);
  assert(v.posed.distanceTo(v.mesh.getVertexPosition(v.row, new THREE.Vector3()).applyMatrix4(v.mesh.matrixWorld)) < 1e-9, 'Affine readback differs from actual skin');
}
for (const part of [jeans, body]) for (const { mesh, rows } of part.rawRows) for (let row = 0; row < rows.length; row++) {
  const v = part.vertices[rows[row]], affine = localToBike({ mesh, row });
  assert(affine.elements.every((x, i) => Math.abs(x - v.skin.elements[i]) < 1e-9), 'Native seam copies have different skin maps');
}
const key = ['Left', 'Right'].map((side, i) => relativeFlex(role('pelvis').getWorldQuaternion(Q()), role('thigh' + side).getWorldQuaternion(Q()), restRelative[i]));
const activationRadius = Math.hypot(...key.map(q => q.angleTo(Q()))); assert(activationRadius > .1);
const rawBike = await load(receipt.bike), origin = rawBike.node('attach_frame_origin').point;
phase = 'closed oriented actual saddle cavity';
const actual = mesh(rawBike, receipt.saddleSource.node, M().makeTranslation(-origin.x, -origin.y, -origin.z));
const saddle = receipt.saddleSource.sourceTriangleOrdinals.map(row => surface([0, 1, 2].map(k => actual.point(actual.indices.get(row * 3 + k))), { row }));
const top = saddle.filter(t => t.normal.y > 1e-9), saddleIndex = index(saddle), topIndex = index(top);
// Closed saddle volume is required for obstacle constraints; geometric duplicates
// at GLB seams are welded by coordinate only for this manifold check.
const shellEdges = new Map(), pointKey = p => p.toArray().map(v => v.toPrecision(14)).join(',');
for (const t of saddle) for (let k = 0; k < 3; k++) {
  const pair = [pointKey(t.points[k]), pointKey(t.points[(k + 1) % 3])], id = [...pair].sort().join('|');
  const row = shellEdges.get(id) ?? { count: 0, winding: 0 }; row.count++; row.winding += pair[0] < pair[1] ? 1 : -1; shellEdges.set(id, row);
}
const badShellEdges = [...shellEdges].filter(([, e]) => e.count !== 2 || e.winding !== 0);
if (badShellEdges.length) failureWitness = { badShellEdges: badShellEdges.slice(0, 32), count: badShellEdges.length };
assert(!badShellEdges.length, 'No closed oriented finite saddle cavity');
const lowerY = (hipY + kneeY) / 2, upperY = Math.max(...jeans.vertices.map(v => v.rest.y));
const active = jeans.vertices.map(v => v.rest.y > lowerY + input.boundaryWidthM && v.rest.y < upperY - input.boundaryWidthM);
const rotations = jeans.vertices.map(v => rotation(new THREE.Matrix3().setFromMatrix4(v.skin.clone().multiply(v.restWorld.clone().invert()))));
const edges = new Map();
for (const f of jeans.faces) for (let k = 0; k < 3; k++) {
  const pair = [f[k], f[(k + 1) % 3]].sort((a, b) => a - b), length = jeans.vertices[pair[0]].rest.distanceTo(jeans.vertices[pair[1]].rest);
  assert(length > 1e-9, 'Degenerate source edge'); edges.set(pair.join(','), [...pair, 1 / length]);
}
const fixed = new Map(jeans.vertices.flatMap((v, i) => active[i] ? [] : [[i, v.posed.clone()]])), coreHandles = new Map();
phase = 'source-shape-preserving finite contact cage';
for (const side of ['left', 'right']) {
  const frozen = patches.patches[side].core, ids = frozen.nativeVertices.map(v => jeans.byNative.get(v.id));
  assert(ids.every(id => id !== undefined && active[id]), 'Frozen anatomical core outside constructive neighborhood');
  const sourceCenter = ids.reduce((v, id) => v.add(jeans.vertices[id].rest), new THREE.Vector3()).divideScalar(ids.length);
  const posedCenter = ids.reduce((v, id) => v.add(jeans.vertices[id].posed), new THREE.Vector3()).divideScalar(ids.length);
  const normal = new THREE.Vector3();
  for (const t of frozen.triangles) {
    const p = t.nativeVertexIDs.map(id => jeans.vertices[jeans.byNative.get(id)].rest);
    normal.add(new THREE.Vector3().crossVectors(p[1].clone().sub(p[0]), p[2].clone().sub(p[0])));
  }
  normal.normalize();
  const mean = new THREE.Matrix3(); mean.elements.fill(0);
  for (const id of ids) for (let k = 0; k < 9; k++) mean.elements[k] += rotations[id].elements[k] / ids.length;
  const r = rotation(mean), contact = closest(posedCenter, topIndex), align = Q().setFromUnitVectors(normal.clone().applyMatrix3(r), contact.triangle.normal.clone().negate());
  const targets = new Map(ids.map(id => [id, jeans.vertices[id].rest.clone().sub(sourceCenter).applyMatrix3(r).applyQuaternion(align).add(contact.point)]));
  const coreSurface = () => frozen.triangles.map((t, row) => surface(t.nativeVertexIDs.map(id => targets.get(jeans.byNative.get(id))), { row, nativeIDs: t.nativeVertexIDs }));
  const initial = support(coreSurface(), top, definitions.offlineSupportProxies.gapBandM);
  failureWitness = { side, stage: 'initial rigid core cage', support: initial, targets: [...targets].map(([id, p]) => ({ nativeID: jeans.vertices[id].nativeID, pointBike: p.toArray() })) };
  assert(initial.minimum && initial.overlapFraction >= .5, 'Rigid anatomical contact cage misses finite saddle');
  const settle = input.clearanceM - initial.minimum.gapM;
  for (const [id, p] of targets) { p.y += settle; fixed.set(id, p); coreHandles.set(id, p); }
  const cage = support(coreSurface(), top, definitions.offlineSupportProxies.gapBandM);
  failureWitness = { side, stage: 'settled rigid core cage', support: cage, targets: [...targets].map(([id, p]) => ({ nativeID: jeans.vertices[id].nativeID, pointBike: p.toArray() })) };
  assert(cage.bandFraction >= definitions.offlineSupportProxies.minimumOverlapAreaInGapBandFraction && cage.centroidInsideCoreAndSaddle,
    'No source-shape-preserving finite contact cage; artist target required');
}
failureWitness = null;
let corrected = jeans.vertices.map(v => v.posed.clone()); const history = [];
phase = 'bounded whole-neighborhood differential reconstruction';
for (let pass = 0; pass < input.maximumObstaclePasses; pass++) {
  const fit = reconstruct(jeans.vertices.map((v, i) => ({ ...v, posed: corrected[i] })), [...edges.values()], fixed, rotations, deadline);
  corrected = fit.positions; let added = 0;
  for (let id = 0; id < corrected.length; id++) if (active[id] && !coreHandles.has(id)) {
    const p = corrected[id], source = jeans.vertices[id].rest;
    if (saddleIndex.box.containsPoint(p) && inside(p, saddle)) {
      const hit = closest(p, saddleIndex); fixed.set(id, hit.point.clone().addScaledVector(hit.triangle.normal, input.clearanceM)); added++;
    } else if (source.z * p.z < -1e-12) {
      const target = p.clone(); target.z = Math.sign(source.z) * Math.min(Math.abs(source.z), input.clearanceM); fixed.set(id, target); added++;
    }
  }
  history.push({ pass, addedObstacleHandles: added, ...fit, positions: undefined });
  if (!added) break;
  assert(pass + 1 < input.maximumObstaclePasses, 'No feasible saddle/center-plane neighborhood in bounded construction');
}
const restJeans = surfaces(jeans, jeans.vertices.map(v => v.rest)), restIndex = index(restJeans), original = jeans.vertices.map(v => v.posed);
let movedBody = 0, minimumSourceCavityM = Infinity;
phase = 'actual source body/garment cage';
const correctedBody = body.vertices.map(v => {
  if (!v.bodyCageMember) return v.posed.clone();
  if (v.rest.y <= lowerY || v.rest.y >= upperY) return v.posed.clone();
  const hit = closest(v.rest, restIndex), ids = hit.triangle.ids;
  if (ids.every(id => corrected[id].distanceTo(original[id]) < 1e-9)) return v.posed.clone();
  failureWitness = { bodyNativeID: v.nativeID, namedFour: v.namedFour, bodyRestPoint: v.rest.toArray(), cageNativeIDs: hit.triangle.nativeIDs,
    cageRestPoints: hit.triangle.points.map(p => p.toArray()), cageDistanceM: Math.sqrt(hit.distanceSq) };
  assert(hit.distanceSq <= input.maximumCageDistanceM ** 2, `Body outside source garment cage: native=${v.nativeID}, distanceM=${Math.sqrt(hit.distanceSq)}, jeansNative=${hit.triangle.nativeIDs}`);
  const offset = v.rest.clone().sub(hit.point), cavity = -offset.dot(hit.triangle.normal);
  failureWitness.signedInsideM = cavity;
  assert(cavity >= -1e-5, `Source body outside garment cavity: native=${v.nativeID}, signedInsideM=${cavity}, jeansNative=${hit.triangle.nativeIDs}; no corrective may hide it`);
  minimumSourceCavityM = Math.min(minimumSourceCavityM, cavity);
  const bary = hit.triangle.shape.getBarycoord(hit.point, new THREE.Vector3()).toArray();
  const oldFrame = triangleFrame(ids.map(id => original[id])).multiply(triangleFrame(hit.triangle.points).transpose());
  const newFrame = triangleFrame(ids.map(id => corrected[id])).multiply(triangleFrame(hit.triangle.points).transpose());
  const delta = ids.reduce((d, id, i) => d.addScaledVector(corrected[id].clone().sub(original[id]), bary[i]), new THREE.Vector3());
  delta.add(offset.clone().applyMatrix3(newFrame)).sub(offset.clone().applyMatrix3(oldFrame)); movedBody++;
  return v.posed.clone().add(delta);
});
failureWitness = null;
for (const [part, targets] of [[jeans, corrected], [body, correctedBody]]) for (let i = 0; i < part.vertices.length; i++) {
  const v = part.vertices[i], linear = new THREE.Matrix3().setFromMatrix4(v.skin); assert(Math.abs(linear.determinant()) > 1e-6, 'Singular exact-skin inverse');
  v.delta = targets[i].clone().sub(v.posed).applyMatrix3(linear.invert());
  assert(v.local.clone().add(v.delta).applyMatrix4(v.skin).distanceTo(targets[i]) < 1e-9, 'Exact morph inverse failed');
}
assert(body.vertices.filter(v => v.protectedArm).every(v => v.delta.lengthSq() === 0), 'Arms/hands must have exactly zero corrective displacement');
const coreMetrics = positions => Object.fromEntries(['left', 'right'].map(side => [side, support(patches.patches[side].core.triangles.map((t, row) =>
  surface(t.nativeVertexIDs.map(id => positions[jeans.byNative.get(id)]), { row, nativeIDs: t.nativeVertexIDs })), top, definitions.offlineSupportProxies.gapBandM)]));
const checks = [];
phase = 'fixed geometry/contact/transition gates';
for (const t of [0, .25, .5, .75, 1]) {
  assert(Date.now() < deadline, 'Bounded corrective deadline reached'); applyPose(t);
  const flex = ['Left', 'Right'].map((side, i) => relativeFlex(role('pelvis').getWorldQuaternion(Q()), role('thigh' + side).getWorldQuaternion(Q()), restRelative[i]));
  const weight = activation(flex, key, activationRadius);
  if (!t) assert(weight < 1e-12, 'Rest shape must remain exact'); if (t === 1) assert(Math.abs(weight - 1) < 1e-10);
  const positions = part => part.vertices.map(v => v.local.clone().addScaledVector(v.delta, weight).applyMatrix4(localToBike(v)));
  const jp = positions(jeans), bp = positions(body), jt = surfaces(jeans, jp), bt = surfaces(body, bp);
  const neighborhood = new THREE.Box3(); for (let id = 0; id < jp.length; id++) if (active[id]) neighborhood.expandByPoint(jp[id]);
  const localJ = jt.filter(f => f.box.intersectsBox(neighborhood)), localB = bt.filter(f => f.box.intersectsBox(neighborhood));
  const self = crossings(localJ, localJ, true), layer = crossings(localJ, localB), contact = t === 1 ? coreMetrics(jp) : null;
  const baseJ = surfaces(jeans, jeans.vertices.map(v => v.local.clone().applyMatrix4(localToBike(v)))).filter(f => f.box.intersectsBox(neighborhood));
  const baseB = surfaces(body, body.vertices.map(v => v.local.clone().applyMatrix4(localToBike(v)))).filter(f => f.box.intersectsBox(neighborhood));
  const baseline = { self: crossings(baseJ, baseJ, true), layer: crossings(baseJ, baseB) };
  for (const [name, check] of [['self', self], ['layer', layer]]) {
    const old = new Set(baseline[name].pairs.map(p => p.join(','))); check.newPairs = check.pairs.filter(p => !old.has(p.join(',')));
  }
  const jeansSaddle = t === 1 ? crossings(jt, saddle) : null, bodySaddle = t === 1 ? crossings(bt, saddle) : null;
  const centers = contact ? Object.values(contact).map(c => c.bandCentroidXZ) : [];
  const supportPass = !contact || centers.every(Boolean) && centers[0][1] * centers[1][1] < 0 && Math.abs((centers[0][1] + centers[1][1]) / 2) <= .001 && Object.values(contact).every(c =>
    c.downwardProjectionFraction >= .5 && c.overlapFraction >= .5 && c.bandFraction >= .5 && c.minimum.gapM >= -1e-9 && c.centroidInsideCoreAndSaddle && c.projectedFoldAreaM2 <= EPS);
  const degenerate = [...localJ, ...localB].filter(f => f.area <= 5e-15).length;
  checks.push({ t, weight, baseline, self, layer, jeansSaddle, bodySaddle, contact, degenerate,
    pass: !self.count && !layer.count && !degenerate && supportPass && !(jeansSaddle?.count) && !(bodySaddle?.count) });
}
const result = { accepted: false, status: checks.every(c => c.pass) ? 'UNACCEPTED_CORRECTIVE_CANDIDATE' : 'FAILED_CORRECTIVE_GATES',
  inputSHA256: sha(fs.readFileSync(path.join(HERE, 'input.json'))), pins: input.pins, sourceRestUnchanged: true,
  activation: { method: 'Compact C2 Wendland radial basis in actual bilateral thigh-relative-to-pelvis quaternion distance',
    keyXYZW: key.map(q => q.toArray()), restRelativeXYZW: restRelative.map(q => q.toArray()), radiusRadians: activationRadius },
  neighborhood: { lowerY, upperY, fixedBoundaryWidthM: input.boundaryWidthM, activeJeansVertices: active.filter(Boolean).length,
    anatomicalBodyMembers: body.vertices.filter(v => v.bodyCageMember).length, protectedArmHandVertices: body.vertices.filter(v => v.protectedArm).length,
    armHandDeltasExactlyZero: true, bodyCageJointNames: [...bodyCageBones], movedBodyVertices: movedBody, minimumSourceCavityM },
  construction: 'Source differential edge detail transported by polar skin rotations; rigid source core cages oriented and settled on actual finite saddle; body follows the actual source garment cage; exact inverse skin creates relative morphs.',
  history, checks, limits: input.limits };
fs.mkdirSync(out, { recursive: true }); fs.writeFileSync(path.join(out, 'corrective.json'), JSON.stringify(result, null, 2) + '\n');
if (!checks.every(c => c.pass)) process.exitCode = 2;
{
  phase = 'unaccepted diagnostic morph export';
  const deltas = Object.fromEntries([jeans, body].map(part => [part.name, part.vertices.filter(v => v.delta.length() > 1e-12).map(v =>
    ({ nativeID: v.nativeID, deltaGLTF: v.delta.toArray(), deltaBlender: [v.delta.x, -v.delta.z, v.delta.y] }))]));
  fs.writeFileSync(path.join(out, 'shape-key.json'), JSON.stringify({ accepted: false, status: result.status, sourceSHA256: input.pins.rider.sha256,
    name: 'SelectedSeatedCorrective06', relative: true, deltas, activation: result.activation }, null, 2) + '\n');
  const exported = await exportMorph(input.pins.rider, deltas, path.join(out, 'rider.glb'));
  fs.writeFileSync(path.join(out, 'rider-contract.json'), JSON.stringify({ ...metadata, accepted: false, glbSHA256: exported.sha256,
    correctiveBaseSHA256: input.pins.rider.sha256, qualificationState: result.status, corrective: result.activation }, null, 2) + '\n');
  fs.writeFileSync(path.join(out, 'export.json'), JSON.stringify({ ...exported, accepted: false, status: result.status }, null, 2) + '\n');
  console.log(JSON.stringify({ status: result.status, glb: path.join(out, 'rider.glb'), exported, checks: checks.map(c => ({ t: c.t, pass: c.pass })) }));
}
} catch (error) {
  fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, 'failure.json'), JSON.stringify({ accepted: false, status: 'FAILED_CONSTRUCTION', phase,
    inputSHA256: sha(fs.readFileSync(path.join(HERE, 'input.json'))), error: String(error), witness: failureWitness, stack: error.stack }, null, 2) + '\n');
  throw error;
}
