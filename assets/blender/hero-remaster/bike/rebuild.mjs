/** Rebuild only candidate assets, never public/models or runtime catalogs. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { pack } from '../../hero_art_pack.mjs';
import { verifyBike } from '../../verify_hero_art.mjs';
import { glbStats } from '../../glb_stats.mjs';
const root=path.resolve(new URL('../../../..',import.meta.url).pathname);
const dir=path.dirname(new URL(import.meta.url).pathname);
const evidence=path.join(root,'docs/evidence/hero-remaster/bike');
const blender=process.env.BLENDER??'/Applications/Blender.app/Contents/MacOS/Blender';
const digest=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const run=(bin,args)=>{const r=spawnSync(bin,args,{cwd:root,encoding:'utf8',maxBuffer:64*1024*1024});if(r.status!==0)throw new Error(r.stdout+'\n'+r.stderr);return r.stdout;};
fs.mkdirSync(evidence,{recursive:true});
const BASE_REF='ec04192d';
const baselineHashes={
 'rookie':'e55919d60267849358ef5e97f4731f42fac6eb2835b9998e1d146d056c0f10f7',
 'pro':'0acc9ac86eeca76cc1812f8870eab36e2e25ca76d6a5cbe86d4a46a36cc12a86',
 'rookie-lod':'4ec26ad0a0c08f7ec7e466523b77b4dd5f6378e9b389fade140eb7d08418d36b',
 'pro-lod':'37455064bf7b6012d67e99454cefced5a1aceac3747796f11cdcfe839436a2b7',
};
const reports=[];
for(const variant of ['rookie','pro'])for(const lod of [false,true]){
 const suffix=lod?'-lod':'';
 const source=path.join(dir,`scratch/pinned-baseline/bike-${variant}${suffix}.glb`);
 fs.mkdirSync(path.dirname(source),{recursive:true});
 const frozen=spawnSync('git',['show',`${BASE_REF}:public/models/bike-${variant}${suffix}.glb`],{cwd:root,maxBuffer:64*1024*1024});
 if(frozen.status!==0)throw new Error(frozen.stderr.toString());
 fs.writeFileSync(source,frozen.stdout);
 if(digest(source)!==baselineHashes[variant+suffix])throw new Error('Pinned baseline hash mismatch');
 const decoded=path.join(dir,`baseline-${variant}${suffix}.decoded.glb`);
 const raw=path.join(dir,`bike-${variant}-remaster-v4${suffix}.raw.glb`);
 const output=path.join(dir,`bike-${variant}-remaster-v4${suffix}.glb`);
 if(!process.argv.includes('--pack-only')){
  run('node',['assets/blender/unpack_meshopt.mjs',source,decoded]);
  const args=['-b','--python-exit-code','1','--python',path.join(dir,'build_v4.py'),'--','--input',decoded,'--output',raw,'--variant',variant];
  if(lod)args.push('--lod');
  fs.writeFileSync(path.join(evidence,`build-${variant}${suffix}.log`),run(blender,args));
 }
 const packReport=await pack(raw,output);
 const verified=await verifyBike(decoded,output,{tris:lod?6000:33500,draws:24});
 const baseline=glbStats(source),candidate=glbStats(output);
 const textureEstimate=s=>s.imageList.reduce((sum,i)=>sum+4*i.w*i.h,0);
 const report={variant,lod,baselineRef:BASE_REF,baselineGitPath:`public/models/bike-${variant}${suffix}.glb`,baseline,candidate,decodedRgbaEstimate:{baseline:textureEstimate(baseline),candidate:textureEstimate(candidate),excludesMipmapsAndDriverDuplication:true},sourceSha256:digest(source),output:path.relative(root,output),verification:verified,pack:packReport,blender:JSON.parse(fs.readFileSync(raw.replace('.glb','.blender.json'))),recipeSha256:digest(path.join(dir,'build_v4.py')),masterSha256:digest(raw.replace('.glb','.blend'))};
 fs.writeFileSync(path.join(evidence,`${variant}-v4${suffix}.json`),JSON.stringify(report,null,2)+'\n');reports.push(report);
}
fs.writeFileSync(path.join(evidence,'manifest-v4.json'),JSON.stringify(reports,null,2)+'\n');
console.log(JSON.stringify(reports.map(r=>({variant:r.variant,lod:r.lod,...r.verification})),null,2));
