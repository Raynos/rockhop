/** Verify the selected stable packages and execute actual soft-body response. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import * as RAPIER from '@dimforge/rapier3d-compat';
const require=createRequire(import.meta.url),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const [outFile]=process.argv.slice(2);assert(outFile&&!fs.existsSync(outFile));
const packages={};
for(const name of ['@dimforge/rapier3d-compat','three','@types/three']){
  const registry=await (await fetch('https://registry.npmjs.org/'+encodeURIComponent(name))).json();
  const installedFile=name==='@types/three'?require.resolve(name+'/package.json'):path.resolve(path.dirname(require.resolve(name)),name==='three'?'../package.json':'../package.json');
  const bytes=fs.readFileSync(installedFile),installed=JSON.parse(bytes),latest=registry['dist-tags'].latest;
  assert.equal(installed.version,latest);
  packages[name]={installed:installed.version,stable:latest,tags:registry['dist-tags'],published:registry.time[latest],
    integrity:registry.versions[latest].dist.integrity,tarball:registry.versions[latest].dist.tarball,installedMetadataSHA256:sha(bytes)};
}
await RAPIER.init();assert.equal(RAPIER.version(),'0.21.0');
const actualExports={};
for(const [name,value] of Object.entries({SoftBodyDesc:RAPIER.SoftBodyDesc,SoftBody:RAPIER.SoftBody,SoftMeshBinding:RAPIER.SoftMeshBinding,World:RAPIER.World})){assert(value);actualExports[name]=typeof value;}
for(const name of ['trimesh','cloth','clothTube'])assert.equal(typeof RAPIER.SoftBodyDesc[name],'function');
for(const name of ['setSelfContacts','setSurfaceCollider','setNoSurfaceCollider','setEdges','setShapeMatching'])assert.equal(typeof RAPIER.SoftBodyDesc.prototype[name],'function');
for(const name of ['setParticleKinematicTarget','particlePositions','setParticlePinned'])assert.equal(typeof RAPIER.SoftBody.prototype[name],'function');
assert.equal(typeof RAPIER.World.prototype.createDeformableCollider,'function');
function response(collision){
  const world=new RAPIER.World({x:0,y:-9.81,z:0});world.timestep=1/120;
  world.createCollider(RAPIER.ColliderDesc.cuboid(2,.05,2).setTranslation(0,-.05,0));
  let desc=RAPIER.SoftBodyDesc.cloth({x:-.1,y:.2,z:-.1},{x:.05,y:0,z:0},{x:0,y:0,z:.05},5,5)
    .setShapeMatching(false).setSelfContacts(collision).setParticleRadius(.003).setSoftness(12,1);
  desc=collision?desc.setSurfaceCollider(RAPIER.ColliderDesc.ball(.003).setFriction(.3)):desc.setNoSurfaceCollider();
  const body=world.createSoftBody(desc),initial=body.particlePositions(),frames=[];
  for(let tick=0;tick<120;tick++){world.step();const p=body.particlePositions();assert(p.every(Number.isFinite));frames.push(sha(Buffer.from(p.buffer,p.byteOffset,p.byteLength)));}
  const p=body.particlePositions(),minY=Math.min(...Array.from(p).filter((_,i)=>i%3===1));
  const result={collision,particles:body.numParticles(),edges:body.numEdges(),initialSHA256:sha(Buffer.from(initial.buffer,initial.byteOffset,initial.byteLength)),
    ticks:120,timestep:world.timestep,minY,frameHashesSHA256:sha(Buffer.from(frames.join('\n'))),finalSHA256:sha(Buffer.from(p.buffer,p.byteOffset,p.byteLength))};
  world.free();return result;
}
const off=response(false),on=response(true);assert.equal(off.initialSHA256,on.initialSHA256);assert(off.minY<-1&&on.minY>.002);
assert.deepEqual(on,response(true));assert.deepEqual(off,response(false));
const otherRoot='/Users/raynos/projects/games/wildshard-singleplayer',otherFiles={};
for(const file of ['AGENTS.md','package.json','pnpm-lock.yaml','src/engine/physics/rapier.ts','vite/rapier.ts'])otherFiles[file]=sha(fs.readFileSync(path.join(otherRoot,file)));
const other=JSON.parse(fs.readFileSync(path.join(otherRoot,'package.json')));
const files=['package.json','pnpm-lock.yaml','src/physics/v2/engine.ts','src/render/hero/GltfRider.ts'];
const report={status:'LATEST_STABLE_DEPENDENCIES_VERIFIED_ISOLATED_CLOTH_RESPONSE_ONLY',checkedUTC:new Date().toISOString(),packages,actualExports,
  actualRapierVersion:RAPIER.version(),pairedGravityFloorSmoke:{off,on,repeatedAllParticleFrameHashesExact:true},
  readOnlyWildshard:{files:otherFiles,rapier:other.dependencies['@dimforge/rapier3d-simd'],three:other.dependencies.three,
    loader:'SIMD with existing custom WASM alias and streaming loader. Inspected only; no files modified.'},
  currentFiles:Object.fromEntries(files.map(f=>[f,sha(fs.readFileSync(f))])),
  priorRapier:'0.12.0 remains a @types/three transitive dependency; it was not used by the ordinary game.',
  sources:['https://registry.npmjs.org/@dimforge%2Frapier3d-compat','https://registry.npmjs.org/three',
    'https://github.com/dimforge/rapier/blob/master/CHANGELOG.md#v0360-24-september-2026',
    'https://rapier.rs/docs/user_guides/javascript/soft_bodies/','https://rapier.rs/docs/user_guides/javascript/soft_body_deformable_colliders/'],
  limits:['The smoke uses 25 particles and a floor. It proves consumed collision changes vertices, not sleeve clearance, fit or mobile performance.',
    'Ordinary production bike physics has no Rapier import. The new cloth path is private until validated.',
    'Compat includes base64 WASM; mobile load/memory cost and SIMD comparison are still unmeasured.',
    'No physical iPhone result, phone deployment or clothing acceptance is claimed.']};
fs.mkdirSync(path.dirname(outFile),{recursive:true});fs.writeFileSync(outFile,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,packages:Object.fromEntries(Object.entries(packages).map(([n,p])=>[n,p.installed])),offMinY:off.minY,onMinY:on.minY}));
