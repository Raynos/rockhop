"""Read-only CPU native eye appearance audit. Orthographic fields are diagnostics, not renders."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,io,json,struct
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,center_of_mass,binary_erosion
REPO=Path('/Users/raynos/projects/games/rockhop');ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind27';PRIVATE=ROOT/'body-bind27';OUT.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True)
source=ROOT/'body-bind22/skin-field01/rider.glb';raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest();assert sha=='cc20ab813669b628c8e5d21596b655188d7188770adc374377cebf40769232ff'
n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
def arr(index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];w={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];s=np.dtype(dtype).itemsize
 return np.ndarray((a['count'],w),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',w*s),s)).copy()
def bitmap(mi):
 tex=doc['textures'][doc['materials'][mi]['pbrMetallicRoughness']['baseColorTexture']['index']];v=doc['bufferViews'][doc['images'][tex['source']]['bufferView']];png=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
 return np.array(Image.open(io.BytesIO(png)).convert('RGBA')),png
pixels,png=bitmap(6);Image.open(io.BytesIO(png)).save(PRIVATE/'source-eye-atlas.png');rgb=pixels[:,:,:3].astype(float)/255
dark=(pixels[:,:,:3].max(2)<20)&(pixels[:,:,3]==255);labs,_=label(dark);sizes=np.bincount(labs.ravel());sizes[0]=0;major=np.argsort(sizes)[-2:]
iris_mask=(rgb[:,:,0]>rgb[:,:,1]*1.35)&(rgb[:,:,0]>rgb[:,:,2]*1.6)&(rgb[:,:,0]-rgb[:,:,2]>.10)&(pixels[:,:,3]==255)
def uv_hit(primitive,targets):
 p=doc['meshes'][1]['primitives'][primitive];pos=arr(p['attributes']['POSITION']).astype(float);uv=arr(p['attributes']['TEXCOORD_0']).astype(float);normal=arr(p['attributes']['NORMAL']).astype(float);tri=arr(p['indices']).reshape(-1,3);t=uv[tri];a=t[:,1]-t[:,0];b=t[:,2]-t[:,0];det=a[:,0]*b[:,1]-a[:,1]*b[:,0]
 valid=abs(det)>1e-15;answers=[]
 for q in targets:
  d=q-t[:,0];u=np.divide(d[:,0]*b[:,1]-d[:,1]*b[:,0],det,out=np.zeros(len(det)),where=valid);v=np.divide(a[:,0]*d[:,1]-a[:,1]*d[:,0],det,out=np.zeros(len(det)),where=valid);ids=np.flatnonzero(valid&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7))
  if not len(ids):answers.append(None);continue
  k=ids[0];w=np.array([1-u[k]-v[k],u[k],v[k]]);point=w@pos[tri[k]];nn=w@normal[tri[k]];nn/=np.linalg.norm(nn);answers.append((point,nn,int(k),tri[k].tolist(),w.tolist()))
 return answers
def raster(primitive,cy,cz,with_uv=False):
 p=doc['meshes'][1]['primitives'][primitive];pos=arr(p['attributes']['POSITION']).astype(float);tri=arr(p['indices']).reshape(-1,3);uv=arr(p['attributes']['TEXCOORD_0']).astype(float) if with_uv else None
 zz=np.linspace(cz-.012,cz+.012,241);yy=np.linspace(cy+.008,cy-.008,161);depth=np.full((len(yy),len(zz)),-np.inf);uvfield=np.zeros((*depth.shape,2));face=np.full(depth.shape,-1,dtype=int)
 xyz=pos[tri];keep=(xyz[:,:,0].max(1)>.68)&(xyz[:,:,1].min(1)<=yy[0])&(xyz[:,:,1].max(1)>=yy[-1])&(xyz[:,:,2].min(1)<=zz[-1])&(xyz[:,:,2].max(1)>=zz[0])
 for k in np.flatnonzero(keep):
  t=xyz[k];j0=max(0,int(np.ceil((t[:,2].min()-zz[0])/.0001-1e-7)));j1=min(len(zz)-1,int(np.floor((t[:,2].max()-zz[0])/.0001+1e-7)));i0=max(0,int(np.ceil((yy[0]-t[:,1].max())/.0001-1e-7)));i1=min(len(yy)-1,int(np.floor((yy[0]-t[:,1].min())/.0001+1e-7)))
  if j1<j0 or i1<i0:continue
  a=t[1,1:]-t[0,1:];b=t[2,1:]-t[0,1:];det=a[0]*b[1]-a[1]*b[0]
  if abs(det)<1e-16:continue
  Y,Z=np.meshgrid(yy[i0:i1+1],zz[j0:j1+1],indexing='ij');dy=Y-t[0,1];dz=Z-t[0,2];u=(dy*b[1]-dz*b[0])/det;v=(a[0]*dz-a[1]*dy)/det;w=1-u-v;x=w*t[0,0]+u*t[1,0]+v*t[2,0]
  sl=np.s_[i0:i1+1,j0:j1+1];update=(u>=-1e-8)&(v>=-1e-8)&(w>=-1e-8)&(x>depth[sl]);depth[sl][update]=x[update];face[sl][update]=k
  if uv is not None:
   value=w[:,:,None]*uv[tri[k,0]]+u[:,:,None]*uv[tri[k,1]]+v[:,:,None]*uv[tri[k,2]];uvfield[sl][update]=value[update]
 return depth,uvfield,face,yy,zz
def sample(uv):
 h,w=pixels.shape[:2];x=uv[:,:,0]*w-.5;y=uv[:,:,1]*h-.5;x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);fx=x-x0;fy=y-y0
 return sum(rgb[np.clip(y0+dy,0,h-1),np.clip(x0+dx,0,w-1)]*((fx if dx else 1-fx)*(fy if dy else 1-fy))[:,:,None] for dx in [0,1] for dy in [0,1])
results=[]
for name,primitive,cy,cz,cx in [('negativeZ',4,1.697,-.0332,.747949309-.0152355616-.004),('positiveZ',6,1.6965,.032,.7469700990846553-.0152355616-.004)]:
 landmark=[]
 for lab in major:
  py,px=center_of_mass(dark,labs,lab);hit=uv_hit(primitive,[np.array([px/1023,py/1023])])[0]
  if hit is None:continue
  region=(labs==lab);boundary=region&~binary_erosion(region);ry,rx=np.nonzero(boundary);puv=np.c_[rx/1023,ry/1023];mapped=[h for h in uv_hit(primitive,puv[::2]) if h is not None];p=np.array([h[0] for h in mapped]);axis=hit[0]-[cx,cy,cz];axis/=np.linalg.norm(axis)
  # Texture iris extent is identified explicitly by chroma around each pupil, not an anatomical diameter assumption.
  yy0,xx0=np.indices(dark.shape);roi=(xx0-px)**2+(yy0-py)**2<145**2;iris=iris_mask&roi;iry,irx=np.nonzero(iris&~binary_erosion(iris));ip=np.array([h[0] for h in uv_hit(primitive,np.c_[irx[::3]/1023,iry[::3]/1023]) if h is not None])
  iris_pixels=rgb[iris];lum=np.sum(iris_pixels*np.array([.2126,.7152,.0722]),axis=1)
  landmark.append({'pupilTextureComponent':int(lab),'pupilTexturePixels':int(sizes[lab]),'pupilTextureCentre':[float(px),float(py)],'pupilTextureBBoxPixels':[int(rx.min()),int(ry.min()),int(rx.max()),int(ry.max())],'sourceGLTFPrimitive':primitive,'pupilCentreXYZ':hit[0].tolist(),'pupilTriangleID':hit[2],'pupilTriangleVertices':hit[3],'pupilBarycentrics':hit[4],'pupilInterpolatedNormal':hit[1].tolist(),'radialGazeAxisXYZ':axis.tolist(),'radialGazePitchDegrees':float(np.degrees(np.arctan2(axis[1],axis[0]))),'radialGazeYawDegrees':float(np.degrees(np.arctan2(axis[2],axis[0]))),'pupilYZDiameterMM':(np.ptp(p[:,1:],axis=0)*1000).tolist(),'irisChromaBBoxPixels':[int(irx.min()),int(iry.min()),int(irx.max()),int(iry.max())],'irisYZDiameterMM':(np.ptp(ip[:,1:],axis=0)*1000).tolist(),'irisUnlitMedianRGB':np.median(iris_pixels,axis=0).tolist(),'irisUnlitEncodedSRGBLumaPercentiles':np.percentile(lum,[0,10,50,90,100]).tolist(),'irisSamples':len(iris_pixels)})
 assert len(landmark)==1
 eye,uv,face,ys,zs=raster(primitive,cy,cz,True);skin=np.maximum.reduce([raster(i,cy,cz)[0] for i in [0,1,2]])
 visible=np.isfinite(eye)&(eye>skin+.000001);col=sample(uv);brown=(col[:,:,0]>col[:,:,1]*1.35)&(col[:,:,0]>col[:,:,2]*1.6)&(col[:,:,0]-col[:,:,2]>.10);pupil=col.max(2)<20/255
 vi=np.nonzero(visible);iris_vis=visible&brown;pupil_vis=visible&pupil;image=np.full((*visible.shape,3),.20);image[visible]=col[visible]
 board=Image.fromarray((image*255+.5).astype(np.uint8)).resize((723,483),Image.Resampling.NEAREST);ImageDraw.Draw(board).text((8,8),name+' actual source22 unlit front UV/occlusion field; not gameplay',fill='white');board.save(OUT/f'{name}-unlit-aperture-field.png')
 # Trace exact native inner-loop source IDs, without touching its registration or closure.
 native_side='R' if name=='positiveZ' else 'L';native=np.load(ROOT/f'anatomical-eye-donor01/standalone01/fitted-native-{native_side}-lids.npz');q=native['quads'];edges=Counter(tuple(sorted((int(a),int(b)))) for f in q for a,b in zip(f,np.roll(f,-1)));adj=defaultdict(list)
 for (a,b),count in edges.items():
  if count==1:adj[a].append(b);adj[b].append(a)
 seen=set();loops=[]
 for first in adj:
  if first in seen:continue
  loop=[];prev=None;current=first
  while current not in seen:
   seen.add(current);loop.append(current);next_vertex=next(k for k in adj[current] if k!=prev);prev,current=current,next_vertex
  loops.append(np.array(loop))
 loops.sort(key=lambda ids:np.ptp(native['positions'][ids,1])*np.ptp(native['positions'][ids,2]));inner=loops[0];assert len(inner)==32
 innerpos=native['positions'][inner];loop_report={'nativeSide':native_side,'localInnerLoopIDs':inner.tolist(),'MakeHumanBaseOBJInnerLoopVertexIDs':native['nativeVertexIDs'][inner].tolist(),'apertureInnerLoopBBoxXYZ':[innerpos.min(0).tolist(),innerpos.max(0).tolist()],'nativeApertureWidthHeightMM':[float(np.ptp(innerpos[:,2])*1000),float(np.ptp(innerpos[:,1])*1000)],'geometryUnchanged':True}
 plot={'eye':name,'sourcePrimitive':primitive,'material':doc['materials'][6],'pupilAndIris':landmark[0],'nativeLoopProvenance':loop_report,'visibleEyeProjectionBBoxMM':[float((zs[vi[1]].max()-zs[vi[1]].min())*1000),float((ys[vi[0]].max()-ys[vi[0]].min())*1000)],'visibleEyePixels':int(visible.sum()),'visibleIrisChromaPixels':int(iris_vis.sum()),'visiblePupilPixels':int(pupil_vis.sum()),'visibleIrisChromaFraction':float(iris_vis.sum()/visible.sum()),'projectionPitchYawDegrees':[0,0],'gridSpacingMM':.1,'visibleIrisChromaSRGBMean':col[iris_vis].mean(0).tolist(),'pixelMaskNPZ':str(PRIVATE/f'{name}-occlusion-field.npz')}
 np.savez_compressed(PRIVATE/f'{name}-occlusion-field.npz',visible=visible,irisMask=iris_vis,pupilMask=pupil_vis,eyeDepth=eye,skinDepth=skin,UV=uv,sourceEyeTriangle=face,y=ys,z=zs);results.append(plot)
assert source.read_bytes()==raw
report={'status':'READONLY measured source22 eye texture/UV/occlusion/gaze diagnosis; no candidate or appearance grade','sourceSHA256':sha,'eyeTexturePNG_SHA256':hashlib.sha256(png).hexdigest(),'eyeTexturePixels':list(pixels.shape[:2][::-1]),'eyeTextureSource':'CC0 MakeHuman brown_eye.png, embedded byte exact','indexConvention':'All primitive, triangle, render-vertex and native source-array IDs zero-based; add1 for an OBJ v token.','eyes':results,'limits':['Iris boundary uses declared source chroma threshold, not anatomy ground truth.','Pupil radial axis is relative to retained donor sphere-fit centre; depressed iris normals are reported separately and are not gaze ground truth.','CPU frontal field is unlit +X orthographic diagnostic, not matched gameplay camera/light or physical transparency.','Reference pixel ratios and appearance cause ranking require parent visual judgment.','No geometry, texture, material, shader, rig, source file or player asset changes.']}
(OUT/'eye-appearance-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
