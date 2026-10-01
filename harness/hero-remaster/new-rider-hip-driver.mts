import * as THREE from 'three';
type HipKey = { sample: number; name: string; relativeSkinQuaternions: number[][] };
type HipMetadata = { version: number; keys: HipKey[]; jointNames: string[]; nearestFullRadiusRad: number; nearestZeroRadiusRad: number; epsilonRad: number };
type HipState = { data: HipMetadata; reference: THREE.SkinnedMesh; meshes: THREE.SkinnedMesh[]; joints: number[] };
const privateHipState = new WeakMap<THREE.Object3D, HipState | null>();
export function applyPrivateHipCorrective(scene: THREE.Object3D, enabled: boolean, amplitude: number): void {
  if (!privateHipState.has(scene)) {
    let metadata: string | null = null;
    const meshes: THREE.SkinnedMesh[] = [];
    scene.traverse(o => {
      if (typeof o.userData.rockhopHipCorrective === 'string') metadata = o.userData.rockhopHipCorrective;
      const mesh = o as THREE.SkinnedMesh;
      if (mesh.isSkinnedMesh && mesh.morphTargetDictionary?.['hipCorrective.sample258'] !== undefined) meshes.push(mesh);
    });
    if (!metadata) { privateHipState.set(scene, null); return; }
    const data = JSON.parse(metadata) as HipMetadata;
    if (data.version !== 1 || meshes.length !== 3) throw new Error('Invalid hip mapping');
    const reference = meshes[0]!;
    const joints = data.jointNames.map(n => reference.skeleton.bones.findIndex(b => b.name === n.replace('.','')));
    if (joints.some(i => i < 0) || reference.skeleton.bones.length !== 19) throw new Error('Invalid hip mapping');
    privateHipState.set(scene, { data, reference, meshes, joints });
  }
  const state = privateHipState.get(scene);
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
  const inversePelvis = q[0]!.clone().invert();
  const features = q.slice(1).map(value => inversePelvis.clone().multiply(value).normalize());
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
  scene.userData.privateHipCorrectiveDiagnostic = { nearestRad: nearest, strength, weights };
}
