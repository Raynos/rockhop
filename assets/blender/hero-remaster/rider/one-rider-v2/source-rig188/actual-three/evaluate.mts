/** Read-only stock Three witness gate. No renderer, model or exported asset. */
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import * as THREE from 'three';
import {loadRigAt} from '/Users/raynos/projects/games/rockhop/src/render/hero/gltfTestUtils';
import {createFixturePlayer} from '/Users/raynos/projects/games/rockhop/harness/hero-remaster/basic-pose-gate/protocol';
const base='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2';
const source=base+'/candidate-handoff170/hood-fixed185-187/rider.glb';
const fixturePath=base+'/basic-pose-gate158/fixture-v4-asymmetric-halfsteps.json';
const out='docs/evidence/hero-remaster/one-rider-v2/source-rig188/actual-three';
const hash=(p:string)=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const before=hash(source);assert.equal(before,'4eb597a9ff926fb5ce30854272d8391347c2e220829486136b1509e02faa947c');
assert.equal(hash(fixturePath),'78732965343f6eba40ae68ca99ffa949f6718910eb7b930b67d4a48d0083afab');
const bytes=fs.readFileSync(source),jl=bytes.readUInt32LE(12),doc=JSON.parse(bytes.subarray(20,20+jl).toString()),bin=bytes.subarray(28+jl);
function accessor(id:number):number[][] {
 const a=doc.accessors[id],width=({SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16}as any)[a.type];
 const sizes:any={5121:1,5123:2,5125:4,5126:4};assert(sizes[a.componentType]);assert(!a.normalized,'raw decoder uses only unnormalized source accessors');
 const read=(view:number,offset:number,count:number,w:number,type:number)=>{
  const v=doc.bufferViews[view],sz=sizes[type],stride=v.byteStride??w*sz,origin=(v.byteOffset??0)+offset;
  return Array.from({length:count},(_,i)=>Array.from({length:w},(_,k)=>{const p=origin+i*stride+k*sz;return type===5126?bin.readFloatLE(p):type===5125?bin.readUInt32LE(p):type===5123?bin.readUInt16LE(p):bin.readUInt8(p);}));
 };
 const result=a.bufferView===undefined?Array.from({length:a.count},()=>Array(width).fill(0)):read(a.bufferView,a.byteOffset??0,a.count,width,a.componentType);
 if(a.sparse){const s=a.sparse,ids=read(s.indices.bufferView,s.indices.byteOffset??0,s.count,1,s.indices.componentType),values=read(s.values.bufferView,s.values.byteOffset??0,s.count,width,a.componentType);for(let k=0;k<s.count;k++)result[ids[k]![0]!]=values[k]!;}
 return result;
}
const gltf=await loadRigAt(pathToFileURL(source),true),fixture=JSON.parse(fs.readFileSync(fixturePath,'utf8')),player=createFixturePlayer(gltf.scene,fixture);
assert.equal(fixture.frames.length,5404);assert.equal(player.meshes.length,5);
const parents=new Map<number,number>();doc.nodes.forEach((n:any,i:number)=>n.children?.forEach((c:number)=>parents.set(c,i)));
const cache=new Map<number,THREE.Matrix4>();function rawWorld(i:number):THREE.Matrix4 {if(cache.has(i))return cache.get(i)!;const n=doc.nodes[i];const local=n.matrix?new THREE.Matrix4().fromArray(n.matrix):new THREE.Matrix4().compose(new THREE.Vector3().fromArray(n.translation??[0,0,0]),new THREE.Quaternion().fromArray(n.rotation??[0,0,0,1]),new THREE.Vector3().fromArray(n.scale??[1,1,1]));const world=parents.has(i)?rawWorld(parents.get(i)!).clone().multiply(local):local;cache.set(i,world);return world;}
const rawRest=doc.skins[0].joints.map((i:number)=>rawWorld(i));let restParity=0;for(let j=0;j<19;j++)for(let k=0;k<16;k++)restParity=Math.max(restParity,Math.abs(rawRest[j].elements[k]-player.rest[j]!.elements[k]!));assert(restParity<1e-12);assert(doc.nodes.some((n:any)=>n.extras?.rockhopRiderSkinConditioned===1));const rawIB=accessor(doc.skins[0].inverseBindMatrices).map(v=>new THREE.Matrix4().fromArray(v));
const body=player.meshes.find(m=>m.geometry.getAttribute('position').count===22240)!;
const glove=player.meshes.find(m=>m.geometry.getAttribute('position').count===4021)!;assert(body&&glove);
const rawPrimitives=[doc.meshes[0].primitives[0],doc.meshes[0].primitives[1]],loaded=[body,glove];
const fields=rawPrimitives.map((p:any,i:number)=>{const mesh=loaded[i]!,positions=accessor(p.attributes.POSITION),joints=accessor(p.attributes.JOINTS_0),weights=accessor(p.attributes.WEIGHTS_0),morphs=p.targets.map((t:any)=>accessor(t.POSITION));let changed=0,maxChange=0;
 for(let v=0;v<positions.length;v++){
  const sum=weights[v]!.reduce((s,w)=>s+Math.abs(w),0);assert(sum>0);
  for(let k=0;k<3;k++)assert.equal(mesh.geometry.getAttribute('position').getComponent(v,k),positions[v]![k]);
  for(let k=0;k<4;k++){assert.equal(mesh.geometry.getAttribute('skinIndex').getComponent(v,k),joints[v]![k]);const predicted=Math.fround(weights[v]![k]!/sum),actual=mesh.geometry.getAttribute('skinWeight').getComponent(v,k);assert.equal(actual,predicted);changed+=actual!==weights[v]![k]?1:0;maxChange=Math.max(maxChange,Math.abs(actual-weights[v]![k]!));weights[v]![k]=actual;}
  for(let t=0;t<morphs.length;t++)for(let k=0;k<3;k++)assert.equal(mesh.geometry.morphAttributes.position[t]!.getComponent(v,k),morphs[t]![v]![k]);
 }
 return {mesh,positions,joints,weights,morphs,changedNormalizationLanes:changed,maximumNormalizationChange:maxChange};});
