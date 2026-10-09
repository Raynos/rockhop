// Append only selected sleeve geometry streams; preserve source/native payloads.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {openGlb,viewBytes,readAt,fileSha,sha,indexValues} from '../download-opt01/geometry01/glb.mjs';
import {verifyParityFiles} from '../focused-delivery07/verify-parity.mjs';
const [source,fitDirectory,out]=process.argv.slice(2);
const BASELINE='585ae314e2b354768a1385e5a85828c142d542b47f8d9fe948f46c7478c112ef';
assert.equal(fileSha(source),BASELINE); assert(!fs.existsSync(out),'Fresh output required');
const patch=path.join(fitDirectory,'patch.npz'),reportFile=path.join(fitDirectory,'report.json');
const report=JSON.parse(fs.readFileSync(reportFile));
assert.equal(report.nonpositiveAreaOrientationDots,0,'Uninverted source topology required');
assert.equal(report.poseCount,482); assert.equal(report.gloveNativeFieldsExact,true);assert.equal(report.newlyDegenerateTriangles,0);
const unpack=spawnSync('python3',['-c',"import zipfile,sys;sys.stdout.buffer.write(zipfile.ZipFile(sys.argv[1]).read('positionsAfter.npy'))",patch],{maxBuffer:16*1024*1024});
assert.equal(unpack.status,0,String(unpack.stderr));
const npy=unpack.stdout;assert.equal(npy.subarray(0,6).toString('latin1'),'\x93NUMPY');assert.equal(npy[6],1);
const header=npy.subarray(10,10+npy.readUInt16LE(8)).toString();assert(header.includes("'<f4'"));assert(header.includes("False"));
const positionBytes=Buffer.from(npy.subarray(10+npy.readUInt16LE(8)));
const g=openGlb(source),before=g.json,j=structuredClone(before),prim=j.meshes[5].primitives[0],n=j.accessors[prim.attributes.POSITION].count;
assert.equal(positionBytes.length,n*12);
const cache=new Map();async function bytes(ai){const view=before.accessors[ai].bufferView;if(!cache.has(view))cache.set(view,await viewBytes(g,view));return cache.get(view);}
const oldP=await bytes(prim.attributes.POSITION),oldN=await bytes(prim.attributes.NORMAL),oldT=await bytes(prim.attributes.TANGENT);
const positions=new Float32Array(positionBytes.buffer,positionBytes.byteOffset,n*3),original=new Float32Array(oldP.buffer,oldP.byteOffset,n*3);
const normals=Buffer.from(oldN),tangents=Buffer.from(oldT);
const inds=indexValues(await bytes(prim.indices),j.accessors[prim.indices]);
const changed=new Uint8Array(n),affectedVertex=new Uint8Array(n),sumN=new Float64Array(n*3),sumT=new Float64Array(n*3),sumWeight=new Float64Array(n);
for(let i=0;i<n;i++)changed[i]=Number(!oldP.subarray(i*12,i*12+12).equals(positionBytes.subarray(i*12,i*12+12)));
for(let i=0;i<inds.length;i+=3)if(changed[inds[i]]||changed[inds[i+1]]||changed[inds[i+2]])for(let k=0;k<3;k++)affectedVertex[inds[i+k]]=1;
const sub=(a,b)=>a.map((x,k)=>x-b[k]);const dot=(a,b)=>a.reduce((s,x,k)=>s+x*b[k],0);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const norm=a=>Math.sqrt(dot(a,a));const unit=a=>{const l=norm(a);assert(l>0);return a.map(x=>x/l);};
const point=(a,i)=>Array.from(a.subarray(i*3,i*3+3));
const normal=i=>[0,1,2].map(k=>Math.max(-1,oldN.readInt16LE(i*8+k*2)/32767));
const tangent=i=>[0,1,2].map(k=>oldT.readFloatLE(i*16+k*4));
// A triangle's actual deformation differential transports authored normals and
// tangents. Incident unchanged faces contribute their identity differential.
let affectedTriangles=0,minOrientation=Infinity;
for(let t=0;t<inds.length;t+=3){
  const ids=[inds[t],inds[t+1],inds[t+2]];if(!ids.some(i=>affectedVertex[i]))continue;
  const [a,b,c]=ids.map(i=>point(original,i)),[aa,bb,cc]=ids.map(i=>point(positions,i));
  const e1=sub(b,a),e2=sub(c,a),f1=sub(bb,aa),f2=sub(cc,aa),area=cross(e1,e2),newArea=cross(f1,f2),weight=norm(area);
  if(weight<1e-20)continue;
  const z=unit(area),zz=unit(newArea),det=dot(e1,cross(e2,z)),newDet=dot(f1,cross(f2,zz));
  assert(det>0&&newDet>0);
  if(ids.some(i=>changed[i])){affectedTriangles++;minOrientation=Math.min(minOrientation,dot(area,newArea));assert(dot(area,newArea)>0,'Float32 output face inversion');}
  const dual=[cross(e2,z).map(x=>x/det),cross(z,e1).map(x=>x/det),cross(e1,e2).map(x=>x/det)];
  const nextDual=[cross(f2,zz).map(x=>x/newDet),cross(zz,f1).map(x=>x/newDet),cross(f1,f2).map(x=>x/newDet)];
  for(const i of ids){if(!affectedVertex[i])continue;
    const nn=normal(i),tt=tangent(i),nc=[dot(e1,nn),dot(e2,nn),dot(z,nn)],tc=dual.map(row=>dot(row,tt));
    const transportedN=unit([0,1,2].map(k=>nc.reduce((s,v,r)=>s+v*nextDual[r][k],0)));
    const transportedT=unit([0,1,2].map(k=>tc[0]*f1[k]+tc[1]*f2[k]+tc[2]*zz[k]));
    for(let k=0;k<3;k++){sumN[i*3+k]+=weight*transportedN[k];sumT[i*3+k]+=weight*transportedT[k];}sumWeight[i]+=weight;
  }
}
for(let i=0;i<n;i++){if(!affectedVertex[i]||!sumWeight[i])continue;
  const nn=unit(point(sumN,i)),tt=point(sumT,i),tn=dot(tt,nn),orthogonal=unit(tt.map((x,k)=>x-tn*nn[k]));
  for(let k=0;k<3;k++){normals.writeInt16LE(Math.round(Math.max(-1,Math.min(1,nn[k]))*32767),i*8+k*2);tangents.writeFloatLE(orthogonal[k],i*16+k*4);}
  // Fourth tangent component and NORMAL's two padding bytes remain exact.
}
const originalBin=readAt(g.fd,fs.statSync(source).size-g.binOffset,g.binOffset),chunks=[originalBin];let offset=originalBin.length;
const changes=[];
for(const [semantic,payload,stride] of [['POSITION',positionBytes,12],['NORMAL',normals,8],['TANGENT',tangents,16],
  ['JOINTS_0',fs.readFileSync(path.join(fitDirectory,'jointsAfter.bin')),4],
  ['WEIGHTS_0',fs.readFileSync(path.join(fitDirectory,'weightsAfter.bin')),8]]){
  const ai=prim.attributes[semantic],previous=await bytes(ai),rows=[];
  for(let i=0;i<n;i++)if(!previous.subarray(i*stride,(i+1)*stride).equals(payload.subarray(i*stride,(i+1)*stride)))rows.push(i);
  if(!rows.length)continue;
  assert.equal(offset%4,0);
  const view={buffer:0,byteOffset:offset,byteLength:payload.length,target:34962};if(semantic==='NORMAL')view.byteStride=8;
  j.accessors[ai].bufferView=j.bufferViews.length;j.bufferViews.push(view);chunks.push(payload);offset+=payload.length;
  if(semantic==='POSITION')for(const [key,fn] of [['min',Math.min],['max',Math.max]]){
    const extrema=[positions[0],positions[1],positions[2]];for(let i=0;i<n;i++)for(let k=0;k<3;k++)extrema[k]=fn(extrema[k],positions[i*3+k]);j.accessors[ai][key]=extrema;
  }
  changes.push({mesh:5,primitive:0,semantic,accessor:ai,count:n,type:j.accessors[ai].type,componentType:j.accessors[ai].componentType,
    normalized:j.accessors[ai].normalized??false,changedRows:rows.length,changedRowIDs:rows,
    beforeDecodedSHA256:sha(previous),afterDecodedSHA256:sha(payload),beforeMetadata:before.accessors[ai],afterMetadata:j.accessors[ai]});
}
assert(changes.some(r=>r.semantic==='POSITION'));
j.buffers[0].byteLength=offset;const json=Buffer.from(JSON.stringify(j)),jp=Buffer.alloc((json.length+3)&~3,0x20);json.copy(jp);
const headerGLB=Buffer.alloc(20);headerGLB.writeUInt32LE(0x46546c67,0);headerGLB.writeUInt32LE(2,4);headerGLB.writeUInt32LE(28+jp.length+offset,8);headerGLB.writeUInt32LE(jp.length,12);headerGLB.writeUInt32LE(0x4e4f534a,16);
const binHeader=Buffer.alloc(8);binHeader.writeUInt32LE(offset,0);binHeader.writeUInt32LE(0x004e4942,4);
fs.mkdirSync(out,{recursive:true});const candidate=path.join(out,'rider.glb');fs.writeFileSync(candidate,Buffer.concat([headerGLB,jp,binHeader,...chunks]));
const record=p=>({path:p,sha256:fileSha(p),bytes:fs.statSync(p).size});
const parity={schema:'selected-cuff-source-parity-v1',accepted:false,baseline:record(source),candidate:record(candidate),
  sourcePatch:{report:record(reportFile),patch:record(patch)},nativeRigAndAnimationJSONExact:true,protectedNativeAccessorBytesExact:true,
  materialsTexturesImagesJSONExact:true,originalBINPayloadPrefixExact:true,unchangedGloveAccessorBytesExact:true,allOtherAccessorBytesExact:true,
  nativeJSONRecordsExact:{},changedAccessors:changes,protectedAccessorStreamsExact:[],unchangedGloveAccessorStreamsExact:[],imagePayloadsExact:[],
  authoredSurfaceTransport:{method:'Incident source-area averaged per-face differential; normals inverse transpose; tangents forward and orthogonalized; original tangent handedness and packed normal padding preserved.',affectedTriangles,minPositiveAreaOrientationDot:minOrientation}};
