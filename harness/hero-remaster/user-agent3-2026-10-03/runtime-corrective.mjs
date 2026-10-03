/** Pure declared rig-angle controller; installation belongs to a private harness. */
export function correctiveWeights(config, currentWXYZ, centers) {
  const unit=q=>{const n=Math.hypot(...q);if(!Number.isFinite(n)||n<1e-9)throw new Error('Invalid controller quaternion');return q.map(v=>v/n);};
  const current=Object.fromEntries(config.joints.map(j=>[j,unit(currentWXYZ[j])]));
  const distances=centers.map(center=>Math.sqrt(config.joints.reduce((sum,joint)=>{
    const q=current[joint],p=unit(center.jointLocalQuaternionsWXYZ[joint]);
    const dot=q.reduce((s,v,k)=>s+v*p[k],0),angle=2*Math.acos(Math.min(1,Math.abs(dot)));return sum+angle*angle;
  },0)));
  const min=Math.min(...distances),closest=distances.indexOf(min);
  if(min<1e-5)return distances.slice(1).map((_,i)=>Number(i+1===closest));
  const inverse=distances.map(d=>1/(d*d*d*d)),total=inverse.reduce((s,v)=>s+v,0);
  return inverse.slice(1).map(v=>v/total);
}
