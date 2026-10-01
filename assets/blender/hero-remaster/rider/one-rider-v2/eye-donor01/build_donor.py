"""Untouched CC0 eye anatomy -> measured standalone donor, CPU only.

No Blender, GPU, head/body donor, fitting operation, or source modification.
The common uniform scale chooses a26mm inner horizontal diameter. Per-eye
translation sets66mm center spacing; source UVs and normals remain authoritative.
"""
import argparse
import hashlib
import json
import struct
import time
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label, center_of_mass

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',required=True)
parser.add_argument('--evidence',required=True)
args=parser.parse_args()
out=Path(args.out); evidence=Path(args.evidence)
out.mkdir(parents=True,exist_ok=True); evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'eyes.glb').exists(), 'Frozen donor exists'
start=time.monotonic()
source=Path('/Users/raynos/projects/weights/makehuman/system-cc0/eyes')
obj=source/'high-poly/high-poly.obj'; image=source/'materials/brown_eye.png'
material=source/'materials/brown.mhmat'; mhclo=source/'high-poly/high-poly.mhclo'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={str(p):sha(p) for p in [obj,image,material,mhclo]}
v=[]; n=[]; uv=[]; polygons=[]
for line in obj.read_text().splitlines():
    t=line.split()
    if not t:continue
    if t[0]=='v':v.append(list(map(float,t[1:4])))
    elif t[0]=='vn':n.append(list(map(float,t[1:4])))
    elif t[0]=='vt':uv.append(list(map(float,t[1:3])))
    elif t[0]=='f':polygons.append([tuple(int(x)-1 for x in s.split('/')) for s in t[1:]])
v,n,uv=map(np.array,(v,n,uv))
assert len(n)==len(v)==1064 and np.isfinite(v).all() and np.isfinite(uv).all()
assert np.min(uv)>=0 and np.max(uv)<=1
adj=[set() for _ in v]
for f in polygons:
    for a,b in zip(f,f[1:]+f[:1]):adj[a[0]].add(b[0]);adj[b[0]].add(a[0])
unseen=set(range(len(v)));comps=[]
while unseen:
    seed=min(unseen);unseen.remove(seed);c={seed};stack=[seed]
    while stack:
        q=stack.pop()
        for a in adj[q]&unseen:unseen.remove(a);c.add(a);stack.append(a)
    comps.append(c)
assert [len(c) for c in comps]==[256,276,256,276]
scale=.026/(v[sorted(comps[1]),0].max()-v[sorted(comps[1]),0].min())
rotation=np.array([[0.,0.,1.],[0.,1.,0.],[-1.,0.,0.]])
assert np.linalg.det(rotation)==1
pixels=np.array(Image.open(image).convert('RGBA'))
def sample_uv(uu):
    return pixels[np.clip(np.rint((1-uu[:,1])*(pixels.shape[0]-1)).astype(int),0,pixels.shape[0]-1),np.clip(np.rint(uu[:,0]*(pixels.shape[1]-1)).astype(int),0,pixels.shape[1]-1)]
inner_centers=[];normalized=v.copy(); center_info=[]
for eye,inner in enumerate([1,3]):
    p=v[sorted(comps[inner])]
    # Algebraic sphere-center least squares is a frame origin, not a change
    # to source shape. Source inner globe has a depressed iris region.
    coefficient=np.linalg.lstsq(np.c_[2*p,np.ones(len(p))],np.sum(p*p,axis=1),rcond=None)[0]
    center=coefficient[:3]; inner_centers.append(center)
    desired=np.array([0.,0.,-.033 if eye==0 else .033])
    ids=sorted(comps[inner]|comps[inner-1])
    relative=v[ids]-center
    normalized[ids]=np.stack([relative[:,2],relative[:,1],-relative[:,0]],axis=1)*scale+desired
    center_info.append(dict(side='R' if eye==0 else 'L',sourceCenter=center.tolist(),normalizedCenter=desired.tolist(),originMethod='algebraic least-squares inner globe sphere center',radiusResidualRangeMeters=(np.linalg.norm(p-center,axis=1)*scale).tolist()))