for(const key of ['nodes','skins','scenes','animations','materials','textures','images','samplers']){assert.deepEqual(j[key],before[key]);parity.nativeJSONRecordsExact[key]={beforeSHA256:sha(JSON.stringify(before[key]??[])),afterSHA256:sha(JSON.stringify(j[key]??[])),exact:true};}
for(let ai=0;ai<before.accessors.length;ai++){if(changes.some(r=>r.accessor===ai))continue;
  const a=before.accessors[ai],hash=sha(await bytes(ai));parity.protectedAccessorStreamsExact.push({accessor:ai,count:a.count,type:a.type,componentType:a.componentType,normalized:a.normalized??false,beforeDecodedSHA256:hash,afterDecodedSHA256:hash,exact:true});}
for(const mesh of [2,3])for(const [primitive,part] of before.meshes[mesh].primitives.entries())for(const [semantic,accessor] of [...Object.entries(part.attributes),['indices',part.indices]]){
  const proof=parity.protectedAccessorStreamsExact.find(r=>r.accessor===accessor);assert(proof);parity.unchangedGloveAccessorStreamsExact.push({...proof,mesh,primitive,semantic});}
for(const [image,item] of before.images.entries()){const view=before.bufferViews[item.bufferView],hash=sha(readAt(g.fd,view.byteLength,g.binOffset+(view.byteOffset??0)));parity.imagePayloadsExact.push({image,bufferView:item.bufferView,bytes:view.byteLength,beforeSHA256:hash,afterSHA256:hash,exact:true});}
fs.closeSync(g.fd);
const parityFile=path.join(out,'parity.json');fs.writeFileSync(parityFile,JSON.stringify(parity,null,2)+'\n');
const {baselineJSON,candidateJSON,...verified}=await verifyParityFiles(parityFile,candidate);
fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify(verified,null,2)+'\n');
console.log(JSON.stringify({candidate:record(candidate),changed:changes.map(({semantic,accessor,changedRows})=>({semantic,accessor,changedRows})),independentParityVerified:verified.pass,accepted:false}));
