import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// An independent, wholly geometric design study. No production map code or backdrop art is used.
const root = document.querySelector('#app');
const artMode = new URLSearchParams(location.search).has('art');
const useBlenderTerrain=!new URLSearchParams(location.search).has('proceduralTerrain');
let terrainReady=!useBlenderTerrain;
if(artMode)document.body.classList.add('art-mode');
const scene = new THREE.Scene();
scene.background = new THREE.Color('#211c18');
scene.fog = new THREE.Fog('#211c18', 29, 49);
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.13;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
root.append(renderer.domElement);

const camera = new THREE.PerspectiveCamera(35, innerWidth / innerHeight, 0.1, 100);
let azimuth = artMode?-.13:.01, polar = artMode?1.0:.82, radius = artMode?20.0:18.5, goalAzimuth = azimuth, goalPolar = polar, goalRadius = radius;
const target = new THREE.Vector3(0, artMode?.68:.9, 0);
const goalTarget=target.clone();
const map = new THREE.Group();
scene.add(map);
map.scale.z=1.24;
if(useBlenderTerrain)new GLTFLoader().load('./assets/sculpted-terrain.glb',gltf=>{
 gltf.scene.traverse(o=>{if(o.isMesh){
  o.castShadow=false;o.receiveShadow=true;
  if(o.material.name==='Warm fractured cliff')o.material.color.set('#94755a');
  if(o.material.name==='Cold fractured cliff')o.material.color.set('#aab9bd');
  if(o.material.name==='Quarry bench strata')o.material.color.set('#c8a77f');
 }});
 map.add(gltf.scene);terrainReady=true;
},undefined,error=>{console.error('Terrain GLB failed',error);});

scene.add(new THREE.HemisphereLight('#dce8ec', '#483226', 1.12));
const sun = new THREE.DirectionalLight('#ffe1ad', 3.65);
sun.position.set(-7, 16, 11); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -15; sun.shadow.camera.right = 15;
sun.shadow.camera.top = 11; sun.shadow.camera.bottom = -11;
sun.shadow.normalBias = 0.025;
scene.add(sun);
const fill = new THREE.DirectionalLight('#9ac8d9', .72); fill.position.set(5, 8, -10); scene.add(fill);

const mat = (color, roughness=1, metalness=0) => new THREE.MeshStandardMaterial({color, roughness, metalness});
const wood = mat('#4f2c19', .86), darkWood = mat('#291c13', .92), plank = mat('#795037', .88);
const steel = mat('#534e47', .63, .35), rust = mat('#9a4f2c', .8, .15), linen = new THREE.MeshStandardMaterial({color:'#e2b95f',side:THREE.DoubleSide,roughness:.88});
const paleStone = mat('#c1b89b'), darkStone=mat('#645e4d'), snowShadow=mat('#bccdd0');

let seed=32817; function random(){seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;}
const gauss=(x,z,cx,cz,sx,sz)=>Math.exp(-(((x-cx)/sx)**2+((z-cz)/sz)**2));
function terrain(x,z){
  const fine=.07*Math.sin(x*5.2-z*3.6)+.035*Math.cos(z*8.2+x*3.8);
  const waves=.11*Math.sin(x*2.4+z*1.6)+fine;
  const coast=.48+Math.max(0,x+6.9)*.04+ .87*gauss(x,z,-5.4,-2.2,2,2.4);
  const forest=1.44*gauss(x,z,-2.8,-2.5,2.1,1.25)+1.25*gauss(x,z,-1.7,2.65,1.25,1.1)+1.0*gauss(x,z,-4.15,2.4,1.2,1.3);
  const qr=Math.hypot((x-2.05)/2.35,(z+2.1)/1.9);
  const quarry=(x>-.2&&x<4.7)?2.28*gauss(x,z,2.05,-2.1,3.35,2.65)-(qr<1.08?.37*Math.floor((1.08-qr)*5):0):0;
  const mountain=2.55*gauss(x,z,6.65,-2.55,1.4,1.2)+1.65*gauss(x,z,5.5,2.9,1.25,1.1)+1.5*gauss(x,z,8.0,1.5,1.0,1.25);
  const frontEscarpment=x>-.3&&x<5.2?1.02*gauss(x,z,2.4,3.7,3.5,1.15):x>=5.2?.8*gauss(x,z,7,3.7,2.4,1.2):x>-4.7?.48*gauss(x,z,-2.6,3.8,2.5,1.1):0;
  const ravine=-1.17*gauss(x,z,4.35,1.8,.57,2.5);
  const shelf= x < -6.5 ? Math.max(-.45,(x+6.5)*.25) : 0;
  return Math.max(.16,coast+forest+quarry+mountain+frontEscarpment+ravine+waves+shelf);
}
function groundColor(x,z,y){
  const noise=Math.sin(x*14+z*23)*.04+Math.sin(x*37-z*19)*.03;
  let c;
  if(x< -5.4)c=new THREE.Color(y<.67?'#80775c':'#766d55');
  else if(x< -.4)c=new THREE.Color(y>1.7?'#727864':'#506247');
  else if(x<4.85)c=new THREE.Color(y<.8?'#806147':'#be8b5a');
  else c=new THREE.Color(y>1.2?'#e0e7e6':'#8e9da1');
  c.offsetHSL(0,0,noise);
  return c;
}

function addMesh(geometry, material, pos, parent=map){
  const mesh=new THREE.Mesh(geometry,material); mesh.position.set(...pos); mesh.castShadow=true; mesh.receiveShadow=true; parent.add(mesh); return mesh;
}
function box(w,h,d,material,x,y,z,parent=map){return addMesh(new THREE.BoxGeometry(w,h,d),material,[x,y,z],parent);}
function cylinder(r1,r2,h,material,x,y,z,parent=map,sides=8){return addMesh(new THREE.CylinderGeometry(r1,r2,h,sides),material,[x,y,z],parent);}
function beamBetween(a,b,thickness,material,parent=map){
  const start=new THREE.Vector3(...a),end=new THREE.Vector3(...b);
  const mid=start.clone().add(end).multiplyScalar(.5),len=start.distanceTo(end);
  const bar=addMesh(new THREE.BoxGeometry(thickness,len,thickness),material,mid.toArray(),parent);
  bar.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),end.sub(start).normalize()); return bar;
}

