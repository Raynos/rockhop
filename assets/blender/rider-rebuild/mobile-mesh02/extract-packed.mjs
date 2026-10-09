// Exact final packed geometry fields, not a second quantization implementation.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {openGlb,accessorBytes,fileSha} from '../download-opt01/geometry01/glb.mjs';
const [input,receipt,partsRoot,out]=process.argv.slice(2),r=JSON.parse(fs.readFileSync(receipt));
assert.equal(fileSha(input),r.output.sha256);assert.equal(r.nativeJsonRigAndClipsExact,true);
const g=openGlb(input);fs.mkdirSync(out,{recursive:true});const rows=[];
for(const [mi,part] of ['boot-L','boot-R','glove-L','glove-R'].entries()){
 const p=g.json.meshes[mi].primitives[0];const w=g.json.accessors[p.attributes.WEIGHTS_0];assert.equal(w.componentType,5123);assert.equal(w.normalized,true);assert.equal(w.type,'VEC4');
 for(const sem of ['POSITION','NORMAL','TEXCOORD_0','TANGENT','JOINTS_0'])assert.deepEqual(await accessorBytes(g,p.attributes[sem]),fs.readFileSync(path.join(partsRoot,part,...(mi>=2?['skin03','bake01']:['bake01']),sem+'.bin')));
 const bytes=await accessorBytes(g,p.attributes.WEIGHTS_0),output=path.join(out,part+'-weights.u16');fs.writeFileSync(output,bytes);rows.push({part,weights:output,vertices:w.count});
}
fs.writeFileSync(path.join(out,'intake.json'),JSON.stringify({sourceSHA256:fileSha(input),parts:rows,allGeometryExceptWeightStorageMatchesAtlasExactly:true},null,2)+'\n');fs.closeSync(g.fd);
