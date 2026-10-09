/** Offline selected75 grip-profile authoring; original asset/rest untouched.
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
    assert(!a.sparse);const [method,width,denom]={5120:['getInt8',1,127],5122:['getInt16',2,32767],5121:['getUint8',1,255],5123:['getUint16',2,65535],5125:['getUint32',4,4294967295],5126:['getFloat32',4,1]}[a.componentType];
    return {count:a.count,get:(row,k=0)=>Math.max(a.normalized?-1:-Infinity,dv[method]((a.byteOffset??0)+row*(b.byteStride??width*components)+k*width,true)/(a.normalized?denom:1)),row(row){return Array.from({length:components},(_,k)=>this.get(row,k));}};
  };
  function walk(i,parent=I()) {const n=d.nodes[i], m=n.matrix?I().fromArray(n.matrix):I().compose(V(n.translation??[0,0,0]),new Quaternion().fromArray(n.rotation??[0,0,0,1]),V(n.scale??[1,1,1]));world[i]=parent.clone().multiply(m);for(const c of n.children??[])walk(c,world[i]);}
  for(const i of d.scenes[d.scene??0].nodes)walk(i);
  const node = name => {const i=d.nodes.findIndex(n=>n.name===name);assert(i>=0,name);return {i,n:d.nodes[i],world:world[i],point:new Vector3().setFromMatrixPosition(world[i])};};
  return {d,read,node,sha256:sha(bytes),file};
}
const output=process.argv[2];assert(output,'Fresh output directory');fs.mkdirSync(output,{recursive:true});assert(!fs.existsSync(output+'/report.json'));
const sourcePath='harness/out/rider-rebuild/download-opt01/textures01/composition01/rider.glb',source=load(sourcePath),d=source.d,meta=JSON.parse(fs.readFileSync('harness/out/rider-rebuild/download-opt01/delivery01/rider-contract.json'));assert(source.sha256===meta.glbSHA256);
const nodes=d.nodes.map(n=>{const o=new Object3D();o.name=n.name;o.position.fromArray(n.translation??[0,0,0]);o.quaternion.fromArray(n.rotation??[0,0,0,1]);o.scale.fromArray(n.scale??[1,1,1]);return o;});d.nodes.forEach((n,i)=>{for(const c of n.children??[])nodes[i].add(nodes[c]);});const root=new Object3D();root.quaternion.fromArray(meta.driver.assetToBikeQuaternionXYZW);for(const i of d.scenes[d.scene??0].nodes)root.add(nodes[i]);root.updateMatrixWorld(true);
const bone=name=>nodes.find(n=>n.name===name),P=name=>bone(name).getWorldPosition(new Vector3()),rest=nodes.map(n=>({p:n.position.clone(),q:n.quaternion.clone(),s:n.scale.clone()}));
const reset=()=>{nodes.forEach((n,i)=>{n.position.copy(rest[i].p);n.quaternion.copy(rest[i].q);n.scale.copy(rest[i].s);});root.updateMatrixWorld(true);};
const basis=(f,n)=>{const x=f.clone().normalize(),y=n.clone().addScaledVector(x,-n.dot(x)).normalize();assert(x.lengthSq()>.99);return I().makeBasis(x,y,new Vector3().crossVectors(x,y));};
const history=JSON.parse(fs.readFileSync('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/bike-grip-surface02/report.json'));
const bikes=history.results.map(r=>{const g=load('public/models/'+r.asset);assert(g.sha256===r.sourceSHA256);return {receipt:r,shift:g.node('attach_frame_origin').point};});
for(const g of bikes[0].receipt.grips){const counterpart=bikes[1].receipt.grips.find(v=>v.side===g.side);assert.deepEqual(g.sourceMeshSurface,counterpart.sourceMeshSurface,'Both authored bike grips have identical exact source surface');assert.deepEqual(bikes[0].shift.toArray(),bikes[1].shift.toArray(),'Same attach-frame canonical shift');}
const report={accepted:false,construction:'Explicit source-geometric contact construction; no weighted coordinate-descent',source:{path:sourcePath,sha256:source.sha256},recipeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),sides:[],limits:['Offline candidate only. No played lean, wrist/elbow or device acceptance.','Current source geometry, selected materials/textures, native rest, shared75skin and inverse binds remain immutable.','The exact outer palmar triangle retains its actual blended MCP/hand/metacarpal fields; point/normal are re-registered after each candidate finger pose.','No anatomical or played acceptance follows from source geometry measurements.']};
const profile={accepted:false,schema:'rockhop-selected-grip-profile-v2',sourceSHA256:source.sha256,sourceContractSHA256:sha(fs.readFileSync('harness/out/rider-rebuild/download-opt01/delivery01/rider-contract.json')),bikes:bikes.map(b=>({asset:b.receipt.asset,sha256:b.receipt.sourceSHA256})),hands:{}};
for(const side of ['left','right']){
 reset();const hand=meta.specification.hands[side],w=bone(hand.wristJointId),palm=bone(hand.socketNodeName),w0=w.matrixWorld.clone(),socket=w0.clone().invert().multiply(palm.matrixWorld);
 const controlDerivation=process.argv[3]?(await import(new URL(process.argv[3],import.meta.url))).prepareControls?.({side,hand,meta,bone,P,V,I,Q,root}):null;
 const f=P(hand.forwardJointId).sub(P(hand.wristJointId)).normalize(),r=P(hand.radialJointId).sub(P(hand.ulnarJointId));r.addScaledVector(f,-r.dot(f)).normalize();const n=new Vector3().crossVectors(f,r).multiplyScalar(hand.normalSign).normalize();
 const anatomicalForwardInWrist=f.clone().transformDirection(w0.clone().invert()),anatomicalNormalInWrist=n.clone().transformDirection(w0.clone().invert()),referenceForward=V([1,-.25,0]).normalize(),referenceNormal=V([-.25,-1,0]).normalize();
 const align=Q().setFromRotationMatrix(basis(referenceForward,referenceNormal).multiply(basis(f,n).invert())),socketQ=align.clone().multiply(w.getWorldQuaternion(Q())).multiply(Q().setFromRotationMatrix(socket)).normalize(),grip=V([.27,.78,meta.driver.sideZ[side]*.33]),target=I().compose(grip,socketQ,V([1,1,1])).multiply(socket.clone().invert());
 const place=matrix=>{const q=Q().setFromRotationMatrix(matrix).normalize(),p=new Vector3().setFromMatrixPosition(matrix),parentQ=w.parent.getWorldQuaternion(Q()).normalize();w.position.copy(w.parent.worldToLocal(p));w.quaternion.copy(parentQ.invert().multiply(q));root.updateMatrixWorld(true);};place(target);
 const gn=source.node('ActualSelectedGlove.'+(side==='left'?'L':'R')),prim=d.meshes[gn.n.mesh].primitives[0],a=prim.attributes,pos=source.read(a.POSITION),normal=source.read(a.NORMAL),j=source.read(a.JOINTS_0),wt=source.read(a.WEIGHTS_0),idx=source.read(prim.indices),skin=d.skins[gn.n.skin],ibm=source.read(skin.inverseBindMatrices),ibms=skin.joints.map((_,i)=>I().fromArray(ibm.row(i))),names=skin.joints.map(i=>d.nodes[i].name);
 const sourceRows=Array.from({length:pos.count},(_,i)=>({p:V(pos.row(i)),n:V(normal.row(i)),fields:Array.from({length:4},(_,k)=>({joint:j.get(i,k),weight:wt.get(i,k)})).filter(f=>f.weight>0)}));
 const matrices=()=>skin.joints.map((node,i)=>nodes[node].matrixWorld.clone().multiply(ibms[i]));
 const skinned=(row,m)=>{const p=new Vector3(),n=new Vector3();for(const field of row.fields){p.addScaledVector(row.p.clone().applyMatrix4(m[field.joint]),field.weight);n.addScaledVector(row.n.clone().transformDirection(m[field.joint]),field.weight);}return {p,n:n.normalize()};};
 let m=matrices(),positions=new Float64Array(pos.count*3);sourceRows.forEach((row,i)=>positions.set(skinned(row,m).p.toArray(),i*3));const point=i=>new Vector3().fromArray(positions,i*3);
 const rigid=new Set([hand.wristJointId,...names.filter(name=>name.startsWith('DEF-palm.')&&name.endsWith(side==='left'?'.L':'.R'))]),rigidRow=row=>row.fields.every(f=>rigid.has(names[f.joint]));
 const posedAnatomicalForward=anatomicalForwardInWrist.clone().applyQuaternion(w.getWorldQuaternion(Q())),posedAnatomicalNormal=anatomicalNormalInWrist.clone().applyQuaternion(w.getWorldQuaternion(Q())),palmarProbeOrigin=P(hand.forwardJointId).addScaledVector(posedAnatomicalForward,-.010);let pad=null;for(const offset of [[0,0,0]]){const ray=new Ray(palmarProbeOrigin.clone().add(V(offset)),posedAnatomicalNormal);for(let i=0;i<idx.count;i+=3){const ids=[idx.get(i),idx.get(i+1),idx.get(i+2)];if(!ids.every(id=>sourceRows[id].fields.every(f=>names[f.joint]===hand.wristJointId||names[f.joint].startsWith('DEF-palm.')||Object.values(hand.digits).flat().includes(names[f.joint]))))continue;const t=new Triangle(...ids.map(point)),p=ray.intersectTriangle(t.a,t.b,t.c,false,new Vector3());if(!p)continue;const normal=t.getNormal(new Vector3());if(normal.dot(posedAnatomicalNormal)<.5)continue;const distance=p.distanceTo(ray.origin);if(!pad||distance<pad.distance)pad={point:p,normal,distance,triangle:i/3,rows:ids,barycentric:t.getBarycoord(p,new Vector3()).toArray()};}}
 if(!pad){const raw=[];for(const offset of [[0,0,0]]){const ray=new Ray(grip.clone().add(V(offset)),V([0,-1,0]));const hits=[];for(let i=0;i<idx.count;i+=3){const ids=[idx.get(i),idx.get(i+1),idx.get(i+2)],t=new Triangle(...ids.map(point)),p=ray.intersectTriangle(t.a,t.b,t.c,false,new Vector3());if(p)hits.push({distance:p.distanceTo(ray.origin),point:p.toArray(),normal:t.getNormal(new Vector3()).toArray(),rows:ids,fields:ids.map(id=>sourceRows[id].fields.map(f=>({name:names[f.joint],weight:f.weight}))),rigid:ids.map(id=>rigidRow(sourceRows[id]))});}hits.sort((a,b)=>a.distance-b.distance);raw.push({offset,hits:hits.slice(0,4)});}fs.writeFileSync(output+'/palm-rejection.json',JSON.stringify({side,raw},null,2)+'\n');throw new Error('No actual palmar surface among the one declared centre ray; exact skin field diagnostics saved');}
 const patch=[];sourceRows.forEach((row,i)=>{const p=point(i);if(p.distanceTo(pad.point)>.012)return;const sample=skinned(row,m);if(sample.n.dot(pad.normal)>.7)patch.push(sample.n);});assert(patch.length>4);const patchN=patch.reduce((sum,v)=>sum.add(v),new Vector3()).normalize();
 const old=bikes[0].receipt.grips.find(g=>g.side===(meta.driver.sideZ[side]>0?'L':'R')),map=new Map(old.sourceMeshSurface.vertices.map(v=>[v.sourceVertex,V(v.point).sub(bikes[0].shift)]));
 const triangles=old.sourceMeshSurface.triangles.map(t=>new Triangle(...t.map(id=>map.get(id))));
 const ray=new Ray(grip,V([0,1,0])),barHits=triangles.map((t,i)=>{const p=ray.intersectTriangle(t.a,t.b,t.c,false,new Vector3());return p?{p,n:t.getNormal(new Vector3()),triangle:i}:null;}).filter(Boolean).sort((a,b)=>a.p.distanceTo(grip)-b.p.distanceTo(grip));assert(barHits.length);const bar=barHits[0];if(bar.n.y<0)bar.n.negate();
 let padInWrist=pad.point.clone().applyMatrix4(w.matrixWorld.clone().invert()),normalInWrist=patchN.clone().transformDirection(w.matrixWorld.clone().invert()),forwardInWrist=anatomicalForwardInWrist.clone();
 let newQ=Q().setFromRotationMatrix(basis(referenceForward,referenceNormal).multiply(basis(anatomicalForwardInWrist,anatomicalNormalInWrist).invert())).normalize(),newP=bar.p.clone().addScaledVector(bar.n,.0005).sub(padInWrist.clone().applyQuaternion(newQ)),wristMatrix=I().compose(newP,newQ,V([1,1,1]));place(wristMatrix);
 const conditionPad=()=>{const mm=matrices(),samples=pad.rows.map(id=>skinned(sourceRows[id],mm)),current=samples.reduce((sum,v,i)=>sum.addScaledVector(v.p,pad.barycentric[i]),new Vector3()),currentNormal=new Triangle(...samples.map(v=>v.p)).getNormal(new Vector3()),inv=w.matrixWorld.clone().invert();padInWrist=current.applyMatrix4(inv);normalInWrist.copy(currentNormal.transformDirection(inv));newQ.copy(Q().setFromRotationMatrix(basis(referenceForward,referenceNormal).multiply(basis(anatomicalForwardInWrist,anatomicalNormalInWrist).invert())).normalize());newP.copy(bar.p).addScaledVector(bar.n,.0005).sub(padInWrist.clone().applyQuaternion(newQ));place(I().compose(newP,newQ,V([1,1,1])));};
 conditionPad();
 const nearest=p=>{let best={distance:Infinity};for(let i=0;i<triangles.length;i++){const t=triangles[i],q=t.closestPointToPoint(p,new Vector3()),distance=p.distanceTo(q);if(distance<best.distance){let n=t.getNormal(new Vector3());const axisA=V(old.recipeAxis.a).sub(bikes[0].shift),axisU=V(old.recipeAxis.unit),centre=t.getMidpoint(new Vector3()),radial=centre.clone().sub(axisA);radial.addScaledVector(axisU,-radial.dot(axisU));if(n.dot(radial)<0)n.negate();best={distance,signed:Math.sign(p.clone().sub(q).dot(n)) * distance,q,n,triangle:i};}}return best;};
 const allIds=Object.values(hand.digits).flat(),handOwned=row=>row.fields.every(f=>rigid.has(names[f.joint])||allIds.includes(names[f.joint]));
 const dominant=row=>names[row.fields.reduce((a,b)=>a.weight>b.weight?a:b).joint];
 const groups=Object.fromEntries(allIds.map(id=>[id,[]]));
 for(let i=0;i<idx.count;i+=3){const ids=[idx.get(i),idx.get(i+1),idx.get(i+2)];
  const owners=[...new Set(ids.map(id=>dominant(sourceRows[id])))];
  for(const owner of owners)if(groups[owner])groups[owner].push({triangle:i/3,rows:ids});
 }
 // Pulp is labeled against its own shaft and positive flex plane, never the
 // whole-palm normal or the arbitrary closest row after posing.
 const labels={},mm=matrices();
 for(const [digit,chain]of Object.entries(hand.digits)){
  labels[digit]=[];
  for(const [k,id]of chain.entries()){
   const b=bone(id),restBone=meta.nativeRest.bones.find(v=>v.name===id),length=V(restBone.head).distanceTo(V(restBone.tail));
   const shaft=V([0,1,0]).applyQuaternion(b.getWorldQuaternion(Q())),hinge=V(meta.driver.digitFlex[side][id].axisLocal).applyQuaternion(b.getWorldQuaternion(Q())),pulpDirection=new Vector3().crossVectors(hinge,shaft).normalize();
   const origin=P(id).addScaledVector(shaft,length*(k===2?.65:.55)),ray=new Ray(origin,pulpDirection),hits=[];
   for(const t of groups[id]){const posed=t.rows.map(i=>skinned(sourceRows[i],mm).p),tri=new Triangle(...posed),p=ray.intersectTriangle(...posed,false,new Vector3());if(!p)continue;
    const normal=tri.getNormal(new Vector3());if(normal.dot(pulpDirection)<.5)continue;
    const bc=tri.getBarycoord(p,new Vector3()).toArray();hits.push({...t,point:p,normal,barycentric:bc,distance:p.distanceTo(origin)});
   }
   hits.sort((a,b)=>a.distance-b.distance);if(!hits.length&&digit==='thumb'&&k<2){labels[digit].push({id,segment:k,length,head:P(id).toArray(),shaft:shaft.toArray(),hinge:hinge.toArray(),pulpDirection:pulpDirection.toArray(),pulp:{unavailable:true,reason:'No outward own-segment triangle on nominal shaft-center ray in declared thumb/index plane; no thenar/proximal pulp label is invented'}});continue;}assert(hits.length,'No anatomically labeled pulp '+id);const hit=hits[0],inv=b.matrixWorld.clone().invert();
   const sourcePoint=hit.rows.reduce((v,row,i)=>v.addScaledVector(sourceRows[row].p,hit.barycentric[i]),new Vector3());
   labels[digit].push({id,segment:k,length,head:P(id).toArray(),shaft:shaft.toArray(),hinge:hinge.toArray(),pulpDirection:pulpDirection.toArray(),pulp:{triangle:hit.triangle,rows:hit.rows,barycentric:hit.barycentric,sourceRestGlb:sourcePoint.toArray(),sourceRestJoint:sourcePoint.clone().applyMatrix4(source.node(id).world.clone().invert()).toArray(),sourceRestNormalGlb:hit.rows.reduce((v,row,i)=>v.addScaledVector(sourceRows[row].n,hit.barycentric[i]),new Vector3()).normalize().toArray(),point:hit.point.toArray(),pointLocal:hit.point.clone().applyMatrix4(inv).toArray(),normalLocal:hit.normal.clone().transformDirection(inv).toArray(),normalDotBendDirection:hit.normal.dot(pulpDirection),thicknessM:hit.distance,regionRadiusM:.003}});
  }
 }
 const axisA=V(old.recipeAxis.a).sub(bikes[0].shift),axisU=V(old.recipeAxis.unit),centre=axisA.clone().addScaledVector(axisU,grip.clone().sub(axisA).dot(axisU));
 const describe={side,controlDerivation,wrist:newP.toArray(),anatomicalForwardInWrist:anatomicalForwardInWrist.toArray(),anatomicalNormalInWrist:anatomicalNormalInWrist.toArray(),bar:{axisA:axisA.toArray(),axisU:axisU.toArray(),centre:centre.toArray(),length:old.recipeAxis.lengthM},labels};
 if(process.argv[3])describe.constructionRecipeSHA256=sha(fs.readFileSync(new URL(process.argv[3],import.meta.url)));
 if(process.argv[3])describe.construction=await (await import(new URL(process.argv[3],import.meta.url))).construct({side,hand,meta,source,d,nodes,rest,root,bone,P,V,I,Q,w,place,matrices,skinned,sourceRows,names,idx,pos,handOwned,rigid,labels,nearest,triangles,axisA,axisU,centre,grip,pad,bar,newP,newQ,anatomicalForwardInWrist,anatomicalNormalInWrist,output});
 report.sides.push(describe);
 console.log(JSON.stringify({side,wrist:newP.toArray(),centre:centre.toArray(),digits:Object.fromEntries(Object.entries(labels).map(([digit,v])=>[digit,v.map(x=>({id:x.id,head:x.head,length:x.length,pulp:x.pulp.point,pulpThickness:x.pulp.thicknessM,pulpDot:x.pulp.normalDotBendDirection}))]))}));
}
fs.writeFileSync(output+'/report.json',JSON.stringify(report,null,2)+'\n');