normal=np.stack([n[:,2],n[:,1],-n[:,0]],axis=1)
normal/=np.linalg.norm(normal,axis=1)[:,None]
assert np.isfinite(normal).all() and np.isfinite(normalized).all()
triangles=[]; tri_uv=[];component_reports=[];component_triangles=[]
for i,c in enumerate(comps):
    ff=[f for f in polygons if f[0][0] in c]; tt=[];uu=[]
    for f in ff:
        for j in range(1,len(f)-1):
            corners=[f[0],f[j],f[j+1]];tt.append([x[0] for x in corners]);uu.append([x[1] for x in corners])
    tt=np.array(tt,dtype=np.int32);uu=np.array(uu,dtype=np.int32)
    component_triangles.append(tt);triangles.extend(tt);tri_uv.extend(uu)
    edges=Counter(tuple(sorted((a[0],b[0]))) for f in ff for a,b in zip(f,f[1:]+f[:1]))
    uv_indices=sorted({p[1] for f in ff for p in f}); rgba=sample_uv(uv[uv_indices])
    area=np.linalg.norm(np.cross(normalized[tt[:,1]]-normalized[tt[:,0]],normalized[tt[:,2]]-normalized[tt[:,0]]),axis=1)/2
    auv=uv[uu];uvab=auv[:,1]-auv[:,0];uvac=auv[:,2]-auv[:,0]
    uvarea=np.abs(uvab[:,0]*uvac[:,1]-uvab[:,1]*uvac[:,0])/2
    geomnorm=np.cross(normalized[tt[:,1]]-normalized[tt[:,0]],normalized[tt[:,2]]-normalized[tt[:,0]])
    geomnorm/=np.linalg.norm(geomnorm,axis=1)[:,None]
    normaldot=np.sum(geomnorm*normal[tt].mean(axis=1),axis=1)
    boundary=[x for x,count in edges.items() if count==1]
    points=normalized[sorted(c)]
    component_reports.append(dict(component=i,side='R' if i<2 else 'L',role='corneal transparent outer shell' if i%2==0 else 'opaque sclera/iris inner globe',sourceVertexRange=[min(c),max(c)],sourceVertices=len(c),sourcePolygons=len(ff),triangles=len(tt),normalizedBBoxMeters=[points.min(0).tolist(),points.max(0).tolist()],horizontalWidthMM=float(np.ptp(points[:,2])*1000),verticalHeightMM=float(np.ptp(points[:,1])*1000),frontToBackDepthMM=float(np.ptp(points[:,0])*1000),sourceUVBBox=[uv[uv_indices].min(0).tolist(),uv[uv_indices].max(0).tolist()],sourceSampledAlphaUnique=np.unique(rgba[:,3]).tolist(),boundaryEdges=len(boundary),nonManifoldEdges=sum(count>2 for count in edges.values()),closedManifold=False,boundaryPlaneXRangeMeters=[float(normalized[np.array(boundary)[:,0],0].min()),float(normalized[np.array(boundary)[:,0],0].max())],zeroAreaTriangles=int(np.sum(area<1e-14)),zeroUVAreaTriangles=int(np.sum(uvarea<1e-14)),faceVsPreservedVertexNormalDotRange=[float(normaldot.min()),float(normaldot.max())]))
triangles=np.array(triangles);tri_uv=np.array(tri_uv)

def segment_tri_hits(a,b,t):
    d=b-a; e1=t[:,1]-t[:,0];e2=t[:,2]-t[:,0]
    p=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.sum(e1*p,axis=1)
    valid=np.abs(det)>1e-14;inv=np.zeros(len(det));inv[valid]=1/det[valid]
    s=a-t[:,0];u=inv*np.sum(s*p,axis=1);q=np.cross(s,e1)
    vv=inv*np.sum(q*d,axis=1);tt=inv*np.sum(q*e2,axis=1)
    return valid&(u>=-1e-9)&(vv>=-1e-9)&(u+vv<=1+1e-9)&(tt>=-1e-9)&(tt<=1+1e-9)

