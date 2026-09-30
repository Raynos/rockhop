#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../.."
kit=assets/blender/course-kits/alpine-trees
dest=assets/blender/course-kits/alpine-trees/build
mkdir -p "$dest"
# Map bakes are explicit pinned inputs, independent of an adjacent checkout/cache.
for source in "$kit"/source/*; do
  name=$(basename "$source")
  cp "$source" "$dest/$name"
  size=256x256
  case "$name" in
    cards-*) size=512x256 ;;
    impostor-*) size=256x512 ;;
  esac
  magick "$source" -resize "$size" /tmp/rockhop-alpine-phone.png
  cwebp -quiet -q 82 -alpha_q 100 -exact -sharp_yuv /tmp/rockhop-alpine-phone.png -o "$dest/${name%.*}.phone.webp"
done
lockf -k "$HOME/projects/localai/.model.lock" /opt/homebrew/bin/blender -b --factory-startup -noaudio --python-exit-code 1 -P "$kit/build.py"
for source in "$dest"/*.raw.glb; do
  node /Users/raynos/projects/games/wildshard-singleplayer/node_modules/@gltf-transform/cli/bin/cli.js meshopt "$source" "${source/.raw.glb/.glb}" --level medium
  python3 "$kit/externalize.py" "${source/.raw.glb/.glb}"
  rm "$source"
done
node "$kit/verify.mjs"
