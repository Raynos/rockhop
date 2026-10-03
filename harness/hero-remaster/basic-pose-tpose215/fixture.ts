import { Matrix4, Quaternion, Vector3 } from 'three';
import type { PoseFixture, PoseFrame } from '../basic-pose-gate/protocol';

export const ROLES = ['pelvis', 'spine', 'chest', 'neck', 'head',
  'shoulder.L', 'upperArm.L', 'forearm.L', 'hand.L',
  'shoulder.R', 'upperArm.R', 'forearm.R', 'hand.R',
  'thigh.L', 'shin.L', 'foot.L', 'thigh.R', 'shin.R', 'foot.R'] as const;
export type Role = typeof ROLES[number];
export const PARENT: Record<Role, Role | null> = {
  pelvis: null, spine: 'pelvis', chest: 'spine', neck: 'chest', head: 'neck',
  'shoulder.L': 'chest', 'upperArm.L': 'shoulder.L', 'forearm.L': 'upperArm.L', 'hand.L': 'forearm.L',
  'shoulder.R': 'chest', 'upperArm.R': 'shoulder.R', 'forearm.R': 'upperArm.R', 'hand.R': 'forearm.R',
  'thigh.L': 'pelvis', 'shin.L': 'thigh.L', 'foot.L': 'shin.L',
  'thigh.R': 'pelvis', 'shin.R': 'thigh.R', 'foot.R': 'shin.R',
};
export interface JointBinding {
  role: Role; nodeIndex: number; name: string; parentNodeIndex: number | null;
  restWorldColumnMajor: number[]; inverseBindColumnMajor: number[];
  /** Maps game anatomical +X front, +Y up, +Z left into this bone's local axes. */
  anatomyLocalQuaternion: number[];
}
export interface Binding {
  schemaVersion: 1; sourceSHA256: string; skinIndex: number;
  /** Actual skin.joints order, never role/traversal order. */
  joints: JointBinding[];
  rootParentWorldColumnMajor: number[];
  meshRestWorldColumnMajor: number[][];
  restBoundsWorld: { min: number[]; max: number[] } | null;
}
export interface PreparedBinding {
  source: Binding; byRole: Map<Role, number>; rest: Matrix4[]; local: Matrix4[];
  frames: Quaternion[]; rootParent: Matrix4;
}
const identity = new Matrix4();
const axes = [new Vector3(1, 0, 0), new Vector3(0, 1, 0), new Vector3(0, 0, 1)];
export function matrixError(a: Matrix4, b: Matrix4): number {
  return Math.max(...a.elements.map((v, i) => Math.abs(v - b.elements[i]!)));
}
export function checkedMatrix(values: number[], label: string): Matrix4 {
  if (values.length !== 16 || !values.every(Number.isFinite)) throw new Error(label + ': invalid matrix');
  const m = new Matrix4().fromArray(values), p = new Vector3(), q = new Quaternion(), s = new Vector3();
  m.decompose(p, q, s);
  if (Math.min(s.x, s.y, s.z) <= 0 || Math.max(s.x, s.y, s.z) - Math.min(s.x, s.y, s.z) > 1e-6
    || matrixError(m, new Matrix4().compose(p, q, s)) > 1e-6)
    throw new Error(label + ': requires positive uniform scale without shear/reflection');
  return m;
}
export function prepareBinding(source: Binding): PreparedBinding {
  if (source.schemaVersion !== 1 || !/^[a-f0-9]{64}$/.test(source.sourceSHA256) || source.joints.length !== 19)
    throw new Error('Invalid source-bound 19-joint binding');
  const byRole = new Map<Role, number>(), nodeIndices = new Set<number>(), names = new Set<string>();
  source.joints.forEach((j, i) => {
    if (!ROLES.includes(j.role) || byRole.has(j.role) || nodeIndices.has(j.nodeIndex) || !j.name || names.has(j.name))
      throw new Error('Duplicate/unknown role, node or name');
    byRole.set(j.role, i); nodeIndices.add(j.nodeIndex); names.add(j.name);
  });
  const rootParent = checkedMatrix(source.rootParentWorldColumnMajor, 'root parent');
  const rest = source.joints.map(j => checkedMatrix(j.restWorldColumnMajor, j.role));
  if (source.meshRestWorldColumnMajor.length === 0) throw new Error('No consumed skinned mesh');
  const meshRest = source.meshRestWorldColumnMajor.map(v => checkedMatrix(v, 'mesh rest'));
  const frames = source.joints.map((j, i) => {
    const parentRole = PARENT[j.role], parentIndex = parentRole === null ? undefined : byRole.get(parentRole);
    if (parentRole !== null && (parentIndex === undefined || j.parentNodeIndex !== source.joints[parentIndex]!.nodeIndex))
      throw new Error(j.role + ': requires direct declared bone parent');
    if (parentRole === null && j.parentNodeIndex !== null && nodeIndices.has(j.parentNodeIndex))
      throw new Error('Root parent cannot be another joint');
    const ibm = checkedMatrix(j.inverseBindColumnMajor, j.role + ' inverse bind');
    for (const mesh of meshRest)
      if (matrixError(rest[i]!.clone().multiply(ibm), mesh) > 1e-5)
        throw new Error(j.role + ': rest/bind cancellation mismatch');
    if (j.anatomyLocalQuaternion.length !== 4 || !j.anatomyLocalQuaternion.every(Number.isFinite))
      throw new Error(j.role + ': missing declared anatomy frame');
    const frame = new Quaternion().fromArray(j.anatomyLocalQuaternion);
    if (Math.abs(frame.length() - 1) > 1e-6) throw new Error(j.role + ': nonunit anatomy frame');
    const worldQ = new Quaternion(); rest[i]!.decompose(new Vector3(), worldQ, new Vector3());
    const anatomyWorld = worldQ.multiply(frame);
    if (axes.some(axis => axis.clone().applyQuaternion(anatomyWorld).distanceTo(axis) > 1e-5))
      throw new Error(j.role + ': anatomy axes must declare game +X front, +Y up, +Z left');
    return frame;
  });
  const position = (role: Role) => new Vector3().setFromMatrixPosition(rest[byRole.get(role)!]!);
  const direction = (from: Role, to: Role, expected: Vector3) => {
    const delta = position(to).sub(position(from));
    if (delta.length() < 1e-5 || delta.normalize().dot(expected) < Math.cos(10 * Math.PI / 180))
      throw new Error(from + ' -> ' + to + ': not declared anatomical T-pose');
  };
  for (const side of ['L', 'R'] as const) {
    const lateral = new Vector3(0, 0, side === 'L' ? 1 : -1);
    direction('upperArm.' + side as Role, 'forearm.' + side as Role, lateral);
    direction('forearm.' + side as Role, 'hand.' + side as Role, lateral);
    direction('thigh.' + side as Role, 'shin.' + side as Role, new Vector3(0, -1, 0));
    direction('shin.' + side as Role, 'foot.' + side as Role, new Vector3(0, -1, 0));
  }
  const local = source.joints.map((j, i) => {
    const parent = PARENT[j.role];
    return (parent === null ? rootParent : rest[byRole.get(parent)!]!).clone().invert().multiply(rest[i]!);
  });
  return { source, byRole, rest, local, frames, rootParent };
}

