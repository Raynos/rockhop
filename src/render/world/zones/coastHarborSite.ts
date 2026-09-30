/** Course-owned foundations/access for authored Coast models; no colliders or RNG.
 * Inputs are the parent's exact placements and authoritative zoneGround callback.
 */
import * as THREE from 'three';
import { fogify } from '../../lighting/environment';
import type { CourseAssetDelivery } from '../courseAssets';
import type { CoastHarborPlacement } from './coastHarbor';

type Ground = (x: number, z: number) => number;
type Point = readonly [number, number];
type Footprint = readonly [number, number, number, number];
export const COAST_DRY_FOOTPRINTS: Readonly<Partial<Record<CoastHarborPlacement['variant'], Footprint>>> = {
  'open-warehouse': [-14.15, 14.15, -6.6, 7.56],
  'brick-repair-shed': [-14.15, 14.15, -6.6, 7.56],
  'sawtooth-maintenance-hall': [-14.15, 14.15, -6.6, 7.56],
  'logistics-yard': [-7.08, 6.08, -4.10, 5.90],
};
const CHUNK = 64;
function checkPlacement(p: CoastHarborPlacement): void {
  if (![p.x,p.y,p.z,p.scale ?? 1,p.yaw ?? 0].every(Number.isFinite) || (p.scale ?? 1) <= 0) throw new Error('Invalid Coast site placement');
}
function ground(groundAt: Ground, x: number, z: number): number {
  const y = groundAt(x,z);
  if (!Number.isFinite(y)) throw new Error('Nonfinite Coast site ground');
  return y;
}
function world(p: CoastHarborPlacement, x: number, z: number): Point {
  const scale = p.scale ?? 1, angle = p.yaw ?? 0;
  return [p.x + scale * (x * Math.cos(angle) + z * Math.sin(angle)),
    p.z + scale * (-x * Math.sin(angle) + z * Math.cos(angle))];
}
function perimeter(p: CoastHarborPlacement, footprint: Footprint, margin = 0): Point[] {
  const [x0,x1,z0,z1] = footprint;
  const corners: Point[] = [[x0-margin,z0-margin],[x0-margin,z1+margin],[x1+margin,z1+margin],[x1+margin,z0-margin]];
  const points: Point[] = [];
  for (let i=0;i<4;i++) {
    const a=corners[i]!, b=corners[(i+1)%4]!;
    const count=Math.ceil(Math.hypot(b[0]-a[0],b[1]-a[1])*(p.scale ?? 1));
    for (let k=0;k<count;k++) points.push(world(p,a[0]+(b[0]-a[0])*k/count,a[1]+(b[1]-a[1])*k/count));
  }
  return points;
}
/** Clones every placement; raises only warehouse/yard roots to max sampled
 * expanded footprint perimeter + centre ground + 0.08m. Max protects level pads.
 */
export function groundCoastHarborPlacements(placements: readonly CoastHarborPlacement[], groundAt: Ground): CoastHarborPlacement[] {
  return placements.map(p => {
    checkPlacement(p); const footprint=COAST_DRY_FOOTPRINTS[p.variant];
    if (!footprint) return {...p};
    const points=perimeter(p,footprint,.24);
    const centre=world(p,(footprint[0]+footprint[1])/2,(footprint[2]+footprint[3])/2);
    const y=Math.max(ground(groundAt,...centre),...points.map(point=>ground(groundAt,...point)))+.08;
    return {...p,y};
  });
}
export interface CoastHarborSiteOptions {
  groundAt: Ground;
  seaY: number;
  /** Maps remain borrowed. One local material clone enables vertex colors/fog. */
  concrete: THREE.MeshStandardMaterial;
}
interface Soup { position: number[]; color: number[]; uv: number[] }
/** Four dry-pad sides follow sampled ground, and pier necks receive a short
 * graded shore apron with matching width, 0.2m sides, caps and trestles.
 * Every triangle belongs to a 64m x chunk; meshes share one owned material clone.
 */
