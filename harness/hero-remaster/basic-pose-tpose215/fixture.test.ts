import { createHash } from 'node:crypto';
import { describe, expect, it } from 'vitest';
import { Bone, BufferGeometry, Float32BufferAttribute, Matrix4, Quaternion, Skeleton, SkinnedMesh,
  Uint16BufferAttribute, Vector3 } from 'three';
import { generateFixture, matrixError, PARENT, prepareBinding, ROLES, samplePose } from './fixture';
import type { Binding, Role } from './fixture';
import { readGlbBinding } from './read-glb';
import type { BindingManifest } from './read-glb';

// Independently authored anatomical pivots; arbitrary rolls and nonidentity mesh bind.
function synthetic() {
  const pivots: Record<Role, number[]> = {
    pelvis: [0, 1, 0], spine: [0, 1.2, 0], chest: [0, 1.4, 0], neck: [0, 1.6, 0], head: [0, 1.7, 0],
    'shoulder.L': [0, 1.45, .12], 'upperArm.L': [0, 1.45, .2], 'forearm.L': [0, 1.45, .5], 'hand.L': [0, 1.45, .75],
    'shoulder.R': [0, 1.45, -.12], 'upperArm.R': [0, 1.45, -.2], 'forearm.R': [0, 1.45, -.5], 'hand.R': [0, 1.45, -.75],
    'thigh.L': [0, 1, .1], 'shin.L': [0, .55, .1], 'foot.L': [0, .1, .1],
    'thigh.R': [0, 1, -.1], 'shin.R': [0, .55, -.1], 'foot.R': [0, .1, -.1],
  };
  const meshWorld = new Matrix4().makeTranslation(.4, .2, -.1);
  const rest = ROLES.map((role, i) => new Matrix4().compose(new Vector3().fromArray(pivots[role]),
    new Quaternion().setFromAxisAngle(new Vector3(1, 2, 3).normalize(), .17 * i), new Vector3(1, 1, 1)));
  const binding: Binding = { schemaVersion: 1, sourceSHA256: 'a'.repeat(64), skinIndex: 0,
    rootParentWorldColumnMajor: new Matrix4().toArray(), meshRestWorldColumnMajor: [meshWorld.toArray()],
    restBoundsWorld: { min: [-.2, 0, -.8], max: [.2, 1.8, .8] },
    joints: [...ROLES].reverse().map(role => {
      const i = ROLES.indexOf(role), q = new Quaternion(); rest[i]!.decompose(new Vector3(), q, new Vector3());
      return { role, name: role, nodeIndex: i, parentNodeIndex: PARENT[role] === null ? null : ROLES.indexOf(PARENT[role]!),
        restWorldColumnMajor: rest[i]!.toArray(), inverseBindColumnMajor: rest[i]!.clone().invert().multiply(meshWorld).toArray(),
        anatomyLocalQuaternion: q.invert().toArray() };
    }) };
  return { binding, pivots, meshWorld, rest };
}
function syntheticGlb() {
  const { binding, rest, meshWorld } = synthetic();
  const nodes = ROLES.map((role, i) => {
    const parent = PARENT[role];
    const matrix = (parent === null ? new Matrix4() : rest[ROLES.indexOf(parent)]!).clone().invert().multiply(rest[i]!);
    return { name: role, matrix: matrix.toArray(), children: ROLES.map((r, n) => PARENT[r] === role ? n : -1).filter(n => n >= 0) };
  });
  const positions = [-.5, -.2, -.7, .2, 1.6, .9, .1, .5, 0];
  const floats = new Float32Array([...binding.joints.flatMap(j => j.inverseBindColumnMajor), ...positions]);
  const raw = Buffer.from(floats.buffer);
  const gltf = { asset: { version: '2.0' }, nodes: [...nodes, { name: 'mesh', matrix: meshWorld.toArray(), mesh: 0, skin: 0 }],
    scenes: [{ nodes: [0, 19] }], skins: [{ joints: binding.joints.map(j => j.nodeIndex), inverseBindMatrices: 0 }],
    buffers: [{ byteLength: raw.length }], bufferViews: [{ buffer: 0, byteOffset: 0, byteLength: 19 * 64 },
      { buffer: 0, byteOffset: 19 * 64, byteLength: positions.length * 4 }],
    accessors: [{ bufferView: 0, componentType: 5126, count: 19, type: 'MAT4' },
      { bufferView: 1, componentType: 5126, count: 3, type: 'VEC3' }], meshes: [{ primitives: [{ attributes: { POSITION: 1 } }] }] };
  const text = Buffer.from(JSON.stringify(gltf)), json = Buffer.alloc(Math.ceil(text.length / 4) * 4, 32); text.copy(json);
  const bytes = Buffer.alloc(12 + 8 + json.length + 8 + raw.length);
  bytes.writeUInt32LE(0x46546c67, 0); bytes.writeUInt32LE(2, 4); bytes.writeUInt32LE(bytes.length, 8);
  bytes.writeUInt32LE(json.length, 12); bytes.writeUInt32LE(0x4e4f534a, 16); json.copy(bytes, 20);
  const offset = 20 + json.length; bytes.writeUInt32LE(raw.length, offset); bytes.writeUInt32LE(0x004e4942, offset + 4); raw.copy(bytes, offset + 8);
  const declaration: BindingManifest = { schemaVersion: 1, sourceSHA256: createHash('sha256').update(bytes).digest('hex'),
    skinIndex: 0, sceneIndex: 0, sceneToGameWorldColumnMajor: new Matrix4().toArray(),
    joints: binding.joints.map(({ role, nodeIndex, name, anatomyLocalQuaternion }) => ({ role, nodeIndex, name, anatomyLocalQuaternion })) };
  return { bytes, declaration };
}
describe('new T-pose hierarchical fixtures (math controls only)', () => {
  it('reads actual scrambled skin order, source hash and nonidentity bind, rejecting changed source/name', () => {
    const { bytes, declaration } = syntheticGlb(), binding = readGlbBinding(bytes, declaration);
    expect(binding.joints.map(j => j.role)).toEqual([...ROLES].reverse());
    expect(binding.restBoundsWorld!.min[0]).toBeCloseTo(-.1);
    const translated = readGlbBinding(bytes, { ...declaration,
      sceneToGameWorldColumnMajor: new Matrix4().makeTranslation(.2, .3, -.4).toArray() });
    expect(translated.rootParentWorldColumnMajor[12]).toBe(.2);
    expect(translated.restBoundsWorld!.min[0]).toBeCloseTo(.1);
    expect(() => readGlbBinding(bytes, { ...declaration, sourceSHA256: '0'.repeat(64) })).toThrow(/SHA/);
    const bad = structuredClone(declaration); bad.joints[0]!.name = 'guessed';
    expect(() => readGlbBinding(bytes, bad)).toThrow(/name/);
  });
  it('cancels rest/bind and refuses wrong anatomy frame, bind or disconnected hierarchy', () => {
    const { binding } = synthetic(), prepared = prepareBinding(binding), neutral = samplePose(prepared, 'neutral', 2);
    expect(neutral.frame.deformationWorldColumnMajor.every(m => matrixError(new Matrix4().fromArray(m), new Matrix4()) === 0)).toBe(true);
    for (const mode of ['axis', 'bind', 'parent']) {
      const bad = structuredClone(binding), hand = bad.joints.find(j => j.role === 'hand.L')!;
      if (mode === 'axis') hand.anatomyLocalQuaternion = [0, 0, 0, 1];
      if (mode === 'bind') hand.inverseBindColumnMajor = new Matrix4().toArray();
      if (mode === 'parent') hand.parentNodeIndex = 0;
      expect(() => prepareBinding(bad)).toThrow();
    }
  });
  it('keeps connected children and matches independent world pivot rotation despite bone rolls', () => {
    const { binding, pivots } = synthetic(), p = prepareBinding(binding), pose = samplePose(p, 'forward_L', 2);
    const get = (role: Role) => new Matrix4().fromArray(pose.desiredWorldColumnMajor[p.byRole.get(role)!]!);
    const expectedHand = new Vector3().fromArray(pivots['hand.L']).sub(new Vector3().fromArray(pivots['upperArm.L']))
      .applyAxisAngle(new Vector3(0, 1, 0), Math.PI / 2).add(new Vector3().fromArray(pivots['upperArm.L']));
    expect(new Vector3().setFromMatrixPosition(get('hand.L')).distanceTo(expectedHand)).toBeLessThan(1e-12);
    for (const role of ROLES) {
      const parent = PARENT[role]; if (parent === null) continue;
      const i = p.byRole.get(role)!, predicted = new Vector3().setFromMatrixPosition(p.local[i]!).applyMatrix4(get(parent));
      expect(predicted.distanceTo(new Vector3().setFromMatrixPosition(get(role)))).toBeLessThan(1e-12);
    }
    expect(matrixError(get('hand.R'), p.rest[p.byRole.get('hand.R')!]!)).toBeLessThan(1e-12);
  });
  it('deforms a real Three SkinnedMesh vertex through nonidentity bind without double transform', () => {
    const { binding, meshWorld, pivots } = synthetic(), p = prepareBinding(binding), byRole = new Map<Role, Bone>();
    for (const role of ROLES) {
      const i = p.byRole.get(role)!, bone = new Bone(); bone.name = role;
      p.local[i]!.decompose(bone.position, bone.quaternion, bone.scale); byRole.set(role, bone);
      if (PARENT[role]) byRole.get(PARENT[role]!)!.add(bone);
    }
    const root = byRole.get('pelvis')!; root.updateMatrixWorld(true);
    const bones = binding.joints.map(j => byRole.get(j.role)!);
    const geometry = new BufferGeometry(), sourceWorldPoint = new Vector3().fromArray(pivots['hand.L']).add(new Vector3(.03, .02, .01));
    geometry.setAttribute('position', new Float32BufferAttribute(sourceWorldPoint.clone().applyMatrix4(meshWorld.clone().invert()).toArray(), 3));
    geometry.setAttribute('skinIndex', new Uint16BufferAttribute([p.byRole.get('hand.L')!, 0, 0, 0], 4));
    geometry.setAttribute('skinWeight', new Float32BufferAttribute([1, 0, 0, 0], 4));
    const mesh = new SkinnedMesh(geometry); meshWorld.decompose(mesh.position, mesh.quaternion, mesh.scale);
    mesh.bind(new Skeleton(bones, binding.joints.map(j => new Matrix4().fromArray(j.inverseBindColumnMajor))), new Matrix4());
    mesh.updateMatrixWorld(true);
    expect(mesh.getVertexPosition(0, new Vector3()).applyMatrix4(mesh.matrixWorld).distanceTo(sourceWorldPoint)).toBeLessThan(1e-7);
    const pose = samplePose(p, 'forward_L', 2);
    for (const role of ROLES) {
      const i = p.byRole.get(role)!, parent = PARENT[role];
      const desired = new Matrix4().fromArray(pose.desiredWorldColumnMajor[i]!);
      const parentWorld = parent ? new Matrix4().fromArray(pose.desiredWorldColumnMajor[p.byRole.get(parent)!]!) : new Matrix4();
      parentWorld.invert().multiply(desired).decompose(byRole.get(role)!.position, byRole.get(role)!.quaternion, byRole.get(role)!.scale);
    }
    root.updateMatrixWorld(true); mesh.skeleton.update();
    const expected = sourceWorldPoint.clone().sub(new Vector3().fromArray(pivots['upperArm.L']))
      .applyAxisAngle(new Vector3(0, 1, 0), Math.PI / 2).add(new Vector3().fromArray(pivots['upperArm.L']));
    expect(mesh.getVertexPosition(0, new Vector3()).applyMatrix4(mesh.matrixWorld).distanceTo(expected)).toBeLessThan(1e-7);
  });
  it('samples reverse/halfsteps, asymmetric grip requests and exact neutral endpoints', () => {
    const { binding } = synthetic(), p = prepareBinding(binding), fixture = generateFixture(binding, 2, 2, 4);
    expect(fixture.families).toHaveLength(28); expect(fixture.frames).toHaveLength(28 * 17);
    for (const family of ['forward_L', 'elbow_R', 'forearm_twist', 'squat', 'sit']) {
      const a = samplePose(p, family, .5), b = samplePose(p, family, 3.5);
      a.desiredWorldColumnMajor.forEach((m, i) => expect(matrixError(new Matrix4().fromArray(m), new Matrix4().fromArray(b.desiredWorldColumnMajor[i]!))).toBeLessThan(1e-12));
    }
    const twist = samplePose(p, 'forearm_twist_L', 2), elbow = p.byRole.get('forearm.L')!, hand = p.byRole.get('hand.L')!;
    const distance = (a: number[], b: number[]) => new Vector3().setFromMatrixPosition(new Matrix4().fromArray(a)).distanceTo(new Vector3().setFromMatrixPosition(new Matrix4().fromArray(b)));
    expect(distance(twist.desiredWorldColumnMajor[elbow]!, twist.desiredWorldColumnMajor[hand]!)).toBeCloseTo(.25, 12);
    expect(samplePose(p, 'grip_L', 2).frame).toMatchObject({ closedGrip: 1, gripSide: 'L' });
    expect(fixture.provenance).toMatchObject({ grip: 'UNMEASURED', contacts: 'UNMEASURED', acceptance: 'UNACCEPTED' });
  });
});
