import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import skyImageUrl from './assets/sky-alpine-a.png?url';

// Standalone visual study. All of the island, route, set dressing and flag towers
// are actual meshes; no camera-facing map plate is used.
const root = document.querySelector('#map');
document.documentElement.classList.toggle('art-mode',new URLSearchParams(location.search).has('art'));
const scene = new THREE.Scene();
scene.background = new THREE.Color('#8db4c2');
scene.fog = new THREE.FogExp2('#9bced0', 0.008);
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(root.clientWidth, root.clientHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
root.appendChild(renderer.domElement);

const camera = new THREE.PerspectiveCamera(31, root.clientWidth / root.clientHeight, 0.1, 250);
camera.position.set(2.5, 20, 32);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0, 0);
controls.enableDamping = true;
controls.dampingFactor = 0.055;
controls.enablePan = false;
controls.minPolarAngle = 0.42;
controls.maxPolarAngle = 1.16;
controls.minDistance = 12;
controls.maxDistance = 105;
controls.maxAzimuthAngle = Infinity;
controls.minAzimuthAngle = -Infinity;
controls.update();

const hemi = new THREE.HemisphereLight('#c9e4e7', '#48534b', 1.15);
scene.add(hemi);
const sun = new THREE.DirectionalLight('#ffddb0', 2.65);
sun.position.set(-22, 45, 33);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -42;
sun.shadow.camera.right = 42;
sun.shadow.camera.top = 35;
sun.shadow.camera.bottom = -35;
sun.shadow.camera.near = 1;
sun.shadow.camera.far = 110;
sun.shadow.bias = -0.0003;
scene.add(sun);
const fill = new THREE.DirectionalLight('#a9dfe9', .72);
fill.position.set(22, 20, -22);
scene.add(fill);

const mat = (color, roughness = 1, metalness = 0) => new THREE.MeshStandardMaterial({ color, roughness, metalness });
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
  return Math.sqrt((x/25.4)**2 + (z/(9.7 + 1.0*Math.sin(x*.23)))**2) + coastJitter + coves - headlands;
};
const routeZ = x => -.40 + 2.55*Math.sin(x*.29+.7) + .8*Math.sin(x*.76-.3)
  + .55*Math.sin(x*.12) + 4.0*(smooth(-13,-10,x)-smooth(-2,1,x))
  + 3.15*(smooth(1,4,x)-smooth(10,14,x));
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