intersection_reports=[]
for outer,inner in [(0,1),(2,3)]:
    aa=normalized[component_triangles[outer]];bb=normalized[component_triangles[inner]]
    found=set()
    for i,t in enumerate(aa):
        eligible=np.where(np.all(t.min(0)<=bb.max(1)+1e-10,axis=1)&np.all(t.max(0)>=bb.min(1)-1e-10,axis=1))[0]
        if not len(eligible):continue
        targets=bb[eligible]
        hit=np.zeros(len(eligible),dtype=bool)
        for j in range(3):hit|=segment_tri_hits(t[j],t[(j+1)%3],targets)
        # Reciprocal segment test handles a small triangle wholly crossing a
        # larger one without the larger one's edges entering the smaller.
        for j,k in enumerate(eligible):
            if not hit[j]:
                for edge in range(3):
                    if segment_tri_hits(bb[k,edge],bb[k,(edge+1)%3],t[None])[0]:hit[j]=True;break
        found.update((i,int(k)) for k in eligible[hit])
    intersection_reports.append(dict(components=[outer,inner],noncoplanarTriangleIntersectionPairs=len(found),method='AABB broadphase plus reciprocal Moller-Trumbore segment/triangle tests',limit='Does not assert absence of coplanar overlapping triangles or eye/head intersections; donor has no head.'))

binary=bytearray();views=[];accessors=[]
def append(data,target=None):
    while len(binary)%4:binary.append(0)
    offset=len(binary);binary.extend(data);r=dict(buffer=0,byteOffset=offset,byteLength=len(data))
    if target:r['target']=target
    views.append(r);return len(views)-1
def accessor(array,kind,ctype,target=None):
    array=np.ascontiguousarray(array);view=append(array.tobytes(),target)
    a=dict(bufferView=view,componentType=ctype,count=len(array),type=kind)
    if kind=='VEC3':a.update(min=array.min(0).tolist(),max=array.max(0).tolist())
    accessors.append(a);return len(accessors)-1
meshes=[];nodes=[]
for i,tt in enumerate(component_triangles):
    # OBJ corners split at UV seams, positions and normals unchanged.
    local={};positions=[];normals=[];texcoord=[];indices=[]
    ff=[f for f in polygons if f[0][0] in comps[i]]
    for f in ff:
        for j in range(1,len(f)-1):
            for vertex,texture in [f[0],f[j],f[j+1]]:
                key=(vertex,texture)
                if key not in local:
                    local[key]=len(positions);positions.append(normalized[vertex]);normals.append(normal[vertex]);texcoord.append([uv[texture,0],1-uv[texture,1]])
                indices.append(local[key])
    primitive=dict(attributes=dict(POSITION=accessor(np.array(positions,dtype='<f4'),'VEC3',5126,34962),NORMAL=accessor(np.array(normals,dtype='<f4'),'VEC3',5126,34962),TEXCOORD_0=accessor(np.array(texcoord,dtype='<f4'),'VEC2',5126,34962)),indices=accessor(np.array(indices,dtype='<u2'),'SCALAR',5123,34963),material=0 if i%2 else 1,mode=4)
    name=('R' if i<2 else 'L')+('_cornea' if i%2==0 else '_sclera_iris')
    meshes.append(dict(name=name,primitives=[primitive]));nodes.append(dict(name=name,mesh=i,extras=dict(sourceComponent=i)))
