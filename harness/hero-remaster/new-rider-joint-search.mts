/** PRIVATE bounded NEW joint-estimate reach search. CPU math and GLB decode only.
 * No source geometry, skins, game code, player files, GPU or physics changes.
 * pnpm exec tsx harness/hero-remaster/new-rider-joint-search.mts [--out=<evidence>]
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { deriveContactAdapter } from './new-rider-contact-adapter.mjs';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils';
import { boneName } from '../../src/render/hero/gltfRider';
import { makeRiderRigPose, riderRigFromHips, riderPoseAtLean } from '../../src/core/riderGeometry';

type V3 = [number,number,number];
type Side = 'L'|'R';
type Adapter = ReturnType<typeof deriveContactAdapter>;
interface ContactWitness { nativeSide:Side;runtimeSide:Side;adapter:Adapter }
const vector=(v:readonly number[])=>{assert(v.length===3&&v.every(Number.isFinite));return new THREE.Vector3(v[0],v[1],v[2]);};
const sha=(p:string)=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
function reach(distance:number,a:number,b:number){
 assert([distance,a,b].every(Number.isFinite)&&a>0&&b>0);
 const min=Math.abs(a-b),max=a+b,low=distance-min,high=max-distance;
 return {distanceM:distance,segmentLengthsM:[a,b],triangleMinM:min,triangleMaxM:max,
  innerReachMarginM:low,outerReachMarginM:high,minimumTriangleMarginM:Math.min(low,high),
  shortfallM:Math.max(0,-low,-high),reachRatio:distance/max,
  additiveMinM:min+.02,additiveMaxM:max*.995,additiveMarginM:Math.min(distance-min-.02,max*.995-distance)};
}
async function main(){
 const base=path.resolve('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01');
 const out=path.resolve(process.argv.find(a=>a.startsWith('--out='))?.slice(6)??path.join(base,'joint-search02'));
 fs.mkdirSync(out,{recursive:true});
 const contactPath=path.join(base,'contact-adapter01/adapter-metadata.json');
 const framesPath=path.join(base,'native-landmarks/cuff-runtime-frames.json');
 const bindReportPath=path.join(base,'body-bind01/report.json');
 const bindGLB='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind01/rider.glb';
 const sourcePaths=[contactPath,framesPath,bindReportPath,bindGLB,path.resolve('harness/hero-remaster/new-rider-contact-adapter.mts'),path.resolve('harness/hero-remaster/new-rider-joint-search.mts'),path.resolve('src/core/riderGeometry.ts')];
 const sources=sourcePaths.map(p=>({path:p,sha256:sha(p)}));
 const metadata=JSON.parse(fs.readFileSync(contactPath,'utf8')) as {hands:ContactWitness[];feet:ContactWitness[]};
 const frames=JSON.parse(fs.readFileSync(framesPath,'utf8')) as {rotationSourceBlenderToRuntime:number[][]};
 const R=frames.rotationSourceBlenderToRuntime;
 const transport=(p:V3)=>vector(R.map(row=>row.reduce((sum,c,i)=>sum+c*p[i]!,0)));
 const contacts=metadata.hands.map(hand=>{
  const foot=metadata.feet.find(f=>f.runtimeSide===hand.runtimeSide)!;
  const handDerived=deriveContactAdapter(hand.adapter.input),footDerived=deriveContactAdapter(foot.adapter.input);
  assert(vector(handDerived.targetJoint).distanceTo(vector(hand.adapter.targetJoint))<1e-12);
  assert(vector(footDerived.targetJoint).distanceTo(vector(foot.adapter.targetJoint))<1e-12);
  return{side:hand.runtimeSide,nativeSide:hand.nativeSide,hand:handDerived,foot:footDerived};
 });
 // Decode current private NEW source; preserve authored rest data, never invoke runtime pose or material preparation.
 const doc=await loadRigAt(pathToFileURL(bindGLB));doc.scene.updateMatrixWorld(true);
 const nodes=new Map<string,THREE.Object3D>();doc.scene.traverse(o=>nodes.set(boneName(o.name),o));
 const observedBones=[...nodes.values()].filter(o=>(o as THREE.Bone).isBone).map(o=>({name:boneName(o.name),parent:o.parent?.name,
  fileWorldPosition:o.getWorldPosition(new THREE.Vector3()).toArray(),worldQuaternion:o.getWorldQuaternion(new THREE.Quaternion()).toArray(),localPosition:o.position.toArray()}));
 assert(observedBones.length===19);
 const bindReport=JSON.parse(fs.readFileSync(bindReportPath,'utf8')) as {jointDefinitions:Record<string,{head:V3;tail:V3}>};
 const actualBindLengths=(['L','R'] as const).map(side=>{const p=(name:string)=>nodes.get(name+'.'+side)!.getWorldPosition(new THREE.Vector3());
  return{side,upperArm:p('upperArm').distanceTo(p('forearm')),forearm:p('forearm').distanceTo(p('hand')),thigh:p('thigh').distanceTo(p('shin')),shin:p('shin').distanceTo(p('foot'))};});
 const actualBindLandmarkChecks=contacts.map(c=>{
  const sourceWrist=c.hand.input.sourceJoint;
  const decodedWrist=nodes.get('hand.'+c.side)!.getWorldPosition(new THREE.Vector3()).sub(new THREE.Vector3(.65,0,0));
  const error=decodedWrist.distanceTo(vector(sourceWrist));assert(error<1e-5,'NEW exported wrist differs from measured source');
  return{side:c.side,maximumWristWorldErrorM:error,decodedSourceWristAxleFrame:decodedWrist.toArray()};
 });
 const profiles=Array.from({length:81},(_,i)=>{
  const lean=-1+i/40,p=riderPoseAtLean(lean,makeRiderRigPose());
  return{id:`lean-${i.toString().padStart(2,'0')}`,kind:'shared-lean-knot',lean,hips:[p.hips.x,p.hips.y] as [number,number],torsoRadians:p.torsoAngle,
   physicalPose:p,physicalJSON:JSON.stringify(p)};
 });
 const diagnosticInputs=[[-.57,.60,55],[-.28,.85,40],[-.22,.90,26],[-.38,.78,28],[-.14,.96,40],[-.40,.70,40]];
 for(const [i,values]of diagnosticInputs.entries()){
  const [x,y,degrees]=values as V3,p=riderRigFromHips(x,y,degrees*Math.PI/180,makeRiderRigPose());
  profiles.push({id:`diagnostic-${i}`,kind:'existing-physical-test-input',lean:NaN,hips:[x,y],torsoRadians:p.torsoAngle,physicalPose:p,physicalJSON:JSON.stringify(p)});
 }
 const bound={shoulderZ:{min:1.42,max:1.44,step:.0025},hipZ:{min:.945,max:.96,step:.0025},
  pelvisBelowAnatomicalHipM:.02,shoulderHalfM:.205,hipHalfM:.105,shoulderY:.02,hipY:.015,
  elbow:{halfX:.285,y:.025,z:1.145},knee:{halfX:.145,y:0,z:.50},ankle:{halfX:.18,y:.045,z:.115},
  searchAuthority:'Explicit parent authoring estimate bounds; positions hidden by garments are estimates, not measured joints',
  finiteGridOnly:true,profiles:'81 exact shared riderTargetTable lean knots plus six existing synthetic physical test inputs'};
 const summaries:Record<string,unknown>[]=[];
 const details:unknown[]=[];
 let candidateIndex=0;
 for(let shoulderStep=0;shoulderStep<=8;shoulderStep++)for(let hipStep=0;hipStep<=6;hipStep++){
  const shoulderZ=Number((1.42+shoulderStep*.0025).toFixed(4)),hipZ=Number((.945+hipStep*.0025).toFixed(4));
  const id=`candidate-${(++candidateIndex).toString().padStart(2,'0')}`;
  const candidate={id,sourceShoulderZ:shoulderZ,sourceAnatomicalHipZ:hipZ,sourcePelvisHeadZ:hipZ-.02,
   shoulderToHipM:shoulderZ-hipZ,sourceElbowZ:1.145,sourceKneeZ:.50,sourceAnkleZ:.115};
  const lengths=contacts.map(c=>{const nativeSign=c.nativeSide==='L'?1:-1;
   const shoulder=transport([nativeSign*.205,.02,shoulderZ]),elbow=transport([nativeSign*.285,.025,1.145]);
   const hip=transport([nativeSign*.105,.015,hipZ]),knee=transport([nativeSign*.145,0,.50]),ankle=transport([nativeSign*.18,.045,.115]);
   return{side:c.side,upperArm:shoulder.distanceTo(elbow),forearm:elbow.distanceTo(vector(c.hand.input.sourceJoint)),thigh:hip.distanceTo(knee),shin:knee.distanceTo(ankle)};
  });
  let worstShortfall=0,minMargin=Infinity,minAdditiveMargin=Infinity;
  let worstLeanShortfall=0,minLeanMargin=Infinity,minLeanAdditiveMargin=Infinity;
  let worstRecord:unknown=null,minimumMarginRecord:unknown=null,minimumAdditiveMarginRecord:unknown=null;
  const rows=[];
  for(const p of profiles){
   const axis=new THREE.Vector3(Math.cos(p.torsoRadians),Math.sin(p.torsoRadians),0);
   const forward=new THREE.Vector3(Math.sin(p.torsoRadians),-Math.cos(p.torsoRadians),0);
   const physicalHip=new THREE.Vector3(p.hips[0],p.hips[1],0),pelvisHead=physicalHip.clone().addScaledVector(axis,-.02);
   const limbs=contacts.map(c=>{
    const sign=c.side==='L'?1:-1,l=lengths.find(x=>x.side===c.side)!;
    const hipRoot=pelvisHead.clone().addScaledVector(axis,.02).add(new THREE.Vector3(0,0,sign*.105));
    const shoulderRoot=pelvisHead.clone().addScaledVector(axis,shoulderZ-(hipZ-.02))
      .addScaledVector(forward,-.02-(-.015)).add(new THREE.Vector3(0,0,sign*.205));
    assert(hipRoot.clone().add(new THREE.Vector3(0,0,-sign*.105)).distanceTo(physicalHip)<1e-12,'Pelvis 20mm hip root alignment mismatch');
    const arm=reach(shoulderRoot.distanceTo(vector(c.hand.targetJoint)),l.upperArm,l.forearm);
    const leg=reach(hipRoot.distanceTo(vector(c.foot.targetJoint)),l.thigh,l.shin);
    for(const[kind,r]of [['hand',arm],['foot',leg]]as const){
     if(r.shortfallM>worstShortfall){worstShortfall=r.shortfallM;worstRecord={profile:p.id,side:c.side,limb:kind,shortfallM:r.shortfallM};}
     if(r.minimumTriangleMarginM<minMargin){minMargin=r.minimumTriangleMarginM;minimumMarginRecord={profile:p.id,side:c.side,limb:kind,marginM:minMargin};}
     if(r.additiveMarginM<minAdditiveMargin){minAdditiveMargin=r.additiveMarginM;minimumAdditiveMarginRecord={profile:p.id,side:c.side,limb:kind,marginM:minAdditiveMargin};}
     if(p.kind==='shared-lean-knot'){worstLeanShortfall=Math.max(worstLeanShortfall,r.shortfallM);minLeanMargin=Math.min(minLeanMargin,r.minimumTriangleMarginM);minLeanAdditiveMargin=Math.min(minLeanAdditiveMargin,r.additiveMarginM);}
    }
    return{side:c.side,shoulderRoot:shoulderRoot.toArray(),hipRoot:hipRoot.toArray(),handTarget:c.hand.targetJoint,ankleTarget:c.foot.targetJoint,arm,leg};
   });
   assert(JSON.stringify(p.physicalPose)===p.physicalJSON,'Source physical pose/COM mutated');
   rows.push({profileId:p.id,pelvisHead:pelvisHead.toArray(),limbs});
  }
  summaries.push({...candidate,lengths,worstShortfallM:worstShortfall,minimumTriangleMarginM:minMargin,minimumAdditiveReachMarginM:minAdditiveMargin,
   allSampledProfilesReachable:worstShortfall<1e-12,allSampledProfilesAdditiveSafe:minAdditiveMargin>=0,
   leanOnly:{worstShortfallM:worstLeanShortfall,minimumTriangleMarginM:minLeanMargin,minimumAdditiveReachMarginM:minLeanAdditiveMargin,all81KnotsReachable:worstLeanShortfall<1e-12,all81KnotsAdditiveSafe:minLeanAdditiveMargin>=0},worstRecord,minimumMarginRecord,minimumAdditiveMarginRecord});
  details.push({candidate,rows});
 }
 // Ordering is a mathematical shortlist, never anatomical selection or acceptance.
 const sorted=[...summaries].sort((a,b)=>Number(a.worstShortfallM)-Number(b.worstShortfallM)||Number(b.minimumTriangleMarginM)-Number(a.minimumTriangleMarginM));
 const feasible=summaries.filter(s=>s.allSampledProfilesReachable),additive=summaries.filter(s=>s.allSampledProfilesAdditiveSafe);
 const leanFeasible=summaries.filter(s=>(s.leanOnly as {all81KnotsReachable:boolean}).all81KnotsReachable);
 const sourceHashesAfter=sources.map(s=>({path:s.path,sha256:sha(s.path)}));assert(sources.every((s,i)=>s.sha256===sourceHashesAfter[i]!.sha256));
 const report={schema:'rockhop.private-new-joint-estimate-search.v1',status:'Bounded synthetic reach evidence; parent must judge garment joint placement and played skin',
  sources,sourceHashesAfter,sourcesUnchanged:true,bodyBind01Observed:{sha256:sha(bindGLB),bones:observedBones,actualBindLengths,actualBindLandmarkChecks,authoredJointDefinitions:bindReport.jointDefinitions},
  bound,profiles:profiles.map(p=>({id:p.id,kind:p.kind,lean:Number.isFinite(p.lean)?p.lean:null,hips:p.hips,torsoRadians:p.torsoRadians,physicalCOM:p.physicalPose.com})),
  contactsUnchanged:true,physicalPoseAndCOMUnchanged:true,candidateCount:summaries.length,frameCountPerCandidate:profiles.length,limbsPerFrame:4,
  summary:{sampledAllProfilesFeasibleCount:feasible.length,sampledAllProfilesAdditiveSafeCount:additive.length,lean81KnotsFeasibleCount:leanFeasible.length,
   bestMathematicalShortlist:sorted.slice(0,5)},candidates:summaries,
  limits:['Source anatomy under clothes is explicitly estimated','No garment boundaries or new joint centres independently accepted','Contact targets reuse provisional contact-adapter01 source palm and bottom2mm sole witnesses; no accepted finger wrap/cylinder/sole fit','No geometry stretch, physics/root-clamp edit, source-skin rewrite or new player asset','Finite sample grid is not proof over continuous trajectory or all reachable physics states','Actual NEW render bone length changes can alter drawn segment COM; independent mass/pose agreement remains unmeasured','No standing-to-sitting, Garage or gameplay moving deformation/contact acceptance from this numerical search']};
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
 fs.writeFileSync(path.join(out,'candidate-frame-reach.json'),JSON.stringify({schema:'rockhop.private-joint-estimate-per-frame.v1',units:'metres',profiles:report.profiles,candidates:details})+'\n');
 console.log(JSON.stringify({status:report.status,candidateCount:summaries.length,frameCountPerCandidate:profiles.length,sourcesUnchanged:true,summary:report.summary},null,2));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)await main();
