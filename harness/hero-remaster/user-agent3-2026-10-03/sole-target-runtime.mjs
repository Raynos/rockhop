/** Private socket offset experiment; marker contact remains a proposal. */
export function installSoleTargetExperiment(debug){
  const rider=debug.rider,T=debug.THREE,frame=debug.bike.frame;if(!rider.debug.physicalPose)throw new Error('Authoritative physical pose required');
  rider.scene.updateMatrixWorld(true);const offsets=[];
  for(const side of['L','R']){const foot=rider.scene.getObjectByName('foot'+side),sole=rider.scene.getObjectByName('soleSocket'+side);if(!foot||!sole||sole.parent!==foot)throw new Error('Exact native foot-child marker required');
    const p=frame.worldToLocal(foot.getWorldPosition(new T.Vector3())),s=frame.worldToLocal(sole.getWorldPosition(new T.Vector3()));offsets.push(s.sub(p));}
  const original=rider.solveLeg;if(typeof original!=='function')throw new Error('Renderer leg target hook missing');const calls=[];
  rider.solveLeg=function(chain,side){const old=chain.ankle[side].clone(),target=new T.Vector3(-.14,.031,side===0?.2:-.2).sub(offsets[side]);
    chain.ankle[side].copy(target);try{original.call(this,chain,side);calls.push({side,legacyAnkle:old.toArray(),socketAnkleTarget:target.toArray()});}finally{chain.ankle[side].copy(old);}};
  return{offsets:offsets.map(p=>p.toArray()),calls,restore(){rider.solveLeg=original;},limits:['Targets the existing05 BODY-centroid sole marker, not a qualified new boot outsole support patch.',
    'Only private renderer chain ankle target changes. No Game physics, source bind/weights/topology, pelvis target or pose clips mutate.',
    'Sole target mismatch must not be hidden by limb scaling or physics displacement. Native bone segment lengths/reach, actual marker error and independent COM proxy are measured.']};
}
/** Existing declared segment centroid/mass fractions, measured from posed bones. */
export function measuredNativeBoneMassProxy(debug,physicsState){
  const T=debug.THREE,frame=debug.bike.frame,scene=debug.rider.scene;
  const point=name=>frame.worldToLocal(scene.getObjectByName(name).getWorldPosition(new T.Vector3()));
  const direction=name=>new T.Vector3(0,1,0).transformDirection(new T.Matrix4().copy(frame.matrixWorld).invert().multiply(scene.getObjectByName(name).matrixWorld));
  const hips=point('pelvis').addScaledVector(direction('pelvis'),.02),shoulder=point('neck'),sum=new T.Vector3().lerpVectors(hips,shoulder,.5).multiplyScalar(.4346);
  sum.addScaledVector(shoulder.clone().addScaledVector(direction('neck'),.175),.0694);
  for(const side of['L','R']){for(const[a,b,fraction,mass]of[['upperArm','forearm',.5772,.0271],['forearm','hand',.4574,.0162],['thigh','shin',.4095,.1416],['shin','foot',.4395,.0433]])sum.addScaledVector(point(a+side).lerp(point(b+side),fraction),mass);
    sum.addScaledVector(point('gripSocket'+side),.0061);sum.addScaledVector(point('foot'+side).add(new T.Vector3(.06,-.055,0)),.0137);}
  const actual=frame.worldToLocal(new T.Vector3(physicsState.riderBody.pos.x,physicsState.riderBody.pos.y,0));return{measured:sum.toArray(),physicalCOM:actual.toArray(),residualM:sum.distanceTo(actual),limits:'Existing segment fractions measured from native bones, not fitted body-volume mass. Analytical renderer debug residual is not this independent proxy.'};
}