imgview=append(image.read_bytes())
doc=dict(asset=dict(version='2.0',generator='Rockhop CPU measured CC0 eye donor01'),scene=0,scenes=[dict(nodes=list(range(4)))],nodes=nodes,meshes=meshes,buffers=[dict(byteLength=len(binary))],bufferViews=views,accessors=accessors,images=[dict(bufferView=imgview,mimeType='image/png',name='untouched MakeHuman brown_eye.png')],textures=[dict(source=0,sampler=0)],samplers=[dict(magFilter=9729,minFilter=9987,wrapS=33071,wrapT=33071)],materials=[dict(name='CC0 brown iris and sclera',pbrMetallicRoughness=dict(baseColorTexture=dict(index=0),baseColorFactor=[1,1,1,1],roughnessFactor=.35,metallicFactor=0),alphaMode='OPAQUE',doubleSided=False),dict(name='Conservative transparent corneal film',pbrMetallicRoughness=dict(baseColorFactor=[1,1,1,.035],roughnessFactor=.08,metallicFactor=0),alphaMode='BLEND',doubleSided=False,extras=dict(sourceAlphaWasZero=True,physicalRefraction=False,adaptation='Source transparent shell uses neutral3.5percent-alpha film for conservative standard-PBR highlights; no blue diffuse texture or proprietary eye shader.'))],extras=dict(status='UNACCEPTED standalone CC0 donor, not fitted or rigged',centersMeters=[[0,0,-.033],[0,0,.033]],innerHorizontalDiameterMeters=.026,axis=dict(front='+X',up='+Y',left='+Z'),sourceHashes=sources))
encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);binary+=b'\0'*((-len(binary))%4)
glb=struct.pack('<4sII',b'glTF',2,12+8+len(encoded)+8+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(binary),b'BIN\0')+binary
(out/'eyes.glb').write_bytes(glb)
np.savez(out/'source-and-normalized.npz',sourceVertices=v,sourceNormals=n,sourceUV=uv,normalizedVertices=normalized,normalizedNormals=normal,triangles=triangles,triangleUVIndices=tri_uv,componentID=np.array([next(i for i,c in enumerate(comps) if j in c) for j in range(len(v))]))
license_header='\n'.join(obj.read_text().splitlines()[:16])+'\n'
(evidence/'source-license-header.txt').write_text(license_header)
# UV evidence is the untouched texture plus exact source wire overlays. This
# is a CPU inspection diagram, not an accepted Blender/game render.
im=Image.open(image).convert('RGB');draw=ImageDraw.Draw(im)
for i,tts in enumerate(component_triangles):
    ff=[f for f in polygons if f[0][0] in comps[i]]
    color=(0,220,255) if i%2==0 else (255,150,0)
    for f in ff:
        coords=[(uv[p[1],0]*1023,(1-uv[p[1],1])*1023) for p in f]
        draw.line(coords+[coords[0]],fill=color,width=1)
im.save(evidence/'source-uv-overlay.png')
report=dict(status='UNACCEPTED standalone anatomical eye donor; parent must fit, render and judge',cpuOnly=True,noSourceOrBodyMutation=True,sourceHashes=sources,sourcesAfter={p:sha(p) for p in sources},scriptSHA256=sha(__file__),donorSHA256=sha(out/'eyes.glb'),artifact=str(out/'eyes.glb'),uniformScale=scale,sourceUnits='Raw OBJ units; explicitly normalized by inner horizontal span, no assumed raw unit conversion.',axis=dict(front='+X',up='+Y',left='+Z',properRotationDeterminant=float(np.linalg.det(rotation))),pairSpacingMM=66,innerHorizontalDiameterMM=26,outerHorizontalDiameterMM=component_reports[0]['horizontalWidthMM'],centerFrames=center_info,components=component_reports,intersections=intersection_reports,UVValidation=dict(sourceRange=[uv.min(0).tolist(),uv.max(0).tolist()],gltfConvention='U unchanged; V=1-sourceV to preserve source PNG orientation',sourceTextureDimensions=list(pixels.shape),textureSHA256=sha(image),textureBytesUntouched=True),normalValidation=dict(sourceCount=len(n),sourceLengthRange=[float(np.linalg.norm(n,axis=1).min()),float(np.linalg.norm(n,axis=1).max())],method='Source vn indexed by vertex number, proper axis rotation and unit normalization only; OBJ faces supply v/vt, no explicit vn corner index'),materials=doc['materials'],limits=['All four surfaces have20 open rear boundary edges; not watertight eyeballs and not declared closed manifold.','Corneal film is a conservative standard-PBR approximation; source MakeHuman GLSL eye/litsphere shader is not reproduced, no refraction claimed.','No target-head fit, eye socket aperture, eyelid occlusion, rig, Blender or gameplay appearance has been validated.','No source face, native head, historical production rider or body geometry used.','UV preservation is validated numerically; parent must inspect actual rendered brown iris orientation.'],wallSeconds=time.monotonic()-start)
assert report['sourceHashes']==report['sourcesAfter']
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(donor=report['artifact'],sha256=report['donorSHA256'],innerMM=26,outerMM=report['outerHorizontalDiameterMM'],components=component_reports,intersections=intersection_reports,wallSeconds=report['wallSeconds']),indent=2))
