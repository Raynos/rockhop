/** CPU fixtures only: no native, optimizer, construction or substitute proof. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {ROOT,arrays,pinned,filePin} from '../selected-boot-surface67/io.mjs';
import {SourceTree,faceCensus} from '../selected-boot-surface67/surface.mjs';
import {normalCensus,fanClosure} from '../selected-boot-closure62/closure.mjs';
import {failureCenters} from '../selected-boot-surface67/closure.mjs';
import {fanRetention} from '../selected-boot-fan59/construct.mjs';
import {rayParity} from './preflight.mjs';
import {ANCESTRY,validateRightMetadata,verifyRepair,readRight} from './construct.mjs';

const HERE=path.dirname(fileURLToPath(import.meta.url)),evidence=path.join(ROOT,'docs/evidence/rider-rebuild/selected-boot-family75');
const findingPin=filePin(path.join(evidence,'right-repair.json')),finding=JSON.parse(pinned(findingPin).data);
const preflight=JSON.parse(pinned(finding.preflight).data),source=JSON.parse(pinned(preflight.source).data),x=arrays(source.arrays);
const mesh={positions:x.RPositions,triangles:Uint32Array.from(x.RTriangles),normals:x.RNormals};
const seed=arrays(finding.protection),prior=arrays(finding.priorQualifiedProtection),groups=[];
ANCESTRY.forEach(pinned);
function pass(name,details){groups.push({name,passed:true,...details});}

// This in-memory schema specimen tests rejection boundaries only. It is never
// saved as a census, never passed to readRight and never claims native execution.
const n=305453,f=610934,loops=3*f,layout={};
for(const [key,dtype,shape] of [['positions','<f4',[n,3]],['triangles','<i4',[f,3]],['triangleLoopIds','<i4',[f,3]],
 ['vertexNormals','<f4',[n,3]],['cornerNormals','<f4',[loops,3]],['namedWeights','<f4',[n,3]],['faceMaterialIds','<i4',[f]],['uvLayer0','<f4',[loops,2]]])layout[key]={dtype,shape};
const specimen={status:'ACTUAL_RIGHT_NATIVE_SOURCE_CENSUS_COMPLETE_UNACCEPTED',acceptedArt:false,sourceObject:'ActualSelectedBoot.R',
 sourceWitnessExact:true,sourceInputBytesUnchanged:true,sourceMatchesActualPreflightGeometry:true,recipeSHA256:filePin(path.join(HERE,'census.py')).sha256,
 native70:source.native70,production70:source.production70,qualifiedLeftReopen:{sha256:'db3f0dbe7a3d610da1d2df8123220a5bc7ebf95d4d3f87157defaf3604c9c3fa'},
 prepareRecipe:source.recipe,sourceNormals:'Native vertex normals read from pinned native70; no CPU proxy substitution.',sourceVertices:n,sourceTriangles:f,
 sourceArrayPackage:{groupNames:['DEF-foot.R','DEF-toe.R','DEF-shin.R.001'],uvLayerNames:['Exact selected raw corner UV copied with Blender V flip'],layout}};
validateRightMetadata(specimen);
const mutations=[v=>v.status='PARTIAL_RIGHT_NATIVE_SOURCE_INTAKE',v=>v.acceptedArt=true,v=>v.sourceObject='ActualSelectedBoot.L',
 v=>v.sourceWitnessExact=false,v=>v.sourceInputBytesUnchanged=false,v=>v.sourceMatchesActualPreflightGeometry=false,
 v=>v.native70.sha256='0'.repeat(64),v=>v.production70.sha256='0'.repeat(64),v=>v.recipeSHA256='0'.repeat(64),
 v=>v.sourceNormals='CPU geometric proxy',v=>v.sourceArrayPackage.groupNames[0]='DEF-foot.L',
 v=>v.sourceArrayPackage.layout.namedWeights.shape=[n,2],v=>v.sourceArrayPackage.layout.positions.dtype='<f8',
 v=>v.sourceArrayPackage.uvLayerNames=[],v=>delete v.sourceArrayPackage.layout.cornerNormals];
for(const mutate of mutations){const changed=structuredClone(specimen);mutate(changed);assert.throws(()=>validateRightMetadata(changed));}
assert.throws(()=>readRight(path.join(ROOT,'harness/out/rider-rebuild/selected-boot-native70/native01/production.json'),source.production70.sha256));
assert.throws(()=>pinned({...findingPin,sha256:'0'.repeat(64)}));
pass('Right intake admits exact structure and rejects side, field, proof, dtype and path drift',{mutationsRejected:mutations.length+2,actualNativeCensusAvailable:false});

// All source identities are cyclic opposite, but positions differ on every ID.
const cyclic=tri=>{const i=tri.indexOf(Math.min(...tri));return [tri[i],tri[(i+1)%3],tri[(i+2)%3]].join(',');};
let different=0;
for(let i=0;i<n;i++)if(x.RPositions[3*i]!==-x.LPositions[3*i]||x.RPositions[3*i+1]!==x.LPositions[3*i+1]||x.RPositions[3*i+2]!==x.LPositions[3*i+2])different++;
for(let i=0;i<3*f;i+=3)assert.equal(cyclic(Array.from(x.RTriangles.subarray(i,i+3))),cyclic(Array.from(x.LTriangles.subarray(i,i+3)).reverse()));
assert.equal(different,n);assert.notEqual(cyclic(Array.from(x.RTriangles.subarray(0,3))),cyclic(Array.from(x.LTriangles.subarray(0,3))));
const current=normalCensus(mesh,x.RCandidateOriginalTriangles);assert.deepEqual(current,preflight.sides.R.vertex);
assert.deepEqual(current.failures.map(row=>row.originalVertexId),[13802,89501,97137,117542]);
pass('Actual opposite source winding and all four right vertex failures reproduced',{separatelyAuthoredVertices:different,vertexFailures:current.failingVertices});

const tree=new SourceTree(mesh.positions,mesh.triangles),geometry=arrays(finding.actualFailureGeometry);
const failedIndices=geometry.targetOriginalVertexIds,failed=faceCensus(mesh,failedIndices,tree).report;
assert.equal(failed.failingFaces,28);assert.equal(failed.samples,28);
for(let i=0;i<28;i++){
 const old=preflight.sides.R.face.failures[i],row=failed.failures[i];
 assert.equal(geometry.targetFaceIds[i],old.targetFaceId);assert.equal(row.normalDot,old.normalDot);assert.equal(row.distanceM,old.distanceM);
 assert.deepEqual(row.bearingSourceFaceIds,old.bearingSourceFaceIds);assert.equal(row.exactInheritedSourceFace,false);
 for(let c=0;c<3;c++)for(let d=0;d<3;d++)assert.equal(geometry.targetCoordinates[i*9+c*3+d],mesh.positions[3*failedIndices[3*i+c]+d]);
}
for(let i=0;i<geometry.bearingOriginalVertexIds.length;i++)for(let d=0;d<3;d++)assert.equal(geometry.bearingCoordinates[3*i+d],mesh.positions[3*geometry.bearingOriginalVertexIds[i]+d]);
pass('Every actual right failed face and global geometric bearing reproduced',{faceFailures:failed.failingFaces,minimumNormalDot:failed.minimumNormalDot,maximumDistanceM:failed.maximumDistanceM});

verifyRepair(mesh,seed,prior,current,preflight.sides.R.face);
assert.equal(failureCenters(current,preflight.sides.R.face).length,146);assert.equal(seed.centerOriginalVertexIds.length,1253);assert.equal(seed.requiredSourceFaceIds.length,5511);
const incomplete=fanClosure(mesh,seed.centerOriginalVertexIds.filter(v=>v!==finding.addedCenters[0]));
assert.throws(()=>verifyRepair(mesh,incomplete,prior,current,preflight.sides.R.face));
const required=new Uint32Array(seed.requiredSourceFaceIds.length*3);
seed.requiredSourceFaceIds.forEach((id,i)=>required.set(mesh.triangles.subarray(3*id,3*id+3),3*i));
assert(fanRetention(mesh,required,seed).passed);
const flipped=required.slice();[flipped[0],flipped[1]]=[flipped[1],flipped[0]];assert(!fanRetention(mesh,flipped,seed).passed);
assert(!fanRetention(mesh,required.slice(3),seed).passed);
pass('Exact monotone union retains every required oriented right fan; deletion and reversal rejected',{priorCenters:1120,addedCenters:133,totalCenters:1253,requiredFaces:5511,mutationsRejected:3});

const tetra=new SourceTree(new Float32Array([0,0,0,1,0,0,0,1,0,0,0,1]),new Uint32Array([0,2,1,0,1,3,0,3,2,1,2,3]));
for(const axis of [0,2]){
 assert.deepEqual(rayParity(tetra,[.1,.2,.3],axis),{inside:true,boundary:false,crossings:1});
 assert.deepEqual(rayParity(tetra,[1.1,1.2,1.3],axis),{inside:false,boundary:false,crossings:0});
 assert(rayParity(tetra,[0,0,0],axis).boundary);
}
for(const side of ['L','R']){
 const r=finding.outsideFootDomainClassification[side],all=new Set(preflight.sides[side].actualNative02FootEnclosure.outsideOriginalBodyVertexIds);
 const partition=[...r.aboveOriginal107mmCoverageOriginalIds,...r.atOrBelowOriginal107mmCoverageOriginalIds];
 assert.equal(new Set(partition).size,all.size);assert(partition.every(v=>all.has(v)));assert.equal(r.atOrBelowOriginal6mmSoleProtectionOriginalIds.length,0);
}
pass('Two-axis parity handles interior, exterior and boundary; collar/domain evidence stays explicitly partitioned',{rightOutside:291,rightAboveEntireSource:6,rightAtOrBelow107mm:220,soleBandOutside:0});

const report={status:'SOURCE_AND_CPU_FIXTURES_PASSED_NATIVE_CENSUS_AND_CONSTRUCTION_NOT_RUN',passed:groups.length,groups,
 recipes:['prepare.py','preflight.mjs','diagnose.py','census.py','construct.mjs','check.mjs'].map(name=>filePin(path.join(HERE,name))),
 actualFinding:findingPin,actualPreflight:finding.preflight,optimizerCalls:0,nativeExecuted:false,acceptedArt:false};
fs.writeFileSync(path.join(evidence,'checks.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,passed:groups.length}));
