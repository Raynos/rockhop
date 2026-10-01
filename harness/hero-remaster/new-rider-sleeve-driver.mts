import * as THREE from 'three';
type SleeveKey = { sample: number; name: string; relativeSkinQuaternions: number[][] };
type SleeveMetadata = { version: number; keys: SleeveKey[]; jointNames: string[]; nearestFullRadiusRad: number; nearestZeroRadiusRad: number; epsilonRad: number };
type SleeveState = { data: SleeveMetadata; reference: THREE.SkinnedMesh; meshes: THREE.SkinnedMesh[]; joints: number[] };
const privateSleeveState = new WeakMap<THREE.Object3D, SleeveState | null>();
export function applyPrivateSleeveCorrective(scene: THREE.Object3D, enabled: boolean, amplitude: number): void {
  if (!privateSleeveState.has(scene)) {
    let metadata: string | null = null;
    const meshes: THREE.SkinnedMesh[] = [];
    scene.traverse(o => {
      if (typeof o.userData.rockhopSleeveCorrective === 'string') metadata = o.userData.rockhopSleeveCorrective;
      const mesh = o as THREE.SkinnedMesh;
      if (mesh.isSkinnedMesh && mesh.morphTargetDictionary?.['sleeveCorrective.sample114'] !== undefined) meshes.push(mesh);
    });
    if (!metadata) { privateSleeveState.set(scene, null); return; }
    const data = JSON.parse(metadata) as SleeveMetadata;
    if (data.version !== 1 || meshes.length !== 3) throw new Error('Invalid sleeve mapping');
    const reference = meshes[0]!;
    const joints = data.jointNames.map(n => reference.skeleton.bones.findIndex(b => b.name === n.replace('.','')));
    if (joints.some(i => i < 0) || reference.skeleton.bones.length !== 19) throw new Error('Invalid sleeve mapping');
    privateSleeveState.set(scene, { data, reference, meshes, joints });
  }
  const state = privateSleeveState.get(scene);
  if (!state) return;
  const { data, reference, meshes, joints } = state;
  // Update transforms only. No bone position, quaternion or target is changed.
  scene.updateWorldMatrix(true, true);
  const q = joints.map(j => {
    const matrix = reference.skeleton.bones[j]!.matrixWorld.clone()
      .multiply(reference.skeleton.boneInverses[j]!).multiply(reference.bindMatrix);
    const result = new THREE.Quaternion();
    matrix.decompose(new THREE.Vector3(), result, new THREE.Vector3());
    return result.normalize();
  });
  const inverseChest = q[0]!.clone().invert();
  const features = q.slice(1).map(value => inverseChest.clone().multiply(value).normalize());
  const distances = data.keys.map(key => Math.sqrt(features.reduce((sum, feature, i) => {
    const angle = feature.angleTo(new THREE.Quaternion().fromArray(key.relativeSkinQuaternions[i]!));
    return sum + angle * angle;
  }, 0)));
  const nearest = Math.min(...distances);
  const t = THREE.MathUtils.clamp((nearest - data.nearestFullRadiusRad) / (data.nearestZeroRadiusRad - data.nearestFullRadiusRad), 0, 1);
  const strength = enabled ? (1 - t*t*(3-2*t)) * THREE.MathUtils.clamp(amplitude,0,1) : 0;
  const radial = distances.map(d => 1 / (d*d + data.epsilonRad*data.epsilonRad));
  const total = radial.reduce((a,b) => a+b,0), weights = radial.map(w => w/total*strength);
  for (const mesh of meshes) {
    for (const [i,key] of data.keys.entries()) {
      const index = mesh.morphTargetDictionary?.[key.name];
      mesh.morphTargetInfluences![index!] = weights[i]!;
    }
  }
  scene.userData.privateSleeveCorrectiveDiagnostic = { nearestRad: nearest, strength, weights };
}
