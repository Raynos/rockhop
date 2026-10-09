#!/usr/bin/env node
// Validate actual pinned Three.js 0.186.1 transcoder, without browser/audio/app changes.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const out = path.resolve(process.argv[2] || 'harness/out/rider-rebuild/download-opt01/textures01');
const variant = process.argv[3] || 'uastc';
const selected = process.argv[4] ? new Set(process.argv[4].split(',').map(Number)) : null;
const root = path.resolve('node_modules/three/examples/jsm/libs/basis');
const jsPath = path.join(root, 'basis_transcoder.js');
const require = createRequire(import.meta.url);
const source = fs.readFileSync(jsPath, 'utf8');
const factory = new Function('require', '__dirname', '__filename', `${source}\nreturn BASIS;`)(require,root,jsPath);
const module = await factory({ wasmBinary: fs.readFileSync(path.join(root,'basis_transcoder.wasm')) });
module.initializeBasis();
const rows = [];
fs.mkdirSync(path.join(out,`${variant}-decoded-rgba`), {recursive:true});
fs.mkdirSync(path.join(out,`${variant}-astc-blocks`), {recursive:true});
for (const map of JSON.parse(fs.readFileSync(path.join(out,`${variant}-encode.json`),'utf8'))) {
  if (selected && !selected.has(map.image)) continue;
  const file = new module.KTX2File(fs.readFileSync(map.path));
  if (!file.isValid() || !file.isUASTC() || !file.startTranscoding()) throw new Error(`Invalid map ${map.image}`);
  const formats = [{name:'ASTC4x4',code:10},{name:'BC7',code:7},{name:'RGBA32',code:13}];
  const row = {image:map.image,width:file.getWidth(),height:file.getHeight(),levels:file.getLevels(),hasAlpha:file.getHasAlpha(),formats:[]};
  for (const format of formats) {
    let bytes=0;
    for (let level=0;level<file.getLevels();level++) {
      const dst = new Uint8Array(file.getImageTranscodedSizeInBytes(level,0,0,format.code));
      if (!file.transcodeImage(dst,level,0,0,format.code,0,-1,-1)) throw new Error(`Transcode ${map.image}/${format.name}/${level}`);
      bytes+=dst.byteLength;
      if (format.code===10) fs.writeFileSync(path.join(out,`${variant}-astc-blocks`,`image-${String(map.image).padStart(2,'0')}-level-${level}.blocks`),dst);
      if (format.code===13 && level===0) fs.writeFileSync(path.join(out,`${variant}-decoded-rgba`,`image-${String(map.image).padStart(2,'0')}.rgba`),dst);
    }
    row.formats.push({name:format.name,totalMipBytes:bytes,allLevelsSucceeded:true});
  }
  file.close();file.delete();
  rows.push(row);
  fs.writeFileSync(path.join(out,`${variant}-runtime-transcode.json`),`${JSON.stringify(rows,null,2)}\n`);
  console.log(JSON.stringify(row));
}
