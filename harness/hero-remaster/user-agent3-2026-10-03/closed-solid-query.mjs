/** Generalized winding and closest finite surface on already qualified closed components. */
import { Vector3, Triangle } from 'three';
export function makeClosedSolidQuery(vertices, faces, components) {
  const points=vertices.map(v=>new Vector3(...v));
  const solids=components.map(c=>({ ...c, surfaces:c.triangles.map(id=>new Triangle(...faces[id].map(i=>points[i]))) }));
  return p => {
    const point=new Vector3(...p),hits=[];
    for(const solid of solids){
      if([0,1,2].some(k=>p[k]<solid.bounds.min[k]-1e-9||p[k]>solid.bounds.max[k]+1e-9))continue;
      let distance=Infinity,winding=0;
      for(const t of solid.surfaces){
        distance=Math.min(distance,t.closestPointToPoint(point,new Vector3()).distanceTo(point));
        const a=t.a.clone().sub(point),b=t.b.clone().sub(point),c=t.c.clone().sub(point),la=a.length(),lb=b.length(),lc=c.length();
        winding+=2*Math.atan2(a.dot(b.clone().cross(c)),la*lb*lc+a.dot(b)*lc+b.dot(c)*la+c.dot(a)*lb);
      }
      winding/=4*Math.PI;
      if(distance<=1e-9)hits.push({component:solid.component,boundary:true,winding,penetrationM:0});
      else if(Math.abs(winding)>.5)hits.push({component:solid.component,boundary:false,winding,penetrationM:distance});
    }
    return {inside:hits.some(h=>!h.boundary),boundary:hits.some(h=>h.boundary),hits};
  };
}
