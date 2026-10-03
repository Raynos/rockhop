/** Focused visibility/ray witnesses on unchanged diagnostic02; never acceptance. */
/* oxlint-disable eslint/no-undef, typescript/no-extraneous-class -- Playwright browser globals and constructor-only silent audio trap. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { preview } from 'vite';
import { webkit } from 'playwright';

const [buildArg, driverArg, outputArg] = process.argv.slice(2);
assert(outputArg, 'Usage: focus.mjs private-build driver.json fresh-output');
const build = path.resolve(buildArg), out = path.resolve(outputArg);
assert(!fs.existsSync(out), 'Capture output must be fresh');
fs.mkdirSync(out, { recursive: true });
const driverBytes = fs.readFileSync(driverArg), driver = JSON.parse(driverBytes);
const manifestBytes = fs.readFileSync(path.join(build, 'hero-review.json'));
const manifest = JSON.parse(manifestBytes);
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const candidate = manifest.models.find(m => m.logical === 'models/rider-street-mustard.glb');
assert.equal(candidate.sha256, driver.conditionedGLBSHA256);
assert(!manifest.newRiderAdapter && !manifest.newRiderSeam && !manifest.newRiderHipCorrective);
const report = { status: 'CAPTURE_PENDING_UNACCEPTED', build, driverSHA256: sha(driverBytes),
  manifestSHA256: sha(manifestBytes), candidate, errors: [], samples: [], clips: [], loaded: [],
  limits: ['Exact authored pose override; no physics-driven candidate riding.',
    'Garage normally selects authored geometry; riding geometry is explicitly staged for comparison.',
    'Native film shares candidate, pose times and named directions; native orthographic and Garage perspective projections differ.',
    'Gray/structural PBR control, no protected generated identity or finished hoodie.',
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
  const witnesses = [
    [112, 'side', 0, [[469,190], [473,193], [477,388]]],
    [144, 'side', 0, [[497,165], [496,167]]],
    [240, 'side', 0, [[376,227], [377,228], [380,230], [478,375], [459,372], [472,330]]],
    [240, 'front-three-quarter', Math.PI / 4, [[461,329], [466,342], [415,331]]],
  ];
  report.rays = [];
  report.scope = 'Unchanged raw diagnostic02; four visibility-only controls; original colors/materials retained. Rays use original delivered cameras; movies use wider camera to include hands and feet. Three separated five-frame windows are explicitly labeled, not a continuous whole-trajectory acceptance film.';
  for (const geometry of ['authored', 'riding']) for (const [index, view, yaw, pixels] of witnesses) {
    const rays = await page.evaluate(({index, geometry, yaw, pixels}) => {
      const r = window.__render, t = window.__rockhop, d = r.debug, a = window.__agent3, T = d.THREE;
      a.index = index; a.geometry = geometry; a.apply();
      r.setCameraOverride({mode:'orbit', yaw, pitch:.10, dist:4.5, x:a.target.x, y:a.target.y, screenX:.5, screenY:.5});
      r.invalidate(); t.render(true);
      const meshes = a.rider.sleeveGeometry.map(item => item.mesh);
      for (const mesh of meshes) { mesh.computeBoundingSphere(); mesh.computeBoundingBox(); }
      const edges = new Map();
      for (const mesh of meshes) {
        const ids = mesh.geometry.getAttribute('_source_id'), ix = mesh.geometry.index;
        const counts = new Map();
        for (let i=0;i<ix.count;i+=3) for (let j=0;j<3;j++) {
          const v = [ids.getX(ix.getX(i+j)), ids.getX(ix.getX(i+(j+1)%3))].sort((a,b)=>a-b).join(':');
          counts.set(v,(counts.get(v)??0)+1);
        }
        edges.set(mesh,counts);
      }
      const boundaryEdges = [];
      for (const mesh of meshes) if(mesh.name.includes('sweatshirt') && index===240) {
        const ids=mesh.geometry.getAttribute('_source_id'), first=new Map();
        for(let i=0;i<ids.count;i++) if(!first.has(ids.getX(i))) first.set(ids.getX(i),i);
        for(const [key,count]of edges.get(mesh)) if(count===1) {
          const source=key.split(':').map(Number);
          const points=source.map(id=>mesh.getVertexPosition(first.get(id),new T.Vector3()).applyMatrix4(mesh.matrixWorld));
          boundaryEdges.push({source,fileM:points.map(v=>v.clone().applyMatrix4(a.wrapper.clone().invert()).toArray()),pixel:points.map(v=>{const p=v.clone().project(d.rig.camera);return[(p.x+1)*480,(1-p.y)*320];})});
        }
      }
      return {camera:{world:d.rig.camera.matrixWorld.toArray(),projection:d.rig.camera.projectionMatrix.toArray()},riderWrapperWorld:a.wrapper.toArray(),boundaryEdges, materials:meshes.map(mesh=>({mesh:mesh.name,material:mesh.material.name,color:mesh.material.color.toArray(),side:mesh.material.side})), rays:pixels.map(([x,y]) => {
        const ray = new T.Raycaster(); ray.setFromCamera(new T.Vector2(x/960*2-1, 1-y/640*2),d.rig.camera);
        return {pixel:[x,y], hits:ray.intersectObjects(meshes,false).slice(0,8).map(hit=>{
          const mesh=hit.object, ids=mesh.geometry.getAttribute('_source_id'), g=mesh.geometry;
          const exported=[hit.face.a,hit.face.b,hit.face.c], source=exported.map(i=>ids.getX(i));
          const points=exported.map(i=>mesh.getVertexPosition(i,new T.Vector3()).applyMatrix4(mesh.matrixWorld));
          const normal=new T.Vector3().subVectors(points[1],points[0]).cross(new T.Vector3().subVectors(points[2],points[0])).normalize();
          return {mesh:mesh.name, triangle:hit.faceIndex, exported, source, distanceM:hit.distance,
            filePointM:hit.point.clone().applyMatrix4(a.wrapper.clone().invert()).toArray(),
            normalDotRay:normal.dot(ray.ray.direction), sourceEdgeFaceCounts:source.map((v,j)=>edges.get(mesh).get([v,source[(j+1)%3]].sort((a,b)=>a-b).join(':'))),
            weights:exported.map(i=>Array.from({length:4},(_,k)=>({joint:mesh.skeleton.bones[g.getAttribute('skinIndex').getComponent(i,k)].name,weight:g.getAttribute('skinWeight').getComponent(i,k)})))};
        })};
      })};
    }, {index,geometry,yaw,pixels});
    report.rays.push({index,timeS:index/48,view,geometry,...rays});
  }
  const anchors = new Map();
  const indices=[104,108,112,116,120,136,140,144,148,152,232,236,240,244,248];
  for (const geometry of ['authored','riding']) for (const isolation of ['all','without-boxers','without-body','without-body-boxers']) {
    const folder=path.join(out,geometry,isolation); fs.mkdirSync(folder,{recursive:true});
    for (let n=0;n<indices.length;n++) {
      const index=indices[n];
      const sample=await page.evaluate(({index,geometry,isolation})=>{
        const t=window.__rockhop,r=window.__render,d=r.debug,a=window.__agent3;
        a.index=index; a.geometry=geometry; a.apply();
        a.rider.scene.traverse(o=>{ if(o.isSkinnedMesh) o.visible=!(isolation.includes('boxers')&&o.name.includes('boxer'))&&!(isolation.includes('body')&&o.name.includes('Canonical_anatomical_body')); });
        r.setCameraOverride({mode:'orbit',yaw:Math.PI/4,pitch:.10,dist:6.0,x:a.target.x,y:a.target.y+.25,screenX:.5,screenY:.5});
        document.getElementById('agent3-label').textContent=`UNACCEPTED SURFACE ISOLATION | original PBR\n${geometry} | ${isolation} | shared t=${(index/48).toFixed(3)}s\nSeparate windows: elbows / overhead / crouch; no fit pass`;
        r.invalidate();t.render(true);
        let matrixMaxError=0; const inverse=a.wrapper.clone().invert();
        for(const [name,bone]of a.bones) matrixMaxError=Math.max(matrixMaxError,...inverse.clone().multiply(bone.matrixWorld).elements.map((v,k)=>Math.abs(v-a.driver.frames[index].jointWorldColumnMajor[name][k])));
        return {index,timeS:index/48,geometry,isolation,matrixMaxError,stateHash:t.hashState(),webdriver:navigator.webdriver,audioContexts:window.__agent3AudioCount,garage:r.debugInfo().garage.on,
          camera:{world:d.rig.camera.matrixWorld.toArray(),projection:d.rig.camera.projectionMatrix.toArray()},
          meshes:a.rider.sleeveGeometry.map(i=>({name:i.mesh.name,visible:i.mesh.visible,authoredSelected:i.mesh.geometry===i.authored,ridingSelected:i.mesh.geometry===i.riding}))};
      },{index,geometry,isolation});
      assert(sample.webdriver&&sample.garage&&sample.audioContexts===0&&sample.matrixMaxError<1e-5);
      const cameraKey=String(index);
      if(!anchors.has(cameraKey)) anchors.set(cameraKey,sample.camera);
      else assert.deepEqual(sample.camera,anchors.get(cameraKey),'Isolation/branch camera mismatch');
      assert.equal(sample.meshes.filter(m=>m.visible).length,isolation==='all'?4:isolation==='without-body-boxers'?2:3);
      await page.screenshot({path:path.join(folder,`${String(n).padStart(4,'0')}.png`)});report.samples.push(sample);
    }
    const movie=path.join(folder,'played.mp4');
    const ff=spawnSync('ffmpeg',['-v','error','-y','-framerate','12','-i',path.join(folder,'%04d.png'),'-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p','-an','-movflags','+faststart',movie],{encoding:'utf8'});
    assert.equal(ff.status,0,ff.stderr);report.clips.push({path:movie,sha256:sha(fs.readFileSync(movie)),frames:indices.length,fps:12,audio:false});
  }
  await Promise.all(loaded);
  assert(report.loaded.some(r => r.sha256 === driver.conditionedGLBSHA256 && r.status === 200));
  assert.equal(new Set(report.samples.map(s => s.stateHash)).size, 1, 'Physics changed during authored capture');
  assert.deepEqual(report.errors, []); report.status = 'CAPTURED_UNACCEPTED';
} catch (e) { report.failure = String(e); process.exitCode = 1; }
finally {
  fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  await context.close(); await browser.close(); await new Promise(resolve => server.httpServer.close(resolve));
  console.log(JSON.stringify({ status: report.status, frames: report.samples.length, clips: report.clips.length, failure: report.failure }));
}
