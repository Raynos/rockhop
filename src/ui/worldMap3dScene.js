import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
const skyImageUrl = import.meta.env.DEV
  ? '/prototypes/world-map-c/assets/sky-alpine-a.png'
  : '/map-review/sky-alpine-a.png';

// Lazy 3D review map. The same procedural island as the selected C prototype
// is mounted only while the map screen is open; all stage navigation stays in
// WorldMapScreen. All route, terrain and towers are real meshes.
export function mountWorldMap3D(root, onSelect, initialIndex = 0, locked = [], medals = []) {
let disposed = false;
const scene = new THREE.Scene();
scene.background = new THREE.Color('#8db4c2');
scene.fog = new THREE.FogExp2('#9bced0', 0.0034);
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
renderer.setSize(root.clientWidth, root.clientHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.035;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
root.appendChild(renderer.domElement);

const camera = new THREE.PerspectiveCamera(30, root.clientWidth / root.clientHeight, 0.1, 250);
// The atlas is read from above: the far side of the forest must not hide the
// road when the player turns the island through a full orbit.
camera.position.set(3, 28, 36);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0, 0);
controls.enableDamping = true;
controls.dampingFactor = 0.055;
controls.enablePan = false;
controls.minPolarAngle = 0.42;
controls.maxPolarAngle = 0.91;
controls.minDistance = 12;
controls.maxDistance = 105;
controls.maxAzimuthAngle = Infinity;
controls.minAzimuthAngle = -Infinity;
controls.update();

const hemi = new THREE.HemisphereLight('#d4e9e8', '#657567', 1.01);
scene.add(hemi);
const sun = new THREE.DirectionalLight('#ffe4bc', 2.10);
sun.position.set(-22, 45, 33);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
sun.shadow.camera.left = -32;
sun.shadow.camera.right = 32;
sun.shadow.camera.top = 24;
sun.shadow.camera.bottom = -24;
sun.shadow.camera.near = 1;
sun.shadow.camera.far = 110;
sun.shadow.bias = -0.0003;
scene.add(sun);
const fill = new THREE.DirectionalLight('#a9dfe9', .34);
fill.position.set(22, 20, -22);
scene.add(fill);

const materialCache=new Map();
const mat = (color, roughness = 1, metalness = 0) => {
 const key=`${color}/${roughness}/${metalness}`;
 if(!materialCache.has(key))materialCache.set(key,new THREE.MeshStandardMaterial({ color, roughness, metalness }));
 return materialCache.get(key);
};
const simplex = (x, z) => {
  const s = Math.sin(x * 127.1 + z * 311.7) * 43758.5453;
  return (s - Math.floor(s)) * 2 - 1;
};
const noise = (x, z) => {
  let a = 0, amp = 1, d = 0;
  for (let i = 0; i < 4; i++) {
    const ix=Math.floor(x), iz=Math.floor(z), fx=x-ix, fz=z-iz;
    const u=fx*fx*(3-2*fx), v=fz*fz*(3-2*fz);
    const lo=THREE.MathUtils.lerp(simplex(ix,iz),simplex(ix+1,iz),u);
    const hi=THREE.MathUtils.lerp(simplex(ix,iz+1),simplex(ix+1,iz+1),u);
    a += THREE.MathUtils.lerp(lo,hi,v)*amp;
    d += amp; x *= 2.03; z *= 2.03; amp *= 0.49;
  }
  return a / d;
};
const ridge = (x, z, cx, cz, sx, sz) => Math.exp(-(((x-cx)/sx)**2 + ((z-cz)/sz)**2));
const smooth = (a,b,x) => { const t = THREE.MathUtils.clamp((x-a)/(b-a),0,1); return t*t*(3-2*t); };
const edgeDistance = (x,z) => {
  const coastJitter = .105*Math.sin(x*.55+z*.29) + .052*Math.sin(x*1.8+z*.7) + .035*Math.sin(x*4.8-z*1.9);
  // Three small coves and two rock headlands keep the shoreline from reading
  // as a regular oval when the island turns. They begin beyond the road.
  const front=smooth(5.6,8.5,z);
  const coves=front*(.21*ridge(x,z,-9.2,8.6,2.2,2.4)
    +.25*ridge(x,z,2.3,8.9,2.7,2.5)
    +.19*ridge(x,z,12.0,8.0,2.0,2.4));
  const headlands=front*(.11*ridge(x,z,-15.2,8.1,1.7,2.8)
    +.09*ridge(x,z,8.1,8.4,1.5,2.5));
  // The player can orbit behind the island. Two rear coves and a projecting
  // headland give that shoreline the same authored profile as the front.
  const rear=smooth(5.4,8.7,-z);
  const backCoves=rear*(.18*ridge(x,z,-15.4,-8.2,2.7,2.0)
    +.23*ridge(x,z,5.1,-8.1,3.3,2.2));
  const backHeadland=rear*.13*ridge(x,z,-3.8,-8.8,2.2,2.5);
  return Math.sqrt((x/25.4)**2 + (z/(9.7 + 1.0*Math.sin(x*.23)))**2) + coastJitter + coves + backCoves - headlands - backHeadland;
};
const routeZ = x => -.40 + 2.55*Math.sin(x*.29+.7) + .8*Math.sin(x*.76-.3)
  + .55*Math.sin(x*.12) + 4.0*(smooth(-13,-10,x)-smooth(-2,1,x))
  + 3.15*(smooth(1,4,x)-smooth(10,14,x))
  // Bend the quarry traverse into the red cut bank. The former route crossed
  // its foreground as one straight beige band, leaving the excavated landform
  // visually disconnected from the journey. All road/tower meshes share this
  // curve, so the selectable order and hit positions follow the bend.
  - 1.8*ridge(x,0,7.8,0,3.1,1);
const groundHeight = (x,z) => {
  const edge = edgeDistance(x,z);
  const base = .72 + .60*smooth(-15,-5,x) + .36*noise(x*.48,z*.48) + .14*noise(x*1.4,z*1.4);
  const woodland = (smooth(-17,-6,x)-smooth(0,5,x)) * (.55 + 1.8*ridge(x,z,-4,-3,13,6));
  const quarry = (smooth(-1,3,x)-smooth(12,16,x)) *
    (2.8*ridge(x,z,7,-3.0,7.4,5.7) + .50*noise(x*.5,z*.5));
  const snow = smooth(11,17,x) * (
    2.5*ridge(x,z,19,4,7,5) + 5.4*ridge(x,z,18,-5.6,5.7,2.8)
    + 4.4*ridge(x,z,24,2.6,4.2,4.5) + 3.1*ridge(x,z,14,-7,4.3,3.2));
  const h = base + woodland + quarry + snow;
  // The rim is fractured by long rock ribs. It still drops into the sea, but
  // it no longer forms one geometrically continuous curtain along the camera.
  const rib=(.25*Math.sin(x*1.18+z*.28)+.13*Math.sin(x*3.75-z*.5))
    * smooth(.67,.83,edge)*(1-smooth(1.0,1.06,edge));
  return h * (1-smooth(.84,1.025,edge)) - 2.05*smooth(.92,1.05,edge) + rib;
};

// A tiny deterministic RNG makes the mockup stable for review and comparisons.
let seed = 9537;
const rand = () => ((seed = (1664525*seed + 1013904223) >>> 0) / 4294967296);
const rr = (a,b) => a+(b-a)*rand();
const terrain = new THREE.Group();
terrain.scale.x=.82;
scene.add(terrain);

const nx=220, nz=100, dx=52/nx, dz=23/nz;
const verts=[], col=[], texcoord=[], indices=[];
const c = new THREE.Color();
const cliffRocks=['#778174','#9fa88e','#965f41','#cd8e62','#879fa5','#c2d0cb'].map(hex=>new THREE.Color(hex));
const cliffMix=[new THREE.Color(),new THREE.Color(),new THREE.Color()];
const colorFor = (x,z,y) => {
  const edge=edgeDistance(x,z);
  const borderNoise=noise(x*.47,z*.47)*1.6;
  c.set(y < .42 ? '#766f5b' : '#77795d');
  // Cooler, darker woodland soil keeps the winding pale trail distinct. The
  // previous sage floor became one broad beige clearing in warm sunlight.
  c.lerp(new THREE.Color(y > 1.25 ? '#60765d' : '#48674d'),smooth(-13.8,-8.7,x+borderNoise));
  c.lerp(new THREE.Color(y > 2.1 ? '#b07145' : '#a66b46'),smooth(.2,4.1,x+borderNoise));
  c.lerp(new THREE.Color(y > 1.2 ? '#dce7e7' : '#a5b5ad'),smooth(11.8,15.5,x+borderNoise));
  const sx=(groundHeight(x+.16,z)-groundHeight(x-.16,z))/.32;
  const sz=(groundHeight(x,z+.16)-groundHeight(x,z-.16))/.32;
  const exposed=smooth(.65,2.9,Math.hypot(sx,sz))*.68;
  const stone=new THREE.Color(x>13?'#5d7681':x>2?'#784b35':'#56605c');
  c.lerp(stone,exposed);
  const rim=smooth(.71,.99,edge);
  const strata=.5+.5*Math.sin(y*4.65+x*.21+noise(x*.42,z*.42)*.85);
  const fineBed=.5+.5*Math.sin(y*10.8+x*.53);
  const mineral=new THREE.Color(x>13?'#a4b9ba':x>2?'#b78158':'#929384');
  c.lerp(mineral,rim*exposed*(.10+.39*strata+.09*fineBed));
  const variation = noise(x*2.3,z*2.3)*.065 + noise(x*.75,z*.75)*.035;
  c.offsetHSL(0,0,variation);
  if (x > 11 && y > 2.2) c.lerp(new THREE.Color('#f5f5ed'), smooth(2.2,4.1,y)*.6);
  // The exposed rim is the island's largest visible surface. Give its cut
  // faces biome-specific rock and broad sediment seams instead of the former
  // uniform charcoal band, including the coast seen from behind the island.
  const cliff=smooth(.82,1.015,edge);
  const bed=.5+.5*Math.sin(y*3.85+x*.19+noise(x*.48,z*.48)*1.35);
  const fractured=.5+.5*noise(x*1.2+y*.7,z*1.2);
  const slate=cliffMix[0].copy(cliffRocks[0]).lerp(cliffRocks[1],bed*.52);
  const rust=cliffMix[1].copy(cliffRocks[2]).lerp(cliffRocks[3],bed*.63);
  const ice=cliffMix[2].copy(cliffRocks[4]).lerp(cliffRocks[5],bed*.67);
  const cliffColor=slate.lerp(rust,smooth(-.2,4.6,x+noise(x*.35,z*.35)*1.3))
    .lerp(ice,smooth(11.1,16.3,x+noise(x*.35,z*.35)*1.3));
  cliffColor.offsetHSL(0,0,(fractured-.5)*.11-.045*(1-smooth(-1.65,.05,y)));
  c.lerp(cliffColor,cliff*.94);
  return c;
};
for(let iz=0;iz<=nz;iz++) for(let ix=0;ix<=nx;ix++){
  const x=-26+ix*dx,z=-11.5+iz*dz,y=groundHeight(x,z);
  verts.push(x,y,z); const cc=colorFor(x,z,y); col.push(cc.r,cc.g,cc.b);
  texcoord.push((x+26)/3.5,(z+11.5)/3.5);
  if(ix<nx&&iz<nz){const i=iz*(nx+1)+ix;indices.push(i,i+nx+1,i+1,i+1,i+nx+1,i+nx+2);}
}

const geo = new THREE.BufferGeometry();
geo.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));
geo.setAttribute('color',new THREE.Float32BufferAttribute(col,3));
geo.setAttribute('uv',new THREE.Float32BufferAttribute(texcoord,2));
geo.setIndex(indices); geo.computeVertexNormals();
const textureCanvas=document.createElement('canvas');textureCanvas.width=256;textureCanvas.height=256;
const textureContext=textureCanvas.getContext('2d'),texturePixels=textureContext.createImageData(256,256);
const hash2=(x,y)=>{const h=Math.sin(x*127.1+y*311.7)*43758.5453;return h-Math.floor(h);};
const valueNoise=(x,y)=>{
 const ix=Math.floor(x),iy=Math.floor(y),fx=x-ix,fy=y-iy;
 const u=fx*fx*(3-2*fx),v=fy*fy*(3-2*fy);
 const a=THREE.MathUtils.lerp(hash2(ix,iy),hash2(ix+1,iy),u);
 const b=THREE.MathUtils.lerp(hash2(ix,iy+1),hash2(ix+1,iy+1),u);
 return THREE.MathUtils.lerp(a,b,v);
};
for(let y=0;y<256;y++)for(let x=0;x<256;x++){
 const coarse=valueNoise(x/37,y/37),fine=valueNoise(x/7,y/7);
 const bedding=.5+.5*Math.sin(y*.31+coarse*4),grain=.15*(hash2(x,y)-.5);
 const brightness=Math.round(185+42*coarse+13*fine+8*bedding+grain*25);
 const i=(y*256+x)*4;texturePixels.data[i]=brightness;
 texturePixels.data[i+1]=brightness;texturePixels.data[i+2]=brightness-3;texturePixels.data[i+3]=255;
}
textureContext.putImageData(texturePixels,0,0);
const groundTexture=new THREE.CanvasTexture(textureCanvas);groundTexture.wrapS=groundTexture.wrapT=THREE.RepeatWrapping;
groundTexture.colorSpace=THREE.SRGBColorSpace;groundTexture.anisotropy=renderer.capabilities.getMaxAnisotropy();
const island = new THREE.Mesh(geo,new THREE.MeshStandardMaterial({vertexColors:true,map:groundTexture,roughness:1,flatShading:true,side:THREE.DoubleSide}));
island.castShadow=true;island.receiveShadow=true;terrain.add(island);

