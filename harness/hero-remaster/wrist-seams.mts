/** Bind-aware sewn wrist audit. CPU rig checks complement, never replace, played engine clips.
 * pnpm exec tsx harness/hero-remaster/wrist-seams.mts [--full=FILE] [--full-map=FILE]
 *   [--lod=FILE --lod-map=FILE] [--out=docs/evidence/hero-remaster/wrists/v6-seams.json]
 * An explicit builder contour is independently checked against actual triangle edge incidence.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { MeshoptEncoder } from 'meshoptimizer/encoder';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils';
import { prepareHero } from '../../src/render/hero/lod';
import { boneName, GltfRider } from '../../src/render/hero/gltfRider';
import type { HeroBike } from '../../src/render/bike/bikeModel';
import type { MaterialLibrary } from '../../src/render/materials/library';
import { FrameBuilder } from '../../src/render/frame';
import { BIKE_GEOMETRY_V2 } from '../../src/render/hero/assetFrame';
import { makeRiderRigPose, riderRigFromHips, riderPoseAtLean, RIDER_TORSO_REST } from '../../src/render/hero/riderRig';

type Ref = { meshName: string; vertexIndices: number[] };
type Pair = { source: Ref; repair: Ref; restPosition: number[] };
type Join = { join: string; closedCycle: boolean; orderedPairs: Pair[] };
type SeamMap = { asset: string; coordinateWeldMetres: number; seams: { side: string; joins: Join[] }[] };
type Endpoint = { mesh: THREE.SkinnedMesh; index: number };
type Edge = { count: number; direction: number };
const arg = (name: string) => process.argv.find(a => a.startsWith(`--${name}=`))?.slice(name.length + 3);
const out = path.resolve(arg('out') ?? 'docs/evidence/hero-remaster/wrists/v6-seams.json');
const full = arg('full') ?? 'assets/blender/hero-remaster/rider/candidate-v6-packed.glb';
const fullMap = arg('full-map') ?? 'assets/blender/hero-remaster/rider/candidate-v6.glb.seams.json';
const subjects = [{ label: 'full', file: full, map: fullMap }];
if (arg('lod')) subjects.push({ label: 'lod', file: arg('lod')!, map: arg('lod-map') ?? 'assets/blender/hero-remaster/rider/candidate-v6-lod.glb.seams.json' });
const poses = [
  { name: 'garage', stage: true, hips: [-.46, .75, 40] },
  ...[-1, 0, 1].map(lean => {
    const p = riderPoseAtLean(lean, makeRiderRigPose());
    return { name: lean < 0 ? 'backlean' : lean > 0 ? 'forwardlean' : 'neutral', stage: false, hips: [p.hips.x, p.hips.y, p.torsoAngle * 180 / Math.PI] };
  }),
  { name: 'compression', stage: false, hips: [-.57, .60, 55] },
  { name: 'extension', stage: false, hips: [-.14, .96, 40] },
  { name: 'landing', stage: false, hips: [-.40, .70, 40] },
];
const limits = { positionMetres: 1e-6, normalizedWeightL1: 1e-6, rawWeightL1: 1e-6, coefficientMaxAbs: 1e-6, worldGapMetres: 1e-6, triangleAreaSquareMetres: 1e-10 };
const failures: string[] = [];
const check = (ok: boolean, reason: string) => { if (!ok) failures.push(reason); };
const position = (e: Endpoint) => new THREE.Vector3().fromBufferAttribute(e.mesh.geometry.getAttribute('position'), e.index);
const world = (e: Endpoint) => e.mesh.getVertexPosition(e.index, new THREE.Vector3()).applyMatrix4(e.mesh.matrixWorld);
const maxAbs = (a: number[], b: number[]) => Math.max(...a.map((v, i) => Math.abs(v - (b[i] ?? 0))));
const edgeKey = (a: string, b: string) => a < b ? `${a}|${b}` : `${b}|${a}`;
const key = (p: THREE.Vector3) => p.toArray().map(v => Math.round(v * 1e6)).join(',');
function edges(mesh: THREE.SkinnedMesh): Map<string, Edge> {
  const index = mesh.geometry.index!;
  if (!index) throw new Error(`Indexed topology required: ${mesh.name}`);
  const keys = Array.from({ length: mesh.geometry.getAttribute('position').count }, (_, i) => key(position({ mesh, index: i })));
  const result = new Map<string, Edge>();
  for (let i = 0; i < index.count; i += 3) for (const [a, b] of [[0, 1], [1, 2], [2, 0]]) {
    const x = keys[index.getX(i + a!)]!, y = keys[index.getX(i + b!)]!;
    if (x === y) continue;
    const k = edgeKey(x, y), e = result.get(k) ?? { count: 0, direction: 0 };
    e.count++; e.direction += x < y ? 1 : -1; result.set(k, e);
  }
  return result;
}
function weights(e: Endpoint, normalize = false): Map<string, number> {
  const indices = e.mesh.geometry.getAttribute('skinIndex'), values = e.mesh.geometry.getAttribute('skinWeight');
  const result = new Map<string, number>(); let sum = 0;
  for (let lane = 0; lane < 4; lane++) {
    const w = values.getComponent(e.index, lane); if (!w) continue;
    const bone = boneName(e.mesh.skeleton.bones[indices.getComponent(e.index, lane)]!.name);
    result.set(bone, (result.get(bone) ?? 0) + w); sum += w;
  }
  if (normalize) for (const [bone, weight] of result) result.set(bone, weight / sum);
  return result;
}
function weightError(a: Endpoint, b: Endpoint, normalize: boolean): number {
  const x = weights(a, normalize), y = weights(b, normalize);
  return [...new Set([...x.keys(), ...y.keys()])].reduce((sum, bone) => sum + Math.abs((x.get(bone) ?? 0) - (y.get(bone) ?? 0)), 0);
}
/** LBS world position = meshWorld*bindInverse * sum_b(boneWorld_b * c_b).
 * c_b = rawWeight_b * boneInverse_b * bindMatrix * [position,1].
 * Equal coefficients, same live bone objects, and equal outer transforms prove seam equality
 * for arbitrary skeletal motion, including translations; normalized weights alone cannot.
 */
