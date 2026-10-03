/** Validate engine local-rest quaternion extraction against all frozen source poses. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { Matrix4, Quaternion, Vector3 } from 'three';
import { readGlbChunks } from './metadata.mjs';
import { correctiveWeights } from './runtime-corrective.mjs';
const [candidateFile,driverFile,expandedFile,controllerFile,outFile]=process.argv.slice(2);assert(outFile&&!fs.existsSync(outFile));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const candidateBytes=fs.readFileSync(candidateFile),driverBytes=fs.readFileSync(driverFile),expandedBytes=fs.readFileSync(expandedFile),controllerBytes=fs.readFileSync(controllerFile);
const g=readGlbChunks(candidateBytes).json,driver=JSON.parse(driverBytes),expanded=JSON.parse(expandedBytes),controller=JSON.parse(controllerBytes);
assert.equal(sha(candidateBytes),controller.candidateGLBSHA256);assert.equal(sha(driverBytes),controller.poseDriverSHA256);
assert.equal(sha(expandedBytes),'ddced495c7ae0218c7ae83f5b47c1d007da137e8d7f05e37e08ae65a9c15d457');assert.deepEqual(controller.configs,expanded.configs);
const parents=new Map(g.nodes.flatMap((n,i)=>(n.children??[]).map(c=>[c,i]))),byName=new Map(g.nodes.map((n,i)=>[n.name,i]));
let maximumQuaternionAngleRad=0,maximumCoefficientError=0;const samples=[];
for(const frame of driver.frames){
  const basis={};
  for(const name of new Set(controller.configs.flatMap(c=>c.joints))){
    const i=byName.get(name),node=g.nodes[i],parent=g.nodes[parents.get(i)];assert(parent&&frame.jointWorldColumnMajor[parent.name]);
    const local=new Matrix4().fromArray(frame.jointWorldColumnMajor[parent.name]).invert().multiply(new Matrix4().fromArray(frame.jointWorldColumnMajor[name]));
    // Decomposition here extracts a metric only. Playback retains exact matrices;
    // these TRS values never replace the source pose or change engine geometry.
    const q=new Quaternion();local.decompose(new Vector3(),q,new Vector3());
    const rest=new Quaternion().fromArray(node.rotation??[0,0,0,1]).normalize();q.premultiply(rest.invert()).normalize();
    basis[name]=[q.w,q.x,q.y,q.z];
    const source=frame.poseBasisBlender[name].quaternionWXYZ,expected=new Quaternion(source[1],source[2],source[3],source[0]).normalize();
    maximumQuaternionAngleRad=Math.max(maximumQuaternionAngleRad,q.angleTo(expected));
  }
  for(const config of controller.configs){const values=correctiveWeights(config,basis,expanded.centers[config.region]);
    assert(values.every(Number.isFinite)&&values.every(v=>v>=0)&&values.reduce((s,v)=>s+v,0)<=1+1e-12);
    for(let k=0;k<values.length;k++)maximumCoefficientError=Math.max(maximumCoefficientError,Math.abs(values[k]-expanded.frames[frame.index].coefficients[config.region][config.keys[k]]));
    if(frame.index===0)assert(values.every(v=>v===0));
    samples.push({frame:frame.index,region:config.region,coefficients:values});
  }
}
assert(maximumQuaternionAngleRad<3e-6);assert(maximumCoefficientError<1e-5);
const report={status:'UNACCEPTED_ENGINE_CONTROLLER_FRAME_CHECK',candidateSHA256:sha(candidateBytes),driverSHA256:sha(driverBytes),expandedSHA256:sha(expandedBytes),controllerSHA256:sha(controllerBytes),
  controllerCodeSHA256:sha(fs.readFileSync(new URL('runtime-corrective.mjs',import.meta.url))),checkCodeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),
  frames:driver.frames.length,maximumQuaternionAngleRad,maximumCoefficientError,restExactlyZero:true,samples,
  derivation:'pose basis quaternion = inverse(normalized file local-rest quaternion) × normalized current local quaternion. Native bone-local axes are retained; no global Blender/glTF axis swizzle is applied to the bone-local basis.',
  limits:['Metric extraction only; no TRS reconstruction of playback matrices. Actual live riding still needs independent source/loader/controller/camera/input receipts.',
    'Native recorded coefficient agreement is finite sampled validation, not extrapolated pose quality or fit/contact acceptance.',
    'Private diagnostic controller only; no normal player coupling or assets changed.']};
fs.writeFileSync(outFile,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({frames:report.frames,maximumQuaternionAngleRad,maximumCoefficientError}));
