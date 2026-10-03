/** Independent zero-default successor admission; geometry remains the frozen04 field. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { Vector3 } from 'three';
import { loadRigAt } from '../../../src/render/hero/gltfTestUtils.ts';
import { prepareHero } from '../../../src/render/hero/lod.ts';
import { GltfRider } from '../../../src/render/hero/GltfRider.ts';
import { readGlbChunks } from './metadata.mjs';
const [oldFile,newFile,outFile]=process.argv.slice(2);assert(outFile&&!fs.existsSync(outFile));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');const pins={};
const pin=(file,expected)=>{const b=fs.readFileSync(file),s=sha(b);if(expected)assert.equal(s,expected);pins[file]={sha256:s,bytes:b.length};return b;};
const before=readGlbChunks(pin(oldFile,'ac64e79a6a2e7595a01a2da9d714df78ee7058d9a22dcc5ecf24915f8085dfdd'));
const after=readGlbChunks(pin(newFile,'ecc3bb87b2b9ff934c20345e47b422665f676a23f26a84622b6ec42cc0d42181'));
const masterFile=path.join(path.dirname(newFile),'rider.blend');pin(masterFile,'f9aa4030ddb18323dcd7fdcbdfc52bbb062f3b2a39a7573a78eddf3383442715');
assert(before.bin.equals(after.bin));const expected=structuredClone(before.json);
assert.deepEqual(expected.meshes[6].weights,[1,1,1]);expected.meshes[6].weights=[0,0,0];
assert.equal(expected.nodes[59].extras.rockhopAppearanceCandidate,'unaccepted appearance04 sewn hood and coherent wardrobe');
expected.nodes[59].extras.rockhopAppearanceCandidate='unaccepted appearance05 zero-rest defaults';assert.deepEqual(after.json,expected);
const controllerFile=path.join(path.dirname(newFile),'source-normals-controller.json'),controller=JSON.parse(pin(controllerFile));
const priorController=JSON.parse(pin(path.join(path.dirname(oldFile),'source-normals-controller.json'),'27f4e3ff5c8760a036052edddba44509ae650e3890a18ea8ef502e771de75ec0'));
assert.deepEqual(controller.configs,priorController.configs);assert.deepEqual(controller.candidateMeshNames,priorController.candidateMeshNames);
assert.equal(controller.candidateGLBSHA256,pins[newFile].sha256);assert.equal(controller.candidateMasterSHA256,pins[masterFile].sha256);assert.equal(controller.poseDriverSHA256,priorController.poseDriverSHA256);
const g=await loadRigAt(pathToFileURL(path.resolve(newFile)),true);g.scene.updateMatrixWorld(true);const closures=[];
g.scene.traverse(m=>{if(!m.isSkinnedMesh)return;m.skeleton.update();const p=m.geometry.attributes.position,v=new Vector3();let maxResidualM=0;
  assert((m.morphTargetInfluences??[]).every(v=>v===0));for(let i=0;i<p.count;i++){m.getVertexPosition(i,v).applyMatrix4(m.matrixWorld);maxResidualM=Math.max(maxResidualM,Math.hypot(v.x-p.getX(i),v.y-p.getY(i),v.z-p.getZ(i)));}
  assert(maxResidualM<2e-6);closures.push({mesh:m.name,vertices:p.count,defaultInfluences:m.morphTargetInfluences??[],maxResidualM});});assert.equal(closures.length,8);
await prepareHero(g);const rider=new GltfRider(g,{complete(){}}),parts=[];
rider.scene.traverse(m=>{if(!m.isSkinnedMesh)return;assert((m.morphTargetInfluences??[]).every(v=>v===0));const sleeve=rider.sleeveGeometry.find(s=>s.mesh===m);assert(sleeve&&sleeve.authored===sleeve.riding);parts.push({mesh:m.name,vertices:m.geometry.attributes.position.count,targets:m.morphTargetDictionary??{},defaultInfluences:m.morphTargetInfluences??[],authoredEqualsRiding:true});});
const cloth=controller.configs.find(c=>c.region==='cloth');assert.equal(parts.filter(m=>cloth.keys.every(k=>Object.hasOwn(m.targets,k))).length,2);
const report={status:'UNACCEPTED_APPEARANCE05_ZERO_DEFAULT_SOURCE_AND_LOADER_CHECKED',pins,
  codeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),exactEntireBIN:true,BINSHA256:sha(after.bin),
  exactOtherJSON:true,JSONExceptions:['mesh6 weights [1,1,1] -> [0,0,0]','node59 extras.rockhopAppearanceCandidate successor label'],
  originalControllerConfigsAndMeshNamesExact:true,closures,runtime:parts,
  limits:['Static zero-default/export/normal loader/clone verification only. No new native motion parity, appearance, supported contact or device acceptance.',
    'All geometry, source normals, UVs, skinning, indices, morph vectors, images and51bind fields are the exact unchanged04 BIN/JSON.',
    'Node images omitted in memory; source bytes inherit verified04 fidelity. Private controller still required for rig-angle coupling.']};
fs.mkdirSync(path.dirname(outFile),{recursive:true});fs.writeFileSync(outFile,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,controllerSHA256:pins[controllerFile].sha256,maxResidualM:Math.max(...closures.map(c=>c.maxResidualM)),runtimeClothParts:2}));
