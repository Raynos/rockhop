/** Matched stock WebGL PBR/gray control; no game-pose or art acceptance. */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createFixturePlayer, type PoseFixture } from './protocol';
const fixture: PoseFixture = await fetch('/pose-fixture.json').then(r=>r.json());
const source = await new GLTFLoader().loadAsync('/fixture-source.glb');
const scene = new THREE.Scene(); scene.background = new THREE.Color('#25272b');
scene.add(source.scene);
scene.add(new THREE.HemisphereLight(0xffffff,0x727580,2));
const key=new THREE.DirectionalLight(0xffffff,3);key.position.set(3,5,4);scene.add(key);
const fill=new THREE.DirectionalLight(0xffffff,1);fill.position.set(-2,3,-4);scene.add(fill);
const player=createFixturePlayer(source.scene,fixture);
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);renderer.setSize(1440,960);renderer.setScissorTest(true);
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1;
document.body.prepend(renderer.domElement);
const cameras=[['front',[4,1.2,0]],['side',[.65,1.2,4]],['back',[-4,1.2,0]]] as const;
const views=cameras.map(([name,position])=>{
 const camera=new THREE.OrthographicCamera(-1.3,1.3,1.3,-1.3,.01,20);
 camera.position.fromArray(position);camera.lookAt(.65,1.2,0);camera.updateMatrixWorld();return {name,camera};
});
const surfaces: {mesh:THREE.Mesh; original:THREE.Material|THREE.Material[]; gray:THREE.MeshStandardMaterial}[]=[];
source.scene.traverse(o=>{
 if((o as THREE.Mesh).isMesh){const mesh=o as THREE.Mesh;surfaces.push({mesh,original:mesh.material,gray:new THREE.MeshStandardMaterial({color:0x929292,roughness:.72,metalness:0,side:THREE.DoubleSide})});}
});
const labels=document.getElementById('labels')!;
for(let row=0;row<2;row++)for(let col=0;col<3;col++){
 const label=document.createElement('span');label.className='label';label.style.left=`${col*480+8}px`;label.style.top=`${row*480+445}px`;label.textContent=`${row?'NEUTRAL GRAY':'TEXTURED PBR'} / ${views[col]!.name}`;labels.append(label);
}
declare global { interface Window { __basicPoseGate?: {ready:boolean;render:(index:number)=>{family:string;frame:number;matrixError:number;trianglesPerView:number;callsPerView:number;jointMatrices:number[][]};}; } }
window.__basicPoseGate={ready:true,render(index){
 const frame=fixture.frames[index];if(!frame)throw new Error('Missing fixture frame');
 const parity=player.apply(frame);let triangles=0,calls=0;
 for(let row=0;row<2;row++){
  for(const s of surfaces)s.mesh.material=row?s.gray:s.original;
  for(let col=0;col<3;col++){
   renderer.setViewport(col*480,(1-row)*480,480,480);renderer.setScissor(col*480,(1-row)*480,480,480);
   renderer.render(scene,views[col]!.camera);triangles=renderer.info.render.triangles;calls=renderer.info.render.calls;
  }
 }
 document.getElementById('title')!.textContent=`UNACCEPTED V5 / ${frame.family} / ${frame.timeSeconds.toFixed(2)}s — authored stress, not gameplay`;
 return {family:frame.family,frame:frame.frame,matrixError:parity.maximumWorldMatrixError,trianglesPerView:triangles,callsPerView:calls,jointMatrices:fixture.jointNames.map(n=>player.bones.get(n)!.matrixWorld.toArray())};
}};
window.__basicPoseGate.render(0);
