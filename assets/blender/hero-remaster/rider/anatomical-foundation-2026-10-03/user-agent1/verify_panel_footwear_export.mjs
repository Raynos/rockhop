// Actual-loader preservation/rest proof for the complete footwear successor.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
const [parentFile, candidateFile, output] = process.argv.slice(2), sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const { loadRigAt } = await import(pathToFileURL(path.resolve('src/render/hero/gltfTestUtils.ts')).href);
const load=async file=>{const g=await loadRigAt(pathToFileURL(path.resolve(file)),true);g.scene.updateMatrixWorld(true);const meshes=[];g.scene.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o);});return {g,meshes};};
const parent=await load(parentFile), candidate=await load(candidateFile);
const bufferHash=a=>sha(Buffer.from(a.buffer,a.byteOffset,a.byteLength));
const preserved=[];let maximumRest=0;
for(const mesh of candidate.meshes) {
  const old=parent.meshes[0];
  if(mesh.skeleton.bones.length!==51||JSON.stringify(mesh.skeleton.bones.map(b=>[b.name,b.parent?.name]))!==JSON.stringify(old.skeleton.bones.map(b=>[b.name,b.parent?.name])))throw Error('51joint hierarchy changed');
  if(mesh.skeleton.boneInverses.some((m,i)=>m.elements.some((x,j)=>x!==old.skeleton.boneInverses[i].elements[j])))throw Error('Inverse bind changed');
  if(mesh.morphTargetInfluences?.some(v=>v!==0))throw Error('Nonzero candidate defaults');
  mesh.skeleton.update();let closure=0;
  for(let i=0;i<mesh.geometry.attributes.position.count;i++) {
    const world=mesh.localToWorld(mesh.getVertexPosition(i,new THREE.Vector3()));
    closure=Math.max(closure,world.distanceTo(new THREE.Vector3().fromBufferAttribute(mesh.geometry.attributes.position,i)));
  }
  maximumRest=Math.max(maximumRest,closure);
  if(mesh.name.startsWith('Complete_canonical_fitted_boot'))continue;
  const reference=parent.meshes.find(m=>m.name===mesh.name);
  if(!reference)throw Error('Unmapped nonfootwear mesh '+mesh.name);
  const hashes={};
  for(const [name,a] of Object.entries(mesh.geometry.attributes)) {
    hashes[name]=bufferHash(a.array);if(hashes[name]!==bufferHash(reference.geometry.attributes[name].array))throw Error('Changed nonboot field '+mesh.name+'/'+name);
  }
  if(bufferHash(mesh.geometry.index.array)!==bufferHash(reference.geometry.index.array))throw Error('Changed nonboot indices');
  for(const [name,targets] of Object.entries(mesh.geometry.morphAttributes)) targets.forEach((a,i)=>{if(bufferHash(a.array)!==bufferHash(reference.geometry.morphAttributes[name][i].array))throw Error('Changed nonboot morph');});
  preserved.push({mesh:mesh.name,rows:mesh.geometry.attributes.position.count,attributeHashes:hashes,restClosureM:closure});
}
const boots=candidate.meshes.filter(m=>m.name.startsWith('Complete_canonical_fitted_boot'));
if(boots.length!==4||preserved.length!==7||maximumRest>2e-6)throw Error('Unexpected footwear/rest inventory');
const report={status:'UNACCEPTED '+path.basename(path.dirname(candidateFile))+' complete footwear actual-loader source preservation/rest; moving wear/engine response pending',
  parent05GLBSHA256:sha(fs.readFileSync(parentFile)),candidateGLBSHA256:sha(fs.readFileSync(candidateFile)),verifierSHA256:sha(fs.readFileSync(new URL(import.meta.url))),actualGLTFLoader:true,threeRevision:THREE.REVISION,
  all51JointNamesParentsInverseBindsExact:true,allCandidateMorphDefaultsZero:true,maximumRestClosureM:maximumRest,allSevenNonBootPrimitiveFieldsExact:preserved,
  newFootwearPrimitives:boots.map(m=>({name:m.name,rows:m.geometry.attributes.position.count,triangles:m.geometry.index.count/3,material:m.material.name,metalness:m.material.metalness,roughness:m.material.roughness})),
  limits:['Original partialboot primitive removed only from visible export; retained hidden in native source.','New complete footwear geometry/materials replace old appearance fragments; no wearable moving/art or livecollision pass.','Current05 contactmap boot indices no longer describe new panel footwear; fresh source-owned sole/ankle binding required.']};
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({preserved:preserved.length,boots:report.newFootwearPrimitives,maximumRest}));
