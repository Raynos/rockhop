/** Close only the explicit regional collider, preserving every source arm face. */
import assert from 'node:assert/strict';
export function closeArmCollider(handoff){
  const result=structuredClone(handoff),body=result.nativeConsumedColliders.body,edges=new Map();
  const key=(a,b)=>[a,b].sort((x,y)=>x-y).join(':');
  for(const [i,t]of body.relevantArmTriangles.entries())for(let k=0;k<3;k++){
    const a=t.bodyVertexIDs[k],b=t.bodyVertexIDs[(k+1)%3],id=key(a,b),list=edges.get(id)??[];list.push({a,b,triangle:i});edges.set(id,list);
  }
  assert([...edges.values()].every(e=>e.length===1||e.length===2));
  for(const e of edges.values())if(e.length===2)assert(e[0].a===e[1].b&&e[0].b===e[1].a);
  const boundary=[...edges.values()].filter(e=>e.length===1).map(e=>e[0]),next=new Map();for(const e of boundary){assert(!next.has(e.a));next.set(e.a,e.b);}
  const visited=new Set(),loops=[];for(const start of next.keys()){
    if(visited.has(start))continue;let id=start;const loop=[];
    do{assert(!visited.has(id));visited.add(id);loop.push(id);id=next.get(id);assert(id!==undefined);}while(id!==start);loops.push(loop);
  }
  assert.deepEqual(loops.map(l=>l.length).sort((a,b)=>a-b),[26,32]);
  const vertices=new Map(body.relevantArmVertices.map(v=>[v.bodyVertexID,v])),caps=[];
  for(const [i,loop]of loops.entries()){
    const center=[0,0,0];for(const id of loop)for(let k=0;k<3;k++)center[k]+=vertices.get(id).restNativeM[k]/loop.length;
    const id=-(i+1);body.relevantArmVertices.push({bodyVertexID:id,restNativeM:center,generatedFromNativeIDs:loop.slice(),generatedRule:'Arithmetic mean of current posed source boundary vertices; collider-only, no rendered body edit.'});
    const triangles=loop.map((a,j)=>({bodyTriangleID:-(caps.reduce((s,c)=>s+c.triangles.length,0)+j+1),bodyVertexIDs:[loop[(j+1)%loop.length],a,id],generatedCap:i}));body.relevantArmTriangles.push(...triangles);caps.push({centerVirtualVertexID:id,boundaryNativeVertexIDs:loop,triangles});
  }
  const closedEdges=new Map();for(const t of body.relevantArmTriangles)for(let i=0;i<3;i++){const a=t.bodyVertexIDs[i],b=t.bodyVertexIDs[(i+1)%3],id=key(a,b),rows=closedEdges.get(id)??[];rows.push([a,b]);closedEdges.set(id,rows);}
  assert([...closedEdges.values()].every(e=>e.length===2&&e[0][0]===e[1][1]&&e[0][1]===e[1][0]));
  const pos=new Map(body.relevantArmVertices.map(v=>[v.bodyVertexID,v.restNativeM]));let volumeM3=0;
  for(const t of body.relevantArmTriangles){const [a,b,c]=t.bodyVertexIDs.map(id=>pos.get(id));volumeM3+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6;}
  assert(volumeM3>0);const euler=body.relevantArmVertices.length-closedEdges.size+body.relevantArmTriangles.length;assert.equal(euler,2);
  result.engineColliderClosure={status:'UNACCEPTED_SOURCE_REGION_CAPPED_COLLIDER',originalVertices:562,originalTriangles:1066,generatedVertices:2,generatedTriangles:58,
    allOriginalFaceAndVertexFieldsExact:true,everyEdgeTwoOppositeFaces:true,eulerCharacteristic:euler,restOrientedVolumeM3:volumeM3,caps,
    limits:['Collider-only caps at the two source boundary loops, not a new anatomical body or garment.',
      'Watertight edge topology and positive rest volume do not prove self-intersection-free moving volume or continuous collision safety.',
      'No fitted proxy size, inward-normal change or inflated particle radius is introduced.']};
  return result;
}
