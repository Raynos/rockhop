// Pinned original selected sculpt extraction, geometry and component images only.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {openGlb,accessorBytes,viewBytes,fileSha} from '../download-opt01/geometry01/glb.mjs';
const [input,out,index]=process.argv.slice(2), meshIndex=Number(index);
assert([0,1,2,3].includes(meshIndex));
assert.equal(fileSha(input),'127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649');
fs.mkdirSync(out,{recursive:true});const g=openGlb(input),p=g.json.meshes[meshIndex].primitives[0];
const material=g.json.materials[p.material],report={source:input,sha256:fileSha(input),meshIndex,meshName:g.json.meshes[meshIndex].name,material,attributes:{},indices:g.json.accessors[p.indices]};
for(const [k,v] of Object.entries(p.attributes)){fs.writeFileSync(path.join(out,k+'.bin'),await accessorBytes(g,v));report.attributes[k]=g.json.accessors[v];}
fs.writeFileSync(path.join(out,'indices.bin'),await accessorBytes(g,p.indices));
for(const [name,index] of [['albedo',material.pbrMetallicRoughness.baseColorTexture.index],['orm',material.pbrMetallicRoughness.metallicRoughnessTexture.index]]){const i=g.json.images[g.json.textures[index].source];assert.equal(i.mimeType,'image/png');fs.writeFileSync(path.join(out,name+'.png'),await viewBytes(g,i.bufferView));}
fs.writeFileSync(path.join(out,'intake.json'),JSON.stringify(report,null,2)+'\n');fs.closeSync(g.fd);console.log(JSON.stringify(report));
