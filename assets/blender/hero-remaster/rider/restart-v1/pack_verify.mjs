/** Pack this wholly rebuilt rider and verify the preserved numeric rig. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pack } from '../../../hero_art_pack.mjs';
import { verifyRider } from '../../../verify_hero_art.mjs';
const dir=path.dirname(new URL(import.meta.url).pathname);
const revision=process.argv[2] ?? 'whole-rider-v1a';
for(const lod of [false,true]){
 const stem=`${revision}${lod?'-lod':''}`;
 await pack(`${dir}/${stem}.glb`,`${dir}/${stem}-packed.glb`,{stripSceneExtras:true});
 const proof=await verifyRider(`${dir}/rig-source-decoded.glb`,`${dir}/${stem}-packed.glb`,{tris:lod?8000:60000,draws:8});
 proof.status='UNACCEPTED whole-body candidate; numeric rig checks are not visual/contact-surface acceptance';
 proof.recipeSHA256=crypto.createHash('sha256').update(fs.readFileSync(`${dir}/build_whole.py`)).digest('hex');
 fs.writeFileSync(`docs/evidence/hero-remaster/restart/${revision}-${lod?'lod':'full'}-contract.json`,JSON.stringify(proof,null,2)+'\n');
 console.log(JSON.stringify(proof));
}