export const BASE_FAMILIES = ['neutral', 'horizontal', 'overhead', 'forward', 'elbow', 'forearm_twist',
  'wrist_flex', 'wrist_deviation', 'grip', 'squat', 'sit', 'lean'] as const;
const ARM_FAMILIES = BASE_FAMILIES.slice(1, 9);
export const FAMILIES = [...BASE_FAMILIES, ...ARM_FAMILIES.flatMap(f => [f + '_L', f + '_R'])];
const smooth = (v: number) => v * v * (3 - 2 * v);
const pulse = (u: number) => smooth(u < 0.5 ? 2 * u : 2 - 2 * u);
const degree = Math.PI / 180;
export interface Sample {
  frame: PoseFrame; desiredWorldColumnMajor: number[][];
  /** Pivot correction is a authored control, never a sole/contact/COM measurement. */
  footPivotResidualMetres: { L: number; R: number } | null;
}
export function samplePose(binding: PreparedBinding, family: string, timeSeconds: number, duration = 4, frameNumber = 0): Sample {
  if (!FAMILIES.includes(family) || !Number.isFinite(timeSeconds) || !Number.isFinite(duration)
    || duration <= 0 || timeSeconds < 0 || timeSeconds > duration) throw new Error('Invalid pose sample');
  const side = family.endsWith('_L') ? 'L' : family.endsWith('_R') ? 'R' : null;
  const base = side ? family.slice(0, -2) : family;
  const u = timeSeconds / duration, amount = pulse(u);
  const rotations = new Map<Role, Quaternion>();
  const rotate = (role: Role, axis: number, angle: number) => {
    rotations.set(role, new Quaternion().setFromAxisAngle(axes[axis]!, angle * degree));
  };
  for (const limb of ['L', 'R'] as const) {
    if (side && limb !== side) continue;
    const s = limb === 'L' ? 1 : -1, arm = 'upperArm.' + limb as Role;
    if (base === 'horizontal') rotate(arm, 0, s * 90 * pulse((u * 2) % 1));
    if (base === 'overhead') rotate(arm, 0, -s * 90 * amount);
    if (base === 'forward') rotate(arm, 1, s * 90 * amount);
    if (['elbow', 'forearm_twist', 'wrist_flex', 'wrist_deviation', 'grip'].includes(base)) {
      const stage = smooth(Math.min(1, Math.min(u, 1 - u) * 4));
      rotate(arm, 1, s * 70 * stage);
      if (base === 'elbow') rotate('forearm.' + limb as Role, 1, s * 120 * amount);
      if (base === 'forearm_twist') rotate('forearm.' + limb as Role, 2, s * 90 * amount);
      if (base === 'wrist_flex') rotate('hand.' + limb as Role, 1, s * 60 * amount);
      if (base === 'wrist_deviation') rotate('hand.' + limb as Role, 0, s * 30 * amount);
    }
  }
  if (base === 'squat' || base === 'sit') {
    for (const limb of ['L', 'R'] as const) {
      rotate('thigh.' + limb as Role, 2, (base === 'sit' ? 90 : 70) * amount);
      rotate('shin.' + limb as Role, 2, (base === 'sit' ? -90 : -140) * amount);
      rotate('foot.' + limb as Role, 2, (base === 'sit' ? 0 : 70) * amount);
    }
    rotate('spine', 2, -15 * amount);
  }
  if (base === 'lean') rotate('pelvis', 0, 20 * (u < 0.5 ? pulse(u * 2) : -pulse((u - 0.5) * 2)));
  const desired = binding.rest.map(m => m.clone());
  const evaluate = (rootOffset: Vector3) => {
    for (const role of ROLES) {
      const i = binding.byRole.get(role)!, parentRole = PARENT[role];
      const parent = parentRole === null ? binding.rootParent : desired[binding.byRole.get(parentRole)!]!;
      const frame = binding.frames[i]!, semanticRotation = rotations.get(role) ?? new Quaternion();
      const localRotation = frame.clone().multiply(semanticRotation).multiply(frame.clone().invert());
      desired[i] = parent.clone().multiply(binding.local[i]!).multiply(new Matrix4().makeRotationFromQuaternion(localRotation));
      if (parentRole === null) desired[i]!.premultiply(new Matrix4().makeTranslation(rootOffset.x, rootOffset.y, rootOffset.z));
    }
  };
  evaluate(new Vector3());
  let footPivotResidualMetres: Sample['footPivotResidualMetres'] = null;
  if (base === 'sit' || base === 'squat') {
    const residual = (limb: 'L' | 'R') => {
      const i = binding.byRole.get('foot.' + limb as Role)!;
      return new Vector3().setFromMatrixPosition(binding.rest[i]!).sub(new Vector3().setFromMatrixPosition(desired[i]!));
    };
    const correction = residual('L').add(residual('R')).multiplyScalar(0.5);
    evaluate(correction);
    footPivotResidualMetres = { L: residual('L').length(), R: residual('R').length() };
  }
  const deformation = desired.map((m, i) => m.clone().multiply(binding.rest[i]!.clone().invert()).toArray());
  // Exact rest endpoints avoid epsilon-only deformation in neutral reference samples.
  if (u === 0 || u === 1 || base === 'neutral') deformation.forEach((_, i) => { deformation[i] = identity.toArray(); });
  return {
    frame: { family, frame: frameNumber, timeSeconds, closedGrip: base === 'grip' ? amount : 0,
      gripSide: side, deformationWorldColumnMajor: deformation },
    desiredWorldColumnMajor: desired.map(m => m.toArray()), footPivotResidualMetres,
  };
}
export interface NewPoseFixture extends PoseFixture {
  provenance: { sourceSHA256: string; skinIndex: number; restWorldColumnMajor: number[][];
    inverseBindColumnMajor: number[][]; anatomyLocalQuaternion: number[][];
    axes: string; baseFps: number; subdivisions: number; acceptance: 'UNACCEPTED';
    grip: 'UNMEASURED'; contacts: 'UNMEASURED'; cameras: ReturnType<typeof cameraCoverage> };
}
export function cameraCoverage(binding: PreparedBinding) {
  const bounds = binding.source.restBoundsWorld;
  if (!bounds) return { status: 'UNMEASURED' as const, views: [] };
  const min = new Vector3().fromArray(bounds.min), max = new Vector3().fromArray(bounds.max);
  if ([...bounds.min, ...bounds.max].some(v => !Number.isFinite(v)) || min.x >= max.x || min.y >= max.y || min.z >= max.z)
    throw new Error('Invalid actual mesh bounds');
  const target = min.clone().add(max).multiplyScalar(0.5), size = max.clone().sub(min);
  const distance = size.length() * 2, span = Math.max(size.x, size.y, size.z) * 1.2;
  return { status: 'REQUESTED_NOT_RENDERED' as const,
    views: [['front', new Vector3(1, 0, 0)], ['left-profile', new Vector3(0, 0, 1)],
      ['back', new Vector3(-1, 0, 0)]].map(([name, axis]) => ({ name: name as string,
      position: target.clone().addScaledVector(axis as Vector3, distance).toArray(), target: target.toArray(),
      up: [0, 1, 0], orthographicSpan: span, aspect: 1 })) };
}
export function generateFixture(source: Binding, baseFps = 24, subdivisions = 2, duration = 4): NewPoseFixture {
  if (!Number.isInteger(baseFps) || baseFps < 1 || !Number.isInteger(subdivisions) || subdivisions < 1
    || duration <= 0 || !Number.isInteger(baseFps * subdivisions * duration)) throw new Error('Invalid sampling grid');
  const binding = prepareBinding(source), fps = baseFps * subdivisions, frames: PoseFrame[] = [];
  for (const family of FAMILIES)
    for (let i = 0; i <= duration * fps; i++) frames.push(samplePose(binding, family, i / fps, duration, i).frame);
  return { schemaVersion: 1, fps, secondsPerFamily: duration,
    jointNames: source.joints.map(j => j.name),
    referenceCentresWorld: binding.rest.map(m => new Vector3().setFromMatrixPosition(m).toArray()),
    families: [...FAMILIES], frames,
    provenance: { sourceSHA256: source.sourceSHA256, skinIndex: source.skinIndex,
      restWorldColumnMajor: source.joints.map(j => j.restWorldColumnMajor),
      inverseBindColumnMajor: source.joints.map(j => j.inverseBindColumnMajor),
      anatomyLocalQuaternion: source.joints.map(j => j.anatomyLocalQuaternion),
      axes: '+X front, +Y up, +Z left; anatomy frames are declared bone-local bases',
      baseFps, subdivisions, acceptance: 'UNACCEPTED', grip: 'UNMEASURED', contacts: 'UNMEASURED',
      cameras: cameraCoverage(binding) } };
}
