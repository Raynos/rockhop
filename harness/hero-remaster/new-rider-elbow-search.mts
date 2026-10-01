/** PRIVATE CPU-only bounded elbow estimate search. No GPU, rendering or asset/code mutations.
 * pnpm exec tsx harness/hero-remaster/new-rider-elbow-search.mts [--out=<evidence>]
 * Dense finite samples do not establish continuous or played deformation/contact acceptance.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { gzipSync } from 'node:zlib';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { deriveContactAdapter } from './new-rider-contact-adapter.mjs';
import { makeRiderRigPose, riderPoseAtLean } from '../../src/core/riderGeometry';
type V3=[number,number,number];
type Side='L'|'R';
type Adapter=ReturnType<typeof deriveContactAdapter>;
interface ContactWitness{nativeSide:Side;runtimeSide:Side;adapter:Adapter}
interface Profile{id:string;kind:string;lean:number|null;hips:[number,number];torsoRadians:number;physicalCOM:{x:number;y:number;z:number}}
const vector=(v:readonly number[])=>{assert(v.length===3&&v.every(Number.isFinite));return new THREE.Vector3(v[0],v[1],v[2]);};
const sha=(p:string)=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
function reach(d:number,a:number,b:number){
 assert([d,a,b].every(Number.isFinite)&&a>0&&b>0);
 const min=Math.abs(a-b),max=a+b,triangle=Math.min(d-min,max-d),safe=Math.min(d-min-.02,.995*max-d);
 return{d,a,b,min,max,triangle,safe,shortfall:Math.max(0,-triangle)};
}
function main(){
 const base=path.resolve('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01');
 const out=path.resolve(process.argv.find(s=>s.startsWith('--out='))?.slice(6)??path.join(base,'elbow-search03'));fs.mkdirSync(out,{recursive:true});
 const previousPath=path.join(base,'joint-search02/report.json'),metadataPath=path.join(base,'contact-adapter01/adapter-metadata.json');
 const sources=[previousPath,metadataPath,path.join(base,'native-landmarks/cuff-runtime-frames.json'),path.resolve('harness/hero-remaster/new-rider-contact-adapter.mts'),path.resolve('harness/hero-remaster/new-rider-elbow-search.mts'),path.resolve('src/core/riderGeometry.ts'),'/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind01/rider.glb'].map(p=>({path:p,sha256:sha(p)}));
 const previous=JSON.parse(fs.readFileSync(previousPath,'utf8')) as {profiles:Profile[];bodyBind01Observed:{sha256:string}};
 const metadata=JSON.parse(fs.readFileSync(metadataPath,'utf8'))as{hands:ContactWitness[];feet:ContactWitness[]};
 const R=JSON.parse(fs.readFileSync(sources[2]!.path,'utf8')).rotationSourceBlenderToRuntime as number[][];
 const transport=(p:V3)=>vector(R.map(row=>row.reduce((a,c,i)=>a+c*p[i]!,0)));
 const contacts=metadata.hands.map(h=>{const f=metadata.feet.find(f=>f.runtimeSide===h.runtimeSide)!;
  const hand=deriveContactAdapter(h.adapter.input),foot=deriveContactAdapter(f.adapter.input);
  assert(vector(hand.targetJoint).distanceTo(vector(h.adapter.targetJoint))<1e-12&&vector(foot.targetJoint).distanceTo(vector(f.adapter.targetJoint))<1e-12);
  return{side:h.runtimeSide,nativeSide:h.nativeSide,hand,foot};
 });
 const coarse=previous.profiles;
 assert(coarse.length===87);
 const dense:Profile[]=Array.from({length:1001},(_,i)=>{const lean=-1+i/500,p=riderPoseAtLean(lean,makeRiderRigPose());return{id:`dense-${i.toString().padStart(4,'0')}`,kind:'dense-shared-lean',lean,hips:[p.hips.x,p.hips.y],torsoRadians:p.torsoAngle,physicalCOM:{...p.com}};});
 const physicalSnapshot=JSON.stringify({coarse,dense});
 const fixed={shoulder:{halfX:.205,y:.02,z:1.44},hip:{halfX:.105,y:.015,z:.945},pelvis:{y:.015,z:.925},knee:{halfX:.145,y:0,z:.50},ankle:{halfX:.18,y:.045,z:.115}};
 const columns=['profileIndex','runtimeSideL0R1','limbHand0Foot1','distanceM','segment1M','segment2M','triangleMinM','triangleMaxM','minimumTriangleMarginM','minimumSafeMarginM','shortfallM'];
 const summaries:ReturnType<typeof evaluateCandidate>['summary'][]=[];
 const coarseRows:unknown[]=[],denseRows:unknown[]=[];
 function evaluateCandidate(id:string,absX:number,z:number,includeDenseRows=false){
  const lengths=contacts.map(c=>{const nativeSign=c.nativeSide==='L'?1:-1,shoulder=transport([nativeSign*.205,.02,1.44]),elbow=transport([nativeSign*absX,.025,z]);
   return{side:c.side,upperArm:shoulder.distanceTo(elbow),forearm:elbow.distanceTo(vector(c.hand.input.sourceJoint)),
    thigh:transport([nativeSign*.105,.015,.945]).distanceTo(transport([nativeSign*.145,0,.5])),
    shin:transport([nativeSign*.145,0,.5]).distanceTo(transport([nativeSign*.18,.045,.115]))};});
  function evaluateSet(profiles:Profile[],retainRows:boolean){
   let triangle=Infinity,safe=Infinity,armTriangle=Infinity,armSafe=Infinity,footTriangle=Infinity,footSafe=Infinity,shortfall=0;
   let minTriangleFrame:unknown=null,minSafeFrame:unknown=null,minArmSafeFrame:unknown=null,minFootSafeFrame:unknown=null;
   const rows:number[][]=[];
   for(const[i,p]of profiles.entries()){
    const axis=new THREE.Vector3(Math.cos(p.torsoRadians),Math.sin(p.torsoRadians),0),forward=new THREE.Vector3(Math.sin(p.torsoRadians),-Math.cos(p.torsoRadians),0);
    const physicalHip=new THREE.Vector3(p.hips[0],p.hips[1],0),pelvis=physicalHip.clone().addScaledVector(axis,-.02);
    for(const c of contacts){
     const sign=c.side==='L'?1:-1,l=lengths.find(l=>l.side===c.side)!;
     const hip=pelvis.clone().addScaledVector(axis,.02).add(new THREE.Vector3(0,0,sign*.105));
     assert(hip.clone().add(new THREE.Vector3(0,0,-sign*.105)).distanceTo(physicalHip)<1e-12);
     const shoulder=pelvis.clone().addScaledVector(axis,1.44-.925).addScaledVector(forward,-.005).add(new THREE.Vector3(0,0,sign*.205));
     const hand=reach(shoulder.distanceTo(vector(c.hand.targetJoint)),l.upperArm,l.forearm),foot=reach(hip.distanceTo(vector(c.foot.targetJoint)),l.thigh,l.shin);
     for(const[k,r]of [['hand',hand],['foot',foot]]as const){
      const record={profileId:p.id,profileIndex:i,lean:p.lean,hips:p.hips,torsoRadians:p.torsoRadians,side:c.side,limb:k,distanceM:r.d,segmentLengthsM:[r.a,r.b],triangleMarginM:r.triangle,safeMarginM:r.safe};
      if(r.triangle<triangle){triangle=r.triangle;minTriangleFrame=record;}
      if(r.safe<safe){safe=r.safe;minSafeFrame=record;}
      shortfall=Math.max(shortfall,r.shortfall);
      if(k==='hand'){armTriangle=Math.min(armTriangle,r.triangle);if(r.safe<armSafe){armSafe=r.safe;minArmSafeFrame=record;}}
      else{footTriangle=Math.min(footTriangle,r.triangle);if(r.safe<footSafe){footSafe=r.safe;minFootSafeFrame=record;}}
      if(retainRows)rows.push([i,c.side==='L'?0:1,k==='hand'?0:1,r.d,r.a,r.b,r.min,r.max,r.triangle,r.safe,r.shortfall]);
     }
    }
   }
   return{minimumTriangleMarginM:triangle,minimumSafeMarginM:safe,minimumArmTriangleMarginM:armTriangle,minimumArmSafeMarginM:armSafe,
    minimumFootTriangleMarginM:footTriangle,minimumFootSafeMarginM:footSafe,worstShortfallM:shortfall,allTriangleReachable:shortfall<1e-12,
    allSafe:safe>=0,armsSafe:armSafe>=0,minTriangleFrame,minSafeFrame,minArmSafeFrame,minFootSafeFrame,rows};
  }
  const a=evaluateSet(coarse,true),b=evaluateSet(dense,includeDenseRows);
  const{rows:coarseData,...coarseSummary}=a,{rows:denseData,...denseSummary}=b;
  return{summary:{id,elbowAbsX:absX,elbowY:.025,elbowZ:z,lengths,coarse:coarseSummary,dense:denseSummary},coarseData,denseData};
 }
 let candidateIndex=0;
 for(let xStep=0;xStep<=8;xStep++)for(let zStep=0;zStep<=12;zStep++){
  const x=Number((.28+xStep*.0025).toFixed(4)),z=Number((1.13+zStep*.0025).toFixed(4));
  const c=evaluateCandidate(`elbow-${(++candidateIndex).toString().padStart(3,'0')}`,x,z,true);
  summaries.push(c.summary);coarseRows.push({candidateId:c.summary.id,rows:c.coarseData});denseRows.push({candidateId:c.summary.id,rows:c.denseData});
 }
 const ordered=[...summaries].sort((a,b)=>b.dense.minimumArmSafeMarginM-a.dense.minimumArmSafeMarginM||b.coarse.minimumArmSafeMarginM-a.coarse.minimumArmSafeMarginM);
 const best=ordered[0]!,bestFull=evaluateCandidate(best.id,best.elbowAbsX,best.elbowZ,true);
 const baseline=evaluateCandidate('frozen-joint-search02-elbow',.285,1.145,true);
 const after=sources.map(s=>({path:s.path,sha256:sha(s.path)}));assert(sources.every((s,i)=>s.sha256===after[i]!.sha256));
 assert(JSON.stringify({coarse,dense})===physicalSnapshot,'Physical profile/COM mutation');
 const summary={candidateCount:summaries.length,coarseProfiles:87,denseLeanSamples:1001,totalEvaluatedLimbTargets:summaries.length*(87+1001)*4,
  coarseAndDenseTriangleFeasible:summaries.filter(s=>s.coarse.allTriangleReachable&&s.dense.allTriangleReachable).length,
  coarseAndDenseArmsSafe:summaries.filter(s=>s.coarse.armsSafe&&s.dense.armsSafe).length,
  coarseAndDenseAllLimbsSafe:summaries.filter(s=>s.coarse.allSafe&&s.dense.allSafe).length,
  bestArmMathematicalSeed:best,frozenElbowBaseline:baseline.summary};
 const report={schema:'rockhop.private-new-elbow-search.v1',status:'Bounded numerical authoring evidence; no rig/source or gameplay acceptance',sources,sourceHashesAfter:after,sourcesUnchanged:true,
  bounds:{elbowAbsX:{min:.28,max:.30,step:.0025},elbowZ:{min:1.13,max:1.16,step:.0025},elbowY:.025,fixed,
   authority:'Parent estimates based on actual cloth surface bounds at Z1.15; hidden elbow joint still estimated'},
  sourceBind01Hash:previous.bodyBind01Observed.sha256,contactsUnchanged:true,physicalPoseAndCOMUnchanged:true,summary,candidates:summaries,
  limits:['All 1001 lean samples are finite-grid points, not mathematical proof over continuous domain','Only source elbow estimates vary; NEW geometry, hip/shoulder/knee/ankle/source bind and physics untouched','All-limb safe margin cannot improve beyond frozen leg margin by changing elbows alone','Palm/sole contact witnesses remain provisional and do not prove wrapping or surface contact','NEW visual joint lengths differ from physical mass map; independent rendered COM agreement remains unmeasured','No played skin/cuff deformation, Garage, standing-to-sitting or engine comparison from numerical helper','Best numerical seed is not automatic anatomical choice; parent judges actual garment boundaries and motion']};
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
 fs.writeFileSync(path.join(out,'coarse-all-candidate-frames.json'),JSON.stringify({units:'metres',columns,profiles:coarse,candidates:coarseRows})+'\n');
 const denseBytes=Buffer.from(JSON.stringify({units:'metres',columns,profiles:dense,candidates:denseRows})+'\n');
 const compressed=gzipSync(denseBytes,{level:9});
 fs.writeFileSync(path.join(out,'dense-all-candidate-frames.json.gz'),compressed);
 fs.writeFileSync(path.join(out,'dense-storage.json'),JSON.stringify({file:'dense-all-candidate-frames.json.gz',format:'gzip UTF-8 JSON; lossless numerical values',uncompressedBytes:denseBytes.length,compressedBytes:compressed.length,uncompressedSHA256:crypto.createHash('sha256').update(denseBytes).digest('hex'),compressedSHA256:crypto.createHash('sha256').update(compressed).digest('hex'),candidateCount:summaries.length,profilesPerCandidate:1001,limbsPerProfile:4},null,2)+'\n');
 fs.writeFileSync(path.join(out,'dense-best-and-baseline-frames.json'),JSON.stringify({units:'metres',columns,profiles:dense,candidates:[{candidateId:best.id,rows:bestFull.denseData},{candidateId:baseline.summary.id,rows:baseline.denseData}]})+'\n');
 console.log(JSON.stringify({status:report.status,sourcesUnchanged:true,summary},null,2));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)main();
