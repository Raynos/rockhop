/** Exhaustive finite-triangle checks, scoped to the actual hand-owned skin. */
import {Vector3,Triangle,Ray} from 'three';
export function validateSurface(c){
 const {sourceRows,idx,matrices,skinned,handOwned,triangles,nearest}=c,m=matrices(),positions=new Float64Array(sourceRows.length*3),owned=new Uint8Array(sourceRows.length),boundsMin=new Vector3(Infinity,Infinity,Infinity),boundsMax=new Vector3(-Infinity,-Infinity,-Infinity);
 for(const t of triangles)for(const p of [t.a,t.b,t.c]){boundsMin.min(p);boundsMax.max(p);}
 boundsMin.addScalar(-.003);boundsMax.addScalar(.003);let ownedVertices=0,checkedVertices=0,insideCount=0,maxPenetrationM=0;const worst=[];
 sourceRows.forEach((row,i)=>{if(!handOwned(row))return;owned[i]=1;ownedVertices++;const p=skinned(row,m).p;positions.set(p.toArray(),i*3);if(p.x<boundsMin.x||p.y<boundsMin.y||p.z<boundsMin.z||p.x>boundsMax.x||p.y>boundsMax.y||p.z>boundsMax.z)return;checkedVertices++;const n=nearest(p);if(n.signed<0){insideCount++;maxPenetrationM=Math.max(maxPenetrationM,-n.signed);if(worst.length<10)worst.push({row:i,point:p.toArray(),penetrationM:-n.signed});}});
 const point=i=>new Vector3().fromArray(positions,i*3),bounds=triangles.map(t=>({t,min:t.a.clone().min(t.b).min(t.c),max:t.a.clone().max(t.b).max(t.c)}));
 const overlap=(a,b,c,d)=>a.x<=d.x&&a.y<=d.y&&a.z<=d.z&&b.x>=c.x&&b.y>=c.y&&b.z>=c.z;
 const hit=(a,b,t)=>{const direction=b.clone().sub(a),length=direction.length();if(length<1e-12)return false;const p=new Ray(a,direction.divideScalar(length)).intersectTriangle(t.a,t.b,t.c,false,new Vector3());return p&&p.distanceTo(a)>1e-8&&p.distanceTo(a)<length-1e-8;};
 let ownedTriangles=0,overlappingPairs=0,crossingPairs=0;const crossingWitnesses=[];
 for(let i=0;i<idx.count;i+=3){const ids=[idx.get(i),idx.get(i+1),idx.get(i+2)];if(!ids.every(id=>owned[id]))continue;ownedTriangles++;const t=new Triangle(...ids.map(point)),min=t.a.clone().min(t.b).min(t.c),max=t.a.clone().max(t.b).max(t.c);if(!overlap(min,max,boundsMin,boundsMax))continue;for(const [k,b]of bounds.entries()){if(!overlap(min,max,b.min,b.max))continue;overlappingPairs++;if(hit(t.a,t.b,b.t)||hit(t.b,t.c,b.t)||hit(t.c,t.a,b.t)||hit(b.t.a,b.t.b,t)||hit(b.t.b,b.t.c,t)||hit(b.t.c,b.t.a,t)){crossingPairs++;if(crossingWitnesses.length<12)crossingWitnesses.push({gloveTriangle:i/3,rows:ids,barTriangle:k});}}}
 return {scope:'Every selected glove triangle whose positive skin influences belong entirely to the same native wrist/palm/digit subtree; forearm cuff excluded and must be checked in full runtime arm pose',ownedVertices,checkedVertices,insideCount,maxPenetrationM,worst,ownedTriangles,overlappingPairs,crossingPairs,crossingWitnesses};
}
