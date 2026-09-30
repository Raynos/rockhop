#!/usr/bin/env bash
# Bounded authored head round over rebuilt v3 geometry; no neural rerun.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
cd "$REPO"
OUT=assets/blender/hero-remaster/rider
BLENDER_BIN=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
for SUFFIX in '' '-lod'; do
  LOD_ARGS=()
  if test -n "$SUFFIX"; then LOD_ARGS+=(--lod); fi
  "$BLENDER_BIN" -b --python-exit-code 1 --python "$OUT/refine_head.py" -- \
    --input "$OUT/candidate-v3$SUFFIX.glb" --out "$OUT/work/head-detail$SUFFIX.glb" "${LOD_ARGS[@]}"
  node "$OUT/graft_head.mjs" "$OUT/candidate-v3$SUFFIX.glb" \
    "$OUT/work/head-detail$SUFFIX.glb" "$OUT/work/candidate-v5$SUFFIX-six.glb"
done
node --input-type=module - <<'JS'
import fs from 'node:fs';
import {pack} from './assets/blender/hero_art_pack.mjs';
import {verifyRider} from './assets/blender/verify_hero_art.mjs';
const p='assets/blender/hero-remaster/rider';
for(const lod of [false,true]){
 const stem=`candidate-v5${lod?'-lod':''}`;
 await pack(`${p}/work/${stem}-six.glb`,`${p}/work/${stem}-six-packed.glb`,{stripSceneExtras:true});
 const proof=await verifyRider(`${p}/work/baseline.glb`,`${p}/work/${stem}-six-packed.glb`,{tris:lod?8000:60000,draws:8});
 fs.writeFileSync(`docs/evidence/hero-remaster/rider-generation/${stem}-six-contract.json`,JSON.stringify(proof,null,2)+'\n');
}
JS
# Append the same UniMate idle after packing. The merger retains every source
# byte and all original clip descriptors; its unused idle samplers are valid
# glTF but cannot be sent back through the common packer's sampler role check.
# The matching generated GT/donor and decoder paths are supplied by the caller.
if test -n "${UNIMATE_GT:-}" && test -n "${UNIMATE_DONOR:-}" && test -n "${MESHOPT_DECODER:-}"; then
  for SUFFIX in '' '-lod'; do
    node "$HOME/projects/localai/bin/unimate/merge_idle.mjs" \
      "$OUT/work/candidate-v5$SUFFIX-six-packed.glb" "$UNIMATE_GT" "$UNIMATE_DONOR" \
      "$OUT/candidate-v5$SUFFIX-packed.glb" "$MESHOPT_DECODER"
    node "$HOME/projects/localai/bin/unimate/merge_idle.mjs" \
      "$OUT/work/candidate-v5$SUFFIX-six.glb" "$UNIMATE_GT" "$UNIMATE_DONOR" \
      "$OUT/candidate-v5$SUFFIX.glb" "$MESHOPT_DECODER"
  done
  node --input-type=module - <<'JS'
import fs from 'node:fs';
import {verifyRider} from './assets/blender/verify_hero_art.mjs';
const p='assets/blender/hero-remaster/rider';
for(const lod of [false,true]){
 const stem=`candidate-v5${lod?'-lod':''}`;
 const proof=await verifyRider(`${p}/work/baseline.glb`,`${p}/${stem}-packed.glb`,{tris:lod?8000:60000,draws:8,allowGarageIdle:true});
 fs.writeFileSync(`docs/evidence/hero-remaster/rider-generation/${stem}-contract.json`,JSON.stringify(proof,null,2)+'\n');
}
JS
else
  echo 'Geometry verified; set UNIMATE_GT, UNIMATE_DONOR and MESHOPT_DECODER to append the original optional idle.'
fi
