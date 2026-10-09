/** Harness-only exact draw census. Import into an existing SILENT headless run. */
export function captureFrame(render, draw, context) {
  const { renderer, rider } = render.debug;
  if (!renderer || !rider?.root || typeof draw !== 'function') throw Error('Missing complete renderer/rider');
  const original = renderer.renderBufferDirect;
  const rows = [];
  function belongsToRider(object) {
    for (let node = object; node; node = node.parent) if (node === rider.root) return true;
    return false;
  }
  renderer.renderBufferDirect = function (...args) {
    const before = renderer.info.render.triangles;
    const result = original.apply(this, args);
    const triangles = renderer.info.render.triangles - before;
    if (!Number.isSafeInteger(triangles) || triangles < 0) throw Error('Unsupported triangle counter');
    const object = args[4];
    rows.push({ object: object?.name ?? '', uuid: object?.uuid ?? '', rider: belongsToRider(object),
      triangles, geometryTriangles: (args[2]?.index?.count ?? args[2]?.attributes?.position?.count ?? 0) / 3 });
    return result;
  };
  try {
    // Synchronous complete frame only: no async work or unrelated animation can
    // interleave. Each direct draw delta survives renderer.info resets between
    // shadow, color and post passes; instances/groups are counted by Three.
    const result = draw();
    if (result && typeof result.then === 'function') throw Error('Census draw must be synchronous');
  } finally {
    renderer.renderBufferDirect = original;
  }
  if (!rows.some(row => row.rider && row.triangles > 0)) throw Error('No actual rider draw; stale/skipped/empty frame');
  const total = rows.reduce((n, row) => n + row.triangles, 0);
  const riderDrawTriangles = rows.filter(row => row.rider).reduce((n, row) => n + row.triangles, 0);
  return { ...context, completeSceneDrawTriangles: total, riderDrawTriangles,
    nonRiderDrawTriangles: total - riderDrawTriangles, drawRows: rows, acceptedArt: false,
    limits: 'Actual sampled complete frame only. No future pose, camera, streaming, texture, timing or device proof.' };
}
