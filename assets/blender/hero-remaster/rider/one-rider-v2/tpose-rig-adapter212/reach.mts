/** Read-only NEW authoring proportions against actual deterministic physical targets. */
import fs from 'node:fs';
import * as THREE from 'three';
import { RIDER_PROFILE, riderRigFromHips, makeRiderRigPose } from '../../../../../../src/core/riderGeometry';
const E='docs/evidence/hero-remaster/one-rider-v2/tpose-rig-adapter212';
const summary=JSON.parse(fs.readFileSync(E+'/section-summary.json','utf8'));
const section=(axis:number,h:number)=>summary.find((s:any)=>s.axis===axis&&s.planeCanonicalM===h);
const largestArm=(h:number)=>section(2,h).loops.filter((l:any)=>l.areaCentroidCanonical[1]>1.2).sort((a:any,b:any)=>b.areaM2-a.areaM2)[0].areaCentroidCanonical as number[];
const legs=(h:number,side:number)=>section(1,h).loops.find((l:any)=>Math.sign(l.areaCentroidCanonical[2])===side).areaCentroidCanonical as number[];
const v=(a:number[])=>new THREE.Vector3().fromArray(a);
const pelvis=v(section(1,.9).loops[0].areaCentroidCanonical);pelvis.y=.88;
const roots=[1,-1].map(sign=>({sign,shoulder:v(largestArm(sign*.18)),elbow:v(largestArm(sign*.34)),wrist:v(largestArm(sign*.50)),hip:v(legs(.49,sign)),knee:v(legs(.49,sign)),ankle:v(legs(.115,sign))}));
const contacts=JSON.parse(fs.readFileSync(E+'/contact-witnesses.json','utf8')).hands;
for(const r of roots){r.hip.copy(r.knee);r.hip.x=pelvis.x;r.hip.y=.9;r.hip.z=r.sign*.105;}
const rows=[];
for(let i=0;i<=200;i++){
 const lean=-1+i/100;const a=lean<=0?RIDER_PROFILE.poses[0]:RIDER_PROFILE.poses[1],b=lean<=0?RIDER_PROFILE.poses[1]:RIDER_PROFILE.poses[2];const t=lean<=0?lean+1:lean;
 const hX=a.hipX+(b.hipX-a.hipX)*t,hY=a.hipY+(b.hipY-a.hipY)*t,torso=(a.torso+(b.torso-a.torso)*t)*Math.PI/180;
 const p=riderRigFromHips(hX,hY,torso,makeRiderRigPose());const axis=new THREE.Vector3(Math.cos(torso),Math.sin(torso),0);const root=new THREE.Vector3(p.hips.x,p.hips.y,0).addScaledVector(axis,-.02);
 const rotation=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),torso-Math.PI/2);
 const limbs=roots.map(r=>{
  const shoulder=r.shoulder.clone().sub(pelvis).applyQuaternion(rotation).add(root);const hip=r.hip.clone().sub(pelvis).applyQuaternion(rotation).add(root);
  // Offset is provisional physical-profile hand convention, not NEW actual-surface fit.
  const grip=new THREE.Vector3(RIDER_PROFILE.grip.x,RIDER_PROFILE.grip.y,r.sign*RIDER_PROFILE.grip.z);
  const wrist=grip.clone().add(new THREE.Vector3(RIDER_PROFILE.wristFromGrip.x,RIDER_PROFILE.wristFromGrip.y,0));
  const ankle=new THREE.Vector3(RIDER_PROFILE.ankle.x,RIDER_PROFILE.ankle.y,r.sign*RIDER_PROFILE.ankle.z);
  const a1=r.shoulder.distanceTo(r.elbow),a2=r.elbow.distanceTo(r.wrist),l1=r.hip.distanceTo(r.knee),l2=r.knee.distanceTo(r.ankle);
  const side=r.sign===1?'L':'R';const contact=contacts.find((h:any)=>h.side===side);
  const newWrist=grip.clone().sub(v(contact.targetWristToGripAxisOffset));
  // Conditional target with actual NEW sole-to-ankle height .115m;
  // source shoe toe orientation remains unmeasured and x offset is bounded.
  const soleY=RIDER_PROFILE.peg.y+.011;
  const legDemandRange=[-.03,0,.03].map(dx=>hip.distanceTo(new THREE.Vector3(RIDER_PROFILE.peg.x+dx,soleY+.115,r.sign*RIDER_PROFILE.peg.z)));
  return{side,posedShoulderAxle:shoulder.toArray(),posedHipAxle:hip.toArray(),armDistanceM:shoulder.distanceTo(wrist),armSegmentsM:[a1,a2],armShortfallM:Math.max(0,shoulder.distanceTo(wrist)-a1-a2),newDeclaredPalmArmDistanceM:shoulder.distanceTo(newWrist),newDeclaredPalmShortfallM:Math.max(0,shoulder.distanceTo(newWrist)-a1-a2),newDeclaredPalmTargetWrist:newWrist.toArray(),legDistanceM:hip.distanceTo(ankle),legSegmentsM:[l1,l2],legShortfallM:Math.max(0,hip.distanceTo(ankle)-l1-l2),newSoleConditionalLegDemandM:legDemandRange};
 });rows.push({lean,physical:p,limbs});
}
const worst=(key:string)=>rows.flatMap(row=>row.limbs.map(l=>({lean:row.lean,side:l.side,value:(l as any)[key]}))).sort((a,b)=>b.value-a.value)[0];
const out={status:'READ_ONLY_PROVISIONAL_JOINT_CENTRES_NOT_RIG_OR_GAMEPLAY_PASS',authority:'Actual riderRigFromHips/RIDER_PROFILE sampled over 201 interpolated lean inputs; not recorded live physics or landings',pelvisEstimate:pelvis.toArray(),roots:roots.map(r=>Object.fromEntries(Object.entries(r).map(([k,x])=>[k,x instanceof THREE.Vector3?x.toArray():x]))),worst:{armDistance:worst('armDistanceM'),armShortfall:worst('armShortfallM'),newDeclaredPalmArmDistance:worst('newDeclaredPalmArmDistanceM'),newDeclaredPalmShortfall:worst('newDeclaredPalmShortfallM'),legDistance:worst('legDistanceM'),legShortfall:worst('legShortfallM'),newSoleConditionalDemandM:Math.max(...rows.flatMap(r=>r.limbs.flatMap(l=>l.newSoleConditionalLegDemandM)))},rows,limits:['Shoulder/elbow/wrist section stations and hidden hip/knee/ankle are explicit NEW authoring hypotheses, not measured skeletal joints.','Legacy wrist-offset control is compared with the literal NEW palm witness and declared contact-frame/radius hypothesis; neither is a played grip pass.','Sole target range uses115mm ankle height with +/-30mm sagittal displacement; final actual sole witness is still required.','No chain endpoints, COM, physics, geometry, inverse binds or game assets changed.','Landings and actual recorded engine maximum lean require a later live matched gate.']};
fs.writeFileSync(E+'/mapped-reach.json',JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify({...out,rows:undefined},null,2));
