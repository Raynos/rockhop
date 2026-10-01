/** PRIVATE uniform metre calibration audit. CPU only; no geometry, rig, runtime or physics writes.
 * pnpm exec tsx harness/hero-remaster/new-rider-scale-search.mts [--out=<evidence>]
 * Uniform dimensional changes are reported; unchanged proportions are not an aesthetic pass.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { gzipSync } from 'node:zlib';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { deriveContactAdapter } from './new-rider-contact-adapter.mjs';
import { makeRiderRigPose,riderPoseAtLean } from '../../src/core/riderGeometry';
type V3=[number,number,number];type Side='L'|'R';type Adapter=ReturnType<typeof deriveContactAdapter>;
interface ContactWitness{nativeSide:Side;runtimeSide:Side;adapter:Adapter}
interface Profile{id:string;kind:string;lean:number|null;hips:[number,number];torsoRadians:number;physicalCOM:{x:number;y:number;z:number}}
interface Bone{bodyHead:V3;bodyTail:V3}
interface NativeHand{nativeAnatomicalSide:Side;wristJoint:V3;bones:Record<string,Bone>}
interface Sole{nativeAnatomicalSide:Side;footEnvelopeBelow120mm:[V3,V3]}
const vector=(v:readonly number[])=>{assert(v.length===3&&v.every(Number.isFinite));return new THREE.Vector3(v[0],v[1],v[2]);};
const sha=(p:string)=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
function reach(d:number,a:number,b:number){assert([d,a,b].every(Number.isFinite)&&a>0&&b>0);const min=Math.abs(a-b),max=a+b,triangle=Math.min(d-min,max-d),safe=Math.min(d-min-.02,.995*max-d);return{d,a,b,min,max,triangle,safe,shortfall:Math.max(0,-triangle)};}
function main(){
 const base=path.resolve('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01'),out=path.resolve(process.argv.find(p=>p.startsWith('--out='))?.slice(6)??path.join(base,'scale-search04'));fs.mkdirSync(out,{recursive:true});
 const sources=[path.join(base,'joint-search02/report.json'),path.join(base,'contact-adapter01/adapter-metadata.json'),path.join(base,'native-landmarks/cuff-runtime-frames.json'),path.join(base,'native-landmarks/report.json'),path.resolve('harness/hero-remaster/new-rider-contact-adapter.mts'),path.resolve('harness/hero-remaster/new-rider-scale-search.mts'),path.resolve('src/core/riderGeometry.ts'),'/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/parent-assembly/donor-fit05/rider.glb'].map(p=>({path:p,sha256:sha(p)}));
 const previous=JSON.parse(fs.readFileSync(sources[0]!.path,'utf8'))as{profiles:Profile[]};
 const metadata=JSON.parse(fs.readFileSync(sources[1]!.path,'utf8'))as{hands:ContactWitness[];feet:ContactWitness[]};
 const R=JSON.parse(fs.readFileSync(sources[2]!.path,'utf8')).rotationSourceBlenderToRuntime as number[][];
 const native=JSON.parse(fs.readFileSync(sources[3]!.path,'utf8'))as{hands:NativeHand[];soleSurfaceWitnesses:Sole[];completeMeshInventory:{object:string;bounds:[V3,V3]}[]};
 const transport=(p:V3)=>vector(R.map(row=>row.reduce((v,c,i)=>v+c*p[i]!,0)));
 const sourceHeight=Math.max(...native.completeMeshInventory.map(m=>m.bounds[1][2]))-Math.min(...native.completeMeshInventory.map(m=>m.bounds[0][2]));
 const sourceAABB=new THREE.Box3();for(const m of native.completeMeshInventory){sourceAABB.expandByPoint(vector(m.bounds[0]));sourceAABB.expandByPoint(vector(m.bounds[1]));}
 const sourceSize=sourceAABB.getSize(new THREE.Vector3());
 const sourceHandMetrics=native.hands.map(h=>{const side=h.nativeAnatomicalSide;
  const joints=Object.entries(h.bones).filter(([name])=>name.startsWith('finger')).flatMap(([,b])=>[vector(b.bodyHead),vector(b.bodyTail)]);
  return{nativeSide:side,indexToLittleMCPDistanceM:vector(h.bones['finger2-1.'+side]!.bodyHead).distanceTo(vector(h.bones['finger5-1.'+side]!.bodyHead)),
   wristToMiddleDistalTailM:vector(h.wristJoint).distanceTo(vector(h.bones['finger3-3.'+side]!.bodyTail)),
   maximumWristToFingerBoneEndpointM:Math.max(...joints.map(p=>p.distanceTo(vector(h.wristJoint)))),
   definition:'Actual NEW skeletal landmarks, not glove surface length/width'};
 });
 const sourceFootMetrics=native.soleSurfaceWitnesses.map(s=>({nativeSide:s.nativeAnatomicalSide,sourceEnvelopeDimensionsBlenderXYZ:vector(s.footEnvelopeBelow120mm[1]).sub(vector(s.footEnvelopeBelow120mm[0])).toArray(),
  definition:'Actual foot-region surface bounds below source120mm include shoe/ankle envelope; not accepted shoe size or isolated sole width'}));
 const profiles:Profile[]=Array.from({length:1001},(_,i)=>{const lean=-1+i/500,p=riderPoseAtLean(lean,makeRiderRigPose());return{id:`lean-${i.toString().padStart(4,'0')}`,kind:'dense-lean',lean,hips:[p.hips.x,p.hips.y],torsoRadians:p.torsoAngle,physicalCOM:{...p.com}};});
 profiles.push(...previous.profiles.filter(p=>p.kind==='existing-physical-test-input'));assert(profiles.length===1007);
 const frozenProfiles=JSON.stringify(profiles);
 const columns=['profileIndex','runtimeSideL0R1','limbHand0Foot1','distanceM','segment1M','segment2M','triangleMinM','triangleMaxM','triangleMarginM','safeMarginM','shortfallM'];
 const candidates:Array<{id:string;scale:number;elbowZ:number;allTriangleFeasible:boolean;allSafe:boolean;minimumSafeMarginM:number;[key:string]:unknown}>=[];const allRows:{candidateId:string;rows:number[][]}[]=[];
 for(const elbowZ of [1.145,1.125])for(let step=0;step<=14;step++){
  const scale=Number((1+step*.005).toFixed(3)),id=`elbowZ${elbowZ}-scale${scale.toFixed(3)}`,sourcePelvisZ=.945-.02/scale;
  const sourceJointVectorsScale=scale;
  const contacts=metadata.hands.map(h=>{const f=metadata.feet.find(f=>f.runtimeSide===h.runtimeSide)!;
   const derive=(a:Adapter)=>deriveContactAdapter({...a.input,sourceJoint:vector(a.input.sourceJoint).multiplyScalar(scale).toArray()as V3,sourceContact:vector(a.input.sourceContact).multiplyScalar(scale).toArray()as V3});
   const hand=derive(h.adapter),foot=derive(f.adapter);
   assert(vector(hand.targetWorldOffset).distanceTo(vector(h.adapter.targetWorldOffset).multiplyScalar(scale))<1e-12);
   assert(vector(foot.targetWorldOffset).distanceTo(vector(f.adapter.targetWorldOffset).multiplyScalar(scale))<1e-12);
   return{side:h.runtimeSide,nativeSide:h.nativeSide,hand,foot};
  });
  const lengths=contacts.map(c=>{const sign=c.nativeSide==='L'?1:-1,shoulder=transport([sign*.205,.02,1.44]).multiplyScalar(scale),elbow=transport([sign*.285,.025,elbowZ]).multiplyScalar(scale);
   const upperArm=shoulder.distanceTo(elbow),forearm=elbow.distanceTo(vector(c.hand.input.sourceJoint));
   return{side:c.side,upperArm,forearm,upperArmToForearmRatio:upperArm/forearm,
    thigh:transport([sign*.105,.015,.945]).distanceTo(transport([sign*.145,0,.50]))*scale,
    shin:transport([sign*.145,0,.50]).distanceTo(transport([sign*.18,.045,.115]))*scale};
  });
  let minTriangle=Infinity,minSafe=Infinity,handSafe=Infinity,footSafe=Infinity,worstShortfall=0;
  let minimumTriangleFrame:unknown=null,minimumSafeFrame:unknown=null;
  const rows=[];
  for(const[index,p]of profiles.entries()){
   const axis=new THREE.Vector3(Math.cos(p.torsoRadians),Math.sin(p.torsoRadians),0),forward=new THREE.Vector3(Math.sin(p.torsoRadians),-Math.cos(p.torsoRadians),0);
   const physicalHip=new THREE.Vector3(p.hips[0],p.hips[1],0),pelvis=physicalHip.clone().addScaledVector(axis,-.02);
   for(const c of contacts){const sign=c.side==='L'?1:-1,l=lengths.find(l=>l.side===c.side)!;
    const hip=pelvis.clone().addScaledVector(axis,(.945-sourcePelvisZ)*scale).add(new THREE.Vector3(0,0,sign*.105*scale));
    assert(hip.clone().add(new THREE.Vector3(0,0,-sign*.105*scale)).distanceTo(physicalHip)<1e-12);
    const shoulder=pelvis.clone().addScaledVector(axis,(1.44-sourcePelvisZ)*scale).addScaledVector(forward,-.005*scale).add(new THREE.Vector3(0,0,sign*.205*scale));
    const arm=reach(shoulder.distanceTo(vector(c.hand.targetJoint)),l.upperArm,l.forearm),leg=reach(hip.distanceTo(vector(c.foot.targetJoint)),l.thigh,l.shin);
    for(const[k,r]of [['hand',arm],['foot',leg]]as const){const record={profile:p.id,index,lean:p.lean,hips:p.hips,torsoRadians:p.torsoRadians,side:c.side,limb:k,triangleMarginM:r.triangle,safeMarginM:r.safe,distanceM:r.d,segmentLengthsM:[r.a,r.b]};
     if(r.triangle<minTriangle){minTriangle=r.triangle;minimumTriangleFrame=record;}if(r.safe<minSafe){minSafe=r.safe;minimumSafeFrame=record;}
     if(k==='hand')handSafe=Math.min(handSafe,r.safe);else footSafe=Math.min(footSafe,r.safe);worstShortfall=Math.max(worstShortfall,r.shortfall);
     rows.push([index,c.side==='L'?0:1,k==='hand'?0:1,r.d,r.a,r.b,r.min,r.max,r.triangle,r.safe,r.shortfall]);
    }
   }
  }
  const handDimensions=sourceHandMetrics.map(h=>({nativeSide:h.nativeSide,indexToLittleMCPDistanceM:h.indexToLittleMCPDistanceM*scale,wristToMiddleDistalTailM:h.wristToMiddleDistalTailM*scale,maximumWristToFingerBoneEndpointM:h.maximumWristToFingerBoneEndpointM*scale}));
  const dimensions={heightM:sourceHeight*scale,sourceAABBBlenderXYZ:sourceSize.clone().multiplyScalar(scale).toArray(),
   shoulderHalfM:.205*scale,hipHalfM:.105*scale,shoulderToAnatomicalHipM:.495*scale,
   manualIPDEstimateM:.065*scale,manualIPDStatus:'Approximate65mm source calibration from image eye witnesses; uncertainty inherited, not actual measured pupil anatomy',
   headSourceAABBBlenderXYZ:vector(native.completeMeshInventory.find(m=>m.object==='textured')!.bounds[1]).sub(vector(native.completeMeshInventory.find(m=>m.object==='textured')!.bounds[0])).multiplyScalar(scale).toArray(),
   hands:handDimensions,feet:sourceFootMetrics.map(s=>({nativeSide:s.nativeSide,footRegionEnvelopeBlenderXYZ:vector(s.sourceEnvelopeDimensionsBlenderXYZ).multiplyScalar(scale).toArray()})),
   uniformSizeIncreasePercent:(scale-1)*100,relativeAspectRatiosUnchanged:true};
  candidates.push({id,scale,sourceJointVectorsScale,elbowZ,sourcePelvisHeadZ:sourcePelvisZ,worldHipAbovePelvisM:(.945-sourcePelvisZ)*scale,lengths,dimensions,
   contacts:contacts.map(c=>({side:c.side,targetWrist:c.hand.targetJoint,targetAnkle:c.foot.targetJoint,targetWristToContact:c.hand.targetWorldOffset,targetAnkleToSole:c.foot.targetWorldOffset})),
   minimumTriangleMarginM:minTriangle,minimumSafeMarginM:minSafe,minimumHandSafeMarginM:handSafe,minimumFootSafeMarginM:footSafe,worstShortfallM:worstShortfall,
   allTriangleFeasible:worstShortfall<1e-12,allSafe:minSafe>=0,minimumTriangleFrame,minimumSafeFrame});
  allRows.push({candidateId:id,rows});
 }
 assert(JSON.stringify(profiles)===frozenProfiles,'Physical profile/COM mutation');
 const after=sources.map(s=>({path:s.path,sha256:sha(s.path)}));assert(sources.every((s,i)=>s.sha256===after[i]!.sha256));
 const summary={candidateCount:candidates.length,profilesPerCandidate:profiles.length,totalEvaluatedLimbTargets:candidates.length*profiles.length*4,
  triangleFeasible:candidates.filter(c=>c.allTriangleFeasible).length,allLimbsSafe:candidates.filter(c=>c.allSafe).length,
  firstSafePerElbow:[1.145,1.125].map(z=>({elbowZ:z,smallestSampledSafeScale:candidates.find(c=>c.elbowZ===z&&c.allSafe)??null})),
  selectionProxy:{targetMinimumStrictMarginM:.010,policy:'Smallest sampled whole-source scale reaching10mm strict padding, elbowZ1.125 ratio hypothesis preferred; not anatomy/appearance acceptance',selected:candidates.find(c=>c.elbowZ===1.125&&c.minimumSafeMarginM>=.010)??null},
  first10mmMarginPerElbow:[1.145,1.125].map(z=>({elbowZ:z,smallestSampledScale:candidates.find(c=>c.elbowZ===z&&c.minimumSafeMarginM>=.010)??null})),
  scale104PerElbow:candidates.filter(c=>c.scale===1.04),strongestMarginsWithinBound:[...candidates].sort((a,b)=>b.minimumSafeMarginM-a.minimumSafeMarginM).slice(0,2)};
 const report={schema:'rockhop.private-uniform-metre-scale.v1',status:'Unit-calibration hypothesis audit only; no asset scale or runtime change applied',sources,sourceHashesAfter:after,sourcesUnchanged:true,
  bounds:{uniformScale:{min:1,max:1.07,step:.005},fixedSourceJointEstimates:{shoulder:[.205,.02,1.44],anatomicalHip:[.105,.015,.945],elbowAbsX:.285,elbowY:.025,elbowZ:[1.145,1.125],knee:[.145,0,.50],ankle:[.18,.045,.115]},sourcePelvisHeadFormula:'hipZ − .02/scale',worldHipOffsetM:.02},
  sourceDimensions:{heightM:sourceHeight,sourceAABBBlenderXYZ:sourceSize.toArray(),hands:sourceHandMetrics,feet:sourceFootMetrics},profiles,
  physicalInputsAndCOMUnchanged:true,uniformContactOffsetScalingVerified:true,summary,candidates,
  limits:['Uniform scale preserves proportions but changes absolute height, head/IPD, clothing, shoe and hand dimensions; game camera/seat/handlebar fit require played evidence','Scale grid alone does not establish true metre calibration; source pupil anatomy and reference height uncertain','All source joint centres under clothes remain prior documented estimates; no boundary nudges or geometry edits','Pelvis authoring head position is adjusted only for fixed world20mm hip adapter convention, not source mesh deformation','Dense1001 lean points plus6 diagnostic states are finite samples, not continuous/all-gameplay proof','Visual mass centroid can change with NEW skeleton anatomy and uniform scaling despite unchanged physical mass map; independent rendered COM adaptation/validation remains unmeasured','Source palm and sole point targets remain provisional, not surface wrap/penetration proof','No Garage, sitting controls, UniMate, skin deformation, LOD or player asset acceptance from numerical audit']};
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
 const raw=Buffer.from(JSON.stringify({units:'metres',columns,profiles,candidates:allRows})+'\n'),compressed=gzipSync(raw,{level:9});
 fs.writeFileSync(path.join(out,'all-candidate-frame-reach.json.gz'),compressed);
 fs.writeFileSync(path.join(out,'storage.json'),JSON.stringify({file:'all-candidate-frame-reach.json.gz',format:'lossless gzip UTF-8 JSON',uncompressedBytes:raw.length,compressedBytes:compressed.length,uncompressedSHA256:crypto.createHash('sha256').update(raw).digest('hex'),compressedSHA256:crypto.createHash('sha256').update(compressed).digest('hex')},null,2)+'\n');
 console.log(JSON.stringify({status:report.status,sourcesUnchanged:true,summary},null,2));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)main();