// Layered seawater gives specular movement around a true island silhouette.
const waterGeo = new THREE.PlaneGeometry(500,500,80,80); waterGeo.rotateX(-Math.PI/2);
const waterUniforms={time:{value:0}};
const waterMaterial=new THREE.ShaderMaterial({uniforms:waterUniforms,transparent:true,depthWrite:false,vertexShader:`
 uniform float time; varying vec3 vWorld; varying vec3 vNormal;
 void main(){
   vec3 p=position;
   p.y=-1.13 + .075*sin(p.x*.75+time*.65)*sin(p.z*.47-time*.46)
         + .042*sin(p.x*2.2-p.z*.8+time*1.1);
   vec4 w=modelMatrix*vec4(p,1.0);vWorld=w.xyz;vNormal=normal;
   gl_Position=projectionMatrix*viewMatrix*w;
 }`,fragmentShader:`
 uniform float time; varying vec3 vWorld; varying vec3 vNormal;
 float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
 float valueNoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
   return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+1.),f.x),f.y);}
 void main(){
   vec2 p=vWorld.xz;float n=valueNoise(p*1.3+time*.035),n2=valueNoise(p*3.7-time*.09);
   float unscaledX=p.x/.82;
   float r=length(vec2(unscaledX/25.4,p.y/(9.7+sin(unscaledX*.23)))) + .105*sin(unscaledX*.55+p.y*.29)+.052*sin(unscaledX*1.8+p.y*.7)+.035*sin(unscaledX*4.8-p.y*1.9);
   float front=smoothstep(5.6,8.5,p.y);
   float coveA=.21*exp(-pow((unscaledX+9.2)/2.2,2.)-pow((p.y-8.6)/2.4,2.));
   float coveB=.25*exp(-pow((unscaledX-2.3)/2.7,2.)-pow((p.y-8.9)/2.5,2.));
   float coveC=.19*exp(-pow((unscaledX-12.)/2.,2.)-pow((p.y-8.)/2.4,2.));
   float headA=.11*exp(-pow((unscaledX+15.2)/1.7,2.)-pow((p.y-8.1)/2.8,2.));
   float headB=.09*exp(-pow((unscaledX-8.1)/1.5,2.)-pow((p.y-8.4)/2.5,2.));
   float rear=smoothstep(5.4,8.7,-p.y);
   float backA=.18*exp(-pow((unscaledX+15.4)/2.7,2.)-pow((p.y+8.2)/2.,2.));
   float backB=.23*exp(-pow((unscaledX-5.1)/3.3,2.)-pow((p.y+8.1)/2.2,2.));
   float backHead=.13*exp(-pow((unscaledX+3.8)/2.2,2.)-pow((p.y+8.8)/2.5,2.));
   r+=front*(coveA+coveB+coveC-headA-headB)+rear*(backA+backB-backHead);
   float shallow=1.-smoothstep(.93,1.18,r);
   vec3 deep=vec3(.009,.115,.162),cove=vec3(.036,.295,.345);
   vec3 color=mix(deep,cove,shallow*.67+.17*n);
   float ripples=valueNoise(vec2(p.x*2.4+p.y*.35+time*.26,p.y*1.8-time*.18));
   float shortCrest=smoothstep(.76,.9,ripples)*(.025+.085*n2);
   float foamBand=1.-smoothstep(.025,.145,abs(r-1.01));
   float foam=foamBand*step(.49,n+.17*n2+.12*sin(p.x*5.+time*.7))*.58;
   float sparkle=pow(max(0.,sin(p.x*3.2+p.y*1.5+time*.4)),56.)*.045*n2;
   color+=vec3(shortCrest+sparkle)*vec3(.38,.74,.77);
   color=mix(color,vec3(.70,.84,.83),foam);
   float cameraDistance=length(vWorld.xz-cameraPosition.xz);
   float horizonAlpha=1.-smoothstep(43.,72.,cameraDistance);
   gl_FragColor=vec4(color,horizonAlpha);
   #include <tonemapping_fragment>
   #include <colorspace_fragment>
 }`,toneMapped:true});
const water = new THREE.Mesh(waterGeo,waterMaterial);scene.add(water);

// Project-owned sky artwork is mapped to an enclosing cylinder, coherent under orbit.
new THREE.TextureLoader().load(skyImageUrl,texture=>{
 if(disposed){texture.dispose();return;}
 texture.colorSpace=THREE.SRGBColorSpace;
 texture.wrapS=THREE.MirroredRepeatWrapping;texture.repeat.x=2;
 const sky=new THREE.Mesh(new THREE.CylinderGeometry(175,175,140,64,1,true),new THREE.MeshBasicMaterial({map:texture,side:THREE.BackSide,depthWrite:false,fog:false}));
 sky.position.y=-35;scene.add(sky);
});

function mesh(geometry,material,x,y,z,parent=terrain){const o=new THREE.Mesh(geometry,material);o.position.set(x,y,z);parent.add(o);return o;}
function box(w,h,d,material,x,y,z,parent=terrain){return mesh(new THREE.BoxGeometry(w,h,d),material,x,y,z,parent);}
function cylinder(r1,r2,h,material,x,y,z,parent=terrain,sides=8){return mesh(new THREE.CylinderGeometry(r1,r2,h,sides),material,x,y,z,parent);}
function line(points, material, radius=.04, parent=terrain){const curve=new THREE.CatmullRomCurve3(points);const tube=new THREE.Mesh(new THREE.TubeGeometry(curve,Math.max(points.length*3,16),radius,5,false),material);parent.add(tube);return tube;}
function spanBeam(a,b,width,depth,material,parent=terrain){
 const delta=new THREE.Vector3().subVectors(b,a),o=mesh(new THREE.BoxGeometry(width,delta.length(),depth),material,(a.x+b.x)/2,(a.y+b.y)/2,(a.z+b.z)/2,parent);
 o.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),delta.normalize());o.castShadow=true;return o;
}

// Small disconnected whitecaps follow breaking waves rather than forming UI rings.
const foamMat=new THREE.MeshBasicMaterial({color:'#d9eeea',transparent:true,opacity:.62,side:THREE.DoubleSide,depthWrite:false});
const foamVerts=[],foamIndices=[];
for(let i=0;i<185;i++){
 const a=rr(0,Math.PI*2),r=rr(1.01,1.19),x=25.3*Math.cos(a)*r,z=9.7*Math.sin(a)*r;
 const length=rr(.12,.49),width=rr(.009,.023),base=foamVerts.length/3;
 foamVerts.push(x-length*.5,-.99,z-width,x-length*.5,-.99,z+width,
                x,-.985,z+.025-width,x,-.985,z+.025+width,
                x+length*.5,-.99,z-width,x+length*.5,-.99,z+width);
 foamIndices.push(base,base+1,base+2,base+1,base+3,base+2,
                  base+2,base+3,base+4,base+3,base+5,base+4);
}
const foamGeo=new THREE.BufferGeometry();foamGeo.setAttribute('position',new THREE.Float32BufferAttribute(foamVerts,3));foamGeo.setIndex(foamIndices);foamGeo.computeVertexNormals();
terrain.add(new THREE.Mesh(foamGeo,foamMat));

// Detached sea stacks and broken promontories give the shoreline a jagged silhouette.
const seaStackMaterial=new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,flatShading:true,side:THREE.DoubleSide});
function seaStack(x,z,radius,height,snowy=false){
 const ring=10,p=[],clr=[],idx=[];
 const levels=[-.22,.08,.55,.86,1],scales=[.82,1,.65,.35,.04];
 for(let j=0;j<levels.length;j++)for(let k=0;k<ring;k++){
   const a=k/ring*Math.PI*2,irregular=.82+.17*Math.sin(k*3.8+x)+.13*Math.cos(k*5.3+z);
   p.push(Math.cos(a)*radius*scales[j]*irregular,levels[j]*height-1.12,Math.sin(a)*radius*scales[j]*irregular);
   const hex=snowy?(j>2?'#e3e8e5':'#7f989e'):(j>2?'#a5987a':x>2?'#885f48':'#72756d');
   const shade=new THREE.Color(hex);shade.offsetHSL(0,0,(k%3-1)*.055+rr(-.025,.025));
   clr.push(shade.r,shade.g,shade.b);
   if(j<levels.length-1){const i=j*ring+k,next=j*ring+(k+1)%ring;idx.push(i,next,i+ring,next,next+ring,i+ring);}
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));
 g.setAttribute('color',new THREE.Float32BufferAttribute(clr,3));g.setIndex(idx);g.computeVertexNormals();
 const o=mesh(g,seaStackMaterial,x,0,z);
 o.castShadow=true;o.receiveShadow=true;
}
for(let i=0;i<39;i++){
 const x=-23.6+i*1.25+rr(-.35,.35),edgeZ=9.5*Math.sqrt(Math.max(.03,1-(x/25.4)**2));
 const z=edgeZ*rr(.96,1.27)+rr(-.2,.3),scale=i%7===0?rr(1.35,2.0):rr(.44,1.05);
 seaStack(x,z,scale*.43,scale*1.35,x>14);
 if(i%5===0)seaStack(x+rr(-.4,.4),z+rr(.7,1.6),scale*.31,scale*.98,x>14);
}
for(let i=0;i<24;i++){
 const x=-22.4+i*1.9+rr(-.3,.3),edgeZ=(9.7+Math.sin(x*.23))*Math.sqrt(Math.max(.04,1-(x/25.4)**2));
 const z=-edgeZ*rr(.99,1.22),scale=i%6===0?rr(1.2,1.7):rr(.35,.86);
 seaStack(x,z,scale*.37,scale*1.22,x>14);
}

// Broad broken outcrops interrupt both cliff faces and carry their silhouette
// down into the surf. Fewer, heavier ribs read as a cut rock mass in an orbit.
const buttressPositions=[],buttressIndices=[];
const buttressLevels=[-.8,-.33,.18,.55,1],buttressWidths=[.82,1,.83,.49,.07],buttressSides=9;
for(let level=0;level<buttressLevels.length;level++)for(let side=0;side<buttressSides;side++){
 const angle=side/buttressSides*Math.PI*2;
 const jag=.78+.13*Math.sin(side*5.73+level*3.91)+.11*Math.cos(side*3.26-level*2.2);
 buttressPositions.push(Math.cos(angle)*buttressWidths[level]*jag,buttressLevels[level],Math.sin(angle)*buttressWidths[level]*jag);
 if(level<buttressLevels.length-1){const a=level*buttressSides+side,b=level*buttressSides+(side+1)%buttressSides;buttressIndices.push(a,b,a+buttressSides,b,b+buttressSides,a+buttressSides);}
}
const buttressGeo=new THREE.BufferGeometry();
buttressGeo.setAttribute('position',new THREE.Float32BufferAttribute(buttressPositions,3));
buttressGeo.setIndex(buttressIndices);buttressGeo.computeVertexNormals();
const buttressMaterials=['#626d62','#78836f','#a46a4b','#a8babc'].map(hex=>mat(hex));
const buttresses=buttressMaterials.map(material=>new THREE.InstancedMesh(buttressGeo,material,40));
const buttressCounts=[0,0,0,0],buttressDummy=new THREE.Object3D();
for(let i=0;i<128;i++){
 const x=rr(-23.0,23.0),side=rand()<.50?1:-1;
 const edgeZ=(9.7+Math.sin(x*.23))*Math.sqrt(Math.max(.08,1-(x/25.4)**2));
 const z=side*edgeZ*rr(.92,1.045);
 const band=x>13?3:x>2?2:x<-11?0:1;
 if(buttressCounts[band]>=40)continue;
 const rear=side<0,top=groundHeight(x,z),height=rr(.82,2.05)*(rear?1.55:1)*(x>13?1.08:1);
 buttressDummy.position.set(x,top-(rear?.31:.57)*height,z);
 buttressDummy.rotation.set(rr(-.14,.14),rr(0,6.28),rr(-.20,.20));
 buttressDummy.scale.set(rr(rear?.55:.38,rear?1.12:.83),height,rr(rear?.52:.37,rear?1.02:.78));buttressDummy.updateMatrix();
 buttresses[band].setMatrixAt(buttressCounts[band]++,buttressDummy.matrix);
}
buttresses.forEach((o,i)=>{o.count=buttressCounts[i];o.castShadow=true;o.receiveShadow=true;terrain.add(o);});

// Two interrupted bedding ledges follow the broken coastline. Muted color and
// longer gaps leave the larger rock facets readable from front and reverse.
{
 const positions=[],colors=[],indices=[];
 const bands=[.911,.969];
 const palettes=[
   ['#7c8376','#656f64'],
   ['#748a78','#617468'],
   ['#a4714e','#80543e'],
   ['#bacbc7','#829fa5'],
 ];
 const coastAt=(x,side,target)=>{
   if(edgeDistance(x,0)>=target)return null;
   let lo=0,hi=12.5;
   for(let i=0;i<15;i++){
     const mid=(lo+hi)/2;
     if(edgeDistance(x,side*mid)<target)lo=mid;else hi=mid;
   }
   return side*(lo+hi)/2;
 };
 for(const side of [-1,1])for(let band=0;band<bands.length;band++)for(let i=0;i<188;i++){
   const x0=-22.55+i*.24,x1=x0+.24;
   if(hash2(Math.floor(x0/1.8)+band*11,side*19)<.46)continue;
   const outer=bands[band]+.008;
   const z00=coastAt(x0,side,bands[band]),z01=coastAt(x0,side,outer);
   const z10=coastAt(x1,side,bands[band]),z11=coastAt(x1,side,outer);
   if([z00,z01,z10,z11].some(z=>z===null))continue;
   const base=positions.length/3;
   for(const [x,z] of [[x0,z00],[x0,z01],[x1,z10],[x1,z11]]){
     positions.push(x,groundHeight(x,z)+.035,z);
     const biome=x>13?3:x>2?2:x>-10?1:0;
     const color=new THREE.Color(palettes[biome][band]);
     color.offsetHSL(0,0,(hash2(x*.9,band*17+side)-.5)*.055);
     colors.push(color.r,color.g,color.b);
   }
   indices.push(base,base+1,base+2,base+1,base+3,base+2);
 }
 const seams=new THREE.BufferGeometry();
 seams.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
 seams.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
 seams.setIndex(indices);seams.computeVertexNormals();
 terrain.add(new THREE.Mesh(seams,new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,side:THREE.DoubleSide})));
}

