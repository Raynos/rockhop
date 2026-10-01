/** Portable named world-deformation fixtures, usable by CPU and browser gates. */
import * as THREE from 'three';
export interface PoseFrame {
  family: string; frame: number; timeSeconds: number; closedGrip: number;
  deformationWorldColumnMajor: number[][];
}
export interface PoseFixture {
  schemaVersion: number; fps: number; secondsPerFamily: number;
  jointNames: string[]; referenceCentresWorld: number[][]; families: string[];
  frames: PoseFrame[];
}
export function createFixturePlayer(scene: THREE.Object3D, fixture: PoseFixture) {
  if (fixture.schemaVersion !== 1 || fixture.jointNames.length !== 19) throw new Error('Unsupported fixture contract');
  scene.updateWorldMatrix(true, true);
  const bones = new Map<string, THREE.Bone>();
  // GLTFLoader removes periods for PropertyBinding. Match only this declared
  // contract; do not infer a replacement skeleton or accept ambiguous aliases.
  const aliases = new Map(fixture.jointNames.map(name => [name.replace(/\./g, ''), name]));
  if (aliases.size !== fixture.jointNames.length) throw new Error('Ambiguous fixture names');
  const meshes: THREE.SkinnedMesh[] = [];
  scene.traverse(o => {
    if ((o as THREE.Bone).isBone) {
      const raw = o.name.replace(/^fresh\.?/, '').replace(/\./g, '');
      const name = aliases.get(raw);
      if (!name) throw new Error('Undeclared bone: ' + o.name);
      if (bones.has(name)) throw new Error('Duplicate bone: ' + name);
      bones.set(name, o as THREE.Bone);
    }
    if ((o as THREE.SkinnedMesh).isSkinnedMesh) meshes.push(o as THREE.SkinnedMesh);
  });
  const rest = fixture.jointNames.map((name, i) => {
    const bone = bones.get(name); if (!bone) throw new Error('Missing mapped bone: ' + name);
    const p = bone.getWorldPosition(new THREE.Vector3());
    if (p.distanceTo(new THREE.Vector3().fromArray(fixture.referenceCentresWorld[i]!)) > 1e-5)
      throw new Error('Fixture/rest mismatch requires explicit adapter: ' + name);
    return bone.matrixWorld.clone();
  });
  const ordered = fixture.jointNames.map((name,i) => ({bone: bones.get(name)!, i}));
  const depth = (bone: THREE.Object3D) => { let d=0; for(let p=bone.parent;p;p=p.parent)d++; return d; };
  ordered.sort((a,b) => depth(a.bone)-depth(b.bone));
  const desired = new Map<THREE.Object3D, THREE.Matrix4>();
  return {
    bones, meshes, rest,
    apply(frame: PoseFrame) {
      if (frame.deformationWorldColumnMajor.length !== rest.length) throw new Error('Pose joint count mismatch');
      desired.clear();
      for (const {bone,i} of ordered) {
        const values=frame.deformationWorldColumnMajor[i]!;
        if(values.length!==16 || !values.every(Number.isFinite)) throw new Error('Nonfinite fixture');
        desired.set(bone, new THREE.Matrix4().fromArray(values).multiply(rest[i]!));
      }
      for (const {bone} of ordered) {
        const parent = bone.parent;
        const parentWorld = parent ? desired.get(parent) ?? parent.matrixWorld : new THREE.Matrix4();
        const local = parentWorld.clone().invert().multiply(desired.get(bone)!);
        local.decompose(bone.position,bone.quaternion,bone.scale);
        bone.updateMatrix();
      }
      for (const mesh of meshes) {
        if (!mesh.morphTargetInfluences) continue;
        // These fixtures admit source grip morphs only, never clip compression.
        for (const [name,index] of Object.entries(mesh.morphTargetDictionary ?? {})) {
          mesh.morphTargetInfluences[index] = /grip/i.test(name) ? frame.closedGrip : 0;
        }
      }
      scene.updateWorldMatrix(true,true);
      for (const mesh of meshes) mesh.skeleton.update();
      let error=0;
      for (const {bone} of ordered)
        for(let k=0;k<16;k++) error=Math.max(error,Math.abs(bone.matrixWorld.elements[k]!-desired.get(bone)!.elements[k]!));
      if(error>1e-8) throw new Error('World/local fixture parity failed: '+error);
      return {maximumWorldMatrixError:error};
    }
  };
}
