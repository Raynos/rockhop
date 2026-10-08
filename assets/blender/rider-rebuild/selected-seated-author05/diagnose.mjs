/** Saved author04 TRS readback only. No driver, optimizer, browser or mesh edits. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../../../src/render/hero/gltfTestUtils.ts';
import { load, mesh, M, pinned, sha } from '../selected-ankle-contact02/surface.mjs';
import { surface, support, clip, overlap, height, moment, nearest } from '../selected-seated-author04/geometry.mjs';

const source = 'assets/blender/rider-rebuild/selected-seated-author04/input.json';
const input = JSON.parse(fs.readFileSync(source));
for (const row of Object.values(input.pins)) pinned(row);
const patches = JSON.parse(pinned(input.pins.patches)), metadata = JSON.parse(pinned(input.pins.contract));
const out = process.argv.find(v => v.startsWith('--out='))?.slice(6);
assert(out && !fs.existsSync(out), 'Use a fresh --out=JSON_PATH');
assert(path.resolve(out).startsWith(path.resolve('harness/out/rider-rebuild/selected-seated-author05') + path.sep));
const gltf = await loadRigAt(pathToFileURL(path.resolve(input.pins.rider.path)), true);
const placement = new THREE.Group(); placement.quaternion.fromArray(metadata.driver.assetToBikeQuaternionXYZW);
placement.add(gltf.scene); placement.updateMatrixWorld(true);
const jeans = gltf.scene.getObjectByName('RiderJeans'); assert(jeans?.isSkinnedMesh);
const native = jeans.geometry.getAttribute('_native_id'), nativeRows = new Map();
for (let i = 0; i < native.count; i++) if (!nativeRows.has(native.getX(i))) nativeRows.set(native.getX(i), i);
const V = p => new THREE.Vector3(...p), range = values => [Math.min(...values), Math.max(...values)];
const sum = values => values.reduce((a, b) => a + b, 0);
const point = id => jeans.getVertexPosition(nativeRows.get(id), new THREE.Vector3()).applyMatrix4(jeans.matrixWorld);
const shape = (t, index) => surface(t.nativeVertexIDs.map(point), { row: index, nativeIDs: t.nativeVertexIDs, sourcePolygon: t.originalPolygonID });
const areaBelow = (triangles, saddle, bound) => {
  let area = 0;
  for (const a of triangles) if (a.normal.y < -1e-9) for (const b of saddle) {
    const polygon = overlap(a, b), gap = p => height(a, p) - height(b, p);
    area += moment(clip(polygon, p => bound - gap(p))).area;
  }
  return area;
};
const report = { accepted: false, recipeSHA256: sha(fs.readFileSync(new URL(import.meta.url))),
  sourceInputSHA256: sha(fs.readFileSync(source)),
  method: 'Apply saved boneLocalTRS without invoking the driver or solver; read only frozen core/context vertices.', bikes: [] };
for (const name of ['rookie', 'pro']) {
  const receiptPath = `harness/out/rider-rebuild/selected-seated-author04/authored01/${name}.json`;
  const bytes = fs.readFileSync(receiptPath), receipt = JSON.parse(bytes);
  for (const row of receipt.boneLocalTRS) {
    const bone = gltf.scene.getObjectByName(THREE.PropertyBinding.sanitizeNodeName(metadata.specification.jointNames[row.id]));
    assert(bone?.isBone); bone.position.fromArray(row.translation); bone.quaternion.fromArray(row.rotationXYZW); bone.scale.fromArray(row.scale);
  }
  placement.updateMatrixWorld(true);
  const raw = await load(receipt.bike), origin = raw.node('attach_frame_origin').point;
  const actual = mesh(raw, receipt.saddleSource.node, M().makeTranslation(-origin.x, -origin.y, -origin.z));
  const saddle = receipt.saddleSource.sourceTriangleOrdinals.map(row => surface([0, 1, 2].map(k => actual.point(actual.indices.get(row * 3 + k))), { row })).filter(t => t.normal.y > 1e-9);
  const sides = {};
  for (const side of ['left', 'right']) {
    const frozen = patches.patches[side], core = frozen.core.triangles.map(shape), context = frozen.context.triangles.map(shape);
    const m = support(core, saddle, 0.001), c = support(context, saddle, 0.001);
    assert(Math.abs(m.meanGapM - receipt.final.cores[side].meanGapM) < 1e-12, 'Saved TRS core readback differs');
    const vertices = frozen.core.nativeVertices.map(v => {
      const row = nativeRows.get(v.id), source = new THREE.Vector3().fromBufferAttribute(jeans.geometry.attributes.position, row).applyMatrix4(jeans.bindMatrix);
      const components = [];
      for (let k = 0; k < 4; k++) {
        const weight = jeans.geometry.attributes.skinWeight.getComponent(row, k); if (!weight) continue;
        const index = jeans.geometry.attributes.skinIndex.getComponent(row, k), bone = jeans.skeleton.bones[index];
        const p = source.clone().applyMatrix4(bone.matrixWorld.clone().multiply(jeans.skeleton.boneInverses[index]));
        components.push({ joint: bone.name, weight, pointBike: p.toArray() });
      }
      const posed = point(v.id), weighted = components.reduce((p, c) => p.addScaledVector(V(c.pointBike), c.weight), new THREE.Vector3());
      const componentReadbackResidualM = weighted.distanceTo(posed);
      assert(componentReadbackResidualM < 1e-9, 'Weighted components disagree with actual skinned point');
      return { nativeID: v.id, sourceXYZ: v.sourceXYZ, posedBike: posed.toArray(), componentReadbackResidualM, components };
    });
    let quadratureCost = 0;
    const triangles = core.map((t, i) => {
      const frozenTriangle = frozen.core.triangles[i];
      const originalPoints = frozenTriangle.nativeVertexIDs.map(id => V(frozen.core.nativeVertices.find(v => v.id === id).sourceXYZ));
      const originalArea = new THREE.Triangle(...originalPoints).getArea();
      for (let k = 0; k < 3; k++) {
        const p = t.points.reduce((v, p, j) => v.addScaledVector(p, j === k ? 2 / 3 : 1 / 6), new THREE.Vector3());
        const wanted = nearest(p, saddle).point.clone(); wanted.y += 0.0005;
        quadratureCost += originalArea / frozen.core.sourceAreaM2 / 3 * p.distanceToSquared(wanted) / 1e-6 / 2;
      }
      return { nativeIDs: t.nativeIDs, polygon: t.sourcePolygon, normalBike: t.normal.toArray(), heightRangeM: range(t.points.map(p => p.y)),
        sourceAreaM2: originalArea, posedAreaM2: t.area, areaRatio: t.area / originalArea,
        edgeRatios: [0, 1, 2].map(k => t.points[k].distanceTo(t.points[(k + 1) % 3]) / originalPoints[k].distanceTo(originalPoints[(k + 1) % 3])) };
    });
    const thresholds = [-0.01, -0.005, 0, 0.001, 0.005, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06];
    sides[side] = { sourceAreaM2: frozen.core.sourceAreaM2, posedAreaM2: m.surfaceAreaM2,
      posedToSourceAreaRatio: m.surfaceAreaM2 / frozen.core.sourceAreaM2,
      meanGapM: m.meanGapM, gapRangeM: [m.minimum.gapM, m.maximum.gapM],
      heightRangeM: range(core.flatMap(t => t.points.map(p => p.y))), normalRanges: [0, 1, 2].map(k => range(triangles.map(t => t.normalBike[k]))),
      gapAreaCdf: thresholds.map(gapM => ({ gapM, overlapFraction: areaBelow(core, saddle, gapM) / m.overlapAreaM2 })),
      contextMinGapM: c.minimum?.gapM, objective: { quadratureCost, contextPenaltyCost: 0.5 * (2 * Math.min(0, c.minimum?.gapM ?? 0) / 0.001) ** 2 },
      triangles, vertices };
  }
  const contacts = receipt.final.contacts, contactCost = sum([...contacts.gripErrM, ...contacts.soleErrM].map(v => 0.5 * (10 * v / 0.001) ** 2));
  const collisions = Object.fromEntries(['jeansSaddle', 'bodySaddle', 'neighboringJeansBody', 'neighboringJeansSelf'].map(k => [k,
    { baseline: receipt.baselineDiagnostics[k].count, final: receipt.diagnostics[k].count, newPairs: receipt.diagnostics[k].newPairsSinceBaseline.length }]));
  report.bikes.push({ name, receipt: { path: receiptPath, sha256: sha(bytes) }, controls: receipt.controls, sides,
    objective: { savedCost: receipt.fit.cost, contactCost }, collisions,
    history: receipt.fit.history.map(h => ({ iteration: h.iteration, cost: h.cost, accepted: h.accepted, damping: h.damping })) });
}
fs.mkdirSync(path.dirname(out), { recursive: true }); fs.writeFileSync(out, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report.bikes.map(b => ({ name: b.name, sides: Object.fromEntries(Object.entries(b.sides).map(([side, s]) => [side,
  { posedToSourceAreaRatio: s.posedToSourceAreaRatio, gapRangeM: s.gapRangeM, meanGapM: s.meanGapM, normalRanges: s.normalRanges,
    contextMinGapM: s.contextMinGapM, objective: s.objective, gapAreaCdf: s.gapAreaCdf }])), objective: b.objective, collisions: b.collisions })), null, 2));
