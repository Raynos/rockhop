// New frozen GLB: zero explicit rest defaults, exact all-BIN preservation.
import fs from 'node:fs';import crypto from 'node:crypto';
const [source,out,master,controller,outController,evidence]=process.argv.slice(2),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
if(fs.existsSync(out))throw Error('Frozen zero-rest GLB exists');
const bytes=fs.readFileSync(source),n=bytes.readUInt32LE(12),original=JSON.parse(bytes.subarray(20,20+n)),doc=structuredClone(original),changed=[];
doc.meshes.forEach((m,i)=>{if(m.weights?.some(w=>w!==0)){changed.push({mesh:i,name:m.name,before:m.weights,after:m.weights.map(()=>0),primitives:m.primitives.length});m.weights=m.weights.map(()=>0);}});
doc.nodes.forEach((node,i)=>{if(node.weights?.some(w=>w!==0)){changed.push({node:i,name:node.name,before:node.weights,after:node.weights.map(()=>0)});node.weights=node.weights.map(()=>0);}});
if(changed.length!==1||changed[0].before.length!==3||changed[0].primitives!==2)throw Error('Expected only combined hoodie defaults');
const root=doc.scenes[doc.scene??0].nodes[0];doc.nodes[root].extras.rockhopAppearanceCandidate='unaccepted appearance05 zero-rest defaults';
const encoded=Buffer.from(JSON.stringify(doc)),json=Buffer.concat([encoded,Buffer.alloc((4-encoded.length%4)%4,32)]),bin=bytes.subarray(20+n),result=Buffer.alloc(20+json.length+bin.length);
bytes.copy(result,0,0,12);result.writeUInt32LE(result.length,8);result.writeUInt32LE(json.length,12);result.writeUInt32LE(0x4e4f534a,16);json.copy(result,20);bin.copy(result,20+json.length);fs.writeFileSync(out,result,{flag:'wx'});
if(!bin.equals(result.subarray(20+json.length)))throw Error('BIN changed');
const c=JSON.parse(fs.readFileSync(controller));c.candidateMasterSHA256=sha(fs.readFileSync(master));c.candidateGLBSHA256=sha(result);c.status='UNACCEPTED appearance05 zero-rest defaults; same geometry/UV/skin/PBR/controllers as04';c.parentAppearanceGLBSHA256=sha(bytes);delete c.nativeQuantizedExportSHA256;fs.writeFileSync(outController,JSON.stringify(c,null,2)+'\n');
const report={status:'UNACCEPTED05 default-only GLB successor, all BIN bytes identical04',sourceGLBSHA256:sha(bytes),candidateGLBSHA256:sha(result),candidateMasterSHA256:c.candidateMasterSHA256,recipeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),changed,allBINBytesIdentical:true,BINSHA256:sha(bin),metadata:'Root candidate label changed, conditioning declaration retained',limits:['Native/export defaults0 must pass actual loader rest and controller checks independently.','No new geometry/UV/images/indices/morph vectors/51bind or art acceptance; raw protected NORMAL bytes retained.']};fs.writeFileSync(evidence,JSON.stringify(report,null,2)+'\n');console.log('ZERO_REST_EXPORT_READY',report.candidateGLBSHA256);
