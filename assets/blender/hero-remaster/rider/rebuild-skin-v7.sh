#!/usr/bin/env bash
# Rebuild the compact material finish from the exact committed wrist repair.
set -euo pipefail
SKIN_REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
cd "$SKIN_REPO"
SKIN_DIR=assets/blender/hero-remaster/rider
SKIN_EVIDENCE=docs/evidence/hero-remaster/rider-generation
mkdir -p "$SKIN_DIR/work"
node --input-type=module - <<'JS'
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
const ref='931ed3d8f10e749be22264796c152898fae69923';
for(const [suffix,hash] of [['','bbf2d63694fd22cfd32d719e3126710b2bb2bb0e5a3042e33286b57ef45b3e61'],['-lod','def6821d99fe7d73442735f1010bdd7e68bd2057d6de25643d91e31429aad72a']]){
 const bytes=execFileSync('git',['show',`${ref}:public/models/rider-street-mustard${suffix}.glb`],{maxBuffer:16*1024*1024});
 assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),hash);
 const file=`assets/blender/hero-remaster/rider/work/skin-v7-v6${suffix}.glb`;
 fs.writeFileSync(file,bytes);
 fs.writeFileSync(file+'.seams.json',execFileSync('git',['show',`${ref}:assets/blender/hero-remaster/delivery/rider-street-mustard${suffix}.glb.seams.json`],{maxBuffer:4*1024*1024}));
}
JS
node "$SKIN_DIR/finish_skin_v7.mjs" "$SKIN_DIR/work/skin-v7-v6.glb" "$SKIN_DIR/candidate-skin-v7b-packed.glb" --compact
node "$SKIN_DIR/finish_skin_v7.mjs" "$SKIN_DIR/work/skin-v7-v6-lod.glb" "$SKIN_DIR/candidate-skin-v7b-lod-packed.glb" --compact --palette="$SKIN_DIR/candidate-skin-v7b-packed.glb.json"
node --input-type=module - <<'JS'
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {verifyRider} from './assets/blender/verify_hero_art.mjs';
const dir='assets/blender/hero-remaster/rider',evidence='docs/evidence/hero-remaster/rider-generation';
for(const [suffix,hash] of [['','47b8825c02953110a24d13b8f280bc61bacaea5760501bf5f58b992e00e92c0e'],['-lod','1af88dd1f5d74db82650779c6c12849cc329759011b48b04bd922c500b013914']]){
 const file=`${dir}/candidate-skin-v7b${suffix}-packed.glb`,tier=suffix?'lod':'full';
 assert.equal(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),hash,'judged export hash must reproduce');
 const proof=await verifyRider(`${dir}/work/skin-v7-v6${suffix}.glb`,file,{tris:suffix?8000:60000,draws:8,allowGarageIdle:true});
 fs.writeFileSync(`${evidence}/skin-v7b-${tier}-contract.json`,JSON.stringify(proof,null,2)+'\n');
 fs.copyFileSync(file+'.json',`${evidence}/skin-v7b-${tier}-source-proof.json`);
 fs.copyFileSync(file+'.seams.json',`${evidence}/skin-v7b-${tier}-correspondence.json`);
}
JS
pnpm exec tsx harness/hero-remaster/wrist-seams.mts \
 --full="$SKIN_DIR/candidate-skin-v7b-packed.glb" --full-map="$SKIN_DIR/candidate-skin-v7b-packed.glb.seams.json" \
 --lod="$SKIN_DIR/candidate-skin-v7b-lod-packed.glb" --lod-map="$SKIN_DIR/candidate-skin-v7b-lod-packed.glb.seams.json" \
 --out="$SKIN_EVIDENCE/skin-v7b-seams.json"
pnpm exec tsx "$SKIN_DIR/skin_v7_memory.mts" "$SKIN_EVIDENCE/skin-v7-runtime-memory.json"