// A graded trail pressed into the relief. The center carries warm compacted
// dirt; its feathered shoulders borrow the surrounding biome color and sink
// back to the ground. Fine crosswise tessellation avoids the old cut-throughs.
function routeMesh(){
 const positions=[],routeColors=[],uv=[],ind=[],count=460,across=16;
 for(let i=0;i<=count;i++){
   const x=-22.15 + i/count*44.2,z=routeZ(x);
   const forestBand=smooth(-13,-10,x)*(1-smooth(1,4,x));
   const width=1.43-.20*forestBand;
   const z1=routeZ(x+.04),z0=routeZ(x-.04);
   const tx=.08,tz=z1-z0,l=Math.hypot(tx,tz),px=-tz/l,pz=tx/l;
   for(let j=0;j<=across;j++){
     const sign=-1+2*j/across;
     const xx=x+px*width*sign,zz=z+pz*width*sign;
     const shoulder=smooth(.41,.99,Math.abs(sign));
     const lift=.13*(1-shoulder)+.042;
     const terrainY=groundHeight(xx,zz);
     positions.push(xx,terrainY+lift,zz);uv.push(i/13,sign);
     const tint=new THREE.Color('#c9ab75');
     tint.lerp(new THREE.Color('#cc9a62'),smooth(1.5,4.5,x));
     tint.lerp(new THREE.Color('#cad0c8'),smooth(12.5,15.5,x));
     tint.offsetHSL(0,0,.022*noise(xx*.7,zz*.7)+.012*noise(xx*2.0,zz*2.0));
     tint.lerp(new THREE.Color(x>13?'#647a7a':x>2?'#805a3f':'#73664d'),smooth(.72,.96,Math.abs(sign))*.57);
     const ground=colorFor(xx,zz,terrainY).clone();
     tint.lerp(ground,shoulder*.96);
     routeColors.push(tint.r,tint.g,tint.b);
   }
   if(i<count)for(let j=0;j<across;j++){
     const k=i*(across+1)+j;ind.push(k,k+1,k+across+1,k+1,k+across+2,k+across+1);
   }
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setAttribute('color',new THREE.Float32BufferAttribute(routeColors,3));g.setIndex(ind);g.computeVertexNormals();
 const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({vertexColors:true,roughness:1}));m.receiveShadow=false;terrain.add(m);return m;
}
routeMesh();
// Two physically raised edges make the route readable when the island is
// viewed from the forest side. They are one continuous mesh per side, rather
// than repeated screen-facing UI lines; they follow the same sampled grade.
function routeKerb(side){
 const positions=[],colors=[],indices=[],count=340;
 for(let i=0;i<=count;i++){
   const x=-22.15+i/count*44.2,z=routeZ(x),t=(routeZ(x+.04)-routeZ(x-.04))/.08;
   const forestBand=smooth(-13,-10,x)*(1-smooth(1,4,x));
   const perpX=-t/Math.hypot(1,t),perpZ=1/Math.hypot(1,t);
   const crest=x>13?'#b7c4bf':x>2?'#d2a06a':'#bca178';
   for(let edge=0;edge<2;edge++){
     const offset=side*(1.28-.19*forestBand+edge*.10),xx=x+perpX*offset,zz=z+perpZ*offset;
     positions.push(xx,groundHeight(xx,zz)+.19-edge*.035,zz);
     const color=new THREE.Color(crest);color.offsetHSL(0,0,(noise(x*1.3,side*3)-.5)*.075);
     colors.push(color.r,color.g,color.b);
   }
   if(i<count){const j=i*2;indices.push(j,j+1,j+2,j+1,j+3,j+2);}
 }
 const geometry=new THREE.BufferGeometry();
 geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
 geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
 geometry.setIndex(indices);geometry.computeVertexNormals();
 const edge=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,side:THREE.DoubleSide}));
 edge.receiveShadow=true;terrain.add(edge);
}
routeKerb(-1);routeKerb(1);
// A shallow retaining fascia makes the quarry traverse read as a built road
// rather than a pale decal on the cut bank.
{
 const verts=[],colors=[],indices=[],count=110;
 for(let i=0;i<=count;i++){
   const x=2.0+i/count*10.8,z=routeZ(x)+1.15,y=groundHeight(x,z)+.18;
   verts.push(x,y,z,x,y-.42,z+.045);
   const tint=new THREE.Color(i%9<4?'#a26c43':'#885237');
   for(let j=0;j<2;j++)colors.push(tint.r,tint.g,tint.b);
   if(i<count){const k=i*2;indices.push(k,k+1,k+2,k+1,k+3,k+2);}
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.setIndex(indices);g.computeVertexNormals();
 const wall=new THREE.Mesh(g,new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,side:THREE.DoubleSide}));wall.castShadow=true;wall.receiveShadow=true;terrain.add(wall);
}
// Off-road dust and wheel marks keep the route legible from the default camera.
const tire=mat('#8b724e');
for(const offset of [-.36,.36]){
 const pts=[];for(let i=0;i<310;i++){const x=-22+i/309*44,z=routeZ(x)+offset;pts.push(new THREE.Vector3(x,groundHeight(x,z)+.15,z));}
 line(pts,tire,.012);
}
// Three distinct roadside civil works articulate the biomes at the same scale
// as the rally towers. Their low rails trace the actual graded road in both
// orbit directions without turning each stop into an arena.
function roadBarrier(x0,x1,step,side,postMaterial,railMaterial,clearance){
 const crest=[];
 for(let x=x0;x<=x1+.001;x+=step){
   const z=routeZ(x)+side*1.79,y=groundHeight(x,z);
   if(edgeDistance(x,z)>.91)continue;
   const post=box(.105,clearance,.11,postMaterial,x,y+clearance*.5,z);
   post.castShadow=true;
   crest.push(new THREE.Vector3(x,y+clearance*.84,z));
   if(crest.length%3===0){
     const brace=box(.065,clearance*.86,.075,postMaterial,x+.09,y+clearance*.43,z+side*.11);
     brace.rotation.z=.28*side;
   }
 }
 if(crest.length>1)line(crest,railMaterial,.055);
}
roadBarrier(-10.1,-6.0,.46,-1,mat('#655440'),mat('#a28259'),.82);
roadBarrier(7.0,11.9,.52,1,mat('#5b5048',.7,.28),mat('#b07e4f',.72,.12),.87);
roadBarrier(15.0,20.6,.54,-1,mat('#69777a',.73,.13),mat('#a9b6b5',.8,.09),.76);

// Three authored crown profiles make the forests read as stands of trees, not
// one repeated stamp. Snow remains a dark conifer with snow caught on the
// upper boughs, so the snow biome has contrast against the pale mountains.
function firGeometry(snowy,species){
 const p=[],colors=[];
 const tri=(a,b,c,color)=>{p.push(...a,...b,...c);const tint=new THREE.Color(color);for(let j=0;j<3;j++)colors.push(tint.r,tint.g,tint.b);};
 const profiles=[
   {levels:6,arms:9,base:.52,rise:.245,tip:1.7,top:'#3c7952',light:'#70a06a',shade:'#193d31'},
   {levels:5,arms:8,base:.61,rise:.305,tip:1.66,top:'#245d48',light:'#4e8968',shade:'#15382f'},
   {levels:7,arms:7,base:.39,rise:.225,tip:1.88,top:'#627e4d',light:'#a2a468',shade:'#344c38'},
 ];
 const s=profiles[species];
 for(let level=0;level<s.levels;level++){
   const y=.41+level*s.rise,rad=s.base*(1-level/s.levels*.78);
   for(let k=0;k<s.arms;k++){
     const angle=k/s.arms*Math.PI*2+level*.34;
     const jag=.82+.14*Math.sin(k*4.13+level*7.71+species*2.1);
     const center=[Math.cos(angle)*.02,y+.38,Math.sin(angle)*.02];
     const left=[Math.cos(angle-.40)*rad*.8,y+.045,Math.sin(angle-.40)*rad*.8];
     const right=[Math.cos(angle+.40)*rad*.8,y+.045,Math.sin(angle+.40)*rad*.8];
     const tip=[Math.cos(angle)*rad*jag,y-.11-.04*(k%3),Math.sin(angle)*rad*jag];
     const underside=[Math.cos(angle)*rad*.34,y-.045,Math.sin(angle)*rad*.34];
     const snowCap=snowy && (level>1 || (k+level)%4!==0);
     const top=snowCap?(level>s.levels-3?'#eef1e8':'#b6c8c2'):(k%3===0?s.light:s.top);
     const shade=snowy?'#31584c':s.shade;
     tri(center,left,tip,top);tri(center,tip,right,top);
     tri(underside,tip,left,shade);tri(underside,right,tip,shade);
   }
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));
 g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.computeVertexNormals();return g;
}
const trunkGeo=new THREE.CylinderGeometry(.044,.095,.65,6),trunkMat=mat('#514433');
const foliageMat=new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,side:THREE.DoubleSide});
const treeKinds=[
 {snowy:false,species:0,capacity:170,core:'#28553e'},
 {snowy:false,species:1,capacity:160,core:'#1a493a'},
 {snowy:false,species:2,capacity:125,core:'#526b40'},
 {snowy:true,species:0,capacity:65,core:'#315c50'},
 {snowy:true,species:1,capacity:65,core:'#254b43'},
 {snowy:true,species:2,capacity:50,core:'#566c55'},
].map(kind=>({
 ...kind,count:0,
 trunk:new THREE.InstancedMesh(trunkGeo,trunkMat,kind.capacity),
 canopy:new THREE.InstancedMesh(firGeometry(kind.snowy,kind.species),foliageMat,kind.capacity),
 core:new THREE.InstancedMesh(new THREE.ConeGeometry(.25,kind.species===2?1.46:1.20,7),mat(kind.core),kind.capacity),
}));
const dum=new THREE.Object3D();
let nForest=0,nSnow=0;
for(let tries=0;tries<15000&&(nForest<350||nSnow<145);tries++){
 const x=rr(-23.6,24.1),z=rr(-8.7,8.7); if(edgeDistance(x,z)>.87 || Math.abs(routeZ(x)-z)<4.55)continue;
 const snowy=x>12.5; if(snowy ? nSnow>=145 : nForest>=350)continue;
 if(!snowy&&(x>1.8&&x<13.0 || x<-11.2&&rand()<.71))continue;
 if(x>-8.0&&x<-2.9&&z>3.5&&z<8.0)continue;
 // Three cuttings through the back-facing woodland keep the route and its
 // towers visible during a reverse orbit, instead of one unbroken fir wall.
 const rear=z<routeZ(x)-2.0;
 if(rear&&x>-10.8&&x<2.0&&[
   [-8.7,1.55],[-4.3,1.25],[-.2,1.60],
 ].some(([cx,r])=>Math.abs(x-cx)<r+.20*Math.sin(z*1.8+cx)))continue;
 // A mottled density field leaves sunlit clearings and groups conifers into
 // recognizable stands; no planted-looking rows along the road.
 const density=.59+.36*noise(x*.26,z*.29)+.17*noise(x*.75,z*.75);
 if(rand()>density)continue;
 const species=rand()<.43?0:rand()<.62?1:2;
 const kind=treeKinds[(snowy?3:0)+species];if(kind.count>=kind.capacity)continue;
 const h=groundHeight(x,z),scale=(species===2?rr(.56,1.28):rr(.67,1.48))*(snowy?.88:1),rot=rr(0,6.28);
 const tIdx=kind.count++;
 if(snowy)nSnow++;else nForest++;
 dum.position.set(x,h+.29*scale,z);dum.rotation.set(0,rot,0);dum.scale.setScalar(scale);dum.updateMatrix();
 kind.trunk.setMatrixAt(tIdx,dum.matrix);
 dum.position.set(x,h,z);dum.updateMatrix();
 kind.canopy.setMatrixAt(tIdx,dum.matrix);
 dum.position.set(x,h+(species===2?1.07:.96)*scale,z);dum.updateMatrix();
 kind.core.setMatrixAt(tIdx,dum.matrix);
 const shade=new THREE.Color('#ffffff').multiplyScalar(rr(.84,1.13));
 kind.canopy.setColorAt(tIdx,shade);
}
for(const kind of treeKinds)for(const obj of [kind.trunk,kind.canopy,kind.core]){
 obj.count=kind.count;
 // A third of the crowns cast the stand's broad shadows. Every crown still
 // shades in the sun, while the software shadow pass loses most tiny triangles.
 obj.castShadow=obj===kind.trunk||(obj===kind.canopy&&kind.species===0);
 obj.receiveShadow=true;terrain.add(obj);
}

// The selected island has a tall woodland skyline behind the trail. Fill the
// far ridge with staggered crowns, while leaving the three narrow sightlines
// through the reverse view open. Shared tree geometry keeps this to three
// instanced draws; the nearer randomized stands still shape the clearings.
const skylineCapacity=84;
const skylineTrunks=new THREE.InstancedMesh(trunkGeo,trunkMat,skylineCapacity);
const skylineCrowns=new THREE.InstancedMesh(treeKinds[0].canopy.geometry,foliageMat,skylineCapacity);
const skylineCores=new THREE.InstancedMesh(treeKinds[0].core.geometry,treeKinds[0].core.material,skylineCapacity);
let skylineCount=0;
for(let row=0;row<3;row++)for(let col=0;col<29;col++){
 const x=-10.9+col*.46+(hash2(col+41,row+7)-.5)*.30;
 const z=-5.35-row*.78+(hash2(col+19,row+27)-.5)*.52;
 if(skylineCount>=skylineCapacity||edgeDistance(x,z)>.83||z>routeZ(x)-4.1)continue;
 if([[-8.7,.47],[-4.3,.42],[-.2,.48]].some(([center,halfWidth])=>Math.abs(x-center)<halfWidth))continue;
 const h=groundHeight(x,z),scale=1.15+row*.13+.36*hash2(col+73,row+13);
 const turn=hash2(col+5,row+67)*Math.PI*2;
 const index=skylineCount++;
 dum.position.set(x,h+.29*scale,z);dum.rotation.set(0,turn,0);dum.scale.setScalar(scale);dum.updateMatrix();
 skylineTrunks.setMatrixAt(index,dum.matrix);
 dum.position.set(x,h,z);dum.updateMatrix();skylineCrowns.setMatrixAt(index,dum.matrix);
 dum.position.set(x,h+.96*scale,z);dum.updateMatrix();skylineCores.setMatrixAt(index,dum.matrix);
 skylineCrowns.setColorAt(index,new THREE.Color('#ffffff').multiplyScalar(.84+.24*hash2(col+97,row+41)));
}
for(const obj of [skylineTrunks,skylineCrowns,skylineCores]){
 obj.count=skylineCount;obj.castShadow=false;obj.receiveShadow=true;terrain.add(obj);
}

