/** Independent JS finite contact check on archived CPU strict witnesses. */
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {triangleContact} from '../../../../../harness/hero-remaster/user-agent3-2026-10-03/triangle-contacts.mjs';
const out=path.dirname(new URL(import.meta.url).pathname),archive=path.join(out,'witnesses.json.gz'),local=path.join(out,'local-witnesses.json');
const rows=JSON.parse(zlib.gunzipSync(fs.readFileSync(archive))),target=JSON.parse(fs.readFileSync(local)).witnesses;
const sub=(a,b)=>a.map((x,i)=>x-b[i]),dot=(a,b)=>a.reduce((sum,x,i)=>sum+x*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function strictCross(a,b){for(const [x,y] of [[a,b],[b,a]]){const u=sub(y[1],y[0]),v=sub(y[2],y[0]),normal=cross(u,v),length=Math.hypot(...normal),unit=normal.map(x=>x/length),uu=dot(u,u),vv=dot(v,v),uv=dot(u,v),det=uu*vv-uv*uv;for(let i=0;i<3;i++){const p=x[i],q=x[(i+1)%3],d0=dot(sub(p,y[0]),unit),d1=dot(sub(q,y[0]),unit);if(d0*d1>=0||Math.min(Math.abs(d0),Math.abs(d1))<=2e-6)continue;const t=d0/(d0-d1),r=sub(p.map((x,k)=>x+t*(q[k]-x)),y[0]),beta=(vv*dot(r,u)-uv*dot(r,v))/det,gamma=(uu*dot(r,v)-uv*dot(r,u))/det;if(beta>1e-6&&gamma>1e-6&&beta+gamma<1-1e-6)return true;}}return false;}
for(const [i,r] of [...rows,...target].entries()){assert(triangleContact(r.XYZ_A,r.XYZ_B),`Finite SAT witness ${i}`);assert(strictCross(r.XYZ_A,r.XYZ_B),`Strict interior witness ${i}`);}
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const result={status:'INDEPENDENT_JS_FINITE_AND_STRICT_WITNESSES_PASS',archiveSHA256:sha(archive),localSHA256:sha(local),recipeSHA256:sha(new URL(import.meta.url)),existingFiniteSATRecipeSHA256:sha('harness/hero-remaster/user-agent3-2026-10-03/triangle-contacts.mjs'),archivedWitnesses:rows.length,localWitnesses:target.length,checks:2*(rows.length+target.length),limits:['Witness consistency check only. Does not independently repeat all BVH discovery or qualify absence/penetration depth/visual quality.']};
fs.writeFileSync(path.join(out,'witness-check.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
