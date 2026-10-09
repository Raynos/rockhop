// Retire source UV seams; retain native field knots and branch boundaries.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {MeshoptSimplifier} from 'meshoptimizer/simplifier';
import {openGlb,fileSha,sha} from '../download-opt01/geometry01/glb.mjs';
const [intake,out]=process.argv.slice(2),meta=JSON.parse(fs.readFileSync(path.join(intake,'intake.json')));
assert.equal(meta.sha256,'127e316a8ff7910a4918b63f83e086e4e658062f102c73f17d0ee2f956750649');assert([2,3].includes(meta.meshIndex));
await MeshoptSimplifier.ready;assert(!fs.existsSync(out));fs.mkdirSync(out,{recursive:true});
function array(name,Type){const b=fs.readFileSync(path.join(intake,name+'.bin'));return new Type(b.buffer,b.byteOffset,b.byteLength/Type.BYTES_PER_ELEMENT);}
const pos=array('POSITION',Float32Array),joints=array('JOINTS_0',Uint8Array),weights=array('WEIGHTS_0',Float32Array),sourceIndices=array('indices',Uint32Array),native=array('_NATIVE_ID',Float32Array);
const g=openGlb(meta.source),names=g.json.skins[0].joints.map(i=>g.json.nodes[i].name),remap=MeshoptSimplifier.generatePositionRemap(pos,3),first=[],compact=new Uint32Array(remap.length);compact.fill(0xffffffff);
for(let v=0;v<remap.length;v++){
 const r=remap[v];if(compact[r]===0xffffffff){compact[r]=first.length;first.push(r);}
 compact[v]=compact[r];for(let k=0;k<4;k++){assert.equal(joints[v*4+k],joints[r*4+k]);assert.equal(weights[v*4+k],weights[r*4+k]);}
}
const p=new Float32Array(first.length*3),ji=new Uint8Array(first.length*4),w=new Float32Array(first.length*4),ids=new Float32Array(first.length),indices=new Uint32Array(sourceIndices.length),active=new Set();
for(let v=0;v<first.length;v++){const r=first[v];p.set(pos.subarray(r*3,r*3+3),v*3);ji.set(joints.subarray(r*4,r*4+4),v*4);w.set(weights.subarray(r*4,r*4+4),v*4);ids[v]=native[r];for(let k=0;k<4;k++)if(w[v*4+k]>0)active.add(ji[v*4+k]);}
for(let i=0;i<indices.length;i++)indices[i]=compact[sourceIndices[i]];
const activeIds=[...active].sort((a,b)=>a-b);assert(activeIds.length<=32);const field=new Float32Array(first.length*activeIds.length),branch=new Uint8Array(first.length),labels=['thumb','index','middle','ring','pinky'];
for(let v=0;v<first.length;v++)for(let k=0;k<4;k++){const j=ji[v*4+k],value=w[v*4+k];if(value<=0)continue;field[v*activeIds.length+activeIds.indexOf(j)]+=value;const m=names[j].match(/^DEF-(?:f_)?(thumb|index|middle|ring|pinky)\./);if(m)branch[v]|=1<<labels.indexOf(m[1]);}
const locks=new Uint8Array(first.length);let boundaryEdges=0;
for(let i=0;i<indices.length;i+=3)for(let k=0;k<3;k++){const a=indices[i+k],b=indices[i+(k+1)%3];if(branch[a]!==branch[b]){locks[a]=locks[b]=1;boundaryEdges++;}}
const [reduced,error]=MeshoptSimplifier.simplifyWithAttributes(indices,p,3,field,activeIds.length,activeIds.map(()=>1),locks,120000,.0002,['ErrorAbsolute','LockBorder','Regularize']);
const used=[...new Set(reduced)].sort((a,b)=>a-b),map=new Uint32Array(first.length);map.fill(0xffffffff);used.forEach((v,i)=>map[v]=i);
const finalIndices=Uint32Array.from(reduced,v=>map[v]),sourceRows=Uint32Array.from(used,v=>first[v]);
const attrs={POSITION:{a:p,width:3},JOINTS_0:{a:ji,width:4},WEIGHTS_0:{a:w,width:4},_NATIVE_ID:{a:ids,width:1}};
for(const [name,{a,width}] of Object.entries(attrs)){const b=new a.constructor(used.length*width);used.forEach((v,i)=>b.set(a.subarray(v*width,v*width+width),i*width));fs.writeFileSync(path.join(out,name+'.bin'),b);}
fs.writeFileSync(path.join(out,'indices.bin'),finalIndices);fs.writeFileSync(path.join(out,'source-row.u32'),sourceRows);
const report={accepted:false,sourceSHA256:meta.sha256,meshIndex:meta.meshIndex,sourceTriangles:indices.length/3,triangles:finalIndices.length/3,vertices:used.length,requestedTriangles:40000,absoluteAggregateErrorMeters:error,nativeVertexPositionsJointsWeightsExactOriginalRows:true,noInterpolatedOrDiscardedWeightMass:true,activeNativeJointIds:activeIds,activeNativeJointNames:activeIds.map(j=>names[j]),attributeWeights:activeIds.map(()=>1),protectedBranchBoundaryVertices:locks.reduce((a,b)=>a+b,0),protectedBoundaryDirectedEdges:boundaryEdges,flags:['ErrorAbsolute','LockBorder','Regularize'],sourceRowsSHA256:sha(sourceRows),limits:'Quadric error is not a hard surface/deformation bound. Original vertex fields are exact, triangle interiors and corrected grip require separate measured and played qualification.'};
fs.writeFileSync(path.join(out,'simplify.json'),JSON.stringify(report,null,2)+'\n');fs.closeSync(g.fd);console.log(JSON.stringify(report));
