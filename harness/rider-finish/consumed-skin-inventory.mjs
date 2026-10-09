/** Prepared inspector for the actual rendered GltfRider/SkinnedMesh tree.
 * No loader, pose driver, shader, geometry writer or acceptance threshold.
 * Call after actual headless-engine draw with an independently pinned mapping.
 */
// Browser-compatible: bundle into the existing private headless game harness.
const assert = Object.assign((condition, message = 'Consumed skin contract failed') => {
  if (!condition) throw new Error(message);
}, {
  equal(actual, expected, message) { assert(actual === expected, message); },
  deepEqual(actual, expected, message) { assert(JSON.stringify(actual) === JSON.stringify(expected), message); },
});

const semanticRows = (mesh, row, semanticByLoaded, jointCount) => {
  const indices = mesh.geometry.getAttribute('skinIndex');
  const weights = mesh.geometry.getAttribute('skinWeight');
  const fields = new Float64Array(jointCount);
  let sum = 0;
  for (let slot = 0; slot < 4; slot++) {
    const index = indices.getComponent(row, slot), weight = weights.getComponent(row, slot);
    assert(Number.isInteger(index) && index >= 0 && index < mesh.skeleton.bones.length);
    assert(Number.isFinite(weight) && weight >= 0);
    const loaded = mesh.skeleton.bones[index].name;
    const semanticIndex = semanticByLoaded.get(loaded);
    assert(semanticIndex !== undefined, `Unknown consumed joint ${loaded}`);
    fields[semanticIndex] += weight;
    sum += weight;
  }
  return { fields, sum };
};

