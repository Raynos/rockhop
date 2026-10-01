/** CPU reproduction of actual recorded states; no geometry or physical inputs changed. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { build } from 'vite';
import { patchNewRiderSource } from './new-rider-private-adapter.mjs';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils';
import { prepareHero } from '../../src/render/hero/lod';
import { GltfBike } from '../../src/render/hero/gltfBike';
import { decodeJSON, expandFrames } from '../../src/core/replay';
import { createSimFor } from '../lib/sim';
import { FrameBuilder } from '../../src/render/frame';
import type { PhysicsState } from '../../src/core/types';
import type { MaterialLibrary } from '../../src/render/materials/library';
const out=path.resolve('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind05/pole-audit01');fs.mkdirSync(out,{recursive:true});
const captured=JSON.parse(fs.readFileSync('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind05/played02/body/report.json','utf8'));
const recording=decodeJSON(fs.readFileSync('docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json','utf8'));
const inputs=expandFrames(recording),node=await createSimFor(recording),samplesByTick=new Map<number, {hash:string}>(captured.samples.map((r:{tick:number;hash:string})=>[r.tick,r]));
let exactHashes=0;for(let tick=1;tick<=inputs.length;tick++){node.step(inputs[tick-1]!);const sample=samplesByTick.get(tick);if(sample){assert.equal(sample.hash,node.hash());exactHashes++;}}assert.equal(exactHashes,480);
const instrumentation=`if (this.newRiderHandTargetQ.size) {
          const dbg = this.debug as typeof this.debug & { privatePole?: unknown[] };
          dbg.privatePole ??= []; dbg.privatePole[i] = { beforeNormalizeLengthSquared: pole.lengthSq(), directionDot: pole.clone().normalize().dot(dir) };
        }
        pole.normalize();`;
// Existing CPU fixture convention: omit only canvas drawing for tyre blobs.
(globalThis as unknown as { document: unknown }).document = { createElement: () => ({ width: 128, height: 64, getContext: () => ({ createRadialGradient: () => ({ addColorStop() {} }), scale() {}, fillRect() {} }) }) };
const results=[];
for(const variant of ['baseline','orthogonal-private-candidate']){
 const dir=path.resolve('harness/out/hero-remaster/pole-audit-'+variant);
 await build({configFile:false,publicDir:false,logLevel:'error',build:{ssr:'src/render/hero/gltfRider.ts',outDir:dir,emptyOutDir:true,minify:false,rollupOptions:{external:['three',/^three\//],output:{entryFileNames:'rider.mjs'}}},plugins:[{name:'private-pole-audit',enforce:'pre',transform(code,id){if(!id.toLowerCase().endsWith('/src/render/hero/gltfrider.ts'))return null;const s=patchNewRiderSource(code,variant!=='baseline');const a='        pole.normalize();';assert.equal(s.split(a).length,2);return{code:s.replace(a,instrumentation),map:null};}}]});
 const {GltfRider}=await import(pathToFileURL(dir+'/rider.mjs').href),lib={complete(){}} as unknown as MaterialLibrary;
 const bg=await loadRigAt(pathToFileURL(path.resolve('public/models/bike-rookie.glb')),true);await prepareHero(bg);const bike=new GltfBike(bg,lib);
 const g=await loadRigAt(pathToFileURL('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind05/rider.glb'),true);await prepareHero(g);const rider=new GltfRider(g,lib);rider.attach(bike);const fb=new FrameBuilder(),rows=[];
 for(const sample of captured.samples){
  const before=JSON.stringify(sample.state),f=fb.build(sample.state as PhysicsState,1);bike.update(f);rider.update(f);rider.update(f);bike.root.updateMatrixWorld(true);assert.equal(JSON.stringify(sample.state),before);
  rows.push({i:sample.i,tick:sample.tick,gripErrM:[...rider.debug.gripErr],soleErrM:[...rider.debug.soleErr],handOnGrip:[...rider.debug.handOnGrip],privatePole:structuredClone(rider.debug.privatePole),physicalInputUnchanged:true});
 }
 const summary={variant,frames:rows.length,maxGripM:Math.max(...rows.flatMap(r=>r.gripErrM)),maxSoleM:Math.max(...rows.flatMap(r=>r.soleErrM)),failedFrames:rows.filter(r=>r.gripErrM.some(x=>x>.001))};
 results.push({summary,rows});
}
assert(results[0]!.summary.failedFrames.length===5,'Reproduce actual five failures');assert(results[1]!.summary.failedFrames.length===0,'Candidate removes numerical failures');
fs.writeFileSync(out+'/report.json',JSON.stringify({exactPhysicsHashes:exactHashes,results,scope:'Actual recorded states replayed through production decoder/prepareHero/GltfBike/GltfRider; CPU only, not new moving rendered acceptance'},null,2)+'\n');console.log(JSON.stringify(results.map(r=>r.summary)));
