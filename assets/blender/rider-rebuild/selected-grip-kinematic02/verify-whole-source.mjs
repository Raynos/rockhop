/** Fixed exported-profile verification. No fitting or source mutations. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {Vector3} from 'three';
import {validateSurface} from './surface-validation.mjs';
export {prepareControls} from './thumb-opposition-plane.mjs';
const profilePath='docs/evidence/rider-rebuild/selected-grip-kinematic02/thumbplane05/runtime-profile.json';
const bytes=fs.readFileSync(profilePath),profile=JSON.parse(bytes);
export function construct(c){
 const {side,source,nodes,rest,bone,V,I,Q,place,root,matrices,skinned,sourceRows,idx,handOwned,triangles,names,output}=c;
 assert.equal(profile.source.sha256,source.sha256);
 const p=profile.hands[side];
 place(I().compose(V(p.wristPositionBike),Q().fromArray(p.wristQuaternionBike),V([1,1,1])));
 for(const [id,control]of Object.entries(p.digitFlex)){
  const b=bone(id),r=rest[nodes.indexOf(b)];
  b.quaternion.copy(r.q).multiply(Q().setFromAxisAngle(V(control.axisLocal),control.maxRadians));
  assert.deepEqual(b.position.toArray(),r.p.toArray(),'Native digital translations preserved');
 }
 root.updateMatrixWorld(true);
 const full=validateSurface({...c,handOwned:()=>true});
 full.scope='Every vertex and triangle in the complete selected source glove primitive, with all four positive skin weights; no material, weight, palm, wrist or cuff exclusions. Foreign forearm joints remain at native rest in this offline fixture.';
 const m=matrices(),positions=sourceRows.map(row=>skinned(row,m).p),allowed=sourceRows.map(handOwned);
 const barMin=new Vector3(Infinity,Infinity,Infinity),barMax=new Vector3(-Infinity,-Infinity,-Infinity);
 for(const t of triangles)for(const v of [t.a,t.b,t.c]){barMin.min(v);barMax.max(v);}
 let excluded=0,disjoint=0,overlap=0;const foreign=new Set(),witnesses=[];
 const allowedNames=new Set([...c.rigid,...Object.values(c.hand.digits).flat()]);
 for(const row of sourceRows)if(!handOwned(row))for(const f of row.fields)if(!allowedNames.has(names[f.joint]))foreign.add(names[f.joint]);
 for(let i=0;i<idx.count;i+=3){
  const ids=[idx.get(i),idx.get(i+1),idx.get(i+2)];if(ids.every(id=>allowed[id]))continue;
  excluded++;const [a,b,d]=ids.map(id=>positions[id]),min=a.clone().min(b).min(d),max=a.clone().max(b).max(d);
  if(min.x>barMax.x||min.y>barMax.y||min.z>barMax.z||max.x<barMin.x||max.y<barMin.y||max.z<barMin.z)disjoint++;
  else{overlap++;if(witnesses.length<10)witnesses.push({triangle:i/3,rows:ids,min:min.toArray(),max:max.toArray()});}
 }
 const result={accepted:false,side,sourceSHA256:source.sha256,profilePath,profileSHA256:crypto.createHash('sha256').update(bytes).digest('hex'),fixedProfile:true,nativeDigitalTranslationsPreserved:true,sourceVertices:sourceRows.length,sourceTriangles:idx.count/3,previouslyHandOwnedTriangles:idx.count/3-excluded,previouslyExcludedTriangles:excluded,excludedTrianglesAABBDisjoint:disjoint,excludedTrianglesAABBOverlap:overlap,excludedOverlapWitnesses:witnesses,foreignPositiveInfluenceNames:[...foreign].sort(),finiteBarBounds:{min:barMin.toArray(),max:barMax.toArray()},fullSurface:full,limits:['No arm IK in this fixed offline fixture: forearm/cuff deformation must be rechecked after runtime limb IK and through moving leans.','Collision-clear geometry is not an anatomical or moving-art acceptance.','Both source bikes have identical exact grip surfaces, verified by the source loader.']};
 fs.writeFileSync(output+'/whole-source-'+side+'.json',JSON.stringify(result,null,2)+'\n');
 return result;
}
