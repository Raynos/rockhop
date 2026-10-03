/** Private consumed current outsole offset and actual skinned arch measurement. */
export function installConstructedSoleTarget(debug, enabled) {
  const rider = debug.rider, T = debug.THREE, frame = debug.bike.frame;
  if (!rider.debug.physicalPose) throw new Error('Actual physical pose required');
  rider.scene.updateMatrixWorld(true);
  const offsets = ['L', 'R'].map(side => {
    const foot = rider.scene.getObjectByName('foot' + side), marker = rider.scene.getObjectByName('soleSocket' + side);
    if (!foot || !marker || marker.parent !== foot) throw new Error('Current foot-child socket absent');
    return frame.worldToLocal(marker.getWorldPosition(new T.Vector3())).sub(frame.worldToLocal(foot.getWorldPosition(new T.Vector3())));
  });
  const original = rider.solveLeg; if (typeof original !== 'function') throw new Error('Leg hook absent');
  let calls = 0;
  if (enabled) rider.solveLeg = function (chain, side) {
    const old = chain.ankle[side].clone();
    chain.ankle[side].set(-.14, .031, side === 0 ? .2 : -.2).sub(offsets[side]);
    try { original.call(this, chain, side); calls++; } finally { chain.ankle[side].copy(old); }
  };
  return { enabled, offsets: offsets.map(v => v.toArray()), get calls() { return calls; }, restore() { rider.solveLeg = original; } };
}

export function makeConstructedSoleMeasurement(debug, inventory) {
  const T = debug.THREE, rider = debug.rider, frame = debug.bike.frame;
  const meshes = []; rider.scene.traverse(o => { if (o.isSkinnedMesh && o.geometry.attributes.position.count === 466 && o.geometry.index.count === 984) meshes.push(o); });
  if (meshes.length !== 1) throw new Error('Current actual outsole primitive ambiguous');
  const mesh = meshes[0], source = mesh.geometry.attributes, relevantRows = new Set();
  for (const side of ['L', 'R']) for (const id of inventory.sides[side].proposedArchTriangleIDs) {
    const row = inventory.triangles[id];
    row.exportedRows.forEach((r, k) => { if (mesh.geometry.index.getX(id * 3 + k) !== r) throw new Error('Source triangle topology changed'); relevantRows.add(r); });
  }
  let maximumSourcePositionResidualM = 0, maximumSourceWeightError = 0;
  for (const row of inventory.rows) {
    const i = row.exportedRow, p = new T.Vector3().fromBufferAttribute(source.position, i);
    maximumSourcePositionResidualM = Math.max(maximumSourcePositionResidualM, p.distanceTo(new T.Vector3(...row.restFileWorldM)));
    const weights = {};
    for (let k = 0; k < 4; k++) { const w = source.skinWeight.getComponent(i, k); if (w > 0) { const name = mesh.skeleton.bones[source.skinIndex.getComponent(i, k)].name; weights[name] = (weights[name] ?? 0) + w; } }
    for (const name of new Set([...Object.keys(weights), ...Object.keys(row.actualLoaderNormalizedWeights)])) maximumSourceWeightError = Math.max(maximumSourceWeightError, Math.abs((weights[name] ?? 0) - (row.actualLoaderNormalizedWeights[name] ?? 0)));
  }
  if (maximumSourcePositionResidualM > 1e-12 || maximumSourceWeightError > 1e-7) throw new Error('Actual source fields differ');
  return { contract: { rows: 466, triangles: 328, actualArchRowsRead: relevantRows.size, maximumSourcePositionResidualM, maximumSourceWeightError,
    limits: ['Consumes actual current09 skinned rubber triangles; arch region remains a proposed load-bearing patch.', 'CPU diagnostic readback only; no GPU, phone performance or shape judgment.'] },
    sample() {
      const started = performance.now(); rider.scene.updateMatrixWorld(true); mesh.skeleton.update();
      const positions = new Map([...relevantRows].map(id => [id, mesh.getVertexPosition(id, new T.Vector3()).applyMatrix4(mesh.matrixWorld)]));
      const sides = ['L', 'R'].map(side => {
        const peg = frame.localToWorld(new T.Vector3(-.14, .031, side === 'L' ? .2 : -.2));
        const marker = rider.scene.getObjectByName('soleSocket' + side).getWorldPosition(new T.Vector3());
        const center = new T.Vector3(), normal = new T.Vector3(); let area = 0, closestDistanceM = Infinity;
        const triangles = inventory.sides[side].proposedArchTriangleIDs.map(id => {
          const points = inventory.triangles[id].exportedRows.map(i => positions.get(i));
          const cross = points[1].clone().sub(points[0]).cross(points[2].clone().sub(points[0])), a = cross.length() / 2;
          if (!(a > 1e-12)) throw new Error('Arch triangle degenerate');
          area += a; center.addScaledVector(points[0].clone().add(points[1]).add(points[2]).multiplyScalar(1 / 3), a); normal.add(cross);
          const closest = new T.Triangle(...points).closestPointToPoint(peg, new T.Vector3()); closestDistanceM = Math.min(closestDistanceM, closest.distanceTo(peg));
          return { exportedTriangleID: id, worldPointsM: points.map(p => p.toArray()), areaM2: a };
        });
        center.multiplyScalar(1 / area); normal.normalize();
        return { side, actualAreaM2: area, actualWorldCenterM: center.toArray(), actualWorldNormal: normal.toArray(), markerWorldM: marker.toArray(), pegWorldM: peg.toArray(),
          centerToMarkerM: center.distanceTo(marker), centerToPegM: center.distanceTo(peg), markerToPegM: marker.distanceTo(peg), pegToActualFiniteArchM: closestDistanceM, triangles };
      });
      return { sides, readbackCpuMs: performance.now() - started };
    } };
}
