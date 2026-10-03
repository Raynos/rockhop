/** Narrow export preservation receipt for an already rejected attachment trial. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
const [originalFile, trialFile, builderFile, outputFile] = process.argv.slice(2);
assert(outputFile, 'Need original GLB, trial GLB, builder report, fresh output');
assert(!fs.existsSync(outputFile), 'Receipt output must be fresh');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const originalBytes=fs.readFileSync(originalFile), trialBytes=fs.readFileSync(trialFile), reportBytes=fs.readFileSync(builderFile);
const builder=JSON.parse(reportBytes);
assert.equal(hash(originalBytes),'7dd161b36f0e7b26e778f02465be3ded5c437406057c6ca691ddd9cdcb48630a');
assert.equal(hash(trialBytes),builder.GLBSHA256);
assert.equal(builder.status,'REJECTED directed attachment experiment');
const filePins=[
  [originalFile.replace(/\.glb$/,'.blend'),'sourceMasterSHA256'],
  [trialFile.replace(/\.glb$/,'.blend'),'masterSHA256'],
  [path.resolve(path.dirname(builderFile),'../diagnostic02/driver.json'),'driverSHA256'],
  [path.join(path.dirname(path.dirname(trialFile)),'pattern_attachment.py'),'recipeSHA256'],
].map(([file,key])=>{const sha256=hash(fs.readFileSync(file));assert.equal(sha256,builder[key]);return{file,sha256};});
const parse = b => new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'');
const [original,trial]=await Promise.all([parse(originalBytes),parse(trialBytes)]);
original.scene.updateMatrixWorld(true);trial.scene.updateMatrixWorld(true);
function collect(scene){const rows=[];scene.traverse(o=>{if(o.isSkinnedMesh)rows.push(o);});return rows;}
const before=collect(original.scene),after=collect(trial.scene);
assert.equal(before.length,4);assert.equal(after.length,3);assert(!after.some(m=>m.name.includes('boxer')));
function attributeHash(a){
  const values=new Float64Array(a.count*a.itemSize);
  for(let i=0;i<a.count;i++)for(let k=0;k<a.itemSize;k++)values[i*a.itemSize+k]=a.getComponent(i,k);
  return {count:a.count,itemSize:a.itemSize,semanticSHA256:hash(Buffer.from(values.buffer))};
}
const rows=[];
for(const mesh of after){
  const reference=before.find(m=>m.name===mesh.name);assert(reference,'Unexpected export identity');
  const joints=mesh.skeleton.bones.map(b=>b.name);
  assert.equal(joints.length,51);assert.deepEqual(joints,reference.skeleton.bones.map(b=>b.name));
  assert.deepEqual(mesh.skeleton.boneInverses.map(m=>m.toArray()),reference.skeleton.boneInverses.map(m=>m.toArray()));
  assert.deepEqual(mesh.bindMatrix.toArray(),reference.bindMatrix.toArray());
  assert.deepEqual(mesh.matrixWorld.toArray(),reference.matrixWorld.toArray());
  const attributes=Object.fromEntries(Object.entries(mesh.geometry.attributes).map(([key,a])=>[key,attributeHash(a)]));
  const index=attributeHash(mesh.geometry.index);
  if(mesh.name.startsWith('Canonical_')){
    assert.deepEqual(Object.keys(mesh.geometry.attributes).sort(),Object.keys(reference.geometry.attributes).sort());
    for(const [key,a]of Object.entries(attributes))assert.deepEqual(a,attributeHash(reference.geometry.attributes[key]),'Body attribute changed: '+key);
    assert.deepEqual(index,attributeHash(reference.geometry.index),'Body triangle index changed');
  } else {
    assert(!attributes._source_id,'Refined garment must not reuse old vertex identity');
    for(const key of ['_pattern_id','_source_tri','_bary_a','_bary_b'])assert(attributes[key],'Missing ancestry '+key);
  }
  rows.push({mesh:mesh.name,attributes,index,completeJointOrder:joints,bindsAndMeshWorld:'exactly unchanged'});
}
const receipt={status:'REJECTED_ATTACHMENT_EXPORT_PRESERVATION_CHECKED',originalSHA256:hash(originalBytes),trialSHA256:hash(trialBytes),builderReportSHA256:hash(reportBytes),filePins,rows,
  builderReportedReview:builder.review.map(({frame,region,bodyTriangleContactPairs,nonadjacentSelfPairs})=>({frame,region,bodyTriangleContactPairs,nonadjacentSelfPairs})),
  limits:['Native collision/inside/topology claims remain builder-reported; no independent Blender clearance rerun.','Garment topology and vertex IDs change; dense pair counts are not comparable to original coarse counts.','Exact loaded body attributes/index and all51 joint orders/binds/mesh transforms preserved; new ancestry attributes checked for presence only.','Rejected before art/movie review; original played witnesses remain QA baseline; no fit or device acceptance.']};
fs.mkdirSync(path.dirname(outputFile),{recursive:true});fs.writeFileSync(outputFile,JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({status:receipt.status,meshes:rows.map(r=>({name:r.mesh,vertices:r.attributes.position.count,triangles:r.index.count/3}))}));
