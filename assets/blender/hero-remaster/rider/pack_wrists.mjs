/** Pack repaired geometry, retaining the same seven semantic clips. */
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {pack} from '../../hero_art_pack.mjs';
const [input,out]=process.argv.slice(2);if(!out)throw new Error('pack_wrists raw-seven.glb output-packed.glb');
const b=fs.readFileSync(input),n=b.readUInt32LE(12),d=JSON.parse(b.subarray(20,20+n)),bin=b.subarray(28+n,28+n+b.readUInt32LE(20+n));
d.animations=d.animations.filter(a=>a.name!=='idle_breathe');
const used=new Set();
for(const m of d.meshes)for(const p of m.primitives){Object.values(p.attributes).forEach(i=>used.add(i));if(p.indices!=null)used.add(p.indices)}
for(const s of d.skins)used.add(s.inverseBindMatrices);
for(const a of d.animations)for(const s of a.samplers){used.add(s.input);used.add(s.output)}
const map=new Map([...used].sort((a,b)=>a-b).map((old,i)=>[old,i]));d.accessors=[...map.keys()].map(i=>d.accessors[i]);
for(const m of d.meshes)for(const p of m.primitives){for(const k of Object.keys(p.attributes))p.attributes[k]=map.get(p.attributes[k]);if(p.indices!=null)p.indices=map.get(p.indices)}
for(const s of d.skins)s.inverseBindMatrices=map.get(s.inverseBindMatrices);
for(const a of d.animations)for(const s of a.samplers){s.input=map.get(s.input);s.output=map.get(s.output)}
const views=new Set(d.accessors.map(a=>a.bufferView));d.images.forEach(i=>views.add(i.bufferView));const vm=new Map([...views].sort((a,b)=>a-b).map((old,i)=>[old,i]));d.bufferViews=[...vm.keys()].map(i=>d.bufferViews[i]);d.accessors.forEach(a=>a.bufferView=vm.get(a.bufferView));d.images.forEach(i=>i.bufferView=vm.get(i.bufferView));
const json=Buffer.from(JSON.stringify(d)),jp=Buffer.concat([json,Buffer.alloc(-json.length&3,32)]),bp=Buffer.concat([bin,Buffer.alloc(-bin.length&3)]),raw=Buffer.alloc(28+jp.length+bp.length);raw.writeUInt32LE(0x46546c67,0);raw.writeUInt32LE(2,4);raw.writeUInt32LE(raw.length,8);raw.writeUInt32LE(jp.length,12);raw.writeUInt32LE(0x4e4f534a,16);jp.copy(raw,20);raw.writeUInt32LE(bp.length,20+jp.length);raw.writeUInt32LE(0x004e4942,24+jp.length);bp.copy(raw,28+jp.length);
const six=input.replace(/\.glb$/, '-six.glb'),packed=six.replace(/\.glb$/,'-packed.glb');fs.writeFileSync(six,raw);await pack(six,packed,{stripSceneExtras:true});
const home=process.env.HOME,local=`${home}/projects/localai`,run=`${local}/runtime/unimate/runs/mps-seed42`,decoder=`${process.cwd()}/node_modules/three/examples/jsm/libs/meshopt_decoder.module.js`;
execFileSync(process.execPath,[`${local}/bin/unimate/merge_idle.mjs`,packed,`${run}/gt-animated.glb`,`${run}/constrained-animated.glb`,out,decoder],{stdio:'inherit'});
