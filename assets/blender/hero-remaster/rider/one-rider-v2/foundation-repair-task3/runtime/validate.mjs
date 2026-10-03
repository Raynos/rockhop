import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';

// Use the installed production engine. No package installation or GPU is involved.
const threeRoot = process.env.TASK3_THREE_ROOT || '/Users/raynos/projects/games/rockhop/node_modules/three';
const T = await import(pathToFileURL(path.join(threeRoot, 'build/three.module.js')));
const { GLTFLoader } = await import(pathToFileURL(path.join(threeRoot, 'examples/jsm/loaders/GLTFLoader.js')));
const { MeshoptDecoder } = await import(pathToFileURL(path.join(threeRoot, 'examples/jsm/libs/meshopt_decoder.module.js')));
const here = path.dirname(fileURLToPath(import.meta.url));
const sha = buffer => createHash('sha256').update(buffer).digest('hex');
const args = process.argv.slice(2);
const input = args[0];
if (!input) throw new Error('Usage: node runtime/validate.mjs manifest.json [output.json] [--dump]');
const inputPath = path.resolve(input);
const baseDir = path.dirname(inputPath);
const manifest = JSON.parse(await readFile(inputPath, 'utf8'));
const output = args[1] && !args[1].startsWith('--') ? path.resolve(args[1]) : path.join(here, 'validation.json');
const dump = args.includes('--dump');
const tolerance = manifest.tolerance_m ?? 0.00002;
const failures = [];

function stripImages(original) {
  // Identical to production test strategy: change only in-memory materials/images.
  // The BIN chunk, geometry, animation, skin weights, and bind matrices stay byte-identical.
  const length = original.readUInt32LE(12);
  const doc = JSON.parse(original.subarray(20, 20 + length));
  for (const mesh of doc.meshes ?? []) for (const primitive of mesh.primitives) {
    delete primitive.material;
    if (primitive.extensions) delete primitive.extensions.KHR_materials_variants;
  }
  doc.materials = []; doc.textures = []; doc.images = [];
  if (doc.extensions) delete doc.extensions.KHR_materials_variants;
  const json = Buffer.from(JSON.stringify(doc));
  const padded = Buffer.concat([json, Buffer.alloc((-json.length) & 3, 32)]);
  const rest = original.subarray(20 + length);
  const result = Buffer.alloc(20 + padded.length + rest.length);
  original.copy(result, 0, 0, 12); result.writeUInt32LE(result.length, 8);
  result.writeUInt32LE(padded.length, 12); result.writeUInt32LE(0x4e4f534a, 16);
  padded.copy(result, 20); rest.copy(result, 20 + padded.length);
  return { doc, result };
}

