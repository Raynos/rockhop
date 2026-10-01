/** PRIVATE CPU-only authoring prototype. No renderer, GPU, physics mutation or player assets.
 * pnpm exec tsx harness/hero-remaster/new-rider-contact-adapter.mts [--out=<private evidence>]
 * Point/orientation mathematics is not a played surface-contact acceptance gate.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { RIDER_PROFILE, makeRiderRigPose, riderRigFromHips, riderPoseAtLean } from '../../src/core/riderGeometry';

type V3 = [number, number, number];
type Q4 = [number, number, number, number];
type Side = 'L' | 'R';
interface ContactInput {
  side: Side;
  sourceJoint: V3;
  sourceContact: V3;
  sourceLongAxis: V3;
  sourceNormalAxis: V3;
  /** Actual NEW bone bind world quaternion; never copied from the production character. */
  bindWorldQuaternion: Q4;
  targetLongAxis: V3;
  targetNormalAxis: V3;
  targetContact: V3;
  targetSocketWorldQuaternion: Q4;
}
const vec = (a: readonly number[]) => new THREE.Vector3(a[0], a[1], a[2]);
const quat = (a: readonly number[]) => new THREE.Quaternion(a[0], a[1], a[2], a[3]).normalize();
const hash = (p: string) => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const maxAbs = (xs: number[]) => Math.max(...xs.map(Math.abs));

/** Proper right-handed anatomical frame. +Y follows fingers/toes; +Z is palm/sole normal.
 * The long axis stays exact; a nonorthogonal measured normal is projected onto its plane.
 * Rigid proper rotations cannot independently map two axes with different included angles.
 */
export function anatomicalFrame(longAxis: V3, normalAxis: V3) {
  const y = vec(longAxis), normal = vec(normalAxis);
  assert(y.length() > 1e-8 && normal.length() > 1e-8, 'Zero anatomical axis');
  y.normalize(); normal.normalize();
  const z = normal.clone().addScaledVector(y, -normal.dot(y));
  assert(z.length() > 1e-6, 'Parallel anatomical axes cannot define orientation');
  z.normalize();
  const x = new THREE.Vector3().crossVectors(y, z).normalize();
  const matrix = new THREE.Matrix4().makeBasis(x, y, z);
  const determinant = matrix.determinant();
  assert(Math.abs(determinant - 1) < 1e-10, 'Orientation must be proper, not reflected');
  const q = new THREE.Quaternion().setFromRotationMatrix(matrix).normalize();
  return { matrix, quaternion: q, longAxis: y, projectedNormalAxis: z,
    rawNormalLongAxisDot: normal.dot(y), rawNormalProjectionAngleRad: normal.angleTo(z), determinant };
}

/** Preserve source bind, derive separate riding target orientation and coherently rotated offset.
 * The source socket is authored as a child of this bone; its local position never changes.
 * The desired socket world orientation is distinct from its source-bind world orientation.
 */