function coefficients(e: Endpoint): Map<string, { bone: THREE.Bone; vector: number[] }> {
  const p = position(e), bind = new THREE.Vector4(p.x, p.y, p.z, 1).applyMatrix4(e.mesh.bindMatrix);
  const indices = e.mesh.geometry.getAttribute('skinIndex'), values = e.mesh.geometry.getAttribute('skinWeight');
  const result = new Map<string, { bone: THREE.Bone; vector: number[] }>();
  for (let lane = 0; lane < 4; lane++) {
    const w = values.getComponent(e.index, lane); if (!w) continue;
    const i = indices.getComponent(e.index, lane), bone = e.mesh.skeleton.bones[i]!, name = boneName(bone.name);
    const v = bind.clone().applyMatrix4(e.mesh.skeleton.boneInverses[i]!).multiplyScalar(w).toArray();
    const prev = result.get(name);
    if (prev) v.forEach((x, j) => { prev.vector[j]! += x; }); else result.set(name, { bone, vector: v });
  }
  return result;
}
function auditPairs(pairs: { a: Endpoint; b: Endpoint }[]) {
  let localPositionMax = 0, normalizedWeightL1Max = 0, rawWeightL1Max = 0, coefficientMax = 0, outerTransformMax = 0, worldGapMax = 0, differentLiveBones = 0;
  for (const { a, b } of pairs) {
    localPositionMax = Math.max(localPositionMax, position(a).distanceTo(position(b)));
    normalizedWeightL1Max = Math.max(normalizedWeightL1Max, weightError(a, b, true));
    rawWeightL1Max = Math.max(rawWeightL1Max, weightError(a, b, false));
    const ca = coefficients(a), cb = coefficients(b);
    for (const bone of new Set([...ca.keys(), ...cb.keys()])) {
      const x = ca.get(bone), y = cb.get(bone);
      coefficientMax = Math.max(coefficientMax, maxAbs(x?.vector ?? [0, 0, 0, 0], y?.vector ?? [0, 0, 0, 0]));
      if (x && y && x.bone !== y.bone) differentLiveBones++;
    }
    const ma = a.mesh.matrixWorld.clone().multiply(a.mesh.bindMatrixInverse), mb = b.mesh.matrixWorld.clone().multiply(b.mesh.bindMatrixInverse);
    outerTransformMax = Math.max(outerTransformMax, maxAbs(ma.elements, mb.elements));
    worldGapMax = Math.max(worldGapMax, world(a).distanceTo(world(b)));
  }
  return { vertexPairs: pairs.length, localPositionMaxMetres: localPositionMax, normalizedWeightL1Max, rawWeightL1Max, coefficientMaxAbs: coefficientMax, outerTransformMaxAbs: outerTransformMax, differentLiveBones, worldGapMaxMetres: worldGapMax };
}
function accept(row: ReturnType<typeof auditPairs>, name: string) {
  check(row.localPositionMaxMetres <= limits.positionMetres, `${name}: local positions differ`);
  check(row.normalizedWeightL1Max <= limits.normalizedWeightL1 && row.rawWeightL1Max <= limits.rawWeightL1, `${name}: boundary weights differ`);
  check(row.coefficientMaxAbs <= limits.coefficientMaxAbs && row.outerTransformMaxAbs <= limits.coefficientMaxAbs && row.differentLiveBones === 0, `${name}: bind-aware skinning coefficients differ`);
  check(row.worldGapMaxMetres <= limits.worldGapMetres, `${name}: deformed seam gap exceeds 1 micrometre`);
}
await MeshoptEncoder.ready; await MeshoptDecoder.ready;
const reports = [];
for (const subject of subjects) {
  const bytes = fs.readFileSync(subject.file), mapBytes = fs.readFileSync(subject.map), mapping = JSON.parse(mapBytes.toString()) as SeamMap;
  const gltf = await loadRigAt(pathToFileURL(path.resolve(subject.file)), true);
  const rawBytes = fs.readFileSync(mapping.asset), raw = await loadRigAt(pathToFileURL(path.resolve(mapping.asset)), true);
  const rawMeshes = new Map<string, THREE.SkinnedMesh>();
  raw.scene.traverse(o => { if ((o as THREE.SkinnedMesh).isSkinnedMesh) rawMeshes.set(o.name, o as THREE.SkinnedMesh); });
  const packed = !bytes.equals(rawBytes), expectedPositions = new Map<string, Float32Array>();
  for (const [name, mesh] of rawMeshes) {
    const positions = mesh.geometry.getAttribute('position'), floats = new Float32Array(positions.count * 3);
    for (let i = 0; i < positions.count; i++) for (let c = 0; c < 3; c++) floats[i * 3 + c] = positions.getComponent(i, c);
    if (!packed) { expectedPositions.set(name, floats); continue; }
    const filtered = MeshoptEncoder.encodeFilterExp(floats, positions.count, 12, 16, 'SharedVector');
    const encoded = MeshoptEncoder.encodeVertexBuffer(filtered, positions.count, 12), decoded = new Uint8Array(filtered.length);
    MeshoptDecoder.decodeGltfBuffer(decoded, positions.count, 12, encoded, 'ATTRIBUTES', 'EXPONENTIAL');
    expectedPositions.set(name, new Float32Array(decoded.buffer));
  }
  let rawMapPositionMax = 0, packedPositionDriftMax = 0, expectedPackedPositionMax = 0;
  await prepareHero(gltf);
  const rider = new GltfRider(gltf, { complete() {} } as unknown as MaterialLibrary), frame = new THREE.Group();
  rider.attach({ frame } as HeroBike); frame.updateMatrixWorld(true);
  const meshes = new Map<string, THREE.SkinnedMesh>();
  frame.traverse(o => { if ((o as THREE.SkinnedMesh).isSkinnedMesh) { check(!meshes.has(o.name), `Duplicate mesh ${o.name}`); meshes.set(o.name, o as THREE.SkinnedMesh); } });
  const resolve = (ref: Ref, expected: number[]): Endpoint[] => ref.vertexIndices.map(index => {
    const mesh = meshes.get(ref.meshName); if (!mesh) throw new Error(`Map mesh missing: ${ref.meshName}`);
    const endpoint = { mesh, index };
    if (index < 0 || index >= mesh.geometry.getAttribute('position').count) throw new Error(`Invalid map index ${ref.meshName}:${index}`);
    const rawMesh = rawMeshes.get(ref.meshName); if (!rawMesh) throw new Error(`Raw map mesh missing: ${ref.meshName}`);
    const rawPosition = position({ mesh: rawMesh, index }), currentPosition = position(endpoint);
    const rawError = rawPosition.distanceTo(new THREE.Vector3(...expected)); rawMapPositionMax = Math.max(rawMapPositionMax, rawError);
    const expectedArray = expectedPositions.get(ref.meshName)!, packedExpected = new THREE.Vector3().fromArray(expectedArray, index * 3);
    const packingError = currentPosition.distanceTo(packedExpected); expectedPackedPositionMax = Math.max(expectedPackedPositionMax, packingError);
    packedPositionDriftMax = Math.max(packedPositionDriftMax, rawPosition.distanceTo(currentPosition));
    check(rawError <= mapping.coordinateWeldMetres, `${subject.label}: raw map position mismatch ${ref.meshName}:${index}`);
    check(packingError === 0, `${subject.label}: packed map index differs from production EXPONENTIAL/16/SharedVector stream ${ref.meshName}:${index}`);
    return endpoint;
  });
  const joins = mapping.seams.flatMap(s => s.joins.map(j => {
    const groups = j.orderedPairs.map(p => ({ source: resolve(p.source, p.restPosition), repair: resolve(p.repair, p.restPosition) }));
    const pairs = groups.flatMap(g => g.source.flatMap(a => g.repair.map(b => ({ a, b }))));
    const sourceEdges = edges(groups[0]!.source[0]!.mesh), repairEdges = edges(groups[0]!.repair[0]!.mesh);
    const contour = groups.map(g => key(position(g.source[0]!))), duplicateContourVertices = contour.length - new Set(contour).size;
    const topology = { declaredClosedCycle: j.closedCycle, contourVertices: contour.length, duplicateContourVertices, missingSourceBoundaryEdges: 0, missingRepairBoundaryEdges: 0, inconsistentWindingEdges: 0 };
    for (let i = 0; i < contour.length; i++) {
      const k = edgeKey(contour[i]!, contour[(i + 1) % contour.length]!), a = sourceEdges.get(k), b = repairEdges.get(k);
      if (a?.count !== 1) topology.missingSourceBoundaryEdges++;
      if (b?.count !== 1) topology.missingRepairBoundaryEdges++;
      if (a && b && a.direction + b.direction !== 0) topology.inconsistentWindingEdges++;
    }
    check(j.closedCycle && contour.length >= 3 && duplicateContourVertices === 0 && topology.missingSourceBoundaryEdges === 0 && topology.missingRepairBoundaryEdges === 0 && topology.inconsistentWindingEdges === 0, `${subject.label}/${s.side}/${j.join}: actual topology is not a closed sewn boundary`);
    return { side: s.side, join: j.join, pairs, contour, topology };
  }));
  check(joins.length === 4 && ['L', 'R'].every(side => ['body', 'glove'].every(join => joins.some(j => j.side === side && j.join === join))), `${subject.label}: requires all four body/glove wrist joins`);
  const repairMesh = meshes.get('Street_continuous_wrists')!;
  const repairEdges = edges(repairMesh), mappedEdges = new Set(joins.flatMap(j => j.contour.map((p, i) => edgeKey(p, j.contour[(i + 1) % j.contour.length]!))));
  const unmappedRepairBoundaryEdges = [...repairEdges].filter(([k, e]) => e.count === 1 && !mappedEdges.has(k)).length;
  const inconsistentInternalRepairWindingEdges = [...repairEdges.values()].filter(e => e.count === 2 && e.direction !== 0).length;
  check(inconsistentInternalRepairWindingEdges === 0, `${subject.label}: inconsistent internal repair winding`);
  const nonManifoldRepairEdges = [...repairEdges.values()].filter(e => e.count > 2).length;
  check(unmappedRepairBoundaryEdges === 0 && nonManifoldRepairEdges === 0, `${subject.label}: unmapped or nonmanifold repair edges`);
  const rows = [];
  // GltfRider's Garage uses authored weights; riding uses conditionSleeveSkin output.
  for (const pose of poses) {
    rider.setStage(pose.stage); rider.setStageTime(.75);
    const [hx, hy, torso] = pose.hips, rig = riderRigFromHips(hx!, hy!, torso! * Math.PI / 180, makeRiderRigPose()), f = new FrameBuilder().frame;
    f.riderBody.present = true; f.riderBody.relX = rig.com.x + BIKE_GEOMETRY_V2.chassisToAxle.x; f.riderBody.relY = rig.com.y + BIKE_GEOMETRY_V2.chassisToAxle.y;
    f.riderBody.relAngle = rig.torsoAngle - RIDER_TORSO_REST; f.tSim = 4; f.dt = 1 / 60; f.cut = true; f.speed = 0;
    for (let i = 0; i < 20; i++) { rider.update(f); frame.updateMatrixWorld(true); }
    const joinRows = joins.map(j => { const metrics = auditPairs(j.pairs); accept(metrics, `${subject.label}/${pose.name}/${j.side}/${j.join}`); return { side: j.side, join: j.join, ...metrics }; });
    let degenerateRepairTriangles = 0, minRepairTriangleArea = Infinity;
    const idx = repairMesh.geometry.index!;
    for (let i = 0; i < idx.count; i += 3) {
      const points = [0, 1, 2].map(k => world({ mesh: repairMesh, index: idx.getX(i + k) }));
      const area = new THREE.Triangle(points[0]!, points[1]!, points[2]!).getArea(); minRepairTriangleArea = Math.min(minRepairTriangleArea, area);
      if (area < limits.triangleAreaSquareMetres || !Number.isFinite(area)) degenerateRepairTriangles++;
    }
    check(degenerateRepairTriangles === 0, `${subject.label}/${pose.name}: collapsed repair triangles`);
    rows.push({ pose: pose.name, syntheticRuntimeFrame: true, stageClip: rider.debug.stageClip, joins: joinRows, repairTriangles: idx.count / 3, degenerateRepairTriangles, minRepairTriangleAreaSquareMetres: minRepairTriangleArea });
  }
  reports.push({ subject: subject.label, file: subject.file, sha256: crypto.createHash('sha256').update(bytes).digest('hex'), map: subject.map, mapSHA256: crypto.createHash('sha256').update(mapBytes).digest('hex'), rawMapAsset: mapping.asset, rawMapAssetSHA256: crypto.createHash('sha256').update(rawBytes).digest('hex'), mapAssociation: { packed, rawMapPositionMaxMetres: rawMapPositionMax, packedPositionDriftMaxMetres: packedPositionDriftMax, expectedPackedPositionMaxMetres: expectedPackedPositionMax, method: 'Raw explicit indices validated against recorded positions, then independently reproduced production EXPONENTIAL/16/SharedVector packing with unchanged indices.' }, topology: joins.map(j => ({ side: j.side, join: j.join, ...j.topology })), unmappedRepairBoundaryEdges, nonManifoldRepairEdges, inconsistentInternalRepairWindingEdges, poses: rows });
  rider.dispose();
}
const report = { pass: failures.length === 0, limits, method: 'Explicit contour correspondence; independent welded triangle-edge incidence; raw and normalized bone-name weights; bind-aware homogeneous LBS coefficients with identical live bone objects and outer transforms; production prepareHero/GltfRider/conditionSleeveSkin CPU deformation.', limitations: ['Seven synthetic runtime frame cases are quantitative probes, not played game evidence.', 'No textures, GPU, silhouettes, collisions, self-intersections or art acceptance asserted.', 'Matching linear skinning coefficients bounds seam splitting for arbitrary bone transforms; triangle areas are checked only in listed cases.', 'Position weld is 1 micrometre for actual edge topology; map association uses its recorded coordinateWeldMetres.'], subjects: reports, failures };
fs.mkdirSync(path.dirname(out), { recursive: true }); fs.writeFileSync(out, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ pass: report.pass, subjects: reports.map(r => ({ subject: r.subject, sha256: r.sha256, maxWorldGapMetres: Math.max(...r.poses.flatMap(p => p.joins.map(j => j.worldGapMaxMetres))) })), failures, out }, null, 2));
if (!report.pass) process.exitCode = 1;
