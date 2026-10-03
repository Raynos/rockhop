// Exact current exported-row ancestry for the new local sleeve, no legacy IDs.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
const [file, parentFile, descriptorFile, output] = process.argv.slice(2);
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const { loadRigAt } = await import(pathToFileURL(path.resolve('src/render/hero/gltfTestUtils.ts')).href);
const load = async file => { const g = await loadRigAt(pathToFileURL(path.resolve(file))); g.scene.updateMatrixWorld(true); const meshes=[]; g.scene.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o);}); return {g,meshes}; };
const sleeve = await load(file), parent = await load(parentFile), descriptor = JSON.parse(fs.readFileSync(descriptorFile));
if (sha(fs.readFileSync(file)) !== descriptor.sleeveRestGLBSHA256 || sleeve.meshes.length !== 1) throw Error('Wrong local pattern');
const mesh = sleeve.meshes[0], reference = parent.meshes[0];
if (mesh.skeleton.bones.length !== 51 || JSON.stringify(mesh.skeleton.bones.map(b=>[b.name,b.parent?.name])) !== JSON.stringify(reference.skeleton.bones.map(b=>[b.name,b.parent?.name]))) throw Error('51joint ancestry changed');
let bindError = 0; mesh.skeleton.boneInverses.forEach((m,i)=>m.elements.forEach((x,j)=>{bindError=Math.max(bindError,Math.abs(x-reference.skeleton.boneInverses[i].elements[j]));}));
if (bindError !== 0) throw Error('Bind changed');
mesh.skeleton.update(); const rows=[]; let maximumRestError=0;
for(let i=0;i<mesh.geometry.attributes.position.count;i++) {
  const world=mesh.localToWorld(mesh.getVertexPosition(i,new THREE.Vector3()));
  const native=[world.x-.65,-world.z,world.y];
  const matches=descriptor.pattern.verticesNativeM.map((p,index)=>({index,error:Math.hypot(...p.map((x,k)=>x-native[k]))})).filter(r=>r.error<2e-6);
  if(matches.length!==1)throw Error('Ambiguous/unmapped native pattern vertex');
  const nativeID=matches[0].index; maximumRestError=Math.max(maximumRestError,matches[0].error);
  const weights=Array.from({length:4},(_,k)=>({joint:mesh.skeleton.bones[mesh.geometry.attributes.skinIndex.array[i*4+k]].name,weight:mesh.geometry.attributes.skinWeight.array[i*4+k]})).filter(w=>w.weight>0);
  const expected=descriptor.pattern.weights[nativeID].map(([joint,weight])=>({joint:THREE.PropertyBinding.sanitizeNodeName(joint),weight}));
  for(const w of weights)if(Math.abs(w.weight-(expected.find(e=>e.joint===w.joint)?.weight??0))>1e-7)throw Error('Exported pattern weight changed');
  rows.push({exportedRow:i,nativePatternVertexID:nativeID,restErrorM:matches[0].error,pinWeight:descriptor.pattern.sewnAnchorWeights[nativeID],weights});
}
const triangles=[];
const sorted = ids=>ids.slice().sort((a,b)=>a-b).join(',');
const lookup=new Map(descriptor.pattern.triangleVertexIDs.map((t,i)=>[sorted(t),i]));
for(let ti=0;ti<mesh.geometry.index.count/3;ti++) {
  const exportedRows=[0,1,2].map(k=>mesh.geometry.index.getX(3*ti+k)), nativeIDs=exportedRows.map(i=>rows[i].nativePatternVertexID), nativeTriangleID=lookup.get(sorted(nativeIDs));
  if(!Number.isInteger(nativeTriangleID))throw Error('Unmapped local triangle');
  triangles.push({exportedTriangleID:ti,exportedRows,nativeTriangleID,nativePatternVertexIDs:nativeIDs});
}
if(new Set(rows.map(r=>r.nativePatternVertexID)).size!==288||new Set(triangles.map(t=>t.nativeTriangleID)).size!==528)throw Error('Incomplete ancestry');
const report={status:'UNACCEPTED valid-rest sleeve export ancestry; actual collision response must be implemented separately',
  sleeveGLBSHA256:sha(fs.readFileSync(file)),parent05GLBSHA256:sha(fs.readFileSync(parentFile)),descriptorSHA256:sha(fs.readFileSync(descriptorFile)),verifierSHA256:sha(fs.readFileSync(new URL(import.meta.url))),
  actualGLTFLoader:true,threeRevision:THREE.REVISION,all51JointNamesParentsAndInverseBindsExact:true,inverseBindMaximumError:bindError,
  exportedVertices:rows.length,nativeVertices:288,UVSeamSplitRows:rows.length-288,triangles:triangles.length,maximumLoadedRestVsNativeM:maximumRestError,
  matrixWorldColumnMajor:mesh.matrixWorld.toArray(),bindMatrixColumnMajor:mesh.bindMatrix.toArray(),bindMatrixInverseColumnMajor:mesh.bindMatrixInverse.toArray(),jointOrder:mesh.skeleton.bones.map(b=>b.name),rows,triangleAncestry:triangles,
  limits:['This rest export does not contain Blender cloth simulation or guarantee arbitrary poses.','No full garment, inter-garment, fit/art/contact or mobile pass.']};
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({rows:rows.length,triangles:triangles.length,bindError,maximumRestError}));