// Mixed broadleaf clumps open the solid wall of identical conifer points.
// Their three offset crown lobes turn as one 3D tree, with copper foliage
// appearing near the quarry boundary and cooler greens in the deepwood.
const broadTrunk=new THREE.InstancedMesh(new THREE.CylinderGeometry(.045,.105,1.0,6),mat('#8a765e'),50);
const broadCanopy=new THREE.InstancedMesh(new THREE.IcosahedronGeometry(.52,0),mat('#ffffff'),150);
let broadCount=0,crownCount=0;
for(let tries=0;tries<1800&&broadCount<38;tries++){
 const x=rr(-11.2,3.0),z=rr(-7.8,7.5);
 if(edgeDistance(x,z)>.84||Math.abs(routeZ(x)-z)<4.2||Math.hypot(x+5.5,z-5.2)<2.6)continue;
 const h=groundHeight(x,z),scale=rr(.65,1.16),rotation=rr(0,6.28);
 dum.position.set(x,h+.79*scale,z);dum.rotation.set(0,rotation,0);dum.scale.setScalar(scale);dum.updateMatrix();
 broadTrunk.setMatrixAt(broadCount++,dum.matrix);
 const copper=smooth(-1.2,2.7,x),tones=copper>.55?['#927b55','#ae915e','#6d7858']:['#718a53','#4f7654','#a1a265'];
 for(let j=0;j<3;j++){
   const a=rotation+j*Math.PI*2/3,offset=j===0?.0:.28;
   dum.position.set(x+Math.cos(a)*offset*scale,h+(1.57+(j%2)*.15)*scale,z+Math.sin(a)*offset*scale);
   dum.rotation.set(rr(-.12,.12),rr(0,6.28),rr(-.12,.12));dum.scale.setScalar(scale*(j===0?.86:.60));dum.updateMatrix();
   broadCanopy.setMatrixAt(crownCount,dum.matrix);
   broadCanopy.setColorAt(crownCount,new THREE.Color(tones[j]));crownCount++;
 }
}
broadTrunk.count=broadCount;broadCanopy.count=crownCount;
for(const obj of [broadTrunk,broadCanopy]){obj.castShadow=true;obj.receiveShadow=true;terrain.add(obj);}

// A timber fire lookout crowns the forest instead of adding another generic
// hut at road level. The observation windows remain visible in the orbit.
const lookout=new THREE.Group();lookout.position.set(-7.6,groundHeight(-7.6,-5.8),-5.8);lookout.scale.setScalar(.83);terrain.add(lookout);
const lookoutWood=mat('#695a43'),lookoutRoof=mat('#9a5940'),lookoutGlass=mat('#4a727a',.23);
for(const dx of [-.53,.53])for(const dz of [-.46,.46]){
 const leg=box(.12,2.9,.12,lookoutWood,dx,1.46,dz,lookout);leg.castShadow=true;
}
for(const side of [-1,1]){
 spanBeam(new THREE.Vector3(-.53,.26,side*.46),new THREE.Vector3(.53,2.72,side*.46),.055,.055,lookoutWood,lookout);
 spanBeam(new THREE.Vector3(.53,.26,side*.46),new THREE.Vector3(-.53,2.72,side*.46),.055,.055,lookoutWood,lookout);
}
box(1.43,.17,1.22,lookoutWood,0,2.83,0,lookout).castShadow=true;
box(1.17,.75,1.05,lookoutWood,0,3.27,0,lookout).castShadow=true;
for(const side of [-1,1]){
 box(.63,.35,.04,lookoutGlass,0,3.34,side*.55,lookout);
 box(.04,.35,.60,lookoutGlass,side*.60,3.34,0,lookout);
}
const lookoutCap=box(1.53,.16,1.31,lookoutRoof,0,3.74,0,lookout);lookoutCap.castShadow=true;
cylinder(.035,.035,.96,mat('#454843'),.48,4.30,-.37,lookout);
const lookoutFlag=box(.47,.18,.025,mat('#d2623e'),.74,4.51,-.37,lookout);lookoutFlag.rotation.z=-.11;

// Distinct rock palettes push the quarry and glacial ridge apart visually.
for(const [xMin,xMax,count,palette] of [
 [-24,-10,180,['#77766a','#938b78','#66635c']],
 [-10,3,100,['#717d6a','#7e846c','#555f54']],
 [2,14,120,['#af754d','#cf9562','#8f5b3d']],
 [13,25,110,['#e4e8df','#acbdc0','#8d9da1']]]){
 const rockGeo=new THREE.IcosahedronGeometry(1,0);
 const instances=palette.map(hex=>new THREE.InstancedMesh(rockGeo,mat(hex),Math.ceil(count/palette.length)+12));
 const totals=[0,0,0];
 for(let i=0;i<count;i++){
   const x=rr(xMin,xMax),z=rr(-9,9); if(edgeDistance(x,z)>.95||Math.abs(routeZ(x)-z)<.65)continue;
   const h=groundHeight(x,z),s=rr(.08,.43)*(x>13?1.4:1),p=i%3;
   dum.position.set(x,h+s*.34,z);dum.rotation.set(rr(0,2),rr(0,6),rr(0,2));dum.scale.set(s,s*rr(.55,1.45),s*rr(.7,1.4));dum.updateMatrix();
   instances[p].setMatrixAt(totals[p]++,dum.matrix);
 }
 instances.forEach((o,i)=>{o.count=totals[i];o.castShadow=true;o.receiveShadow=true;terrain.add(o);});
}

// The island needed a middle scale between the terrain colors and its large
// trees. Patchy heath, sedge and frost shrubs make each clearing feel planted
// by its climate. Each biome uses one shared mesh and one draw call.
function groundCoverGeometry(kind){
 const p=[],colors=[],indices=[];
 const palette=kind===0?['#758652','#586c45','#a7a16d']:
   kind===1?['#658458','#466c54','#9ba971']:
   kind===2?['#b68a58','#8d714f','#d1aa70']:
             ['#718f8b','#aebeb9','#eff1df'];
 for(let blade=0;blade<5;blade++){
   const angle=blade*Math.PI*2/5,rad=.105+(blade%2)*.045;
   const x=Math.cos(angle)*rad,z=Math.sin(angle)*rad;
   const height=(kind===3?.31:.22)+.08*Math.sin(blade*3+kind);
   const base=p.length/3;
   p.push(x-.075,0,z,x+.075,0,z,x*.39,height,z*.39);
   const tint=new THREE.Color(palette[blade%3]);
   for(let j=0;j<3;j++)colors.push(tint.r,tint.g,tint.b);
   indices.push(base,base+1,base+2);
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));
 g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.setIndex(indices);g.computeVertexNormals();
 return g;
}
const coverMat=new THREE.MeshStandardMaterial({vertexColors:true,side:THREE.DoubleSide,roughness:1});
const coverCapacity=[290,540,190,170];
const covers=[0,1,2,3].map(biome=>new THREE.InstancedMesh(groundCoverGeometry(biome),coverMat,coverCapacity[biome]));
const coverCount=[0,0,0,0];
for(let i=0;i<3300;i++){
 const x=rr(-24,24),z=rr(-9.5,9.5),biome=x>12.8?3:x>2.3?2:x>-10?1:0;
 if(coverCount[biome]>=covers[biome].count||edgeDistance(x,z)>.83||Math.abs(routeZ(x)-z)<1.42)continue;
 const y=groundHeight(x,z),s=rr(.58,1.60)*(biome===3?.76:1);
 dum.position.set(x,y+.025,z);dum.rotation.set(0,rr(0,6.28),0);dum.scale.setScalar(s);dum.updateMatrix();
 covers[biome].setMatrixAt(coverCount[biome]++,dum.matrix);
}
covers.forEach((o,i)=>{o.count=coverCount[i];o.receiveShadow=true;terrain.add(o);});

// Road edge stakes are deliberately lower than the selectable flag towers.
// They keep the pale trail legible from the reverse orbit without icon plates.
const stakeGeo=new THREE.CylinderGeometry(.055,.075,.57,5),stakeMat=mat('#66594c');
const stakes=new THREE.InstancedMesh(stakeGeo,stakeMat,62);
const stakeCount={value:0};
for(let x=-21.0;x<22.0;x+=1.38){
 const z=routeZ(x)+(Math.floor((x+21)/1.38)%2?1.33:-1.33),y=groundHeight(x,z);
 if(edgeDistance(x,z)>.89)continue;
 dum.position.set(x,y+.29,z);dum.rotation.set(0,rr(0,6.28),0);dum.scale.setScalar(rr(.8,1.3));dum.updateMatrix();
 stakes.setMatrixAt(stakeCount.value++,dum.matrix);
}
stakes.count=stakeCount.value;stakes.castShadow=true;terrain.add(stakes);

// Each summit is a small joined ridge rather than a smooth, repeated cone.
// The feet sample the island height field, so the broad rock shoulders meet
// the snow ground without an obvious cylindrical collar when the map turns.
const mountainMaterial=new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,flatShading:true,side:THREE.DoubleSide});
function mountain(x,z,rx,rz,height,phase){
 const sectors=17,levels=[0,.12,.27,.43,.59,.73,.85,.94,1];
 const widths=[1,.91,.79,.65,.51,.37,.24,.12,0];
 const points=[],positions=[],colors=[];
 for(let l=0;l<levels.length;l++){
   const ring=[];
   for(let k=0;k<sectors;k++){
     const a=k/sectors*Math.PI*2,up=levels[l];
     const shoulder=1+.12*Math.sin(a*3+phase)+.065*Math.sin(a*7-phase*.7)
       +.04*Math.sin(a*11+l*.9+phase);
     const r=widths[l]*shoulder;
     const wx=x+Math.cos(a)*rx*r+up*up*.24;
     const wz=z+Math.sin(a)*rz*r-up*up*.12;
     const rise=height*up+(.08*Math.sin(k*2.4+phase+l*.8))*Math.sin(up*Math.PI);
     ring.push({x:wx,y:groundHeight(wx,wz)+rise-.10,z:wz,rise});
   }
   points.push(ring);
 }
 const addFace=(a,b,c,l,k)=>{
   positions.push(a.x,a.y,a.z,b.x,b.y,b.z,c.x,c.y,c.z);
   const elevation=(a.rise+b.rise+c.rise)/(3*height);
   const cut=.35+.07*Math.sin(k*.85+phase)+.03*Math.sin(k*2.6+l*.4);
   const couloir=Math.sin(k*1.15+phase)>.72&&l<6;
   const exposed=elevation>cut && couloir;
   const snow=elevation>cut&&!exposed;
   const shade=.5+.5*Math.sin(k*2.55+l*1.1+phase);
   const tint=new THREE.Color(snow?'#d7e4e1':exposed?'#66818a':'#61777e');
   tint.lerp(new THREE.Color(snow?'#fffdf0':exposed?'#aec0be':'#a4aaa7'),shade*(snow?.72:.60));
   if(!snow&&!exposed&&elevation<.17)tint.lerp(new THREE.Color('#a5b9b7'),.32);
   for(let v=0;v<3;v++)colors.push(tint.r,tint.g,tint.b);
 };
 for(let l=0;l<levels.length-1;l++)for(let k=0;k<sectors;k++){
   const next=(k+1)%sectors;
   addFace(points[l][k],points[l][next],points[l+1][k],l,k);
   addFace(points[l][next],points[l+1][next],points[l+1][k],l,k);
 }
 const g=new THREE.BufferGeometry();
 g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
 g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.computeVertexNormals();
 const o=mesh(g,mountainMaterial,0,0,0);
 o.castShadow=true;o.receiveShadow=true;
}
mountain(15.4,4.7,2.75,2.60,2.95,.7);
mountain(18.4,-4.9,2.65,2.65,3.55,1.8);
mountain(13.9,-5.5,2.20,2.25,2.60,3.2);

