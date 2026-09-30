import * as THREE from 'three';
import { describe, expect, it, vi } from 'vitest';
import { compileTrack } from '../../../tracks/compile';
import { C1 } from '../../../tracks/rockhop/coast';
import { planC1Harbor, type CoastHarborPlacement } from './coastHarbor';
import { zoneGround } from './zoneKit';
import { buildCoastHarborSite, COAST_DRY_FOOTPRINTS, groundCoastHarborPlacements } from './coastHarborSite';

const track=compileTrack(C1);
const groundAt=(x:number,z:number)=>zoneGround('coast',track.def.profile,x,z);
const seaY=Math.min(...track.def.profile.map(p=>p.y))-.42-2.4;
const plan=planC1Harbor(groundAt,seaY).map(p=>({...p,z:COAST_DRY_FOOTPRINTS[p.variant] ? -9.8 : p.z}));
function positions(root: THREE.Group): THREE.Vector3[] {
  return root.children.flatMap(o=>{
    const attribute=(o as THREE.Mesh).geometry.getAttribute('position');
    return Array.from({length:attribute.count},(_,i)=>new THREE.Vector3(attribute.getX(i),attribute.getY(i),attribute.getZ(i)));
  });
}
describe('Coast harbor truthful pads and access',()=>{
  it('clones placements, preserves wet roots, and grounds full dry footprints',()=>{
    const original=structuredClone(plan);const placed=groundCoastHarborPlacements(plan,groundAt);
    expect(plan).toEqual(original);
    for(const [index,p] of placed.entries()){
      expect(p).not.toBe(plan[index]);
      const bounds=COAST_DRY_FOOTPRINTS[p.variant];
      if(!bounds){expect(p).toEqual(plan[index]);continue;}
      for(const x of [bounds[0],bounds[1]])for(const z of [bounds[2],bounds[3]]){
        const scale=p.scale??1,yaw=p.yaw??0;
        const worldX=p.x+scale*(x*Math.cos(yaw)+z*Math.sin(yaw));
        const worldZ=p.z+scale*(-x*Math.sin(yaw)+z*Math.cos(yaw));
        expect(p.y).toBeGreaterThanOrEqual(groundAt(worldX,worldZ)+.079);
      }
    }
  });
  it('samples rotated perimeter peaks rather than only model origin',()=>{
    const p:CoastHarborPlacement={variant:'open-warehouse',x:0,y:0,z:-15,scale:1,yaw:Math.PI/2};
    const a=groundCoastHarborPlacements([p],(x,z)=>Math.abs(z+15)*.1+Math.abs(x)*.05)[0]!;
    expect(a.y).toBeGreaterThan(1.8);expect(p.y).toBe(0);
  });
  it('makes finite pads inside 64m chunks, clear of riding and brake corridor',()=>{
    const p=groundCoastHarborPlacements(plan,groundAt);const concrete=new THREE.MeshStandardMaterial();
    const site=buildCoastHarborSite(p,{groundAt,seaY,concrete});
    expect(site.root.children.length).toBeGreaterThan(4);expect(site.root.children.length).toBeLessThanOrEqual(9);
    for(const child of site.root.children){
      const mesh=child as THREE.Mesh;mesh.geometry.computeBoundingBox();
      expect(mesh.geometry.boundingBox!.max.x-mesh.geometry.boundingBox!.min.x).toBeLessThanOrEqual(64.0001);
      expect(mesh.geometry.getAttribute('color').count).toBe(mesh.geometry.getAttribute('position').count);
      expect(mesh.geometry.getAttribute('normal')).toBeDefined();expect(mesh.geometry.getAttribute('uv')).toBeDefined();
    }
    for(const v of positions(site.root)){
      expect([v.x,v.y,v.z].every(Number.isFinite)).toBe(true);expect(v.z).toBeLessThan(-3.8);
      expect(v.x<180||v.x>260).toBe(true);
    }
    expect(site.textureBytes).toBe(0);site.dispose();
  });
  it('connects exact four authored pier endpoints and shore deck heights/width',()=>{
    const piers=plan.filter(p=>p.variant==='loading-pier');expect(piers).toHaveLength(4);
    const site=buildCoastHarborSite(piers,{groundAt,seaY,concrete:new THREE.MeshStandardMaterial()});
    const vertices=positions(site.root);
    for(const p of piers){
      const scale=p.scale??1,endZ=p.z+36*scale,endY=p.y+.175*scale;
      for(const x of [p.x-2.1*scale,p.x+2.1*scale]){
        expect(vertices.some(v=>Math.abs(v.x-x)<1e-4&&Math.abs(v.z-endZ)<1e-4&&Math.abs(v.y-endY)<1e-4)).toBe(true);
        const shoreY=Math.max(groundAt(p.x-2.1*scale,-11.6),groundAt(p.x+2.1*scale,-11.6))+.08;
        expect(vertices.some(v=>Math.abs(v.x-x)<1e-4&&Math.abs(v.z+11.6)<1e-4&&Math.abs(v.y-shoreY)<1e-4)).toBe(true);
        expect(vertices.some(v=>Math.abs(v.x-x)<1e-4&&Math.abs(v.z-endZ)<1e-4&&Math.abs(v.y-(endY-.2))<1e-4)).toBe(true);
      }
      expect(vertices.some(v=>v.x>p.x-2&&v.x<p.x+2&&v.z>endZ&&v.z<-11.6&&v.y<seaY-.6)).toBe(true);
    }
    site.dispose();
  });
  it('pad tops coincide with grounded dry roots and skirts meet sampled ground',()=>{
    const placed=groundCoastHarborPlacements(plan.filter(p=>p.variant==='open-warehouse'),groundAt);
    const site=buildCoastHarborSite(placed,{groundAt,seaY,concrete:new THREE.MeshStandardMaterial()});
    const vertices=positions(site.root);
    for(const p of placed)for(const x of [-14.39,14.39])for(const z of [-6.84,7.80]){
      const scale=p.scale??1;const worldX=p.x+x*scale,worldZ=p.z+z*scale;
      expect(vertices.some(v=>Math.abs(v.x-worldX)<1e-4&&Math.abs(v.z-worldZ)<1e-4&&Math.abs(v.y-p.y)<1e-4)).toBe(true);
      const groundY=groundAt(worldX,worldZ)-.035;
      expect(vertices.some(v=>Math.abs(v.x-worldX)<1e-4&&Math.abs(v.z-worldZ)<1e-4&&Math.abs(v.y-groundY)<1e-4)).toBe(true);
    }
    site.dispose();
  });
  it('retires owned geometry/material exactly once but preserves borrowed material/maps',()=>{
    const concrete=new THREE.MeshStandardMaterial();const map=new THREE.Texture();concrete.map=map;
    const matDispose=vi.spyOn(concrete,'dispose'),mapDispose=vi.spyOn(map,'dispose');
    const site=buildCoastHarborSite(groundCoastHarborPlacements(plan,groundAt),{groundAt,seaY,concrete});
    const geometry=(site.root.children[0] as THREE.Mesh).geometry;const geometryDispose=vi.spyOn(geometry,'dispose');
    const own=(site.root.children[0] as THREE.Mesh).material as THREE.MeshStandardMaterial;const ownDispose=vi.spyOn(own,'dispose');
    expect(own).not.toBe(concrete);expect(own.vertexColors).toBe(true);expect(own.map).toBe(map);expect(concrete.vertexColors).toBe(false);
    site.dispose();site.dispose();expect(geometryDispose).toHaveBeenCalledOnce();expect(ownDispose).toHaveBeenCalledOnce();
    expect(mapDispose).not.toHaveBeenCalled();expect(matDispose).not.toHaveBeenCalled();
  });
  it('rejects malformed terrain/placements and ungrounded dry slabs',()=>{
    expect(()=>groundCoastHarborPlacements([{variant:'open-warehouse',x:0,y:0,z:0}],()=>NaN)).toThrow('Nonfinite');
    const concrete=new THREE.MeshStandardMaterial();
    expect(()=>buildCoastHarborSite([{variant:'open-warehouse',x:0,y:0,z:-9.8}],{groundAt:()=>2,seaY,concrete})).toThrow('grounded');
    expect(()=>buildCoastHarborSite([{variant:'loading-pier',x:0,y:0,z:0}],{groundAt,seaY,concrete})).toThrow('seaward');
    expect(()=>groundCoastHarborPlacements([{variant:'loading-pier',x:NaN,y:0,z:0}],groundAt)).toThrow('Invalid');
  });
});