const nx=260, nz=120, dx=52/nx, dz=23/nz;
const verts=[], col=[], texcoord=[], indices=[];
const c = new THREE.Color();
const colorFor = (x,z,y) => {
  if (edgeDistance(x,z)>.96) return c.set('#484b47');
  const borderNoise=noise(x*.47,z*.47)*1.6;
  c.set(y < .42 ? '#766f5b' : '#77795d');
  c.lerp(new THREE.Color(y > 1.25 ? '#75836c' : '#597657'),smooth(-13.8,-8.7,x+borderNoise));
  c.lerp(new THREE.Color(y > 2.1 ? '#b07145' : '#a66b46'),smooth(.2,4.1,x+borderNoise));
  c.lerp(new THREE.Color(y > 1.2 ? '#dce7e7' : '#a5b5ad'),smooth(11.8,15.5,x+borderNoise));
  const sx=(groundHeight(x+.16,z)-groundHeight(x-.16,z))/.32;
  const sz=(groundHeight(x,z+.16)-groundHeight(x,z-.16))/.32;
  const exposed=smooth(.65,2.9,Math.hypot(sx,sz))*.68;
  const stone=new THREE.Color(x>13?'#5d7681':x>2?'#784b35':'#56605c');
  c.lerp(stone,exposed);
  const rim=smooth(.71,.99,edgeDistance(x,z));
  const strata=.5+.5*Math.sin(y*5.8+x*.69+noise(x*.8,z*.8)*2.1);
  const mineral=new THREE.Color(x>13?'#85999c':x>2?'#a5714e':'#72786c');
  c.lerp(mineral,rim*exposed*(.10+.34*strata));
  const variation = noise(x*2.3,z*2.3)*.065 + noise(x*.75,z*.75)*.035;
  c.offsetHSL(0,0,variation);
  if (x > 11 && y > 2.2) c.lerp(new THREE.Color('#f5f5ed'), smooth(2.2,4.1,y)*.6);
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
const island = new THREE.Mesh(geo,new THREE.MeshStandardMaterial({vertexColors:true,map:groundTexture,roughness:1,flatShading:false,side:THREE.DoubleSide}));
island.castShadow=true;island.receiveShadow=true;terrain.add(island);

// Layered seawater gives specular movement around a true island silhouette.
const waterGeo = new THREE.PlaneGeometry(500,500,160,160); waterGeo.rotateX(-Math.PI/2);
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
   r+=front*(coveA+coveB+coveC-headA-headB);
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
const foamMat=new THREE.MeshBasicMaterial({color:'#d9eeea',transparent:true,opacity:.65});
for(let i=0;i<185;i++){
 const a=rr(0,Math.PI*2),r=rr(1.01,1.19),x=25.3*Math.cos(a)*r,z=9.7*Math.sin(a)*r;
 const len=rr(.12,.49),pts=[new THREE.Vector3(x-len*.5,-1.00,z),new THREE.Vector3(x,-.99,z+.03),new THREE.Vector3(x+len*.5,-1.00,z)];
 line(pts,foamMat,rr(.009,.023),terrain);
}

// Detached sea stacks and broken promontories give the shoreline a jagged silhouette.
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
 const o=mesh(g,new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,flatShading:true,side:THREE.DoubleSide}),x,0,z);
 o.castShadow=true;o.receiveShadow=true;
}
for(let i=0;i<39;i++){
 const x=-23.6+i*1.25+rr(-.35,.35),edgeZ=9.5*Math.sqrt(Math.max(.03,1-(x/25.4)**2));
 const z=edgeZ*rr(.96,1.27)+rr(-.2,.3),scale=i%7===0?rr(1.35,2.0):rr(.44,1.05);
 seaStack(x,z,scale*.43,scale*1.35,x>14);
 if(i%5===0)seaStack(x+rr(-.4,.4),z+rr(.7,1.6),scale*.31,scale*.98,x>14);
}

// Broken outcrops interrupt the long front cliff and carry its silhouette
// down into the surf. They are instanced to keep the extra draw cost bounded.
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
const buttressMaterials=['#535c57','#687269','#8a6751','#8f9da1'].map(hex=>mat(hex));
const buttresses=buttressMaterials.map(material=>new THREE.InstancedMesh(buttressGeo,material,48));
const buttressCounts=[0,0,0,0],buttressDummy=new THREE.Object3D();
for(let i=0;i<124;i++){
 const x=rr(-23.0,23.0),side=rand()<.76?1:-1;
 const edgeZ=(9.7+Math.sin(x*.23))*Math.sqrt(Math.max(.08,1-(x/25.4)**2));
 const z=side*edgeZ*rr(.92,1.045);
 const band=x>13?3:x>2?2:x<-11?0:1;
 if(buttressCounts[band]>=48)continue;
 const top=groundHeight(x,z),height=rr(.55,1.50)*(x>13?1.15:1);
 buttressDummy.position.set(x,top-.68*height,z);
 buttressDummy.rotation.set(rr(-.14,.14),rr(0,6.28),rr(-.20,.20));
 buttressDummy.scale.set(rr(.24,.54),height,rr(.27,.58));buttressDummy.updateMatrix();
 buttresses[band].setMatrixAt(buttressCounts[band]++,buttressDummy.matrix);
}
buttresses.forEach((o,i)=>{o.count=buttressCounts[i];o.castShadow=true;o.receiveShadow=true;terrain.add(o);});

