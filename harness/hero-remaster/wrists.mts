/** CPU skin-surface audit; no DOM, browser, audio, GPU, or asset writes.
 * pnpm exec tsx harness/hero-remaster/wrists.mts [--out=docs/evidence/hero-remaster/wrists]
 * Bone/socket proximity is reported separately from cuff coverage; neither proves a closed seam.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
import * as THREE from 'three';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils';
import { prepareHero } from '../../src/render/hero/lod';
import { boneName, GltfRider } from '../../src/render/hero/gltfRider';
import type { HeroBike } from '../../src/render/bike/bikeModel';
import type { MaterialLibrary } from '../../src/render/materials/library';
import { FrameBuilder } from '../../src/render/frame';
import { BIKE_GEOMETRY_V2 } from '../../src/render/hero/assetFrame';
import { makeRiderRigPose, riderRigFromHips, riderPoseAtLean, RIDER_TORSO_REST } from '../../src/render/hero/riderRig';

type Side = 'L' | 'R';
type Face = { mesh: THREE.SkinnedMesh; id: number; indices: number[]; group: 'sleeve' | 'glove' };
type Rim = { mesh: THREE.SkinnedMesh; edges: [number, number][]; components: { edges: number; vertices: number; vertexIndices: number[]; meanHandWeight: number; restCenter: number[]; degreeHistogram: Record<string, number>; closedCycle: boolean }[] };
type Anchor = { centerHandLocal: THREE.Vector3; normalHandLocal: THREE.Vector3; sourceMesh: string; sourceVertices: number[] };
const anchors = new Map<Side, Anchor>();
const out = path.resolve(process.argv.find(x => x.startsWith('--out='))?.slice(6) ?? 'docs/evidence/hero-remaster/wrists');
fs.mkdirSync(out, { recursive: true });
// Pin the donor so the before audit remains reproducible after promotion.
const donorCommit = 'ec04192d61e39dcc8bdb80fd97842e8019ef4e55';
const donorPaths = ['rider-street-mustard.glb', 'rider-street-mustard-lod.glb'];
for (const filename of donorPaths) fs.writeFileSync(path.join(out, filename), execFileSync('git', ['show', `${donorCommit}:public/models/${filename}`], { maxBuffer: 16 * 1024 * 1024 }));
const subjects = [
  ['original-full', path.join(out, donorPaths[0]!)],
  ['original-lod', path.join(out, donorPaths[1]!)],
  ['v5-full', 'assets/blender/hero-remaster/rider/candidate-v5-packed.glb'],
  ['v5-lod', 'assets/blender/hero-remaster/rider/candidate-v5-lod-packed.glb'],
] as const;
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
const quant = (v: THREE.Vector3) => v.toArray().map(x => Math.round(x * 1e5)).join(',');
const percentile = (values: number[], p: number) => values.length ? [...values].sort((a, b) => a - b)[Math.min(values.length - 1, Math.floor(values.length * p))]! : null;
function weight(mesh: THREE.SkinnedMesh, vertex: number, names: string[]): number {
  const si = mesh.geometry.getAttribute('skinIndex'), sw = mesh.geometry.getAttribute('skinWeight');
  let sum = 0;
  for (let i = 0; i < 4; i++) if (names.includes(boneName(mesh.skeleton.bones[si.getComponent(vertex, i)]!.name))) sum += sw.getComponent(vertex, i);
  return sum;
}
function weights(mesh: THREE.SkinnedMesh, i: number) {
  const si = mesh.geometry.getAttribute('skinIndex'), sw = mesh.geometry.getAttribute('skinWeight'), out: Record<string, number> = {};
  let total = 0;
  for (let lane = 0; lane < 4; lane++) { const name = boneName(mesh.skeleton.bones[si.getComponent(i, lane)]!.name), w = sw.getComponent(i, lane); out[name] = (out[name] ?? 0) + w; total += w; }
  for (const name of Object.keys(out)) out[name]! /= total;
  return out;
}
function vertex(mesh: THREE.SkinnedMesh, i: number): THREE.Vector3 {
  return mesh.getVertexPosition(i, new THREE.Vector3()).applyMatrix4(mesh.matrixWorld);
}
function boundary(mesh: THREE.SkinnedMesh, side: Side, wrist: THREE.Vector3, axis: THREE.Vector3): Rim {
  const index = mesh.geometry.index!, positions = mesh.geometry.getAttribute('position');
  const keys = new Map<string, number>(), weld: number[] = [];
  for (let i = 0; i < positions.count; i++) {
    const key = quant(new THREE.Vector3().fromBufferAttribute(positions, i));
    if (!keys.has(key)) keys.set(key, i);
    weld.push(keys.get(key)!);
  }
  const map = new Map<string, { edge: [number, number]; count: number }>();
  for (let i = 0; i < index.count; i += 3) for (const [a, b] of [[0, 1], [1, 2], [2, 0]]) {
    const x = weld[index.getX(i + a!)]!, y = weld[index.getX(i + b!)]!;
    if (x === y) continue;
    const key = x < y ? `${x}:${y}` : `${y}:${x}`;
    const item = map.get(key);
    if (item) item.count++; else map.set(key, { edge: [x, y], count: 1 });
  }
  const edges: [number, number][] = [];
  for (const { count, edge } of map.values()) {
    if (count !== 1) continue;
    const [a, b] = edge, p = vertex(mesh, a).add(vertex(mesh, b)).multiplyScalar(.5).sub(wrist);
    const axial = p.dot(axis), radius = p.clone().addScaledVector(axis, -axial).length();
    if (axial < -.12 || axial > .10 || radius > .20) continue;
    if ((weight(mesh, a, [`hand.${side}`, `forearm.${side}`]) + weight(mesh, b, [`hand.${side}`, `forearm.${side}`])) < .2) continue;
    edges.push(edge);
  }
  const adjacent = new Map<number, number[]>();
  for (const [a, b] of edges) { adjacent.set(a, [...adjacent.get(a) ?? [], b]); adjacent.set(b, [...adjacent.get(b) ?? [], a]); }
  const seen = new Set<number>(), components: Rim['components'] = [];
  for (const start of adjacent.keys()) {
    if (seen.has(start)) continue;
    const stack = [start], ids: number[] = [];
    while (stack.length) { const i = stack.pop()!; if (seen.has(i)) continue; seen.add(i); ids.push(i); stack.push(...adjacent.get(i)!); }
    const degreeHistogram: Record<string, number> = {};
    for (const i of ids) { const d = adjacent.get(i)!.length; degreeHistogram[d] = (degreeHistogram[d] ?? 0) + 1; }
    const center = ids.reduce((p, i) => p.add(vertex(mesh, i)), new THREE.Vector3()).multiplyScalar(1 / ids.length);
    components.push({ edges: ids.reduce((n, i) => n + adjacent.get(i)!.length, 0) / 2, vertices: ids.length, vertexIndices: ids, meanHandWeight: ids.reduce((n, i) => n + weight(mesh, i, [`hand.${side}`]), 0) / ids.length, restCenter: center.toArray(), degreeHistogram, closedCycle: ids.length >= 3 && ids.every(i => adjacent.get(i)!.length === 2) });
  }
  return { mesh, edges, components };
}
function selection(meshes: THREE.SkinnedMesh[], side: Side, wrist: THREE.Vector3, axis: THREE.Vector3) {
  const faces: Face[] = [], rims: Rim[] = [];
  for (const mesh of meshes) {
    const index = mesh.geometry.index;
    if (!index) throw new Error(`Indexed mesh required: ${mesh.name}`);
    for (let i = 0; i < index.count; i += 3) {
      const indices = [index.getX(i), index.getX(i + 1), index.getX(i + 2)];
      const center = indices.reduce((p, v) => p.add(vertex(mesh, v)), new THREE.Vector3()).multiplyScalar(1 / 3);
      const total = indices.reduce((n, v) => n + weight(mesh, v, [`hand.${side}`, `forearm.${side}`]), 0) / 3;
      if (center.distanceTo(wrist) > .25 || total < .15) continue;
      const hand = indices.reduce((n, v) => n + weight(mesh, v, [`hand.${side}`]), 0) / 3;
      const group = mesh.name.startsWith('Authored_grips') || (!mesh.name.startsWith('Street_remaster') && hand > .55) ? 'glove' : 'sleeve';
      faces.push({ mesh, id: i / 3, indices, group });
    }
    rims.push(boundary(mesh, side, wrist, axis));
  }
  return { faces, rims };
}
type Point = { x: number; y: number; z: number };
function slice(triangles: { points: Point[]; group: Face['group'] }[], z: number) {
  const segments: { a: Point; b: Point; group: Face['group'] }[] = [];
  for (const triangle of triangles) {
    const hit: Point[] = [];
    for (const [i, j] of [[0, 1], [1, 2], [2, 0]]) {
      const a = triangle.points[i!]!, b = triangle.points[j!]!;
      if (Math.abs(a.z - z) < 1e-6 && Math.abs(b.z - z) < 1e-6) { segments.push({ a, b, group: triangle.group }); continue; }
      if ((a.z < z) === (b.z < z) || Math.abs(a.z - b.z) < 1e-12) continue;
      const t = (z - a.z) / (b.z - a.z);
      hit.push({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, z });
    }
    if (hit.length === 2) segments.push({ a: hit[0]!, b: hit[1]!, group: triangle.group });
  }
  const radii: number[] = [], coverage = { union: 0, sleeve: 0, glove: 0 };
  for (let i = 0; i < 32; i++) {
    const angle = i * Math.PI / 16, dx = Math.cos(angle), dy = Math.sin(angle);
    let sleeve = false, glove = false, nearest = Infinity;
    for (const { a, b, group } of segments) {
      const ex = b.x - a.x, ey = b.y - a.y, det = dx * ey - dy * ex;
      if (Math.abs(det) < 1e-12) continue;
      const t = (a.x * ey - a.y * ex) / det, u = (a.x * dy - a.y * dx) / det;
      if (t < .008 || t > .20 || u < -1e-6 || u > 1 + 1e-6) continue;
      if (group === 'sleeve') sleeve = true; else glove = true;
      nearest = Math.min(nearest, t);
    }
    if (sleeve) coverage.sleeve++; if (glove) coverage.glove++;
    if (sleeve || glove) { coverage.union++; radii.push(nearest); }
  }
  return { axialMetres: z, segments: segments.length, coverage: { union: coverage.union / 32, sleeve: coverage.sleeve / 32, glove: coverage.glove / 32 }, medianRadiusMetres: percentile(radii, .5), maxRadiusMetres: percentile(radii, 1) };
}
function surfaceDistances(samples: THREE.Vector3[], faces: Face[], group: Face['group']) {
  if (!samples.length) return null;
  const all = faces.filter(f => f.group === group).map(f => new THREE.Triangle(...f.indices.map(i => vertex(f.mesh, i)) as [THREE.Vector3, THREE.Vector3, THREE.Vector3]));
  const triangles = all.filter(t => t.getArea() > 1e-12);
  if (!triangles.length) return null;
  const distances = samples.map(p => {
    let best = Infinity;
    for (const t of triangles) { const d = p.distanceTo(t.closestPointToPoint(p, new THREE.Vector3())); if (Number.isFinite(d)) best = Math.min(best, d); }
    return best;
  });
  return { samples: samples.length, opposingTriangles: triangles.length, degenerateOpposingTrianglesExcluded: all.length - triangles.length, minMetres: percentile(distances, 0), medianMetres: percentile(distances, .5), p95Metres: percentile(distances, .95), maxMetres: percentile(distances, 1) };
}
const matrixReports: unknown[] = [], reports: unknown[] = [];
for (const [label, relative] of subjects) {
  const file = path.resolve(relative), bytes = fs.readFileSync(file), gltf = await loadRigAt(pathToFileURL(file), true);
  await prepareHero(gltf);
  const rider = new GltfRider(gltf, { complete() {} } as unknown as MaterialLibrary), frame = new THREE.Group();
  rider.attach({ frame } as HeroBike); frame.updateMatrixWorld(true);
  const meshes: THREE.SkinnedMesh[] = [], bones = new Map<string, THREE.Bone>();
  frame.traverse(o => { if ((o as THREE.SkinnedMesh).isSkinnedMesh) meshes.push(o as THREE.SkinnedMesh); if ((o as THREE.Bone).isBone) bones.set(boneName(o.name), o as THREE.Bone); });
  const selected = Object.fromEntries((['L', 'R'] as const).map(side => {
    const wrist = bones.get(`hand.${side}`)!.getWorldPosition(new THREE.Vector3());
    const axis = wrist.clone().sub(bones.get(`forearm.${side}`)!.getWorldPosition(new THREE.Vector3())).normalize();
    return [side, selection(meshes, side, wrist, axis)];
  })) as Record<Side, ReturnType<typeof selection>>;
  const coincident = Object.fromEntries((['L', 'R'] as const).map(side => {
    const byPosition = new Map<string, { mesh: THREE.SkinnedMesh; index: number; rest: THREE.Vector3 }[]>(), seen = new Set<string>();
    for (const face of selected[side].faces) for (const i of face.indices) {
      const id = `${face.mesh.uuid}:${i}`; if (seen.has(id)) continue; seen.add(id);
      const rest = vertex(face.mesh, i), key = rest.toArray().map(x => Math.round(x * 1e4)).join(',');
      byPosition.set(key, [...byPosition.get(key) ?? [], { mesh: face.mesh, index: i, rest }]);
    }
    const pairs = [];
    for (const group of byPosition.values()) for (let i = 0; i < group.length; i++) for (let j = i + 1; j < group.length; j++) {
      const a = group[i]!, b = group[j]!;
      if (a.mesh === b.mesh || a.rest.distanceTo(b.rest) > .0002) continue;
      const wa = weights(a.mesh, a.index), wb = weights(b.mesh, b.index), error = [...new Set([...Object.keys(wa), ...Object.keys(wb)])].reduce((n, bone) => n + Math.abs((wa[bone] ?? 0) - (wb[bone] ?? 0)), 0);
      pairs.push({ a, b, weightsA: wa, weightsB: wb, normalizedWeightL1Error: error, restErrorMetres: a.rest.distanceTo(b.rest) });
    }
    return [side, pairs];
  })) as Record<Side, { a: { mesh: THREE.SkinnedMesh; index: number; rest: THREE.Vector3 }; b: { mesh: THREE.SkinnedMesh; index: number; rest: THREE.Vector3 }; weightsA: Record<string, number>; weightsB: Record<string, number>; normalizedWeightL1Error: number; restErrorMetres: number }[]>;
  if (label === 'original-full') for (const side of ['L', 'R'] as const) {
    const choices = selected[side].rims.flatMap(r => r.components.filter(c => c.closedCycle && c.meanHandWeight > .99 && c.vertices >= 50).map(c => ({ rim: r, component: c })));
    if (choices.length !== 1) throw new Error(`Full donor glove opening must be unambiguous ${side}: ${choices.length}`);
    const { rim, component } = choices[0]!, points = component.vertexIndices.map(i => vertex(rim.mesh, i));
    const center = points.reduce((p, v) => p.add(v), new THREE.Vector3()).multiplyScalar(1 / points.length);
    let normal = new THREE.Vector3(), area = 0;
    for (const a of points) for (const b of points) {
      const cross = a.clone().sub(points[0]!).cross(b.clone().sub(points[0]!));
      if (cross.lengthSq() > area) { area = cross.lengthSq(); normal = cross; }
    }
    normal.normalize();
    const hand = bones.get(`hand.${side}`)!, inverse = hand.matrixWorld.clone().invert();
    anchors.set(side, { centerHandLocal: center.applyMatrix4(inverse), normalHandLocal: normal.transformDirection(inverse), sourceMesh: rim.mesh.name, sourceVertices: component.vertexIndices });
  }
  const selections = Object.fromEntries((['L', 'R'] as const).map(side => [side, {
    faces: selected[side].faces.map(f => ({ mesh: f.mesh.name, triangle: f.id, vertices: f.indices, group: f.group })),
    rims: selected[side].rims.filter(r => r.edges.length).map(r => ({ mesh: r.mesh.name, edges: r.edges, components: r.components, weights: [...new Set(r.edges.flat())].map(i => ({ vertex: i, weights: Array.from({ length: 4 }, (_, lane) => ({ bone: boneName(r.mesh.skeleton.bones[r.mesh.geometry.getAttribute('skinIndex').getComponent(i, lane)]!.name), weight: r.mesh.geometry.getAttribute('skinWeight').getComponent(i, lane) })) })) })),
  }]));
  fs.writeFileSync(path.join(out, `${label}-selection.json`), JSON.stringify(selections, null, 2) + '\n');
  const rows: unknown[] = [];
  for (const pose of poses) {
    rider.setStage(pose.stage); rider.setStageTime(.75);
    const [hx, hy, torso] = pose.hips;
    const rig = riderRigFromHips(hx!, hy!, torso! * Math.PI / 180, makeRiderRigPose()), f = new FrameBuilder().frame;
    f.riderBody.present = true; f.riderBody.relX = rig.com.x + BIKE_GEOMETRY_V2.chassisToAxle.x; f.riderBody.relY = rig.com.y + BIKE_GEOMETRY_V2.chassisToAxle.y;
    f.riderBody.relAngle = rig.torsoAngle - RIDER_TORSO_REST; f.tSim = 4; f.dt = 1 / 60; f.cut = true; f.speed = 0;
    for (let i = 0; i < 20; i++) { rider.update(f); frame.updateMatrixWorld(true); }
    matrixReports.push({ subject: label, pose: pose.name, hips: pose.hips, frame: { bikeX: f.bikeX, bikeY: f.bikeY, bikeAngle: f.bikeAngle, riderBody: f.riderBody }, debug: structuredClone(rider.debug), frameMatrix: frame.matrixWorld.toArray(), bones: [...bones].map(([name, b]) => ({ name, localPosition: b.position.toArray(), localQuaternion: b.quaternion.toArray(), matrixWorld: b.matrixWorld.toArray() })), meshes: meshes.map(m => ({ name: m.name, matrixWorld: m.matrixWorld.toArray(), bindMatrix: m.bindMatrix.toArray(), bindMatrixInverse: m.bindMatrixInverse.toArray(), bones: m.skeleton.bones.map(b => boneName(b.name)), boneInverses: m.skeleton.boneInverses.map(x => x.toArray()) })) });
    for (const side of ['L', 'R'] as const) {
      const wrist = bones.get(`hand.${side}`)!.getWorldPosition(new THREE.Vector3()), elbow = bones.get(`forearm.${side}`)!.getWorldPosition(new THREE.Vector3());
      const axis = wrist.clone().sub(elbow).normalize(), u = new THREE.Vector3(0, 0, 1).cross(axis).normalize(), v = axis.clone().cross(u).normalize();
      const faces = selected[side].faces, triangles = faces.map(face => ({ group: face.group, points: face.indices.map(i => { const p = vertex(face.mesh, i).sub(wrist); return { x: p.dot(u), y: p.dot(v), z: p.dot(axis) }; }) }));
      const sections = Array.from({ length: 101 }, (_, i) => slice(triangles, -.12 + i * .002));
      const joint = sections.filter(s => s.axialMetres >= -.06 && s.axialMetres <= .04);
      const anchor = anchors.get(side)!, hand = bones.get(`hand.${side}`)!;
      const cuffCenter = anchor.centerHandLocal.clone().applyMatrix4(hand.matrixWorld), cuffAxis = anchor.normalHandLocal.clone().transformDirection(hand.matrixWorld);
      if (cuffAxis.dot(axis) < 0) cuffAxis.negate();
      const cuffU = new THREE.Vector3(0, 0, 1).cross(cuffAxis).normalize(), cuffV = cuffAxis.clone().cross(cuffU).normalize();
      const cuffTriangles = faces.map(face => ({ group: face.group, points: face.indices.map(i => { const p = vertex(face.mesh, i).sub(cuffCenter); return { x: p.dot(cuffU), y: p.dot(cuffV), z: p.dot(cuffAxis) }; }) }));
      const cuffSections = Array.from({ length: 41 }, (_, i) => slice(cuffTriangles, -.04 + i * .002));
      const cuffJoin = cuffSections.filter(s => s.axialMetres >= -.01 && s.axialMetres <= .01);
      const degenerates = { sleeve: 0, glove: 0 };
      for (const face of faces) { const p = face.indices.map(i => vertex(face.mesh, i)); if (new THREE.Triangle(p[0]!, p[1]!, p[2]!).getArea() < 1e-10) degenerates[face.group]++; }
      let current = 0, longest = 0;
      for (const s of joint) { current = s.coverage.union < .5 ? current + 1 : 0; longest = Math.max(longest, current); }
      const boundaryRows = selected[side].rims.filter(r => r.edges.length).map(r => {
        const group = r.mesh.name.startsWith('Authored_grips') ? 'glove' : 'sleeve';
        const all = r.edges.map(([a, b]) => vertex(r.mesh, a).add(vertex(r.mesh, b)).multiplyScalar(.5));
        const points = all.filter((_, i) => i % Math.max(1, Math.ceil(all.length / 64)) === 0);
        return { mesh: r.mesh.name, edges: r.edges.length, components: r.components, collapsedEdgesUnderHalfMillimetre: r.edges.filter(([a, b]) => vertex(r.mesh, a).distanceTo(vertex(r.mesh, b)) < .0005).length, opposingTriangleSurfaceDistance: surfaceDistances(points, faces, group === 'glove' ? 'sleeve' : 'glove') };
      });
      const seamCandidates = coincident[side].map(p => ({ meshA: p.a.mesh.name, vertexA: p.a.index, meshB: p.b.mesh.name, vertexB: p.b.index, weightsA: p.weightsA, weightsB: p.weightsB, normalizedWeightL1Error: p.normalizedWeightL1Error, restErrorMetres: p.restErrorMetres, deformedErrorMetres: vertex(p.a.mesh, p.a.index).distanceTo(vertex(p.b.mesh, p.b.index)) }));
      rows.push({ pose: pose.name, side, physicalPose: rider.debug.physicalPose, stageClip: rider.debug.stageClip, wristBone: wrist.toArray(), elbowBone: elbow.toArray(), gripErrorMetres: rider.debug.gripErr[side === 'L' ? 0 : 1], faces: { sleeve: faces.filter(f => f.group === 'sleeve').length, glove: faces.filter(f => f.group === 'glove').length }, degenerateTrianglesAreaUnder1eMinus10SquareMetres: degenerates, coincidentCrossMeshCandidates: { count: seamCandidates.length, notAClosedSeamCorrespondence: true, maxNormalizedWeightL1Error: percentile(seamCandidates.map(p => p.normalizedWeightL1Error), 1), maxDeformedErrorMetres: percentile(seamCandidates.map(p => p.deformedErrorMetres), 1), pairs: seamCandidates }, cuffAnchor: { source: 'original-full pure-hand-weight closed88vertex glove-opening contour', sourceMesh: anchor.sourceMesh, sourceVertices: anchor.sourceVertices, center: cuffCenter.toArray(), normal: cuffAxis.toArray(), centerHandLocal: anchor.centerHandLocal.toArray(), normalHandLocal: anchor.normalHandLocal.toArray() }, cuffOpeningPlane: cuffSections[20], cuffJoinMinAngularCoverage: Math.min(...cuffJoin.map(s => s.coverage.union)), cuffSections, wristPlane: sections[60], joinWindowMinAngularCoverage: Math.min(...joint.map(s => s.coverage.union)), longestAxialIntervalWithUnderHalfRingCoverageMetres: longest * .002, boundary: boundaryRows, sections });
    }
  }
  const report = { subject: label, source: file, bytes: bytes.length, sha256: crypto.createHash('sha256').update(bytes).digest('hex'), rows };
  fs.writeFileSync(path.join(out, `${label}.json`), JSON.stringify(report, null, 2) + '\n'); reports.push({ subject: label, source: file, sha256: report.sha256, report: `${label}.json` });
  console.log(JSON.stringify({ subject: label, sha256: report.sha256, poses: rows.length }));
}
fs.writeFileSync(path.join(out, 'runtime-matrices.json'), JSON.stringify(matrixReports, null, 2) + '\n');
fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify({ method: { decoder: 'GLTFLoader/MeshoptDecoder, prepareHero, new GltfRider, real setStage/update, getVertexPosition', sourceSelection: 'Bind/rest: triangle centroid within25cm of hand bone and average same-side forearm+hand weight>=.15. Original glove partition average hand weight>.55; V5 authored contact mesh separate.', topology: 'Open edges after10micrometre position welding; selected midpoints axial[-12,+10]cm, radius<=20cm, side arm weight>=.10. Selected region can truncate an edge component, so a noncycle is diagnostic, not definitive full-mesh topology.', slices: 'Triangle-plane intersections in runtime elbow→wrist frame.101planes every2mm from-12cm to+8cm;32radial rays each. Hits at radii8mm..20cm. Full angular occupancy alone does not prove connected/watertight seam.', cuffAnchor: 'Actual unique original-full closed88vertex glove opening, mean hand weight>.99; centroid and plane normal transformed through corresponding hand bone. Shared full donor reference is explicit for LOD rather than inventing a closed LOD contour.41planes every2mm ±4cm; focus ±1cm.', surfaceDistance: 'Deterministic maximum64open-edge midpoint samples permesh to opposing complete selected nondegenerate triangles; excluded degenerate count explicit. Never arbitrary nearestvertex.', coincidentCandidates: 'Cross-mesh vertices in same100micrometre rest-world bin, restdistance<=200micrometres. Normalize weights by actual skeleton bone names, compareL1 and actual deformedpositions. Does NOT establish full-ring correspondence.', poses: 'Garage plays accepted clip at.75seconds. Six riding poses use real GltfRider physical IK path from explicit hips/torso table,20updates to settle stageexit; synthetic runtime frames, not recorded actual Game events.' }, unmeasured: ['Watertight stitched sleeve/glove ring correspondence', 'Material/texture silhouette and actual camera exposure', 'Continuous every-tick recorded riding/crash pose sweep', 'Visual hand-size acceptance', 'Actual engine frame matrix parity; parent camera harness owns comparison'], reports }, null, 2) + '\n');

for (const filename of donorPaths) fs.unlinkSync(path.join(out, filename));
