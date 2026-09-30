/** Node-only decoded bank + candidate composition audit. No shared renderer hook. */
import fs from 'node:fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { readGlb, writeGlb } from '../../hero_art_pack.mjs';
import { loadCoastHarbor, planC1Harbor } from '../../../../src/render/world/zones/coastHarbor';
const out=new URL('./out/',import.meta.url);
const plan=planC1Harbor(()=>0,-2.82);
const results=[];
for(const tier of ['full','lod'] as const){
  const source=fs.readFileSync(new URL(`coast-harbor${tier==='lod'?'-lod':''}.glb`,out));
  const {doc,bin}=readGlb(source);delete doc.images;delete doc.textures;delete doc.samplers;
  for(const m of doc.materials){delete m.normalTexture;delete m.occlusionTexture;delete m.pbrMetallicRoughness.baseColorTexture;delete m.pbrMetallicRoughness.metallicRoughnessTexture;}
  const bytes=writeGlb(doc,bin);
  const gltf=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
  const images=[{width:512,height:512},{width:512,height:512},{width:512,height:512}];
  const seen=new Set<THREE.Material>();gltf.scene.traverse(o=>{if(!(o instanceof THREE.Mesh)||seen.has(o.material as THREE.Material))return;const m=o.material as THREE.MeshStandardMaterial;seen.add(m);if(m.name!=='coast manufactured PBR atlas')return;m.map=new THREE.Texture(images[0]);m.normalMap=new THREE.Texture(images[1]);m.roughnessMap=new THREE.Texture(images[2]);m.metalnessMap=m.roughnessMap;});
  const original=GLTFLoader.prototype.loadAsync;
  GLTFLoader.prototype.loadAsync=async()=>gltf;
  try{
    const asset=await loadCoastHarbor(plan,{detail:tier,assetRoot:'https://source.example/',resolveModel:s=>s,resolveResource:s=>s});
    let wholeTriangles=0;const unique=new Set<THREE.BufferGeometry>();const samples=[];
    for(const o of asset.root.children as THREE.InstancedMesh[]){unique.add(o.geometry);wholeTriangles+=(o.geometry.index?.count??o.geometry.attributes.position!.count)/3*o.count;}
    for(let x=0;x<=500;x+=.25){
      let calls=0,triangles=0;
      for(const o of asset.root.children as THREE.InstancedMesh[]){
        const b=o.boundingBox!;
        // Conservative longitudinal envelope; deliberately ignores depth/fog occlusion.
        if(b.max.x<x-32||b.min.x>x+32)continue;
        calls++;triangles+=(o.geometry.index?.count??o.geometry.attributes.position!.count)/3*o.count;
      }
      samples.push({x,calls,triangles});
    }
    const geometryBytes=[...unique].reduce((sum,g)=>sum+(g.index?.array.byteLength??0)+Object.values(g.attributes).reduce((s,a)=>s+a.array.byteLength,0),0);
    results.push({tier,actors:plan.length,wholeBankGeometryBytes:geometryBytes,ownedResidentMapsBytes:asset.textureBytes,wholeCourseCandidateCalls:asset.root.children.length,wholeCourseCandidateTriangles:wholeTriangles,max64mWindowCalls:Math.max(...samples.map(s=>s.calls)),max64mWindowTriangles:Math.max(...samples.map(s=>s.triangles)),peakCallWindows:samples.filter(s=>s.calls===Math.max(...samples.map(q=>q.calls))).slice(0,3),limit:'CPU x-envelope estimate only; no renderer culling, production fog, hero, terrain, colliders, post or actual GPU proof'});
    asset.dispose();
  }finally{GLTFLoader.prototype.loadAsync=original;}
}
const audit={status:'offline candidate, not integrated or visually accepted',plan,results};
fs.writeFileSync(new URL('../../../../docs/evidence/course-remaster/coast-harbor/composition-audit.json',import.meta.url),JSON.stringify(audit,null,2)+'\n');console.log(JSON.stringify(results,null,2));
