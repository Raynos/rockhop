/** A2/A3 actual seeded forest/material/shadow audit. Node only; no asset decoding or scene hooks. */
import * as THREE from 'three';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { A2, A3 } from '../../../../src/tracks/rockhop/alpine';
import { compileTrack } from '../../../../src/tracks/compile';
import { setPiecesOf } from '../../../../src/tracks/author';
import { footprint, type TrackKind } from '../../../../src/tracks/kinds';
import { MaterialLibrary } from '../../../../src/render/materials/library';
import { BIOMES } from '../../../../src/render/biomes';
import { buildBiomeKit } from '../../../../src/render/world/biomeKit';
import { buildRideSurfaces } from '../../../../src/render/world/deck';
import { buildObstacles } from '../../../../src/render/world/obstacles';
import { buildGates } from '../../../../src/render/world/gates';
import { PropBatch, type WorldDetail } from '../../../../src/render/world/props';
import type { ArtLibrary } from '../../../../src/render/art/library';
const noop=()=>{}, gradient={addColorStop:noop};
const context=new Proxy<Record<string,unknown>>({}, {get(target,key){
  if(key in target) return target[key as string];
  if(key==='createLinearGradient'||key==='createRadialGradient') return ()=>gradient;
  if(key==='getImageData'||key==='createImageData') return (_x:number,_y:number,w:number,h:number)=>({data:new Uint8ClampedArray((w??_x)*(h??_y)*4)});
  if(key==='measureText') return ()=>({width:100});
  return noop;
}});
Object.defineProperty(globalThis,'document',{value:{createElement:()=>({width:0,height:0,getContext:()=>context})},configurable:true});
const textures=new Map<string,THREE.Texture>();
const art={texture(id:string){let t=textures.get(id);if(!t){t=new THREE.DataTexture(new Uint8Array([128,128,128,255]),1,1);textures.set(id,t);}return t;},entry(){return {bytes:0};},has(){return true;},bitmap(){return {width:512,height:512};}} as unknown as ArtLibrary;
const sourceFiles=['src/render/world/zones/zoneKit.ts','src/render/world/biomeKit.ts','src/render/world/zones/geo.ts','src/render/world/zones/zoneDeck.ts','src/render/materials/library.ts','src/render/biomes/index.ts','src/tracks/rockhop/alpine.ts'];
const sourceHashes=Object.fromEntries(sourceFiles.map(f=>[f,createHash('sha256').update(readFileSync(f)).digest('hex')]));
const reports=[];
for(const def of [A2,A3]) {
  const track=compileTrack(def),tiers=[];
  for(const detail of ['low','high'] as const satisfies readonly WorldDetail[]) {
    const library=new MaterialLibrary(def.seed);
    const batches=new Set<PropBatch>();
    const add=PropBatch.prototype.add;
    PropBatch.prototype.add=function(...args:Parameters<typeof add>){add.apply(this,args);batches.add(this);};
    PropBatch.CHUNK_M=detail==='low'?80:40;
    let kit:ReturnType<typeof buildBiomeKit>;
    try {kit=buildBiomeKit(track,BIOMES.alpine,library,art,detail);} finally {PropBatch.prototype.add=add;}
    const snapshot=(material:THREE.Material)=>{
      const m=material as THREE.MeshStandardMaterial;
      return {name:m.name,libraryName:library.nameOf(m),color:m.color?.toArray(),roughness:m.roughness,metalness:m.metalness,vertexColors:m.vertexColors,side:m.side,alphaTest:m.alphaTest,transparent:m.transparent,depthWrite:m.depthWrite,fog:m.fog,
        mapNames:Object.fromEntries(['map','normalMap','roughnessMap','metalnessMap','aoMap'].map(key=>{const t=m[key as 'map'];return [key,t?{name:t.name,imageSize:[t.image?.width??null,t.image?.height??null],repeat:t.repeat.toArray(),colorSpace:t.colorSpace}:null];}))};
    };
    const rows=[...batches].filter(b=>/^pine(?:far)?\d$/.test(b.name)||b.name==='contactshadow'||/^(sawmill|waterwheel|loggingtruck|cabin|logstack2?|stump|railfence|timberramp)$/.test(b.name)).map(b=>{
      b.geometry.computeBoundingBox();
      return {name:b.name,shadows:b.shadows,material:snapshot(b.material),prototypeTriangles:(b.geometry.index?.count??b.geometry.getAttribute('position').count)/3,prototypeBounds:b.geometry.boundingBox,
        items:b.items.map(({m,c},index)=>({index,matrix:m.elements.slice(),color:c?.toArray()??null,x:m.elements[12]!,y:m.elements[13]!,z:m.elements[14]!}))};
    });
    const trees=rows.filter(b=>/^pine(?:far)?\d$/.test(b.name));
    const near=trees.filter(b=>!b.name.startsWith('pinefar')).flatMap(b=>b.items.map(item=>({...item,batch:b.name})));
    const far=trees.filter(b=>b.name.startsWith('pinefar')).flatMap(b=>b.items.map(item=>({...item,batch:b.name})));
    const shadows=rows.find(b=>b.name==='contactshadow')!.items;
    const treeShadows=shadows.filter(s=>near.some(t=>Math.abs(t.x-s.x)<1e-8&&Math.abs(t.z-s.z)<1e-8));
    const sceneMeshes:unknown[]=[];
    let draws=0,triangles=0,castMeshes=0;
    kit.group.traverse(object=>{
      if(!(object instanceof THREE.Mesh)) return;
      draws+=Array.isArray(object.material)?object.geometry.groups.length:1;
      triangles+=(object.geometry.index?.count??object.geometry.getAttribute('position').count)/3*(object instanceof THREE.InstancedMesh?object.count:1);
      if(object.castShadow) castMeshes++;
      if(object.name==='terrain'||object.name==='zone:lake'||object.material instanceof THREE.MeshBasicMaterial){object.geometry.computeBoundingBox();sceneMeshes.push({name:object.name,position:object.position.toArray(),bounds:object.geometry.boundingBox,castShadow:object.castShadow,receiveShadow:object.receiveShadow,material:Array.isArray(object.material)?object.material.map(snapshot):snapshot(object.material)});}
    });
    const deck=buildRideSurfaces(track,BIOMES.alpine,library),obstacles=buildObstacles(track,library),gates=buildGates(track,BIOMES.alpine,library,art);
    let allDraws=draws,allTriangles=triangles,allCastMeshes=castMeshes;
    for(const group of [deck.group,deck.supports,obstacles.group,gates.group]) group.traverse(object=>{
      if(!(object instanceof THREE.Mesh)) return;
      allDraws+=Array.isArray(object.material)?object.geometry.groups.length:1;
      allTriangles+=(object.geometry.index?.count??object.geometry.getAttribute('position').count)/3*(object instanceof THREE.InstancedMesh?object.count:1);
      if(object.castShadow) allCastMeshes++;
    });
    tiers.push({detail,chunkMetres:PropBatch.CHUNK_M,nearCount:near.length,farCount:far.length,foregroundTrees:near.filter(t=>t.z>0).length,treeShadowCount:treeShadows.length,farDepthBanks:[far.filter(t=>t.z>=-49).length,far.filter(t=>t.z<-49).length],constructedBiome:{draws,triangles,castMeshes},constructedStaticWorld:{draws:allDraws,triangles:allTriangles,castMeshes:allCastMeshes},near,far,treeShadows,batches:rows,sceneMeshes});
  }
  if(JSON.stringify(tiers[0]!.near)!==JSON.stringify(tiers[1]!.near)||JSON.stringify(tiers[0]!.far)!==JSON.stringify(tiers[1]!.far)) throw new Error(`${def.id}: detail changes anchors`);
  reports.push({id:def.id,seed:def.seed,trackHash:track.hash,bounds:track.bounds,checkpoints:def.checkpoints,cameras:def.meta?.camera,setPieces:setPiecesOf(def),hazards:track.hazards,
    placed:track.placed.map(p=>({...p,x1:p.pos.x+footprint(p.kind as TrackKind,p.params)})),tiers});
}
const report={nodeOnly:true,pixelsStubbed:true,originalAnchorTierParity:true,sourceHashes,limitations:['Actual seeded builders and materials before texture generation; canvas pixels/dummy art cannot establish appearance.','Counts are constructed biome geometry/material draws, not frustum-visible GPU frames.','No A2/A3 course asset hooks or public bytes added.'],tracks:reports};
writeFileSync(new URL('../../../../docs/evidence/course-remaster/alpine-tree-kit/a2-a3-existing-forest-audit.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(reports.map(r=>({id:r.id,seed:r.seed,hash:r.trackHash,near:r.tiers[0]!.nearCount,far:r.tiers[0]!.farCount,shadows:r.tiers[0]!.treeShadowCount,foreground:r.tiers[0]!.foregroundTrees,depthBanks:r.tiers[0]!.farDepthBanks,setPieces:r.setPieces,lowCameras:r.cameras?.filter(c=>c.mode==='low')})),null,2));
