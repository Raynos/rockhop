/** Exact candidate poses on actual Garage stage; riding geometry is diagnostic. */
/* oxlint-disable eslint/no-undef, typescript/no-extraneous-class -- Playwright browser globals and constructor-only silent audio trap. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';

const [buildArg, driverArg, expandedArg, outputArg] = process.argv.slice(2);
assert(outputArg, 'Usage: corrective-capture.mjs private-build driver.json expanded-driver.json fresh-output');
const build = path.resolve(buildArg), out = path.resolve(outputArg);
assert(!fs.existsSync(out), 'Capture output must be fresh');
fs.mkdirSync(out, { recursive: true });
const driverBytes = fs.readFileSync(driverArg), driver = JSON.parse(driverBytes);
const expandedBytes=fs.readFileSync(expandedArg), expanded=JSON.parse(expandedBytes);
const manifestBytes = fs.readFileSync(path.join(build, 'hero-review.json'));
const manifest = JSON.parse(manifestBytes);
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const candidate = manifest.models.find(m => m.logical === 'models/rider-street-mustard.glb');
assert.equal(candidate.sha256, expanded.GLBSHA256);
assert.equal(sha(driverBytes),expanded.poseDriverSHA256);
assert.equal(sha(expandedBytes),'ddced495c7ae0218c7ae83f5b47c1d007da137e8d7f05e37e08ae65a9c15d457');
assert(!manifest.newRiderAdapter && !manifest.newRiderSeam && !manifest.newRiderHipCorrective);
const report = { status: 'CAPTURE_PENDING_UNACCEPTED', build, driverSHA256: sha(driverBytes),
  manifestSHA256: sha(manifestBytes), expandedSHA256:sha(expandedBytes), candidate, errors: [], samples: [], clips: [], loaded: [],
  limits: ['Exact authored matrices and explicit recorded corrective coefficients; no production driver or physics-driven candidate riding.',
    'Garage normally selects authored geometry; riding geometry is explicitly staged for comparison.',
    'Native film shares candidate, pose times and named directions; native orthographic and Garage perspective projections differ.',
    'Original PBR/materials; before/after same three dressed meshes, body remains visible. One shirt base normal change is documented in admission.',
    'Finite frames do not certify continuous parity, clearance, support, art or device acceptance.'] };
const server = await preview({ configFile: false, root: process.cwd(), build: { outDir: build },
  preview: { host: '127.0.0.1', port: 0 }, logLevel: 'warn' });
const browser = await webkit.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 960, height: 640 }, deviceScaleFactor: 1 });
await context.addInitScript(() => {
  localStorage.setItem('rockhop.onboarded', '1'); window.__agent3AudioCount = 0;
  for (const key of ['AudioContext', 'webkitAudioContext']) window[key] = class {
    constructor() { window.__agent3AudioCount++; throw new Error('Silent capture forbids AudioContext'); }
  };
});
const page = await context.newPage(), loaded = [];
page.on('pageerror', e => report.errors.push(e.message));
page.on('response', r => {
  if (r.url().includes(candidate.url)) loaded.push(r.body().then(b => report.loaded.push({ sha256: sha(b), bytes: b.length, status: r.status() })));
});
try {
  report.launchURL = server.resolvedUrls.local[0] + '?audio=0&sw=0&outfit=street-mustard&rider=gltf&bike=gltf&physics=v2&hz=120';
  await page.goto(report.launchURL, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__rockhop?.ready && window.__rockhop?.app, null, { timeout: 120000 });
  await page.waitForFunction(() => !document.querySelector('#loader') || document.querySelector('#loader')?.getAttribute('data-done') === '1', null, { timeout: 120000 });
  await page.evaluate(async () => {
    const t = window.__rockhop, r = window.__render;
    t.setQuality('high'); await r.whenReady(); t.app.goto('garage'); await r.whenReady(); t.render(true);
  });
  await page.waitForFunction(() => window.__render.debugInfo().garage.on);
  await page.waitForTimeout(700);
  await page.addStyleTag({ content: '#ui,#ui *,.hud,.touch-controls{visibility:hidden!important} #agent3-label{position:fixed;z-index:99999;top:8px;left:10px;color:white;background:#101820e8;padding:8px;font:14px monospace;white-space:pre;visibility:visible!important}' });
  await page.evaluate(driver => {
    const r = window.__render, d = r.debug, T = d.THREE, rider = d.rider;
    const label = document.createElement('div'); label.id = 'agent3-label'; document.body.append(label);
    const bones = new Map();
    for (const [o, assoc] of rider.source.parser.associations) {
      if (!o.isBone || assoc.nodes === undefined) continue;
      const name = rider.source.parser.json.nodes[assoc.nodes].name;
      const matches = rider.scene.getObjectsByProperty('name', o.name);
      if (matches.length !== 1) throw new Error('Ambiguous runtime bone ' + name);
      bones.set(name, matches[0]);
    }
    if (bones.size !== driver.jointOrderNative.length) throw new Error('Complete skin joint count mismatch');
    rider.scene.updateMatrixWorld(true);
    const wrapper = rider.scene.matrixWorld.clone();
    const target = new T.Vector3(.65, .9, 0).applyMatrix4(wrapper);
    window.__agent3 = { rider, bones, wrapper, target, driver, index: 0, geometry: 'authored', apply() {
      for (const item of rider.sleeveGeometry) item.mesh.geometry = this.geometry === 'authored' ? item.authored : item.riding;
      rider.scene.updateMatrixWorld(true);
      const f = driver.frames[this.index], desired = new Map();
      for (const [name, bone] of bones) desired.set(bone, wrapper.clone().multiply(new T.Matrix4().fromArray(f.jointWorldColumnMajor[name])));
      for (const [bone, world] of desired) {
        const parent = desired.get(bone.parent) ?? bone.parent.matrixWorld;
        bone.matrixAutoUpdate = false; bone.matrix.copy(parent.clone().invert().multiply(world));
      }
      rider.scene.updateMatrixWorld(true);
      rider.scene.traverse(o => { if (o.isSkinnedMesh) o.skeleton.update(); });
    } };
    rider.update = () => window.__agent3.apply();
  }, driver);
  await page.evaluate(expanded=>{
    const a=window.__agent3,d=window.__render.debug;
    a.expanded=expanded;a.corrective='off';a.baseApply=a.apply;
    a.morphMeshes=expanded.configs.map(config=>{
      const matches=a.rider.sleeveGeometry.map(i=>i.mesh).filter(m=>m.morphTargetDictionary&&config.keys.every(k=>Number.isInteger(m.morphTargetDictionary[k])));
      if(matches.length!==1)throw new Error('Runtime target identity mismatch');
      return{config,mesh:matches[0]};
    });
    a.apply=function(){
      this.baseApply();
      for(const {config,mesh}of this.morphMeshes){
        mesh.morphTargetInfluences.fill(0);
        if(this.corrective==='controller')for(const name of config.keys)mesh.morphTargetInfluences[mesh.morphTargetDictionary[name]]=expanded.frames[this.index].coefficients[config.region][name];
      }
    };
    a.body=a.rider.sleeveGeometry.find(i=>i.mesh.name.startsWith('Canonical_')).mesh;
    a.bounds=new Map();
    a.loaderSnapshot=a.rider.sleeveGeometry.map(item=>{
      let owner=item.mesh;while(owner&&owner.userData.rockhopRiderSkinConditioned===undefined)owner=owner.parent;
      return{name:item.mesh.name,vertices:item.mesh.geometry.attributes.position.count,morphTargetDictionary:item.mesh.morphTargetDictionary??{},morphPositionTargets:item.mesh.geometry.morphAttributes.position?.length??0,morphTargetsRelative:item.mesh.geometry.morphTargetsRelative,authoredEqualsRiding:item.authored===item.riding,conditionedOwner:owner?.name,conditionedFlag:owner?.userData.rockhopRiderSkinConditioned,materialSide:item.mesh.material.side};
    });
    if(a.loaderSnapshot.some(r=>!r.authoredEqualsRiding||r.conditionedFlag!==1))throw new Error('Normal loader added conditioning or lost declaration');
    a.THREE=d.THREE;
  },expanded);
  report.loaderSnapshot=await page.evaluate(()=>window.__agent3.loaderSnapshot);
  report.rays=[];
  const witnesses=[
    [112,'side',0,[[469,190],[473,193]]],
    [144,'side',0,[[497,165],[496,167]]],
    [240,'side',0,[[376,227],[377,228],[478,375]]],
    [72,'side',0,[[469,190],[497,165]]],
  ];
  for(const geometry of ['authored','riding'])for(const corrective of ['off','controller'])for(const [index,view,yaw,pixels]of witnesses){
    const rays=await page.evaluate(({index,geometry,corrective,yaw,pixels})=>{
      const a=window.__agent3,r=window.__render,t=window.__rockhop,d=r.debug,T=d.THREE;
      a.index=index;a.geometry=geometry;a.corrective=corrective;a.apply();
      r.setCameraOverride({mode:'orbit',yaw,pitch:.10,dist:4.5,x:a.target.x,y:a.target.y,screenX:.5,screenY:.5});r.invalidate();t.render(true);
      const meshes=a.rider.sleeveGeometry.map(i=>i.mesh);
      for(const m of meshes){m.computeBoundingSphere();m.computeBoundingBox();}
      return {camera:{world:d.rig.camera.matrixWorld.toArray(),projection:d.rig.camera.projectionMatrix.toArray()},riderWrapperWorld:a.wrapper.toArray(),rays:pixels.map(([x,y])=>{
        const ray=new T.Raycaster();ray.setFromCamera(new T.Vector2(x/960*2-1,1-y/640*2),d.rig.camera);
        return{pixel:[x,y],hits:ray.intersectObjects(meshes,false).slice(0,5).map(h=>{const ids=h.object.geometry.attributes._source_id;return{mesh:h.object.name,triangle:h.faceIndex,source:[h.face.a,h.face.b,h.face.c].map(i=>ids.getX(i)),distanceM:h.distance,filePointM:h.point.clone().applyMatrix4(a.wrapper.clone().invert()).toArray()};})};
      })};
    },{index,geometry,corrective,yaw,pixels});
    report.rays.push({index,timeS:index/48,view,geometry,corrective,...rays});
  }
  const views=[['side',0],['front-three-quarter',Math.PI/4],['rear-three-quarter',-Math.PI/4]],anchors=new Map();
  for(const [view,yaw]of views)for(const geometry of ['authored','riding'])for(const corrective of ['off','controller']){
    const folder=path.join(out,view,geometry,corrective);fs.mkdirSync(folder,{recursive:true});
    for(let n=0;n<=132;n++){
      const index=n*4;
      const sample=await page.evaluate(({index,geometry,corrective,view,yaw})=>{
        const a=window.__agent3,t=window.__rockhop,r=window.__render,d=r.debug,T=d.THREE;
        a.index=index;a.geometry=geometry;a.corrective=corrective;a.apply();
        r.setCameraOverride({mode:'orbit',yaw,pitch:.10,dist:6.75,x:a.target.x,y:a.target.y+.25,screenX:.5,screenY:.5});
        document.getElementById('agent3-label').textContent=`UNACCEPTED LOCAL CORRECTIVE | actual Garage | ${view}\n${geometry==='authored'?'Normal Garage':'Tagged normal riding geometry staged in Garage'} | morph ${corrective}\nShared t=${(index/48).toFixed(3)}s | same3dressed meshes/materials | synthetic FK`;
        r.invalidate();t.render(true);
        let matrixMaxError=0;const inv=a.wrapper.clone().invert();
        for(const [name,bone]of a.bones)matrixMaxError=Math.max(matrixMaxError,...inv.clone().multiply(bone.matrixWorld).elements.map((v,k)=>Math.abs(v-a.driver.frames[index].jointWorldColumnMajor[name][k])));
        const key=`${view}/${index}`;
        if(!a.bounds.has(key)){
          const bound={minX:Infinity,minY:Infinity,maxX:-Infinity,maxY:-Infinity};
          for(let i=0;i<a.body.geometry.attributes.position.count;i++){
            const p=a.body.getVertexPosition(i,new T.Vector3()).applyMatrix4(a.body.matrixWorld).project(d.rig.camera),x=(p.x+1)*480,y=(1-p.y)*320;
            bound.minX=Math.min(bound.minX,x);bound.maxX=Math.max(bound.maxX,x);bound.minY=Math.min(bound.minY,y);bound.maxY=Math.max(bound.maxY,y);
          }
          a.bounds.set(key,bound);
        }
        return{index,timeS:index/48,geometry,corrective,view,matrixMaxError,bodyPixelBounds:a.bounds.get(key),stateHash:t.hashState(),webdriver:navigator.webdriver,audioContexts:window.__agent3AudioCount,garage:r.debugInfo().garage.on,
          camera:{world:d.rig.camera.matrixWorld.toArray(),projection:d.rig.camera.projectionMatrix.toArray()},
          riderWrapperWorld:a.wrapper.toArray(),bikeFrameWorld:d.bike.frame.matrixWorld.toArray(),
          morphCoefficients:a.morphMeshes.map(({config,mesh})=>({region:config.region,values:Object.fromEntries(config.keys.map(name=>[name,mesh.morphTargetInfluences[mesh.morphTargetDictionary[name]]]))}))};
      },{index,geometry,corrective,view,yaw});
      assert(sample.webdriver&&sample.garage&&sample.audioContexts===0&&sample.matrixMaxError<1e-10);
      const b=sample.bodyPixelBounds;assert(b.minX>=0&&b.maxX<=960&&b.minY>=80&&b.maxY<=640,'Body/limbs or label overlap outside frame: '+JSON.stringify(sample));
      const key=`${view}/${index}`;if(!anchors.has(key))anchors.set(key,sample.camera);else assert.deepEqual(sample.camera,anchors.get(key),'Before/after/branch effective camera mismatch');
      for(const row of sample.morphCoefficients)for(const [name,value]of Object.entries(row.values))assert.equal(value,corrective==='off'?0:expanded.frames[index].coefficients[row.region][name]);
      await page.screenshot({path:path.join(folder,`${String(n).padStart(4,'0')}.png`)});report.samples.push(sample);
    }
    const movie=path.join(folder,'played.mp4');
    const ff=spawnSync('ffmpeg',['-v','error','-y','-framerate','12','-i',path.join(folder,'%04d.png'),'-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p','-an','-movflags','+faststart',movie],{encoding:'utf8'});
    assert.equal(ff.status,0,ff.stderr);report.clips.push({path:movie,sha256:sha(fs.readFileSync(movie)),frames:133,fps:12,audio:false});
  }
  await Promise.all(loaded);
  assert(report.loaded.some(r => r.sha256 === expanded.GLBSHA256 && r.status === 200));
  assert.equal(new Set(report.samples.map(s => s.stateHash)).size, 1, 'Physics changed during authored capture');
  assert.deepEqual(report.errors, []); report.status = 'CAPTURED_UNACCEPTED';
} catch (e) { report.failure = String(e); process.exitCode = 1; }
finally {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  await context.close(); await browser.close(); await new Promise(resolve => server.httpServer.close(resolve));
  console.log(JSON.stringify({ status: report.status, frames: report.samples.length, clips: report.clips.length, failure: report.failure }));
}
