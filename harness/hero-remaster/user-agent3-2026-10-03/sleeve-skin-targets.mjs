/** Canonical source-weighted garment/body skinning and local clearance. */
import {Vector3, Matrix4, Triangle} from 'three';
const nativeToFile=p=>new Vector3(p[0]+.65,p[2],-p[1]);
export function liveSleeveTargets(debug,handoff){
  const rider=debug.rider,bodyMesh=rider.sleeveGeometry.find(p=>p.mesh.geometry.attributes.position.count===9981)?.mesh;
  if(!bodyMesh)throw new Error('Exact canonical body template missing');
  rider.scene.updateMatrixWorld(true);bodyMesh.skeleton.update();
  const palette=new Map(bodyMesh.skeleton.bones.map((b,i)=>[b.name,new Matrix4().multiplyMatrices(b.matrixWorld,bodyMesh.skeleton.boneInverses[i])]));
  if(palette.size!==51)throw new Error('Complete native bind missing');
  const skin=(p,weights)=>{const input=nativeToFile(p).applyMatrix4(bodyMesh.bindMatrix),result=new Vector3();let total=0;
    for(const[name,w]of weights){const matrix=palette.get(name.replaceAll('.',''));if(!matrix)throw new Error('Missing collider skin joint '+name);result.addScaledVector(input.clone().applyMatrix4(matrix),w);total+=w;}
    if(Math.abs(total-1)>2e-6)throw new Error('Collider weight sum');return result.multiplyScalar(1/total).applyMatrix4(bodyMesh.bindMatrixInverse).applyMatrix4(bodyMesh.matrixWorld);};
  const pattern=handoff.pattern,body=handoff.nativeConsumedColliders.body;
  const currentBodyPositions=new Map();for(const v of body.relevantArmVertices){const p=v.generatedFromNativeIDs?
    v.generatedFromNativeIDs.reduce((sum,id)=>sum.add(currentBodyPositions.get(id)),new Vector3()).multiplyScalar(1/v.generatedFromNativeIDs.length):skin(v.restNativeM,v.weights);currentBodyPositions.set(v.bodyVertexID,p);}
  const bodyPositions=body.relevantArmVertices.map(v=>currentBodyPositions.get(v.bodyVertexID)),attribute=bodyMesh.geometry.attributes._source_id;
  if(!attribute)throw new Error('Canonical body ancestry missing');const rows=new Map();for(let i=0;i<attribute.count;i++){const id=attribute.getX(i);if(!rows.has(id))rows.set(id,[]);rows.get(id).push(i);}
  let sourceBodyMaximumResidualM=0,matchedNativeBodyVertices=0;
  for(let i=0;i<body.relevantArmVertices.length;i++){if(body.relevantArmVertices[i].generatedFromNativeIDs)continue;const sourceID=body.relevantArmVertices[i].bodyVertexID,indices=rows.get(sourceID);if(!indices)throw new Error('Collider native body vertex is not visible body '+sourceID);matchedNativeBodyVertices++;
    for(const row of indices)sourceBodyMaximumResidualM=Math.max(sourceBodyMaximumResidualM,bodyMesh.getVertexPosition(row,new Vector3()).applyMatrix4(bodyMesh.matrixWorld).distanceTo(bodyPositions[i]));}
  return{cloth:pattern.verticesNativeM.map((p,i)=>skin(p,pattern.weights[i])),body:bodyPositions,
    skinTemplate:{mesh:bodyMesh.name,bind:bodyMesh.bindMatrix.toArray(),bindInverse:bodyMesh.bindMatrixInverse.toArray(),world:bodyMesh.matrixWorld.toArray(),jointCount:palette.size,matchedNativeBodyVertices,sourceBodyMaximumResidualM}};
}
export function sleeveClearance(cloth,body,handoff){
  const ids=new Map(handoff.nativeConsumedColliders.body.relevantArmVertices.map((v,i)=>[v.bodyVertexID,i])),triangles=handoff.nativeConsumedColliders.body.relevantArmTriangles.map(t=>{
    const p=t.bodyVertexIDs.map(id=>body[ids.get(id)]),normal=p[1].clone().sub(p[0]).cross(p[2].clone().sub(p[0])).normalize();return{triangle:new Triangle(...p),normal,id:t.bodyTriangleID};});
  const samples=cloth.map((p,i)=>({p,kind:'vertex',id:i}));
  for(let i=0;i<handoff.pattern.triangleVertexIDs.length;i++){const p=handoff.pattern.triangleVertexIDs[i].map(id=>cloth[id]);samples.push({p:p[0].clone().add(p[1]).add(p[2]).multiplyScalar(1/3),kind:'centroid',id:i});}
  let minUnsignedM=Infinity,minLocalNormalM=Infinity,witness=null;const closest=new Vector3();
  for(const s of samples){let gap=Infinity,best=null,point=null;for(const t of triangles){t.triangle.closestPointToPoint(s.p,closest);const d=closest.distanceTo(s.p);if(d<gap){gap=d;best=t;point=closest.clone();}}
    const dot=s.p.clone().sub(point).dot(best.normal);minUnsignedM=Math.min(minUnsignedM,gap);if(dot<minLocalNormalM){minLocalNormalM=dot;witness={kind:s.kind,id:s.id,bodyTriangleID:best.id,sampleWorldM:s.p.toArray(),bodyWorldM:point.toArray(),bodyNormal:best.normal.toArray(),unsignedM:gap,localNormalM:dot};}}
  return{samples:samples.length,minUnsignedM,minLocalNormalM,witness,finite:cloth.every(p=>p.toArray().every(Number.isFinite)),
    limits:'Vertex/centroid nearest local face normal and unsigned distance only; open regional collider, not signed-volume or complete triangle intersection proof.'};
}
