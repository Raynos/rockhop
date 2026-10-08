/** Proposed cheap post-bone-pose activation. No bike identity or surface query. */
import { Quaternion } from 'three';
export function prepareSeatedCorrective(rider, recipe) {
  const binding = recipe.activation, rest = binding.restRelativeXYZW.map(v => new Quaternion().fromArray(v));
  const key = binding.keyXYZW.map(v => new Quaternion().fromArray(v));
  const meshes = rider.binding.meshes.filter(({ role }) => role === 'RiderJeans' || role === 'RiderBody' || role.startsWith('RiderBody.primitive')).map(({ mesh }) => mesh);
  if (!meshes.length || meshes.some(m => m.morphTargetDictionary?.SelectedSeatedCorrective06 === undefined)) throw new Error('Selected corrective morph is missing');
  return () => {
    rider.scene.updateWorldMatrix(true, true);
    const pelvis = rider.bone(rider.role('pelvis')).getWorldQuaternion(new Quaternion());
    const current = ['Left', 'Right'].map((side, i) => pelvis.clone().invert().multiply(rider.bone(rider.role('thigh' + side)).getWorldQuaternion(new Quaternion())).multiply(rest[i].clone().invert()).normalize());
    const distance = Math.hypot(...current.map((q, i) => q.angleTo(key[i]))), x = distance / binding.radiusRadians;
    const weight = x >= 1 ? 0 : (1 - x) ** 4 * (4 * x + 1);
    for (const mesh of meshes) mesh.morphTargetInfluences[mesh.morphTargetDictionary.SelectedSeatedCorrective06] = weight;
    return weight;
  };
}
