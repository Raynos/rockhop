/** Isolated CPU verifier for the metadata contract; parent owns runtime driver. */
import * as THREE from 'three';
type Key = { name: string; relativeSkinQuaternions: number[][] };
type Metadata = { version: number; keys: Key[]; jointNames: string[]; nearestFullRadiusRad: number; nearestZeroRadiusRad: number; epsilonRad: number };
export function applyCPUDriver(scene: THREE.Object3D, enabled: boolean, amplitude: number) {
  let metadata: string | undefined;
  const meshes: THREE.SkinnedMesh[]=[];
  scene.traverse(o=>{
    if(typeof o.userData.rockhopSleeveCorrective==='string')metadata=o.userData.rockhopSleeveCorrective;
    const m=o as THREE.SkinnedMesh;
    if(m.isSkinnedMesh&&m.morphTargetDictionary?.['sleeveCorrective.sample114']!==undefined)meshes.push(m);
  });
  if(!metadata||meshes.length!==3)throw new Error('Missing sleeve metadata or primitive targets');
  const data=JSON.parse(metadata) as Metadata,reference=meshes[0]!;
  if(data.version!==1||data.keys.length!==4||reference.skeleton.bones.length!==19)throw new Error('Invalid sleeve contract');
  const joints=data.jointNames.map(n=>reference.skeleton.bones.findIndex(b=>b.name===n.replace('.','')));
  if(joints.some(i=>i<0))throw new Error('Missing mapped arm joint');
  scene.updateWorldMatrix(true,true);
  const q=joints.map(j=>{
    const mat=reference.skeleton.bones[j]!.matrixWorld.clone().multiply(reference.skeleton.boneInverses[j]!).multiply(reference.bindMatrix),q=new THREE.Quaternion();
    mat.decompose(new THREE.Vector3(),q,new THREE.Vector3());return q.normalize();
  });
  const ref=q[0]!.clone().invert(),features=q.slice(1).map(q=>ref.clone().multiply(q).normalize());
  const distances=data.keys.map(key=>Math.sqrt(features.reduce((s,q,i)=>s+q.angleTo(new THREE.Quaternion().fromArray(key.relativeSkinQuaternions[i]!))**2,0))),nearest=Math.min(...distances);
  const t=THREE.MathUtils.clamp((nearest-data.nearestFullRadiusRad)/(data.nearestZeroRadiusRad-data.nearestFullRadiusRad),0,1),strength=enabled?(1-t*t*(3-2*t))*THREE.MathUtils.clamp(amplitude,0,1):0;
  const radial=distances.map(d=>1/(d*d+data.epsilonRad*data.epsilonRad)),sum=radial.reduce((a,b)=>a+b,0),weights=radial.map(w=>w/sum*strength);
  for(const mesh of meshes)for(const [i,key] of data.keys.entries()){
    const index=mesh.morphTargetDictionary?.[key.name];if(index===undefined||!mesh.morphTargetInfluences)throw new Error('Missing morph channel');mesh.morphTargetInfluences[index]=weights[i]!;
  }
  return {nearestRad:nearest,strength,weights,features:features.map(q=>q.toArray()),distances};
}
