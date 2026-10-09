// Actual pinned WASM formats used by r186 loader for ETC1S, no browser.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const out=path.resolve(process.argv[2]);
const root=path.resolve('node_modules/three/examples/jsm/libs/basis');
const jsPath=path.join(root,'basis_transcoder.js'),require=createRequire(import.meta.url);
const factory=new Function('require','__dirname','__filename',`${fs.readFileSync(jsPath,'utf8')}\nreturn BASIS;`)(require,root,jsPath);
const module=await factory({wasmBinary:fs.readFileSync(path.join(root,'basis_transcoder.wasm'))});module.initializeBasis();
const rows=[];
fs.mkdirSync(path.join(out,'etc1s-max-decoded-rgba'),{recursive:true});
fs.mkdirSync(path.join(out,'etc1s-max-etc-blocks'),{recursive:true});
for(const map of JSON.parse(fs.readFileSync(path.join(out,'etc1s-max-encode.json')))){
 const file=new module.KTX2File(fs.readFileSync(map.path));
 assert(file.isValid()&&!file.isUASTC()&&file.startTranscoding());
 const row={image:map.image,width:file.getWidth(),height:file.getHeight(),levels:file.getLevels(),hasAlpha:file.getHasAlpha(),formats:[]};
 for(const format of [{name:'ETC2_RGB_via_ETC1',code:0},{name:'ETC2_RGBA',code:1},{name:'BC7',code:7},{name:'RGBA32',code:13}]){
  let bytes=0;
  for(let level=0;level<file.getLevels();level++){
   const data=new Uint8Array(file.getImageTranscodedSizeInBytes(level,0,0,format.code));
   assert(file.transcodeImage(data,level,0,0,format.code,0,-1,-1));bytes+=data.byteLength;
   if(format.code===0)fs.writeFileSync(path.join(out,'etc1s-max-etc-blocks',`image-${String(map.image).padStart(2,'0')}-level-${level}.blocks`),data);
   if(format.code===13&&level===0)fs.writeFileSync(path.join(out,'etc1s-max-decoded-rgba',`image-${String(map.image).padStart(2,'0')}.rgba`),data);
  }
  row.formats.push({name:format.name,allLevelsSucceeded:true,totalMipBytes:bytes});
 }
 rows.push(row);file.close();file.delete();
}
fs.writeFileSync(path.join(out,'etc1s-max-runtime-transcode.json'),JSON.stringify(rows,null,2)+'\n');console.log(JSON.stringify(rows));
