/** CPU guard: shader-property trial changes exactly one runtime material reference. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../../../../../../src/render/hero/gltfTestUtils.ts';
import { prepareHero } from '../../../../../../../src/render/hero/lod.ts';
import { prepareHeroMaterials } from '../../../../../../../src/render/hero/gltf.ts';
import { MaterialLibrary } from '../../../../../../../src/render/materials/library.ts';
import { coatOpaqueEyesForPrivateTrial, SOURCE22_SHA256, EXPECTED_EYE_GEOMETRY, EYE_MATERIAL } from './private_eye_coat.ts';
const source='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind22/skin-field01/rider.glb';
const evidence='/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind29';
const raw=fs.readFileSync(source);
const sha=(b:Buffer)=>crypto.createHash('sha256').update(b).digest('hex');
assert.equal(sha(raw),SOURCE22_SHA256);
const gltf=await loadRigAt(pathToFileURL(source),true);
await prepareHero(gltf);
const lib=new MaterialLibrary(1);prepareHeroMaterials(gltf.scene,m=>lib.complete(m));
function fingerprint(g: THREE.BufferGeometry): string {
 const h=crypto.createHash('sha256');
 for (const [name,a] of Object.entries(g.attributes).sort(([x],[y])=>x.localeCompare(y))) {
  h.update(name+'/'+a.itemSize+'/'+a.count+'/'+a.normalized);
  const values=new Float64Array(a.count*a.itemSize);
  for(let i=0;i<a.count;i++)for(let c=0;c<a.itemSize;c++)values[i*a.itemSize+c]=a.getComponent(i,c);
  h.update(Buffer.from(values.buffer));
 }
 if(g.index)h.update(Buffer.from(Uint32Array.from(g.index.array).buffer));return h.digest('hex');
}
const before: {mesh:THREE.Mesh;geometry:THREE.BufferGeometry;hash:string;material:THREE.Material|THREE.Material[];properties:unknown;transform:unknown;boneMatrices?:Float32Array;bind?:number[];skeleton?:THREE.Skeleton}[]=[];
gltf.scene.updateMatrixWorld(true);
gltf.scene.traverse(o=>{
 const m=o as THREE.SkinnedMesh;if(!m.isMesh)return;
 before.push({mesh:m,geometry:m.geometry,hash:fingerprint(m.geometry),material:m.material,
 properties:Array.isArray(m.material)?m.material.map(s=>s.toJSON()):m.material.toJSON(),
 transform:[m.matrix.toArray(),m.matrixWorld.toArray()],
 ...(m.isSkinnedMesh?{skeleton:m.skeleton,boneMatrices:m.skeleton.boneMatrices.slice(),bind:[...m.bindMatrix.elements,...m.bindMatrixInverse.elements]}:{})});
});
const cornea=before.find(b=>!Array.isArray(b.material)&&b.material.name===EYE_MATERIAL)!;
assert.equal(cornea.hash,EXPECTED_EYE_GEOMETRY);
const animations=gltf.animations.map(c=>c.toJSON());
const trial=coatOpaqueEyesForPrivateTrial(gltf.scene,{sourceSHA256:sha(raw),geometrySHA256:cornea.hash});
assert.equal(trial.material.type,'MeshPhysicalMaterial');assert.equal(trial.material.transmission,0);assert.equal(trial.material.thickness,0);
assert.equal(trial.material.ior,1.5);assert.equal(trial.material.opacity,1);assert.equal(trial.material.alphaTest,0);
assert.equal(trial.material.transparent,false);assert.equal(trial.material.depthWrite,true);assert.equal(trial.material.side,THREE.DoubleSide);
assert.equal(trial.material.roughness,.35);assert.equal(trial.material.clearcoat,1);assert.equal(trial.material.clearcoatRoughness,.08);assert.equal(trial.material.metalness,0);
assert.equal(trial.material.opacity>=trial.material.alphaTest,true);
for(const b of before){
 const m=b.mesh as THREE.SkinnedMesh;
 assert.equal(m.geometry,b.geometry);assert.equal(fingerprint(m.geometry),b.hash);
 assert.deepEqual([m.matrix.toArray(),m.matrixWorld.toArray()],b.transform);
 if(b.skeleton){assert.equal(m.skeleton,b.skeleton);assert.deepEqual(m.skeleton.boneMatrices,b.boneMatrices);assert.deepEqual([...m.bindMatrix.elements,...m.bindMatrixInverse.elements],b.bind);assert.equal(m.skeleton.bones.length,19);}
 if(b!==cornea){assert.equal(m.material,b.material);assert.deepEqual(Array.isArray(m.material)?m.material.map(s=>s.toJSON()):m.material.toJSON(),b.properties);}
}
const old=cornea.material as THREE.MeshStandardMaterial;
assert.deepEqual(trial.material.defines,{STANDARD:'',PHYSICAL:''});
assert.equal(trial.material.onBeforeCompile,old.onBeforeCompile);
assert.equal(trial.material.customProgramCacheKey,old.customProgramCacheKey);
for(const key of ['map','normalMap','roughnessMap','metalnessMap','aoMap','emissiveMap','envMap'] as const)assert.equal(trial.material[key],old[key]);
assert.deepEqual(trial.material.color.toArray(),old.color.toArray());assert.equal(trial.material.envMapIntensity,old.envMapIntensity);
assert.deepEqual(gltf.animations.map(c=>c.toJSON()),animations);
assert.deepEqual(fs.readFileSync(source),raw);
const settings={type:trial.material.type,transmission:trial.material.transmission,thickness:trial.material.thickness,ior:trial.material.ior,opacity:trial.material.opacity,alphaTest:trial.material.alphaTest,transparent:trial.material.transparent,depthWrite:trial.material.depthWrite,side:trial.material.side,roughness:trial.material.roughness,metalness:trial.material.metalness,envMapIntensity:trial.material.envMapIntensity};
trial.undo();assert.equal(cornea.mesh.material,old);
// A foreign geometry receipt must fail before any material mutation.
assert.throws(()=>coatOpaqueEyesForPrivateTrial(gltf.scene,{sourceSHA256:SOURCE22_SHA256,geometrySHA256:'wrong'}));
assert.equal(cornea.mesh.material,old);
const report={status:'PASS CPU-only single opaque-eye coat trial; played appearance unaccepted',
 sourceSHA256:sha(raw), sourceGLBBytesUntouched:raw.length, geometrySHA256:cornea.hash,
 semanticRegion:{sourceMesh:1,sourcePrimitives:[4,6],sourceMaterial:6,preparedVertices:552,preparedTriangles:1060},
 materialReferencesChanged:1,geometryUVNormalsWeightsBindAndClipsExact:true,otherMaterialsExact:true,
 textureReferencesAndCompileHooksRetained:true,undoAndForeignGuardPassed:true,
 settings:{...settings,clearcoat:1,clearcoatRoughness:.08},
 diagnosis:'Prepared22 opaque-eye normals at measured pupils point forward. Roughness.35 dielectric is preserved; original cornea opacity.035 is alpha-discarded. No inverted-normal diagnosis supported.',
 hypothesis:'A reflective coat on the opaque eye can add moving wet-surface response without transmissive framebuffer or source pigmentation changes. This cannot restore anatomical corneal bulge or repair exposed lids.',
 sources:['https://threejs.org/docs/pages/MeshPhysicalMaterial.html','https://docs.blender.org/manual/en/4.5/render/shader_nodes/shader/principled.html'],
 limits:['No GPU or measured highlight until matched72-frame playback.','Exact original22 source, not rejected28 albedo or24 transmission.','Whole eye receives coating; coat normals follow existing iris/sclera surface, no anatomical refraction.','No full-body, device, performance or production acceptance.']};
fs.writeFileSync(evidence+'/private-trial-verification.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
