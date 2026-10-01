/** Private post-condition repair for the exact welded NEW body/hood rim. */
import type * as THREE from 'three';
export function reconcilePrivateNewRiderClothRim(scene: THREE.Object3D): void {
  const invalid = (): never => { throw new Error('Private rim contract mismatch'); };
  const meshes: THREE.SkinnedMesh[] = [];
  scene.traverse(o => {
    const m = o as THREE.SkinnedMesh;
    if (m.isSkinnedMesh && m.name.startsWith('Protected') && !m.name.endsWith('_1')) meshes.push(m);
  });
  if (meshes.length !== 2) invalid();
  const reference = meshes[0]!;
  for (const mesh of meshes) {
    if (mesh.skeleton.bones.length !== 19 || mesh.skeleton.bones.some((b, i) => b.name !== reference.skeleton.bones[i]!.name)) invalid();
    for (const name of ['bindMatrix', 'matrixWorld'] as const) {
      if (mesh[name].elements.some((v, i) => Math.abs(v - reference[name].elements[i]!) > 1e-7)) invalid();
    }
    if (mesh.skeleton.boneInverses.some((m, i) => m.elements.some((v, j) => Math.abs(v - reference.skeleton.boneInverses[i]!.elements[j]!) > 1e-7))) invalid();
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
  let joined = 0, maxDiscardedMass = 0;
  for (const entries of groups.values()) {
    if (new Set(entries.map(e => e.mesh)).size !== 2) continue;
    const accumulated = new Map<number, number>();
    for (const { mesh, vertex } of entries) {
      const indices = mesh.geometry.getAttribute('skinIndex'), weights = mesh.geometry.getAttribute('skinWeight');
      for (let lane = 0; lane < 4; lane++) {
        const joint = indices.getComponent(vertex, lane), w = weights.getComponent(vertex, lane);
        accumulated.set(joint, (accumulated.get(joint) ?? 0) + w / entries.length);
      }
      // Both grip morphs are zero at this sewn cloth rim.
      for (const p of mesh.geometry.morphAttributes.position ?? []) {
        if (Math.hypot(p.getX(vertex), p.getY(vertex), p.getZ(vertex)) > 1e-8) invalid();
      }
    }
    const sorted = [...accumulated].filter(([, w]) => w > 0).sort((a, b) => b[1] - a[1] || a[0] - b[0]);
    const kept = sorted.slice(0, 4), total = kept.reduce((s, [, w]) => s + w, 0);
    if (!(total > 0 && Number.isFinite(total))) invalid();
    maxDiscardedMass = Math.max(maxDiscardedMass, sorted.slice(4).reduce((s, [, w]) => s + w, 0));
    for (const { mesh, vertex } of entries) {
      const indices = mesh.geometry.getAttribute('skinIndex'), weights = mesh.geometry.getAttribute('skinWeight');
      for (let lane = 0; lane < 4; lane++) {
        indices.setComponent(vertex, lane, kept[lane]?.[0] ?? 0);
        weights.setComponent(vertex, lane, kept[lane] ? kept[lane]![1] / total : 0);
      }
      indices.needsUpdate = true; weights.needsUpdate = true;
    }
    joined++;
  }
  if (joined !== 307) invalid();
  scene.userData.rockhopPrivateClothRim = { joined, maxDiscardedMass };
}
