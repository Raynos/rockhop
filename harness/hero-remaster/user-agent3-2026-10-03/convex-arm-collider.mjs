/** Conservative arm solids from complete current-pose source faces. */
import { Vector3, Triangle } from 'three';
import { ConvexHull } from 'three/addons/math/ConvexHull.js';
export function partitionArmFaces(handoff){
  const body=handoff.nativeConsumedColliders.body,rows=new Map(body.relevantArmVertices.map((v,i)=>[v.bodyVertexID,{...v,row:i}]));
  const parts=[{name:'upperArm.L',faces:[],vertices:new Set()},{name:'forearm.L',faces:[],vertices:new Set()}];
  for(const face of body.relevantArmTriangles){const sums=[0,0];for(const id of face.bodyVertexIDs)for(const[name,weight]of rows.get(id).weights){if(name==='upperArm.L')sums[0]+=weight;if(name==='forearm.L')sums[1]+=weight;}
    const part=parts[sums[0]>=sums[1]?0:1];part.faces.push(face.bodyTriangleID);for(const id of face.bodyVertexIDs)part.vertices.add(id);
  }
  return parts.map(p=>({name:p.name,sourceTriangleIDs:p.faces,sourceVertexIDs:[...p.vertices].sort((a,b)=>a-b),rows:[...p.vertices].sort((a,b)=>a-b).map(id=>rows.get(id).row)}));
}
export function closedConvexVolume(points,part){
  if(!points.every(p=>p.toArray().every(Number.isFinite)))throw new Error('Nonfinite collision input');
  const selected=part.rows.map(i=>points[i]),hull=new ConvexHull().setFromPoints(selected),ids=new Map(),vertices=[],faces=[];
  for(const face of hull.faces){const triangle=[];let edge=face.edge;do{const point=edge.head().point;
    if(!ids.has(point)){ids.set(point,vertices.length);vertices.push(point);}triangle.push(ids.get(point));edge=edge.next;
  }while(edge!==face.edge);if(triangle.length!==3)throw new Error('Nontriangle convex face');faces.push(triangle);}
  if(faces.length<4)throw new Error('Degenerate convex volume');
  const center=vertices.reduce((s,p)=>s.add(p),new Vector3()).multiplyScalar(1/vertices.length),edges=new Map();let volume=0;
  const facets=faces.map((face,i)=>{const triangle=new Triangle(...face.map(id=>vertices[id]));
    for(let j=0;j<3;j++){const a=face[j],b=face[(j+1)%3],key=[a,b].sort((x,y)=>x-y).join(':');if(!edges.has(key))edges.set(key,[]);edges.get(key).push([a,b]);}
    const[a,b,c]=face.map(id=>vertices[id].clone().sub(center));volume+=a.dot(b.clone().cross(c))/6;
    return{triangle,normal:hull.faces[i].normal.clone(),constant:hull.faces[i].constant};});
  const closed=[...edges.values()].every(e=>e.length===2&&e[0][0]===e[1][1]&&e[0][1]===e[1][0]),euler=vertices.length-edges.size+faces.length;
  let maximumSourcePlaneOutsideM=0;for(const p of selected)for(const f of facets)maximumSourcePlaneOutsideM=Math.max(maximumSourcePlaneOutsideM,f.normal.dot(p)-f.constant);
  if(!closed||euler!==2||volume<=0||maximumSourcePlaneOutsideM>2e-9)throw new Error('Invalid source-enclosing collision solid');
  return{part,vertices,faces,facets,qualification:{vertices:vertices.length,faces:faces.length,edges:edges.size,euler,everyEdgeTwoOppositeFaces:closed,positiveVolumeM3:volume,maximumSourcePlaneOutsideM}};
}
/** Exact triangle distance plus convex half-space sign; no GJK point query. */
export function convexPointDistance(point,solid){
  let maximumPlane=-Infinity,gap=Infinity,best=null;const closest=new Vector3();
  for(const f of solid.facets){maximumPlane=Math.max(maximumPlane,f.normal.dot(point)-f.constant);f.triangle.closestPointToPoint(point,closest);const d=point.distanceTo(closest);if(d<gap){gap=d;best={point:closest.clone(),normal:f.normal};}}
  const inside=maximumPlane<=1e-10;return{inside,signedDistanceM:inside?-gap:gap,closest:best.point,outwardNormal:best.normal,maximumPlaneM:maximumPlane};
}
/** Bounded positional response for a primary skinned vertex, not cloth history. */
export function projectOutsideVolume(point,solid,clearanceM=.002,capM=.02){
  const q=convexPointDistance(point,solid),need=clearanceM-q.signedDistanceM;if(need<=0)return{point:point.clone(),deltaM:0,capped:false};
  const direction=q.inside?q.outwardNormal:point.clone().sub(q.closest).normalize(),deltaM=Math.min(need,capM);
  return{point:point.clone().addScaledVector(direction,deltaM),deltaM,capped:need>capM};
}