// A stepped wooden object makes the geography read as a miniature, not a flat image.
box(19.2,.16,10.05,darkWood,0,-.65,0);
box(19.0,.58,9.85,wood,0,-.29,0);
box(18.65,.1,9.52,plank,0,.04,0);
for(const edge of [-1,1]){
  box(19.0,.08,.1,darkWood,0,-.26,edge*4.87);
  box(.1,.08,9.75,darkWood,edge*9.43,-.26,0);
}
for(let i=0;i<8;i++){
  const y=-.53+i*.067;
  box(19.02,.012,9.86,i%2?mat('#805337'):mat('#3f2517'),0,y,0);
}
// Four engraved biome plates, deliberately outside the road and without arena markers.
function textTexture(text,bg='#33291e',fg='#e8cb9c',width=512,height=160){
 const c=document.createElement('canvas');c.width=width;c.height=height;const g=c.getContext('2d');
 g.fillStyle=bg;g.fillRect(0,0,width,height);g.strokeStyle='#a78555';g.lineWidth=11;g.strokeRect(9,9,width-18,height-18);
 g.fillStyle=fg;g.font=`bold ${Math.floor(height*.43)}px Georgia`;g.textAlign='center';g.textBaseline='middle';g.fillText(text,width/2,height/2+2);
 const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;return tex;
}
const textureLoader=new THREE.TextureLoader();
function texture(name,rx=1,ry=1){
 const t=textureLoader.load(`./textures/${name}_diff_1k.jpg`);t.colorSpace=THREE.SRGBColorSpace;
 t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(rx,ry);t.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());return t;
}
const terrainZones=[
 [-9.175,-5.25,'coast_sand_rocks_02'],[-5.25,-.2,'forest_ground_04'],[-.2,4.8,'sandstone_cracks'],[4.8,9.175,'snow_02']
];
if(!useBlenderTerrain)for(const [left,right,name] of terrainZones){
 const geo=new THREE.PlaneGeometry(right-left,9.25,Math.ceil((right-left)*18),120);geo.rotateX(-Math.PI/2);geo.translate((left+right)/2,0,0);
 const vert=geo.attributes.position,cols=[];
 for(let i=0;i<vert.count;i++){
  const x=vert.getX(i),z=vert.getZ(i),y=terrain(x,z);vert.setY(i,y);
  const c=groundColor(x,z,y).lerp(new THREE.Color('#ffffff'),name==='snow_02'?.52:.58);cols.push(c.r,c.g,c.b);
 }
 geo.setAttribute('color',new THREE.Float32BufferAttribute(cols,3));geo.computeVertexNormals();
 const mesh=addMesh(geo,new THREE.MeshStandardMaterial({map:texture(name,(right-left)*1.2,9.25*1.2),vertexColors:true,roughness:.97,side:THREE.DoubleSide}),[0,0,0]);mesh.castShadow=false;
}
wood.map=texture('dark_wood',2,1);wood.needsUpdate=true;
plank.map=texture('dark_wood',3,1);plank.needsUpdate=true;
wood.color.set('#a88268');plank.color.set('#c4a389');
const rockWarmTex=texture('marble_cliff_03');
const rockColdTex=texture('marble_cliff_05');

// Continuous fractured rock strata turn the rectangular height field into a sculpted tray insert.
function cliffFace(start,end,frontZ=4.59,rockTex=rockWarmTex){
 const nx=Math.ceil((end-start)/.115),ny=7,positions=[],cols=[],uvs=[],indices=[];
 for(let ix=0;ix<=nx;ix++){
  const x=start+(end-start)*ix/nx,top=terrain(x,3.84);
  for(let iy=0;iy<=ny;iy++){
   const v=iy/ny,n=Math.sin(ix*8.71+iy*6.83)*.07+Math.sin(ix*3.12-iy*7.3)*.045;
   const y=.09+(top-.09)*(1-v)+(iy&&iy<ny?n:0);
   const z=3.82+v*(frontZ-3.82)+n*.57;
   positions.push(x+(iy&&iy<ny?n*.4:0),y,z);
   const base=new THREE.Color(x<-.35?'#bcc6b6':x<4.7?'#f0c095':'#edf1f1');
   if(x>4.7&&y>top*.75)base.lerp(new THREE.Color('#ffffff'),.45);
   base.multiplyScalar(.91+.17*(.5+.5*Math.sin(ix*2.52+iy*7.3)));
   cols.push(base.r,base.g,base.b);
   uvs.push((x-start)*1.05,iy/ny*1.7);
  }
 }
 for(let ix=0;ix<nx;ix++)for(let iy=0;iy<ny;iy++){
  const a=ix*(ny+1)+iy,b=(ix+1)*(ny+1)+iy;
  if((ix+iy)%2)indices.push(a,b,a+1,b,b+1,a+1);else indices.push(a,b,b+1,a,b+1,a+1);
 }
 const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geo.setAttribute('color',new THREE.Float32BufferAttribute(cols,3));geo.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));geo.setIndex(indices);geo.computeVertexNormals();
 return addMesh(geo,new THREE.MeshStandardMaterial({map:rockTex,vertexColors:true,roughness:1,flatShading:true,side:THREE.DoubleSide}),[0,0,0]);
}
if(!useBlenderTerrain){
 cliffFace(-4.7,-.35,4.59,rockWarmTex);
 cliffFace(-.35,4.7,4.59,rockWarmTex);
 cliffFace(4.7,9.05,4.59,rockColdTex);
}
// Deep fissures and drainage seams are physical strips on the rock face.
for(const x of [-3.35,-2.96,4.85,6.6]){
 const top=terrain(x,3.85),points=[];
 for(let i=0;i<=8;i++){
  const t=i/8;points.push(new THREE.Vector3(x+.06*Math.sin(i*1.8),.1+(top-.1)*(1-t),3.87+t*.73+.025*Math.sin(i*2.4)));
 }
 const stream=addMesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points),35,x>4?.055:.034,5,false),new THREE.MeshPhysicalMaterial({color:x>4?'#c6e8f3':'#9dd7de',transparent:true,opacity:.85,roughness:.22}),[0,0,0]);stream.castShadow=false;
}

