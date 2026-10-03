/** Canonical loader-rest reference, not an art pose or moving acceptance. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../../src/render/hero/gltfTestUtils.ts';
import { makeBootSurfaces } from './boot-surfaces-runtime.mjs';
const [sourceFile,nativeFile,outDir]=process.argv.slice(2);assert(outDir&&!fs.existsSync(outDir));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),source=fs.readFileSync(sourceFile),native=fs.readFileSync(nativeFile);
assert.equal(sha(source),'780983f4887f66b18dbf7a4643cb3a80f5241071124129bab3cf9e5d4b0abb8e');
assert.equal(sha(native),'5e36f665d8d80bff522abb970512d1ccc126a9b497ed3eda3411cab2b2b3da24');
const g=await loadRigAt(pathToFileURL(path.resolve(sourceFile)),true);g.scene.updateMatrixWorld(true);
const measurement=makeBootSurfaces({THREE,rider:{scene:g.scene}},JSON.parse(native));
const positions=new Float64Array(measurement.sample()),bytes=Buffer.from(positions.buffer);fs.mkdirSync(outDir,{recursive:true});fs.writeFileSync(path.join(outDir,'positions.f64'),bytes);
fs.writeFileSync(path.join(outDir,'receipt.json'),JSON.stringify({status:'CANONICAL_SOURCE09_LOADER_REST_REFERENCE_ONLY',sourceSHA256:sha(source),nativeSHA256:sha(native),positionsSHA256:sha(bytes),actualBoot:measurement.contract,
  limits:['Independent rest surface reference, not posed film or motion/shape acceptance. Upper/outsole assembly overlap is intentional in source09 construction; body contact remains separate.']},null,2)+'\n');
