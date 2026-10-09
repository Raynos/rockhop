/** Geometric contact IK. Fixed material point targets, joint rotations only.
 * No parameter grid and no coordinate descent. Never player-accepted here.
 */
import fs from 'node:fs';
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
 const outcomes={};
 for(const [digit,chain]of Object.entries(hand.digits)){
  if(digit==='thumb')continue;
  // A distal pulp point at rear/below the bar in its native MCP axial plane.
  // The point lies on an actual finite triangle. No arbitrary nearest-row fit.
  const axial=P(chain[0]).sub(axisA).dot(axisU),target=barTarget(axial,rad(220)),label=labels[digit][2];
  const bounds=chain.map((id,k)=>[0,rad([85,95,80][k])-restAngles[id]]);
  const evaluate=x=>{chain.forEach((id,k)=>setFlex(id,x[k]));update();const s=material(label);return s.point.sub(target.point).toArray();};
  const solved=solve(bounds.map(([a,b])=>.8*b),bounds,evaluate);const s=material(label),near=nearest(s.point);
  outcomes[digit]={...solved,bounds,restAngles:chain.map(id=>restAngles[id]),target:{point:target.point.toArray(),normal:target.normal.toArray(),triangle:target.triangle,axial:target.axial},point:s.point.toArray(),normal:s.normal.toArray(),normalDot:s.normal.dot(near.n),gapM:near.signed,jointQuaternions:chain.map(id=>bone(id).quaternion.toArray())};
 }
 {
  const chain=hand.digits.thumb,cmc=bone(chain[0]),label=labels.thumb[2];
  // Opposition crosses the thumb pulp toward the ring/MCP axial station on
  // the rear/below finite bar. This is anatomically separate from CMC roll.
  const axial=P(hand.digits.ring[0]).sub(axisA).dot(axisU),target=barTarget(axial,rad(225));
  const bounds=[[-Math.PI,Math.PI],[-Math.PI,Math.PI],[-Math.PI,Math.PI],[0,rad(60)-restAngles[chain[1]]],[0,rad(80)-restAngles[chain[2]]]];
  const evaluate=x=>{const axis=V(x.slice(0,3)),angle=axis.length();cmc.quaternion.copy(restQ(chain[0]));if(angle>0)cmc.quaternion.multiply(Q().setFromAxisAngle(axis.divideScalar(angle),angle));setFlex(chain[1],x[3]);setFlex(chain[2],x[4]);update();const s=material(label),e=s.point.clone().sub(target.point),n=s.normal.clone().add(target.normal).multiplyScalar(.025);return [...e.toArray(),...n.toArray()];};
  // Point-direction CMC swing seeds the simultaneous point/normal IK; its
  // residual can only be removed by articulated MCP/IP plus actual axial roll.
  evaluate([0,0,0,bounds[3][1]*.65,bounds[4][1]*.65]);const origin=P(chain[0]),from=material(label).point.sub(origin).normalize(),to=target.point.clone().sub(origin).normalize(),swing=Q().setFromUnitVectors(from,to),parent=cmc.parent.getWorldQuaternion(Q()),local=parent.clone().multiply(restQ(chain[0]));const localSwing=local.clone().invert().multiply(swing).multiply(local),angle=2*Math.acos(clamp(localSwing.w,-1,1)),seed=V([localSwing.x,localSwing.y,localSwing.z]).normalize().multiplyScalar(angle).toArray();
  const solved=solve([...seed,bounds[3][1]*.65,bounds[4][1]*.65],bounds,evaluate,100),s=material(label),near=nearest(s.point);
  outcomes.thumb={...solved,bounds,restAngles:chain.map(id=>restAngles[id]),target:{point:target.point.toArray(),normal:target.normal.toArray(),triangle:target.triangle,axial:target.axial},point:s.point.toArray(),normal:s.normal.toArray(),normalDot:s.normal.dot(near.n),gapM:near.signed,jointQuaternions:chain.map(id=>bone(id).quaternion.toArray())};
 }
 const m=matrices(),allIds=Object.values(hand.digits).flat(),points=[],inside=[];let maxPenetration=0;
 for(let i=0;i<sourceRows.length;i++){const row=sourceRows[i];if(!handOwned(row))continue;const s=skinned(row,m),r=radial(s.p),axial=s.p.clone().sub(axisA).dot(axisU);if(i%64===0)points.push({row:i,point:s.p.toArray(),normal:s.n.toArray(),dominantJoint:names[row.fields.reduce((a,b)=>a.weight>b.weight?a:b).joint]});if(r.length()>.023||axial<0||axial>c.describe?.bar?.length+.003)continue;const n=nearest(s.p);if(n.signed<0){if(inside.length<20)inside.push({row:i,point:s.p.toArray(),gap:n.signed});maxPenetration=Math.max(maxPenetration,-n.signed);}}
 const bones=Object.entries(hand.digits).map(([digit,chain])=>({digit,joints:chain.map(id=>({id,head:P(id).toArray(),tail:V([0,labels[digit].find(l=>l.id===id).length,0]).applyMatrix4(bone(id).matrixWorld).toArray()}))}));
 const evidence={accepted:false,method:'Damped differential IK of fixed source pulp material against explicit finite targets; no coordinate descent or parameter grid',wristPositionBike:w.getWorldPosition(new Vector3()).toArray(),wristQuaternionBike:w.getWorldQuaternion(Q()).toArray(),outcomes,insideWitnesses:inside,maximumPenetrationM:maxPenetration};
 fs.writeFileSync(output+'/geometry-'+side+'.json',JSON.stringify({side,bar:triangles.map(t=>[t.a.toArray(),t.b.toArray(),t.c.toArray()]),points,bones,contacts:Object.entries(outcomes).map(([digit,o])=>({digit,point:o.point,target:o.target.point}))})+'\n');
 fs.writeFileSync(output+'/profile-'+side+'.json',JSON.stringify(evidence,null,2)+'\n');console.log(JSON.stringify({side,maximumPenetrationM:maxPenetration,contacts:Object.fromEntries(Object.entries(outcomes).map(([digit,o])=>[digit,{gap:o.gapM,normal:o.normalDot,error:Math.hypot(...o.residual),values:o.values,steps:o.trace.length}]))}));return evidence;
}