// Irregular coast: the dark sea is a polygonal 3D sheet with physical highlights and shore foam.
const coastLine=z=>-5.9+.28*Math.sin(z*1.45)+.23*Math.sin(z*3.1)+Math.max(0,z-1.5)*.37;
const waterPos=[],waterColors=[],waterIdx=[],wnx=35,wnz=94;
for(let iz=0;iz<=wnz;iz++){
 const z=-4.55+iz/wnz*9.1,edge=coastLine(z);
 for(let ix=0;ix<=wnx;ix++){
  const u=ix/wnx,x=-9.16+(edge+9.16)*u,wave=.013*Math.sin(x*9+z*5)+.008*Math.sin(x*19-z*12);
  waterPos.push(x,.424+wave,z);
  const c=new THREE.Color('#0c4650').lerp(new THREE.Color('#3b8793'),.13+.22*(.5+.5*Math.sin(x*4+z*6)));
  waterColors.push(c.r,c.g,c.b);
  if(ix<wnx&&iz<wnz){const a=iz*(wnx+1)+ix,b=a+wnx+1;waterIdx.push(a,b,a+1,b,b+1,a+1);}
 }
}
const waterGeo=new THREE.BufferGeometry();waterGeo.setAttribute('position',new THREE.Float32BufferAttribute(waterPos,3));waterGeo.setAttribute('color',new THREE.Float32BufferAttribute(waterColors,3));waterGeo.setIndex(waterIdx);waterGeo.computeVertexNormals();
const sea=addMesh(waterGeo,new THREE.MeshPhysicalMaterial({vertexColors:true,roughness:.2,metalness:.27,clearcoat:1,clearcoatRoughness:.14,side:THREE.DoubleSide}),[0,0,0]);sea.castShadow=false;
const foamPoints=[];for(let i=0;i<=70;i++){const z=-4.45+i/70*8.9;foamPoints.push(new THREE.Vector3(coastLine(z)-.04,.447,z));}
const shoreFoam=addMesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(foamPoints),140,.028,4,false),new THREE.MeshBasicMaterial({color:'#b5d4d0',transparent:true,opacity:.68}),[0,0,0]);shoreFoam.castShadow=false;
const rippleMaterial=new THREE.MeshBasicMaterial({color:'#bbdeda',transparent:true,opacity:.61,side:THREE.DoubleSide});
const ripples=[];
for(let i=0;i<240;i++){
  const z=-4.4+random()*8.8,x=-9.1+random()*(coastLine(z)+9.05);
  const ring=addMesh(new THREE.RingGeometry(.035+random()*.035,.055+random()*.04,10,1,Math.PI*.15,Math.PI*.8),rippleMaterial,[x,.404,z]);
  ring.position.y=.455;ring.rotation.x=-Math.PI/2;ring.rotation.z=random()*6;ring.castShadow=false;ripples.push(ring);
}
for(let i=0;i<47;i++){
 const z=-4.25+random()*8.5,x=-9+random()*(coastLine(z)+8.9);
 const r=.07+random()*.22;const rock=addMesh(new THREE.IcosahedronGeometry(r,1),darkStone,[x,.43,z]);rock.scale.set(1,.6+random()*1.4,1);
 const edge=addMesh(new THREE.RingGeometry(r*.85,r*1.45,13),new THREE.MeshBasicMaterial({color:'#c7dfd7',transparent:true,opacity:.48,side:THREE.DoubleSide}),[x,.451,z]);edge.rotation.x=-Math.PI/2;edge.castShadow=false;
}

// Snow peaks and quarry strata are separate real geometry layered over the height field.
function makeMountain(x,z,w,h,color){
 const base=terrain(x,z)-.12,sides=9,rings=6,positions=[],colors=[],uvs=[],indices=[];
 const baseColor=color.color.clone().lerp(new THREE.Color('#ffffff'),x>4.5?.76:.62),topColor=x>4.5?new THREE.Color('#ffffff'):baseColor.clone().lerp(new THREE.Color('#dfd5c1'),.4);
 const leanX=(random()-.5)*w*.44,leanZ=(random()-.5)*w*.4,angles=[];
 for(let k=0;k<sides;k++)angles.push(k/sides*Math.PI*2+(random()-.5)*.18);
 for(let j=0;j<rings;j++){
  const t=j/(rings-1),r=[1.2,1.06,.88,.63,.35,.035][j];
  for(let k=0;k<sides;k++){
   const a=angles[k],jag=.77+random()*.47;
   positions.push(x+Math.cos(a)*w*r*jag+leanX*t,base+h*t+(j&&j<rings-1?(random()-.5)*h*.09:0),z+Math.sin(a)*w*r*jag+leanZ*t);
   const c=baseColor.clone().lerp(topColor,x>4.5?THREE.MathUtils.smoothstep(t,.49,.84):t*.42);
   c.multiplyScalar(.85+random()*.3);colors.push(c.r,c.g,c.b);
   uvs.push(k/sides*2,t*1.5);
  }
 }
 for(let j=0;j<rings-1;j++)for(let k=0;k<sides;k++){
  const a=j*sides+k,b=j*sides+(k+1)%sides,c=(j+1)*sides+k,d=(j+1)*sides+(k+1)%sides;
  indices.push(a,b,c,b,d,c);
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));g.setIndex(indices);g.computeVertexNormals();
 return addMesh(g,new THREE.MeshStandardMaterial({map:x>4.5?rockColdTex:rockWarmTex,vertexColors:true,flatShading:true,roughness:1,side:THREE.DoubleSide}),[0,0,0]);
}
for(let i=0;i<48;i++){
 const x=4.7+random()*4.2,z=-4.1+random()*8.2;
 const h=.25+random()*1.17,w=.19+random()*.35;
 makeMountain(x,z,w,h,i%4? snowShadow:darkStone);
}
for(let i=0;i<33;i++){
 const x=-4.3+random()*3,z=-3.7+random()*1.4;
 makeMountain(x,z,.22+random()*.37,.4+random()*1.1,i%2?darkStone:paleStone);
}
// A broken, scalloped escarpment creates a visible carved-stone edge above the wood.
for(let i=0;i<(useBlenderTerrain?0:22);i++){
 const x=-4.45+random()*9.15,z=3.54+random()*.53;
 makeMountain(x,z,.12+random()*.18,.16+random()*.37,i%3?darkStone:paleStone);
}
// Open quarry benches are geology, not circular stage pads.
for(let k=0;k<(useBlenderTerrain?0:6);k++){
 const rr=.34+k*.16,positions=[],colors=[],indices=[];
 for(let j=0;j<=32;j++){
  const a=j/32*Math.PI,x=2.05+2.35*rr*Math.cos(a),z=-1.92+1.9*rr*Math.sin(a),top=terrain(x,z)+.23;
  positions.push(x,top,z,x,top-.61,z);
  const c=new THREE.Color(k%2?'#d2a174':'#99603e').multiplyScalar(.76+.25*Math.sin(j*1.71));
  for(let h=0;h<2;h++)colors.push(c.r,c.g,c.b);
  if(j<32){const n=j*2;indices.push(n,n+1,n+2,n+1,n+3,n+2);}
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.setIndex(indices);g.computeVertexNormals();
 const wall=addMesh(g,new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,flatShading:true,side:THREE.DoubleSide}),[0,0,0]);wall.castShadow=false;
}
const quarryRubble=new THREE.InstancedMesh(new THREE.DodecahedronGeometry(1,0),new THREE.MeshStandardMaterial({color:'#ffffff',roughness:1,flatShading:true}),470);
const rubbleObject=new THREE.Object3D();
for(let i=0;i<470;i++){
 const x=.15+random()*4.5,z=-3.95+random()*7.9,y=terrain(x,z),large=i<45;
 const s=large?.11+random()*.24:.025+random()*.08;
 rubbleObject.position.set(x,y+s*.32,z);rubbleObject.rotation.set(random()*.6,random()*Math.PI*2,random()*.6);
 rubbleObject.scale.set(s*(.7+random()*.8),s*(.38+random()*.58),s*(.7+random()*.8));rubbleObject.updateMatrix();quarryRubble.setMatrixAt(i,rubbleObject.matrix);
 const c=new THREE.Color(i%6===0?'#6f5744':i%3===0?'#b88963':'#d3af83');quarryRubble.setColorAt(i,c);
}
quarryRubble.castShadow=true;quarryRubble.receiveShadow=true;quarryRubble.computeBoundingSphere();map.add(quarryRubble);

