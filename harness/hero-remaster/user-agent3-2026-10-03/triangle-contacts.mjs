/** Finite triangle contact checks, independent of solver collision flags. */
const sub=(a,b)=>a.map((x,i)=>x-b[i]);
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
export function triangleContact(a,b,epsilon=1e-9){
  for(let k=0;k<3;k++)if(Math.max(...a.map(p=>p[k]))<Math.min(...b.map(p=>p[k]))-epsilon||Math.max(...b.map(p=>p[k]))<Math.min(...a.map(p=>p[k]))-epsilon)return false;
  const ea=a.map((p,i)=>sub(a[(i+1)%3],p)),eb=b.map((p,i)=>sub(b[(i+1)%3],p)),na=cross(ea[0],ea[1]),nb=cross(eb[0],eb[1]),axes=[na,nb];
  for(const x of ea)for(const y of eb)axes.push(cross(x,y));
  const nLength=Math.hypot(...na),mLength=Math.hypot(...nb);if(nLength<1e-14||mLength<1e-14)throw new Error('Degenerate triangle is not qualified');
  if(Math.hypot(...cross(na,nb))/(nLength*mLength)<1e-8)for(const edge of [...ea,...eb])axes.push(cross(na,edge));
  for(const axis of axes){const length=Math.hypot(...axis);if(length<1e-14)continue;const pa=a.map(p=>dot(p,axis)/length),pb=b.map(p=>dot(p,axis)/length);
    if(Math.max(...pa)<Math.min(...pb)-epsilon||Math.max(...pb)<Math.min(...pa)-epsilon)return false;}
  return true;
}
export function meshContacts(aVertices,aFaces,bVertices,bFaces,sameMesh=false){
  const a=aFaces.map(ids=>ids.map(i=>aVertices[i])),b=bFaces.map(ids=>ids.map(i=>bVertices[i]));let count=0;const witnesses=[];
  for(let i=0;i<a.length;i++)for(let j=sameMesh?i+1:0;j<b.length;j++){
    if(sameMesh&&aFaces[i].some(id=>bFaces[j].includes(id)))continue;
    if(triangleContact(a[i],b[j])){count++;if(witnesses.length<8)witnesses.push({triangleA:i,triangleB:j});}
  }
  return{pairs:count,witnesses,epsilonM:1e-9,limits:'Finite triangle contacts at this pose, not swept/continuous or volume penetration. Same-mesh faces sharing a vertex are excluded.'};
}
