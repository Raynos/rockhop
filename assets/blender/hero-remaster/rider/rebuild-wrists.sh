#!/usr/bin/env bash
# Rebuild bounded V6 surface repair over the retained V5 uncompressed masters.
set -euo pipefail
REPO=$(cd "$(dirname "$0")/../../../.." && pwd)
cd "$REPO"
WRIST_DIR=assets/blender/hero-remaster/rider
BLENDER_BIN=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
# Masters are outputs of rebuild.sh + rebuild-head.sh with the same UniMate
# optional idle appended. They are ignored local art working files, not weights.
# Fail explicitly if a different neural/head source would be repaired silently.
test "$(shasum -a 256 "$WRIST_DIR/candidate-v5.glb" | cut -d ' ' -f 1)" = 9745955fcaeee25a6c30a5b40f6d620a732fa9b7faf762d8efc26e44331b24e6
test "$(shasum -a 256 "$WRIST_DIR/candidate-v5-lod.glb" | cut -d ' ' -f 1)" = b696cda1f89a41ed3975516513ad295e1cf9c4a641337ae92cfb11d23951c12b
mkdir -p "$WRIST_DIR/work"
"$BLENDER_BIN" -b --python-exit-code 1 --python "$WRIST_DIR/repair_wrists.py" -- \
 --input "$WRIST_DIR/candidate-v5.glb" --out "$WRIST_DIR/work/wrist-repair.glb"
node "$WRIST_DIR/graft_wrists.mjs" "$WRIST_DIR/candidate-v5.glb" \
 "$WRIST_DIR/work/wrist-repair.glb" "$WRIST_DIR/candidate-v6.glb"
node "$WRIST_DIR/pack_wrists.mjs" "$WRIST_DIR/candidate-v6.glb" "$WRIST_DIR/candidate-v6-packed.glb"
"$BLENDER_BIN" -b --python-exit-code 1 --python "$WRIST_DIR/rebuild_lod_body.py" -- \
 --input "$WRIST_DIR/candidate-v6.glb" --seams "$WRIST_DIR/candidate-v6.glb.seams.json" \
 --out "$WRIST_DIR/work/clean-lod-body.glb"
node "$WRIST_DIR/graft_lod_body.mjs" "$WRIST_DIR/candidate-v5-lod.glb" \
 "$WRIST_DIR/work/clean-lod-body.glb" "$WRIST_DIR/work/clean-lod-source.glb"
"$BLENDER_BIN" -b --python-exit-code 1 --python "$WRIST_DIR/repair_wrists.py" -- \
 --input "$WRIST_DIR/work/clean-lod-source.glb" --out "$WRIST_DIR/work/wrist-repair-lod.glb" --lod
node "$WRIST_DIR/graft_wrists.mjs" "$WRIST_DIR/work/clean-lod-source.glb" \
 "$WRIST_DIR/work/wrist-repair-lod.glb" "$WRIST_DIR/candidate-v6-lod.glb"
node "$WRIST_DIR/pack_wrists.mjs" "$WRIST_DIR/candidate-v6-lod.glb" "$WRIST_DIR/candidate-v6-lod-packed.glb"
# These hashes name the exports judged in the parent engine movies and audit.
test "$(shasum -a 256 "$WRIST_DIR/candidate-v6-packed.glb" | cut -d ' ' -f 1)" = bbf2d63694fd22cfd32d719e3126710b2bb2bb0e5a3042e33286b57ef45b3e61
test "$(shasum -a 256 "$WRIST_DIR/candidate-v6-lod-packed.glb" | cut -d ' ' -f 1)" = def6821d99fe7d73442735f1010bdd7e68bd2057d6de25643d91e31429aad72a
node --input-type=module - <<'JS'
import fs from 'node:fs';
import {verifyRider} from './assets/blender/verify_hero_art.mjs';
for(const lod of [false,true]){
 const stem=`candidate-v6${lod?'-lod':''}`;
 const proof=await verifyRider('assets/blender/hero-remaster/rider/work/baseline.glb',`assets/blender/hero-remaster/rider/${stem}-packed.glb`,{tris:lod?8000:60000,draws:8,allowGarageIdle:true});
 fs.writeFileSync(`docs/evidence/hero-remaster/rider-generation/${stem}-contract.json`,JSON.stringify(proof,null,2)+'\n');
}
JS
"$BLENDER_BIN" -b --python-exit-code 1 --python "$WRIST_DIR/compare_lod.py" -- \
 --before "$WRIST_DIR/candidate-v5-lod.glb" --after "$WRIST_DIR/candidate-v6-lod.glb" \
 --out docs/evidence/hero-remaster/rider-generation/v6-lod-deviation.json