// Open-cut quarry benches follow an irregular horseshoe; each wall and shelf has volume.
const sandstone=mat('#a6633b'),ore=mat('#755849');
const quarryFaceMaterial=new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,side:THREE.DoubleSide,flatShading:true});
function quarryBench(rx,rz,raise,shift){
 const n=64,wallPos=[],ledgePos=[],faceColors=[],ledgeColors=[],wallIdx=[],ledgeIdx=[];
 for(let i=0;i<=n;i++){
   const a=-.22*Math.PI+i/n*1.47*Math.PI;
   const ripple=1+.09*Math.sin(5*a+shift)+.035*Math.sin(13*a+shift*.7);
   const cx=7.3,cz=-3.5,x=cx+Math.cos(a)*rx*ripple,z=cz+Math.sin(a)*rz*ripple;
   const nx=Math.cos(a),nz=Math.sin(a),ground=groundHeight(x,z),top=ground+raise+.1*Math.sin(a*9);
   wallPos.push(x,ground+.015,z,x,top,z);
   ledgePos.push(x,top,z,x+nx*.35,groundHeight(x+nx*.35,z+nz*.35)+raise*.75,nz*.35+z);
   const cc=new THREE.Color(i%6===0?'#814b32':i%3===0?'#a35e38':'#ba7546');
   for(let k=0;k<2;k++)faceColors.push(cc.r,cc.g,cc.b);
   const ll=new THREE.Color(i%5===0?'#b77545':'#cd925a');
   for(let k=0;k<2;k++)ledgeColors.push(ll.r,ll.g,ll.b);
   if(i<n){const j=i*2;wallIdx.push(j,j+1,j+2,j+1,j+3,j+2);ledgeIdx.push(j,j+1,j+2,j+1,j+3,j+2);}
 }
 for(const [positions,colors,idx] of [[wallPos,faceColors,wallIdx],[ledgePos,ledgeColors,ledgeIdx]]){
   const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
   g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.setIndex(idx);g.computeVertexNormals();
   const o=new THREE.Mesh(g,quarryFaceMaterial);
   o.castShadow=true;o.receiveShadow=true;terrain.add(o);
 }
}
quarryBench(4.8,3.0,.46,.4);
quarryBench(3.55,2.25,.68,1.4);
quarryBench(2.2,1.4,.9,2.1);
const quarryRoad=mat('#e5b674');
for(let i=0;i<12;i++){
  const x=rr(3.3,11.2),z=rr(-5.6,-1.7),y=groundHeight(x,z);
  const shard=mesh(new THREE.DodecahedronGeometry(rr(.08,.26),0),i%3?sandstone:quarryRoad,x,y+.08,z);
  shard.scale.set(rr(.6,1.3),rr(.45,1.8),rr(.6,1.4));shard.rotation.set(rr(0,3),rr(0,6),rr(0,3));
}
for(let i=0;i<8;i++){
 const x=rr(3,12),z=rr(-5,-2),h=groundHeight(x,z);
 const b=box(rr(.3,.9),rr(.2,.5),rr(.22,.7),ore,x,h+.15,z);b.rotation.y=rr(0,6.28);
}
const conveyorIron=mat('#514945',.62,.45),conveyorWood=mat('#785a43');
const beltA=new THREE.Vector3(3.7,groundHeight(3.7,-4.3)+1.25,-4.3);
const beltB=new THREE.Vector3(11.8,groundHeight(11.8,-4.4)+1.8,-4.4);
spanBeam(beltA,beltB,.18,.58,conveyorIron);
for(const side of [-1,1]){
 line([new THREE.Vector3(beltA.x,beltA.y+.21,beltA.z+side*.32),new THREE.Vector3(beltB.x,beltB.y+.21,beltB.z+side*.32)],conveyorWood,.043);
 for(let i=0;i<=8;i++){
   const t=i/8,x=THREE.MathUtils.lerp(beltA.x,beltB.x,t),z=-4.4,y=THREE.MathUtils.lerp(beltA.y,beltB.y,t);
   const foot=groundHeight(x,z);
   spanBeam(new THREE.Vector3(x,foot,z+side*.33),new THREE.Vector3(x,y,z+side*.33),.055,.055,conveyorIron);
   if(i<8)spanBeam(new THREE.Vector3(x,foot+.25,z+side*.33),new THREE.Vector3(x+1.0,THREE.MathUtils.lerp(beltA.y,beltB.y,(i+1)/8),z+side*.33),.03,.03,conveyorIron);
 }
}
const excavator=new THREE.Group();excavator.position.set(9.2,groundHeight(9.2,-1.9),-1.9);excavator.rotation.y=-.5;terrain.add(excavator);
box(1.2,.35,.65,mat('#644c3e'),0,.28,0,excavator).castShadow=true;
for(const side of [-1,1]){
 const track=mesh(new THREE.CylinderGeometry(.24,.24,1.28,12),mat('#343838'),0,.24,side*.43,excavator);track.rotation.z=Math.PI/2;
}
box(.83,.64,.67,mat('#d59643'),-.15,.78,0,excavator).castShadow=true;
box(.28,.36,.03,mat('#3c5d67',.15),-.35,.86,.35,excavator);
spanBeam(new THREE.Vector3(.25,.95,0),new THREE.Vector3(1.42,1.76,0),.17,.23,mat('#a86f38'),excavator);
spanBeam(new THREE.Vector3(1.42,1.76,0),new THREE.Vector3(2.08,1.16,0),.13,.18,mat('#a86f38'),excavator);
box(.45,.20,.40,ore,2.20,1.05,0,excavator).rotation.z=.27;
// A haul truck gives the quarry an unmistakable working scale at wide view.
const truck=new THREE.Group();truck.position.set(6.2,groundHeight(6.2,-2.0)+.10,-2.0);truck.rotation.y=.36;terrain.add(truck);
const truckYellow=mat('#cfa25a'),truckDark=mat('#3a403d'),truckSteel=mat('#68605a');
box(1.65,.26,.78,truckDark,0,.45,0,truck).castShadow=true;
box(.72,.68,.76,truckYellow,-.48,.88,0,truck).castShadow=true;
box(.36,.30,.025,mat('#36545d',.24),-.59,1.03,.395,truck);
const hopper=box(.96,.43,.83,truckYellow,.46,.90,0,truck);hopper.rotation.z=-.12;hopper.castShadow=true;
box(.94,.07,.83,truckSteel,.46,.68,0,truck);
for(const x of [-.53,.55])for(const z of [-.46,.46]){
 const wheel=mesh(new THREE.CylinderGeometry(.33,.33,.16,12),truckDark,x,.34,z,truck);wheel.rotation.x=Math.PI/2;wheel.castShadow=true;
 const hub=mesh(new THREE.CylinderGeometry(.13,.13,.165,10),truckSteel,x,.34,z+Math.sign(z)*.015,truck);hub.rotation.x=Math.PI/2;
}
// A fixed mine headframe gives the excavation a readable industrial skyline.
const mineFrame=new THREE.Group();mineFrame.position.set(4.7,groundHeight(4.7,-5.1),-5.1);terrain.add(mineFrame);
const mineIron=mat('#684d43',.75,.22),mineTrim=mat('#bd8150');
for(const x of [-.63,.63]){
 spanBeam(new THREE.Vector3(x*1.38,.04,0),new THREE.Vector3(x*.54,3.45,0),.12,.14,mineIron,mineFrame);
 spanBeam(new THREE.Vector3(x*.54,3.45,0),new THREE.Vector3(0,3.85,0),.10,.12,mineIron,mineFrame);
}
for(const y of [.74,1.50,2.30,3.06])box(1.27,.09,.14,mineIron,0,y,0,mineFrame);
const pulley=mesh(new THREE.TorusGeometry(.42,.085,8,16),mineTrim,0,3.70,.13,mineFrame);pulley.castShadow=true;
line([new THREE.Vector3(0,3.70,.25),new THREE.Vector3(.17,.24,.25)],mat('#393a38',.62,.3),.016,mineFrame);
box(.72,.54,.65,mineTrim,0,.29,.10,mineFrame).castShadow=true;
for(let i=0;i<14;i++){
 const x=rr(2.2,7.7),z=rr(-7.3,-4.9),y=groundHeight(x,z),s=rr(.20,.49);
 const oreChunk=mesh(new THREE.IcosahedronGeometry(s,0),i%3?ore:sandstone,x,y+s*.55,z);
 oreChunk.scale.set(1.1,rr(.55,1.15),.8);
}
// A road bridge spans the eastern ravine on pillars.
for(let x=17.1;x<21.1;x+=.8){
 const z=routeZ(x),y=groundHeight(x,z);
 const deck=box(.78,.18,1.36,mat('#b9a992'),x,y+.16,z);deck.castShadow=true;
 for(const side of [-1,1]){
   const post=box(.11,.68,.11,mat('#8d9697'),x,y+.52,z+side*.66);post.castShadow=true;
   box(.76,.055,.085,mat('#68797c'),x,y+.83,z+side*.66);
 }
 const p=box(.16,Math.max(.5,y+1.4),.16,mat('#a8a9a2'),x,(y-1.3)/2,z+.6);p.castShadow=true;
}
const waterfallTop=groundHeight(-1.8,7.55)+.18;
const fallsPositions=[],fallsColors=[],fallsIndices=[];
for(let i=0;i<13;i++){
 const x=-2.45+i*.105+rr(-.025,.025),thickness=rr(.055,.105);
 const p=[x,waterfallTop,9.0,x+rr(-.08,.08),-1.11,10.0,x+thickness,waterfallTop,9.0,x+thickness+rr(-.08,.08),-1.11,10.0];
 const start=fallsPositions.length/3;fallsPositions.push(...p);
 const tint=new THREE.Color(i%3===0?'#f3ffff':'#a1dce1');
 for(let j=0;j<4;j++)fallsColors.push(tint.r,tint.g,tint.b);
 fallsIndices.push(start,start+1,start+2,start+2,start+1,start+3);
}
const fallsGeo=new THREE.BufferGeometry();fallsGeo.setAttribute('position',new THREE.Float32BufferAttribute(fallsPositions,3));fallsGeo.setAttribute('color',new THREE.Float32BufferAttribute(fallsColors,3));fallsGeo.setIndex(fallsIndices);fallsGeo.computeVertexNormals();
terrain.add(new THREE.Mesh(fallsGeo,new THREE.MeshBasicMaterial({vertexColors:true,transparent:true,opacity:.76,side:THREE.DoubleSide,depthWrite:false})));
const mist=new THREE.InstancedMesh(new THREE.IcosahedronGeometry(.16,1),new THREE.MeshBasicMaterial({color:'#eaf5ec',transparent:true,opacity:.5,depthWrite:false}),13);
for(let i=0;i<13;i++){
 dum.position.set(rr(-2.55,-1.1),-1.0+rr(-.14,.2),rr(9.8,10.4));dum.rotation.set(0,rr(0,6.28),0);dum.scale.set(rr(.6,1.2),.3,rr(.6,1.2));dum.updateMatrix();mist.setMatrixAt(i,dum.matrix);
}
terrain.add(mist);
const waterwheel=new THREE.Group();waterwheel.position.set(-3.38,groundHeight(-3.38,8.45)-.18,8.65);terrain.add(waterwheel);
const wheelWood=mat('#725941'),wheelRim=mat('#9b7651');
for(const depth of [-.12,.12]){
 const ring=mesh(new THREE.TorusGeometry(.65,.075,7,16),wheelRim,0,0,depth,waterwheel);ring.castShadow=true;
 for(let i=0;i<8;i++){
   const a=i*Math.PI/4;
   spanBeam(new THREE.Vector3(0,0,depth),new THREE.Vector3(Math.cos(a)*.61,Math.sin(a)*.61,depth),.06,.07,wheelWood,waterwheel);
 }
}
for(let i=0;i<8;i++){
 const a=i*Math.PI/4;
 const bucket=box(.30,.09,.38,wheelWood,Math.cos(a)*.68,Math.sin(a)*.68,0,waterwheel);
 bucket.rotation.z=a;bucket.castShadow=true;
}
const wheelAxle=cylinder(.12,.12,.55,mat('#4d443d'),0,0,0,waterwheel);wheelAxle.rotation.x=Math.PI/2;
for(const side of [-1,1])spanBeam(new THREE.Vector3(side*.75,-.72,-.37),new THREE.Vector3(0,0,-.34),.08,.08,wheelWood,waterwheel);

