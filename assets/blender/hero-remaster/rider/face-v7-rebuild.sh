#!/usr/bin/env bash
# Head-only authored candidate. Rebuild does not promote any public model.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
cd "$REPO"
FACE_DIR=assets/blender/hero-remaster/rider
BLENDER_BIN=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
test "$(shasum -a 256 "$FACE_DIR/candidate-v6.glb" | cut -d ' ' -f 1)" = a6901b4e1d0d830814d1772de5dc3b7f5a7c9ca06e3a0be24904fab449a1638c
test "$(shasum -a 256 "$FACE_DIR/candidate-v6-lod.glb" | cut -d ' ' -f 1)" = 3f2977797331078df93e41774e097868116ce826ac7eb46a805c77e1172d6482
for TIER in full lod; do
  SOURCE_SUFFIX=''; DETAIL_ARGS=()
  if test "$TIER" = lod; then SOURCE_SUFFIX=-lod; DETAIL_ARGS=(--lod); fi
  SOURCE="$FACE_DIR/candidate-v6${SOURCE_SUFFIX}.glb"
  "$BLENDER_BIN" -b --python-exit-code 1 --python "$FACE_DIR/face-v7-build.py" -- \
    --input "$SOURCE" --out "$FACE_DIR/face-v7-$TIER-donor.glb" ${DETAIL_ARGS[@]+"${DETAIL_ARGS[@]}"}
  node "$FACE_DIR/face-v7-graft.mjs" "$SOURCE" "$FACE_DIR/face-v7-$TIER-donor.glb" "$FACE_DIR/face-v7-$TIER.glb"
  node "$FACE_DIR/pack_wrists.mjs" "$FACE_DIR/face-v7-$TIER.glb" "$FACE_DIR/face-v7-$TIER-packed.glb"
done
node --input-type=module - <<'JS'
import fs from 'node:fs';
import {verifyRider} from './assets/blender/verify_hero_art.mjs';
for(const tier of ['full','lod']){
 const proof=await verifyRider('assets/blender/hero-remaster/rider/work/baseline.glb',`assets/blender/hero-remaster/rider/face-v7-${tier}-packed.glb`,{tris:tier==='full'?60000:8000,draws:8,allowGarageIdle:true});
 fs.writeFileSync(`docs/evidence/hero-remaster/rider-generation/face-v7-${tier}-contract.json`,JSON.stringify(proof,null,2)+'\n');
}
JS
test "$(shasum -a 256 "$FACE_DIR/face-v7-full-packed.glb" | cut -d ' ' -f 1)" = cbbaa485422b7a4e10551104e8ab23ec09ed476266074a0a14062a0150c5f277
test "$(shasum -a 256 "$FACE_DIR/face-v7-lod-packed.glb" | cut -d ' ' -f 1)" = 2b84ca8ab4520c83f4945905c17890f93a2ae77f058202fda8fad7039265ae29