const witnesses=[{label:'left_inner_elbow_edge',field:0,ids:[2030,2172]},{label:'right_lateral_edge',field:0,ids:[18709,19053]},{label:'hip_edge',field:0,ids:[12346,12359]}];
let gi=0,gm=0;for(let i=0;i<fields[1]!.positions.length;i++)for(const morph of fields[1]!.morphs){const mag=Math.hypot(...morph[i]!);if(mag>gm){gm=mag;gi=i;}}
assert(gm>0);witnesses.push({label:'nonzero_grip_morph_witness',field:1,ids:[gi,gi]});
let maxParity=0,maxWorld=0,morphBefore=0;const trajectories:any[]=[],vector=new THREE.Vector3();
for(const frame of fixture.frames){const parity=player.apply(frame);maxWorld=Math.max(maxWorld,parity.maximumWorldMatrixError);const ideal=frame.deformationWorldColumnMajor.map((v:number[],i:number)=>new THREE.Matrix4().fromArray(v).multiply(rawRest[i]!).multiply(rawIB[i]!));
 for(const wit of witnesses){const a=fields[wit.field]!,actual:number[][]=[],independent:number[][]=[];
  for(const id of wit.ids){actual.push(a.mesh.localToWorld(a.mesh.getVertexPosition(id,vector)).toArray());const p=[...a.positions[id]!];
   for(let t=0;t<a.morphs.length;t++){const alpha=a.mesh.morphTargetInfluences?.[t]??0;for(let k=0;k<3;k++)p[k]!+=alpha*a.morphs[t]![id]![k]!;if(alpha&&Math.hypot(...a.morphs[t]![id]!)>0)morphBefore++;}
   const q=[0,0,0];for(let lane=0;lane<4;lane++){const w=a.weights[id]![lane]!;if(!w)continue;const e=ideal[a.joints[id]![lane]!]!.elements;for(let k=0;k<3;k++)q[k]!+=w*(e[k]!*p[0]!+e[k+4]!*p[1]!+e[k+8]!*p[2]!+e[k+12]!);}
   independent.push(q);const error=Math.hypot(...q.map((v,k)=>v-actual[actual.length-1]![k]!));maxParity=Math.max(maxParity,error);assert(error<1e-10,'independent raw affine parity');
  }
  const edge=actual[1]!.map((v,k)=>v-actual[0]![k]!);const restEdge=a.positions[wit.ids[1]!]!.map((v,k)=>v-a.positions[wit.ids[0]!]![k]!);const length=Math.hypot(...restEdge);
  trajectories.push({witness:wit.label,family:frame.family,frame:frame.frame,timeSeconds:frame.timeSeconds,actualWorldPositionsM:actual,independentPositionsM:independent,edgeLengthM:Math.hypot(...edge),restEdgeM:length,ratio:length?Math.hypot(...edge)/length:null,closedGrip:frame.closedGrip,gripSide:frame.gripSide??null});
 }
}
assert(morphBefore>0);assert.equal(hash(source),before);
const rows=witnesses.flatMap(wit=>fixture.families.map((family:string)=>{const rs=trajectories.filter(r=>r.witness===wit.label&&r.family===family),worst=rs.reduce((a,b)=>(a.ratio??0)>(b.ratio??0)?a:b);return {witness:wit.label,family,samples:rs.length,maximumRatio:worst.ratio,worstFrame:worst.frame};}));
const trajectoryRaw=Buffer.from(JSON.stringify(trajectories)+'\n');fs.writeFileSync(out+'/witness-trajectories.json.gz',gzipSync(trajectoryRaw,{level:9}));
const result={status:'ACTUAL_STOCK_THREE_WITNESSES_ONLY_NO_ART_ACCEPTANCE',source,sourceSHA256:before,fixture:fixturePath,fixtureSHA256:hash(fixturePath),recipeSHA256:hash(new URL(import.meta.url).pathname),loaderSHA256:hash('src/render/hero/gltfTestUtils.ts'),protocolSHA256:hash('harness/hero-remaster/basic-pose-gate/protocol.ts'),bones:player.bones.size,meshes:player.meshes.length,frames:fixture.frames.length,witnesses:witnesses.map(w=>({...w,sourceMorphPositionDeltas:fields[w.field]!.morphs.map(x=>w.ids.map(id=>x[id]))})),changedNormalizationLanes:fields.map(f=>({vertices:f.positions.length,lanes:f.changedNormalizationLanes,maximumChange:f.maximumNormalizationChange})),maximumActualVsIndependentAffineErrorM:maxParity,maximumWorldFixtureError:maxWorld,nonzeroMorphBeforeLBSApplications:morphBefore,rawDocumentRestVsLoaderMaxError:restParity,trajectoriesUncompressedSHA256:crypto.createHash('sha256').update(trajectoryRaw).digest('hex'),trajectoriesGzipSHA256:hash(out+'/witness-trajectories.json.gz'),rows,limits:['All5404 controlled fixture frames, only6body+1glove vertices, no full garment or intersections acceptance.','No renderer/GPU, textures omitted only in loader memory, source unchanged.','No bone/weight/geometry changes or production physics/controller test.','Explicit child-axis gameplay adaptation is outside this named-world fixture gate.','Known deep underarm construction web remains failed; this does not prescribe weights-only repair.']};
fs.writeFileSync(out+'/report.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({frames:result.frames,maxParity,maxWorld,morphBefore,normalization:result.changedNormalizationLanes,selected:rows.filter(r=>['overhead.L','overhead.R','sit','forward.L'].includes(r.family))}));