export function buildCoastHarborSite(placements: readonly CoastHarborPlacement[], options: CoastHarborSiteOptions): CourseAssetDelivery {
  if (!Number.isFinite(options.seaY)) throw new Error('Nonfinite Coast site sea');
  const chunks=new Map<number,Soup>();
  const root=new THREE.Group();root.name='coast-harbor-site';
  const geometries: THREE.BufferGeometry[]=[];
  const material=options.concrete.clone();material.name='coast-harbor-site concrete';material.vertexColors=true;fogify(material);
  const top = [.89,.92,.9], side = [.59,.65,.61], timber = [.30,.29,.24];
  const triangle=(a: THREE.Vector3,b: THREE.Vector3,c: THREE.Vector3,color: readonly number[]): void => {
    // Clip individual triangles to each chunk rather than assigning a large pad by centre.
    const min=Math.floor(Math.min(a.x,b.x,c.x)/CHUNK),max=Math.floor(Math.max(a.x,b.x,c.x)/CHUNK);
    for(let chunk=min;chunk<=max;chunk++) {
      let polygon=[a,b,c];
      for(const [bound,sign] of [[chunk*CHUNK,1],[(chunk+1)*CHUNK,-1]] as const) {
        const clipped: THREE.Vector3[]=[];
        for(let i=0;i<polygon.length;i++) {
          const u=polygon[i]!,v=polygon[(i+1)%polygon.length]!;
          const inside=(u.x-bound)*sign>=0, next=(v.x-bound)*sign>=0;
          if(inside)clipped.push(u);
          if(inside!==next)clipped.push(u.clone().lerp(v,(bound-u.x)/(v.x-u.x)));
        }
        polygon=clipped;
      }
      if(polygon.length<3)continue;
      let soup=chunks.get(chunk);if(!soup){soup={position:[],color:[],uv:[]};chunks.set(chunk,soup);}
      for(let i=1;i<polygon.length-1;i++) {
        const points=[polygon[0]!,polygon[i]!,polygon[i+1]!];
        if(points[1]!.clone().sub(points[0]!).cross(points[2]!.clone().sub(points[0]!)).lengthSq()<1e-14)continue;
        for(const point of points){soup.position.push(point.x,point.y,point.z);soup.color.push(...color);soup.uv.push(point.x/3,point.z/3);}
      }
    }
  };
  const quad=(a: THREE.Vector3,b: THREE.Vector3,c: THREE.Vector3,d: THREE.Vector3,color: readonly number[]):void=>{triangle(a,b,c,color);triangle(a,c,d,color);};
  const box=(x: number,z: number,y0: number,y1: number,halfX: number,halfZ: number):void=>{
    const a=new THREE.Vector3(x-halfX,y0,z-halfZ),b=new THREE.Vector3(x-halfX,y0,z+halfZ),c=new THREE.Vector3(x+halfX,y0,z+halfZ),d=new THREE.Vector3(x+halfX,y0,z-halfZ);
    const aa=a.clone().setY(y1),bb=b.clone().setY(y1),cc=c.clone().setY(y1),dd=d.clone().setY(y1);
    quad(aa,bb,cc,dd,timber);quad(a,aa,dd,d,timber);quad(b,bb,aa,a,timber);quad(c,cc,bb,b,timber);quad(d,dd,cc,c,timber);
  };
  try {
    for(const p of placements) {
      checkPlacement(p);const footprint=COAST_DRY_FOOTPRINTS[p.variant];
      if(footprint) {
        const points=perimeter(p,footprint,.24);
        const centre=new THREE.Vector3(p.x,p.y,p.z);
        for(let i=0;i<points.length;i++) {
          const a=points[i]!, b=points[(i+1)%points.length]!;
          const ya=ground(options.groundAt,...a),yb=ground(options.groundAt,...b);
          if(Math.max(ya,yb)>p.y+.001)throw new Error('Coast site pad needs grounded placement');
          const aa=new THREE.Vector3(a[0],p.y,a[1]),bb=new THREE.Vector3(b[0],p.y,b[1]);
          triangle(centre,aa,bb,top);
          quad(aa,new THREE.Vector3(a[0],ya-.035,a[1]),new THREE.Vector3(b[0],yb-.035,b[1]),bb,side);
        }
      }
      if(p.variant==='loading-pier') {
        const scale=p.scale ?? 1;
        const end=world(p,0,36);const endY=p.y+.175*scale;
        const shore: Point=[end[0],-11.6];
        if(end[1]>=shore[1])throw new Error('Coast pier endpoint must remain seaward of shore');
        const half=2.1*scale;
        const shoreY=Math.max(ground(options.groundAt,shore[0]-half,shore[1]),ground(options.groundAt,shore[0]+half,shore[1]))+.08;
        const length=shore[1]-end[1],steps=Math.max(1,Math.ceil(length/1.5));
        const dx=Math.cos(p.yaw ?? 0)*half,dz=-Math.sin(p.yaw ?? 0)*half;
        for(let i=0;i<steps;i++) {
          const t0=i/steps,t1=(i+1)/steps;
          const z0=end[1]+length*t0,z1=end[1]+length*t1;
          const y0=endY+(shoreY-endY)*t0,y1=endY+(shoreY-endY)*t1;
          // The seam starts in the pier's rotated frame and straightens at shore.
          const dz0=dz*(1-t0),dz1=dz*(1-t1);
          const width0=dx+(half-dx)*t0,width1=dx+(half-dx)*t1;
          const a=new THREE.Vector3(end[0]-width0,y0,z0-dz0),b=new THREE.Vector3(end[0]-width1,y1,z1-dz1);
          const c=new THREE.Vector3(end[0]+width1,y1,z1+dz1),d=new THREE.Vector3(end[0]+width0,y0,z0+dz0);
          quad(a,b,c,d,top);
          quad(a,a.clone().add(new THREE.Vector3(0,-.2,0)),b.clone().add(new THREE.Vector3(0,-.2,0)),b,side);
          quad(c,c.clone().add(new THREE.Vector3(0,-.2,0)),d.clone().add(new THREE.Vector3(0,-.2,0)),d,side);
          if(i===0)quad(d,d.clone().add(new THREE.Vector3(0,-.2,0)),a.clone().add(new THREE.Vector3(0,-.2,0)),a,side);
          if(i===steps-1)quad(b,b.clone().add(new THREE.Vector3(0,-.2,0)),c.clone().add(new THREE.Vector3(0,-.2,0)),c,side);
        }
        for(let t=.25;t<1;t+=Math.min(.5,3/length)) {
          const z=end[1]+length*t,y=endY+(shoreY-endY)*t-.2;
          for(const x of [end[0]-half*.72,end[0]+half*.72])box(x,z,Math.min(options.seaY-.65,ground(options.groundAt,x,z)-.12),y,.13*scale,.13*scale);
        }
      }
    }
    for(const [chunk,soup] of chunks) {
      if(!soup.position.length)continue;
      const geometry=new THREE.BufferGeometry();geometries.push(geometry);
      geometry.setAttribute('position',new THREE.Float32BufferAttribute(soup.position,3));
      geometry.setAttribute('color',new THREE.Float32BufferAttribute(soup.color,3));geometry.setAttribute('uv',new THREE.Float32BufferAttribute(soup.uv,2));
      geometry.computeVertexNormals();geometry.computeBoundingBox();geometry.computeBoundingSphere();
      const mesh=new THREE.Mesh(geometry,material);mesh.name=`coast-harbor-site:${chunk}`;mesh.castShadow=false;mesh.receiveShadow=true;root.add(mesh);
    }
    let disposed=false;
    return {root,textureBytes:0,dispose(){if(disposed)return;disposed=true;root.clear();for(const g of geometries)g.dispose();material.dispose();}};
  } catch(error) {for(const g of geometries)g.dispose();material.dispose();throw error;}
}
