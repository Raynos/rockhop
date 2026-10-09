/** Geometric contact IK. Fixed material point targets, joint rotations only.
 * No parameter grid and no coordinate descent. Never player-accepted here.
 */
import fs from 'node:fs';
import {validateSurface} from './surface-validation.mjs';
import {Vector3,Quaternion,Matrix4,Triangle,Ray} from 'three';
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x)),rad=d=>d*Math.PI/180;
function linearSolve(a,b){const n=b.length,A=a.map((r,i)=>[...r,b[i]]);for(let k=0;k<n;k++){let pivot=k;for(let i=k+1;i<n;i++)if(Math.abs(A[i][k])>Math.abs(A[pivot][k]))pivot=i;if(Math.abs(A[pivot][k])<1e-14)return Array(n).fill(0);[A[k],A[pivot]]=[A[pivot],A[k]];const v=A[k][k];for(let j=k;j<=n;j++)A[k][j]/=v;for(let i=0;i<n;i++)if(i!==k){const f=A[i][k];for(let j=k;j<=n;j++)A[i][j]-=f*A[k][j];}}return A.map(r=>r[n]);}
// Damped differential IK simultaneously solves the contact equations. Bounds
// limit actual additional joint flex; target itself is fixed before iteration.
function solve(seed,bounds,evaluate,iterations=60){let x=[...seed],trace=[];const norm=r=>r.reduce((a,b)=>a+b*b,0);for(let it=0;it<iterations;it++){const r=evaluate(x),error=norm(r);trace.push({it,error,values:[...x]});if(error<1e-10)break;const columns=x.map((_,k)=>{const v=[...x];v[k]+=.0001;const s=evaluate(v);return s.map((y,i)=>(y-r[i])/.0001);});const A=x.map((_,i)=>x.map((_,j)=>columns[i].reduce((s,v,k)=>s+v*columns[j][k],i===j?1e-8:0))),b=x.map((_,i)=>-columns[i].reduce((s,v,k)=>s+v*r[k],0));let step=linearSolve(A,b),length=Math.hypot(...step);if(length>.3)step=step.map(v=>v*.3/length);let accepted=false;for(let k=0;k<8;k++){const q=x.map((v,i)=>clamp(v+step[i]*2**-k,...bounds[i]));if(norm(evaluate(q))<error){x=q;accepted=true;break;}}if(!accepted)break;}return {values:x,residual:evaluate(x),trace};}
export async function construct(c){
 const {side,hand,meta,source,nodes,rest,root,bone,P,V,I,Q,w,place,matrices,skinned,sourceRows,names,idx,pos,handOwned,rigid,labels,nearest,triangles,axisA,axisU,centre,grip,pad,bar,newP,newQ,output}=c;
 const update=()=>root.updateMatrixWorld(true),restQ=id=>rest[nodes.indexOf(bone(id))].q;
 const setFlex=(id,value)=>bone(id).quaternion.copy(restQ(id)).multiply(Q().setFromAxisAngle(V(meta.driver.digitFlex[side][id].axisLocal),value));
 const material=(label)=>{const m=matrices(),samples=label.pulp.rows.map(i=>skinned(sourceRows[i],m)),point=samples.reduce((v,s,i)=>v.addScaledVector(s.p,label.pulp.barycentric[i]),new Vector3()),normal=samples.reduce((v,s,i)=>v.addScaledVector(s.n,label.pulp.barycentric[i]),new Vector3()).normalize();return {point,normal};};
 const radial=p=>{const q=p.clone().sub(axisA);return q.addScaledVector(axisU,-q.dot(axisU));};
 const barTarget=(axial,angle,clearance=.0006)=>{const x=V([1,0,0]).addScaledVector(axisU,-axisU.x).normalize(),y=new Vector3().crossVectors(axisU,x);if(y.y<0)y.negate();const out=x.multiplyScalar(Math.cos(angle)).addScaledVector(y,Math.sin(angle)),base=axisA.clone().addScaledVector(axisU,axial),ray=new Ray(base,out),hits=triangles.flatMap((t,i)=>{const p=ray.intersectTriangle(t.a,t.b,t.c,false,new Vector3());return p?[{point:p,normal:t.getNormal(new Vector3()),triangle:i}]:[];});hits.sort((a,b)=>a.point.distanceTo(base)-b.point.distanceTo(base));if(!hits.length)throw Error('Finite contact target missing');const hit=hits[0];if(hit.normal.dot(out)<0)hit.normal.negate();return {...hit,point:hit.point.clone().addScaledVector(hit.normal,clearance),axial,angle};};
 const angularRest=id=>{const b=bone(id),axis=V(meta.driver.digitFlex[side][id].axisLocal).applyQuaternion(b.getWorldQuaternion(Q())),a=V([0,1,0]).applyQuaternion(b.parent.getWorldQuaternion(Q())),v=V([0,1,0]).applyQuaternion(b.getWorldQuaternion(Q()));a.addScaledVector(axis,-a.dot(axis)).normalize();v.addScaledVector(axis,-v.dot(axis)).normalize();return Math.atan2(axis.dot(new Vector3().crossVectors(a,v)),a.dot(v));};
 const restAngles=Object.fromEntries(Object.values(hand.digits).flat().map(id=>[id,angularRest(id)]));
 const outcomes={},clearance=.0008;
 const ownRows=sourceRows.map((row,i)=>({row,i})).filter(({row,i})=>i%32===0&&handOwned(row)),dominant=row=>names[row.fields.reduce((a,b)=>a.weight>b.weight?a:b).joint];
 const minimum=rows=>{const m=matrices();let best={gap:Infinity};for(const {row,i}of rows){const sample=skinned(row,m),axial=sample.p.clone().sub(axisA).dot(axisU);if(axial<-.003||axial>.169)continue;const rr=radial(sample.p).length();if(rr>.045&&best.gap<.015)continue;const near=nearest(sample.p);if(near.signed<best.gap)best={gap:near.signed,row:i,point:sample.p.toArray(),normal:sample.n.toArray(),normalDot:sample.n.dot(near.n),barPoint:near.q.toArray()};}return best;};
 const supportRows=ownRows.filter(({row})=>rigid.has(dominant(row)));
 const supportTrace=[];for(let it=0;it<12;it++){const contact=minimum(supportRows);supportTrace.push(contact);if(contact.gap>=clearance)break;const shift=bar.n.clone().multiplyScalar(Math.max(.0005,clearance-contact.gap));const matrix=w.matrixWorld.clone();matrix.setPosition(w.getWorldPosition(new Vector3()).add(shift));place(matrix);}
 for(const [digit,chain]of Object.entries(hand.digits)){
  if(digit==='thumb')continue;
  const bounds=chain.map((id,k)=>[0,rad([85,95,80][k])-restAngles[id]]),values=[],contacts=[];
  for(const [k,id]of chain.entries()){
   const rows=ownRows.filter(({row})=>dominant(row)===id),evaluate=theta=>{setFlex(id,theta);update();return minimum(rows);};
   let theta=0,last=evaluate(0),chosen=last;const steps=[{theta,contact:last}];
   if(last.gap>clearance){while(theta<bounds[k][1]){const next=Math.min(bounds[k][1],theta+rad(5)),contact=evaluate(next);steps.push({theta:next,contact});if(contact.gap<=clearance){let lo=theta,hi=next;for(let it=0;it<30;it++){const mid=(lo+hi)/2;if(evaluate(mid).gap<=clearance)hi=mid;else lo=mid;}theta=lo;chosen=evaluate(theta);break;}theta=next;last=contact;chosen=contact;}}
   values.push(theta);contacts.push({id,...chosen,steps});
  }
  const sample=material(labels[digit][2]),near=nearest(sample.point);
  outcomes[digit]={method:'Sequential positive hinge closure to first actual segment-skin contact;5degree swept brackets then30bisections, no multi-parameter fit',values,bounds,contacts,target:{point:near.q.toArray(),normal:near.n.toArray()},point:sample.point.toArray(),normal:sample.normal.toArray(),normalDot:sample.normal.dot(near.n),gapM:near.signed,residual:[Math.max(0,near.signed-clearance)],trace:[],jointQuaternions:chain.map(id=>bone(id).quaternion.toArray())};
 }

 {
  const chain=hand.digits.thumb,cmc=bone(chain[0]),label=labels.thumb[2];
  if(!label.pulp.rows.every(row=>sourceRows[row].fields.every(f=>chain.includes(names[f.joint]))))throw Error('Thumb material crosses CMC subtree; rigid invariant invalid');
  const origin=P(chain[0]),thumbRows=ownRows.filter(({row})=>chain.includes(dominant(row))),fingerAxial=Object.values(hand.digits).filter(v=>v!==chain).map(v=>P(v[0]).sub(axisA).dot(axisU)),span=[Math.min(...fingerAxial)-.015,Math.max(...fingerAxial)+.015],faceTrials=[],candidates=[];
  const pose=s=>{setFlex(chain[0],0);setFlex(chain[1],rad(10+50*s)-restAngles[chain[1]]);setFlex(chain[2],rad(25+55*s)-restAngles[chain[2]]);update();const sample=material(label),reach=sample.point.clone().sub(origin);return {reach,normal:sample.normal,invariant:reach.dot(sample.normal),length:reach.length()};};
  const endpointStates=[pose(0),pose(1)],endpoints=endpointStates.map(v=>({dot:v.invariant,length:v.length}));
  for(const [faceId,t]of triangles.entries()){
   const planeNormal=t.getNormal(new Vector3()),mid=t.getMidpoint(new Vector3());if(planeNormal.dot(radial(mid))<0)planeNormal.negate();if(planeNormal.y>-.25)continue;
   const planePoint=mid.clone().addScaledVector(planeNormal,clearance),signedRootPlane=origin.clone().sub(planePoint).dot(planeNormal),bracket=(endpoints[0].dot-signedRootPlane)*(endpoints[1].dot-signedRootPlane)<=0,trial={faceId,planeNormal:planeNormal.toArray(),signedRootPlane,bracket};faceTrials.push(trial);if(!bracket)continue;
   let lo=0,hi=1;for(let i=0;i<48;i++){const m=(lo+hi)/2,v=pose(m);if((endpoints[0].dot-signedRootPlane)*(v.invariant-signedRootPlane)>0)lo=m;else hi=m;}const coupling=(lo+hi)/2,state=pose(coupling),u=axisU.clone().addScaledVector(planeNormal,-axisU.dot(planeNormal)).normalize(),delta=planePoint.clone().sub(origin),B=delta.dot(u),C=delta.lengthSq()-state.length**2,D=B*B-C;trial.coupling=coupling;trial.discriminant=D;if(D<0)continue;
   for(const distance of [-B-Math.sqrt(D),-B+Math.sqrt(D)]){
    const point=planePoint.clone().addScaledVector(u,distance),axial=point.clone().sub(axisA).dot(axisU),near=nearest(point);if(axial<span[0]||axial>span[1]||near.distance<clearance-.0004||near.distance>clearance+.0004)continue;
    pose(coupling);const wanted=point.clone().sub(origin),frame=(f,n)=>{const x=f.clone().normalize(),y=n.clone().addScaledVector(x,-n.dot(x)).normalize();return I().makeBasis(x,y,new Vector3().crossVectors(x,y));},rotate=Q().setFromRotationMatrix(frame(wanted,planeNormal.clone().negate()).multiply(frame(state.reach,state.normal).invert()));
    const world=rotate.clone().multiply(cmc.getWorldQuaternion(Q()));cmc.quaternion.copy(cmc.parent.getWorldQuaternion(Q()).invert().multiply(world));update();const sample=material(label),actual=nearest(sample.point),collision=minimum(thumbRows);
    candidates.push({faceId,coupling,axial,point:sample.point.toArray(),normal:sample.normal.toArray(),normalDot:sample.normal.dot(actual.n),gapM:actual.signed,target:{point:point.toArray(),normal:planeNormal.toArray()},positionErrorM:sample.point.distanceTo(point),CMCrotationRadians:2*Math.acos(Math.abs(clamp(rotate.w,-1,1))),collision,jointQuaternions:chain.map(id=>bone(id).quaternion.toArray())});
   }
  }
  candidates.sort((a,b)=>{const ap=Math.max(0,-a.collision.gap-.0005),bp=Math.max(0,-b.collision.gap-.0005);return ap-bp||a.CMCrotationRadians-b.CMCrotationRadians;});
  if(candidates.length){const best=candidates[0];chain.forEach((id,i)=>bone(id).quaternion.fromArray(best.jointQuaternions[i]));update();outcomes.thumb={...best,endpoints,axialSpan:span,faceTrials,candidates,values:[best.coupling],residual:[best.positionErrorM],trace:[]};}
  else {pose(0);outcomes.thumb={failed:'No finite lower-face reach-circle intersection inside anatomical hand axial span under declared MCP10to60/IP25to80degree coupling',endpoints,axialSpan:span,faceTrials,residual:[1],trace:[],values:[]};}
 }

 const m=matrices(),allIds=Object.values(hand.digits).flat(),points=[],inside=[];let maxPenetration=0;
 for(let i=0;i<sourceRows.length;i++){const row=sourceRows[i];if(!handOwned(row))continue;const s=skinned(row,m),r=radial(s.p),axial=s.p.clone().sub(axisA).dot(axisU);if(i%64===0)points.push({row:i,point:s.p.toArray(),normal:s.n.toArray(),dominantJoint:names[row.fields.reduce((a,b)=>a.weight>b.weight?a:b).joint]});if(r.length()>.023||axial<0||axial>.1658764601+.003)continue;const n=nearest(s.p);if(n.signed<0){if(inside.length<20)inside.push({row:i,point:s.p.toArray(),gap:n.signed});maxPenetration=Math.max(maxPenetration,-n.signed);}}
 const bones=Object.entries(hand.digits).map(([digit,chain])=>({digit,joints:chain.map(id=>({id,head:P(id).toArray(),tail:V([0,labels[digit].find(l=>l.id===id).length,0]).applyMatrix4(bone(id).matrixWorld).toArray()}))}));
 const fullSurface=validateSurface(c);
 const evidence={accepted:false,supportTrace,fullSurface,method:'Damped differential IK of fixed source pulp material against explicit finite targets; no coordinate descent or parameter grid',wristPositionBike:w.getWorldPosition(new Vector3()).toArray(),wristQuaternionBike:w.getWorldQuaternion(Q()).toArray(),outcomes,insideWitnesses:inside,maximumPenetrationM:maxPenetration};
 fs.writeFileSync(output+'/geometry-'+side+'.json',JSON.stringify({side,bar:triangles.map(t=>[t.a.toArray(),t.b.toArray(),t.c.toArray()]),points,bones,contacts:Object.entries(outcomes).map(([digit,o])=>({digit,point:o.point??null,target:o.target?.point??null}))})+'\n');
 fs.writeFileSync(output+'/profile-'+side+'.json',JSON.stringify(evidence,null,2)+'\n');console.log(JSON.stringify({side,maximumPenetrationM:maxPenetration,contacts:Object.fromEntries(Object.entries(outcomes).map(([digit,o])=>[digit,{gap:o.gapM,normal:o.normalDot,error:Math.hypot(...o.residual),values:o.values,steps:o.trace.length}]))}));return evidence;
}