function positions(mesh) {
  const count = mesh.geometry.getAttribute('position').count;
  const result = new Float64Array(count * 3), point = new T.Vector3();
  for (let i = 0; i < count; i++) {
    mesh.getVertexPosition(i, point).applyMatrix4(mesh.matrixWorld);
    point.toArray(result, i * 3);
  }
  return result;
}
const distance = (a, b, i) => Math.hypot(a[3*i]-b[3*i], a[3*i+1]-b[3*i+1], a[3*i+2]-b[3*i+2]);
function compare(a, b) {
  if (a.length !== b.length) throw new Error(`Reference length ${b.length} != decoded length ${a.length}`);
  let max = 0, squared = 0, worst = -1;
  for (let i = 0; i < a.length / 3; i++) {
    const d = distance(a,b,i); if(d>max){max=d;worst=i;} squared += d*d;
  }
  return { count:a.length/3, max_m:max, rms_m:Math.sqrt(squared/(a.length/3)), worst_vertex:worst, pass:max<=tolerance };
}
const quantile = (sorted,p) => sorted.length ? sorted[Math.floor((sorted.length-1)*p)] : null;
function deformation(mesh, rest, posed) {
  const index=mesh.geometry.index, count=index?.count ?? rest.length/3;
  const at=i=>index ? index.getX(i):i;
  const edges=new Set(), lengths=[], longLengths=[], areas=[];
  let invalid=0, collapsed=0, signedReversed=0;
  const vec=(arr,i)=>new T.Vector3().fromArray(arr,3*i);
  for(let i=0;i<count;i+=3){
    const ids=[at(i),at(i+1),at(i+2)];
    if(ids.length<3)continue;
    const before=ids.map(id=>vec(rest,id)),after=ids.map(id=>vec(posed,id));
    const cross0=before[1].clone().sub(before[0]).cross(before[2].clone().sub(before[0]));
    const cross1=after[1].clone().sub(after[0]).cross(after[2].clone().sub(after[0]));
    const a0=cross0.length();if(a0>1e-12){const ratio=cross1.length()/a0;areas.push(ratio);if(ratio<.1)collapsed++;if(cross0.dot(cross1)<0)signedReversed++;}
    for(let j=0;j<3;j++){
      const a=ids[j],b=ids[(j+1)%3],key=a<b?`${a},${b}`:`${b},${a}`;
      if(edges.has(key))continue;edges.add(key);
      const l0=vec(rest,a).distanceTo(vec(rest,b));
      if(l0>1e-9){const ratio=vec(posed,a).distanceTo(vec(posed,b))/l0;lengths.push(ratio);if(l0>=.002)longLengths.push(ratio);}
    }
  }
  for(const v of posed)if(!Number.isFinite(v))invalid++;
  lengths.sort((a,b)=>a-b);longLengths.sort((a,b)=>a-b);areas.sort((a,b)=>a-b);
  return { nonfinite_components:invalid, unique_index_edges:edges.size, edge_ratio:{min:lengths[0],p01:quantile(lengths,.01),p50:quantile(lengths,.5),p99:quantile(lengths,.99),max:lengths.at(-1)}, edge_ratio_rest_at_least_2mm:{count:longLengths.length,p01:quantile(longLengths,.01),p50:quantile(longLengths,.5),p99:quantile(longLengths,.99),max:longLengths.at(-1)}, triangle_area_ratio:{min:areas[0],p01:quantile(areas,.01),p50:quantile(areas,.5),p99:quantile(areas,.99),max:areas.at(-1)}, area_below_10pct:collapsed, world_normal_opposed_to_rest:signedReversed, note:'Area ratios compare indexed triangles. World normal opposition includes normal rigid rotations, and is not an intersection or inversion proof.' };
}
function meshRecord(gltf,mesh,i){
 const a=gltf.parser.associations.get(mesh)??{};
 return {mesh, id:`${a.meshes ?? 'unknown'}:${a.primitives ?? 0}:${i}`,name:mesh.name,node_index:a.nodes ?? null,mesh_index:a.meshes ?? null,primitive_index:a.primitives ?? 0};
}
function boneReport(mesh){
 const weights=mesh.geometry.getAttribute('skinWeight'),indices=mesh.geometry.getAttribute('skinIndex');
 let weightError=0,badIndices=0;
 for(let i=0;i<weights.count;i++){let sum=0;for(let k=0;k<4;k++){const w=weights.getComponent(i,k),j=indices.getComponent(i,k);sum+=w;if(w!==0&&(j<0||j>=mesh.skeleton.bones.length))badIndices++;}weightError=Math.max(weightError,Math.abs(1-sum));}
 return {bone_count:mesh.skeleton.bones.length,bone_names:mesh.skeleton.bones.map(b=>b.name),max_weight_sum_error:weightError,invalid_weighted_indices:badIndices,bind_matrix:mesh.bindMatrix.toArray(), bind_mode:mesh.bindMode};
}
function selectMesh(records,ref){
 const matches=records.filter(r=>ref.id!==undefined ? r.id===ref.id : ref.mesh_index!==undefined ? r.mesh_index===ref.mesh_index&&r.primitive_index===(ref.primitive_index??0) : r.name===ref.mesh);
 if(matches.length!==1)throw new Error(`Reference mesh selector must match once: ${JSON.stringify(ref)}, matched ${matches.length}`);
 return matches[0];
}
async function referenceData(ref){
 if(ref.positions)return Float64Array.from(ref.positions.flat());
 const bytes=await readFile(path.resolve(baseDir,ref.path));
 if(ref.format==='json')return Float64Array.from(JSON.parse(bytes).flat());
 if(ref.format!=='float32le'&&ref.format!=='float64le')throw new Error('Reference format must be json, float32le, or float64le');
 const stride=ref.format==='float32le'?4:8, arr=new Float64Array(bytes.length/stride);
 for(let i=0;i<arr.length;i++)arr[i]=stride===4?bytes.readFloatLE(i*4):bytes.readDoubleLE(i*8);
 return arr;
}