// Winding single road, draped on terrain. Each biome gets three actual 3D selectable rally towers.
const knots=[[-7.95,2.0],[-7.15,1.1],[-6.5,-.15],[-5.65,-1.05],[-4.7,.45],[-3.85,1.38],[-2.8,2.22],[-1.65,1.78],[-.5,1.05],[.65,1.28],[1.75,2.03],[2.7,2.37],[3.75,2.06],[4.5,1.28],[5.25,.55],[6.1,-.4],[7.2,-.05],[7.8,1.0],[8.05,2.1]];
const route=new THREE.CatmullRomCurve3(knots.map(([x,z])=>new THREE.Vector3(x,0,z)),false,'catmullrom',.22);
const samples=[];for(let i=0;i<=300;i++){
 const t=i/300,p=route.getPoint(t);
 const viaductRise=2.02*THREE.MathUtils.smoothstep(p.x,3.45,3.95)*(1-THREE.MathUtils.smoothstep(p.x,4.65,5.14));
 const y=Math.max(terrain(p.x,p.z)+.18,viaductRise);
 samples.push(new THREE.Vector3(p.x,y,p.z));
}
function ribbon(width,yOffset,material,uvScale){
 const positions=[],uvs=[],indices=[];let distance=0;
 for(let i=0;i<samples.length;i++){
   const p=samples[i],before=samples[Math.max(0,i-1)],after=samples[Math.min(samples.length-1,i+1)];
   if(i)distance+=samples[i-1].distanceTo(p);
   const tx=after.x-before.x,tz=after.z-before.z,len=Math.hypot(tx,tz)||1,nx=-tz/len,nz=tx/len;
   for(const side of [-1,1]){
     const x=p.x+nx*width*.5*side,z=p.z+nz*width*.5*side;
     positions.push(x,Math.max(p.y,terrain(x,z)+.045)+yOffset,z);uvs.push(side<0?0:1,distance/uvScale);
   }
   if(i<samples.length-1){const a=i*2;indices.push(a,a+1,a+2,a+1,a+3,a+2);}
 }
 const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geo.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));geo.setIndex(indices);geo.computeVertexNormals();
 const m=addMesh(geo,material,[0,0,0]);m.castShadow=false;return m;
}
ribbon(1.16,-.005,mat('#514b41'),2);
const roadCanvas=document.createElement('canvas');roadCanvas.width=128;roadCanvas.height=512;
const rg=roadCanvas.getContext('2d');rg.fillStyle='#d0c3ac';rg.fillRect(0,0,128,512);
for(let i=0;i<6500;i++){rg.fillStyle=i%4?'#6c6258':'#f1e6d3';rg.globalAlpha=.06+random()*.16;rg.fillRect(random()*128,random()*512,1+random()*5,1+random()*8);}rg.globalAlpha=1;
for(const x of [28,100]){rg.fillStyle='#594f42';rg.globalAlpha=.16;rg.fillRect(x,0,5,512);}rg.globalAlpha=1;
const roadTex=new THREE.CanvasTexture(roadCanvas);roadTex.wrapS=roadTex.wrapT=THREE.RepeatWrapping;roadTex.colorSpace=THREE.SRGBColorSpace;
ribbon(.99,.018,new THREE.MeshStandardMaterial({map:roadTex,roughness:1,side:THREE.DoubleSide}),1.55);

// Wooden suspension bridges over difficult terrain visibly support the route.
function bridge(t0,t1){
 const n=16,pts=[];for(let i=0;i<=n;i++)pts.push(samples[Math.round((t0+(t1-t0)*i/n)*300)]);
 for(let i=0;i<n;i++){
   const p=pts[i],q=pts[i+1],mid=p.clone().add(q).multiplyScalar(.5),length=p.distanceTo(q);
   const b=box(.7,.08,length,plank,mid.x,mid.y-.045,mid.z);b.lookAt(q.x,mid.y,q.z);
   if(i%2===0){
    const earth=terrain(mid.x,mid.z);cylinder(.045,.07,Math.max(.05,mid.y-earth),darkWood,mid.x,(mid.y+earth)*.5,mid.z);
   }
 }
}
bridge(.22,.285);bridge(.53,.595);
bridge(.65,.735);
for(const t of [.665,.69,.715]){
 const p=samples[Math.round(t*300)],ground=terrain(p.x,p.z),height=Math.max(.1,p.y-ground);
 box(.16,height,.25,paleStone,p.x,ground+height*.5,p.z);
 box(.23,.07,.32,darkStone,p.x,p.y-.08,p.z);
}

