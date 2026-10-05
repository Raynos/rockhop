/** Full original body and rest glove SAT/BVH; no skin or swept proof. */
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const [input,output]=process.argv.slice(2);
const {triangleRows,bvhContacts}=await import(pathToFileURL(path.resolve('harness/hero-remaster/user-agent3-2026-10-03/triangle-bvh.mjs')));
const source=JSON.parse(fs.readFileSync(input,'utf8'));
const valid=(vertices,faces)=>{
 const rows=triangleRows(vertices,faces);
 let excluded=0;
 const admitted=rows.filter(row=>{
  const [a,b,c]=row.points,u=b.map((v,i)=>v-a[i]),v=c.map((v,i)=>v-a[i]);
  const n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
  if(Math.hypot(...n)<1e-14){excluded++;return false;}return true;
 });
 return {rows:admitted,excluded};
};
const report={accepted:false,status:'FINITE_REST_SURFACE_CONTACT_CHECK_ONLY',
 limits:'Finite SAT contacts, no signed inside/outside, swept proof, collider response, native/GPU or art acceptance.',frames:[]};
for(const frame of source.frames){
 const glove=valid(frame.gloveXYZ,source.gloveFaces),body=valid(frame.bodyXYZ,source.bodyFaces);
 report.frames.push({side:source.side,frame:frame.index,time:frame.time,
  gloveDegenerateRowsExcluded:glove.excluded,bodyDegenerateRowsExcluded:body.excluded,
  bodyContact:bvhContacts(glove.rows,body.rows),selfContact:bvhContacts(glove.rows,glove.rows,true,true)});
}
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({side:source.side,frames:report.frames.length,
 maxBodyContacts:Math.max(...report.frames.map(x=>x.bodyContact.pairs)),
 maxSelfContacts:Math.max(...report.frames.map(x=>x.selfContact.pairs))}));
