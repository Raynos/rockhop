/** Pose-local activation with scratch storage prepared once for each rider. */
import { Quaternion, Vector3 } from 'three';

export function prepareSeatedCorrective(rider, recipe) {
  const binding = recipe.activation;
  const pelvis = rider.bone(rider.role('pelvis'));
  const thighs = ['Left', 'Right'].map(side => rider.bone(rider.role('thigh' + side)));
  const inverseRest = binding.restRelativeXYZW.map(q => new Quaternion().fromArray(q).invert());
  const key = binding.keyXYZW.map(q => new Quaternion().fromArray(q));
  const targets = rider.binding.meshes.filter(({ role }) => role === 'RiderJeans' || role === 'RiderBody' || role.startsWith('RiderBody.primitive'))
    .map(({ mesh }) => [mesh, mesh.morphTargetDictionary?.SelectedSeatedCorrective06]);
  if (!targets.length || targets.some(([, index]) => index === undefined)) throw new Error('Selected corrective morph is missing');
  const inversePelvis = new Quaternion(), flex = new Quaternion();
  const position = new Vector3(), scale = new Vector3();
  // The real rider passes true immediately after its full world-matrix update.
  // Standalone callers omit the flag and receive the same fresh-pose guarantee.
  return (worldMatricesCurrent = false) => {
    if (!worldMatricesCurrent) rider.scene.updateWorldMatrix(true, true);
    pelvis.matrixWorld.decompose(position, inversePelvis, scale); inversePelvis.invert();
    let distanceSquared = 0;
    for (let i = 0; i < thighs.length; i++) {
      thighs[i].matrixWorld.decompose(position, flex, scale);
      flex.premultiply(inversePelvis).multiply(inverseRest[i]).normalize();
      distanceSquared += flex.angleTo(key[i]) ** 2;
    }
    const x = Math.sqrt(distanceSquared) / binding.radiusRadians;
    const weight = x >= 1 ? 0 : (1 - x) ** 4 * (4 * x + 1);
    for (let i = 0; i < targets.length; i++) targets[i][0].morphTargetInfluences[targets[i][1]] = weight;
    return weight;
  };
}