// Dense miniature trees use instancing: true 3D with silhouettes and correct rotation parallax.
seed=48602;
const treeData=[];
function closeToRoad(x,z,canopy=0){let nearest=99;for(let i=0;i<samples.length;i+=3){nearest=Math.min(nearest,Math.hypot(samples[i].x-x,samples[i].z-z));}return nearest<1.06+canopy*.42;}
for(let i=0;i<430;i++){
 const x=-5.0+random()*5.3,z=-4.25+random()*8.5;
 const s=.42+random()*.8;
 if(closeToRoad(x,z,s)||terrain(x,z)<.45)continue;
 treeData.push({x,z,s,kind:random()*5|0,snow:false});
}
for(let i=0;i<155;i++){
 const x=4.72+random()*4.1,z=-4.2+random()*8.4;
 const s=.34+random()*.72;
 if(closeToRoad(x,z,s)||terrain(x,z)<.45)continue;
 treeData.push({x,z,s,kind:random()*3|0,snow:true});
}
function coniferGeometry(snowy,variant){
 const pos=[],col=[];
 function tri(a,b,c,color){for(const v of [a,b,c]){pos.push(...v);col.push(color.r,color.g,color.b);}}
 const trunkColor=new THREE.Color('#594335');
 for(let k=0;k<9;k++){
  const a=k/9*Math.PI*2,b=(k+1)/9*Math.PI*2,r0=.042,r1=.018;
  const p=[Math.cos(a)*r0,0,Math.sin(a)*r0],q=[Math.cos(b)*r0,0,Math.sin(b)*r0];
  const u=[Math.cos(a)*r1,1.03,Math.sin(a)*r1],v=[Math.cos(b)*r1,1.03,Math.sin(b)*r1];
  tri(p,q,u,trunkColor);tri(q,v,u,trunkColor);
 }
 const greens=snowy?['#334f49','#4b6255','#607568','#75877b']:['#193d32','#28513b','#476b45','#547349'];
 const tiers=variant===1?10:9;
 for(let tier=0;tier<tiers;tier++){
  const h=.22+tier*.089,extent=(.345*(1-tier/(tiers+.9)))*(variant===2?.86:1.0);
  const branches=variant===1?9:8;
  for(let branch=0;branch<branches;branch++){
   const angle=branch/branches*Math.PI*2+tier*.43+variant*.29;
   const ca=Math.cos(angle),sa=Math.sin(angle),width=.14*(1-tier/(tiers+2));
   const len=extent*(.76+random()*.45);
   const inner=[ca*.035,h+.015,sa*.035],outer=[ca*len,h-.07-random()*.035,sa*len];
   const wingA=[ca*len*.61-Math.sin(angle)*width,h+.005,sa*len*.61+Math.cos(angle)*width];
   const wingB=[ca*len*.61+Math.sin(angle)*width,h+.005,sa*len*.61-Math.cos(angle)*width];
   const ridge=[ca*len*.55,h+.09,sa*len*.55];
   const branchColor=new THREE.Color(greens[(tier+branch+variant)%greens.length]);
   branchColor.multiplyScalar(.85+random()*.3);
   tri(inner,wingA,ridge,branchColor);tri(inner,ridge,wingB,branchColor);
   tri(wingA,outer,ridge,branchColor);tri(ridge,outer,wingB,branchColor);
   tri(wingB,outer,wingA,branchColor.clone().multiplyScalar(.77));
   if(snowy&&tier%2===0){
    const snowColor=new THREE.Color('#d4dcdb').multiplyScalar(.83+random()*.23);
    tri(ridge,wingA,outer,snowColor);
   }
  }
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));g.computeVertexNormals();return g;
}
for(const snowy of [false,true])for(let j=0;j<3;j++){
 const subset=treeData.filter(t=>t.snow===snowy && t.kind%3===j),n=subset.length;
 const trees=new THREE.InstancedMesh(coniferGeometry(snowy,j),new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,side:THREE.DoubleSide,flatShading:true}),n);
 const obj=new THREE.Object3D();
 for(let i=0;i<n;i++){
  const t=subset[i],y=terrain(t.x,t.z);obj.position.set(t.x,y-.025,t.z);
  obj.scale.set(t.s*(.9+random()*.2),t.s*(.76+random()*.48),t.s*(.9+random()*.2));obj.rotation.y=random()*Math.PI*2;obj.updateMatrix();trees.setMatrixAt(i,obj.matrix);
 }
 trees.castShadow=true;trees.receiveShadow=true;trees.computeBoundingSphere();map.add(trees);
}
// Real needle silhouettes on radial branch cards for selected hero trees. The cards
// are fixed in the 3D tree geometry and never face the camera.
function twigCanopyGeometry(){
 const positions=[],uvs=[],indices=[];
 const crops=[[.64,.98,.67,.98],[.13,.46,.64,.98],[.29,.62,.21,.57],[.64,.96,.17,.56]];
 for(let tier=0;tier<8;tier++)for(let branch=0;branch<7;branch++){
  const a=branch/7*Math.PI*2+tier*.4,tangent=[-Math.sin(a),0,Math.cos(a)],radial=[Math.cos(a),0,Math.sin(a)];
  const h=.23+tier*.1,r=.17*(1-tier/10),w=.19*(1-tier/10),height=.24*(1-tier/11),id=positions.length/3;
  const crop=crops[(tier+branch)%crops.length];
  for(const [sx,sy,u,v] of [[-1,-1,crop[0],crop[2]],[1,-1,crop[1],crop[2]],[-1,1,crop[0],crop[3]],[1,1,crop[1],crop[3]]]){
   positions.push(radial[0]*r+tangent[0]*w*sx/2,h+sy*height/2,radial[2]*r+tangent[2]*w*sx/2);uvs.push(u,v);
  }
  indices.push(id,id+1,id+2,id+1,id+3,id+2);
 }
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));g.setIndex(indices);g.computeVertexNormals();return g;
}
const twigDiffuse=textureLoader.load('./textures/fir_tree_01_twig_diff_1k.jpg');twigDiffuse.colorSpace=THREE.SRGBColorSpace;
const twigAlpha=textureLoader.load('./textures/fir_tree_01_twig_alpha_1k.png');
const heroTreeData=treeData.filter(t=>!t.snow&&t.s>.72).slice(0,92);
const needles=new THREE.InstancedMesh(twigCanopyGeometry(),new THREE.MeshStandardMaterial({map:twigDiffuse,alphaMap:twigAlpha,alphaTest:.44,side:THREE.DoubleSide,roughness:.96,depthWrite:true}),heroTreeData.length);
for(let i=0;i<heroTreeData.length;i++){
 const t=heroTreeData[i],obj=new THREE.Object3D();obj.position.set(t.x,terrain(t.x,t.z),t.z);obj.scale.setScalar(t.s);obj.rotation.y=(i*2.39996)%(Math.PI*2);obj.updateMatrix();needles.setMatrixAt(i,obj.matrix);
}
needles.castShadow=true;needles.computeBoundingSphere();map.add(needles);
// Rounded oak and golden birch crowns break up the repeated pine silhouette.
const broadleaf=[];
for(let i=0;i<115;i++){
 const x=-4.9+random()*4.8,z=-3.95+random()*7.9,s=.45+random()*.48;
 if(closeToRoad(x,z,s+.2)||terrain(x,z)<.5)continue;
 broadleaf.push({x,z,s,y:terrain(x,z),kind:i%7});
}
const trunkInst=new THREE.InstancedMesh(new THREE.CylinderGeometry(.045,.065,.72,7),new THREE.MeshStandardMaterial({color:'#4c3528',roughness:1}),broadleaf.length);
const crownInst=new THREE.InstancedMesh(new THREE.IcosahedronGeometry(.31,2),new THREE.MeshStandardMaterial({color:'#ffffff',roughness:1,flatShading:true}),broadleaf.length*4);
const broadObj=new THREE.Object3D();
for(let i=0;i<broadleaf.length;i++){
 const t=broadleaf[i];broadObj.position.set(t.x,t.y+.34*t.s,t.z);broadObj.scale.setScalar(t.s);broadObj.rotation.y=i*2.399; broadObj.updateMatrix();trunkInst.setMatrixAt(i,broadObj.matrix);
 for(let j=0;j<4;j++){
  const a=j*2.4+i*.35,index=i*4+j;
  broadObj.position.set(t.x+Math.cos(a)*.16*t.s,t.y+(.65+(j%2)*.19)*t.s,t.z+Math.sin(a)*.15*t.s);
  broadObj.scale.set(t.s*(j===0?1.26:.9),t.s*(j===0?1.04:.7),t.s*(j===0?1.04:.88)); broadObj.rotation.y=a; broadObj.updateMatrix(); crownInst.setMatrixAt(index,broadObj.matrix);
  const c=new THREE.Color(t.kind===0?'#a58b39':t.kind===1?'#6b793e':j%2?'#4c6840':'#617843');c.multiplyScalar(.88+random()*.24);crownInst.setColorAt(index,c);
 }
}
trunkInst.castShadow=true;crownInst.castShadow=true;trunkInst.computeBoundingSphere();crownInst.computeBoundingSphere();map.add(trunkInst,crownInst);
seed=73191;

