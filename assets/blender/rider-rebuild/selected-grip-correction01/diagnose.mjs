/** Read-only exact selected75 glove pose against actual finite bike grip triangles.
 * No images/textures, rest/asset edits, or production changes. Results unaccepted.
 */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {Matrix4,Quaternion,Vector3,Object3D,Triangle,Ray} from 'three';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const V=a=>new Vector3().fromArray(a),I=()=>new Matrix4(),Q=()=>new Quaternion();
await MeshoptDecoder.ready;
function load(file) {
  const bytes=fs.readFileSync(file), length=bytes.readUInt32LE(12), d=JSON.parse(bytes.subarray(20,20+length));
  assert(bytes.toString('ascii',0,4)==='glTF'); const bin=bytes.subarray(28+length), cache=new Map(), world=[];
  const view = i => {
    if(cache.has(i))return cache.get(i);
    const b=d.bufferViews[i], e=b.extensions?.EXT_meshopt_compression; let raw;
    if(e){raw=new Uint8Array(e.count*e.byteStride);MeshoptDecoder.decodeGltfBuffer(raw,e.count,e.byteStride,bin.subarray(e.byteOffset,e.byteOffset+e.byteLength),e.mode,e.filter);}
    else {assert(b.buffer===0);raw=bin.subarray(b.byteOffset??0,(b.byteOffset??0)+b.byteLength);}
    const dv=new DataView(raw.buffer,raw.byteOffset,raw.byteLength);cache.set(i,dv);return dv;
  };
  const read = i => {
    const a=d.accessors[i], b=d.bufferViews[a.bufferView], dv=view(a.bufferView), components={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16}[a.type];
    assert(!a.sparse);const [method,width,denom]={5121:['getUint8',1,255],5123:['getUint16',2,65535],5125:['getUint32',4,4294967295],5126:['getFloat32',4,1]}[a.componentType];
    return {count:a.count,get:(row,k=0)=>dv[method]((a.byteOffset??0)+row*(b.byteStride??width*components)+k*width,true)/(a.normalized?denom:1),row(row){return Array.from({length:components},(_,k)=>this.get(row,k));}};
  };
  function walk(i,parent=I()) {const n=d.nodes[i], m=n.matrix?I().fromArray(n.matrix):I().compose(V(n.translation??[0,0,0]),new Quaternion().fromArray(n.rotation??[0,0,0,1]),V(n.scale??[1,1,1]));world[i]=parent.clone().multiply(m);for(const c of n.children??[])walk(c,world[i]);}
  for(const i of d.scenes[d.scene??0].nodes)walk(i);
  const node = name => {const i=d.nodes.findIndex(n=>n.name===name);assert(i>=0,name);return {i,n:d.nodes[i],world:world[i],point:new Vector3().setFromMatrixPosition(world[i])};};
  return {d,read,node,sha256:sha(bytes),file};
}
const sourcePath='harness/out/rider-rebuild/download-opt01/textures01/composition01/rider.glb';
const source=load(sourcePath),d=source.d;
const meta=JSON.parse(fs.readFileSync('harness/out/rider-rebuild/download-opt01/delivery01/rider-contract.json'));
assert(source.sha256===meta.glbSHA256);
const nodes=d.nodes.map(n=>{const o=new Object3D();o.name=n.name;o.position.fromArray(n.translation??[0,0,0]);o.quaternion.fromArray(n.rotation??[0,0,0,1]);o.scale.fromArray(n.scale??[1,1,1]);return o;});
d.nodes.forEach((n,i)=>{for(const c of n.children??[])nodes[i].add(nodes[c]);});
const root=new Object3D();root.quaternion.fromArray(meta.driver.assetToBikeQuaternionXYZW);for(const i of d.scenes[d.scene??0].nodes)root.add(nodes[i]);root.updateMatrixWorld(true);
const bone=name=>nodes.find(n=>n.name===name),P=name=>bone(name).getWorldPosition(new Vector3());
const basis=(f,n)=>{const x=f.clone().normalize(),y=n.clone().addScaledVector(x,-n.dot(x)).normalize();return I().makeBasis(x,y,new Vector3().crossVectors(x,y));};
const historical=JSON.parse(fs.readFileSync('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/bike-grip-surface02/report.json'));
const bikes=historical.results.map(r=>{const g=load('public/models/'+r.asset);assert(g.sha256===r.sourceSHA256);return {receipt:r,shift:g.node('attach_frame_origin').point};});
const report={accepted:false,source:{path:sourcePath,sha256:source.sha256},sides:[],limits:['CPU FOUR skin readback in exact currently loaded rest; this isolates wrist/digit pose and is not a played lean/contact acceptance.','Sampled vertex nearest distances every16rows; surface rays use every glove triangle.','Axis distances of joints diagnose articulation, never skin contact.','Finite bike triangles are SHA-matched archived actual geometry, no cylinder substitute.']};
const quantile=(a,q)=>{a.sort((x,y)=>x-y);return a[Math.min(a.length-1,Math.floor(q*a.length))];};
for(const side of ['left','right']){
 const hand=meta.specification.hands[side],w=bone(hand.wristJointId),palm=bone(hand.socketNodeName),socket=w.matrixWorld.clone().invert().multiply(palm.matrixWorld);
 const f=P(hand.forwardJointId).sub(P(hand.wristJointId)).normalize(),r=P(hand.radialJointId).sub(P(hand.ulnarJointId));r.addScaledVector(f,-r.dot(f)).normalize();const n=new Vector3().crossVectors(f,r).multiplyScalar(hand.normalSign).normalize();
 const align=Q().setFromRotationMatrix(basis(V([1,-.25,0]),V([0,-1,0])).multiply(basis(f,n).invert()));
 const socketQ=align.clone().multiply(w.getWorldQuaternion(Q())).multiply(Q().setFromRotationMatrix(socket)).normalize(),grip=V([.27,.78,meta.driver.sideZ[side]*.33]);
 const target=I().compose(grip,socketQ,V([1,1,1])).multiply(socket.clone().invert()),worldQ=Q().setFromRotationMatrix(target).normalize(),wp=new Vector3().setFromMatrixPosition(target),parentQ=w.parent.getWorldQuaternion(Q()).normalize();
 w.position.copy(w.parent.worldToLocal(wp.clone()));w.quaternion.copy(parentQ.invert().multiply(worldQ));w.updateMatrix();root.updateMatrixWorld(true);
 const result={side,restPalmNormalBike:n.toArray(),wristBike:wp.toArray(),socketBike:palm.getWorldPosition(new Vector3()).toArray(),digits:{},bikes:[]};
 for(const [name,chain]of Object.entries(hand.digits)){for(const id of chain){const flex=meta.driver.digitFlex[side][id];bone(id).quaternion.multiply(Q().setFromAxisAngle(V(flex.axisLocal),flex.maxRadians));}root.updateMatrixWorld(true);const points=chain.map(id=>P(id).toArray());result.digits[name]={points,radialFromAxisM:points.map(p=>Math.hypot(p[0]-grip.x,p[1]-grip.y))};}
 const gn=source.node('ActualSelectedGlove.'+(side==='left'?'L':'R')),prim=d.meshes[gn.n.mesh].primitives[0],a=prim.attributes,pos=source.read(a.POSITION),j=source.read(a.JOINTS_0),wt=source.read(a.WEIGHTS_0),idx=source.read(prim.indices),skin=d.skins[gn.n.skin],ibm=source.read(skin.inverseBindMatrices);
 const matrices=skin.joints.map((node,i)=>nodes[node].matrixWorld.clone().multiply(I().fromArray(ibm.row(i))));
 const positions=new Float64Array(pos.count*3),dominant=[],counts={};let missing=0;
 for(let i=0;i<pos.count;i++){const p=V(pos.row(i)),out=new Vector3();let strongest=-1,name='';for(let k=0;k<4;k++){const weight=wt.get(i,k);if(weight<=0)continue;const joint=j.get(i,k);out.addScaledVector(p.clone().applyMatrix4(matrices[joint]),weight);if(weight>strongest){strongest=weight;name=d.nodes[skin.joints[joint]].name;}counts[d.nodes[skin.joints[joint]].name]=(counts[d.nodes[skin.joints[joint]].name]??0)+1;}positions.set(out.toArray(),i*3);dominant.push(name);}
 result.positiveInfluenceRows=Object.fromEntries(Object.values(hand.digits).flat().map(id=>[id,counts[id]??0]));
 const point=i=>new Vector3().fromArray(positions,i*3);
 for(const bike of bikes){const old=bike.receipt.grips.find(g=>g.side===(meta.driver.sideZ[side]>0?'L':'R')),surface=old.sourceMeshSurface,map=new Map(surface.vertices.map(v=>[v.sourceVertex,V(v.point).sub(bike.shift)])),triangles=surface.triangles.map(t=>new Triangle(...t.map(id=>map.get(id))));
 const grouped={};let min=Infinity,witness;for(let i=0;i<pos.count;i+=16){const p=point(i);let distance=Infinity,nearest=new Vector3();for(const t of triangles){const q=t.closestPointToPoint(p,new Vector3()),v=p.distanceTo(q);if(v<distance){distance=v;nearest=q;}}const name=dominant[i];(grouped[name]??=[]).push(distance);if(distance<min){min=distance;witness={row:i,point:p.toArray(),finitePoint:nearest.toArray(),dominant:name};}}
 const rays=[];for(const dir of [[0,1,0],[0,-1,0],[1,0,0],[-1,0,0]]){const direction=V(dir),ray=new Ray(grip,direction),hits=[];for(let i=0;i<idx.count;i+=3){const ids=[idx.get(i),idx.get(i+1),idx.get(i+2)],p=ray.intersectTriangle(point(ids[0]),point(ids[1]),point(ids[2]),false,new Vector3());if(p)hits.push({distanceM:p.distanceTo(grip),point:p.toArray(),triangle:i/3,rows:ids,dominant:ids.map(id=>dominant[id])});}hits.sort((a,b)=>a.distanceM-b.distanceM);rays.push({direction:dir,hits:hits.slice(0,4)});}
 result.bikes.push({asset:bike.receipt.asset,sha256:bike.receipt.sourceSHA256,closestSample:{distanceM:min,witness},digitSampleDistances:Object.fromEntries(Object.values(hand.digits).flat().map(id=>{const values=grouped[id]??[];return[id,{samples:values.length,minM:values.length?Math.min(...values):null,medianM:values.length?quantile(values,.5):null,p95M:values.length?quantile(values,.95):null}]})),rays});}
 report.sides.push(result);
}
fs.writeFileSync('docs/evidence/rider-rebuild/selected-grip-correction01/diagnosis01/report.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report.sides.map(s=>({side:s.side,wristBike:s.wristBike,digits:s.digits,coverage:s.positiveInfluenceRows,bikes:s.bikes.map(b=>({asset:b.asset,nearest:b.closestSample.distanceM,digitSampleDistances:b.digitSampleDistances,rays:b.rays}))}))));
