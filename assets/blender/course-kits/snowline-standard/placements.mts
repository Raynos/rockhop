/** Reproducible collider/landmark report; no game source or physics is changed. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { compileTrack } from '../../../../src/tracks/compile';
import { S1, S2, S3 } from '../../../../src/tracks/rockhop/snowline';
import { snowContactFaceGeometry } from '../../../../src/render/world/zones/snowlineStandard';

const here=path.dirname(fileURLToPath(import.meta.url));
const report=[];
for(const def of [S1,S2,S3]){
  const track=compileTrack(def);
  const prop=(name:string)=>track.placed.filter(p=>p.params.prop===name).map(p=>({
    x:p.pos.x,y:p.pos.y,kind:p.kind,colliderIds:p.colliderIds,
  }));
  const cats=prop('snowcat');
  let nearTriangles=0;
  for(let x=Math.floor((track.bounds.minX-10)/40)*40;x<track.def.finishX+20;x+=40){
    const geo=snowContactFaceGeometry(track,x,Math.min(x+40,track.def.finishX+20));
    nearTriangles+=geo.getAttribute('position').count/3;
    geo.dispose();
  }
  report.push({id:def.id,colliderHash:track.hash,seed:def.seed,finishX:def.finishX,
    proposed:{station:def.id==='s1-lift-line'?{x:297,z:-7.1}:undefined,
      snowcat:cats.length?{x:(cats[0]!.x+cats.at(-1)!.x)/2,z:-6.2}:undefined,
      summit:def.id==='s3-whiteout'?{x:def.finishX-16,z:-13.8}:undefined},
    obstacleSnowcats:cats,cornices:prop('cornice'),iceLedgedBoxes:prop('ice-ledge').filter(p=>p.kind==='box'),
    exactGaps:track.placed.filter(p=>p.kind==='gap').map(p=>({x0:p.pos.x,x1:p.pos.x+Number(p.params.width),hazard:p.params.hazard})),
    fullCourseFaceTriangles:nearTriangles,
  });
}
fs.writeFileSync(path.join(here,'out','placements.json'),JSON.stringify(report,null,2)+'\n');
process.stdout.write(JSON.stringify(report.map(({id,colliderHash,finishX,fullCourseFaceTriangles,proposed})=>({id,colliderHash,finishX,fullCourseFaceTriangles,proposed})),null,2)+'\n');
