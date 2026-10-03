// Preserve exact native skin fields below Blender's installed1e-4 cutoff.
import fs from 'node:fs';
import crypto from 'node:crypto';
const [input,attachmentsFile,handoffFile,output,receipt]=process.argv.slice(2);
if(fs.existsSync(output))throw Error('Frozen skin derivative exists');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const original=fs.readFileSync(input),bytes=Buffer.from(original),length=bytes.readUInt32LE(12),doc=JSON.parse(bytes.subarray(20,20+length)),binStart=28+length;
const d=JSON.parse(fs.readFileSync(attachmentsFile)),h=JSON.parse(fs.readFileSync(handoffFile));
if(sha(original)!==d.candidateGLBSHA256||doc.meshes.length!==1||doc.meshes[0].primitives.length!==1)throw Error('Wrong raw sleeve source');
const primitive=doc.meshes[0].primitives[0],p=doc.accessors[primitive.attributes.POSITION],j=doc.accessors[primitive.attributes.JOINTS_0],w=doc.accessors[primitive.attributes.WEIGHTS_0];
if(p.componentType!==5126||w.componentType!==5126||p.type!=='VEC3'||j.type!=='VEC4'||w.type!=='VEC4'||![5121,5123].includes(j.componentType))throw Error('Unexpected raw skin layout');
const jointSize=j.componentType===5121?1:2;
const offset=(accessor,row,k,size,components)=>{const view=doc.bufferViews[accessor.bufferView];return binStart+(view.byteOffset??0)+(accessor.byteOffset??0)+row*(view.byteStride??size*components)+k*size;};
const joints=doc.skins[0].joints.map(id=>doc.nodes[id].name),allowed=new Set();const ancestry=[];
for(let row=0;row<p.count;row++){
 const raw=[0,1,2].map(k=>bytes.readFloatLE(offset(p,row,k,4,3))),native=[raw[0]-.65,-raw[2],raw[1]];
 const matches=h.pattern.verticesNativeM.map((v,id)=>({id,error:Math.hypot(...v.map((x,k)=>x-native[k]))})).filter(r=>r.error<2e-6);
 if(matches.length!==1)throw Error('Unmapped source row');
 const id=matches[0].id,pairs=Object.entries(d.attachments[id].actualNativeAfterWeights).sort((a,b)=>b[1]-a[1]);
 if(pairs.length>4||Math.abs(pairs.reduce((s,p)=>s+p[1],0)-1)>1e-6)throw Error('Invalid native skin field');
 for(let k=0;k<4;k++){
  const index=k<pairs.length?joints.indexOf(pairs[k][0]):0,value=k<pairs.length?pairs[k][1]:0;
  if(index<0)throw Error('Missing native joint');
  const jo=offset(j,row,k,jointSize,4),wo=offset(w,row,k,4,4);
  if(jointSize===1)bytes.writeUInt8(index,jo);else bytes.writeUInt16LE(index,jo);
  bytes.writeFloatLE(value,wo);
  for(let b=0;b<jointSize;b++)allowed.add(jo+b);for(let b=0;b<4;b++)allowed.add(wo+b);
 }
 ancestry.push({exportedRow:row,nativeVertexID:id,rawPositionVsNativeM:matches[0].error});
}
let changed=0;for(let i=0;i<bytes.length;i++)if(bytes[i]!==original[i]){if(!allowed.has(i))throw Error('Non-skin byte changed');changed++;}
fs.writeFileSync(output,bytes);
fs.writeFileSync(receipt,JSON.stringify({status:'UNACCEPTED exactnative skin derivative; only JOINTS_0/WEIGHTS_0 bytes restored',inputSHA256:sha(original),outputSHA256:sha(bytes),attachmentsSHA256:sha(fs.readFileSync(attachmentsFile)),recipeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),
 installedExporterCutoff:0.0001,installedPrimarySource:'/Applications/Blender.app/Contents/Resources/5.2/scripts/addons_core/io_scene_gltf2/blender/exp/primitive_extract.py:1561',
 bytesChanged:changed,allOtherBytesExact:true,ancestry,limits:['Actual GLTFLoader weight verification follows; no export cutoff tolerance was weakened.','No extra joints, geometry, UV, normal, material, bind or native source change.']},null,2)+'\n');
console.log(JSON.stringify({outputSHA256:sha(bytes),rows:ancestry.length,changed}));