// Harbor: the boat, timber landing and crane are built as real volumes. Rods
// of one material are merged so the richer silhouette does not cost a draw
// per strut at the island's normal phone-sized framing.
const harborRoot=new THREE.Group();terrain.add(harborRoot);
const dock=mat('#574536'),woodTop=mat('#9b7652'),rust=mat('#9b4937'),roofMat=mat('#45443c');
function harborRods(segments,material,parent=harborRoot,sides=5){
 const up=new THREE.Vector3(0,1,0),parts=[];
 for(const [start,end,radius] of segments){
   const direction=new THREE.Vector3().subVectors(end,start),length=direction.length();
   const piece=new THREE.CylinderGeometry(radius,radius,length,sides);
   piece.applyMatrix4(new THREE.Matrix4().compose(
     new THREE.Vector3().addVectors(start,end).multiplyScalar(.5),
     new THREE.Quaternion().setFromUnitVectors(up,direction.normalize()),
     new THREE.Vector3(1,1,1)));
   parts.push(piece);
 }
 const joined=mergeGeometries(parts,false);
 for(const piece of parts)piece.dispose();
 const result=mesh(joined,material,0,0,0,parent);result.castShadow=true;
 return result;
}
function harborBoxes(parts,material,parent=harborRoot){
 const shapes=parts.map(([width,height,depth,x,y,z])=>{
   const shape=new THREE.BoxGeometry(width,height,depth);
   shape.translate(x,y,z);return shape;
 });
 const joined=mergeGeometries(shapes,false);
 for(const shape of shapes)shape.dispose();
 const result=mesh(joined,material,0,0,0,parent);result.castShadow=true;
 return result;
}
const lightPlanks=[],darkPlanks=[],dockPiles=[],dockRods=[];
for(let i=0;i<19;i++){
 const z=6.1+i*.215;
 (i%5===0?darkPlanks:lightPlanks).push([1.62,.13,.184,-17.0,-.37,z]);
 if(i%5===0)for(const offset of [-.69,.69]){
   dockPiles.push([.17,1.85,.18,-17.0+offset,-1.19,z]);
   dockRods.push([new THREE.Vector3(-17.0+offset,-.43,z),new THREE.Vector3(-17.0+offset,-.43,z+.70),.035]);
 }
}
harborBoxes(lightPlanks,woodTop);harborBoxes(darkPlanks,dock);harborBoxes(dockPiles,dock);
harborRods(dockRods,mat('#c1a47a'));
for(const z of [6.65,9.35]){
 const cleat=box(.29,.10,.10,mat('#3f4543',.52,.3),-16.22,-.19,z,harborRoot);cleat.castShadow=true;
}
for(let i=0;i<12;i++){
 const x=-18.0+(i%3)*.47,z=4.4+Math.floor(i/3)*.46,y=groundHeight(x,z);
 box(.39,.35,.33,mat(['#94563c','#5b6a64','#a48153'][i%3]),x,y+.18,z,harborRoot).castShadow=true;
}
const ship=new THREE.Group();ship.position.set(-17.5,-.73,9.45);ship.rotation.y=-.14;harborRoot.add(ship);
// Frame third value is sheer height: the fine bow lifts clear of the water.
const hullFrames=[[-2.75,.48,.38],[-2.35,.68,.31],[-1.25,.82,.28],[.2,.86,.29],[1.42,.77,.36],[2.33,.47,.53],[2.78,.06,.65]],hullP=[],hullC=[],hullI=[];
for(let i=0;i<hullFrames.length;i++){
 const [x,w,sheer]=hullFrames[i];
 const ring=[[x,sheer,-w],[x,-.10,-w*.90],[x,-.60,-w*.48],[x,-.68,0],[x,-.60,w*.48],[x,-.10,w*.90],[x,sheer,w]];
 for(const [px,py,pz] of ring){
   hullP.push(px,py,pz);
   const cc=new THREE.Color(py<-.42?'#36525c':py<.07?'#6c514a':'#a96848');
   cc.offsetHSL(0,0,i%2?.025:-.025);hullC.push(cc.r,cc.g,cc.b);
 }
 if(i<hullFrames.length-1)for(let j=0;j<6;j++){const a=i*7+j,b=a+7;hullI.push(a,b,a+1,a+1,b,b+1);}
}
const hullGeo=new THREE.BufferGeometry();hullGeo.setAttribute('position',new THREE.Float32BufferAttribute(hullP,3));
hullGeo.setAttribute('color',new THREE.Float32BufferAttribute(hullC,3));hullGeo.setIndex(hullI);hullGeo.computeVertexNormals();
const hull=mesh(hullGeo,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.79,metalness:.22,side:THREE.DoubleSide}),0,0,0,ship);hull.castShadow=true;
const gunwale=[],guardRail=[],railStanchions=[];
for(const side of [-1,1]){
 for(let i=0;i<hullFrames.length-1;i++){
   const [ax,aw,ay]=hullFrames[i],[bx,bw,by]=hullFrames[i+1];
   gunwale.push([new THREE.Vector3(ax,ay+.035,side*aw),new THREE.Vector3(bx,by+.035,side*bw),.052]);
   if(i>0){
     railStanchions.push([new THREE.Vector3(ax,ay,side*aw),new THREE.Vector3(ax,ay+.35,side*aw),.021]);
     guardRail.push([new THREE.Vector3(ax,ay+.35,side*aw),new THREE.Vector3(bx,by+.35,side*bw),.021]);
   }
 }
}
harborRods(gunwale,mat('#d7b488',.64,.12),ship,7);
harborRods([...guardRail,...railStanchions],mat('#434e50',.58,.32),ship);
// The open deck follows the taper instead of covering the hull with a cuboid.
const deckP=[0,.26,0],deckI=[];
for(const [x,w,sheer] of hullFrames)deckP.push(x,sheer-.045,-w*.86);
for(let i=hullFrames.length-1;i>=0;i--){const [x,w,sheer]=hullFrames[i];deckP.push(x,sheer-.045,w*.86);}
for(let i=1;i<deckP.length/3;i++)deckI.push(0,i,i===deckP.length/3-1?1:i+1);
const deckGeo=new THREE.BufferGeometry();deckGeo.setAttribute('position',new THREE.Float32BufferAttribute(deckP,3));deckGeo.setIndex(deckI);deckGeo.computeVertexNormals();
mesh(deckGeo,new THREE.MeshStandardMaterial({color:'#7d624b',roughness:.93,side:THREE.DoubleSide}),0,0,0,ship).receiveShadow=true;
box(1.16,.78,.97,mat('#d3bea0'),-1.24,.70,0,ship).castShadow=true;
const pilotRoof=box(1.47,.13,1.16,mat('#a54c34',.77,.1),-1.25,1.17,0,ship);
pilotRoof.rotation.z=-.11;pilotRoof.castShadow=true;
const glass=mat('#315d6b',.20);
for(const side of [-1,1]){
 box(.68,.32,.03,glass,-1.26,.83,side*.50,ship);
 box(.68,.038,.045,mat('#c7b494'),-1.26,.66,side*.52,ship);
}
box(.03,.32,.72,glass,-.64,.83,0,ship);
for(const z of [-.37,.37])box(.035,.34,.035,mat('#aa9b83'),-.62,.83,z,ship);
box(.65,.17,.92,mat('#9c724c'),1.61,.54,0,ship).castShadow=true;
const rubRail=[];
for(const side of [-1,1])for(let i=0;i<hullFrames.length-1;i++){
 const [ax,aw,ay]=hullFrames[i],[bx,bw,by]=hullFrames[i+1];
 rubRail.push([new THREE.Vector3(ax,ay-.23,side*aw*.96),new THREE.Vector3(bx,by-.23,side*bw*.96),.021]);
}
harborRods(rubRail,mat('#dec39c',.85),ship);
// Glazed gondolas and their cable make the snow pass distinct from the quarry
// trestle while staying below the level markers in silhouette.
const cable=mat('#596266',.55,.35),gondolaBlue=mat('#446472'),gondolaRoof=mat('#9aa7a8');
const cableA=new THREE.Vector3(13.9,groundHeight(13.9,-5.4)+2.02,-5.4);
const cableB=new THREE.Vector3(20.5,groundHeight(20.5,-5.4)+2.02,-5.4);
line([cableA,new THREE.Vector3(17.2,(cableA.y+cableB.y)/2-.22,-5.35),cableB],cable,.023);
for(const t of [.30,.68]){
 const x=THREE.MathUtils.lerp(cableA.x,cableB.x,t),z=-5.35,y=THREE.MathUtils.lerp(cableA.y,cableB.y,t)-.1;
 const cabin=new THREE.Group();cabin.position.set(x,y-.78,z);terrain.add(cabin);
 box(.72,.55,.47,gondolaBlue,0,0,0,cabin).castShadow=true;
 box(.78,.11,.52,gondolaRoof,0,.32,0,cabin).castShadow=true;
 for(const side of [-1,1])box(.44,.24,.025,mat('#a7d2d3',.14),0,.04,side*.252,cabin);
 box(.055,.35,.055,cable,0,.52,0,cabin);
}
for(let i=0;i<3;i++)box(.51,.28,.48,mat(i%2?'#6b5e4e':'#865c44'),.12+i*.58,.48,0,ship).castShadow=true;
for(let i=0;i<3;i++){
 const o=mesh(new THREE.TorusGeometry(.16,.045,7,12),mat('#ded6bd'),-.65+i*.68,.52,-.67,ship);
 o.rotation.y=Math.PI/2;
}
cylinder(.042,.06,2.15,mat('#4c4540'),-1.30,2.30,0,ship).castShadow=true;
const mastTop=new THREE.Vector3(-1.30,3.37,0);
harborRods([
 [mastTop,new THREE.Vector3(-2.49,.50,-.39),.017],
 [mastTop,new THREE.Vector3(2.10,.67,.44),.017],
 [new THREE.Vector3(-1.30,2.55,0),new THREE.Vector3(.16,1.49,-.18),.028],
 [new THREE.Vector3(-1.30,2.55,0),new THREE.Vector3(.16,1.49,.18),.028],
 ],mat('#484844',.64,.25),ship);
// A capped funnel and paired fenders remain legible at a distant orbit.
cylinder(.13,.18,.40,mat('#3d4949'),-.46,1.54,0,ship,7).castShadow=true;
cylinder(.17,.17,.06,mat('#b5774a'),-.46,1.76,0,ship,7);
for(const x of [-.60,.45,1.46]){
 const fender=mesh(new THREE.SphereGeometry(.135,6,5),mat('#d6c6a6'),x,.0,-.72,ship);
 fender.scale.set(.8,1.5,.7);
}
const craneX=-17.4,craneZ=6.1,craneY=groundHeight(craneX,craneZ);
const crane=new THREE.Group();crane.position.set(craneX,craneY,craneZ);harborRoot.add(crane);
box(1.02,.29,.82,mat('#715942'),0,.14,0,crane).castShadow=true;
const frame=[];
const cranePoint=(x,y,z)=>new THREE.Vector3(x,y,z);
for(const z of [-.30,.30]){
 const leftFoot=cranePoint(-.43,.29,z),rightFoot=cranePoint(.43,.29,z);
 const leftTop=cranePoint(-.28,4.18,z*.72),rightTop=cranePoint(.28,4.18,z*.72);
 frame.push([leftFoot,leftTop,.075],[rightFoot,rightTop,.075]);
 for(let i=0;i<5;i++){
   const y=.43+i*.72,yNext=y+.72;
   const width=.43-(y/4.18)*.15,nextWidth=.43-(yNext/4.18)*.15;
   frame.push([cranePoint(-width,y,z),cranePoint(width,y,z),.035]);
   frame.push([cranePoint(i%2?-width:width,y,z),cranePoint(i%2?nextWidth:-nextWidth,yNext,z),.032]);
 }
}
for(const y of [.68,1.95,3.25,4.12])for(const x of [-.33,.33]){
 frame.push([cranePoint(x,y,-.30),cranePoint(x,y,.30),.029]);
}
// Paired side chords give the cantilever a triangular section from any orbit.
const boomRoot=cranePoint(-.23,4.25,0),boomEnd=cranePoint(-3.87,4.56,.16);
for(const side of [-1,1]){
 const z=side*.22;
 const topRoot=cranePoint(boomRoot.x,boomRoot.y,z),topEnd=cranePoint(boomEnd.x,boomEnd.y,boomEnd.z+z*.47);
 const lowRoot=cranePoint(-.23,3.92,z),lowEnd=cranePoint(-3.86,4.29,boomEnd.z+z*.47);
 frame.push([topRoot,topEnd,.060],[lowRoot,lowEnd,.045]);
 for(let i=0;i<8;i++){
   const a=i/8,b=(i+1)/8;
   const high=topRoot.clone().lerp(topEnd,a),low=lowRoot.clone().lerp(lowEnd,b);
   frame.push([high,low,.027]);
 }
}
for(const t of [.25,.50,.75,1]){
 const x=THREE.MathUtils.lerp(boomRoot.x,boomEnd.x,t),y=THREE.MathUtils.lerp(boomRoot.y,boomEnd.y,t);
 frame.push([cranePoint(x,y,-.22),cranePoint(x,y,.22),.026]);
}
frame.push([cranePoint(.12,4.2,0),cranePoint(1.45,4.25,0),.065]);
frame.push([cranePoint(.36,4.08,-.19),cranePoint(1.45,4.25,0),.037]);
frame.push([cranePoint(.36,4.08,.19),cranePoint(1.45,4.25,0),.037]);
harborRods(frame,rust,crane);
box(.85,.42,.65,mat('#564940'),.12,4.31,0,crane).castShadow=true;
box(.61,.15,.62,mat('#bf6e46'),.12,4.59,0,crane).castShadow=true;
box(.44,.18,.52,mat('#5d4b3e'),1.34,3.99,0,crane).castShadow=true;
const craneCable=mat('#384044',.62,.39);
harborRods([
 [cranePoint(.10,5.15,0),boomEnd,.018],
 [cranePoint(.10,5.15,0),cranePoint(1.43,4.25,0),.018],
 [boomEnd,cranePoint(boomEnd.x,1.55,boomEnd.z),.018],
 ],craneCable,crane);
