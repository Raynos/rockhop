/** Observe the unchanged installed skinning path; eight-slot math is reference only. */
import { Vector3, Matrix4, Skeleton } from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
export async function installGarmentObserver(debug, url, contract) {
  const gltf = await new GLTFLoader().loadAsync(url); gltf.scene.updateMatrixWorld(true);
  const meshes = []; gltf.scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
  if (meshes.length !== 1) throw new Error('Frozen garment mesh missing');
  const mesh = meshes[0], skin = mesh.skeleton, attrs = mesh.geometry.attributes;
  if (attrs.position.count !== 7123 || mesh.geometry.index.count !== 35520 || !attrs.joints_1 || !attrs.weights_1) throw new Error('Frozen source14 fields missing');
  const body = debug.rider.sleeveGeometry.find(o => o.mesh.geometry.attributes.position.count === 9981)?.mesh;
  if (!body) throw new Error('Protected actual body missing');
  const byName = new Map(body.skeleton.bones.map((b, i) => [b.name, { bone: b, inverse: body.skeleton.boneInverses[i] }]));
  let maximumInverseBindDifference = 0;
  const bones = skin.bones.map((b, i) => {
    const matched = byName.get(b.name); if (!matched) throw new Error('Original joint identity missing');
    for (let k = 0; k < 16; k++) maximumInverseBindDifference = Math.max(maximumInverseBindDifference, Math.abs(skin.boneInverses[i].elements[k] - matched.inverse.elements[k]));
    return matched.bone;
  });
  if (maximumInverseBindDifference !== 0) throw new Error('Actual protected body bind mismatch');
  const bind = mesh.bindMatrix.clone(); mesh.removeFromParent(); mesh.position.set(0, 0, 0); mesh.quaternion.identity(); mesh.scale.set(1, 1, 1);
  mesh.bindMatrix.copy(bind); mesh.skeleton = new Skeleton(bones, skin.boneInverses.map(m => m.clone())); mesh.frustumCulled = false;
  debug.scene.add(mesh); mesh.updateMatrixWorld(true); mesh.skeleton.update();
  const hidden = [];
  for (const o of debug.rider.sleeveGeometry) if (o.mesh.name.startsWith('Clean_native_hoodie_sewn_neckline_and_fitted_pocket')) { o.mesh.visible = false; hidden.push(o.mesh.name); }
  if (hidden.length !== 2) throw new Error('Old hoodie identity mismatch');
  const rows = contract.secondSetRows.map(x => x.row), representatives = new Map();
  contract.nativeMapping.forEach((id, row) => { if (!representatives.has(id)) representatives.set(id, row); });
  const mats = () => bones.map((b, i) => new Matrix4().copy(mesh.matrixWorld).multiply(mesh.bindMatrixInverse).multiply(b.matrixWorld).multiply(mesh.skeleton.boneInverses[i]).multiply(mesh.bindMatrix));
  const reference = (row, matrices, full) => {
    const pos = new Vector3().fromBufferAttribute(attrs.position, row), result = new Vector3(); let total = 0;
    for (let set = 0; set < (full ? 2 : 1); set++) for (let k = 0; k < 4; k++) {
      const ia = set ? attrs.joints_1 : attrs.skinIndex, wa = set ? attrs.weights_1 : attrs.skinWeight;
      // Reference weights come from independently verified raw GLB accessors,
      // not a reconstruction from rounded, loader-normalized primary slots.
      const w = full ? contract.sourceWeights[row][set * 4 + k] : wa.getComponent(row, k);
      if (w > 0) { result.addScaledVector(pos.clone().applyMatrix4(matrices[ia.getComponent(row, k)]), w); total += w; }
    }
    return full ? result.multiplyScalar(1 / total) : result;
  };
  return { mesh, contract: { rows: 7123, nativeVertices: 6046, maximumInverseBindDifference, hidden,
      attributes: Object.keys(attrs), bind: bind.toArray(), jointOrder: bones.map(b => b.name),
      nativeMapping: contract.nativeMapping, nativeFaces: contract.nativeFaces,
      material: { name: mesh.material.name, type: mesh.material.type, color: mesh.material.color.toArray(), roughness: mesh.material.roughness, metalness: mesh.material.metalness } },
    sample(full = false) {
      mesh.updateMatrixWorld(true); mesh.skeleton.update(); const matrices = mats(), observed = [], expected8 = []; let manual4ResidualM = 0, maximumOmittedWeightDisplacementM = 0, witness = null;
      for (const row of rows) {
        const actual = mesh.getVertexPosition(row, new Vector3()).applyMatrix4(mesh.matrixWorld), four = reference(row, matrices, false), eight = reference(row, matrices, true), gap = actual.distanceTo(eight);
        manual4ResidualM = Math.max(manual4ResidualM, actual.distanceTo(four)); observed.push(...actual.toArray()); expected8.push(...eight.toArray());
        if (gap > maximumOmittedWeightDisplacementM) { maximumOmittedWeightDisplacementM = gap; witness = { row, nativeVertexID: contract.nativeMapping[row], actual4WorldM: actual.toArray(), reference8WorldM: eight.toArray() }; }
      }
      if (manual4ResidualM > 2e-12) throw new Error('Manual primary weights do not reproduce actual CPU skinning');
      return { maximumOmittedWeightDisplacementM, manual4ResidualM, witness, secondaryRows: rows, observed, expected8,
        matrices: matrices.flatMap(m => m.toArray()),
        fullNativePositions: full ? [...representatives.values()].flatMap(row => mesh.getVertexPosition(row, new Vector3()).applyMatrix4(mesh.matrixWorld).toArray()) : null };
    } };
}
