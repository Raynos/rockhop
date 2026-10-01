import * as THREE from 'three';
import { loadRigAt } from '../../../../../../../src/render/hero/gltfTestUtils';
for (const file of ['/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/guarded-correction01/rider.glb', process.cwd()+'/public/models/bike-rookie.glb']) {
 const g=await loadRigAt(new URL('file://'+file)); g.scene.updateMatrixWorld(true); const rows:unknown[]=[];
 g.scene.traverse(o=>{ const m=o as THREE.SkinnedMesh; if(!m.isMesh)return; const p=m.geometry.getAttribute('position'); const box=new THREE.Box3(); for(let i=0;i<p.count;i++)box.expandByPoint(new THREE.Vector3().fromBufferAttribute(p,i)); rows.push({name:o.name,vertices:p.count,triangles:(m.geometry.index?.count??p.count)/3,material:Array.isArray(m.material)?m.material.map(x=>x.name):m.material.name,bounds:{min:box.min.toArray(),max:box.max.toArray()},matrixWorld:m.matrixWorld.toArray(),bones:m.skeleton?.bones.map(b=>b.name),morph:m.morphTargetDictionary});});
 console.log(JSON.stringify({file,rows}));
}
