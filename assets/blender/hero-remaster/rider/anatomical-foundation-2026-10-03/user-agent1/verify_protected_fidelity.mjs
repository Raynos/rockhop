// Verify protected fidelity; optional new-file derivative restores raw source
// NORMAL bytes lost to native custom-normal quantization, preserving the input.
import fs from 'node:fs';
import crypto from 'node:crypto';
const [donorPath,candidatePath,output,restoreTo] = process.argv.slice(2);
if(restoreTo&&fs.existsSync(restoreTo))throw Error("Frozen normal derivative exists");
const sha = raw => crypto.createHash('sha256').update(raw).digest('hex');
function read(file) {
  const bytes=fs.readFileSync(file), n=bytes.readUInt32LE(12), doc=JSON.parse(bytes.subarray(20,20+n)), bin=bytes.subarray(28+n);
  function attribute(index) {
    const a=doc.accessors[index], v=doc.bufferViews[a.bufferView], c={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type], size={5126:4,5125:4,5123:2,5121:1}[a.componentType];
    const values=[];
    for(let i=0;i<a.count;i++) { const row=[]; for(let j=0;j<c;j++) {const off=(v.byteOffset??0)+(a.byteOffset??0)+i*(v.byteStride??c*size)+j*size;
      row.push(a.componentType===5126?bin.readFloatLE(off):a.componentType===5125?bin.readUInt32LE(off):a.componentType===5123?bin.readUInt16LE(off):bin.readUInt8(off));} values.push(row); }
    return values;
  }
  function image(index) {const v=doc.bufferViews[doc.images[index].bufferView];return bin.subarray(v.byteOffset??0,(v.byteOffset??0)+v.byteLength);}
  function normalWrite(index,row,values) {
    const a=doc.accessors[index],v=doc.bufferViews[a.bufferView];if(a.componentType!==5126||a.type!=='VEC3')throw Error('Expected float normal');
    values.forEach((value,j)=>bin.writeFloatLE(value,(v.byteOffset??0)+(a.byteOffset??0)+row*(v.byteStride??12)+j*4));
  }
  return {bytes,doc,attribute,image,normalWrite};
}
const source=read(donorPath), candidate=read(candidatePath);
if(sha(source.bytes)!=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754') throw Error('Wrong donor');
const rows=[];
for(const [pi,match] of [[0,'Protected textured head'],[1,'Protected coherent cheek']]) {
  const sp=source.doc.meshes[1].primitives[pi], mesh=candidate.doc.meshes.find(m=>m.name.startsWith(match));
  if(!mesh || mesh.primitives.length!==1) throw Error('Expected one protected primitive '+match);
  const p=mesh.primitives[0], sv=source.attribute(sp.attributes.POSITION), su=source.attribute(sp.attributes.TEXCOORD_0), sn=source.attribute(sp.attributes.NORMAL);
  const cv=candidate.attribute(p.attributes.POSITION), cu=candidate.attribute(p.attributes.TEXCOORD_0), cn=candidate.attribute(p.attributes.NORMAL);
  // Blender skinned export bakes root+.65 into POSITION; both raw
  // source/candidate arrays therefore occupy the same pinned file-world rest.
  const key=v=>v.map(x=>Math.floor(x*1e5)).join(','); const map=new Map();
  sv.forEach((v,i)=>{const k=key(v,su[i]);const ids=map.get(k)??[];ids.push(i);map.set(k,ids);});
  let maxPos=0,maxUV=0,maxNormal=0,maxUnitNormal=0,maxAngle=0,ambiguous=0;
  for(let i=0;i<cv.length;i++) {
    const cell=cv[i].map(x=>Math.floor(x*1e5)), ids=[];
    for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)for(let dz=-1;dz<=1;dz++) {
      for(const j of map.get([cell[0]+dx,cell[1]+dy,cell[2]+dz].join(','))??[]) {
        if(cv[i].every((x,k)=>Math.abs(x-sv[j][k])<2e-7)&&cu[i].every((x,k)=>Math.abs(x-su[j][k])<2e-7))ids.push(j);
      }
    }
    if(!ids.length)throw Error('Unmapped protected row '+match+' '+i);
    if(ids.length>1)ambiguous++;
    const sourceId=ids.reduce((best,j)=>sn[j].reduce((sum,x,k)=>sum+(x-cn[i][k])**2,0)<sn[best].reduce((sum,x,k)=>sum+(x-cn[i][k])**2,0)?j:best,ids[0]);
    const j=sourceId;maxPos=Math.max(maxPos,...cv[i].map((x,k)=>Math.abs(x-sv[j][k])));maxUV=Math.max(maxUV,...cu[i].map((x,k)=>Math.abs(x-su[j][k])));
    const normalError=Math.hypot(...cn[i].map((x,k)=>x-sn[j][k]));maxNormal=Math.max(maxNormal,normalError);
    maxUnitNormal=Math.max(maxUnitNormal,Math.hypot(...cn[i].map((x,k)=>x/Math.hypot(...cn[i])-sn[j][k]/Math.hypot(...sn[j]))));
    if(restoreTo)candidate.normalWrite(p.attributes.NORMAL,i,sn[j]);
    const dot=cn[i].reduce((sum,x,k)=>sum+x*sn[j][k],0)/(Math.hypot(...cn[i])*Math.hypot(...sn[j]));maxAngle=Math.max(maxAngle,Math.acos(Math.max(-1,Math.min(1,dot)))*180/Math.PI);
  }
  const sm=source.doc.materials[sp.material], cm=candidate.doc.materials[p.material], expected=sm.extensions?.KHR_materials_specular?.specularFactor??1, actual=cm.extensions?.KHR_materials_specular?.specularFactor??1;
  const si=source.doc.textures[sm.pbrMetallicRoughness.baseColorTexture.index].source, ci=candidate.doc.textures[cm.pbrMetallicRoughness.baseColorTexture.index].source;
  if(maxPos>2e-7||maxUV>2e-7||maxUnitNormal>1e-3||Math.abs(expected-actual)>1e-7||sha(source.image(si))!==sha(candidate.image(ci))) throw Error('Protected source fidelity bound failed '+JSON.stringify({match,maxPos,maxUV,maxNormal,maxUnitNormal,expected,actual}));
  rows.push({name:match,candidateVertices:cv.length,maxPositionErrorM:maxPos,maxUVError:maxUV,maxNativeRawNormalVectorError:maxNormal,maxNativeUnitNormalError:maxUnitNormal,maxNativeNormalAngleDegrees:maxAngle,
    rawSourceNormalRestoredToNewExport:!!restoreTo,
    ambiguousPositionUVCandidateRows:ambiguous,expectedSpecularFactor:expected,actualSpecularFactor:actual,baseColorImageSHA256:sha(candidate.image(ci))});
}
if(restoreTo)fs.writeFileSync(restoreTo,candidate.bytes,{flag:'wx'});
const report={status:restoreTo?'New GLB derivative restores exact raw protected source NORMAL values; input/native quantization residual measured':'Protected source positions/UV/image bytes/specular within float bounds; native normalized normal directions verified',
  donorSHA256:sha(source.bytes),inputCandidateSHA256:sha(fs.readFileSync(candidatePath)),candidateSHA256:sha(candidate.bytes),recipeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),rows,
  limits:['Position+UV duplicate candidates resolve by source-normal agreement; ambiguity count is explicit, not a unique source-ID claim.',
    'Blender custom-normal storage/export quantizes/normalizes vectors; native residual is measured. Optional derivative overwrites only protected NORMAL accessor components with raw source values, leaving input frozen.',
    'This read-only export proof is not actual Garage appearance/art/mobile or complete fit acceptance.']};
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log('PROTECTED_FIDELITY_VERIFIED',rows);