// Coast-to-summit ribbon, made from sampled vertices that lie on the relief.
function routeMesh(width, color, lift){
 const positions=[],normals=[],uv=[],ind=[];const count=450;
 for(let i=0;i<=count;i++){
   const x=-22.15 + i/count*44.2,z=routeZ(x);
   const z1=routeZ(x+.04),z0=routeZ(x-.04);
   const tx=.08,tz=z1-z0,l=Math.hypot(tx,tz),px=-tz/l,pz=tx/l;
   for(const sign of [-1,1]){
     const xx=x+px*width*sign,zz=z+pz*width*sign;
     positions.push(xx,groundHeight(xx,zz)+lift,zz);normals.push(0,1,0);uv.push(i/13,sign);
   }
   if(i<count){const j=i*2;ind.push(j,j+1,j+2,j+1,j+3,j+2);}
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('normal',new THREE.Float32BufferAttribute(normals,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(ind);g.computeVertexNormals();
 const m=new THREE.Mesh(g,mat(color));m.receiveShadow=true;terrain.add(m);return m;
}
routeMesh(1.28,'#504033',.23);routeMesh(.89,'#e2bb7a',.27);
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
 const pts=[];for(let i=0;i<310;i++){const x=-22+i/309*44,z=routeZ(x)+offset;pts.push(new THREE.Vector3(x,groundHeight(x,z)+.30,z));}
 line(pts,tire,.018);
}

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
 {snowy:false,species:0,capacity:130,core:'#28553e'},
 {snowy:false,species:1,capacity:110,core:'#1a493a'},
 {snowy:false,species:2,capacity:85,core:'#526b40'},
 {snowy:true,species:0,capacity:48,core:'#315c50'},
 {snowy:true,species:1,capacity:48,core:'#254b43'},
 {snowy:true,species:2,capacity:35,core:'#566c55'},
].map(kind=>({
 ...kind,count:0,
 trunk:new THREE.InstancedMesh(trunkGeo,trunkMat,kind.capacity),
 canopy:new THREE.InstancedMesh(firGeometry(kind.snowy,kind.species),foliageMat,kind.capacity),
 core:new THREE.InstancedMesh(new THREE.ConeGeometry(.25,kind.species===2?1.46:1.20,7),mat(kind.core),kind.capacity),
}));
const dum=new THREE.Object3D();
let nForest=0,nSnow=0;
for(let tries=0;tries<12000&&(nForest<325||nSnow<131);tries++){
 const x=rr(-23.6,24.1),z=rr(-8.7,8.7); if(edgeDistance(x,z)>.87 || Math.abs(routeZ(x)-z)<3.05)continue;
 const snowy=x>12.5; if(snowy ? nSnow>=131 : nForest>=325)continue;
 if(!snowy&&(x>1.8&&x<13.0 || x<-11.2&&rand()<.71))continue;
 if(x>-8.0&&x<-2.9&&z>3.5&&z<8.0)continue;
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
for(const kind of treeKinds)for(const obj of [kind.trunk,kind.canopy,kind.core]){obj.count=kind.count;obj.castShadow=true;obj.receiveShadow=true;terrain.add(obj);}

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

// Faceted glacial massifs protrude above the pine line on the snow end.
function mountain(x,z,radius,height){
 const ringCount=9,levels=[0,.20,.48,.74,1],sizes=[1,.83,.58,.34,0],v=[],cl=[],ids=[];
 for(let l=0;l<levels.length;l++)for(let k=0;k<ringCount;k++){
   const a=k/ringCount*Math.PI*2,jag=.84+.18*Math.sin(k*2.23+x*1.7)+.12*Math.sin(k*4.7+z);
   const r=radius*sizes[l]*jag,px=Math.cos(a)*r,pz=Math.sin(a)*r,py=levels[l]*height+.08*noise(px+x,pz+z);
   v.push(px,py,pz);
   const base=new THREE.Color(l>=3?'#eef1eb':l===2?'#c6d1ce':'#798c91');
   base.offsetHSL(0,0,noise(k*2,l*4)*.09);cl.push(base.r,base.g,base.b);
   if(l<levels.length-1){const i=l*ringCount+k,n=l*ringCount+(k+1)%ringCount;ids.push(i,n,i+ringCount,n,n+ringCount,i+ringCount);}
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(v,3));g.setAttribute('color',new THREE.Float32BufferAttribute(cl,3));g.setIndex(ids);g.computeVertexNormals();
 const o=mesh(g,new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,flatShading:true,side:THREE.DoubleSide}),x,groundHeight(x,z)-.2,z);
 o.castShadow=true;o.receiveShadow=true;
}
mountain(15.4,4.7,2.6,2.65);
mountain(18.4,-4.5,2.45,3.15);
mountain(14.1,-5.2,2.1,2.45);