// Small scene anchors: fishing pier and grounded boat, sawmill, quarry crane, snow lift.
const pierCurve=new THREE.CatmullRomCurve3([new THREE.Vector3(-8.65,0,2.85),new THREE.Vector3(-7.9,0,2.7),new THREE.Vector3(-7.13,0,2.18),new THREE.Vector3(-6.15,0,1.65)]);
for(let i=0;i<27;i++){
 const t=i/26,p=pierCurve.getPoint(t),d=pierCurve.getTangent(t),yaw=Math.atan2(d.x,d.z);
 const plankPiece=box(.43,.06,.16,plank,p.x,.59,p.z);plankPiece.rotation.y=yaw;
 if(i%3===0){for(const side of [-1,1]){
  const px=p.x+Math.cos(yaw)*side*.26,pz=p.z-Math.sin(yaw)*side*.26;
  cylinder(.038,.048,.75,darkWood,px,.22,pz);
  cylinder(.025,.025,.32,rust,px,.76,pz);
 }}
}
const ship=new THREE.Group();map.add(ship);ship.position.set(-8.02,.39,-2.37);ship.rotation.y=-.38;
const hullStations=[[-1.5,.32],[-1.15,.53],[-.55,.61],[.3,.59],[.95,.42],[1.45,.05]];
const hullPos=[],hullCol=[],hullIdx=[];
for(let s=0;s<hullStations.length;s++){
 const [z,w]=hullStations[s];
 for(const [x,y] of [[-w,.53],[w,.53],[-w*.91,.12],[w*.91,.12],[-w*.42,-.08],[w*.42,-.08]]){
  hullPos.push(x,y,z);const c=new THREE.Color('#873e28').multiplyScalar(.66+random()*.45);hullCol.push(c.r,c.g,c.b);
 }
 if(s<hullStations.length-1){const a=s*6,b=a+6;for(const [u,v] of [[0,2],[2,4],[5,3],[3,1]])hullIdx.push(a+u,a+v,b+u,a+v,b+v,b+u);}
}
const hullGeo=new THREE.BufferGeometry();hullGeo.setAttribute('position',new THREE.Float32BufferAttribute(hullPos,3));hullGeo.setAttribute('color',new THREE.Float32BufferAttribute(hullCol,3));hullGeo.setIndex(hullIdx);hullGeo.computeVertexNormals();
addMesh(hullGeo,new THREE.MeshStandardMaterial({vertexColors:true,side:THREE.DoubleSide,flatShading:true,metalness:.42,roughness:.78}),[0,0,0],ship);
box(.85,.055,2.32,plank,0,.55,-.04,ship);
box(.56,.48,.53,paleStone,0,.8,-.83,ship);
box(.65,.09,.61,darkWood,0,1.07,-.83,ship);
for(const side of [-1,1]){
 for(let z=-1.25;z<1.2;z+=.3)cylinder(.014,.014,.34,steel,side*.51,.72,z,ship,5);
 beamBetween([side*.51,.86,-1.3],[side*.36,.86,1.25],.018,steel,ship);
}
for(let i=0;i<6;i++){
 const z=-.5+i*.22;box(.3,.18,.18,i%2?rust:darkWood,-.06,.65,z,ship);
}
beamBetween([0,.55,-.25],[0,1.54,-.25],.038,steel,ship);
beamBetween([0,1.53,-.25],[.47,1.2,.58],.026,rust,ship);
beamBetween([.47,1.2,.58],[.47,.37,.58],.01,steel,ship);
const shipHook=cylinder(.045,.05,.1,steel,.47,.42,.58,ship);shipHook.castShadow=false;
for(let i=0;i<5;i++){const x=-4.8+i*.12;box(.12,.18,.7,wood,x,terrain(x,2.45)+.1,2.45);}
const millY=terrain(-2.75,2.65);box(1.05,.42,.78,wood,-2.75,millY+.25,2.65);
const roof=box(1.25,.13,.95,darkWood,-2.75,millY+.54,2.65);roof.rotation.z=.13;
for(let i=0;i<11;i++){const x=-3.5+i*.15;const log=cylinder(.075,.075,.65,plank,x,terrain(x,3.42)+.08,3.42);log.rotation.z=Math.PI/2;}
function crane(x,z,h){
 const y=terrain(x,z);cylinder(.23,.31,.14,rust,x,y+.08,z);
 for(let i=0;i<4;i++)beamBetween([x+Math.sin(i*Math.PI/2)*.15,y+.1,z+Math.cos(i*Math.PI/2)*.15],[x+Math.sin(i*Math.PI/2)*.08,y+h,z+Math.cos(i*Math.PI/2)*.08],.045,steel);
 for(let yy=.35;yy<h;yy+=.26){box(.35,.025,.35,steel,x,y+yy,z);}
 beamBetween([x-.1,y+h,z],[x+1.7,y+h+.22,z],.075,rust);
 beamBetween([x,y+h,z],[x+1.65,y+h+.18,z],.025,darkWood);
 beamBetween([x+1.3,y+h+.18,z],[x+1.3,y+.23,z],.014,steel);
 cylinder(.065,.04,.17,steel,x+1.3,y+.25,z);
}
crane(2.4,-.8,1.35);
crane(-7.13,-3.3,2.0);
// Layered harbor sheds and freight stacks add the industrial silhouette in B's left quarter.
for(const [x,z,w,d,h] of [[-6.83,-3.88,.7,.65,.62],[-6.21,-3.55,.54,.44,.43],[-7.7,-3.72,.54,.42,.36]]){
 const y=terrain(x,z);box(w,h,d,wood,x,y+h/2,z);
 const roof=box(w*1.17,.08,d*1.22,darkWood,x,y+h+.035,z);roof.rotation.z=.11;
 for(const dx of [-w*.28,w*.28])box(.055,h*.33,.015,rust,x+dx,y+h*.4,z+d*.51);
}
for(let i=0;i<14;i++){
 const x=-7.45+(i%5)*.32,z=-4.2+Math.floor(i/5)*.33,y=terrain(x,z);
 const crate=box(.23,.18+random()*.1,.24,i%3?rust:plank,x,y+.11,z);crate.rotation.y=random()*.25;
}
// Quarry conveyor: timber/steel trestles bridge the carved pit rather than floating across it.
const conveyorStart=new THREE.Vector3(.55,terrain(.55,-2.0)+.65,-2.0);
const conveyorEnd=new THREE.Vector3(3.75,terrain(3.75,-2.8)+.62,-2.8);
const conveyorDir=conveyorEnd.clone().sub(conveyorStart).normalize();
const conveyorSide=new THREE.Vector3(-conveyorDir.z,0,conveyorDir.x);
for(const side of [-1,1]){
 const a=conveyorStart.clone().addScaledVector(conveyorSide,side*.15),b=conveyorEnd.clone().addScaledVector(conveyorSide,side*.15);
 beamBetween(a.toArray(),b.toArray(),.045,rust);
}
for(let i=0;i<=20;i++){
 const t=i/20,p=conveyorStart.clone().lerp(conveyorEnd,t),left=p.clone().addScaledVector(conveyorSide,-.17),right=p.clone().addScaledVector(conveyorSide,.17);
 beamBetween(left.toArray(),right.toArray(),.027,plank);
 if(i%4===0){
  const below=terrain(p.x,p.z),baseL=left.clone();baseL.y=below;const baseR=right.clone();baseR.y=below;
  beamBetween(left.toArray(),baseL.toArray(),.035,steel);beamBetween(right.toArray(),baseR.toArray(),.035,steel);
  beamBetween(left.toArray(),baseR.toArray(),.018,steel);
 }
}
for(const p of [conveyorStart,conveyorEnd]){
 const y=terrain(p.x,p.z);box(.44,.49,.46,wood,p.x,y+.28,p.z);const roof=box(.53,.07,.54,rust,p.x,y+.56,p.z);roof.rotation.z=.13;
}
const liftA=[5.0,terrain(5,3.0),3.0],liftB=[7.65,terrain(7.65,2.4),2.4];
for(const [x,y,z] of [liftA,liftB]){
 beamBetween([x,y,z],[x,y+.92,z],.075,steel);cylinder(.19,.19,.05,steel,x,y+.93,z);
}
beamBetween([liftA[0],liftA[1]+.94,liftA[2]],[liftB[0],liftB[1]+.94,liftB[2]],.022,darkWood);
for(let i=1;i<5;i++){
 const t=i/5,x=THREE.MathUtils.lerp(liftA[0],liftB[0],t),z=THREE.MathUtils.lerp(liftA[2],liftB[2],t),y=THREE.MathUtils.lerp(liftA[1],liftB[1],t)+.94;
 beamBetween([x,y,z],[x,y-.18,z],.012,steel);box(.23,.045,.13,rust,x,y-.2,z);
}

