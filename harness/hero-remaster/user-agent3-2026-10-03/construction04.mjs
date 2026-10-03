/** Frozen construction04 source/loader admission; never an art/contact verdict. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { Vector3 } from 'three';
import { loadRigAt } from '../../../src/render/hero/gltfTestUtils.ts';
import { prepareHero } from '../../../src/render/hero/lod.ts';
import { GltfRider } from '../../../src/render/hero/GltfRider.ts';
import { readGlbChunks } from './metadata.mjs';
import { acc, rig, primitiveSignature, material, image } from './fidelity-utils.mjs';

const [previousFile, candidateFile, outputFile] = process.argv.slice(2);
assert(outputFile && !fs.existsSync(outputFile), 'Need frozen03/frozen04/fresh-report');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const pins = {};
function pin(file, expected) {
  const b = fs.readFileSync(file), actual = sha(b);
  if (expected) assert.equal(actual, expected);
  pins[file] = { sha256: actual, bytes: b.length }; return b;
}
const previous = readGlbChunks(pin(previousFile, '010501c350e43967f98d90b9a4f2562f1171f177a30d520292c404bfb1e19efe'));
const candidate = readGlbChunks(pin(candidateFile, 'ac64e79a6a2e7595a01a2da9d714df78ee7058d9a22dcc5ecf24915f8085dfdd'));
pin(path.join(path.dirname(candidateFile), 'rider.blend'), '82a61f3a4f66ffcda399c4889e420acbee59a21f369b4e1c0cd2ca0f86a4934c');
const controllerFile = path.join(path.dirname(candidateFile), 'source-normals-controller.json');
const controller = JSON.parse(pin(controllerFile));
const priorController = JSON.parse(pin(path.join(path.dirname(previousFile), 'source-normals-controller.json'), '51f5f84afac0232953d1df3cee69c7bff5c09b8b0bffa26345bff0cb05825ff1'));
assert.deepEqual(controller.configs, priorController.configs);
assert.equal(controller.candidateGLBSHA256, pins[candidateFile].sha256);
assert.equal(controller.candidateMasterSHA256, pins[path.join(path.dirname(candidateFile), 'rider.blend')].sha256);
assert.equal(controller.poseDriverSHA256, '8c40c42af362a8d3d8ae44d27a0b07570f600b26adc66d325239413f66c7625b');
assert.deepEqual(rig(candidate), rig(previous)); assert.equal(rig(candidate).names.length, 51);
const preserved = candidate.json.meshes.flatMap(m => {
  const old = previous.json.meshes.find(o => o.name === m.name);
  if (!old) return [];
  assert.equal(m.primitives.length, old.primitives.length);
  m.primitives.forEach((p, i) => {
    assert.deepEqual(primitiveSignature(candidate, p), primitiveSignature(previous, old.primitives[i]));
    assert.deepEqual(material(candidate, p.material), material(previous, old.primitives[i].material));
  });
  return [{ mesh: m.name, exactAttributesIndicesMorphsMaterials: true }];
});
assert.equal(preserved.length, 6, 'All six protected/body/accessory/jeans meshes must remain exact');
const node = candidate.json.nodes.find(n => n.name === controller.candidateMeshNames.cloth);
assert(node && node.skin !== undefined);
const hoodie = candidate.json.meshes[node.mesh]; assert.equal(hoodie.primitives.length, 2);
const clothConfig = controller.configs.find(c => c.region === 'cloth');
assert.deepEqual(hoodie.extras.targetNames, clothConfig.keys);
const oldNode = previous.json.nodes.find(n => n.name === priorController.candidateMeshNames?.cloth)
  ?? previous.json.nodes.find(n => previous.json.meshes[n.mesh]?.extras?.targetNames?.length === 3);
assert(oldNode); const old = previous.json.meshes[oldNode.mesh].primitives[0];
const oldIDs = acc(previous, old.attributes._SOURCE_ID).flat();
const rows = new Map();
for (let i = 0; i < oldIDs.length; i++) rows.set(oldIDs[i], [...(rows.get(oldIDs[i]) ?? []), i]);
const originalAttributes = ['POSITION', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0'];
const oldValues = Object.fromEntries(originalAttributes.map(k => [k, acc(previous, old.attributes[k])]));
const oldTargets = old.targets.map(t => acc(previous, t.POSITION));
const originalsSeen = new Set();
const parts = hoodie.primitives.map((p, primitive) => {
  assert.equal(p.targets.length, 3); assert.equal(p.material, hoodie.primitives[0].material);
  const ids = acc(candidate, p.attributes._SOURCE_ID).flat();
  const values = Object.fromEntries(originalAttributes.map(k => [k, acc(candidate, p.attributes[k])]));
  const targets = p.targets.map(t => acc(candidate, t.POSITION));
  let originalRows = 0, addedRows = 0, maxAddedDeltaM = 0; const seamUVExceptions=[];
  ids.forEach((id, row) => {
    assert(Number.isInteger(id) && id >= 0 && id < 1385);
    if (id < 1250) {
      originalRows++; originalsSeen.add(id);
      const required = primitive === 0 ? originalAttributes : originalAttributes.filter(k=>k!=='TEXCOORD_0');
      const hits = (rows.get(id) ?? []).filter(i => required.every(k =>
        values[k][row].every((v, c) => v === oldValues[k][i][c])));
      assert(hits.length, 'Original source field drift at ID ' + id);
      if(primitive===1&&!hits.some(i=>values.TEXCOORD_0[row].every((v,c)=>v===oldValues.TEXCOORD_0[i][c])))seamUVExceptions.push({sourceID:id,row,newUV:values.TEXCOORD_0[row]});
      assert(hits.some(i => targets.every((t, k) => t[row].every((v, c) => v === oldTargets[k][i][c]))), 'Original corrective position delta drift');
    } else {
      addedRows++; for (const t of targets) maxAddedDeltaM = Math.max(maxAddedDeltaM, Math.hypot(...t[row]));
    }
  });
  assert(maxAddedDeltaM <= .04);
  return { primitive, vertices: ids.length, originalRows, addedRows, maxAddedDeltaM, material: p.material, exactOriginalPositionSkinAndPositionMorphs: true, exactOriginalUV: primitive===0, seamUVExceptions };
});
assert.deepEqual([...originalsSeen].sort((a,b)=>a-b), [...new Set(oldIDs)].sort((a,b)=>a-b));
const triangleIDs=(g,p,ids)=>{const idx=acc(g,p.indices).flat(),out=[];for(let i=0;i<idx.length;i+=3){const t=idx.slice(i,i+3).map(r=>ids[r]);out.push([t,[t[1],t[2],t[0]],[t[2],t[0],t[1]]].map(v=>v.join(',')).sort()[0]);}return out.sort();};
assert.deepEqual(triangleIDs(candidate,hoodie.primitives[0],acc(candidate,hoodie.primitives[0].attributes._SOURCE_ID).flat()),triangleIDs(previous,old,oldIDs));
const cotton = material(candidate, hoodie.primitives[0].material);
assert.equal(cotton.pbrMetallicRoughness.baseColorTexture.index.sha256, '150340262f9eb74ee5e4f5e5a66405209b8238d2b3cd5c7086019b67e3ebb9ea');
assert.equal(cotton.pbrMetallicRoughness.metallicFactor, 0);
assert(Math.abs(cotton.pbrMetallicRoughness.roughnessFactor - .82) < 1e-7);
assert.equal(cotton.extensions.KHR_materials_specular.specularFactor, .25);
const quantized = readGlbChunks(pin(path.join(path.dirname(candidateFile), 'rider.glb'), '413428f04e93b0dd7523d6c9fb96c5e5b990c49c1d974f4cbbec0a12ed605e04'));
assert.deepEqual(quantized.json, candidate.json); assert.equal(quantized.bin.length, candidate.bin.length);
const allowed = new Uint8Array(candidate.bin.length); const normalRanges = [];
for (const m of candidate.json.meshes.filter(m=>m.name.startsWith('Protected '))) {
  const a = candidate.json.accessors[m.primitives[0].attributes.NORMAL], v = candidate.json.bufferViews[a.bufferView];
  assert.equal(a.componentType, 5126); assert.equal(a.type, 'VEC3'); assert(!a.sparse);
  for (let r=0;r<a.count;r++) { const start=(v.byteOffset??0)+(a.byteOffset??0)+r*(v.byteStride??12); allowed.fill(1,start,start+12); }
  normalRanges.push({ mesh:m.name, rows:a.count });
}
let changedBytes=0;
for(let i=0;i<candidate.bin.length;i++) if(candidate.bin[i]!==quantized.bin[i]) { assert.equal(allowed[i],1); changedBytes++; }
const loaded = await loadRigAt(pathToFileURL(path.resolve(candidateFile)), true);
loaded.scene.updateMatrixWorld(true); const closures=[]; const point=new Vector3();
loaded.scene.traverse(m=>{
  if(!m.isSkinnedMesh)return; m.skeleton.update(); const p=m.geometry.attributes.position; let defaultResidualM=0; const defaultWeights=m.morphTargetInfluences?.slice()??[];
  for(let i=0;i<p.count;i++) { m.getVertexPosition(i,point).applyMatrix4(m.matrixWorld); defaultResidualM=Math.max(defaultResidualM,Math.hypot(point.x-p.getX(i),point.y-p.getY(i),point.z-p.getZ(i))); }
  if(m.morphTargetInfluences)m.morphTargetInfluences.fill(0);
  let maxResidualM=0;
  for(let i=0;i<p.count;i++) { m.getVertexPosition(i,point).applyMatrix4(m.matrixWorld); maxResidualM=Math.max(maxResidualM,Math.hypot(point.x-p.getX(i),point.y-p.getY(i),point.z-p.getZ(i))); }
  assert(maxResidualM<2e-6);
  closures.push({mesh:m.name,vertices:p.count,defaultWeights,defaultResidualM,zeroMorphResidualM:maxResidualM});
}); assert.equal(closures.length,8);
await prepareHero(loaded);
const rider = new GltfRider(loaded, { complete() {} });
const runtime=[];
rider.root.updateMatrixWorld(true);
rider.scene.traverse(m=>{
  if(!m.isSkinnedMesh)return;
  let owner=m; while(owner&&!Object.hasOwn(owner.userData,'rockhopRiderSkinConditioned'))owner=owner.parent;
  assert.equal(owner?.userData.rockhopRiderSkinConditioned,1);
  const sleeve=rider.sleeveGeometry.find(i=>i.mesh===m); assert(sleeve && sleeve.authored===sleeve.riding);
  const mats=Array.isArray(m.material)?m.material:[m.material];
  assert(mats.every(mat=>mat.isMeshStandardMaterial&&!mat.isMeshPhysicalMaterial&&mat.side===2));
  runtime.push({mesh:m.name,vertices:m.geometry.attributes.position.count,bones:m.skeleton.bones.length,
    targets:m.morphTargetDictionary??{},conditionedOwner:owner.name,authoredEqualsRiding:true,
    materialNames:mats.map(mat=>mat.name),materialTypes:mats.map(mat=>mat.type),matrixWorld:m.matrixWorld.toArray()});
});
const morphParts=runtime.filter(m=>clothConfig.keys.every(k=>Object.hasOwn(m.targets,k)));
assert.equal(morphParts.length,2, 'Actual loader retains both hoodie primitives');
const report={status:'UNACCEPTED_CONSTRUCTION04_DEFAULT_HOODIE_MORPHS_NONZERO',pins,
  codePins:Object.fromEntries(['construction04.mjs','fidelity-utils.mjs','metadata.mjs'].map(f=>[f,sha(fs.readFileSync(new URL(f,import.meta.url)))])),
  engineCodePins:Object.fromEntries(['src/render/hero/gltfTestUtils.ts','src/render/hero/lod.ts','src/render/hero/GltfRider.ts','src/render/hero/sleeveSkin.ts'].map(f=>[f,sha(fs.readFileSync(f))])),
  complete51BindRestHierarchyExact:true,preserved,cloth:{parts,cotton,originalSourceIDs:originalsSeen.size,
    deliberateExceptions:['New sewn hood/pocket topology, neckline seam UVs and base normals; old hood/flap removed; new coherent mustard image.', 'Original shirt NORMAL deltas and topology ancestry are not certified by this attribute correspondence.']},
  normalOnlyDerivative:{changedBytes,normalRanges,allOtherJSONAndBinaryExact:true},
  defaultControllerDefect:{meshWeights:hoodie.weights,bothRuntimePartsDefaultWeights:closures.filter(c=>c.defaultWeights.length===3).map(c=>c.defaultWeights),maxDefaultRestResidualM:Math.max(...closures.map(c=>c.defaultResidualM)),correctiveInfluencesExplicitlyZeroedForBindCheck:true},
  controller:{sha256:pins[controllerFile].sha256,originalConfigsExact:true,candidateMeshNames:controller.candidateMeshNames,requiredRuntimeClothParts:2,automaticProductionCoupling:false},
  embeddedImages:candidate.json.images.map((_,i)=>image(candidate,i)),closures,runtime,
  limits:['Static source and actual decoder/prepareHero/clone admission only; no moving/native parity, appearance, support or device verdict.',
    'Node loader omits texture references in memory; embedded image bytes and source descriptors checked independently.',
    'Source physical specular factors flatten in normal prepareHero. Both separate hoodie primitives require explicit controller coefficients.',
    'Only parent judges admission/played art; no normal player assets changed. No LOD candidate provided.']};
fs.mkdirSync(path.dirname(outputFile),{recursive:true});fs.writeFileSync(outputFile,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,parts,changedBytes,maximumZeroMorphRestResidualM:Math.max(...closures.map(c=>c.zeroMorphResidualM)),maximumDefaultRestResidualM:Math.max(...closures.map(c=>c.defaultResidualM)),runtimeClothParts:morphParts.length,controllerSHA256:report.controller.sha256}));
