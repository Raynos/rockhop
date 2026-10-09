// Read exact selected storage into offline diagnosis arrays. No asset mutation.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {openGlb,accessorBytes,fileSha,sha} from '../download-opt01/geometry01/glb.mjs';
const [input,output] = process.argv.slice(2);
const sourceSHA256 = '585ae314e2b354768a1385e5a85828c142d542b47f8d9fe948f46c7478c112ef';
assert.equal(fileSha(input), sourceSHA256);
assert(!fs.existsSync(output), 'Fresh output required');
fs.mkdirSync(output, {recursive:true});
const g = openGlb(input), j = g.json;
const report = {accepted:false, source:{path:input,sha256:sourceSHA256}, components:[]};
for (const mi of [2,3,5]) {
  const node = j.nodes.find(n => n.mesh === mi), p = j.meshes[mi].primitives[0], skin = j.skins[node.skin];
  const directory = path.join(output, node.name); fs.mkdirSync(directory);
  const row = {meshIndex:mi, name:node.name, material:j.materials[p.material], attributes:{}, nativeJointNames:skin.joints.map(i=>j.nodes[i].name)};
  for (const [name, ai] of Object.entries({...p.attributes,indices:p.indices,inverseBindMatrices:skin.inverseBindMatrices})) {
    const bytes = await accessorBytes(g,ai);
    fs.writeFileSync(path.join(directory,name+'.bin'),bytes);
    row.attributes[name] = {...j.accessors[ai], decodedSHA256:sha(bytes)};
  }
  report.components.push(row);
}
fs.writeFileSync(path.join(output,'intake.json'),JSON.stringify(report,null,2)+'\n');
fs.closeSync(g.fd);
console.log(JSON.stringify({accepted:false,sourceSHA256,components:report.components.map(c=>({name:c.name,vertices:c.attributes.POSITION.count}))}));
