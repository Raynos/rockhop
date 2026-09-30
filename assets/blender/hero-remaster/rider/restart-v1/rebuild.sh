#!/usr/bin/env bash
# New source generation + whole rider export. Never writes public or game code.
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
"$BLENDER_BIN" -b --factory-startup --python-exit-code 1 --python "$OUT/build_whole.py" -- --output "$OUT/whole-rider-v1a.glb"
"$BLENDER_BIN" -b --factory-startup --python-exit-code 1 --python "$OUT/build_whole.py" -- --lod --output "$OUT/whole-rider-v1a-lod.glb"
node "$OUT/pack_verify.mjs" whole-rider-v1a
python3 - <<'PY'
import hashlib,pathlib,json
p=pathlib.Path('assets/blender/hero-remaster/rider/restart-v1')
expected={'whole-rider-v1a-packed.glb':'d0a1533a8ab6d24335f7da41f67e1c6ed727975b665760e9cb462123dd75156c','whole-rider-v1a-lod-packed.glb':'92a009adcc1e37c51fbbe5594b69ec67a019d134ce5b3d69eb56db6c85d0ae94'}
for f,sha in expected.items():
 actual=hashlib.sha256((p/f).read_bytes()).hexdigest()
 assert actual==sha,(f,actual,sha)
print(json.dumps({'status':'frozen unaccepted shape candidate reproduced','hashes':expected}))
PY