const report={date:new Date().toISOString(),engine:{revision:T.REVISION,three_root:threeRoot,node:process.version},method:'Actual GLTFLoader + AnimationMixer + SkinnedMesh.getVertexPosition in Node, CPU only. Texture references removed only in memory; no material/render assertion.',tolerance_m:tolerance,variants:[],limitations:['CPU skinning agrees with standard weighted-matrix shader formula; no GPU render or DQ claim.','Triangle area and edge ratios are proxies, not closed-mesh volume or self-intersection measurements.','Parent-generated independent world-space expectations are required for cross-tool equivalence; otherwise parity remains unmeasured.']};
for(const inputVariant of manifest.variants){
 const variant=typeof inputVariant==='string'?{id:path.basename(inputVariant,'.glb'),path:inputVariant}:inputVariant;
 const source=path.resolve(baseDir,variant.path),original=await readFile(source),{doc,result}=stripImages(original);
 if(variant.sha256_reference_source&&variant.sha256_reference_source!==sha(original))failures.push(`${variant.id}: GLB changed after references were generated; regenerate references`);
 const gltf=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(result.buffer.slice(result.byteOffset,result.byteOffset+result.byteLength),'');
 gltf.scene.updateMatrixWorld(true);
 const records=[];gltf.scene.traverse(o=>{if(o.isSkinnedMesh)records.push(meshRecord(gltf,o,records.length));});
 if(!records.length)throw new Error(`No skinned mesh decoded for ${variant.id}`);
 const rests=new Map(records.map(r=>[r.id,positions(r.mesh)]));
 const vreport={id:variant.id,path:source,sha256:sha(original),raw_skin_joint_counts:(doc.skins??[]).map(s=>s.joints.length),available_clips:gltf.animations.map(c=>({name:c.name,duration_s:c.duration})),ignored_extra_joint_weight_sets:(doc.meshes??[]).flatMap((m,mi)=>m.primitives.flatMap((p,pi)=>Object.keys(p.attributes).filter(k=>/^JOINTS_[1-9]|^WEIGHTS_[1-9]/.test(k)).map(k=>({mesh:mi,primitive:pi,attribute:k})))),meshes:records.map(({mesh,...r})=>({...r,vertices:mesh.geometry.getAttribute('position').count,...boneReport(mesh)})),clips:[]};
 if(vreport.ignored_extra_joint_weight_sets.length)failures.push(`${variant.id}: extra joint sets exceed installed standard skinning contract`);
 for(const spec of variant.clips??gltf.animations.map(c=>({name:c.name}))){
  const clip=gltf.animations.find(c=>c.name===(typeof spec==='string'?spec:spec.name));
  if(!clip)throw new Error(`Missing clip ${JSON.stringify(spec)} in ${variant.id}`);
  const keyTimes=[...new Set(clip.tracks.flatMap(t=>Array.from(t.times)))].sort((a,b)=>a-b);
  const mandatory=[0,clip.duration,clip.duration*.137,clip.duration*.371,clip.duration*.613,clip.duration*.887];
  const requested=typeof spec==='string'?[]:(spec.times??[]);
  const times=[...new Set([...mandatory,...keyTimes,...requested,...(variant.expected??[]).filter(r=>r.clip===clip.name).map(r=>r.time)])].sort((a,b)=>a-b);
  const mixer=new T.AnimationMixer(gltf.scene),action=mixer.clipAction(clip);
  action.setLoop(T.LoopOnce,1);action.clampWhenFinished=true;
  const creport={name:clip.name,duration_s:clip.duration,track_count:clip.tracks.length,key_times_s:keyTimes,sample_count:times.length,samples:[]};
  for(const time of times){
   mixer.stopAllAction();action.reset().play();mixer.setTime(time);gltf.scene.updateMatrixWorld(true);records.forEach(r=>r.mesh.skeleton.update());
   const sample={time_s:time,kind:time===0?'start':Math.abs(time-clip.duration)<1e-7?'true_endpoint':keyTimes.some(k=>Math.abs(k-time)<1e-7)?'key':'interpolation_holdout',action_time_s:action.time,action_paused:action.paused,joints:records[0].mesh.skeleton.bones.map(b=>({name:b.name,world_position_m:b.getWorldPosition(new T.Vector3()).toArray(),local_scale:b.scale.toArray()})),meshes:[]};
   for(const record of records){
    const posed=positions(record.mesh),mreport={id:record.id,...deformation(record.mesh,rests.get(record.id),posed)};
    if(dump){const filename=`${variant.id}-${clip.name.replace(/[^\w-]/g,'_')}-${time.toFixed(7)}-${record.id.replace(/:/g,'_')}.f32`;await mkdir(path.join(here,'samples'),{recursive:true});const bytes=Buffer.alloc(posed.length*4);posed.forEach((v,i)=>bytes.writeFloatLE(v,i*4));await writeFile(path.join(here,'samples',filename),bytes);mreport.dump_path=path.join(here,'samples',filename);}
    sample.meshes.push(mreport);
   }
   for(const ref of variant.expected??[]){
    if(ref.clip!==clip.name||Math.abs(ref.time-time)>1e-6)continue;
    const record=selectMesh(records,ref),all=positions(record.mesh),actual=ref.vertex_indices?Float64Array.from(ref.vertex_indices.flatMap(i=>Array.from(all.slice(i*3,i*3+3)))):all;
    const parity={...compare(actual,await referenceData(ref)),reference_origin:ref.reference_origin??'independent parent reference'};sample.meshes.find(m=>m.id===record.id).parity=parity;
    if(!parity.pass)failures.push(`${variant.id}/${clip.name}/${time}/${record.id}: parity max ${parity.max_m}m exceeds ${tolerance}m`);
   }
   if(sample.meshes.some(m=>m.nonfinite_components))failures.push(`${variant.id}/${clip.name}/${time}: nonfinite vertices`);
   if(Math.abs(time-clip.duration)<1e-7&&Math.abs(action.time-clip.duration)>1e-7)failures.push(`${variant.id}/${clip.name}: endpoint incorrectly wrapped`);
   creport.samples.push(sample);
  }
  mixer.stopAllAction();mixer.uncacheRoot(gltf.scene);vreport.clips.push(creport);
 }
 vreport.parity_status=(variant.expected?.length??0)>0?'measured':'unmeasured: independent expectations not supplied';
 const parityResults=vreport.clips.flatMap(c=>c.samples.flatMap(s=>s.meshes.filter(m=>m.parity).map(m=>m.parity)));
 vreport.parity_summary={primitive_arrays:parityResults.length,vertex_comparisons:parityResults.reduce((n,p)=>n+p.count,0),max_m:Math.max(0,...parityResults.map(p=>p.max_m)),failed_arrays:parityResults.filter(p=>!p.pass).length};
 report.variants.push(vreport);
}
report.failures=failures;report.structural_finite_endpoint_checks_pass=failures.length===0;report.parity_measured=report.variants.every(v=>v.parity_status==='measured');report.status=failures.length?'failed':'loader/finite/endpoints verified; appearance acceptance not asserted';
await writeFile(output,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({output,three_revision:T.REVISION,variants:report.variants.map(v=>({id:v.id,meshes:v.meshes.length,bones:v.raw_skin_joint_counts,clips:v.clips.map(c=>({name:c.name,samples:c.sample_count})),parity:v.parity_status,parity_summary:v.parity_summary})),failure_count:failures.length,first_failures:failures.slice(0,10)},null,2));
if(failures.length)process.exitCode=1;