// Open-cut quarry benches follow an irregular horseshoe; each wall and shelf has volume.
const sandstone=mat('#a6633b'),ore=mat('#755849');
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
   const o=new THREE.Mesh(g,new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,side:THREE.DoubleSide,flatShading:true}));
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
  shard.scale.set(rr(.6,1.3),rr(.45,1.8),rr(.6,1.4));shard.rotation.set(rr(0,3),rr(0,6),rr(0,3));shard.castShadow=true;
}
for(let i=0;i<8;i++){
 const x=rr(3,12),z=rr(-5,-2),h=groundHeight(x,z);
 const b=box(rr(.3,.9),rr(.2,.5),rr(.22,.7),ore,x,h+.15,z);b.rotation.y=rr(0,6.28);b.castShadow=true;
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
for(let i=0;i<13;i++){
 const x=-2.45+i*.105+rr(-.025,.025),thickness=rr(.055,.105);
 const p=[x,waterfallTop,9.0,x+rr(-.08,.08),-1.11,10.0,x+thickness,waterfallTop,9.0,x+thickness+rr(-.08,.08),-1.11,10.0];
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));g.setIndex([0,1,2,2,1,3]);g.computeVertexNormals();
 const stream=new THREE.Mesh(g,new THREE.MeshBasicMaterial({color:i%3===0?'#f3ffff':'#a1dce1',transparent:true,opacity:rr(.63,.88),side:THREE.DoubleSide,depthWrite:false}));terrain.add(stream);
}
for(let i=0;i<13;i++){
 const puff=mesh(new THREE.IcosahedronGeometry(rr(.09,.22),1),new THREE.MeshBasicMaterial({color:'#eaf5ec',transparent:true,opacity:rr(.35,.65)}),rr(-2.55,-1.1),-1.0+rr(-.14,.2),rr(9.8,10.4));
 puff.scale.y=.3;
}

