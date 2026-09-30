#!/usr/bin/env bash
# Invoke only after the parent releases the shared runtime/public freeze.
set -euo pipefail
cd "$(dirname "$0")/../../../.."
kit=assets/blender/course-kits/alpine-trees
dest=public/models/course-kits/alpine-trees
stage="$kit/stage"
mkdir -p "$stage"
cp "$kit/build/trees-full.phone.glb" "$stage/trees.glb"
cp "$kit/build/trees-near.phone.glb" "$stage/trees-lod.glb"
cp "$kit"/build/*.phone.webp "$stage/"
if [ -d "$dest" ]; then
  if [ -n "$(ls -A "$dest")" ]; then
    echo 'Existing staged Alpine assets require parent review before replacement.' >&2
    exit 1
  fi
  rmdir "$dest"
fi
mv "$stage" "$dest"
echo 'Staged one phone full/LOD pair and fourteen maps; no far geometry file.'