export function deriveContactAdapter(input: ContactInput) {
  const sourceFrame = anatomicalFrame(input.sourceLongAxis, input.sourceNormalAxis);
  const targetFrame = anatomicalFrame(input.targetLongAxis, input.targetNormalAxis);
  const delta = targetFrame.quaternion.clone().multiply(sourceFrame.quaternion.clone().invert()).normalize();
  const bindQ = quat(input.bindWorldQuaternion);
  const targetRestQ = delta.clone().multiply(bindQ).normalize();
  const sourceOffset = vec(input.sourceContact).sub(vec(input.sourceJoint));
  const localOffset = sourceOffset.clone().applyQuaternion(bindQ.clone().invert());
  const targetOffset = localOffset.clone().applyQuaternion(targetRestQ);
  const targetJoint = vec(input.targetContact).sub(targetOffset);
  const targetSocketQ = quat(input.targetSocketWorldQuaternion);
  const socketLocalQ = targetRestQ.clone().invert().multiply(targetSocketQ).normalize();
  const sourceBindSocketQ = bindQ.clone().multiply(socketLocalQ).normalize();
  const sourceOrigin = vec(input.sourceJoint);
  const rigid = new THREE.Matrix4().compose(targetJoint, delta, new THREE.Vector3(1, 1, 1))
    .multiply(new THREE.Matrix4().makeTranslation(-sourceOrigin.x, -sourceOrigin.y, -sourceOrigin.z));
  const mappedContact = vec(input.sourceContact).applyMatrix4(rigid);
  const mappedLong = sourceFrame.longAxis.clone().applyQuaternion(delta);
  const mappedNormal = sourceFrame.projectedNormalAxis.clone().applyQuaternion(delta);
  const actualSocketQ = targetRestQ.clone().multiply(socketLocalQ).normalize();
  const normalError = mappedNormal.distanceTo(targetFrame.projectedNormalAxis);
  const longError = mappedLong.distanceTo(targetFrame.longAxis);
  const pointError = mappedContact.distanceTo(vec(input.targetContact));
  const orientationError = actualSocketQ.angleTo(targetSocketQ);
  const qUnitError = Math.abs(targetRestQ.length() - 1);
  assert(pointError < 1e-12 && normalError < 1e-12 && longError < 1e-12, 'Anatomical/contact transform mismatch');
  assert(orientationError < 1e-7 && qUnitError < 1e-12, 'Socket orientation mismatch');
  assert(Math.abs(rigid.determinant() - 1) < 1e-10, 'Contact transport reflected/scaled geometry');
  return {
    input, sourceFrame: { determinant: sourceFrame.determinant, rawNormalLongAxisDot: sourceFrame.rawNormalLongAxisDot,
      rawNormalProjectionAngleRad: sourceFrame.rawNormalProjectionAngleRad, quaternion: sourceFrame.quaternion.toArray() },
    targetFrame: { determinant: targetFrame.determinant, rawNormalLongAxisDot: targetFrame.rawNormalLongAxisDot,
      rawNormalProjectionAngleRad: targetFrame.rawNormalProjectionAngleRad, quaternion: targetFrame.quaternion.toArray() },
    deltaWorldQuaternion: delta.toArray(), sourceBindWorldQuaternion: bindQ.toArray(),
    targetRestWorldQuaternion: targetRestQ.toArray(), sourceWorldOffset: sourceOffset.toArray(),
    socketLocalPosition: localOffset.toArray(), targetWorldOffset: targetOffset.toArray(),
    targetJoint: targetJoint.toArray(), socketLocalQuaternion: socketLocalQ.toArray(),
    sourceBindSocketWorldQuaternion: sourceBindSocketQ.toArray(), targetSocketRestWorldQuaternion: targetSocketQ.toArray(),
    rigidSourceWorldToRidingWorldMatrix: rigid.toArray(), checks: { pointErrorM: pointError, normalAxisError: normalError,
      longAxisError: longError, socketAngleErrorRad: orientationError, quaternionUnitError: qUnitError,
      rotationDeterminant: rigid.determinant(), offsetLengthErrorM: Math.abs(targetOffset.length() - sourceOffset.length()) },
  };
}

