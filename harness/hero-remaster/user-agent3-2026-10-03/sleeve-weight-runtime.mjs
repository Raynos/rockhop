/** Actual GLTF skinning source control, driven by the existing real body bones. */
import{Vector3,Skeleton}from'three';import{GLTFLoader}from'three/addons/loaders/GLTFLoader.js';
export async function loadSleeveWeightControl(debug,url,handoff){
  const gltf=await new GLTFLoader().loadAsync(url);gltf.scene.updateMatrixWorld(true);const meshes=[];gltf.scene.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o);});if(meshes.length!==1)throw new Error('Expected one source sleeve mesh');
  const mesh=meshes[0],sourceSkin=mesh.skeleton;sourceSkin.update();const attributes=mesh.geometry.attributes,ancestry=[],seen=new Set();
  for(let row=0;row<attributes.position.count;row++){const world=mesh.getVertexPosition(row,new Vector3()).applyMatrix4(mesh.matrixWorld),native=[world.x-.65,-world.z,world.y],matches=handoff.pattern.verticesNativeM.map((p,id)=>({id,error:Math.hypot(...p.map((x,i)=>x-native[i]))})).filter(v=>v.error<2e-6);
    if(matches.length!==1)throw new Error('Source sleeve rest row ancestry ambiguous');const id=matches[0].id;ancestry.push({row,nativeVertexID:id,restResidualM:matches[0].error});seen.add(id);}
  if(seen.size!==288||mesh.geometry.index.count!==528*3||sourceSkin.bones.length!==51)throw new Error('Frozen source topology/bind absent');
  const body=debug.rider.sleeveGeometry.find(p=>p.mesh.geometry.attributes.position.count===9981)?.mesh;if(!body)throw new Error('Actual canonical body missing');
  const byName=new Map(body.skeleton.bones.map((b,i)=>[b.name,{bone:b,inverse:body.skeleton.boneInverses[i]}]));let maximumInverseBindComponentDifference=0;
  const bones=sourceSkin.bones.map((b,i)=>{const current=byName.get(b.name);if(!current)throw new Error('Source bind name missing on actual body');for(let k=0;k<16;k++)maximumInverseBindComponentDifference=Math.max(maximumInverseBindComponentDifference,Math.abs(sourceSkin.boneInverses[i].elements[k]-current.inverse.elements[k]));return current.bone;});
  if(maximumInverseBindComponentDifference>2e-6)throw new Error('Source control inverse bind differs from protected body');
  // Keep the source mesh bind matrix. Attached bind mode removes the current
  // mesh world transform, so the external actual bone worlds determine skinning.
  const restBind=mesh.bindMatrix.clone();mesh.removeFromParent();mesh.position.set(0,0,0);mesh.quaternion.identity();mesh.scale.set(1,1,1);mesh.matrix.identity();mesh.matrixWorld.identity();mesh.bindMatrix.copy(restBind);mesh.skeleton=new Skeleton(bones,sourceSkin.boneInverses.map(m=>m.clone()));mesh.frustumCulled=false;debug.scene.add(mesh);mesh.updateMatrixWorld(true);mesh.skeleton.update();
  const nativeFaces=Array.from({length:528},(_,f)=>Array.from(mesh.geometry.index.array.subarray(f*3,f*3+3),row=>ancestry[row].nativeVertexID));
  const keys=faces=>faces.map(f=>f.slice().sort((a,b)=>a-b).join(':')).sort();if(JSON.stringify(keys(nativeFaces))!==JSON.stringify(keys(handoff.pattern.triangleVertexIDs)))throw new Error('Exported source triangles differ from frozen native pattern');
  const actualWeights=ancestry.map(({row,nativeVertexID})=>({row,nativeVertexID,weights:Array.from({length:4},(_,k)=>[mesh.skeleton.bones[attributes.skinIndex.getComponent(row,k)].name,attributes.skinWeight.getComponent(row,k)]).filter(([,w])=>w>0)}));
  const material=m=>({name:m.name,type:m.type,color:m.color.toArray(),metalness:m.metalness,roughness:m.roughness,side:m.side});
  return{mesh,ancestry,nativeFaces,actualWeights,contract:{actualGLTFLoader:true,rows:ancestry.length,nativeVertices:288,triangles:528,joints:51,maximumInverseBindComponentDifference,material:material(mesh.material),bind:restBind.toArray(),ancestry,
    limits:['Actual source positions/UV/normals/skin attributes/material retained. Only skeleton bone references map by exact same51native names to current actual body poses.','No bone transform, physics pose, source rest/weights or projection change. Collision correction and layered safety remain open.']},
    sample(){mesh.updateMatrixWorld(true);mesh.skeleton.update();const rows=ancestry.map(({row})=>mesh.getVertexPosition(row,new Vector3()).applyMatrix4(mesh.matrixWorld));const native=Array(288),splits=[];let maximumDuplicateResidualM=0;for(const a of ancestry){if(native[a.nativeVertexID]){const gap=native[a.nativeVertexID].distanceTo(rows[a.row]);maximumDuplicateResidualM=Math.max(maximumDuplicateResidualM,gap);splits.push({row:a.row,id:a.nativeVertexID,gapM:gap});}else native[a.nativeVertexID]=rows[a.row];}
      return{positions:new Float32Array(native.flatMap(p=>p.toArray())),maximumDuplicateResidualM};},dispose(){debug.scene.remove(mesh);mesh.geometry.dispose();mesh.material.dispose();mesh.skeleton.dispose();}};
}
