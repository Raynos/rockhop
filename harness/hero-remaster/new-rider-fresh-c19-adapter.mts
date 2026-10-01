/** Private freshC19axis adapter only; production posing/physics remain unchanged. */
import assert from 'node:assert/strict';
import { patchNewRiderSource } from './new-rider-private-adapter.mjs';

export function patchFreshC19Source(original: string): string {
  let source = patchNewRiderSource(original, true, false);
  const prefix = '    this.scene.traverse((o) => {\n      if ((o as THREE.Bone).isBone) this.bones.set(boneName(o.name), o as THREE.Bone);\n    });\n';
  const anchor = prefix + '    for (const name of ORDER) {\n      const b = this.bones.get(name);';
  assert.equal(source.split(anchor).length - 1, 1);
  source = source.replace(anchor, prefix + `    let freshC19Axes = false;
    this.scene.traverse(o => { if (o.userData.rockhopFreshC19RestAxes === 'WORLD_ALIGNED_EXPLICIT_CHILD_DIRECTIONS') freshC19Axes = true; });
    const anatomicalChildren: Record<string, string> = {
      pelvis: 'spine', spine: 'chest', chest: 'neck', neck: 'head',
      'shoulder.L': 'upperArm.L', 'upperArm.L': 'forearm.L', 'forearm.L': 'hand.L',
      'shoulder.R': 'upperArm.R', 'upperArm.R': 'forearm.R', 'forearm.R': 'hand.R',
      'thigh.L': 'shin.L', 'shin.L': 'foot.L', 'thigh.R': 'shin.R', 'shin.R': 'foot.R',
    };
    for (const name of ORDER) {
      const b = this.bones.get(name);`);
  const axis = '      this.d0.set(name, new THREE.Vector3(0, 1, 0).applyQuaternion(q).normalize());';
  assert.equal(source.split(axis).length - 1, 1);
  source = source.replace(axis, `      const restDirection = new THREE.Vector3(0, 1, 0).applyQuaternion(q).normalize();
      if (freshC19Axes && anatomicalChildren[name]) {
        const child = this.bones.get(anatomicalChildren[name]!);
        if (!child) throw new Error('FreshC19 anatomical child missing: ' + name);
        restDirection.copy(child.getWorldPosition(new THREE.Vector3())).sub(b.getWorldPosition(new THREE.Vector3()));
        if (restDirection.lengthSq() < 1e-10) throw new Error('FreshC19 rest axis collapsed: ' + name);
        restDirection.normalize();
      }
      this.d0.set(name, restDirection);`);
  return source;
}
