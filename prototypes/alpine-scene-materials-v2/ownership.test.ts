import { describe,it,expect,vi,afterEach } from 'vitest';
import fs from 'node:fs';
import { runInNewContext } from 'node:vm';
import * as THREE from 'three';
import ts from 'typescript';
import { applyAlpineSurface, alpineSoil, calibrateAlpineCanopy } from './out/common/src/render/world/zones/alpineSurface';
import type { ZoneKit } from './out/common/src/render/world/zones/zoneKit';
import type { MaterialLibrary } from './out/common/src/render/materials/library';
import { mountCourseAssets } from './out/common/src/render/world/courseAssets';

/** Painter stub exercises map creation/lifetime, not pixels or moving art. */
function painterDocument() {
  const gradient={addColorStop:vi.fn()};
  const context={fillRect:vi.fn(),beginPath:vi.fn(),moveTo:vi.fn(),lineTo:vi.fn(),stroke:vi.fn(),putImageData:vi.fn(),
    createRadialGradient:()=>gradient,createLinearGradient:()=>gradient,
    createImageData:(w:number,h:number)=>({data:new Uint8ClampedArray(w*h*4)}),fillStyle:'',strokeStyle:'',lineWidth:1};
  vi.stubGlobal('document',{createElement:()=>({width:0,height:0,getContext:()=>context})});
}
function library() {
  const borrowed=new THREE.DataTexture(new Uint8Array([128,128,255,255]),1,1);
  const complete=(material:THREE.MeshStandardMaterial)=>{
    material.map??=borrowed;material.normalMap??=borrowed;
    material.roughnessMap=material.metalnessMap=material.aoMap=material.emissiveMap=borrowed;
  };
  return {borrowed,lib:{complete} as MaterialLibrary};
}
function fixture() {
  const {borrowed,lib}=library();
  const terrain=new THREE.Mesh(new THREE.PlaneGeometry(10,4,2,2).rotateX(-Math.PI/2),new THREE.MeshStandardMaterial({map:borrowed,normalMap:borrowed}));
  terrain.name='terrain';terrain.geometry.setAttribute('color',new THREE.Float32BufferAttribute(Array.from({length:terrain.geometry.getAttribute('position').count*3},()=>.8),3));
  const lake=new THREE.Mesh(new THREE.PlaneGeometry(48,32).rotateX(-Math.PI/2),new THREE.MeshStandardMaterial());lake.name='zone:lake';
  return {terrain,lake,borrowed,lib,kit:{meshes:[terrain,lake],batches:[],textureBytes:0,scroll:[]} as ZoneKit};
}
afterEach(()=>vi.unstubAllGlobals());
describe('fresh A1 material integration ownership',()=>{
  it('keeps positions, normals, UVs and indices exact while changing only terrain colour',()=>{
    painterDocument();const {kit,lib}=fixture();
    const snapshots=kit.meshes.map(mesh=>Object.fromEntries(['position','normal','uv'].map(key=>[key,Array.from(mesh.geometry.getAttribute(key).array)]).concat([['index',Array.from(mesh.geometry.index!.array)]])));
    applyAlpineSurface(kit,lib);
    kit.meshes.forEach((mesh,i)=>{
      for(const key of ['position','normal','uv']) expect(Array.from(mesh.geometry.getAttribute(key).array)).toEqual(snapshots[i]![key]);
      expect(Array.from(mesh.geometry.index!.array)).toEqual(snapshots[i]!['index']);
    });
    expect(kit.scroll).toHaveLength(1);expect(kit.scroll[0]!.vx).toBe(.004);
    expect(kit.meshes[0]!.geometry.getAttribute('color').getX(0)).not.toBeCloseTo(.8);
  });
  it('executes the exact private builder hook and releases displaced clones without borrowed maps',()=>{
    painterDocument();const {kit,lib,terrain,lake,borrowed}=fixture();
    const oldTerrain=terrain.material,oldLake=lake.material;
    const terrainDispose=vi.spyOn(oldTerrain,'dispose'),lakeDispose=vi.spyOn(oldLake,'dispose'),borrowedDispose=vi.spyOn(borrowed,'dispose');
    const source=fs.readFileSync(new URL('./out/after/src/render/world/biomeKit.ts',import.meta.url),'utf8');
    const block=source.slice(source.indexOf("      if (track.def.id === 'a1-sawdust') {"),source.indexOf('      // Keep a procedural vessel'));
    runInNewContext(ts.transpile(block),{zk:kit,lib,track:{def:{id:'a1-sawdust'}},applyAlpineSurface});
    expect(terrainDispose).toHaveBeenCalledTimes(1);expect(lakeDispose).toHaveBeenCalledTimes(1);expect(borrowedDispose).not.toHaveBeenCalled();
    for(const mesh of kit.meshes) {
      const material=mesh.material as THREE.MeshStandardMaterial;expect(material.name).toBe('');
      for(const value of Object.values(material)) if(value instanceof THREE.CanvasTexture) value.dispose();
      material.dispose();
    }
    expect(borrowedDispose).not.toHaveBeenCalled();
  });
  it('exposes Canvas resources to generic retirement and does not derive library texture jobs',()=>{
    painterDocument();const {lib,borrowed}=library();
    let bytes=128*128*4*4/3;
    for(const role of ['tread','bank','floor'] as const) {
      const soil=alpineSoil(lib,role);bytes+=soil.bytes;
      expect(soil.mat.name).toBe('');expect(soil.mat.map).toBeInstanceOf(THREE.CanvasTexture);
      expect(soil.mat.normalMap).toBeInstanceOf(THREE.CanvasTexture);expect(soil.mat.roughnessMap).toBe(borrowed);
      expect(soil.mat.vertexColors).toBe(true);
    }
    expect(bytes).toBeCloseTo(3.6666666667*1024*1024,2);
  });
  it('calibrates only owned source branch materials; preserves alpha, vertex colours and all maps',()=>{
    const {borrowed}=library();const branch=new THREE.MeshStandardMaterial({map:borrowed,alphaMap:borrowed,alphaTest:.45,vertexColors:true});branch.name='alpine-branches';
    calibrateAlpineCanopy(branch);expect(branch.color.toArray()).toEqual([.72,1,.84]);expect(branch.normalScale.toArray()).toEqual([.45,.45]);
    expect(branch.alphaTest).toBe(.45);expect(branch.vertexColors).toBe(true);expect(branch.map).toBe(borrowed);expect(branch.alphaMap).toBe(borrowed);
    const trunk=new THREE.MeshStandardMaterial();const old=trunk.color.clone();calibrateAlpineCanopy(trunk);expect(trunk.color).toEqual(old);
  });
  it('keeps the complete accepted fallback/removal/late-attachment block unchanged',()=>{
    const file='./out/common/src/render/world/biomeKit.ts',after='./out/after/src/render/world/biomeKit.ts';
    const extract=(source:string)=>source.slice(source.indexOf('      if (authoredCourse && a1ForestApplicable(track))'),source.indexOf('      meshes.push(...zk.meshes)'));
    const before=extract(fs.readFileSync(new URL(file,import.meta.url),'utf8'));
    const changed=extract(fs.readFileSync(new URL(after,import.meta.url),'utf8')).replace(' lib.complete(material); calibrateAlpineCanopy(material);',' lib.complete(material);');
    expect(changed).toBe(before);
  });
  it('retains originals on failure and retires late forest resolution without attachment',async()=>{
    const failed=mountCourseAssets(Promise.reject(new Error('required map missing')),()=>undefined);const fallback={visible:true};
    await failed.ready;if(failed.root.children.length)fallback.visible=false;expect(fallback.visible).toBe(true);
    let resolve!:(asset:{root:THREE.Group;textureBytes:number;dispose:()=>void})=>void;
    const pending=new Promise<{root:THREE.Group;textureBytes:number;dispose:()=>void}>(r=>{resolve=r;});
    const owner=mountCourseAssets(pending),dispose=vi.fn();owner.cancel();resolve({root:new THREE.Group(),textureBytes:0,dispose});await owner.ready;
    expect(owner.root.children).toHaveLength(0);expect(dispose).toHaveBeenCalledTimes(1);
  });
});
