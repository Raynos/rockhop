/** Private post-condition repair for the exact welded NEW body/hood rim. */
import type * as THREE from 'three';
export function reconcilePrivateNewRiderClothRim(scene: THREE.Object3D): void {
  const invalid: () => never = () => { throw new Error('Private rim contract mismatch'); };
  const meshes: THREE.SkinnedMesh[] = [];
  scene.traverse(o => {
    const m = o as THREE.SkinnedMesh;
    if (m.isSkinnedMesh && m.name.startsWith('Protected') && !m.name.endsWith('_1')) meshes.push(m);
  });
  if (meshes.length !== 2) invalid();
  const reference = meshes[0]!;
  for (const mesh of meshes) {
    if (mesh.skeleton.bones.length !== 19 || mesh.skeleton.bones.some((b, i) => b.name !== reference.skeleton.bones[i]!.name)) invalid();
    if (!mesh.bindMatrix.equals(reference.bindMatrix) || !mesh.matrixWorld.equals(reference.matrixWorld)) invalid();
    if (mesh.skeleton.boneInverses.some((m, i) => !m.equals(reference.skeleton.boneInverses[i]!))) invalid();
  }
  type Entry = { mesh: THREE.SkinnedMesh; vertex: number };
  const groups = new Map<string, Entry[]>();
  for (const mesh of meshes) {
    const p = mesh.geometry.getAttribute('position');
    for (let vertex = 0; vertex < p.count; vertex++) {
      // Exact source coordinates only. Never join nearby disconnected surfaces.
      const key = [p.getX(vertex), p.getY(vertex), p.getZ(vertex)].join(',');
      const entries = groups.get(key) ?? [];
      entries.push({ mesh, vertex }); groups.set(key, entries);
    }
  }
  let joined = 0;
  for (const entries of groups.values()) {
    if (new Set(entries.map(e => e.mesh)).size !== 2) continue;
    const authority = entries.find(e => e.mesh.name.endsWith('_2'));
    if (!authority) invalid();
    const si = authority.mesh.geometry.getAttribute('skinIndex'), sw = authority.mesh.geometry.getAttribute('skinWeight');
    for (const { mesh, vertex } of entries) {
      const indices = mesh.geometry.getAttribute('skinIndex'), weights = mesh.geometry.getAttribute('skinWeight');
      for (let lane = 0; lane < 4; lane++) {
        indices.setComponent(vertex, lane, si.getComponent(authority.vertex, lane));
        weights.setComponent(vertex, lane, sw.getComponent(authority.vertex, lane));
      }
      indices.needsUpdate = true; weights.needsUpdate = true;
    }
    joined++;
  }
  if (joined !== 307) invalid();
  scene.userData.rockhopPrivateClothRim = { joined };
}
