#!/usr/bin/env bash
# Frozen second fresh-whole-rider fit. Never overwrites v1/v1a candidates.
set -euo pipefail
REPO_DIR=$(cd "$(dirname "$0")/../../../../.." && pwd)
cd "$REPO_DIR"
OUT=assets/blender/hero-remaster/rider/restart-v1
BLENDER_BIN=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
git show ec04192d61e39dcc8bdb80fd97842e8019ef4e55:public/models/rider-street-mustard.glb > "$OUT/rig-source-packed.glb"
RIG_SHA=$(shasum -a 256 "$OUT/rig-source-packed.glb" | cut -d ' ' -f 1)
test "$RIG_SHA" = 11743d396b85b9e9d06f554e528886c7a093c4f30c6d958ae5750659491bc40c
node assets/blender/unpack_meshopt.mjs "$OUT/rig-source-packed.glb" "$OUT/rig-source-decoded.glb"
"$BLENDER_BIN" -b --factory-startup --python-exit-code 1 --python "$OUT/probe_fresh_base.py"
"$BLENDER_BIN" -b --factory-startup --python-exit-code 1 --python "$OUT/build_whole_v2.py" -- --output "$OUT/whole-rider-v2.glb"
"$BLENDER_BIN" -b --factory-startup --python-exit-code 1 --python "$OUT/build_whole_v2.py" -- --lod --output "$OUT/whole-rider-v2-lod.glb"
node "$OUT/pack_verify_v2.mjs"
pnpm exec tsx "$OUT/audit_surfaces.mts" whole-rider-v2
python3 - <<'PY'
import hashlib,pathlib,json
p=pathlib.Path('assets/blender/hero-remaster/rider/restart-v1')
expected={'whole-rider-v2-packed.glb':'89935b89694861b138c3f51abb6294b32749e1ed1b696249652239735a1cd629','whole-rider-v2-lod-packed.glb':'045c06a39691431badc0c3b5a5a94d63942c7949d7bad8a96581b062e8d41847'}
for f,sha in expected.items():
 actual=hashlib.sha256((p/f).read_bytes()).hexdigest()
 assert actual==sha,(f,actual,sha)
print(json.dumps({'status':'unaccepted v2 whole fit reproduced','hashes':expected}))
PY