const stageNames=['The Dock Run','Salt Spray','Harbor Leap','Pine Trail','Ravine Pass','Timber Bridge','Dust Bowl','Quarry Climb','Iron Crossing','Frostline','Lift Ridge','The Summit'];
const biomes=['Coast','Forest','Quarry','Snowline'];
const towerTargets=[],towerGroups=[];
function flagShape(){const shape=new THREE.Shape();shape.moveTo(0,0);shape.lineTo(.37,.08);shape.lineTo(.33,.32);shape.lineTo(0,.3);shape.closePath();return new THREE.ShapeGeometry(shape);}
for(let i=0;i<12;i++){
 const t=.035+i*.079;const p=route.getPoint(t),ahead=route.getPoint(Math.min(1,t+.006));
 const dir=new THREE.Vector2(ahead.x-p.x,ahead.z-p.z).normalize(),normal=new THREE.Vector2(-dir.y,dir.x);
 const x=p.x+normal.x*.52,z=p.z+normal.y*.52,y=terrain(x,z);
 const tower=new THREE.Group();map.add(tower);tower.position.set(x,y,z);tower.rotation.y=-Math.atan2(dir.y,dir.x);tower.scale.setScalar(.88);
 box(.24,.09,.24,steel,0,.035,0,tower);
 for(const dx of [-.075,.075]){beamBetween([dx,.07,-.07],[dx*.55,.82,-.07],.033,rust,tower);beamBetween([dx,.07,.07],[dx*.55,.82,.07],.033,rust,tower);}
 for(const yy of [.24,.42,.61,.79]){box(.18,.025,.16,steel,0,yy,0,tower);}
 box(.27,.09,.27,darkWood,0,.83,0,tower);
 cylinder(.018,.018,.47,darkWood,0,1.1,0,tower);
 const flag=addMesh(flagShape(),linen,[0,1.01,0],tower);
 flag.material=mat(i<3?'#e46535':i<6?'#e99e37':i<9?'#dc693e':'#e7533f');flag.material.side=THREE.DoubleSide;
 flag.rotation.y=Math.PI/2;
 const number=addMesh(new THREE.PlaneGeometry(.29,.22),new THREE.MeshBasicMaterial({map:textTexture(String(i+1).padStart(2,'0'),'#d7ba80','#30302a',256,192),side:THREE.DoubleSide}),[0,.55,.092],tower);number.castShadow=false;
 const beacon=cylinder(.06,.06,.08,new THREE.MeshStandardMaterial({color:'#fcae4f',emissive:'#c05c1e',emissiveIntensity:1.5,roughness:.3}),0,.9,0,tower);beacon.castShadow=false;
 const hit=box(1.28,1.85,1.28,new THREE.MeshBasicMaterial({transparent:true,opacity:0,depthWrite:false}),0,.74,0,tower);hit.userData.stage=i;towerTargets.push(hit);towerGroups.push(tower);
}