export function inventoryConsumedSkin(scene, contract) {
  assert(scene?.traverse && contract.joints.length === 51 && contract.regions.length);
  const semantics = contract.joints.map(joint => joint.semanticName);
  const loadedNames = contract.joints.map(joint => joint.loadedName);
  const semanticByLoaded = new Map(loadedNames.map((name, i) => [name, i]));
  assert.equal(new Set(semantics).size, 51);
  assert.equal(new Set(loadedNames).size, 51, 'Sanitized loader names must not collide');
  const regionMap = new Map(contract.regions.map(region => [region.id, region]));
  assert.equal(regionMap.size, contract.regions.length);
  const consumed = new Map(contract.regions.map(region => [region.id, { rows: 0, vertices: new Set(), corners: new Set(), maximumNamedNormalizedFourFieldDifference: 0 }]));
  const meshes = [], bones = [];
  scene.traverse(object => {
    if (object.isBone) bones.push(object.name);
    if (!object.isSkinnedMesh) return;
    const geometry = object.geometry;
    const position = geometry.getAttribute('position');
    const normal = geometry.getAttribute('normal');
    const native = geometry.getAttribute('_native_id');
    const corner = geometry.getAttribute('_corner_id');
    const region = geometry.getAttribute('_region_id');
    const weights = geometry.getAttribute('skinWeight');
    const indices = geometry.getAttribute('skinIndex');
    assert(position && normal && native && corner && region && weights && indices,
      'Every consumed part requires region/native/corner identity, normals and four-slot skin');
    for (const attribute of [normal, native, corner, region, weights, indices]) assert.equal(attribute.count, position.count);
    assert.equal(weights.itemSize, 4); assert.equal(indices.itemSize, 4);
    assert.equal(native.itemSize, 1); assert.equal(corner.itemSize, 1); assert.equal(region.itemSize, 1);
    assert(!native.normalized && !corner.normalized && !region.normalized);
    assert.deepEqual(object.skeleton.bones.map(bone => bone.name).sort((a, b) => a < b ? -1 : a > b ? 1 : 0), [...loadedNames].sort((a, b) => a < b ? -1 : a > b ? 1 : 0));
    let normalizedSumMaximumDelta = 0;
    for (let row = 0; row < position.count; row++) {
      const rid = region.getX(row), vid = native.getX(row), cid = corner.getX(row);
      assert(Number.isInteger(rid) && Number.isInteger(vid) && Number.isInteger(cid));
      const authority = regionMap.get(rid); assert(authority, `Unknown consumed region ${rid}`);
      assert(vid >= 0 && vid < authority.nativeVertexCount && cid >= 0 && cid < authority.cornerVertexIDs.length);
      assert.equal(authority.cornerVertexIDs[cid], vid, 'Actual exported corner identity must resolve to its native point');
      const result = consumed.get(rid);
      result.rows++; result.vertices.add(vid); result.corners.add(cid);
      const actual = semanticRows(object, row, semanticByLoaded, semantics.length);
      normalizedSumMaximumDelta = Math.max(normalizedSumMaximumDelta, Math.abs(actual.sum - 1));
      for (let j = 0; j < semantics.length; j++) {
        result.maximumNamedNormalizedFourFieldDifference = Math.max(result.maximumNamedNormalizedFourFieldDifference,
          Math.abs(actual.fields[j] - authority.normalizedFourWeights[vid][j]));
      }
    }
    let skinOwner = null;
    for (let ancestor = object; ancestor; ancestor = ancestor.parent) {
      if (!Object.hasOwn(ancestor.userData, 'rockhopRiderSkinConditioned')) continue;
      skinOwner = { name: ancestor.name, value: ancestor.userData.rockhopRiderSkinConditioned };
      break;
    }
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    meshes.push({ name: object.name, actualSkinnedMesh: true, rows: position.count,
      triangles: (geometry.index?.count ?? position.count) / 3,
      bindMatrix: [...object.bindMatrix.elements], bindMatrixInverse: [...object.bindMatrixInverse.elements],
      joints: object.skeleton.bones.map((bone, i) => ({ loadedName: bone.name, inverseBind: [...object.skeleton.boneInverses[i].elements] })),
      normalizedSumMaximumDelta, nearestAuthoredSkinOwner: skinOwner,
      materials: materials.map(material => ({ name: material.name, type: material.type,
        maps: ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap'].flatMap(key => material[key]
          ? [{ key, name: material[key].name, dimensions: [material[key].image?.width, material[key].image?.height] }] : []) })),
      compiledNormalRoute: 'UNMEASURED; rendered shader source/readback required' });
  });
  assert.deepEqual(bones.sort((a, b) => a < b ? -1 : a > b ? 1 : 0), [...loadedNames].sort((a, b) => a < b ? -1 : a > b ? 1 : 0), 'Actual cloned rig must expose all51 unique declared joints');
  assert(meshes.length, 'No consumed candidate skinned meshes');
  const regions = contract.regions.map(region => {
    const actual = consumed.get(region.id);
    assert(actual.rows, `Missing consumed region ${region.name}`);
    const missingVertices = region.usedNativeVertexIDs.filter(id => !actual.vertices.has(id));
    const missingCorners = region.requiredCornerIDs.filter(id => !actual.corners.has(id));
    return { region: region.name, id: region.id, rows: actual.rows,
      usedNativeVertices: region.usedNativeVertexIDs.length, coveredNativeVertices: actual.vertices.size,
      sourceUnusedVertices: region.nativeVertexCount - region.usedNativeVertexIDs.length,
      missingUsedNativeVertexIDs: missingVertices, missingRequiredCornerIDs: missingCorners,
      maximumNamedNormalizedFourFieldDifference: actual.maximumNamedNormalizedFourFieldDifference };
  });
  return { status: 'UNACCEPTED_ACTUAL_RENDER_TREE_SKIN_INVENTORY', meshes, regions,
    limits: ['Read-only actual post-draw tree inventory; no loader/pose/material/shader/geometry mutation.',
      'Region/native/corner coverage and named fields do not prove triangle orientation, inverse-bind parity, GPU normals, played quality or device cost.',
      'Unused native points remain explicit; they are not silently required as rendered triangles.',
      'No threshold relaxation, missing part exemption or nearest-coordinate correspondence.'] };
}