// Harbor: a tapered steel trawler, timber pier, cargo and a visible lattice crane.
const dock=mat('#574536'),woodTop=mat('#9b7652'),rust=mat('#8e4a37'),roofMat=mat('#45443c');
for(let i=0;i<18;i++){
 const z=6.1+i*.22,deck=box(1.5,.12,.19,i%4===0?dock:woodTop,-17.0,-.38,z);deck.castShadow=true;
 if(i%5===0)for(const off of [-.63,.63])box(.14,1.75,.14,dock,-17.0+off,-1.18,z).castShadow=true;
}
for(let i=0;i<12;i++){
 const x=-18.0+(i%3)*.47,z=4.4+Math.floor(i/3)*.46,y=groundHeight(x,z);
 box(.39,.35,.33,mat(['#94563c','#5b6a64','#a48153'][i%3]),x,y+.18,z).castShadow=true;
}
const ship=new THREE.Group();ship.position.set(-17.5,-.73,9.45);ship.rotation.y=-.14;terrain.add(ship);
const hullFrames=[[-2.8,.12],[-2.2,.55],[-1.0,.77],[.9,.79],[2.1,.58],[2.7,.12]],hullP=[],hullC=[],hullI=[];
for(let i=0;i<hullFrames.length;i++){
 const [x,w]=hullFrames[i];
 const ring=[[x,.31,-w],[x,-.28,-w*.75],[x,-.68,0],[x,-.28,w*.75],[x,.31,w]];
 for(const [px,py,pz] of ring){hullP.push(px,py,pz);const cc=new THREE.Color(py<-.3?'#394d56':i%2?'#805447':'#53616a');hullC.push(cc.r,cc.g,cc.b);}
 if(i<hullFrames.length-1)for(let j=0;j<4;j++){const a=i*5+j,b=a+5;hullI.push(a,b,a+1,a+1,b,b+1);}
}
const hullGeo=new THREE.BufferGeometry();hullGeo.setAttribute('position',new THREE.Float32BufferAttribute(hullP,3));
hullGeo.setAttribute('color',new THREE.Float32BufferAttribute(hullC,3));hullGeo.setIndex(hullI);hullGeo.computeVertexNormals();
const hull=mesh(hullGeo,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.85,metalness:.18,side:THREE.DoubleSide}),0,0,0,ship);hull.castShadow=true;
box(4.3,.13,1.17,mat('#665748'),-.08,.29,0,ship).castShadow=true;
box(1.12,.88,.91,mat('#a98d69'),-1.15,.79,0,ship).castShadow=true;
box(1.32,.15,1.05,rust,-1.15,1.29,0,ship).castShadow=true;
const glass=mat('#315d6b',.18);
for(const side of [-1,1])for(let i=0;i<3;i++)box(.25,.26,.035,glass,-1.47+i*.32,.85,side*.47,ship);
for(const side of [-1,1]){
 const rail=[];for(const [x,w] of hullFrames)rail.push(new THREE.Vector3(x,.7,side*w));line(rail,mat('#3c4546',.5,.35),.025,ship);
 for(let i=1;i<hullFrames.length-1;i++)box(.025,.42,.025,mat('#3c4546'),hullFrames[i][0],.5,side*hullFrames[i][1],ship);
}
for(let i=0;i<4;i++)box(.65,.38,.46,mat(i%2?'#6b5e4e':'#865c44'),.2+i*.62,.55,0,ship).castShadow=true;
cylinder(.035,.05,2.3,mat('#4c4540'),-1.02,2.36,0,ship).castShadow=true;
line([new THREE.Vector3(-1.02,3.5,0),new THREE.Vector3(-2.4,.55,-.34)],mat('#4c4540'),.018,ship);
line([new THREE.Vector3(-1.02,3.5,0),new THREE.Vector3(1.9,.55,.38)],mat('#4c4540'),.018,ship);
const craneX=-17.4,craneZ=6.1,craneY=groundHeight(craneX,craneZ);
box(.85,.35,.8,mat('#715942'),craneX,craneY+.18,craneZ).castShadow=true;
for(const side of [-1,1]){
 const leg=box(.11,3.95,.11,rust,craneX+side*.27,craneY+2.25,craneZ);leg.rotation.z=side*.09;leg.castShadow=true;
}
for(let i=0;i<5;i++){
 const y=craneY+.75+i*.73;
 box(.62,.08,.1,rust,craneX,y,craneZ).castShadow=true;
 line([new THREE.Vector3(craneX-.27,y,craneZ),new THREE.Vector3(craneX+.27,y+.73,craneZ)],rust,.027);
}
const jibStart=new THREE.Vector3(craneX,craneY+4.32,craneZ),jibEnd=new THREE.Vector3(craneX-3.65,craneY+4.72,craneZ+.4);
line([jibStart,jibEnd],rust,.083);line([new THREE.Vector3(craneX,craneY+4.04,craneZ),new THREE.Vector3(jibEnd.x,jibEnd.y-.25,jibEnd.z)],rust,.055);
for(let i=1;i<8;i++){
 const t=i/8,x=THREE.MathUtils.lerp(jibStart.x,jibEnd.x,t),z=THREE.MathUtils.lerp(jibStart.z,jibEnd.z,t),y=THREE.MathUtils.lerp(jibStart.y,jibEnd.y,t);
 line([new THREE.Vector3(x,y,z),new THREE.Vector3(x+.42,y-.25,z)],rust,.025);
}
line([jibEnd,new THREE.Vector3(jibEnd.x,craneY+1.8,jibEnd.z)],mat('#383b39'),.016);
mesh(new THREE.TorusGeometry(.18,.042,8,12,Math.PI*1.7),mat('#4c5050',.55,.4),jibEnd.x,craneY+1.67,jibEnd.z).rotation.z=Math.PI/2;
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
// Quarry machinery, snow chalet and cable pylons are recognizable from wide view.
building(10.6,-5.8,1.8,1.25,mat('#705a48'),mat('#494843'));
building(18.5,-2.6,1.7,1.2,mat('#c6c9c2'),mat('#515f62'));
for(let i=0;i<3;i++){
 const x=14.1+i*3.2,z=-5.4+Math.sin(i)*.8,y=groundHeight(x,z);
 box(.15,2.0,.15,mat('#5c686a'),x,y+1,z).castShadow=true;
 box(1.2,.13,.13,mat('#5c686a'),x,y+2,z).castShadow=true;
 if(i<2){const nx=x+3.2,nz=-5.4+Math.sin(i+1)*.8,ny=groundHeight(nx,nz);line([new THREE.Vector3(x,y+1.98,z),new THREE.Vector3(nx,ny+1.98,nz)],mat('#5c686a'),.024);}
}

