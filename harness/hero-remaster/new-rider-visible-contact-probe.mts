/** Read-only actual skinned hand/sole surfaces during recorded physics, never socket proxies. */
/* oxlint-disable typescript/no-explicit-any -- private actual renderer diagnostics. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
import { decodeJSON, expandFrames } from '../../src/core/replay';
const arg=(k:string,f='')=>process.argv.find(a=>a.startsWith(`--${k}=`))?.slice(k.length+3)??f;
const build=path.resolve(arg('build','harness/out/hero-remaster/new-rider-body11-build'));
const out=path.resolve(arg('out','docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11'));
const roi=JSON.parse(fs.readFileSync(path.join(out,'source-roi.json'),'utf8'));
const grip=JSON.parse(fs.readFileSync('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/bike-grip-surface02/report.json','utf8')).results[0].grips;
const recording=decodeJSON(fs.readFileSync('docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json','utf8'));
const inputs=expandFrames(recording),fps=12,steps=recording.header.physicsHz/fps,frames=480;
assert(Number.isInteger(steps)&&inputs.length>=frames*steps);
const report:any={sourceSHA256:roi.sourceSHA256,build,scope:'Actual native hand + lowest 2.1mm shoe vertices, real runtime skin and morphs versus literal bike triangles; no pose injected',fps,frames,samples:[],errors:[],loaded:[]};
for(const entry of [...roi.hands,...roi.feet])assert(!fs.existsSync(path.join(out,`${entry.bikeMeshName==='handlebar'?'hand':'sole'}-${entry.side}.f32`)),'Fresh point-buffer destination required');
for(const focus of ['hands','feet']){fs.mkdirSync(path.join(out,focus,'frames'),{recursive:true});assert.equal(fs.readdirSync(path.join(out,focus,'frames')).length,0);}
const server=await preview({configFile:false,root:process.cwd(),build:{outDir:build},preview:{host:'127.0.0.1',port:0},logLevel:'warn'});
const browser=await webkit.launch({headless:true}),context=await browser.newContext({viewport:{width:1280,height:720},deviceScaleFactor:1});
await context.addInitScript(()=>localStorage.setItem('rockhop.onboarded','1'));
const page=await context.newPage(), responses:Promise<void>[]=[];
page.on('pageerror',e=>report.errors.push(e.message));
page.on('response',r=>{if(r.url().endsWith('.glb'))responses.push(r.body().then(b=>report.loaded.push({url:r.url(),sha256:crypto.createHash('sha256').update(b).digest('hex')})));});
try{
 await page.goto(server.resolvedUrls!.local[0]+`?harness=1&audio=0&sw=0&outfit=street-mustard&physics=${recording.header.physics??'v1'}&hz=${recording.header.physicsHz}`);
 await page.waitForFunction(()=>(window as any).__rockhop?.ready,null,{timeout:120000});
 await page.evaluate(async header=>{const t=(window as any).__rockhop,r=(window as any).__render;t.setBike(header.bike??'rookie');await r.whenReady();await t.loadTrack(header.trackId,header.seed);await r.whenReady();t.setQuality('high');await r.whenReady();t.skipCountdown();t.render(true);},recording.header);
 report.surfaceSetup=await page.evaluate(({roi,grip})=>{
  const d=(window as any).__render.debug,T=d.THREE,sets:any[]=[];
  for(const entry of [...roi.hands,...roi.feet]){
   const mesh=d.rider.scene.getObjectByName(entry.meshName),bikeMesh=d.bike.root.getObjectByName(entry.bikeMeshName);
   if(!mesh?.isSkinnedMesh||!bikeMesh?.isMesh)throw new Error('Missing actual surface mesh');
   const pos=bikeMesh.geometry.getAttribute('position'),indices=bikeMesh.geometry.index,triangles:any[]=[];
   if(!indices)throw new Error('Indexed bike surface required');
   let triangleIds:number[][];
   if(entry.bikeMeshName==='handlebar')triangleIds=grip.find((g:any)=>g.side===entry.side).sourceMeshSurface.triangles;
   else{
    triangleIds=[];const sign=entry.side==='L'?1:-1;
    for(let i=0;i<indices.count;i+=3){const ids=[indices.getX(i),indices.getX(i+1),indices.getX(i+2)];if(ids.every(v=>pos.getZ(v)*sign>0))triangleIds.push(ids);}
   }
   for(const ids of triangleIds){const p=ids.map(i=>new T.Vector3().fromBufferAttribute(pos,i));const tri=new T.Triangle(...p);triangles.push({tri,normal:tri.getNormal(new T.Vector3()),sourceVertices:ids});}
   sets.push({entry,mesh,bikeMesh,triangles});
  }
  (window as any).__surfaceProbe=sets;
  return sets.map(s=>({side:s.entry.side,riderMesh:s.mesh.name,riderVertices:s.entry.sourceVertices.length,bikeMesh:s.bikeMesh.name,bikeTriangles:s.triangles.length,morphDictionary:s.mesh.morphTargetDictionary,morphInfluences:s.mesh.morphTargetInfluences,sourceTriangles:s.entry.triangles.length,bikeTriangleVertices:s.triangles.map((q:any)=>({sourceVertices:q.sourceVertices,points:[q.tri.a.toArray(),q.tri.b.toArray(),q.tri.c.toArray()]}))}));
 },{roi,grip});
 await page.addStyleTag({content:'.hud,.hud-top,.hud-bottom,.run-hud,.touch-controls,.countdown{visibility:hidden!important}'});
 await page.evaluate(()=>{for(const e of document.querySelectorAll<HTMLElement>('body > *'))if(e.tagName!=='CANVAS'&&!e.querySelector('canvas'))e.style.visibility='hidden';});
 for(let i=0;i<frames;i++){
  const sample=await page.evaluate(({input,i})=>{
   const t=(window as any).__rockhop,r=(window as any).__render,d=r.debug,T=d.THREE,sets=(window as any).__surfaceProbe;
   for(const f of input){t.setInput(f);t.step(1);} r.invalidate();t.render(true);
   const contacts:any[]=[],focus=i%2===0?'hands':'feet',target=new T.Vector3();let targetN=0;
   // A coarse actual surface midpoint chooses the orbit, then the final current
   // presentation is measured. Never bind state-labelled metrics to the earlier
   // presentation matrices just because their bike-local distances look stable.
   for(const s of sets)if((focus==='hands')===(s.entry.bikeMeshName==='handlebar'))for(const v of s.entry.sourceVertices){target.add(s.mesh.localToWorld(s.mesh.getVertexPosition(v,new T.Vector3())));targetN++;}
   target.divideScalar(targetN);
   r.setCameraOverride({mode:'orbit',x:target.x,y:target.y,yaw:.4+1.25*Math.sin(i*Math.PI*2/119),pitch:.12,dist:3,screenX:.5,screenY:.5});
   d.rig.camera.clearViewOffset();d.rig.camera.zoom=2.2;d.rig.camera.updateProjectionMatrix();r.invalidate();t.render(true);
   const renderedTarget=new T.Vector3();let renderedN=0;
   for(const s of sets)if((focus==='hands')===(s.entry.bikeMeshName==='handlebar'))for(const v of s.entry.sourceVertices){renderedTarget.add(s.mesh.localToWorld(s.mesh.getVertexPosition(v,new T.Vector3())));renderedN++;}
   renderedTarget.divideScalar(renderedN);
   const ndc=renderedTarget.clone().project(d.rig.camera),size=d.renderer.getSize(new T.Vector2());d.rig.camera.setViewOffset(size.x,size.y,ndc.x*size.x/2,-ndc.y*size.y/2,size.x,size.y);d.rig.camera.updateProjectionMatrix();r.invalidate();t.render(true);
   const finalTarget=new T.Vector3();let finalN=0;
   for(const s of sets){
    const points:any[]=[],gaps:number[]=[],signed:number[]=[],witness:any[]=[];
    const inverse=s.bikeMesh.matrixWorld.clone().invert(),nearest=new T.Vector3(),delta=new T.Vector3();
    for(const sourceVertex of s.entry.sourceVertices){
     const world=s.mesh.localToWorld(s.mesh.getVertexPosition(sourceVertex,new T.Vector3()));const p=world.clone().applyMatrix4(inverse);points.push(p.toArray());
     if((focus==='hands')===(s.entry.bikeMeshName==='handlebar')){finalTarget.add(world);finalN++;}
     let best=Infinity,bestSigned=0,bestTri=-1,bestPoint:any=null;
     for(let j=0;j<s.triangles.length;j++){const q=s.triangles[j];q.tri.closestPointToPoint(p,nearest);const next=p.distanceToSquared(nearest);if(next<best){best=next;bestSigned=delta.copy(p).sub(nearest).dot(q.normal)<0?-Math.sqrt(next):Math.sqrt(next);bestTri=j;bestPoint=nearest.toArray();}}
     gaps.push(Math.sqrt(best));signed.push(bestSigned);witness.push({triangle:bestTri,point:bestPoint});
    }
    if(!points.flat().every(Number.isFinite))throw new Error('Nonfinite skinned surface');
    const groups:any={};if(s.entry.fingerSurfaceGroups)for(const [finger,ids] of Object.entries(s.entry.fingerSurfaceGroups) as [string,number[]][]){const sorted=ids.map(v=>({v,gap:gaps[v]!})).sort((a,b)=>a.gap-b.gap);const w=sorted[0]!;groups[finger]={minimumAbsoluteVertexTriangleGapM:w.gap,within1mmVertices:sorted.filter(x=>x.gap<=.001).length,witness:{sourceVertex:s.entry.sourceVertices[w.v],skinPoint:points[w.v],...witness[w.v]}};}
    const min=Math.min(...gaps),index=gaps.indexOf(min);
    contacts.push({side:s.entry.side,kind:s.entry.bikeMeshName==='handlebar'?'hand':'sole',minimumAbsoluteVertexTriangleGapM:min,maximumUnsignedVertexTriangleGapM:Math.max(...gaps),maximumNearestNormalSignedVertexDepthM:Math.max(0,...signed.map(x=>-x)),within1mmVertices:gaps.filter(x=>x<=.001).length,groups,witness:{sourceVertex:s.entry.sourceVertices[index],skinPoint:points[index],...witness[index]},points});
   }
   finalTarget.divideScalar(finalN);
   const after=finalTarget.clone().project(d.rig.camera);if(Math.hypot(after.x,after.y)>1e-6)throw new Error('Actual FINAL contact-surface projection did not center');
   const finalPresentationFocusDeltaM=finalTarget.distanceTo(renderedTarget);if(finalPresentationFocusDeltaM>1e-6)throw new Error('Actual final surfaces changed after projection render');
   return {i,focus,tick:t.getState().tick,state:structuredClone(t.getState()),hash:t.hashState(),debug:structuredClone(d.rider.debug),contacts,effectiveCamera:{position:d.rig.camera.position.toArray(),quaternion:d.rig.camera.quaternion.toArray(),fov:d.rig.camera.fov,zoom:d.rig.camera.zoom,view:structuredClone(d.rig.camera.view)},focusWorld:finalTarget.toArray(),surfaceProjection:{before:ndc.toArray(),after:after.toArray(),beforeCameraPresentationFocusWorld:target.toArray(),presentationFocusDeltaM:target.distanceTo(renderedTarget),finalPresentationFocusDeltaM}};
  },{input:inputs.slice(i*steps,(i+1)*steps),i});
  for(const c of sample.contacts){const values=new Float32Array(c.points.flat());fs.appendFileSync(path.join(out,`${c.kind}-${c.side}.f32`),Buffer.from(values.buffer));delete c.points;}
  report.samples.push(sample);
  await page.screenshot({path:path.join(out,sample.focus,'frames',`${String(Math.floor(i/2)).padStart(4,'0')}.png`)});
 }
 await Promise.all(responses);assert(report.loaded.some((r:any)=>r.sha256===roi.sourceSHA256),'Actual body11 was not consumed');assert.deepEqual(report.errors,[]);
 for(const focus of ['hands','feet']){const f=spawnSync('ffmpeg',['-v','error','-y','-framerate','6','-i',path.join(out,focus,'frames/%04d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p',path.join(out,focus,'played.mp4')],{encoding:'utf8'});assert.equal(f.status,0,f.stderr);}
 report.limits=[...roi.limits,'Nearest-face normal signs on quantized surfaces are local diagnostics, not watertight penetration certificates.','Actual source triangles/points retained for whole-triangle audits; runtime metric here samples vertices only.','Hand and foot camera views alternate at 6fps each; 480 contact samples at 12fps. Rendered far-side contacts may be occluded.','Recorded input and runtime pose are unchanged; no surface contact acceptance is claimed by the builder.'];
}catch(e){report.failure=e instanceof Error?e.message:String(e);process.exitCode=1;}
finally{await context.close();await browser.close();await new Promise<void>(resolve=>server.httpServer.close(()=>resolve()));fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({out,samples:report.samples.length,failure:report.failure,errors:report.errors}));}
