/** Whole-rider played authored anatomy on the normal private game stage. */
/* oxlint-disable eslint/no-undef, typescript/no-extraneous-class -- headless browser globals and silent AudioContext trap. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';
const [buildArg, driverFile, expandedFile, controllerFile, outArg] = process.argv.slice(2);
assert(outArg); const build=path.resolve(buildArg),out=path.resolve(outArg);
assert(!fs.existsSync(out));fs.mkdirSync(out,{recursive:true});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const driverBytes=fs.readFileSync(driverFile),driver=JSON.parse(driverBytes);
const expandedBytes=fs.readFileSync(expandedFile),expanded=JSON.parse(expandedBytes);
const controllerBytes=fs.readFileSync(controllerFile),controller=JSON.parse(controllerBytes);
const manifestBytes=fs.readFileSync(path.join(build,'hero-review.json')),manifest=JSON.parse(manifestBytes);
const candidate=manifest.models.find(m=>m.logical==='models/rider-street-mustard.glb');
assert.equal(candidate.sha256,controller.candidateGLBSHA256);
assert.equal(sha(driverBytes),controller.poseDriverSHA256);
assert.equal(sha(expandedBytes),'ddced495c7ae0218c7ae83f5b47c1d007da137e8d7f05e37e08ae65a9c15d457');
assert.deepEqual(controller.configs,expanded.configs);
assert(!manifest.newRiderAdapter&&!manifest.newRiderSeam&&!manifest.newRiderHipCorrective);
const report={status:'CAPTURE_PENDING_UNACCEPTED',candidate,build,
  driverSHA256:sha(driverBytes),controllerSHA256:sha(controllerBytes),expandedSHA256:sha(expandedBytes),manifestSHA256:sha(manifestBytes),
  captureSHA256:sha(fs.readFileSync(new URL(import.meta.url))),presentationSHA256:sha(fs.readFileSync(new URL('presentation.mjs',import.meta.url))),
  sourceMasterSHA256:controller.candidateMasterSHA256,errors:[],loaded:[],samples:[],clips:[],
  limits:['Authored 51-joint anatomical replay; bike hidden by visibility only. No supported riding/contact claim.',
    'Private explicit diagnostic coefficients applied to both cloth primitives. Normal production has no automatic rig-angle controller.',
    'Whole-rider bounds and silent delivery decoding do not establish art, fit, native parity, LOD or physical device acceptance.']};
const server=await preview({configFile:false,root:process.cwd(),build:{outDir:build},preview:{host:'127.0.0.1',port:0},logLevel:'warn'});
const browser=await webkit.launch({headless:true});
const context=await browser.newContext({viewport:{width:960,height:640},deviceScaleFactor:1});
await context.addInitScript(()=>{localStorage.setItem('rockhop.onboarded','1');window.__agent3AudioCount=0;for(const k of['AudioContext','webkitAudioContext'])window[k]=class{constructor(){window.__agent3AudioCount++;throw new Error('Silent harness forbids AudioContext');}};});
const page=await context.newPage(),responses=[];
page.on('pageerror',e=>report.errors.push(e.message));
page.on('response',r=>{if(r.url().includes(candidate.url))responses.push(r.body().then(b=>report.loaded.push({sha256:sha(b),status:r.status(),bytes:b.length})));});
try{
  await page.goto(server.resolvedUrls.local[0]+'?audio=0&sw=0&outfit=street-mustard&rider=gltf&bike=gltf&physics=v2&hz=120');
  await page.waitForFunction(()=>window.__rockhop?.ready,null,{timeout:120000});
  await page.waitForFunction(()=>!document.querySelector('#loader')||document.querySelector('#loader').getAttribute('data-done')==='1',null,{timeout:120000});
  await page.evaluate(async()=>{const t=window.__rockhop,r=window.__render;t.setQuality('high');await r.whenReady();t.app.goto('garage');await r.whenReady();t.render(true);});
  await page.waitForFunction(()=>window.__render.debugInfo().garage.on);await page.waitForTimeout(700);
  await page.addStyleTag({content:'#ui,#ui *,.hud,.touch-controls{visibility:hidden!important} #agent3-label{position:fixed;z-index:99999;top:8px;left:10px;color:white;background:#101820e8;padding:8px;font:14px monospace;white-space:pre;visibility:visible!important}'});
  await page.addScriptTag({content:fs.readFileSync(new URL('presentation.mjs',import.meta.url),'utf8').replace(/^export /gm,'')});
  report.loader=await page.evaluate(({driver,expanded,controller})=>{
    const r=window.__render,d=r.debug,T=d.THREE,rider=d.rider,bones=new Map();
    for(const[o,a]of rider.source.parser.associations){if(!o.isBone||a.nodes===undefined)continue;const name=rider.source.parser.json.nodes[a.nodes].name,matches=rider.scene.getObjectsByProperty('name',o.name);if(matches.length!==1)throw new Error('Ambiguous clone bone '+name);bones.set(name,matches[0]);}
    if(bones.size!==51||driver.jointOrderNative.length!==51)throw new Error('Complete skin missing');
    rider.scene.updateMatrixWorld(true);const wrapper=rider.scene.matrixWorld.clone(),meshes=rider.sleeveGeometry.map(i=>i.mesh);
    const morphParts=controller.configs.flatMap(config=>{const matches=meshes.filter(m=>config.keys.every(k=>Number.isInteger(m.morphTargetDictionary?.[k])));if(matches.length!==(config.region==='cloth'?2:1))throw new Error('Primitive controller mismatch');return matches.map(mesh=>({config,mesh}));});
    const presentation=bikeFreeAnatomyPresentation(d.bike.root,rider.scene);
    const target=new T.Vector3(.65,.9,0).applyMatrix4(wrapper);
    const label=document.createElement('div');label.id='agent3-label';document.body.append(label);
    const initial=meshes.map(mesh=>{let owner=mesh;while(owner&&owner.userData.rockhopRiderSkinConditioned===undefined)owner=owner.parent;const entry=rider.sleeveGeometry.find(i=>i.mesh===mesh);if(owner?.userData.rockhopRiderSkinConditioned!==1||entry.authored!==entry.riding)throw new Error('Conditioning scope changed');const mats=Array.isArray(mesh.material)?mesh.material:[mesh.material];return{mesh:mesh.name,vertices:mesh.geometry.attributes.position.count,defaultInfluences:mesh.morphTargetInfluences?.slice()??[],targets:mesh.morphTargetDictionary??{},authoredEqualsRiding:true,owner:owner.name,materials:mats.map(m=>({name:m.name,type:m.type,color:m.color?.toArray(),roughness:m.roughness,metalness:m.metalness,side:m.side,mapSize:m.map?[m.map.image?.width,m.map.image?.height]:null,mapColorSpace:m.map?.colorSpace}))};});
    window.__agent3={driver,expanded,controller,rider,bones,wrapper,target,meshes,morphParts,presentation,index:0,apply(){
      rider.scene.updateMatrixWorld(true);const desired=new Map();for(const[name,bone]of bones)desired.set(bone,wrapper.clone().multiply(new T.Matrix4().fromArray(driver.frames[this.index].jointWorldColumnMajor[name])));
      for(const[bone,world]of desired){const parent=desired.get(bone.parent)??bone.parent.matrixWorld;bone.matrixAutoUpdate=false;bone.matrix.copy(parent.clone().invert().multiply(world));}
      for(const{config,mesh}of morphParts){mesh.morphTargetInfluences.fill(0);for(const k of config.keys)mesh.morphTargetInfluences[mesh.morphTargetDictionary[k]]=expanded.frames[this.index].coefficients[config.region][k];}
      rider.scene.updateMatrixWorld(true);for(const m of meshes)m.skeleton.update();presentation.applyVisibility();
    }};rider.update=()=>window.__agent3.apply();
    return{completeBones:bones.size,meshes:initial,bikeVisibility:presentation.hiddenBranches,primitiveControllerMatches:morphParts.map(({config,mesh})=>({region:config.region,mesh:mesh.name}))};
  },{driver,expanded,controller});
  for(const[view,yaw]of[['front-three-quarter',Math.PI/4],['rear-three-quarter',-Math.PI/4]]){
    const folder=path.join(out,view);fs.mkdirSync(folder);
    for(let n=0;n<=132;n++){
      const index=n*4;
      const sample=await page.evaluate(({index,yaw,view})=>{
        const a=window.__agent3,r=window.__render,t=window.__rockhop,d=r.debug,T=d.THREE;a.index=index;a.apply();
        r.setCameraOverride({mode:'orbit',yaw,pitch:.1,dist:6.75,x:a.target.x,y:a.target.y+.25,screenX:.5,screenY:.5});
        document.getElementById('agent3-label').textContent=`UNACCEPTED WHOLE RIDER | actual engine | ${view}\nBike-free anatomy | explicit 51-joint authored replay + controller\nShared t=${(index/48).toFixed(3)}s | source frames0..528`;
        r.invalidate();t.render(true);a.presentation.assertPresentation();
        let matrixMaxError=0;const inv=a.wrapper.clone().invert();for(const[name,bone]of a.bones)matrixMaxError=Math.max(matrixMaxError,...inv.clone().multiply(bone.matrixWorld).elements.map((v,k)=>Math.abs(v-a.driver.frames[index].jointWorldColumnMajor[name][k])));
        const bounds={minX:Infinity,minY:Infinity,maxX:-Infinity,maxY:-Infinity},p=new T.Vector3();
        for(const m of a.meshes){m.skeleton.update();for(let i=0;i<m.geometry.attributes.position.count;i++){m.getVertexPosition(i,p).applyMatrix4(m.matrixWorld).project(d.rig.camera);const x=(p.x+1)*480,y=(1-p.y)*320;bounds.minX=Math.min(bounds.minX,x);bounds.maxX=Math.max(bounds.maxX,x);bounds.minY=Math.min(bounds.minY,y);bounds.maxY=Math.max(bounds.maxY,y);}}
        return{index,timeS:index/48,view,matrixMaxError,wholeRiderPixelBounds:bounds,bikeVisible:false,poseInjection:true,stateHash:t.hashState(),webdriver:navigator.webdriver,audioContexts:window.__agent3AudioCount,garage:r.debugInfo().garage.on,
          camera:{world:d.rig.camera.matrixWorld.toArray(),projection:d.rig.camera.projectionMatrix.toArray()},riderWrapperWorld:a.wrapper.toArray(),
          coefficients:a.morphParts.map(({config,mesh})=>({region:config.region,mesh:mesh.name,values:Object.fromEntries(config.keys.map(k=>[k,mesh.morphTargetInfluences[mesh.morphTargetDictionary[k]]]))}))};
      },{index,yaw,view});
      assert(sample.webdriver&&sample.garage&&sample.audioContexts===0&&sample.matrixMaxError<1e-10);
      const b=sample.wholeRiderPixelBounds;assert(b.minX>=0&&b.maxX<=960&&b.minY>=80&&b.maxY<=640,'Whole rider outside bounds '+JSON.stringify(b));
      for(const row of sample.coefficients)for(const[k,v]of Object.entries(row.values))assert.equal(v,expanded.frames[index].coefficients[row.region][k]);
      await page.screenshot({path:path.join(folder,String(n).padStart(4,'0')+'.png')});report.samples.push(sample);
    }
    const movie=path.join(folder,'played.mp4');const ff=spawnSync('ffmpeg',['-v','error','-y','-framerate','12','-i',path.join(folder,'%04d.png'),'-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p','-an','-movflags','+faststart',movie],{encoding:'utf8'});assert.equal(ff.status,0,ff.stderr);
    report.clips.push({path:movie,sha256:sha(fs.readFileSync(movie)),frames:133,fps:12,audio:false});
  }
  await Promise.all(responses);assert(report.loaded.some(r=>r.sha256===candidate.sha256&&r.status===200));assert.equal(new Set(report.samples.map(s=>s.stateHash)).size,1);assert.deepEqual(report.errors,[]);report.status='CAPTURED_BIKE_FREE_ANATOMY_UNACCEPTED';
}catch(e){report.failure=String(e);process.exitCode=1;}
finally{fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');await context.close();await browser.close();await new Promise(resolve=>server.httpServer.close(resolve));console.log(JSON.stringify({status:report.status,frames:report.samples.length,clips:report.clips.length,failure:report.failure}));}
