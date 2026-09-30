/** Offline Coast frontage bank. Never writes public/catalogs/dist. Blender shares model lock. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { pack, readGlb, writeGlb } from '../../hero_art_pack.mjs';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
const dir=path.dirname(fileURLToPath(import.meta.url)), root=path.resolve(dir,'../../../..'), out=path.join(dir,'out');
fs.mkdirSync(out,{recursive:true});
const run=(cmd,args)=>{const r=spawnSync(cmd,args,{cwd:root,encoding:'utf8',maxBuffer:32*1024*1024}); if(r.status!==0)throw Error(`${cmd}: ${r.stderr}\n${r.stdout}`);};
if(!process.argv.includes('--pack-only')) run('lockf',['-k',path.join(process.env.HOME,'projects/localai/.model.lock'),'blender','-b','--factory-startup','-noaudio','--python-exit-code','1','-P',path.join(dir,'build.py'),'--','--out',out,...(process.argv.includes('--skip-render')?['--skip-render']:[])]);
const maps=new Map(); const models=[]; const sha=buffer=>createHash('sha256').update(buffer).digest('hex');
for(const stem of ['coast-frontage','coast-frontage-lod']){
  const {doc,bin}=readGlb(fs.readFileSync(path.join(out,stem+'.raw.glb')));
  const imageViews=new Set(doc.images.map(i=>i.bufferView)); const indices=new Map(); const chunks=[]; let offset=0;
  for(const [id,view] of doc.bufferViews.entries()){
    if(imageViews.has(id))continue;
    const pad=(4-offset%4)%4; chunks.push(Buffer.alloc(pad)); offset+=pad;
    indices.set(id,{index:indices.size,view:{...view,byteOffset:offset}});
    chunks.push(bin.subarray(view.byteOffset??0,(view.byteOffset??0)+view.byteLength)); offset+=view.byteLength;
  }
  for(const image of doc.images){
    const source=doc.bufferViews[image.bufferView]; const bytes=bin.subarray(source.byteOffset??0,(source.byteOffset??0)+source.byteLength);
    const kind=/normal/i.test(image.name)?'normal':/arm|metal|rough/i.test(image.name)?'arm':'albedo';
    const family=/frontage/i.test(image.name)?'frontage':'coast';
    const name=`${family}-${kind}.phone.webp`, png=path.join(out,`exported-${family}-${kind}.png`);
    fs.writeFileSync(png,bytes); run('cwebp',['-quiet','-lossless',png,'-o',path.join(out,name)]);
    const hash=sha(fs.readFileSync(path.join(out,name))); assert(!maps.has(name)||maps.get(name).sha256===hash,'LOD texture changed');
    maps.set(name,{file:name,bytes:fs.statSync(path.join(out,name)).size,sha256:hash,width:family==='frontage'?256:512,height:family==='frontage'?256:512});
    delete image.bufferView; delete image.mimeType; image.uri=name;
  }
  for(const a of doc.accessors) a.bufferView=indices.get(a.bufferView).index;
  doc.bufferViews=[...indices.values()].map(i=>i.view); doc.buffers=[{byteLength:offset}];
  const external=path.join(out,stem+'.external.glb'), target=path.join(out,stem+'.glb');
  fs.writeFileSync(external,writeGlb(doc,Buffer.concat(chunks)));
  const compression=await pack(external,target,{stripSceneExtras:true});
  // Production decoder, no DOM/network: strip maps for geometry validation only.
  const packed=readGlb(fs.readFileSync(target)); const decodeDoc=structuredClone(packed.doc);
  delete decodeDoc.images; delete decodeDoc.textures; delete decodeDoc.samplers;
  for(const m of decodeDoc.materials){delete m.normalTexture;delete m.occlusionTexture;delete m.emissiveTexture;delete m.pbrMetallicRoughness.baseColorTexture;delete m.pbrMetallicRoughness.metallicRoughnessTexture;}
  const bytes=writeGlb(decodeDoc,packed.bin); const gltf=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
  const prototypes=[]; let total=0,draws=0,geometryBytes=0;
  for(const node of gltf.scene.children){let triangles=0,primitives=0; const bounds=[];
    node.traverse(o=>{if(!o.isMesh)return;primitives++;const g=o.geometry;triangles+=(g.index?.count??g.attributes.position.count)/3; for(const [name,a] of Object.entries(g.attributes)){geometryBytes+=a.array.byteLength;for(let i=0;i<a.count;i++)for(let j=0;j<a.itemSize;j++)assert(Number.isFinite(a.array[i*a.itemSize+j]),`${node.name} nonfinite ${name}`);}geometryBytes+=g.index?.array.byteLength??0;g.computeBoundingBox();bounds.push({min:g.boundingBox.min.toArray(),max:g.boundingBox.max.toArray()});assert(g.attributes.uv,'atlas UV absent'); if(o.material.name==='coast manufactured PBR atlas') for(let i=0;i<g.attributes.uv.count;i++){assert(g.attributes.uv.getX(i)>.006&&g.attributes.uv.getY(i)>.006,'lost material region UV');} g.dispose();});
    if(['brick-repair-shed','sawtooth-maintenance-hall'].includes(node.name)) for(const b of bounds) {
      assert(b.min[0]>=-14.15 && b.max[0]<=14.15,`${node.name} exceeds existing X footprint`);
      assert(b.min[2]>=-6.60 && b.max[2]<=7.56,`${node.name} exceeds existing depth footprint: ${b.min[2]}..${b.max[2]}`);
      assert(b.min[1]>=0,`${node.name} below grounded pivot`);
    }
    total+=triangles;draws+=primitives;prototypes.push({name:node.name,triangles,primitives,bounds});
  }
  assert.equal(prototypes.length,9);assert(draws<=27);assert(total<=(stem.endsWith('lod')?65000:125000));
  models.push({file:stem+'.glb',bytes:fs.statSync(target).size,sha256:sha(fs.readFileSync(target)),triangles:total,draws,geometryBytes,prototypes,compression:{views:compression.compressedViews,positionBits:compression.positionBits,normalBits:compression.normalBits}});
}
// The extension may replace selected warehouse instances, but every original
// prototype and original map must remain available to unchanged placements.
const baseline=JSON.parse(fs.readFileSync(path.join(dir,'../coast-harbor/delivery/manifest.json'),'utf8'));
for(let tier=0;tier<2;tier++)for(const original of baseline.models[tier].prototypes){
  const retained=models[tier].prototypes.find(p=>p.name===original.name);
  assert(retained && retained.triangles===original.triangles && retained.primitives===original.primitives,
    `Original Coast prototype changed: ${original.name}`);
}
for(const original of baseline.maps){
  assert.equal(maps.get(original.file)?.sha256,original.sha256,`Original Coast map changed: ${original.file}`);
}
for(const name of ['brick-repair-shed','sawtooth-maintenance-hall']) if(fs.existsSync(path.join(out,`${name}-000.png`)))
  run('magick',['montage',...[0,40,80,120,160,200,240,280,320].map(a=>path.join(out,`${name}-${String(a).padStart(3,'0')}.png`)),'-tile','3x3','-geometry','900x600+6+6','-background','#253638',path.join(out,`${name}-nine-angle.jpg`)]);
const manifest={status:'offline authored candidate; no played integration or acceptance',modelAxes:'GLB X along quay, Y up, warehouse front at Z=-6, dry prototypes base Y=0',maps:[...maps.values()],models,residentMapsBytes:[...maps.values()].reduce((sum,m)=>sum+m.width*m.height*4*4/3,0),sourceSha256:sha(fs.readFileSync(path.join(dir,'build.py'))),variantSourceSha256:sha(fs.readFileSync(path.join(dir,'frontage_variants.py')))};
fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify(manifest,null,2));
