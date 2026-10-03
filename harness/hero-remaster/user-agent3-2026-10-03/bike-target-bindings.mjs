/** Played live bike target bindings. Proposed patches await parent selection. */
/* oxlint-disable eslint/no-undef, typescript/no-extraneous-class -- headless browser and silent AudioContext trap. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { decodeJSON, expandFrames } from '../../../src/core/replay.ts';
const [buildArg,inventoryFile,outArg]=process.argv.slice(2);assert(outArg&&!fs.existsSync(outArg));
const build=path.resolve(buildArg),out=path.resolve(outArg);fs.mkdirSync(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const inventoryBytes=fs.readFileSync(inventoryFile),inventory=JSON.parse(inventoryBytes);
const manifestBytes=fs.readFileSync(path.join(build,'hero-review.json')),manifest=JSON.parse(manifestBytes);
assert.equal(inventory.candidateSHA256,manifest.models.find(m=>m.logical==='models/rider-street-mustard.glb').sha256);
const recordingFile='docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/split-fixtures01-inputs/recordings/riding-poses-lean-transitions-rookie.json';
const recordingBytes=fs.readFileSync(recordingFile),recording=decodeJSON(recordingBytes.toString()),inputs=expandFrames(recording);
const report={status:'UNACCEPTED_TARGET_BINDING_REVIEW_PENDING',candidateSHA256:inventory.candidateSHA256,
  codeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),inventorySHA256:sha(inventoryBytes),manifestSHA256:sha(manifestBytes),recordingFile,recordingSHA256:sha(recordingBytes),
  errors:[],loaded:[],cases:[],clips:[],
  limits:['Proposed colored triangle regions need parent selection; no palm/sole/pelvis contact measurements or closed-volume claims.',
    'Bike geometry untouched; child overlays identify exact proposed target triangles. Rider hidden for bike-surface inspection, no rider acceptance.',
    'Full and bike LOD source/runtime triangle ordinals are independently mapped; no full-to-LOD rider ancestry is available.',
    'Recorded input first480ticks is replayed from tick1; it is a moving bike binding diagnostic, not complete clear qualification.']};
const server=await preview({configFile:false,root:process.cwd(),build:{outDir:build},preview:{host:'127.0.0.1',port:0},logLevel:'warn'});
const browser=await webkit.launch({headless:true}),context=await browser.newContext({viewport:{width:960,height:640},deviceScaleFactor:1});
await context.addInitScript(()=>{localStorage.setItem('rockhop.onboarded','1');window.__agent3AudioCount=0;for(const k of['AudioContext','webkitAudioContext'])window[k]=class{constructor(){window.__agent3AudioCount++;throw new Error('Silent target review');}};});
const page=await context.newPage(),responses=[];page.on('pageerror',e=>report.errors.push(e.message));
page.on('response',r=>{if(r.url().endsWith('.glb'))responses.push(r.body().then(b=>report.loaded.push({url:r.url(),sha256:sha(b),status:r.status()})));});
try{
  await page.goto(server.resolvedUrls.local[0]+'?harness=1&audio=0&sw=0&outfit=street-mustard&physics=v2&hz=120');
  await page.waitForFunction(()=>window.__rockhop?.ready,null,{timeout:120000});
  await page.waitForFunction(()=>!document.querySelector('#loader')||document.querySelector('#loader').getAttribute('data-done')==='1',null,{timeout:120000});
  await page.addStyleTag({content:'#ui,#ui *,.hud,.touch-controls{visibility:hidden!important} .agent3label{position:fixed;z-index:99999;color:white;background:#101820e8;padding:5px;font:13px monospace;white-space:pre;visibility:visible!important}'});
  for(const cls of['rookie','pro'])for(const tier of['high','low']){
    const logical=`models/bike-${cls}${tier==='low'?'-lod':''}.glb`,source=inventory.reports.find(r=>r.logical===logical);assert(source);
    await page.evaluate(async({cls,tier})=>{const t=window.__rockhop,r=window.__render;t.setBike(cls);await r.whenReady();await t.loadTrack('flat-test',1);t.setQuality(tier);await r.whenReady();t.skipCountdown();t.render(true);},{cls,tier});
    const binding=await page.evaluate(async source=>{
      const t=window.__rockhop,r=window.__render,d=r.debug,T=d.THREE,bike=d.bike;
      d.rider.scene.visible=false;for(const e of document.querySelectorAll('.agent3label'))e.remove();
      const label=document.createElement('div');label.className='agent3label';label.id='agent3-title';label.style.left='8px';label.style.top='8px';document.body.append(label);
      const locator=o=>{const path=[];let p=o;while(p!==bike.root){if(!p.parent)throw new Error('Target outside actual bike');path.unshift(p.parent.children.indexOf(p));p=p.parent;}return{childPath:path,name:o.name};};
      const targets=[],geometry=[];
      const digest=async payload=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(payload))),b=>b.toString(16).padStart(2,'0')).join('');
      for(const s of source.sources){
        const matches=bike.root.getObjectsByProperty('name',s.sourceNodeName).filter(o=>o.isMesh);if(matches.length!==1)throw new Error('Ambiguous bike target');const mesh=matches[0],p=mesh.geometry.attributes.position,idx=mesh.geometry.index;
        const payload=JSON.stringify({positions:Array.from({length:p.count},(_,i)=>[p.getX(i),p.getY(i),p.getZ(i)]),indices:Array.from({length:idx.count},(_,i)=>idx.getX(i))});
        const actual=await digest(payload);if(actual!==s.geometrySHA256)throw new Error('Runtime geometry differs from independently decoded source');
        const stablePayload=JSON.stringify({schema:'rockhop-rigid-target-v1',positions:Array.from({length:p.count},(_,i)=>[p.getX(i),p.getY(i),p.getZ(i)]),index:Array.from({length:idx.count},(_,i)=>idx.getX(i))});
        geometry.push({mesh:locator(mesh),sourceNode:s.nodeIndex,sourceMesh:s.sourceMeshIndex,sourcePrimitive:s.primitiveIndex,sourceGeometrySHA256:s.geometrySHA256,runtimeRigidSurfaceSHA256:await digest(stablePayload),sourceNodeMatrixWorld:s.sourceNodeMatrixWorld});
        const selections=s.sourceNodeName==='bodywork'?[['saddle proposed', [3],0xff55ff]]:s.sourceNodeName==='handlebar'?[['grip +Z proposed',[0],0x00ff77],['grip -Z proposed',[3],0x00ff77]]:[['peg +Z proposed',Array.from({length:11},(_,i)=>i),0x00ddff],['peg -Z proposed',Array.from({length:11},(_,i)=>i+12),0x00ddff]];
        for(const[name,components,color]of selections){const parts=s.components.filter(c=>components.includes(c.component));if(parts.length!==components.length)throw new Error('Missing target component');const triangles=parts.flatMap(c=>c.sourceTriangleOrdinals),vertices=[...new Set(parts.flatMap(c=>c.sourceVertexIndices))];
          const g=new T.BufferGeometry();g.setAttribute('position',p);g.setIndex(triangles.flatMap(tr=>[0,1,2].map(c=>idx.getX(tr*3+c))));
          const overlay=new T.Mesh(g,new T.MeshBasicMaterial({color,wireframe:true,depthTest:false,transparent:true,opacity:.85}));overlay.name='agent3-target:'+name;overlay.renderOrder=9999;mesh.add(overlay);
          const centre=new T.Vector3();for(const id of vertices)centre.add(new T.Vector3(p.getX(id),p.getY(id),p.getZ(id)));centre.multiplyScalar(1/vertices.length);
          const tag=document.createElement('div');tag.className='agent3label';tag.textContent=name;tag.style.color='#'+color.toString(16).padStart(6,'0');document.body.append(tag);
          targets.push({name,mesh,centre,tag,components,triangles,locator:locator(mesh)});
        }
      }
      window.__agent3Targets={bike,source,geometry,targets};t.render(true);
      return{assetSHA256:source.assetSHA256,geometry,frame:locator(bike.frame),frameOriginFileFrameM:source.frameOriginFileFrameM,
        proposedTargets:targets.map(o=>({name:o.name,mesh:o.locator,sourceComponents:o.components,sourceTriangleOrdinals:o.triangles,runtimeTriangleOrdinals:o.triangles,parentReviewed:false,closure:'unreviewed'})),
        riderVisible:false,riderCandidateLoaded:source.logical.includes('-lod.')?'normal player LOD; no candidate LOD claim':'candidate full'};
    },source);
    const folder=path.join(out,`${cls}-${tier}`);fs.mkdirSync(folder);const samples=[];
    for(let i=0;i<48;i++){
      const sample=await page.evaluate(({input,i,cls,tier})=>{
        const t=window.__rockhop,r=window.__render,d=r.debug,T=d.THREE,a=window.__agent3Targets;for(const frame of input){t.setInput(frame);t.step(1);t.render(true);}
        const c=new T.Vector3().setFromMatrixPosition(a.bike.frame.matrixWorld);c.y+=.38;r.setCameraOverride({mode:'orbit',yaw:.45+Math.sin(i/47*Math.PI*2)*.7,pitch:.18,dist:4.5,x:c.x,y:c.y,screenX:.5,screenY:.5});
        document.getElementById('agent3-title').textContent=`UNACCEPTED TARGET BINDINGS | ${cls} ${tier}\nGreen grip / cyan peg / magenta saddle proposals\nRecorded input ticks1..${(i+1)*10} | source and runtime triangles exact`;
        r.invalidate();t.render(true);
        let matrixError=0;const matrices=[];
        for(const g of a.geometry){let m=a.bike.root;for(const k of g.mesh.childPath)m=m.children[k];if(m.name!==g.mesh.name)throw new Error('Runtime locator drift');const expected=a.bike.frame.matrixWorld.clone().multiply(new T.Matrix4().makeTranslation(...a.source.frameOriginFileFrameM.map(v=>-v))).multiply(new T.Matrix4().fromArray(g.sourceNodeMatrixWorld));matrixError=Math.max(matrixError,...m.matrixWorld.elements.map((v,k)=>Math.abs(v-expected.elements[k])));matrices.push({mesh:g.mesh.name,world:m.matrixWorld.toArray()});}
        for(const target of a.targets){const p=target.centre.clone().applyMatrix4(target.mesh.matrixWorld).project(d.rig.camera);target.tag.style.left=((p.x+1)*480)+'px';target.tag.style.top=((1-p.y)*320)+'px';}
        return{frame:i,inputTick:(i+1)*10,stateHash:t.hashState(),tick:t.getState().tick,phase:t.phase(),matrixError,matrices,bikeFrameWorld:a.bike.frame.matrixWorld.toArray(),cameraWorld:d.rig.camera.matrixWorld.toArray(),cameraProjection:d.rig.camera.projectionMatrix.toArray(),poseInjection:false,audioContexts:window.__agent3AudioCount,webdriver:navigator.webdriver};
      },{input:inputs.slice(i*10,(i+1)*10),i,cls,tier});
      assert(sample.matrixError<1e-9&&sample.webdriver&&sample.audioContexts===0&&sample.phase==='riding');samples.push(sample);await page.screenshot({path:path.join(folder,String(i).padStart(4,'0')+'.png')});
    }
    const movie=path.join(folder,'played.mp4');const ff=spawnSync('ffmpeg',['-v','error','-y','-framerate','12','-i',path.join(folder,'%04d.png'),'-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p','-an','-movflags','+faststart',movie],{encoding:'utf8'});assert.equal(ff.status,0,ff.stderr);
    report.clips.push({path:movie,sha256:sha(fs.readFileSync(movie)),frames:48,fps:12,audio:false});report.cases.push({cls,tier,logical,binding,samples});
  }
  await Promise.all(responses);for(const r of inventory.reports){const m=manifest.models.find(m=>m.logical===r.logical);assert(report.loaded.some(l=>l.url.endsWith('/'+m.url)&&l.sha256===m.sha256&&l.status===200));}assert.deepEqual(report.errors,[]);
}catch(e){report.failure=String(e);process.exitCode=1;}
finally{fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');await context.close();await browser.close();await new Promise(resolve=>server.httpServer.close(resolve));console.log(JSON.stringify({status:report.status,cases:report.cases.length,clips:report.clips.length,failure:report.failure}));}
