/** Read-only full-triangle residuals reconstructed from exact captured engine matrices. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { Vector3, Triangle, Box3, PropertyBinding } from 'three';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils.ts';

const base = path.resolve('harness/out/rider-contact-diagnostic-2026-10-03');
const report = JSON.parse(fs.readFileSync(path.join(base, 'aligned-step01/report.json')));
const source = path.join(base, 'source/Rockhop-supported-rider-contact-diagnostic.glb');
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
assert.equal(sha(source), '7adc07e7ee97278013af3f79d201e349fb0094f826aa7f25d02a550412e10cee');
const rider = await loadRigAt(pathToFileURL(source), true);
const bike = await loadRigAt(pathToFileURL(path.resolve('public/models/bike-rookie.glb')), true);
const roi = JSON.parse(fs.readFileSync('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11/source-roi.json'));
const rawFile = '/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/rider.glb';
assert.equal(sha(rawFile), roi.sourceSHA256);
const raw = await loadRigAt(pathToFileURL(rawFile), true);
const grips = JSON.parse(fs.readFileSync('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/bike-grip-surface02/report.json')).results[0].grips;
const seatIds = JSON.parse(fs.readFileSync('docs/evidence/hero-remaster/one-rider-v2/saddle-surface165/report.json')).seat_triangle_ids;
const named = new Map(), meshes = [];
rider.scene.traverse(o => { named.set(o.name, o); if (o.isSkinnedMesh) meshes.push(o); });
const baseGeometryProof = [];
raw.scene.traverse(o => {
  if (!o.isSkinnedMesh) return;
  const repaired = named.get(o.name); assert(repaired?.isSkinnedMesh);
  const hashes = {};
  for (const key of ['position', 'normal', 'skinIndex', 'skinWeight', 'index']) {
    const a = key === 'index' ? o.geometry.index : o.geometry.attributes[key];
    const b = key === 'index' ? repaired.geometry.index : repaired.geometry.attributes[key];
    const bytes = attribute => Buffer.from(attribute.array.buffer, attribute.array.byteOffset, attribute.array.byteLength);
    assert(bytes(a).equals(bytes(b)), `ROI source correspondence: ${o.name}/${key}`);
    hashes[key] = crypto.createHash('sha256').update(bytes(a)).digest('hex');
  }
  baseGeometryProof.push({ name: o.name, hashes });
});
assert.equal(baseGeometryProof.length, 5);
const clip = rider.animations.find(a => a.name === 'diagnostic_contact_observations_STEP'); assert(clip);
const sampler = clip.tracks.map(track => { const binding = new PropertyBinding(rider.scene, track.name); binding.bind(); return { binding, interpolant: track.createInterpolant() }; });
const runtimeBike = new Map(report.samples[0].fixture.bikeRuntimeNodes.map(n => [n.name, n]));
bike.scene.traverse(o => { const row = runtimeBike.get(o.name); if (row) { o.matrixWorld.fromArray(row.world); o.matrixAutoUpdate = false; } });
const body = named.get(roi.feet[0].meshName); assert(body?.isSkinnedMesh);
const faces = mesh => { const ix = mesh.geometry.index; assert(ix); return Array.from({ length: ix.count / 3 }, (_, i) => [ix.getX(i * 3), ix.getX(i * 3 + 1), ix.getX(i * 3 + 2)]); };
const bodyFaces = faces(body), positions = body.geometry.attributes.position, indices = body.geometry.attributes.skinIndex, weights = body.geometry.attributes.skinWeight;
const definitions = [];
const maskProvenance = [];
for (const side of ['L', 'R']) {
  const hand = roi.hands.find(h => h.side === side), target = grips.find(g => g.side === side);
  const sourceFaces = hand.actualExportedTriangleSourceVertices;
  const faceKey = f => f.slice().sort((a, b) => a - b).join(',');
  const nativeMapped = new Set(hand.triangles.map(f => faceKey(f.map(i => hand.sourceVertices[i]))));
  const exportedMapped = new Set(sourceFaces.map(faceKey));
  const actual = new Set(faces(named.get(hand.meshName)).map(faceKey));
  assert(sourceFaces.every(f => actual.has(faceKey(f))));
  maskProvenance.push({ side, authoritative: 'actualExportedTriangleSourceVertices', verifiedActualFaces: sourceFaces.length, nativeMappedFacesNotActualExport: [...nativeMapped].filter(f => !exportedMapped.has(f)).length });
  definitions.push({ name: 'grip.' + side, mesh: named.get(hand.meshName), sourceFaces, targetMesh: bike.scene.getObjectByName('handlebar'), targetFaces: target.sourceMeshSurface.triangles, coverage: 'All3312retained native hand triangles; full44literal grip target faces. Anatomical palmar-pad classification unreviewed.' });
  const footBone = body.skeleton.bones.findIndex(b => b.name === 'foot' + side); assert(footBone >= 0);
  const influenced = i => Array.from({ length: 4 }, (_, k) => indices.getComponent(i, k) === footBone ? weights.getComponent(i, k) : 0).some(w => w > 0);
  const footFaces = bodyFaces.filter(f => f.some(influenced));
  const selected = new Set(footFaces.map(f => f.join(',')));
  for (const f of roi.feet.find(f => f.side === side).triangles) assert(selected.has(f.map(i => roi.feet.find(f => f.side === side).sourceVertices[i]).join(',')), 'Full foot influence coverage must include every literal sole triangle');
  const targetMesh = bike.scene.getObjectByName('pegs'); assert(targetMesh?.isMesh);
  const p = targetMesh.geometry.attributes.position;
  definitions.push({ name: 'shoe.' + side, mesh: body, sourceFaces: footFaces, targetMesh, targetFaces: faces(targetMesh).filter(f => f.every(i => p.getZ(i) * (side === 'L' ? 1 : -1) > 0)), coverage: 'Every complete source triangle with any positive named foot-bone influence; includes all67/77literal sole faces plus shoe/ankle regions. Anatomical sole-only classification unreviewed.' });
}
const hipFaces = bodyFaces.filter(f => f.every(i => positions.getY(i) > .69 && positions.getY(i) < 1.08 && Math.abs(positions.getZ(i)) < .245));
const bodywork = bike.scene.getObjectByName('bodywork'); assert(bodywork?.isMesh);
const targetBodyFaces = faces(bodywork);
definitions.push({ name: 'hip-saddle', mesh: body, sourceFaces: hipFaces, targetMesh: bodywork, targetFaces: seatIds.map(i => targetBodyFaces[i]), coverage: 'All complete rest-Y0.69..1.08m/absZ<0.245m source body faces;48literal upward saddle faces. Includes upper thighs/cloth, excludes saddle sides/underside.' });
const nearest = new Vector3(), delta = new Vector3(), planePoint = new Vector3();
const segmentDistance2 = (p1, q1, p2, q2) => {
  const d1 = q1.clone().sub(p1), d2 = q2.clone().sub(p2), r = p1.clone().sub(p2);
  const a = d1.dot(d1), e = d2.dot(d2), f = d2.dot(r); let s, t;
  if (a <= 1e-20 && e <= 1e-20) return p1.distanceToSquared(p2);
  if (a <= 1e-20) { s = 0; t = Math.min(1, Math.max(0, f / e)); }
  else { const c = d1.dot(r); if (e <= 1e-20) { t = 0; s = Math.min(1, Math.max(0, -c / a)); }
    else { const b = d1.dot(d2), denominator = a * e - b * b; s = denominator !== 0 ? Math.min(1, Math.max(0, (b * f - c * e) / denominator)) : 0; t = (b * s + f) / e;
      if (t < 0) { t = 0; s = Math.min(1, Math.max(0, -c / a)); } else if (t > 1) { t = 1; s = Math.min(1, Math.max(0, (b - c) / a)); } }
  }
  return p1.clone().addScaledVector(d1, s).distanceToSquared(p2.clone().addScaledVector(d2, t));
};
const crosses = (a, b, tri) => {
  const normal = tri.getNormal(new Vector3()), da = delta.copy(a).sub(tri.a).dot(normal), db = delta.copy(b).sub(tri.a).dot(normal);
  if (da * db > 0 || Math.abs(da - db) < 1e-18) return false;
  const t = da / (da - db); if (t < 0 || t > 1) return false;
  planePoint.copy(a).lerp(b, t); return tri.containsPoint(planePoint);
};
const triangleDistance2 = (a, b) => {
  const aa = [a.a, a.b, a.c], bb = [b.a, b.b, b.c]; let best = Infinity;
  for (let i = 0; i < 3; i++) { if (crosses(aa[i], aa[(i + 1) % 3], b) || crosses(bb[i], bb[(i + 1) % 3], a)) return 0;
    b.closestPointToPoint(aa[i], nearest); best = Math.min(best, aa[i].distanceToSquared(nearest));
    a.closestPointToPoint(bb[i], nearest); best = Math.min(best, bb[i].distanceToSquared(nearest));
    for (let j = 0; j < 3; j++) best = Math.min(best, segmentDistance2(aa[i], aa[(i + 1) % 3], bb[j], bb[(j + 1) % 3])); }
  return best;
};
const control = new Triangle(new Vector3(0, 0, 0), new Vector3(1, 0, 0), new Vector3(0, 1, 0));
assert.equal(triangleDistance2(control, new Triangle(new Vector3(0, 0, 1), new Vector3(1, 0, 1), new Vector3(0, 1, 1))), 1, 'Known parallel separation is one metre');
assert.equal(triangleDistance2(control, new Triangle(new Vector3(.2, .2, -1), new Vector3(.2, .2, 1), new Vector3(.8, .2, 0))), 0, 'Transverse face crossing is zero separation');
const boxGap2 = (a, b) => ['x', 'y', 'z'].reduce((n, k) => n + Math.max(0, a.min[k] - b.max[k], b.min[k] - a.max[k]) ** 2, 0);
const makeTriangles = (mesh, rows, skinned) => {
  const cache = new Map(); const p = mesh.geometry.attributes.position;
  const vertex = i => { if (!cache.has(i)) cache.set(i, (skinned ? mesh.getVertexPosition(i, new Vector3()) : new Vector3().fromBufferAttribute(p, i)).applyMatrix4(mesh.matrixWorld)); return cache.get(i); };
  return rows.map((ids, i) => { const points = ids.map(vertex); return { i, ids, tri: new Triangle(...points), box: new Box3().setFromPoints(points) }; });
};
const rows = []; let worldMatrixMaxError = 0;
for (const sample of report.samples) {
  for (const track of sampler) track.binding.setValue(track.interpolant.evaluate(sample.time), 0);
  rider.scene.matrix.fromArray(sample.sceneMatrix); rider.scene.matrixAutoUpdate = false;
  for (const [name, row] of Object.entries(sample.bones)) { const o = named.get(name); assert(o?.isBone); o.matrix.fromArray(row.local); o.matrixAutoUpdate = false; }
  for (const m of meshes) { const row = sample.meshes.find(r => r.name === m.name); assert(row); if (m.morphTargetInfluences) m.morphTargetInfluences.splice(0, m.morphTargetInfluences.length, ...row.morphWeights); }
  rider.scene.updateMatrixWorld(true); meshes.forEach(m => m.skeleton.update());
  for (const [name, row] of Object.entries(sample.bones)) named.get(name).matrixWorld.elements.forEach((v, i) => { worldMatrixMaxError = Math.max(worldMatrixMaxError, Math.abs(v - row.world[i])); });
  for (const m of meshes) { const row = sample.meshes.find(r => r.name === m.name); m.matrixWorld.elements.forEach((v, i) => { worldMatrixMaxError = Math.max(worldMatrixMaxError, Math.abs(v - row.matrix[i])); }); }
  assert(worldMatrixMaxError < 1e-10, 'Exact captured bone and mesh matrices must match before measuring surfaces');
  for (const d of definitions) {
    const a = makeTriangles(d.mesh, d.sourceFaces, true), b = makeTriangles(d.targetMesh, d.targetFaces, false);
    let best = Infinity, witness = null, pairs = 0, zeroPairs = 0; const zeroSource = new Set(), zeroTarget = new Set();
    for (const x of a) for (const y of b) {
      if (boxGap2(x.box, y.box) > best) continue; pairs++;
      const distance = triangleDistance2(x.tri, y.tri);
      if (distance === 0) { zeroPairs++; zeroSource.add(x.i); zeroTarget.add(y.i); }
      if (distance < best) { best = distance; witness = { sourceVertices: x.ids, targetVertices: y.ids, sourceTriangleWorld: [x.tri.a.toArray(), x.tri.b.toArray(), x.tri.c.toArray()], targetTriangleWorld: [y.tri.a.toArray(), y.tri.b.toArray(), y.tri.c.toArray()] }; }
    }
    assert(Number.isFinite(best)); rows.push({ sourceTime: sample.time, contact: d.name, sourceFaces: a.length, targetFaces: b.length, coverage: d.coverage, minimumTriangleSurfaceGapM: Math.sqrt(best), evaluatedPairs: pairs, zeroDistancePairs: zeroPairs, zeroDistanceSourceFaces: zeroSource.size, zeroDistanceTargetFaces: zeroTarget.size, witness });
  }
  console.log(JSON.stringify({ time: sample.time, contacts: rows.slice(-5).map(r => [r.contact, r.minimumTriangleSurfaceGapM]) }));
}
assert(worldMatrixMaxError < 1e-10);
fs.writeFileSync(path.join(base, 'full-surface-residuals.json'), JSON.stringify({ status: 'MEASURED_UNACCEPTED', sourceSHA256: sha(source), sourceLibraryFileID: 'libfile_c7329e8d1f5081919a603ffb962cfc31', sourceLibraryVersion: 3, roiSourceSHA256: sha(rawFile), baseGeometryProof, maskProvenance, bikeSHA256: sha('public/models/bike-rookie.glb'), capturedReportSHA256: sha(path.join(base, 'aligned-step01/report.json')), worldMatrixMaxError,
  actualClip: clip.name, sourceTimes: report.samples.map(s => s.time), wrapperMode: report.wrapperMode, captureRepositorySHA: report.repoSHA, actualBuild: JSON.parse(fs.readFileSync(path.join(report.build, 'version.json'))), browser: report.browser, device: report.device, launchURL: report.launchURL,
  method: 'ProductionGLTFDecoder/ThreeCPUskin reconstruction from exact captured engine local/world matrices and morphs; exact finite triangle edge/face/edge-edge unsigned distance withAABB lower-bound pruning.',
  rows, limits: ['Unsigned minimum separation only; zero can mean contact or crossing, not accepted grip/support.', 'Open anatomical/contact classification; native hand/foot-influence supersets do not certify palm/sole pad normals, force, friction or anatomical quality.', 'Saddle includes48upwardfaces only; sides/underside excluded. Broad hip patch includes upper thighs and folds; minimum cannot establish posterior support or refute the cloud6–9mm posterior-hover observation. No closed-volume penetration certificate.', '17STEPobservations only; no interpolation/CCD or physics-driven pose acceptance.', 'No shader readback, textures/normals, performance, physical device or stranger pass.'] }, null, 2) + '\n');
