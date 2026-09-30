#!/usr/bin/env bash
# Rebuild the contact-corrected Hunyuan whole rider; no production paths mutate.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
cd "$REPO"
OUT=assets/blender/hero-remaster/rider
BLENDER_BIN=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
# The neural runs are intentionally a separate, expensive prerequisite.
test -f "$OUT/raw/hunyuan-42/street-apose.glb"
# Recover the reviewed donor after a different rider is promoted to public.
mkdir -p "$OUT/work"
if ! test -f "$OUT/work/source-baseline.glb"; then
  git show ec04192d61e39dcc8bdb80fd97842e8019ef4e55:public/models/rider-street-mustard.glb | python3 -c 'import sys; from pathlib import Path; Path("assets/blender/hero-remaster/rider/work/source-baseline.glb").open("xb").write(sys.stdin.buffer.read())'
fi
BASELINE_SHA=$(shasum -a 256 "$OUT/work/source-baseline.glb" | cut -d ' ' -f 1)
test "$BASELINE_SHA" = 11743d396b85b9e9d06f554e528886c7a093c4f30c6d958ae5750659491bc40c
node assets/blender/unpack_meshopt.mjs "$OUT/work/source-baseline.glb" "$OUT/work/baseline.glb"
"$BLENDER_BIN" -b --python-exit-code 1 --python "$OUT/authored_contacts.py"
"$BLENDER_BIN" -b --python-exit-code 1 --python "$OUT/fit_rider.py" -- \
 --input "$OUT/raw/hunyuan-42/street-apose.glb" --output "$OUT/candidate-v3.glb" --contacts
"$BLENDER_BIN" -b --python-exit-code 1 --python "$OUT/fit_rider.py" -- \
 --input "$OUT/raw/hunyuan-42/street-apose.glb" --output "$OUT/candidate-v3-lod.glb" --contacts --lod
node --input-type=module - <<'JS'
import fs from 'node:fs';
import {pack} from './assets/blender/hero_art_pack.mjs';
import {verifyRider} from './assets/blender/verify_hero_art.mjs';
const p='assets/blender/hero-remaster/rider';
for(const lod of [false,true]){
 const stem=`candidate-v3${lod?'-lod':''}`;
 await pack(`${p}/${stem}.glb`,`${p}/${stem}-packed.glb`,{stripSceneExtras:true});
 const proof=await verifyRider(`${p}/work/baseline.glb`,`${p}/${stem}-packed.glb`,{tris:lod?8000:60000,draws:8});
 fs.writeFileSync(`docs/evidence/hero-remaster/rider-generation/${stem}-contract.json`,JSON.stringify(proof,null,2)+'\n');
 console.log(JSON.stringify({file:stem,sha256:proof.sha256,bytes:proof.bytes,triangles:proof.triangles,draws:proof.draws}));
}
JS
