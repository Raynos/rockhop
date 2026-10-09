// Execute the pinned historical02 recipe with only explicit source-pin adaptation.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { fileSha } from '../../download-opt01/geometry01/glb.mjs';
const [input,output,receiptPath]=process.argv.slice(2);
assert(input && output && receiptPath);
const graftSha='b916c7f0503df6be571a345740ebf7ec5b374f2108c0165890986dc22ffef4f0';
const recipeUrl=new URL('../../download-opt01/geometry02/pack.mjs',import.meta.url);
const recipeSha='d76b24997fd378cb4036f75a0c8de79381115e21763f23030fb4ac4361f75728';
assert.equal(fileSha(input),graftSha);
assert.equal(fileSha(recipeUrl),recipeSha,'Historical02 recipe changed');
let source=fs.readFileSync(recipeUrl,'utf8');
function replaceOne(before,after){assert.equal(source.split(before).length,2);source=source.replace(before,after);}
replaceOne("const expectedSha = '127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649';",`const expectedSha = '${graftSha}';`);
replaceOne('assert.deepEqual(j.buffers, [{ byteLength: 358320904 }]);','assert.deepEqual(j.buffers, [{ byteLength: 209617068 }]);');
for(const name of ['meshoptimizer/encoder','meshoptimizer/decoder'])replaceOne(`from '${name}'`,`from '${import.meta.resolve(name)}'`);
replaceOne("from '../geometry01/glb.mjs'",`from '${new URL('../../download-opt01/geometry01/glb.mjs',import.meta.url).href}'`);
await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const receipt=JSON.parse(fs.readFileSync(receiptPath));
const hoodie=receipt.primitives.filter(p=>p.mesh===5);
assert.equal(hoodie.length,1);
assert(hoodie[0].attributes.includes('TANGENT'));
assert(!hoodie[0].precision.some(p=>p.semantic==='TANGENT'),'TANGENT must remain Float32');
for(const p of receipt.primitives)for(const precision of p.precision)
 if(precision.semantic==='TEXCOORD_0')assert(precision.maxTexelErrorAt4096<0.05,'Actual unchanged02 UV quantization exceeds0.05texel');
receipt.composition={sourceGraftSHA256:graftSha,historicalRecipeSHA256:recipeSha,
 sourcePinAndBinLengthOnly:true,quantizationAlgorithmsFlagsUnchanged:true,TANGENTFloat32Preserved:true,
 actualUVErrorLessThan005Texel4096:true,accepted:false};
fs.writeFileSync(receiptPath,`${JSON.stringify(receipt,null,2)}\n`);