function main() {
  const evidenceRoot = path.resolve('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01');
  const out = path.resolve(process.argv.find(x => x.startsWith('--out='))?.slice(6) ?? path.join(evidenceRoot, 'contact-adapter01'));
  fs.mkdirSync(out, { recursive: true });
  const inputs = ['native-landmarks/cuff-runtime-frames.json', 'native-landmarks/surface-witness.json',
    'native-landmarks/report.json', 'runtime-audit/production-runtime-contract.json'].map(p => path.join(evidenceRoot, p));
  const sources = [...inputs, path.resolve('src/core/riderGeometry.ts'), path.resolve('src/render/hero/gltfRider.ts'),
    path.resolve('harness/hero-remaster/new-rider-contact-adapter.mts')].map(p => ({ path: p, sha256: hash(p) }));
  const frames = JSON.parse(fs.readFileSync(inputs[0]!, 'utf8'));
  const witnesses = JSON.parse(fs.readFileSync(inputs[1]!, 'utf8'));
  const landmarks = JSON.parse(fs.readFileSync(inputs[2]!, 'utf8'));
  const R = frames.rotationSourceBlenderToRuntime as number[][];
  const transport = (p: V3): V3 => R.map(row => row.reduce((v, c, i) => v + c * p[i]!, 0)) as V3;
  const sideMap = new Map<Side, Side>(frames.runtimeHands.map((h: {nativeSide:Side;runtimeContractSide:Side}) => [h.nativeSide,h.runtimeContractSide]));
  assert(sideMap.get('L') === 'R' && sideMap.get('R') === 'L', 'Explicit native-to-runtime side map required');
  const determinantR = new THREE.Matrix4().set(R[0]![0]!,R[0]![1]!,R[0]![2]!,0,R[1]![0]!,R[1]![1]!,R[1]![2]!,0,R[2]![0]!,R[2]![1]!,R[2]![2]!,0,0,0,0,1).determinant();
  assert(Math.abs(determinantR - 1) < 1e-12, 'Coordinate transform must not reflect source');
  const authoringChoices = {
    hand: { targetPalmFacingAxis: [1,0,0], targetFingerLongAxis: [0,-1,0], targetSocketQuaternion: [0,0,0,1],
      sourceBindBasis: 'NEW bone local +Y=fingerLongAxis, +Z=projected palmFacingAxis; mathematical prototype, parent must use actual exported bind quaternion',
      targetEvidence: 'Declared rear-side palm approach/fingers downward hypothesis; not measured grip articulation or accepted fit',
      contactEvidence: 'Actual negative-canonical palm surface witness; socket on grip axis is an authoring hypothesis, not cylinder surface fit' },
    foot: { targetSoleNormalAxis: [0,-1,0], targetToeAxis: [1,0,0], sourceSoleNormalBlender: [0,0,-1], sourceToeAxisBlender: [0,-1,0],
      sourceJointEstimatesBlender: { L: [.18,.045,.115], R: [-.18,.045,.115] },
      sourceContactEvidence: 'Actual bottom2mm vertex centroid; selected diagnostic point is not accepted peg socket',
      jointEvidence: 'Explicit parent authoring estimate; ankle hidden under shoe, not a measured joint centre',
      axisEvidence: 'Bottom plane and reference-front authoring axes; local sole normal/toe direction still need surface/correspondence refinement' },
  };
  const hands = frames.runtimeHands.map((h: {nativeSide:Side;runtimeContractSide:Side;wrist:{axleMidpointFrame:V3};actualPalmSurfaceWitness:{axleMidpointFrame:V3};fingerLongAxis:V3;palmFacingAxis:V3}) => {
    const sourceFrame = anatomicalFrame(h.fingerLongAxis,h.palmFacingAxis);
    const surface = witnesses.surfaces.find((s: {side:Side}) => s.side === h.nativeSide);
    const hit = surface.hits.find((hit: {canonicalNormalSign:number}) => hit.canonicalNormalSign === -1);
    const contact = transport(hit.point);
    assert(vec(contact).distanceTo(vec(h.actualPalmSurfaceWitness.axleMidpointFrame)) < 1e-9, 'Actual surface witness mismatch');
    const side = h.runtimeContractSide, sign = side === 'L' ? 1 : -1;
    const adapter = deriveContactAdapter({ side, sourceJoint: h.wrist.axleMidpointFrame, sourceContact: contact,
      sourceLongAxis: h.fingerLongAxis, sourceNormalAxis: h.palmFacingAxis,
      bindWorldQuaternion: sourceFrame.quaternion.toArray() as Q4, targetLongAxis: [0,-1,0], targetNormalAxis: [1,0,0],
      targetContact: [RIDER_PROFILE.grip.x,RIDER_PROFILE.grip.y,sign*RIDER_PROFILE.grip.z], targetSocketWorldQuaternion: [0,0,0,1] });
    return { nativeSide:h.nativeSide,runtimeSide:side,sourceSurfaceTriangleVertices:hit.sourceTriangleVertices,
      actualSurfaceNormalRuntime:transport(hit.normal),canonicalFrameNormalVersusLocalTriangleNormalAngleRad:vec(transport(hit.normal)).angleTo(vec(h.palmFacingAxis)),
      actualSurfaceNormalAfterRotation:vec(transport(hit.normal)).applyQuaternion(quat(adapter.deltaWorldQuaternion)).toArray(),adapter };
  });
  const feet = landmarks.soleSurfaceWitnesses.map((s: {nativeAnatomicalSide:Side;bottom2mmVertexCentroid:V3;bottom2mmVertexCount:number}) => {
    const side=sideMap.get(s.nativeAnatomicalSide)!,sign=side==='L'?1:-1;
    const jointAuthoring=authoringChoices.foot.sourceJointEstimatesBlender[s.nativeAnatomicalSide] as V3;
    const sourceLong=transport([0,-1,0]),sourceNormal=transport([0,0,-1]);
    const sourceFrame=anatomicalFrame(sourceLong,sourceNormal);
    const adapter=deriveContactAdapter({side,sourceJoint:transport(jointAuthoring),sourceContact:transport(s.bottom2mmVertexCentroid),
      sourceLongAxis:sourceLong,sourceNormalAxis:sourceNormal,bindWorldQuaternion:sourceFrame.quaternion.toArray() as Q4,
      targetLongAxis:[1,0,0],targetNormalAxis:[0,-1,0],targetContact:[RIDER_PROFILE.peg.x,RIDER_PROFILE.peg.y+.011,sign*RIDER_PROFILE.peg.z],targetSocketWorldQuaternion:[0,0,0,1]});
    return {nativeSide:s.nativeAnatomicalSide,runtimeSide:side,sourceSurfaceWitnessVertexCount:s.bottom2mmVertexCount,
      sourceJointStatus:'Parent estimate, not measured',adapter,legacyPhysicalAnkle:[RIDER_PROFILE.ankle.x,RIDER_PROFILE.ankle.y,sign*RIDER_PROFILE.ankle.z],
      adaptedAnkleMinusLegacyPhysicalAnkle:vec(adapter.targetJoint).sub(new THREE.Vector3(RIDER_PROFILE.ankle.x,RIDER_PROFILE.ankle.y,sign*RIDER_PROFILE.ankle.z)).toArray()};
  });
  const poseInputs=[{name:'authored-seated-profile',lean:0,hipX:RIDER_PROFILE.poses[1].hipX,hipY:RIDER_PROFILE.poses[1].hipY,torsoDegrees:RIDER_PROFILE.poses[1].torso},
    ...[-1,1].map(lean=>{const p=riderPoseAtLean(lean,makeRiderRigPose());return{name:lean<0?'maximum-back-profile':'maximum-forward-profile',lean,hipX:p.hips.x,hipY:p.hips.y,torsoDegrees:p.torsoAngle*180/Math.PI};}),
    {name:'landing-recovery-diagnostic',lean:0,hipX:-.40,hipY:.70,torsoDegrees:40}];
  const estimates={hipHalf:.105,shoulderHalf:.205,sourceHipBlender:[.105,.015,.90],sourceShoulderBlender:[.205,.02,1.38],
    sourceElbowBlender:[.285,.025,1.125],sourceKneeBlender:[.145,0,.50],sourceAnkleBlender:[.18,.045,.115]};
  const upperArmLength=Math.sqrt((.285-.205)**2+(.025-.02)**2+(1.125-1.38)**2);
  const forearmLengths=hands.map(h=>({side:h.runtimeSide,length:vec(h.adapter.input.sourceJoint).distanceTo(transport([h.nativeSide==='L'?.285:-.285,.025,1.125]))}));
  const thighLength=vec(estimates.sourceHipBlender).distanceTo(vec(estimates.sourceKneeBlender));
  const shinLength=vec(estimates.sourceKneeBlender).distanceTo(vec(estimates.sourceAnkleBlender));
  const reach=poseInputs.map(p=>{
    const physical=riderRigFromHips(p.hipX,p.hipY,p.torsoDegrees*Math.PI/180,makeRiderRigPose());
    const beforePhysical=JSON.stringify(physical);
    const limbs=hands.map(h=>{const side=h.runtimeSide,sign=side==='L'?1:-1;
      const foot=feet.find((f:{runtimeSide:Side})=>f.runtimeSide===side)!;
      // Anatomical source offsets, not production rest positions, determine this provisional root layout.
      const torsoAxis=new THREE.Vector3(Math.cos(physical.torsoAngle),Math.sin(physical.torsoAngle),0);
      const shoulder=new THREE.Vector3(physical.hips.x,physical.hips.y,sign*estimates.shoulderHalf)
        .addScaledVector(torsoAxis,1.38-.90);
      const hip=new THREE.Vector3(physical.hips.x,physical.hips.y,sign*estimates.hipHalf);
      const armD=shoulder.distanceTo(vec(h.adapter.targetJoint)),legD=hip.distanceTo(vec(foot.adapter.targetJoint));
      const armA=upperArmLength,armB=forearmLengths.find(x=>x.side===side)!.length;
      const limits=(d:number,a:number,b:number)=>({distanceM:d,segmentLengthsM:[a,b],sumM:a+b,minReachM:Math.abs(a-b),
        maxReachM:a+b,shortfallM:Math.max(0,d-a-b,Math.abs(a-b)-d),reachRatio:d/(a+b),
        additiveSafe:d>=(Math.abs(a-b)+.02)&&d<=(a+b)*.995});
      return{side,estimatedShoulder:shoulder.toArray(),estimatedHip:hip.toArray(),hand:limits(armD,armA,armB),foot:limits(legD,thighLength,shinLength)};
    });
    assert(JSON.stringify(physical)===beforePhysical,'Adapter mutated physical pose/COM');
    return{input:p,physicalPose:physical,limbs,physicalPoseUnchanged:true,status:'Synthetic profile inputs with explicitly estimated NEW roots; not authored animation, live engine frames or joint-fit acceptance'};
  });
  // Generic noncanonical NEW bind orientation must work too; preserving bind is not the same as preserving target restQ.
  const arbitraryBind=quat([.2,-.3,.1,.9]).toArray() as Q4;
  const arbitraryTest=deriveContactAdapter({...hands[0]!.adapter.input,bindWorldQuaternion:arbitraryBind});
  const invalidCases=[];
  for(const input of [{longAxis:[0,0,0],normalAxis:[1,0,0]},{longAxis:[1,0,0],normalAxis:[1,0,0]}]) {
    let rejected=false;try{anatomicalFrame(input.longAxis as V3,input.normalAxis as V3);}catch{rejected=true;}assert(rejected);invalidCases.push({...input,rejected});
  }
  const after=sources.map(s=>({path:s.path,sha256:hash(s.path)}));
  assert(sources.every((s,i)=>s.sha256===after[i]!.sha256),'Protected/source file changed');
  const worstChecks=maxAbs([...hands,...feet].flatMap(h=>Object.entries(h.adapter.checks).filter(([k])=>k!=='rotationDeterminant').map(([,v])=>v)));
  const report={schema:'rockhop.private-new-rider-contact-adapter.v1',status:'Mathematical prototype only, not applied to runtime or assets',
    sources,sourceHashesAfter:after,sourcesUnchanged:true,coordinateRotation:R,coordinateRotationDeterminant:determinantR,
    explicitNativeToRuntimeSideMapping:Object.fromEntries(sideMap),authoringChoices,hands,feet,reachDiagnostics:reach,
    checks:{maximumNumericalError:worstChecks,arbitraryNewBindQuaternionTest:arbitraryTest.checks,invalidFramesRejected:invalidCases,
      properRotationsOnly:true,quaternionsUnit:true,sourceBindPreserved:true,physicalPoseAndCOMUnchanged:true},
    minimalRuntimeProposal:{preserve:['source inverse binds','source skeleton restLocalP/restLocalQ','q0/d0 for source swing reference','RIDER_PROFILE','riderRigFromCOM and existing chain elbow/knee/COM authority'],
      explicitNewMetadata:['per-side source bind quaternion','target riding hand/foot world quaternion','bone-local socket position and quaternion','target socket world quaternion','native-to-runtime side mapping','contact witness provenance'],
      renderOnlyChanges:['solveArm wristTarget = physical grip − metadata rotated NEW wrist-to-socket offset','solveLeg ankleTarget = physical sole target − metadata rotated NEW ankle-to-sole offset','setWorld(hand/foot, targetRestWorldQ) instead of source q0','gripRestQ angular diagnostic must use metadata target socket world Q','Garage still authors matching seated clip contacts; no automatic IK correction'],
      requirement:'Explicit render metadata adapter proposal; no implementation or player asset promotion is included here'},
    limits:['Palm approach/finger direction are declared hypotheses, not accepted articulation','Actual source palm triangle normal differs from canonical plane; projection diagnostic is explicit','Surface witness placed at grip axis does not prove cylindrical surface fit; refine true contact radius and finger wrap','Bottom2mm vertex centroid is not accepted sole contact point; ankle/root centres estimated under clothes','Estimated NEW arm lengths may not reach physical maximum-lean poses; expose shortfalls and fit actual new roots/lengths','No pose deformation, cuff continuity in motion, Garage clip, standing-to-chair clip, surface collision, engine rendering or playback evidence','Historical production geometry and rest quaternions are never donors; no GPU or player assets touched']};
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,sourcesUnchanged:true,checks:report.checks,
    hands:hands.map(h=>({nativeSide:h.nativeSide,runtimeSide:h.runtimeSide,targetWrist:h.adapter.targetJoint,targetOffset:h.adapter.targetWorldOffset})),
    feet:feet.map((f:{runtimeSide:Side;adapter:ReturnType<typeof deriveContactAdapter>;adaptedAnkleMinusLegacyPhysicalAnkle:number[]})=>({runtimeSide:f.runtimeSide,targetAnkle:f.adapter.targetJoint,ankleDifference:f.adaptedAnkleMinusLegacyPhysicalAnkle})),
    reach:reach.map(r=>({name:r.input.name,limbs:r.limbs.map(l=>({side:l.side,armShortfall:l.hand.shortfallM,legShortfall:l.foot.shortfallM,armReach:l.hand.reachRatio,legReach:l.foot.reachRatio}))}))},null,2));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(path.resolve(process.argv[1])).href)main();
