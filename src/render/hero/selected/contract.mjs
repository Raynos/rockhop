/** Private intake helpers, independent of legacy names/counts and player code.
 * Capture only in the loaded rest pose, from explicit author semantic mappings.
 * These functions establish transport/control contracts, not anatomy or contact.
 */
import { Matrix4, Quaternion, Vector3 } from 'three';

const require = (condition, message) => {
  if (!condition) throw new Error(`Humanoid contract: ${message}`);
};
const finite = (values, length) => Array.isArray(values) && values.length === length && values.every(Number.isFinite);
const clone = value => JSON.parse(JSON.stringify(value));
const ancestor = (child, parent) => {
  for (let node = child.parent; node; node = node.parent) if (node === parent) return true;
  return false;
};
const nearestBone = node => {
  for (let parent = node.parent; parent; parent = parent.parent) if (parent.isBone) return parent;
  return null;
};
const pose = bone => ({ translation: bone.position.toArray(), rotationXYZW: bone.quaternion.toArray(), scale: bone.scale.toArray() });
const validPose = value => finite(value?.translation, 3) && finite(value?.rotationXYZW, 4) && finite(value?.scale, 3)
  && value.scale.every(x => x > 0) && Math.abs(value.rotationXYZW.reduce((sum, x) => sum + x * x, 0) - 1) < 1e-5;
const close = (a, b) => a.length === b.length && a.every((x, i) => Math.abs(x - b[i]) < 1e-9);

function inventory(root, spec) {
  require(root?.traverse && spec.units === 'metres' && spec.frame === 'gltf-y-up', 'Declare metre/Y-up file frame');
  const names = new Map(), bones = [], skins = [];
  root.traverse(node => {
    const list = names.get(node.name) ?? []; list.push(node); names.set(node.name, list);
    if (node.isBone) bones.push(node);
    if (node.isSkinnedMesh) skins.push(node);
  });
  const exact = name => {
    require(typeof name === 'string' && names.get(name)?.length === 1, `Ambiguous/missing exact node ${name}`);
    return names.get(name)[0];
  };
  const byId = new Map(Object.entries(spec.jointNames ?? {}).map(([id, name]) => [id, exact(name)]));
  require(byId.size > 0 && byId.size === bones.length && new Set(byId.values()).size === bones.length,
    'Declare every actual joint once, including intermediate/twist/finger joints');
  require([...byId.values()].every(node => node.isBone), 'Joint mapping must resolve actual Bones');
  const idByBone = new Map([...byId].map(([id, bone]) => [bone, id]));
  for (const ids of Object.values(spec.roles ?? {})) {
    require((Array.isArray(ids) ? ids : [ids]).every(id => byId.has(id)), 'Unknown explicit semantic role joint');
  }
  const meshes = Object.entries(spec.meshNames ?? {}).map(([role, name]) => ({ role, mesh: exact(name) }));
  require(meshes.length && meshes.every(row => row.mesh.isSkinnedMesh)
    && new Set(meshes.map(row => row.mesh)).size === skins.length && meshes.length === skins.length,
  'Declare every skinned part once, including body/gloves/garments');
  const inverses = new Map();
  for (const { mesh } of meshes) {
    require(mesh.skeleton.bones.length === bones.length && new Set(mesh.skeleton.bones).size === bones.length
      && mesh.skeleton.bones.every(bone => idByBone.has(bone)), 'Every part must share the actual joint objects');
    require(mesh.skeleton.boneInverses.length === bones.length, 'Missing inverse binds');
    mesh.skeleton.bones.forEach((bone, index) => {
      const matrix = mesh.skeleton.boneInverses[index].elements;
      require(matrix.every(Number.isFinite), 'Nonfinite inverse bind');
      if (inverses.has(bone)) require(matrix.every((x, k) => x === inverses.get(bone)[k]), 'Part inverse binds disagree');
      else inverses.set(bone, [...matrix]);
    });
  }
  const depth = bone => { let n = 0; for (let p = bone.parent; p; p = p.parent) n++; return n; };
  const order = [...byId].sort((a, b) => depth(a[1]) - depth(b[1]));
  return { root, exact, byId, idByBone, meshes, inverses, order };
}

