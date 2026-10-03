// Verify actual consumed skin weights on byte-identical rest geometry.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
import * as THREE from 'three';
const [baselineFile,candidateFile,attachmentsFile,handoffFile,output]=process.argv.slice(2);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const {loadRigAt}=await import(pathToFileURL(path.resolve('src/render/hero/gltfTestUtils.ts')).href);
async function load(file){const g=await loadRigAt(pathToFileURL(path.resolve(file)),true);g.scene.updateMatrixWorld(true);const meshes=[];g.scene.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o);});if(meshes.length!==1)throw Error('Expected one sleeve');return meshes[0];}
const baseline=await load(baselineFile),candidate=await load(candidateFile),d=JSON.parse(fs.readFileSync(attachmentsFile)),h=JSON.parse(fs.readFileSync(handoffFile));
if(sha(fs.readFileSync(candidateFile))!==d.candidateGLBSHA256||sha(fs.readFileSync(baselineFile))!==h.sleeveRestGLBSHA256)throw Error('Frozen source mismatch');
const hash=a=>sha(Buffer.from(a.buffer,a.byteOffset,a.byteLength));
const fields={};
for(const [name,a] of Object.entries(candidate.geometry.attributes)){
  if(['skinIndex','skinWeight'].includes(name))continue;
  fields[name]=hash(a.array);if(fields[name]!==hash(baseline.geometry.attributes[name].array))throw Error('Rest attribute changed '+name);
}
if(hash(candidate.geometry.index.array)!==hash(baseline.geometry.index.array))throw Error('Indices changed');
if(candidate.skeleton.bones.length!==51||JSON.stringify(candidate.skeleton.bones.map(b=>[b.name,b.parent?.name]))!==JSON.stringify(baseline.skeleton.bones.map(b=>[b.name,b.parent?.name])))throw Error('51joint hierarchy changed');
if(candidate.skeleton.boneInverses.some((m,i)=>m.elements.some((x,j)=>x!==baseline.skeleton.boneInverses[i].elements[j])))throw Error('Bind changed');
const material=m=>({name:m.name,type:m.type,color:m.color.toArray(),metalness:m.metalness,roughness:m.roughness});
if(JSON.stringify(material(candidate.material))!==JSON.stringify(material(baseline.material)))throw Error('Material changed');
candidate.skeleton.update();const rows=[];let maxRest=0,maxWeightError=0,worst=null;
for(let i=0;i<candidate.geometry.attributes.position.count;i++){
  const world=candidate.localToWorld(candidate.getVertexPosition(i,new THREE.Vector3())),native=[world.x-.65,-world.z,world.y];
  const matches=h.pattern.verticesNativeM.map((p,index)=>({index,error:Math.hypot(...p.map((x,j)=>x-native[j]))})).filter(r=>r.error<2e-6);
  if(matches.length!==1)throw Error('Unmapped native source row');
  const id=matches[0].index,expected=Object.fromEntries(Object.entries(d.attachments[id].actualNativeAfterWeights).map(([name,w])=>[THREE.PropertyBinding.sanitizeNodeName(name),w]));
  const weights={};for(let k=0;k<4;k++){const w=candidate.geometry.attributes.skinWeight.array[i*4+k];if(w>0)weights[candidate.skeleton.bones[candidate.geometry.attributes.skinIndex.array[i*4+k]].name]=w;}
  for(const name of new Set([...Object.keys(weights),...Object.keys(expected)])){const e=Math.abs((weights[name]??0)-(expected[name]??0));if(e>maxWeightError){maxWeightError=e;worst={row:i,id,expected,weights,name};}}
  maxRest=Math.max(maxRest,matches[0].error);rows.push({exportedRow:i,nativeVertexID:id,weights,restResidualM:matches[0].error,pinWeightUnchanged:d.attachments[id].sewnAnchorWeightUnchanged});
}
if(maxWeightError>1e-7||new Set(rows.map(r=>r.nativeVertexID)).size!==288||candidate.geometry.index.count/3!==528)throw Error('Weight/ancestry mismatch '+JSON.stringify({maxWeightError,native:new Set(rows.map(r=>r.nativeVertexID)).size,triangles:candidate.geometry.index.count/3,worst}));
const report={status:'UNACCEPTED exactsame-rest actualGLTFLoader body-derived weighting control; actual703tick check pending',
 baselineGLBSHA256:sha(fs.readFileSync(baselineFile)),candidateGLBSHA256:sha(fs.readFileSync(candidateFile)),attachmentsSHA256:sha(fs.readFileSync(attachmentsFile)),verifierSHA256:sha(fs.readFileSync(new URL(import.meta.url))),
 actualGLTFLoader:true,threeRevision:THREE.REVISION,allRestNonSkinAttributesAndIndicesByteExact:fields,all51NamesParentsInverseBindsExact:true,materialExact:material(candidate.material),
 nativeVertices:288,exportedRows:rows.length,triangles:528,maximumRestResidualM:maxRest,maximumActualLoaderWeightError:maxWeightError,rows,
 limits:['New skin weights are consumed by ordinary skinning. No unused attachment table certifies active collision or coupled fold response.','Same pattern/rest/material/bind/pins, no gap or projection-distance change. Agent3 independently checks actual gameplay and root judges moving form.']};
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({rows:rows.length,maxRest,maxWeightError}));
