/** Header-only coordinate audit; does not decode geometry or allocate textures. */
import fs from 'node:fs';
import {Vector3,Quaternion,Matrix4,Object3D} from 'three';
const V=a=>new Vector3().fromArray(a),Q=()=>new Quaternion(),I=()=>new Matrix4();
const f=fs.openSync('harness/out/rider-rebuild/download-opt01/textures01/composition01/rider.glb','r'),header=Buffer.alloc(20);fs.readSync(f,header,0,20,0);const json=Buffer.alloc(header.readUInt32LE(12));fs.readSync(f,json,0,json.length,20);fs.closeSync(f);const d=JSON.parse(json);
const nodes=d.nodes.map(n=>{const o=new Object3D();o.name=n.name;o.position.fromArray(n.translation??[0,0,0]);o.quaternion.fromArray(n.rotation??[0,0,0,1]);o.scale.fromArray(n.scale??[1,1,1]);return o;});d.nodes.forEach((n,i)=>{for(const child of n.children??[])nodes[i].add(nodes[child]);});const root=new Object3D();for(const i of d.scenes[d.scene??0].nodes)root.add(nodes[i]);root.updateMatrixWorld(true);const bone=name=>nodes.find(n=>n.name===name),inverse=Object.fromEntries(nodes.map(n=>[n.name,n.matrixWorld.clone().invert()]));

const {prepareControls}=await import('./thumb-opposition-plane.mjs');const meta=JSON.parse(fs.readFileSync('harness/out/rider-rebuild/download-opt01/delivery01/rider-contract.json')),P=name=>bone(name).getWorldPosition(new Vector3()),result={accepted:false,scope:'GLB JSON header/native transforms only; no geometry or textures decoded',sides:{}};for(const side of ['left','right'])result.sides[side]=prepareControls({side,hand:meta.specification.hands[side],meta,bone,P,V,Q});console.log(JSON.stringify(result,null,2));