function handFrame(binding, hand) {
  const wrist = binding.byId.get(hand.wristJointId);
  require(wrist, 'Unknown wrist joint');
  const socket = binding.exact(hand.socketNodeName);
  require(ancestor(socket, wrist) && nearestBone(socket) === wrist, 'Palm socket must be rigid under its wrist');
  require(Object.keys(hand.digits ?? {}).sort().join(',') === 'index,middle,pinky,ring,thumb', 'Declare all five digit chains');
  const used = new Set();
  for (const chain of Object.values(hand.digits)) {
    require(Array.isArray(chain) && chain.length, 'Empty digit chain');
    let parent = wrist;
    for (const id of chain) {
      const bone = binding.byId.get(id);
      require(bone && !used.has(id) && ancestor(bone, parent), 'Invalid/shared/nonhierarchical digit joint');
      used.add(id); parent = bone;
    }
  }
  require(hand.normalSign === 1 || hand.normalSign === -1, 'Declare outward palm normal sign');
  wrist.updateWorldMatrix(true, true);
  const inverse = wrist.matrixWorld.clone().invert();
  const landmark = id => {
    const bone = binding.byId.get(id);
    require(bone && ancestor(bone, wrist), 'Palm landmark must be explicitly mapped under wrist');
    return bone.getWorldPosition(new Vector3()).applyMatrix4(inverse);
  };
  const forward = landmark(hand.forwardJointId);
  const radial = landmark(hand.radialJointId).sub(landmark(hand.ulnarJointId));
  require(forward.lengthSq() > 1e-12 && radial.lengthSq() > 1e-12, 'Coincident palm landmarks');
  forward.normalize(); radial.addScaledVector(forward, -radial.dot(forward));
  require(radial.lengthSq() > 1e-12, 'Collinear palm landmarks'); radial.normalize();
  const normal = new Vector3().crossVectors(forward, radial).multiplyScalar(hand.normalSign);
  return { socketInWrist: inverse.multiply(socket.matrixWorld).toArray(),
    axesInWrist: { forward: forward.toArray(), radial: radial.toArray(), normal: normal.toArray() } };
}

/** Semantic names/landmarks are supplied by the author, never guessed from names/XYZ. */
export function captureHumanoidContract(root, specification) {
  const spec = clone(specification), binding = inventory(root, spec);
  root.updateWorldMatrix(true, true);
  const joints = binding.order.map(([id, bone]) => {
    const restLocal = pose(bone); require(validPose(restLocal), `Invalid rest TRS ${id}`);
    return { id, nodeName: bone.name, parentJointId: binding.idByBone.get(nearestBone(bone)) ?? null,
      immediateParentName: bone.parent?.name ?? null, restLocal, inverseBind: binding.inverses.get(bone) };
  });
  const hands = Object.fromEntries(Object.entries(spec.hands ?? {}).map(([side, hand]) => [side, { ...hand, ...handFrame(binding, hand) }]));
  return { schema: 'rockhop-humanoid-contract-v1', ...spec, jointCount: joints.length, joints, hands,
    meshes: binding.meshes.map(({ role, mesh }) => ({ role, nodeName: mesh.name,
      bindMatrix: mesh.bindMatrix.toArray(), bindMatrixInverse: mesh.bindMatrixInverse.toArray() })) };
}