// Brass ticks and bolts around the base sell tabletop scale at any viewing angle.
const brass=mat('#ad8c54',.35,.55);
for(let i=0;i<20;i++){
 const x=-8.8+i*.93;const b=box(.018,.012,.11,brass,x,.09,-4.76);b.castShadow=false;
}
for(const x of [-9.3,9.3])for(const z of [-4.78,4.78]){const nail=cylinder(.06,.06,.014,brass,x,.07,z);nail.castShadow=false;}
// Table and distant studio darkness.
const tabletop=addMesh(new THREE.PlaneGeometry(200,200),new THREE.MeshStandardMaterial({color:'#6b4931',map:texture('dark_wood',45,45),roughness:.9}),[0,-.75,0],scene);tabletop.rotation.x=-Math.PI/2;tabletop.castShadow=false;

let pointerDown=false,lastX=0,lastY=0,dragDistance=0;
renderer.domElement.addEventListener('pointerdown',e=>{pointerDown=true;lastX=e.clientX;lastY=e.clientY;dragDistance=0;renderer.domElement.setPointerCapture(e.pointerId);});
renderer.domElement.addEventListener('pointermove',e=>{if(!pointerDown)return;const dx=e.clientX-lastX,dy=e.clientY-lastY;dragDistance+=Math.abs(dx)+Math.abs(dy);goalAzimuth-=dx*.006;goalPolar=THREE.MathUtils.clamp(goalPolar+dy*.003,.62,1.28);lastX=e.clientX;lastY=e.clientY;});
renderer.domElement.addEventListener('pointerup',e=>{pointerDown=false;if(dragDistance<7)selectAt(e.clientX,e.clientY);});
renderer.domElement.addEventListener('wheel',e=>{e.preventDefault();goalRadius=THREE.MathUtils.clamp(goalRadius+e.deltaY*.018,7.8,37);},{passive:false});
document.querySelector('#left').onclick=()=>goalAzimuth-=Math.PI/5;
document.querySelector('#right').onclick=()=>goalAzimuth+=Math.PI/5;
function resetView(){goalAzimuth=.01;goalPolar=.82;goalRadius=18.5;goalTarget.set(0,.9,0);towerGroups.forEach(t=>t.scale.setScalar(.88));}
document.querySelector('#reset').onclick=resetView;
document.querySelector('#card-close').onclick=()=>{document.querySelector('#card').hidden=true;document.querySelector('.hud').classList.remove('has-selection');resetView();};
const raycaster=new THREE.Raycaster();
function selectAt(x,y){
 let nearest=-1,nearestPixels=Infinity;
 for(let i=0;i<towerGroups.length;i++){
  const p=towerGroups[i].localToWorld(new THREE.Vector3(0,.66,0)).project(camera);
  if(p.z>1)continue;
  const px=(p.x+1)*innerWidth/2,py=(1-p.y)*innerHeight/2,d=Math.hypot(px-x,py-y);
  if(d<nearestPixels){nearest=i;nearestPixels=d;}
 }
 if(nearest>=0&&nearestPixels<28){selectStage(nearest);return;}
 const ndc=new THREE.Vector2(x/innerWidth*2-1,-y/innerHeight*2+1);
 raycaster.setFromCamera(ndc,camera);const hits=raycaster.intersectObjects(towerTargets,false);
 if(hits.length)selectStage(hits[0].object.userData.stage);
}
function selectStage(i){
 document.querySelector('#card').hidden=false;
 document.querySelector('.hud').classList.add('has-selection');
 document.querySelector('#card-number').textContent=`STAGE ${String(i+1).padStart(2,'0')} / 12`;
 document.querySelector('#card-title').textContent=stageNames[i];
 document.querySelector('#card-detail').textContent=`${biomes[Math.floor(i/3)]} • Roadside rally start tower`;
 towerGroups.forEach((t,j)=>t.scale.setScalar(j===i?1.55:.88));
 towerGroups[i].getWorldPosition(goalTarget);goalTarget.y+=.43;goalRadius=8.8;goalPolar=1.02;
 window.__selectedStage=i+1;
}
window.__mapB={
  rotateBy:r=>goalAzimuth+=r,
  setView:(a,p,r)=>{goalAzimuth=a;goalPolar=p;goalRadius=r;},
  resetView,
  stageScreenPosition:i=>{const p=towerGroups[i].localToWorld(new THREE.Vector3(0,.66,0)).project(camera);return {x:(p.x+1)*innerWidth/2,y:(1-p.y)*innerHeight/2};},
  getState:()=>({azimuth,polar,radius,selected:window.__selectedStage||null,towers:towerGroups.length,geometry:true,terrainReady,terrainSource:useBlenderTerrain?'blender-glb':'procedural'})
};
function resize(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);}
addEventListener('resize',resize);
const clock=new THREE.Clock();
function frame(){
 const dt=Math.min(.05,clock.getDelta());const a=1-Math.exp(-dt*9);
 azimuth=THREE.MathUtils.lerp(azimuth,goalAzimuth,a);polar=THREE.MathUtils.lerp(polar,goalPolar,a);radius=THREE.MathUtils.lerp(radius,goalRadius,a);
 target.lerp(goalTarget,a);
 camera.position.set(Math.sin(azimuth)*Math.sin(polar)*radius,Math.cos(polar)*radius+target.y,Math.cos(azimuth)*Math.sin(polar)*radius);
 camera.lookAt(target);
 renderer.render(scene,camera);requestAnimationFrame(frame);
}
frame();
