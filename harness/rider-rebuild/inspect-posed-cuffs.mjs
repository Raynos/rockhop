/** Read-only page.evaluate probe for the existing silent actual Garage harness. */
export function inspectActualCuffFragment(options = {}) {
  const debug = window.__render.debug, { THREE, rider } = debug;
  const camera = debug.rig.camera, canvas = debug.renderer.domElement;
  const rect = canvas.getBoundingClientRect(), vec = () => new THREE.Vector3();
  const meshes = rider.binding.meshes.map(row => row.mesh);
  const gloves = meshes.filter(mesh => /^ActualSelectedGlove[LR]/.test(mesh.name));
  const hoodie = meshes.find(mesh => mesh.name === 'RiderHoodie');
  if (gloves.length !== 2 || !hoodie) throw Error('Exact selected parts missing');
  const fields = (mesh, i) => {
    const { skinIndex: joints, skinWeight: weights } = mesh.geometry.attributes;
    return Array.from({ length: 4 }, (_, slot) => ({
      bone: mesh.skeleton.bones[joints.getComponent(i, slot)].name,
      weight: weights.getComponent(i, slot),
    })).filter(row => row.weight > 0);
  };
  const rest = (mesh, i) => vec().fromBufferAttribute(mesh.geometry.attributes.position, i);
  const posed = (mesh, i) => mesh.getVertexPosition(i, vec()).applyMatrix4(mesh.matrixWorld);
  const vertex = (mesh, i) => ({
    index: i, nativeId: mesh.geometry.attributes._native_id?.getX(i) ?? null,
    restLocal: rest(mesh, i).toArray(), posedWorld: posed(mesh, i).toArray(), weights: fields(mesh, i),
  });
  // Cache only the small hoodie; preserve live glove ray hits and source IDs.
  const hoodRest = [], hoodPose = [], hoodIndex = hoodie.geometry.index;
  for (let i = 0; i < hoodie.geometry.attributes.position.count; i++) {
    hoodRest.push(rest(hoodie, i).applyMatrix4(hoodie.matrixWorld));
    hoodPose.push(posed(hoodie, i));
  }
  const closest = (point, points) => {
    let best = null, distanceSq = Infinity;
    const triangle = new THREE.Triangle(), hit = vec(), normal = vec(), bary = vec();
    for (let i = 0; i < hoodIndex.count; i += 3) {
      const ids = [hoodIndex.getX(i), hoodIndex.getX(i + 1), hoodIndex.getX(i + 2)];
      triangle.set(...ids.map(id => points[id]));
      triangle.getNormal(normal);
      if (normal.lengthSq() < .5) continue;
      triangle.closestPointToPoint(point, hit);
      const candidate = point.distanceToSquared(hit);
      if (candidate >= distanceSq) continue;
      distanceSq = candidate; triangle.getBarycoord(hit, bary);
      best = { faceIndex: i / 3, indices: ids, point: hit.toArray(), barycentric: bary.toArray(),
        distanceM: Math.sqrt(candidate), signedNormalDistanceM: point.clone().sub(hit).dot(normal),
        weights: ids.map(id => fields(hoodie, id)) };
    }
    return best;
  };
  const probes = options.pixels ?? [[788, 372], [790, 370], [793, 367], [794, 362], [797, 375]];
  const ray = new THREE.Raycaster();
  const rows = probes.map(([x, y]) => {
    ray.setFromCamera(new THREE.Vector2((x - rect.x) / rect.width * 2 - 1,
      1 - (y - rect.y) / rect.height * 2), camera);
    const hits = ray.intersectObjects([...gloves, hoodie], false);
    return { pixel: [x, y], hits: hits.slice(0, 3).map(hit => {
      const mesh = hit.object, ids = [hit.face.a, hit.face.b, hit.face.c];
      const row = { mesh: mesh.name, distance: hit.distance, pointWorld: hit.point.toArray(),
        faceIndex: hit.faceIndex, vertices: ids.map(i => vertex(mesh, i)) };
      if (gloves.includes(mesh)) {
        const tri = new THREE.Triangle(...ids.map(i => posed(mesh, i)));
        const bary = tri.getBarycoord(hit.point, vec());
        const original = ids.reduce((sum, i, j) => sum.addScaledVector(rest(mesh, i), bary.getComponent(j)), vec());
        row.hitBarycentric = bary.toArray(); row.restLocal = original.toArray();
        row.nearestHoodiePosed = closest(hit.point, hoodPose);
        row.nearestHoodieRest = closest(original.clone().applyMatrix4(mesh.matrixWorld), hoodRest);
      }
      return row;
    }) };
  });
  return { acceptedArt: false, stageTime: window.__render.stageTime,
    sourceSHA256: rider.debug.candidate.sourceSHA256,
    canvas: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
    cameraWorld: camera.matrixWorld.toArray(), cameraProjection: camera.projectionMatrix.toArray(),
    rows, limits: ['Read-only live fragment identity and local nearest surface measurements.',
      'Positive signed normal distance is a local crossing witness, not watertight containment.',
      'The screen pixels target garage06 front at 1440x900; use fresh screenshot if no glove hit.'] };
}