/** Bind a loaded REST instance; a posed or differently calibrated asset is rejected. */
export function bindHumanoidContract(root, input) {
  const contract = clone(input);
  require(contract.schema === 'rockhop-humanoid-contract-v1', 'Unknown schema');
  const binding = inventory(root, contract);
  require(contract.joints?.length === binding.order.length && contract.jointCount === binding.order.length, 'Joint count changed');
  const rests = new Map();
  for (const row of contract.joints) {
    const bone = binding.byId.get(row.id);
    require(bone && !rests.has(row.id) && row.nodeName === bone.name && validPose(row.restLocal), 'Invalid rest identity/TRS');
    const loaded = pose(bone);
    require(Object.keys(loaded).every(key => close(loaded[key], row.restLocal[key])), 'Loaded joint is not the declared source rest');
    require(row.parentJointId === (binding.idByBone.get(nearestBone(bone)) ?? null)
      && row.immediateParentName === (bone.parent?.name ?? null), 'Actual parent hierarchy changed');
    require(finite(row.inverseBind, 16) && row.inverseBind.every((x, k) => x === binding.inverses.get(bone)[k]), 'Source inverse bind changed');
    rests.set(row.id, row.restLocal);
  }
  for (const { role, mesh } of binding.meshes) {
    const row = contract.meshes?.find(item => item.role === role && item.nodeName === mesh.name);
    require(row && finite(row.bindMatrix, 16) && finite(row.bindMatrixInverse, 16)
      && row.bindMatrix.every((x, k) => x === mesh.bindMatrix.elements[k])
      && row.bindMatrixInverse.every((x, k) => x === mesh.bindMatrixInverse.elements[k]), 'Part bind matrix changed');
  }
  for (const hand of Object.values(contract.hands)) {
    const calibrated = handFrame(binding, hand);
    require(finite(hand.socketInWrist, 16) && Math.abs(new Matrix4().fromArray(hand.socketInWrist).determinant()) > 1e-12,
      'Invalid serialized socket frame');
    for (const axis of Object.values(hand.axesInWrist ?? {})) require(finite(axis, 3), 'Invalid serialized palm axis');
    require(Object.keys(hand.axesInWrist ?? {}).sort().join(',') === 'forward,normal,radial', 'Missing calibrated palm axes');
    require(close(calibrated.socketInWrist, hand.socketInWrist)
      && Object.keys(calibrated.axesInWrist).every(key => close(calibrated.axesInWrist[key], hand.axesInWrist[key])),
    'Source palm socket or anatomical calibration changed');
  }
  return { ...binding, contract, rests };
}

/** Reset every actual joint, including nonphysics fingers/twists/metacarpals. */
export function resetHumanoidPose(binding) {
  for (const [id, bone] of binding.order) {
    const rest = binding.rests.get(id);
    bone.position.fromArray(rest.translation); bone.quaternion.fromArray(rest.rotationXYZW); bone.scale.fromArray(rest.scale);
    bone.updateMatrix();
  }
  binding.root.updateWorldMatrix(true, true);
}

/** Convert through the ACTUAL immediate parent, including unmapped physics roles. */
export function setJointWorldQuaternion(binding, id, worldQuaternion, similarityTolerance = 1e-5) {
  const bone = binding.byId.get(id); require(bone, 'Unknown driven joint');
  require(Number.isFinite(similarityTolerance) && similarityTolerance >= 0 && similarityTolerance <= 1e-4, 'Explicit near-similarity tolerance must be <= 1e-4');
  require(worldQuaternion?.isQuaternion && Math.abs(worldQuaternion.lengthSq() - 1) < 1e-5, 'Unit target quaternion required');
  const parentQuaternion = new Quaternion();
  if (bone.parent) {
    bone.parent.updateWorldMatrix(true, false);
    const e = bone.parent.matrixWorld.elements, columns = [0, 4, 8].map(k => new Vector3(e[k], e[k + 1], e[k + 2]));
    const lengths = columns.map(column => column.length());
    // Blender/glTF float32 TRS can compound ~1e-6 uniform-scale residuals.
    // This is a relative serialization tolerance, not acceptance of actual shear.
    const scale = Math.max(...lengths);
    require(Math.min(...lengths) > 1e-12 && (scale - Math.min(...lengths)) / scale < similarityTolerance
      && columns.every((a, i) => columns.every((b, j) => i === j || Math.abs(a.dot(b)) / (lengths[i] * lengths[j]) < similarityTolerance))
      && bone.parent.matrixWorld.determinant() > 0,
    `Quaternion-only world solve needs a nonreflected similarity parent (${bone.name} under ${bone.parent.name}; scales ${lengths.join(',')})`);
    bone.parent.getWorldQuaternion(parentQuaternion).normalize();
  }
  bone.quaternion.copy(parentQuaternion.invert().multiply(worldQuaternion)).normalize();
  bone.updateMatrix(); bone.updateWorldMatrix(false, true);
}

/** WristWorld * SocketInWrist = TargetSocketWorld; rotates offset AND orientation. */
export function solvePalmSocketTarget(binding, side, targetSocketWorld) {
  const hand = binding.contract.hands[side]; require(hand, 'Unknown hand');
  require(targetSocketWorld?.isMatrix4 && targetSocketWorld.elements.every(Number.isFinite)
    && Math.abs(targetSocketWorld.determinant()) > 1e-12, 'Finite nonsingular target socket frame required');
  return targetSocketWorld.clone().multiply(new Matrix4().fromArray(hand.socketInWrist).invert());
}
