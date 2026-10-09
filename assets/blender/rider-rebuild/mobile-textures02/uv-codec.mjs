// Diagnostic only: exact UV bytes, sequential bounded encodes, no GLB mutation.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { MeshoptEncoder } from 'meshoptimizer/encoder';
import { MeshoptDecoder as ThreeDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { openGlb, viewBytes, fileSha, sha } from '../download-opt01/geometry01/glb.mjs';
const [input, output] = process.argv.slice(2);
assert(input && output);
assert.equal(fileSha(input), 'f814b8d7cde87b1e41b45eec75cd55fdea89b915bf9acae0e5a18b40d3a156af');
await Promise.all([MeshoptEncoder.ready, ThreeDecoder.ready]);
const glb = openGlb(input), rows = [], used = new Set();
for (const [mesh, m] of glb.json.meshes.entries()) for (const [primitive, p] of m.primitives.entries()) {
 const a = glb.json.accessors[p.attributes.TEXCOORD_0], vi = a.bufferView;
 if (used.has(vi)) continue;
 used.add(vi);
 const view = glb.json.bufferViews[vi], existing = view.extensions?.EXT_meshopt_compression;
 const original = await viewBytes(glb, vi), stride = original.length / a.count;
 const sourceWire = existing?.byteLength ?? original.length;
 const formats = [];
 for (const version of [0, 1]) {
  const encoded = MeshoptEncoder.encodeVertexBufferLevel(original, a.count, stride, 3, version);
  const decoded = Buffer.alloc(original.length);
  ThreeDecoder.decodeGltfBuffer(decoded, a.count, stride, encoded, 'ATTRIBUTES', 'NONE');
  assert(decoded.equals(original));
  assert.equal(encoded[0], version === 0 ? 0xa0 : 0xa1);
  formats.push({version, level:3, extension:version===0?'EXT_meshopt_compression':'KHR_meshopt_compression',
   encodedBytes:encoded.length, savingsIfSmaller:Math.max(0,sourceWire-encoded.length),
   decodedByteExact:true, decodedSHA256:sha(decoded), actualPinnedDecoderPass:true});
 }
 rows.push({mesh,primitive,view:vi,componentType:a.componentType,count:a.count,stride,
  sourceDecodedBytes:original.length,sourceWireBytes:sourceWire,sourceDecodedSHA256:sha(original),formats});
}
const totals=[0,1].map(version=>({version,sourceWireBytes:rows.reduce((n,r)=>n+r.sourceWireBytes,0),
 savings:rows.reduce((n,r)=>n+r.formats.find(f=>f.version===version).savingsIfSmaller,0)}));
const result={source:input,sourceSHA256:fileSha(input),diagnosticOnly:true,accepted:false,rows,totals,
 scope:'No UV quantization/reordering; version1 requires KHR labeling, separate KHR fallback buffer and actual GLTFLoader/tooling proof before candidate use.'};
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');fs.closeSync(glb.fd);console.log(JSON.stringify(totals));