const hoist=mesh(new THREE.TorusGeometry(.20,.047,7,12),mat('#a16b4b',.64,.3),boomEnd.x,1.47,boomEnd.z,crane);
hoist.rotation.z=Math.PI/2;hoist.castShadow=true;
const hook=mesh(new THREE.TorusGeometry(.17,.052,7,12,Math.PI*1.55),mat('#353b3a',.6,.45),boomEnd.x,1.18,boomEnd.z,crane);
hook.rotation.z=Math.PI/2;hook.castShadow=true;
for(let i=0;i<6;i++){
 const x=-21.1+i*1.6,z=10.3+Math.sin(i*2.4)*.65;
 const buoy=mesh(new THREE.ConeGeometry(.18,.38,7),mat(i%2?'#dc8c43':'#e9d5a5'),x,-.72,z,harborRoot);
 buoy.castShadow=true;
 cylinder(.025,.035,.26,mat('#6e6a58'),x,-.47,z,harborRoot);
}
// Bake the static harbor into one vertex-painted mesh. The daylight map reads
// by silhouette and albedo at phone scale; tiny roughness differences did not
// survive the orbit capture, while the many separate materials cost 27 draws.
harborRoot.updateMatrixWorld(true);
const harborMeshes=[];harborRoot.traverse(object=>{if(object.isMesh)harborMeshes.push(object);});
const harborPieces=[];
const harborInverse=harborRoot.matrixWorld.clone().invert();
for(const object of harborMeshes){
 const source=object.geometry;
 const piece=source.index?source.toNonIndexed():source.clone();
 piece.applyMatrix4(harborInverse.clone().multiply(object.matrixWorld));
 const count=piece.attributes.position.count,vertexColor=piece.getAttribute('color');
 const tint=object.material.color||new THREE.Color('#ffffff');
 const colors=new Float32Array(count*3);
 for(let i=0;i<count;i++){
   colors[i*3]=(vertexColor?vertexColor.getX(i):1)*tint.r;
   colors[i*3+1]=(vertexColor?vertexColor.getY(i):1)*tint.g;
   colors[i*3+2]=(vertexColor?vertexColor.getZ(i):1)*tint.b;
 }
 for(const name of Object.keys(piece.attributes))if(name!=='position'&&name!=='normal')piece.deleteAttribute(name);
 piece.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
 harborPieces.push(piece);
 object.parent.remove(object);source.dispose();
}
const harborGeometry=mergeGeometries(harborPieces,false);
for(const piece of harborPieces)piece.dispose();
const harborPaint=new THREE.Mesh(harborGeometry,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.79,metalness:.12,side:THREE.DoubleSide}));
harborPaint.castShadow=true;harborRoot.add(harborPaint);
// A painted harbor light and stacked fishing traps anchor the bare rock head.
const lightHouse=new THREE.Group();lightHouse.position.set(-21.2,groundHeight(-21.2,-3.2),-3.2);terrain.add(lightHouse);
const lampWall=mat('#ded5bc'),lampRed=mat('#ad634b'),lampGlass=mat('#ebd5a3',.28);
cylinder(.40,.50,.75,lampWall,0,.38,0,lightHouse,10).castShadow=true;
cylinder(.35,.41,.46,lampRed,0,.98,0,lightHouse,10).castShadow=true;
cylinder(.30,.35,.78,lampWall,0,1.60,0,lightHouse,10).castShadow=true;
for(let i=0;i<4;i++){
 const a=i*Math.PI/2;
 const window=box(.26,.34,.035,lampGlass,Math.cos(a)*.32,2.06,Math.sin(a)*.32,lightHouse);
 window.rotation.y=-a;
}
cylinder(.43,.32,.12,lampRed,0,2.34,0,lightHouse,10).castShadow=true;
const beaconLamp=cylinder(.13,.13,.18,new THREE.MeshStandardMaterial({color:'#fff3bc',emissive:'#ffbd55',emissiveIntensity:1.4}),0,2.49,0,lightHouse,10);
beaconLamp.castShadow=false;
for(let i=0;i<6;i++){
 const x=-18.0+(i%3)*.44,z=5.0+Math.floor(i/3)*.47,y=groundHeight(x,z);
 const trap=box(.37,.24,.32,mat('#7b6650'),x,y+.13,z);trap.castShadow=true;
 for(const side of [-1,1])box(.38,.025,.025,mat('#b39569'),x,y+.26,z+side*.14);
}
// Forest sawmill and its log piles.
function building(x,z,w,d,body,roof){
 const y=groundHeight(x,z),wall=box(w,.8,d,body,x,y+.42,z);wall.castShadow=true;
 for(const side of [-1,1]){
   const slope=box(w+.17,.10,d*.62,roof,x,y+1.03,z+side*d*.245);
   slope.rotation.x=side*.42;slope.castShadow=true;
 }
 box(.36,.52,.05,mat('#2d3939'),x,y+.35,z+d*.51);
 for(const off of [-w*.30,w*.30])box(.26,.22,.045,mat('#517079',.22),x+off,y+.54,z+d*.52);
 box(.18,.65,.17,mat('#6b6152'),x+w*.31,y+1.34,z-d*.12).castShadow=true;
 return wall;
}
building(-5.5,5.2,3.1,1.6,mat('#66543d'),roofMat);
for(let i=0;i<11;i++){
 const x=rr(-8.1,-3.4),z=rr(4.0,6.6),y=groundHeight(x,z);
 const log=cylinder(.14,.14,1.5,woodTop,x,y+.2,z);log.rotation.z=Math.PI/2;log.castShadow=true;
}
// Quarry machinery and cable pylons are recognizable from wide view.
building(10.6,-5.8,1.8,1.25,mat('#705a48'),mat('#494843'));
// The upper pass is a tiny inhabited village, not a repeated prop cabin. Each
// house sits on its own stone footing; the roof silhouettes, balconies and
// timber frames stay legible from the road and from a reverse orbit. Snow is
// geometry laid across the slate roof, rather than a screen-facing decal.
const villageStone=mat('#89999a'),villageStoneDark=mat('#647a7c');
const villageTimber=mat('#694f3e'),villageTrim=mat('#ae8d6b');
const villageRoof=mat('#445864'),villageRoofDark=mat('#33454e');
const villageSnow=mat('#e3ece9'),villageSnowBright=mat('#faf8e9');
const villageGlass=mat('#254b54',.28,.12);
const villageWindowGlow=new THREE.MeshStandardMaterial({color:'#e9bb76',emissive:'#9d6332',emissiveIntensity:.62,roughness:.36});
const villageRoot=new THREE.Group();terrain.add(villageRoot);
function alpineHouse(x,z,w,d,angle,wallColor,kind=0){
 const house=new THREE.Group();house.position.set(x,groundHeight(x,z)+.04,z);house.rotation.y=angle;villageRoot.add(house);
 const wall=mat(wallColor),half=w*.5,sideHeight=kind===1?.96:1.12,roofRise=kind===2?.57:.70;
 const foot=box(w+.21,.35,d+.18,villageStone,0,.15,0,house);foot.castShadow=true;
 box(w+.30,.095,d+.26,villageStoneDark,0,.34,0,house);
 const body=box(w,sideHeight,d,wall,0,.39+sideHeight*.5,0,house);body.castShadow=true;
 // Gable triangles close the ends; the two broad pitches have true thickness.
 const gable=new THREE.Shape();gable.moveTo(-half,.39+sideHeight);gable.lineTo(half,.39+sideHeight);gable.lineTo(0,.39+sideHeight+roofRise);gable.closePath();
 const gableGeo=new THREE.ShapeGeometry(gable);
 for(const face of [-1,1]){
   const end=mesh(gableGeo,wall,0,0,face*d*.5,house);end.material.side=THREE.DoubleSide;
   const rail=box(w+.08,.075,.055,villageTimber,0,.40+sideHeight,face*(d*.5+.025),house);rail.castShadow=true;
 }
 const roofHalf=half+.18,angleRoof=Math.atan2(roofRise,half),roofLength=Math.hypot(roofHalf,roofRise)+.02;
 for(const side of [-1,1]){
   const pitch=box(roofLength,.115,d+.35,side===1?villageRoof:villageRoofDark,side*roofHalf*.46,.43+sideHeight+roofRise*.48,0,house);
   pitch.rotation.z=-side*angleRoof;pitch.castShadow=true;
   // Broken snow shelves follow each roof slope. A clear dark strip at the
   // eave keeps the building readable on the pale winter terrain.
   const snowShelf=box(roofLength*.82,.047,d+.38,side===1?villageSnowBright:villageSnow,side*roofHalf*.42,.54+sideHeight+roofRise*.48,0,house);
   snowShelf.rotation.z=-side*angleRoof;snowShelf.castShadow=true;
   const fascia=box(.065,.13,d+.41,villageTrim,side*(half+.12),.41+sideHeight,0,house);
   fascia.rotation.z=-side*angleRoof;fascia.castShadow=true;
 }
 const ridge=box(.15,.11,d+.41,villageSnowBright,0,.47+sideHeight+roofRise,0,house);ridge.castShadow=true;
 // The visible front has a real recessed entry, shutters and a lit window.
 const front=d*.5+.024;
 box(.36,.72,.07,villageTimber,-w*.21,.75,front,house);
 box(.23,.05,.075,villageTrim,-w*.21,1.02,front+.01,house);
 box(.30,.31,.055,villageWindowGlow,w*.20,.99,front,house);
 for(const dx of [-.19,.19])box(.065,.35,.075,villageTimber,w*.20+dx,.99,front+.02,house);
 box(.36,.055,.08,villageTrim,w*.20,.79,front+.04,house);
 for(const side of [-1,1]){
   const xx=side*(half+.035);
   for(const zz of [-d*.24,d*.24]){
     box(.047,.31,.31,villageGlass,xx,.99,zz,house);
     box(.07,.36,.045,villageTrim,xx,.99,zz-.17,house);
     box(.07,.36,.045,villageTrim,xx,.99,zz+.17,house);
   }
 }
 for(const xx of [-half+.09,half-.09])for(const zz of [-d*.5+.06,d*.5-.06]){
   const post=box(.095,sideHeight,.095,villageTimber,xx,.40+sideHeight*.5,zz,house);post.castShadow=true;
 }
 box(w+.04,.10,.12,villageTimber,0,.42,front+.045,house);
 // Stacked stone chimney with a contrasting cap; the taller lodge has a
 // small porch and balcony to give the group a hierarchy at phone scale.
 const chimney=box(.22,.82,.25,villageStoneDark,w*.23,.44+sideHeight+roofRise*.75,-d*.2,house);chimney.castShadow=true;
 box(.32,.11,.34,villageSnowBright,w*.23,.89+sideHeight+roofRise*.75,-d*.2,house).castShadow=true;
 if(kind===0){
   const porch=box(w*.64,.10,.48,villageTimber,0,.39,front+.27,house);porch.castShadow=true;
   for(const xx of [-w*.26,w*.26]){
     box(.07,.55,.07,villageTimber,xx,.71,front+.46,house).castShadow=true;
     box(.08,.07,.49,villageTrim,xx,.99,front+.23,house);
   }
   box(w*.57,.07,.08,villageTrim,0,.99,front+.46,house);
 }
 return house;
}
alpineHouse(18.8,-2.45,1.55,1.38,-.18,'#d9d7c8',1);
alpineHouse(20.62,-2.20,1.96,1.62,.18,'#c6c5b6',0);
alpineHouse(17.52,1.65,1.34,1.24,-.34,'#e2ddd0',2);
// Short stone retainers and timber steps make the houses belong to the slope.
for(const [x,z,rot,length] of [[18.8,-1.45,-.18,1.70],[20.60,-1.05,.18,2.08],[17.50,2.51,-.34,1.47]]){
 const y=groundHeight(x,z);
 const wall=box(length,.26,.18,villageStoneDark,x,y+.12,z,villageRoot);wall.rotation.y=rot;wall.castShadow=true;
 for(const end of [-1,1]){
   const cap=box(.15,.32,.24,villageStone,x+end*length*.49,y+.16,z,villageRoot);cap.rotation.y=rot;cap.castShadow=true;
 }
}
// The village has many tiny pieces, but one vertex-painted mesh at runtime.
// Keep roof, window and stone color while avoiding a draw per plank.
villageRoot.updateMatrixWorld(true);
const villageMeshes=[];villageRoot.traverse(object=>{if(object.isMesh)villageMeshes.push(object);});
const villageInverse=villageRoot.matrixWorld.clone().invert(),villagePieces=[];
for(const object of villageMeshes){
 const source=object.geometry,piece=source.index?source.toNonIndexed():source.clone();
 piece.applyMatrix4(villageInverse.clone().multiply(object.matrixWorld));
 const color=object.material.color||new THREE.Color('#ffffff'),colors=new Float32Array(piece.attributes.position.count*3);
 for(let i=0;i<piece.attributes.position.count;i++){
   colors[i*3]=color.r;colors[i*3+1]=color.g;colors[i*3+2]=color.b;
 }
 for(const name of Object.keys(piece.attributes))if(name!=='position'&&name!=='normal')piece.deleteAttribute(name);
 piece.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));villagePieces.push(piece);
 object.parent.remove(object);
}
const villageGeometry=mergeGeometries(villagePieces,false);
for(const piece of villagePieces)piece.dispose();
const villagePaint=mesh(villageGeometry,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.85,side:THREE.DoubleSide}),0,0,0,villageRoot);
villagePaint.castShadow=true;villagePaint.receiveShadow=true;
// Faceted blue ice tongues and fractured edges make the snow face an actual
// glacier rather than a white clone of the rocky coast.
const glacialIce=[mat('#a7cbd0'),mat('#c7dedc'),mat('#6f9ba8')];
for(let i=0;i<12;i++){
 const x=rr(14.5,22.6),z=rr(5.2,8.6);if(edgeDistance(x,z)>.92||Math.abs(routeZ(x)-z)<1.6)continue;
 const y=groundHeight(x,z),w=rr(.24,.68),h=rr(.45,1.22);
 const ice=mesh(new THREE.IcosahedronGeometry(1,0),glacialIce[i%3],x,y+h*.26,z);
 ice.scale.set(w,h,w*.7);ice.rotation.set(rr(-.2,.2),rr(0,6.28),rr(-.25,.25));ice.castShadow=true;
}
for(let i=0;i<5;i++){
 const x=15.2+i*1.5,z=7.3+Math.sin(i*2.2)*.5,y=groundHeight(x,z);
 const fissure=box(rr(.40,.85),.035,.09,mat('#436e7b'),x,y+.09,z);fissure.rotation.y=rr(-.5,.5);
}
for(let i=0;i<3;i++){
 const x=14.1+i*3.2,z=-5.4+Math.sin(i)*.8,y=groundHeight(x,z);
 box(.15,2.0,.15,mat('#5c686a'),x,y+1,z).castShadow=true;
 box(1.2,.13,.13,mat('#5c686a'),x,y+2,z).castShadow=true;
 if(i<2){const nx=x+3.2,nz=-5.4+Math.sin(i+1)*.8,ny=groundHeight(nx,nz);line([new THREE.Vector3(x,y+1.98,z),new THREE.Vector3(nx,ny+1.98,nz)],mat('#5c686a'),.024);}
}

const stages=[];
const towerMaterials={post:mat('#626363',.7,.55),brace:mat('#938b7c',.7,.3),lamp:mat('#fdd894',.28),red:mat('#d64936',.75),yellow:mat('#ebbd53',.73),black:mat('#262e30',.8),cream:mat('#eee8d2',.8)};
function makeFlag(width,height,color,parent,y){
 const shape=new THREE.Shape();shape.moveTo(0,0);shape.lineTo(width*.8,.06);shape.lineTo(width,height*.39);shape.lineTo(width*.81,height*.86);shape.lineTo(0,height);shape.closePath();
 const flag=new THREE.Mesh(new THREE.ShapeGeometry(shape,2),color);flag.material.side=THREE.DoubleSide;flag.position.set(.16,y,0);flag.rotation.y=-.32;parent.add(flag);
 return flag;
}
function makeTower(i,x,z){
 const y=groundHeight(x,z),g=new THREE.Group();g.position.set(x,y,z);g.scale.setScalar(1.43);terrain.add(g);
 const biome=Math.floor(i/3);
 const metal=towerMaterials.post;
 const pad=box(.47,.12,.42,mat(biome===3?'#a3b4b1':biome===2?'#87543c':'#686155'),0,.06,0,g);pad.castShadow=true;
 for(const off of [-.11,.11]){const post=box(.053,1.55,.06,metal,off,.79,0,g);post.castShadow=true;}
 for(const yy of [.45,.95,1.36]) box(.28,.035,.04,towerMaterials.brace,0,yy,0,g);
 const cap=box(.43,.15,.29,metal,0,1.59,0,g);cap.castShadow=true;
 const beacon=box(.21,.18,.17,towerMaterials.lamp,0,1.76,0,g);beacon.material=new THREE.MeshStandardMaterial({color:'#ffdf91',emissive:'#ff8a28',emissiveIntensity:1.8,roughness:.3});
 const upperFlag=makeFlag(.58,.34,biome===3?towerMaterials.cream:towerMaterials.red,g,1.13);
 const lowerFlag=makeFlag(.50,.28,biome===3?towerMaterials.red:towerMaterials.yellow,g,.73);
 const sign=box(.57,.46,.04,towerMaterials.black,-.45,1.03,.03,g);sign.castShadow=true;
 // Canvas marker stays a textured part of the box and turns with the tower.
 const canvas=document.createElement('canvas');canvas.width=128;canvas.height=96;
 const ctx=canvas.getContext('2d');ctx.fillStyle='#19292c';ctx.fillRect(0,0,128,96);ctx.strokeStyle='#f3c777';ctx.lineWidth=4;ctx.strokeRect(5,5,118,86);
 ctx.font='800 59px Arial';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='#f8eed4';ctx.fillText(String(i+1).padStart(2,'0'),64,49);
 const plane=new THREE.Mesh(new THREE.PlaneGeometry(.55,.42),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(canvas),side:THREE.DoubleSide}));plane.position.set(-.45,1.03,.057);g.add(plane);
 const reverseSign=new THREE.Mesh(plane.geometry,plane.material);
 reverseSign.position.set(-.45,1.03,-.057);reverseSign.rotation.y=Math.PI;g.add(reverseSign);
 const tireMat=mat('#272b2a');
 for(let t=0;t<2;t++){const tire=mesh(new THREE.TorusGeometry(.19,.065,6,10),tireMat,-.38,.08+t*.11,-.27,g);tire.rotation.x=Math.PI/2;}
 const hit=mesh(new THREE.CylinderGeometry(.59,.59,2.3,8),new THREE.MeshBasicMaterial({visible:false}),0,1.1,0,g);hit.userData.stage=i;
 g.userData.index=i;stages.push({g,hit,x,z,y,beacon,upperFlag,lowerFlag});
 return g;
}
for(let i=0;i<12;i++){
 const x=(i===0?-20.1:-21.2+i*3.77),z=routeZ(x)+(i%2===0?-1.05:1.1);
 makeTower(i,x,z);
}

