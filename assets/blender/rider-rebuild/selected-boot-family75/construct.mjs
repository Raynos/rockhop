/** Right intake only; unchanged37/59/62/67 construction and all-failure closure. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath,pathToFileURL } from 'node:url';
import { ROOT,POLICY,sha,pinned,fieldsAndAttributes,topology,compactCandidate,writeArrays } from '../selected-production-constructor37/construct.mjs';
import { protectFans,fanRetention } from '../selected-boot-fan59/construct.mjs';
import { normalCensus,fanClosure } from '../selected-boot-closure62/closure.mjs';
import { SourceTree,faceCensus } from '../selected-boot-surface67/surface.mjs';
import { addFailures,failureCenters } from '../selected-boot-surface67/closure.mjs';
import { arrays } from '../selected-boot-surface67/io.mjs';

const HERE=path.dirname(fileURLToPath(import.meta.url)),BASE=path.join(ROOT,'harness/out/rider-rebuild/selected-boot-family75');
export const ANCESTRY=[['selected-production-constructor37/construct.mjs','3d7ec9faa6d8f10140591c4303012f9ecba69c8d7dd6284d3b851052bbe3d741'],
 ['selected-boot-fan59/construct.mjs','ff1328930687d5eb8e7b1c0e7f5961e2fac11f911e88d0e4224fa5e37f1c571f'],
 ['selected-boot-closure62/closure.mjs','89cb51a5d9587a0c6726ab65d7678b9e0072756d16973dab3263e96e849ce294'],
 ['selected-boot-surface67/surface.mjs','4c68f83bfd76f2fedb2cec42de6cfef4ee8d1cca74f3959cffa813521778d07a'],
 ['selected-boot-surface67/closure.mjs','63994435703329695c7a7553cbd64de678a088ae5edba1682f78306caf676c8b'],
 ['selected-boot-surface67/io.mjs','0d16140064776a453ae8cc51e7fef53f7498d9f9ef61e9eacdd9167eebff1e50']]
 .map(([file,sha256])=>({path:'assets/blender/rider-rebuild/'+file,sha256}));
const bytes=a=>Buffer.from(a.buffer,a.byteOffset,a.byteLength);
function inside(file){const rel=path.relative(BASE,path.resolve(file));assert(rel&&!rel.startsWith('..')&&!path.isAbsolute(rel));}

export function validateRightMetadata(census){
  assert.equal(census.status,'ACTUAL_RIGHT_NATIVE_SOURCE_CENSUS_COMPLETE_UNACCEPTED');assert.equal(census.acceptedArt,false);
  assert.equal(census.sourceObject,'ActualSelectedBoot.R');
  for(const key of ['sourceWitnessExact','sourceInputBytesUnchanged','sourceMatchesActualPreflightGeometry'])assert.equal(census[key],true);
  assert.equal(census.recipeSHA256,sha(fs.readFileSync(path.join(HERE,'census.py'))));
  assert.equal(census.native70.sha256,'ffac10be163895d2ecb76d6552c9e357b86122d522543b7117974884be0ea52c');
  assert.equal(census.production70.sha256,'518fe4ce2f7da86adc176c45d3d3393f70d1b1a4daaae0701ff245baa2681465');
  assert.equal(census.qualifiedLeftReopen.sha256,'db3f0dbe7a3d610da1d2df8123220a5bc7ebf95d4d3f87157defaf3604c9c3fa');
  assert.equal(census.prepareRecipe.sha256,sha(fs.readFileSync(path.join(HERE,'prepare.py'))));
  assert.equal(census.sourceNormals,'Native vertex normals read from pinned native70; no CPU proxy substitution.');
  const pkg=census.sourceArrayPackage,n=census.sourceVertices,f=census.sourceTriangles;
  assert.equal(n,305453);assert.equal(f,610934);assert.deepEqual(pkg.groupNames,['DEF-foot.R','DEF-toe.R','DEF-shin.R.001']);
  const loops=3*f,expected={positions:['<f4',[n,3]],triangles:['<i4',[f,3]],triangleLoopIds:['<i4',[f,3]],
    vertexNormals:['<f4',[n,3]],cornerNormals:['<f4',[loops,3]],namedWeights:['<f4',[n,3]],faceMaterialIds:['<i4',[f]]};
  assert.deepEqual(pkg.uvLayerNames,['Exact selected raw corner UV copied with Blender V flip']);
  pkg.uvLayerNames.forEach((_,i)=>expected['uvLayer'+i]=['<f4',[loops,2]]);
  assert.deepEqual(Object.keys(pkg.layout).sort(),Object.keys(expected).sort());
  for(const [key,[dtype,shape]] of Object.entries(expected)){assert.equal(pkg.layout[key].dtype,dtype);assert.deepEqual(pkg.layout[key].shape,shape);}
}

export function verifyRepair(a,seed,prior,vertex,face){
  const centers=[...new Set([...prior.centerOriginalVertexIds,...failureCenters(vertex,face)])].sort((x,y)=>x-y);
  assert.deepEqual(seed.centerOriginalVertexIds,Uint32Array.from(centers),'Repair must contain precisely prior constraints plus every actual failure fan');
  const expected=fanClosure(a,centers);
  for(const key of Object.keys(expected))assert.deepEqual(expected[key],seed[key],`Actual RIGHT fan seed changed: ${key}`);
}

export function readRight(censusPath,reviewedSHA){
  inside(censusPath);const censusPin={path:path.relative(ROOT,path.resolve(censusPath)),sha256:reviewedSHA};
  const census=JSON.parse(pinned(censusPin).data);validateRightMetadata(census);
  for(const key of ['native70','production70','qualifiedLeftReopen','wholeSourceWitness','rightRepair','prepareRecipe'])pinned(census[key]);
  const witness=JSON.parse(pinned(census.wholeSourceWitness).data);assert(witness.diff.equal&&witness.diff.valueDifferenceCount===0);
  const x=arrays(census.sourceArrayPackage),names=census.sourceArrayPackage.groupNames;
  assert.equal(x.positions.length,3*census.sourceVertices);assert.equal(x.triangles.length,3*census.sourceTriangles);
  const a={positions:x.positions,triangles:Uint32Array.from(x.triangles),normals:x.vertexNormals,fields:x.namedWeights,
    loopIds:x.triangleLoopIds,cornerNormals:x.cornerNormals,materials:x.faceMaterialIds,names,
    uv:census.sourceArrayPackage.uvLayerNames.map((name,i)=>({name,values:x['uvLayer'+i]}))};
  const finding=JSON.parse(pinned(census.rightRepair).data);assert.equal(finding.status,'COMPLETE_RIGHT_LOCAL_REPAIR_SEED_NATIVE_SOURCE_CENSUS_REQUIRED');
  pinned(finding.recipe);pinned(finding.actualFailureGeometry);
  const preflight=JSON.parse(pinned(finding.preflight).data),cpu=JSON.parse(pinned(preflight.source).data),prior=arrays(cpu.arrays);
  pinned(preflight.recipe);pinned(cpu.recipe);
  assert.deepEqual(a.positions,prior.RPositions);assert.deepEqual(a.triangles,Uint32Array.from(prior.RTriangles));
  assert.equal(finding.priorQualifiedLeftConstructor.sha256,'14b4f68aee996befc290a5cfc135029b5a7e5b6933d42398e3eae1a2347eb487');
  const left=JSON.parse(pinned(finding.priorQualifiedLeftConstructor).data);assert.deepEqual(left.finalFanProtection,finding.priorQualifiedProtection);
  const seed=arrays(finding.protection);verifyRepair(a,seed,arrays(finding.priorQualifiedProtection),preflight.sides.R.vertex,preflight.sides.R.face);
  return {census,censusPin,a,finding,seed};
}

async function main(){
  assert.equal(process.argv.length,5,'Usage: node construct.mjs ACTUAL_RIGHT_CENSUS REVIEWED_CENSUS_SHA NEW_OUT');
  ANCESTRY.forEach(pinned);const {census,censusPin,a,finding,seed}=readRight(process.argv[2],process.argv[3]);
  const out=path.resolve(process.argv[4]);inside(out);assert(!fs.existsSync(out));fs.mkdirSync(out,{recursive:true});
  const report={status:'RIGHT_EXISTING67_CONSTRUCTION_INTAKE_UNACCEPTED',acceptedArt:false,sourceObject:'ActualSelectedBoot.R',
    recipeSHA256:sha(fs.readFileSync(fileURLToPath(import.meta.url))),unchangedConstructionAncestry:ANCESTRY,census:censusPin,
    sourceArrayPackage:census.sourceArrayPackage,rightRepair:census.rightRepair,groupNames:a.names,
    numericalPolicy:{targetTriangles:POLICY.targetTriangles,targetErrorM:POLICY.targetErrorM,minimumNormalDot:POLICY.minimumNormalDot,
      maximumSkinWeightL1:POLICY.maximumSkinWeightL1,flags:POLICY.flags,simplifierSHA256:POLICY.simplifierSHA256},
    sceneBudgetPassed:false,allocationPassed:false,bakeCompleted:false,candidateAttempts:0,fixedPoint:{complete:false,iterations:[]}};
  const write=()=>fs.writeFileSync(path.join(out,'constructor.json'),`${JSON.stringify(report,null,2)}\n`);write();
  try{
    const attributes=fieldsAndAttributes(a);assert.equal(attributes.report.rowsNotFloat32Normalized,0);
    report.attributes=attributes.report;report.attributeWeights=attributes.weights;
    const t=topology(a),tree=new SourceTree(a.positions,a.triangles);report.originalTopology=t.report;
    let protection=seed;
    const preflight=JSON.parse(pinned(finding.preflight).data),cpu=JSON.parse(pinned(preflight.source).data),prior=arrays(cpu.arrays).RCandidateOriginalTriangles;
    const initialVertex=normalCensus(a,prior),initialFace=faceCensus(a,prior,tree).report;
    report.nativeNormalInputPriorTopologyCensus={vertex:initialVertex,face:initialFace};
    if(!initialVertex.passed||!initialFace.passed)protection=addFailures(a,seed,initialVertex,initialFace,false).next;
    write();const moduleFile=path.join(ROOT,'node_modules/meshoptimizer/meshopt_simplifier.js');assert.equal(sha(fs.readFileSync(moduleFile)),POLICY.simplifierSHA256);
    const {MeshoptSimplifier}=await import(pathToFileURL(moduleFile).href);await MeshoptSimplifier.ready;assert(MeshoptSimplifier.supported);
    const immutable=[a.positions,a.triangles,a.normals,a.fields,a.loopIds,a.cornerNormals,a.materials,...a.uv.map(u=>u.values),attributes.attributes];
    const hashes=immutable.map(x=>sha(bytes(x)));
    for(;;){
      const iteration=++report.candidateAttempts,stem=`iteration-${String(iteration).padStart(3,'0')}`;
      const row={iteration,status:'RUNNING_UNACCEPTED',fanProtection:protectFans(a,t,protection),protection:writeArrays(path.join(out,stem+'-protection.bin'),protection)};
      report.fixedPoint.iterations.push(row);write();const locksHash=sha(bytes(t.locks));
      const [indices,error]=MeshoptSimplifier.simplifyWithAttributes(a.triangles,a.positions,3,attributes.attributes,attributes.stride,attributes.weights,t.locks,POLICY.targetTriangles*3,POLICY.targetErrorM,POLICY.flags);
      assert.deepEqual(immutable.map(x=>sha(bytes(x))),hashes);assert.equal(sha(bytes(t.locks)),locksHash);assert(Number.isFinite(error)&&error>=0);
      row.returnedOriginalIndices=writeArrays(path.join(out,stem+'-original-indices.bin'),{triangles:indices});
      const candidate=compactCandidate(a,t,indices);row.candidate=writeArrays(path.join(out,stem+'-candidate.bin'),candidate);
      row.targetTriangles=indices.length/3;row.targetVertices=candidate.originalVertexIds.length;row.approximateCombinedErrorM=error;
      row.fanRetention=fanRetention(a,indices,protection);write();assert(row.fanRetention.passed);
      row.vertexNormalCensus=normalCensus(a,indices);assert.equal(row.vertexNormalCensus.verticesExamined,row.targetVertices);
      const face=faceCensus(a,indices,tree);row.faceCentroidCensus=face.report;
      row.faceCentroidArrays=writeArrays(path.join(out,stem+'-face-centroids.bin'),face.arrays);
      const complete=row.vertexNormalCensus.passed&&row.faceCentroidCensus.passed;row.status=complete?'CPU_VERTEX_AND_FACE_FIXED_POINT_UNACCEPTED':'REQUIRES_MORE_ORIGINAL_RIGHT_FANS';write();
      if(complete){
        report.fixedPoint.complete=true;for(const key of ['candidate','returnedOriginalIndices','targetTriangles','targetVertices','fanRetention','vertexNormalCensus','faceCentroidCensus','faceCentroidArrays'])report[key]=row[key];
        report.finalFanProtection=row.protection;report.sourceInputBytesUnchanged=true;report.exactOriginalPositionsAndNamedFields=true;
        report.simplificationTargetIsSoft=true;report.simplificationTargetReached=row.targetTriangles<=POLICY.targetTriangles;
        report.status='RIGHT_CPU_COMPACT_CANDIDATE_NATIVE_PAIR_QUALIFICATION_PENDING';
        report.limits='Same67 fixed-point method on genuine right source. Soft8k target is not forced. Original guarded run bounds all iterations. No native pair/bake/scene-allocation or art acceptance; all original native vertex/skin/FOUR/surface gates still required.';
        write();return;
      }
      const added=addFailures(a,protection,row.vertexNormalCensus,row.faceCentroidCensus);
      row.addedOriginalFanCenters=added.addedCenters;row.nextProtectedCenters=added.next.centerOriginalVertexIds.length;protection=added.next;write();
    }
  }catch(error){report.status='REJECTED_RIGHT_CONSTRUCTION_UNACCEPTED';report.failure=String(error.stack||error);write();throw error;}
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await main();