const levelNames=['Breakwater Run','Dockside Dash','Tide Cliffs','Pine Bend','Timberline','Sawmill Switch','Cutbank','Red Quarry','Ore Drop','Frostline','Glacier Bridge','Summit Signal'];
const biomeNames=['THE BREAKWATER','DEEPWOOD','RED QUARRY','SNOWLINE'];
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
 makeFlag(.58,.34,biome===3?towerMaterials.cream:towerMaterials.red,g,1.13);
 makeFlag(.50,.28,biome===3?towerMaterials.red:towerMaterials.yellow,g,.73);
 const sign=box(.57,.46,.04,towerMaterials.black,-.45,1.03,.03,g);sign.castShadow=true;
 // Canvas marker stays a textured part of the box and turns with the tower.
 const canvas=document.createElement('canvas');canvas.width=128;canvas.height=96;
 const ctx=canvas.getContext('2d');ctx.fillStyle='#19292c';ctx.fillRect(0,0,128,96);ctx.strokeStyle='#f3c777';ctx.lineWidth=4;ctx.strokeRect(5,5,118,86);
 ctx.font='800 59px Arial';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='#f8eed4';ctx.fillText(String(i+1).padStart(2,'0'),64,49);
 const plane=new THREE.Mesh(new THREE.PlaneGeometry(.55,.42),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(canvas),side:THREE.DoubleSide}));plane.position.set(-.45,1.03,.057);g.add(plane);
 const tireMat=mat('#272b2a');
 for(let t=0;t<2;t++){const tire=mesh(new THREE.TorusGeometry(.19,.065,6,10),tireMat,-.38,.08+t*.11,-.27,g);tire.rotation.x=Math.PI/2;}
 const hit=mesh(new THREE.CylinderGeometry(.59,.59,2.3,8),new THREE.MeshBasicMaterial({visible:false}),0,1.1,0,g);hit.userData.stage=i;
 g.userData.index=i;stages.push({g,hit,x,z,y,beacon});
 return g;
}
for(let i=0;i<12;i++){
 const x=(i===0?-20.1:-21.2+i*3.77),z=routeZ(x)+(i%2===0?-1.05:1.1);
 makeTower(i,x,z);
}

