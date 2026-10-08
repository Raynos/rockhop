/** Read-only identity correction: include every visible scene mesh, not only garments. */
export function identifyActualWristFragment() {
  const { THREE, scene, renderer, rig } = window.__render.debug;
  const camera = rig.camera, rect = renderer.domElement.getBoundingClientRect();
  const meshes = []; scene.traverseVisible(node => { if (node.isMesh) meshes.push(node); });
  const ray = new THREE.Raycaster(); ray.layers.mask = camera.layers.mask;
  const pixels = [[790, 370], [793, 367], [794, 362]];
  const rows = pixels.map(([x, y]) => {
    ray.setFromCamera(new THREE.Vector2((x - rect.x) / rect.width * 2 - 1,
      1 - (y - rect.y) / rect.height * 2), camera);
    // Animated SkinnedMesh bounds can predate this pose. Bypass only glove
    // broadphase; installed Three's triangle path still uses current skinning.
    const gloves = meshes.filter(mesh => /^ActualSelectedGlove[LR]/.test(mesh.name));
    const hits = ray.intersectObjects(meshes.filter(mesh => !gloves.includes(mesh)), false);
    for (const mesh of gloves) {
      const localRay = ray.ray.clone().applyMatrix4(mesh.matrixWorld.clone().invert());
      mesh._computeIntersections(ray, hits, localRay);
    }
    hits.sort((a, b) => a.distance-b.distance);
    return { pixel: [x, y], hits: hits.slice(0, 3).map(hit => {
      const mesh = hit.object, attrs = mesh.geometry.attributes, lineage = [];
      for (let node = mesh; node; node = node.parent) lineage.push(node.name || node.type);
      const material = Array.isArray(mesh.material) ? mesh.material[hit.face.materialIndex] : mesh.material;
      return { mesh: mesh.name, lineage, faceIndex: hit.faceIndex, distance: hit.distance,
        pointWorld: hit.point.toArray(), uv: hit.uv?.toArray(),
        material: { name: material.name, color: material.color?.toArray(), map: material.map?.name },
        vertices: [hit.face.a, hit.face.b, hit.face.c].map(i => ({ index: i,
          nativeId: attrs._native_id?.getX(i) ?? null,
          restLocal: new THREE.Vector3().fromBufferAttribute(attrs.position, i).toArray(),
          posedWorld: mesh.getVertexPosition(i, new THREE.Vector3()).applyMatrix4(mesh.matrixWorld).toArray(),
          weights: !mesh.isSkinnedMesh ? [] : Array.from({ length: 4 }, (_, slot) => ({
            bone: mesh.skeleton.bones[attrs.skinIndex.getComponent(i, slot)].name,
            weight: attrs.skinWeight.getComponent(i, slot),
          })).filter(row => row.weight > 0),
        })) };
    }), gloveBounds: meshes.filter(mesh => /^ActualSelectedGlove[LR]/.test(mesh.name)).map(mesh => ({
      name: mesh.name, sphereWasComputed: !!mesh.boundingSphere,
      rayIntersectsCurrentSphere: !mesh.boundingSphere ? null : ray.ray.intersectsSphere(
        mesh.boundingSphere.clone().applyMatrix4(mesh.matrixWorld)),
      hasBoundingBox: !!mesh.boundingBox,
    })) };
  });
  return { acceptedArt: false, stageTime: window.__render.stageTime, visibleMeshes: meshes.length,
    cameraWorld: camera.matrixWorld.toArray(), rows,
    skinFrames: meshes.filter(mesh => /^(ActualSelectedGlove[LR]|RiderHoodie)$/.test(mesh.name)).map(mesh => ({
      name: mesh.name, matrixWorld: mesh.matrixWorld.toArray(), bindMatrix: mesh.bindMatrix.toArray(),
      bindMatrixInverse: mesh.bindMatrixInverse.toArray(), bones: mesh.skeleton.bones.map((bone, i) => ({
        name: bone.name, skinMatrix: bone.matrixWorld.clone().multiply(mesh.skeleton.boneInverses[i]).toArray(),
      })),
    })),
    limits: ['Synchronous source identity only; no posed/rest clearance or moving-art acceptance.'] };
}
