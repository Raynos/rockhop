/** Decode both frozen candidates with the exact runtime GLTFLoader/MeshoptDecoder. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { glbStats } from '../../glb_stats.mjs';

const dir = path.dirname(fileURLToPath(import.meta.url));
const expected = new Set(['gorge-wall','shelf-face','lift-tower','lift-chair','lift-station','snowcat','summit-beacon']);
await MeshoptDecoder.ready;
const report = [];
function geometryOnly(bytes){
  // Node has no ImageBitmap decoder; retain the exact compressed geometry and
  // node transforms while stripping only material image references. Image
  // dimensions/mime/byte caps are checked against the original GLB below.
  const jsonLength=bytes.readUInt32LE(12);
  const doc=JSON.parse(bytes.subarray(20,20+jsonLength).toString());
  delete doc.images;delete doc.textures;delete doc.samplers;
  for(const m of doc.materials??[]){
    delete m.normalTexture;delete m.occlusionTexture;delete m.emissiveTexture;
    if(m.pbrMetallicRoughness){delete m.pbrMetallicRoughness.baseColorTexture;delete m.pbrMetallicRoughness.metallicRoughnessTexture;}
  }
  const json=Buffer.from(JSON.stringify(doc));
  const pad=Buffer.alloc((4-json.length%4)%4,32);
  const bin=bytes.subarray(20+jsonLength);
  const out=Buffer.alloc(20+json.length+pad.length+bin.length);
  out.writeUInt32LE(0x46546c67,0);out.writeUInt32LE(2,4);out.writeUInt32LE(out.length,8);
  out.writeUInt32LE(json.length+pad.length,12);out.writeUInt32LE(0x4e4f534a,16);
  json.copy(out,20);pad.copy(out,20+json.length);bin.copy(out,20+json.length+pad.length);
  return out;
}
for (const file of ['snowline-standard-packed.glb','snowline-standard-lod-packed.glb']) {
  const bytes = fs.readFileSync(path.join(dir,'out',file));
  const s = glbStats(path.join(dir,'out',file));
  if(s.maxTexture>512||s.imageBytes>2_000_000) throw new Error(`${file}: texture budget`);
  const geometry=geometryOnly(bytes);
  const loaded = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder)
    .parseAsync(geometry.buffer.slice(geometry.byteOffset,geometry.byteOffset+geometry.byteLength),'');
  loaded.scene.updateMatrixWorld(true);
  const names = new Set();
  for(const name of expected){
    const node=loaded.scene.getObjectByName('snowline'+name);
    if(!node) throw new Error(`${file}: missing ${name}`);
    names.add(name);
    let parts=0;
    node.traverse(object=>{
      if(!(object instanceof THREE.Mesh)) return;
      parts++;
      const box=new THREE.Box3().setFromObject(object);
      if(![...box.min,...box.max].every(Number.isFinite)) throw new Error(`${file}: nonfinite ${name}`);
      const position=object.geometry.getAttribute('position');
      const color=object.geometry.getAttribute('color');
      if(!position||!color||color.count!==position.count) throw new Error(`${file}: lost COLOR_0 ${name}`);
      const mats=Array.isArray(object.material)?object.material:[object.material];
      for(const m of mats) if(!m.vertexColors) throw new Error(`${file}: palette disabled ${name}`);
    });
    if(parts<1||parts>4) throw new Error(`${file}: bad part count ${name}:${parts}`);
  }
  report.push({ file,sha256:s.sha256,bytes:s.bytes,triangles:s.triangles,draws:s.draws,
    images:s.imageList,names:[...names].sort((a,b)=>a<b?-1:a>b?1:0),decoder:'three GLTFLoader + bundled MeshoptDecoder; texture metadata from original GLB' });
}
fs.writeFileSync(path.join(dir,'out','decoder-report.json'),JSON.stringify(report,null,2)+'\n');
process.stdout.write(JSON.stringify(report,null,2)+'\n');