let selected=0;
const selectionTitle=document.querySelector('#selection-title');
const selectionDetail=document.querySelector('#selection-detail');
const biomeTitle=document.querySelector('#biome');
const halo=new THREE.Mesh(new THREE.TorusGeometry(.64,.055,8,48),new THREE.MeshBasicMaterial({color:'#ffd680',transparent:true,opacity:.95}));
halo.rotation.x=Math.PI/2;terrain.add(halo);
const beam=new THREE.Mesh(new THREE.CylinderGeometry(.06,.16,2.25,8),new THREE.MeshBasicMaterial({color:'#ffd079',transparent:true,opacity:.25,depthWrite:false}));terrain.add(beam);
function selectStage(i){
 selected=i;const item=stages[i];halo.position.set(item.x,item.y+.085,item.z);beam.position.set(item.x,item.y+3.40,item.z);
 selectionTitle.textContent=`${String(i+1).padStart(2,'0')} · ${levelNames[i]}`;
 selectionDetail.textContent=`${['COAST','FOREST','QUARRY','SNOW'][Math.floor(i/3)]} / READY TO RIDE`;
 biomeTitle.textContent=`${String(Math.floor(i/3)+1).padStart(2,'0')} / ${biomeNames[Math.floor(i/3)]}`;
}
selectStage(0);
const overviewCamera=new THREE.Vector3(2.5,20,32);
let focusTween=null;
function moveView(position,target){
 focusTween={start:performance.now(),fromPosition:camera.position.clone(),fromTarget:controls.target.clone(),toPosition:position,toTarget:target};
 controls.enabled=false;
}
function focusStage(i){
 selectStage(i);
 const stage=stages[i],target=new THREE.Vector3(stage.x*terrain.scale.x,stage.y+1.25,stage.z);
 const direction=camera.position.clone().sub(controls.target).normalize();
 moveView(target.clone().addScaledVector(direction,17.8),target);
 document.documentElement.classList.add('focused');
}
document.querySelector('#overview').addEventListener('click',()=>{
 document.documentElement.classList.remove('focused');
 moveView(overviewCamera.clone(),new THREE.Vector3());
});
document.querySelector('#ride').addEventListener('click',()=>{
 const toast=document.querySelector('#toast');toast.textContent=`STAGE ${String(selected+1).padStart(2,'0')} · ${levelNames[selected].toUpperCase()}`;
 toast.classList.add('show');setTimeout(()=>toast.classList.remove('show'),1700);
});
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
let downX=0,downY=0;
renderer.domElement.addEventListener('pointerdown',e=>{downX=e.clientX;downY=e.clientY;});
renderer.domElement.addEventListener('pointerup',e=>{
 if(Math.hypot(e.clientX-downX,e.clientY-downY)>8)return;
 const rect=renderer.domElement.getBoundingClientRect();pointer.set(((e.clientX-rect.left)/rect.width)*2-1,-((e.clientY-rect.top)/rect.height)*2+1);
 raycaster.setFromCamera(pointer,camera);
 const hit=raycaster.intersectObjects(stages.map(s=>s.hit));
 if(hit.length) focusStage(hit[0].object.userData.stage);
});
window.addEventListener('resize',()=>{
 camera.aspect=root.clientWidth/root.clientHeight;camera.updateProjectionMatrix();renderer.setSize(root.clientWidth,root.clientHeight);
});
let last=performance.now(),frames=0;
function animate(now){
 requestAnimationFrame(animate);
 if(focusTween){
   const t=THREE.MathUtils.clamp((now-focusTween.start)/700,0,1),ease=1-(1-t)**3;
   camera.position.copy(focusTween.fromPosition).lerp(focusTween.toPosition,ease);
   controls.target.copy(focusTween.fromTarget).lerp(focusTween.toTarget,ease);
   if(t===1){focusTween=null;controls.enabled=true;}
 }
 controls.update();
 waterUniforms.time.value=now*.001;
 halo.rotation.z=now*.00025;
 beam.material.opacity=.16+.07*Math.sin(now*.0035);
 stages.forEach((stage,i)=>{stage.beacon.material.emissiveIntensity=i===selected?2.6+Math.sin(now*.006)*.4:1.1;});
 renderer.render(scene,camera);
 frames++;
 if(now-last>1000){window.__atlasFPS=Math.round(frames*1000/(now-last));frames=0;last=now;}
}
requestAnimationFrame(animate);
window.__atlas={scene,camera,controls,renderer,stages,selectStage,focusStage,get selected(){return selected;},get fps(){return window.__atlasFPS}};