// Hand-authored props are built in small pieces above, then baked into a few
// static material batches. Tower furniture can join the set, while hit meshes,
// number plates, flags and selected beacons keep their own scene nodes.
function mergeStaticSetDressing(){
 terrain.updateMatrixWorld(true);
 const inverseTerrain=terrain.matrixWorld.clone().invert();
 const dynamic=new Set(stages.flatMap(stage=>[stage.hit,stage.beacon,stage.upperFlag,stage.lowerFlag]));
 const batches=new Map();
 terrain.traverse(object=>{
   if(!object.isMesh||object.isInstancedMesh||object===island||dynamic.has(object)||object.material.transparent||!object.visible||object.children.length||Object.keys(object.userData).length)return;
   const attrs=Object.entries(object.geometry.attributes).map(([name,attr])=>`${name}:${attr.itemSize}:${attr.normalized}:${attr.array.constructor.name}`).sort().join('|');
   const key=`${object.material.uuid}/${attrs}/${Boolean(object.geometry.index)}/${object.castShadow}/${object.receiveShadow}`;
   if(!batches.has(key))batches.set(key,[]);
   batches.get(key).push(object);
 });
 let mergedObjects=0,mergedBatches=0;
 for(const objects of batches.values()){
   if(objects.length<2)continue;
   const geometryCopies=objects.map(object=>{
     const relative=inverseTerrain.clone().multiply(object.matrixWorld);
     return object.geometry.clone().applyMatrix4(relative);
   });
   const geometry=mergeGeometries(geometryCopies,false);
   geometryCopies.forEach(copy=>copy.dispose());
   if(!geometry)continue;
   const merged=new THREE.Mesh(geometry,objects[0].material);
   merged.castShadow=objects[0].castShadow;merged.receiveShadow=objects[0].receiveShadow;
   merged.name=`static-${mergedBatches}`;
   for(const object of objects)object.parent.remove(object);
   terrain.add(merged);mergedObjects+=objects.length;mergedBatches++;
 }
 return {mergedObjects,mergedBatches};
}
const meshMerge=mergeStaticSetDressing();

let selected=0,raf=0,lastRender=0,frames=0,fpsAt=performance.now(),fps=0;
const frameInterval=1000/60;
const halo=new THREE.Mesh(new THREE.TorusGeometry(.64,.055,8,48),new THREE.MeshBasicMaterial({color:'#ffd680',transparent:true,opacity:.95}));
halo.rotation.x=Math.PI/2;terrain.add(halo);
const beam=new THREE.Mesh(new THREE.CylinderGeometry(.06,.16,2.25,8),new THREE.MeshBasicMaterial({color:'#ffd079',transparent:true,opacity:.25,depthWrite:false}));terrain.add(beam);
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
let focusTween=null,downX=0,downY=0;
function selectStage(index,focus=false){
 if(index<0||index>=stages.length||disposed)return;
 selected=index;
 const item=stages[index];
 halo.position.set(item.x,item.y+.085,item.z);
 beam.position.set(item.x,item.y+3.40,item.z);
 if(focus){
   const target=new THREE.Vector3(item.x*terrain.scale.x,item.y+1.25,item.z);
   const direction=camera.position.clone().sub(controls.target).normalize();
   focusTween={start:performance.now(),fromPosition:camera.position.clone(),fromTarget:controls.target.clone(),toPosition:target.clone().addScaledVector(direction,17.8),toTarget:target};
   controls.enabled=false;
 }
}
function setLocked(next){
 locked=next;
 applyProgress();
}
function setProgress(nextLocks,nextMedals){
 locked=nextLocks;medals=nextMedals;
 applyProgress();
}
const medalFlags={bronze:mat('#b87342',.38,.55),silver:mat('#e0e8e4',.28,.66),gold:mat('#f4c34c',.32,.55),platinum:mat('#7af0ee',.2,.45)};
function applyProgress(){
 for(let i=0;i<stages.length;i++){
   const stage=stages[i],biome=Math.floor(i/3),isLocked=!!locked[i],earned=medalFlags[medals[i]];
   stage.upperFlag.material=isLocked?mat('#68767a'):earned??(biome===3?towerMaterials.cream:towerMaterials.red);
   stage.lowerFlag.material=isLocked?mat('#657175'):biome===3?towerMaterials.red:towerMaterials.yellow;
 }
}
applyProgress();
selectStage(initialIndex);
function onPointerDown(event){downX=event.clientX;downY=event.clientY;}
function onPointerUp(event){
 if(disposed||Math.hypot(event.clientX-downX,event.clientY-downY)>8)return;
 const rect=renderer.domElement.getBoundingClientRect();
 let nearest=-1,nearestPx=36;
 for(let i=0;i<stages.length;i++){
   const projected=stages[i].hit.getWorldPosition(new THREE.Vector3()).project(camera);
   if(projected.z>=1)continue;
   const x=rect.left+(projected.x+1)*rect.width/2,y=rect.top+(1-projected.y)*rect.height/2;
   const px=Math.hypot(event.clientX-x,event.clientY-y);
   if(px<nearestPx){nearest=i;nearestPx=px;}
 }
 pointer.set(((event.clientX-rect.left)/rect.width)*2-1,-((event.clientY-rect.top)/rect.height)*2+1);
 raycaster.setFromCamera(pointer,camera);
 const hit=raycaster.intersectObjects(stages.map(stage=>stage.hit));
 if(nearest>=0||hit.length){
   const index=nearest>=0?nearest:hit[0].object.userData.stage;
   selectStage(index,true);
   onSelect(index);
 }
}
renderer.domElement.addEventListener('pointerdown',onPointerDown);
renderer.domElement.addEventListener('pointerup',onPointerUp);
function resize(){
 if(disposed)return;
 const width=Math.max(1,root.clientWidth),height=Math.max(1,root.clientHeight);
 camera.aspect=width/height;camera.updateProjectionMatrix();renderer.setSize(width,height);
}
window.addEventListener('resize',resize);
function animate(now){
 if(disposed)return;
 raf=requestAnimationFrame(animate);
 if(focusTween){
   const t=THREE.MathUtils.clamp((now-focusTween.start)/700,0,1),ease=1-(1-t)**3;
   camera.position.copy(focusTween.fromPosition).lerp(focusTween.toPosition,ease);
   controls.target.copy(focusTween.fromTarget).lerp(focusTween.toTarget,ease);
   if(t>=1){focusTween=null;controls.enabled=true;}
 }
 controls.update();
 if(now-lastRender<frameInterval)return;
 // Keep the fractional remainder so a 120 Hz display produces 60 renders,
 // rather than drifting down to every third animation frame.
 lastRender=now-(now-lastRender)%frameInterval;
 waterUniforms.time.value=now*.001;
 halo.rotation.z=now*.00025;
 beam.material.opacity=.16+.07*Math.sin(now*.0035);
 stages.forEach((stage,i)=>{stage.beacon.material.emissiveIntensity=i===selected?2.6+Math.sin(now*.006)*.4:1.1;});
 renderer.render(scene,camera);
 frames++;
 if(now-fpsAt>1000){fps=Math.round(frames*1000/(now-fpsAt));frames=0;fpsAt=now;}
}
raf=requestAnimationFrame(animate);
function dispose(){
 if(disposed)return;
 disposed=true;
 cancelAnimationFrame(raf);
 window.removeEventListener('resize',resize);
 renderer.domElement.removeEventListener('pointerdown',onPointerDown);
 renderer.domElement.removeEventListener('pointerup',onPointerUp);
 controls.dispose();
 const geometries=new Set(),materials=new Set(),textures=new Set();
 scene.traverse(object=>{
   if(!object.isMesh)return;
   geometries.add(object.geometry);
   const list=Array.isArray(object.material)?object.material:[object.material];
   for(const material of list){materials.add(material);if(material.map)textures.add(material.map);}
 });
 for(const geometry of geometries)geometry.dispose();
 for(const texture of textures)texture.dispose();
 for(const material of materials)material.dispose();
 renderer.dispose();renderer.forceContextLoss();renderer.domElement.remove();
}
return {
 selectStage,setLocked,setProgress,resize,dispose,
 stats(){return {fps,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,meshMerge,selected,disposed};},
 towerScreenPoint(index){
   const stage=stages[index];if(!stage)return null;
   const world=stage.hit.getWorldPosition(new THREE.Vector3()).project(camera),rect=renderer.domElement.getBoundingClientRect();
   return {x:rect.left+(world.x+1)*rect.width/2,y:rect.top+(1-world.y)*rect.height/2};
 },
};
}

// The review shell lives in this lazy chunk, keeping its DOM, portrait handling
// and renderer lifecycle out of the player-loaded map screen.
const REVIEW_CSS = `
.worldmap-screen .wm3d-host, .worldmap-screen .wm3d-detail, .worldmap-screen .wm3d-rotate { display: none; }
.worldmap-screen.wm3d-enabled .wm-view { display: none; }
.worldmap-screen.wm3d-enabled .wm3d-host { display: block; position: absolute; inset: 0; z-index: 0; overflow: hidden; background: #1c5265; touch-action: none; }
.worldmap-screen.wm3d-enabled .wm3d-host canvas { display: block; width: 100%; height: 100%; touch-action: none; }
.worldmap-screen.wm3d-enabled .wm3d-detail { display: block; position: absolute; left: 50%; top: calc(14px + var(--sat)); z-index: 5; transform: translateX(-50%); min-width: min(27vw, 210px); max-width: min(35vw, 275px); padding: 8px 12px; border-radius: 10px; background: rgba(15, 31, 35, .92); box-shadow: 0 0 0 1px rgba(239, 227, 200, .25), 0 8px 25px #09181c99; color: var(--cream); text-align: center; pointer-events: none; }
.worldmap-screen.wm3d-enabled .wm3d-detail .head { color: var(--ochre); font: 800 10px/1.2 var(--sans); letter-spacing: .11em; text-transform: uppercase; }
.worldmap-screen.wm3d-enabled .wm3d-detail .name { margin-top: 3px; font: 400 21px/1 var(--display); text-transform: uppercase; }
.worldmap-screen.wm3d-enabled .wm3d-detail .times { margin-top: 4px; color: var(--ink-dim); font: 700 11px/1.2 var(--mono); }
.worldmap-screen.wm3d-enabled .wm3d-detail .times b { color: var(--green); }
.worldmap-screen.wm3d-enabled .wm3d-detail .rule { margin-top: 5px; color: var(--ochre); font: 800 10px/1.2 var(--sans); text-transform: uppercase; }
.worldmap-screen.wm3d-enabled .wm3d-detail .wm3d-medal { margin-top: 5px; color: var(--medal-color); font: 800 10px/1.2 var(--sans); letter-spacing: .08em; text-transform: uppercase; }
.worldmap-screen.wm3d-enabled .wm3d-detail .wm3d-medal.bronze { --medal-color: #dba372; }
.worldmap-screen.wm3d-enabled .wm3d-detail .wm3d-medal.silver { --medal-color: #e0e8e4; }
.worldmap-screen.wm3d-enabled .wm3d-detail .wm3d-medal.gold { --medal-color: #f4c34c; }
.worldmap-screen.wm3d-enabled .wm3d-detail .wm3d-medal.platinum { --medal-color: #7af0ee; }
.worldmap-screen.wm3d-enabled .wm3d-detail .board, .worldmap-screen.wm3d-enabled .wm3d-detail .wm-card-ghost { display: none; }
.worldmap-screen.wm3d-enabled .wm-brand, .worldmap-screen.wm3d-enabled .backbtn, .worldmap-screen.wm3d-enabled .wm-progress, .worldmap-screen.wm3d-enabled .wm-actions { z-index: 6; }
.worldmap-screen.wm3d-enabled .legend { display: none; }
@media (orientation: portrait) {
  .worldmap-screen.wm3d-enabled .wm3d-host, .worldmap-screen.wm3d-enabled .wm3d-detail, .worldmap-screen.wm3d-enabled .wm-brand, .worldmap-screen.wm3d-enabled .backbtn, .worldmap-screen.wm3d-enabled .wm-progress, .worldmap-screen.wm3d-enabled .wm-actions { display: none; }
  .worldmap-screen.wm3d-enabled .wm3d-rotate { display: flex; position: absolute; inset: 0; z-index: 10; align-items: center; justify-content: center; flex-direction: column; gap: 12px; background: radial-gradient(circle at 50% 40%, #247283, #0c454e 72%); color: var(--cream); text-align: center; text-transform: uppercase; }
  .worldmap-screen.wm3d-enabled .wm3d-rotate span { font-size: 72px; line-height: 1; }
  .worldmap-screen.wm3d-enabled .wm3d-rotate strong { font: 400 clamp(28px, 7vw, 48px)/1 var(--display); }
  .worldmap-screen.wm3d-enabled .wm3d-rotate small { font: 700 13px/1.4 var(--sans); letter-spacing: .18em; }
}
`;
export function mountWorldMap3DReview(root,onSelect,initialIndex=0,locked=[],medals=[]){
 if(!document.getElementById("worldmap-3d-review-css")){const style=document.createElement("style");style.id="worldmap-3d-review-css";style.textContent=REVIEW_CSS;document.head.appendChild(style);}
 const host=document.createElement('div'),detail=document.createElement('div'),rotate=document.createElement('div');
 host.className='wm3d-host';detail.className='wm3d-detail';rotate.className='wm3d-rotate';
 rotate.innerHTML='<span>↻</span><strong>Rotate your phone</strong><small>ROCKHOP plays in landscape</small>';
 root.append(host,detail,rotate);
 let scene=null,index=initialIndex,locks=locked,earned=medals,disposed=false;
 function resize(){
   if(disposed)return;
   if(window.innerHeight>window.innerWidth){
     scene?.dispose();scene=null;delete host.dataset.ready;delete window.__rockhopMap3d;
   }else if(!scene){
     scene=mountWorldMap3D(host,onSelect,index,locks,earned);
     host.dataset.ready='1';window.__rockhopMap3d=scene;
   }else scene.resize();
 }
 window.addEventListener('resize',resize);
 resize();
 return {
   selectStage(next,focus){index=next;scene?.selectStage(next,focus);},
   setLocked(next){locks=next;scene?.setLocked(next);},
   setProgress(nextLocks,nextMedals){locks=nextLocks;earned=nextMedals;scene?.setProgress(nextLocks,nextMedals);},
   setDetail(html,id,isLocked,medal){
     const label=medal==='platinum'?'Diamond':medal;
     detail.innerHTML=html+(label&&!isLocked?`<div class="wm3d-medal ${medal}">${label} cleared</div>`:'');
     detail.dataset.track=id;detail.classList.toggle('locked',isLocked);
   },
   resize,
   dispose(){if(disposed)return;disposed=true;window.removeEventListener('resize',resize);scene?.dispose();scene=null;delete window.__rockhopMap3d;host.remove();detail.remove();rotate.remove();},
 };
}
