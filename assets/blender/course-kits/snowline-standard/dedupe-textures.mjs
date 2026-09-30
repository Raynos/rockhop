/** Collapse duplicate glTF texture descriptors after Meshopt packing.
 *
 * Blender may emit two `textures[]` entries for the same image and sampler
 * when separate ice and painted-metal nodes share the original grain. Three
 * caches by texture index, so without this rewrite the second descriptor can
 * trigger a duplicate GPU upload. This touches only GLB JSON; the packed BIN,
 * mesh data and embedded image bytes remain byte-identical.
 */
import fs from 'node:fs';

for(const file of process.argv.slice(2)) {
  const bytes=fs.readFileSync(file);
  if(bytes.readUInt32LE(0)!==0x46546c67) throw new Error(`${file}: not GLB`);
  const oldJsonLength=bytes.readUInt32LE(12);
  const doc=JSON.parse(bytes.subarray(20,20+oldJsonLength).toString());
  const textures=doc.textures??[];
  const seen=new Map();
  const remap=[];
  const unique=[];
  textures.forEach((texture,index)=>{
    const key=JSON.stringify(texture);
    const prior=seen.get(key);
    if(prior!==undefined) remap[index]=prior;
    else {const next=unique.length;seen.set(key,next);remap[index]=next;unique.push(texture);}
  });
  if(unique.length===textures.length) continue;
  const rewrite=(value)=>{
    if(!value||typeof value!=='object') return;
    for(const [key,child] of Object.entries(value)) {
      if(key.endsWith('Texture')&&child&&typeof child==='object'&&Number.isInteger(child.index)) {
        child.index=remap[child.index];
      }
      rewrite(child);
    }
  };
  rewrite(doc.materials);
  doc.textures=unique;
  const json=Buffer.from(JSON.stringify(doc));
  const padding=Buffer.alloc((4-json.length%4)%4,32);
  const remaining=bytes.subarray(20+oldJsonLength);
  const out=Buffer.alloc(20+json.length+padding.length+remaining.length);
  out.writeUInt32LE(0x46546c67,0);
  out.writeUInt32LE(2,4);
  out.writeUInt32LE(out.length,8);
  out.writeUInt32LE(json.length+padding.length,12);
  out.writeUInt32LE(0x4e4f534a,16);
  json.copy(out,20);padding.copy(out,20+json.length);
  remaining.copy(out,20+json.length+padding.length);
  fs.writeFileSync(file,out);
  process.stdout.write(`${file}: ${textures.length} → ${unique.length} texture descriptors\n`);
}
