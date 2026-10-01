"""Read-only CPU visibility/conservation audit of the guarded orbital trial."""
from pathlib import Path
import hashlib,json,struct
import numpy as np

ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
EVIDENCE=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind14/construction01')
def load(path):
    raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0]
    return raw,json.loads(raw[20:20+size]),raw[28+size:]
CORRECTION=True
path=ROOT/'rig-adapter01/body-bind14/construction01/rider.glb'

raw,doc,binary=load(path)
sraw,source,sbin=load(ROOT/'rig-adapter01/body-bind11/guarded-correction01/rider.glb')
def array(document,buf,index):
    a=document['accessors'][index];v=document['bufferViews'][a['bufferView']]
    lanes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];width=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],lanes),dtype=dtype,buffer=buf,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',lanes*width),width)).copy()
primitives=doc['meshes'][1]['primitives']
geometry=[];attributes=[]
for p in primitives:
    a={k:array(doc,binary,i) for k,i in p['attributes'].items()};t=array(doc,binary,p['indices']).reshape(-1,3)
    attributes.append(a);geometry.append(a['POSITION'][t].astype(float))
def ray_x(triangles,y,z):
    yz=triangles[:,:,1:];point=np.array([y,z]);eligible=(yz.min(1)<=point+1e-10).all(1)&(yz.max(1)>=point-1e-10).all(1)
    triangles=triangles[eligible];yz=yz[eligible]
    a=yz[:,1]-yz[:,0];b=yz[:,2]-yz[:,0];d=point-yz[:,0]
    det=a[:,0]*b[:,1]-a[:,1]*b[:,0];good=abs(det)>1e-15
    a=a[good];b=b[good];d=d[good];det=det[good];triangles=triangles[good]
    u=(d[:,0]*b[:,1]-d[:,1]*b[:,0])/det;q=(a[:,0]*d[:,1]-a[:,1]*d[:,0])/det
    bary=np.c_[1-u-q,u,q];inside=(bary>=-1e-8).all(1)
    return None if not inside.any() else float(np.max(np.sum(bary[inside]*triangles[inside,:,0],axis=1)))
skin=np.concatenate(geometry[:3]);rows=[]
for name,cy,cz,inner in [('positiveZ',1.6965,.032,6),('negativeZ',1.697,-.0332,4)]:
    for horizontal in np.linspace(-.009,.009,13):
        for vertical in np.linspace(-.0019,.0024,7):
            if CORRECTION:
                sin_angle=np.sqrt(1-(horizontal/.0118)**2)
                bound=(.0030 if vertical>=0 else .0019)*sin_angle**1.3
                if abs(vertical)>bound-.0001:continue
            yy=cy-.0007+vertical;zz=cz+horizontal
            ix=ray_x(geometry[inner],yy,zz);sx=ray_x(skin,yy,zz)
            visible=ix is not None and (sx is None or ix>sx+1e-7)
            rows.append(dict(eye=name,y=yy,z=zz,irisX=ix,skinX=sx,irisBeforeAllSkin=visible))
def segment_hits(start,end,triangles):
    direction=end-start;e1=triangles[:,1]-triangles[:,0];e2=triangles[:,2]-triangles[:,0]
    cross=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.sum(e1*cross,axis=1)
    good=abs(det)>1e-14;inverse=np.zeros(len(det));inverse[good]=1/det[good]
    s=start-triangles[:,0];u=inverse*np.sum(s*cross,axis=1);q=np.cross(s,e1)
    v=inverse*np.sum(q*direction,axis=1);t=inverse*np.sum(q*e2,axis=1)
    return good&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(t>=-1e-8)&(t<=1+1e-8)
intersection=[]
eyes=np.concatenate([geometry[4],geometry[6]])
for i,face in enumerate(geometry[2]):
    candidates=np.flatnonzero((face.min(0)<=eyes.max(1)+1e-10).all(1)&(face.max(0)>=eyes.min(1)-1e-10).all(1))
    if not len(candidates):continue
    targets=eyes[candidates];hits=np.zeros(len(candidates),dtype=bool)
    for edge in range(3):hits|=segment_hits(face[edge],face[(edge+1)%3],targets)
    for j,target in enumerate(targets):
        if not hits[j]:
            hits[j]=any(segment_hits(target[k],target[(k+1)%3],face[None])[0] for k in range(3))
    intersection.extend([dict(lidTriangle=i,eyeTriangle=int(q)) for q in candidates[hits]])
conservation=[]
for k,index in source['meshes'][1]['primitives'][0]['attributes'].items():
    old=array(source,sbin,index);new=attributes[0][k]
    conservation.append(dict(attribute=k,originalPrefixExact=bool(np.array_equal(old,new[:len(old)]))))
report=dict(status='CPU numerical audit only; parent appearance judgement pending',candidateSHA256=hashlib.sha256(raw).hexdigest(),originalBinaryPrefixExact=binary[:len(sbin)]==sbin,originalHeadAttributes=conservation,
    originalOtherMeshesExact=all(doc['meshes'][i]==source['meshes'][i] for i in range(len(source['meshes'])) if i!=1),
    originalCheekPrimitiveExact=doc['meshes'][1]['primitives'][1]==source['meshes'][1]['primitives'][1],
    originalNodesSkinAnimationExact=all(doc[k]==source[k] for k in ['nodes','skins','animations','scenes']),
    visibleApertureRays=len(rows),irisBeforeAllSkinRays=sum(row['irisBeforeAllSkin'] for row in rows),rayTests=rows,
    lidOpaqueEyeIntersectionPairs=len(intersection),intersectionPairs=intersection,
    limits=['Axis-aligned aperture rays prove frontal donor visibility only, not nine-angle or moving appearance.','Triangle intersections include hidden inward-sheet transitions; they do not alone locate visible defects.','New four-ring skin uses sampled constant skin color and lacks original pore detail.','Transparent cornea sorting and hood/neck motion require actual parent renders.'])
construction=json.loads((EVIDENCE/'construction.json').read_text())
regions=[];offset=0
for eye in construction['eyes']:
    for role,count in zip(['outside-to-ring1','ring1-to-ring2','ring2-to-aperture','aperture-to-tunnel','tunnel-to-inside'],[eye['outerVertices']+128,256,256,256,eye['innerVertices']+128]):
        regions.append((offset,offset+count,eye['eye']+'/'+role));offset+=count
from collections import Counter
report['intersectionRegionCounts']=dict(Counter(next(label for start,end,label in regions if start<=pair['lidTriangle']<end) for pair in intersection))
report['frontLidOpaqueEyeIntersectionPairs']=sum(count for label,count in report['intersectionRegionCounts'].items() if not label.endswith('/tunnel-to-inside'))
assert report['originalBinaryPrefixExact'] and all(row['originalPrefixExact'] for row in conservation)
assert report['originalOtherMeshesExact'] and report['originalCheekPrimitiveExact'] and report['originalNodesSkinAnimationExact']
(EVIDENCE/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['irisBeforeAllSkinRays']==report['visibleApertureRays'], 'Authored lid obstructs intended visible aperture'
print(json.dumps({k:report[k] for k in ['visibleApertureRays','irisBeforeAllSkinRays','lidOpaqueEyeIntersectionPairs','originalBinaryPrefixExact']}))

assert report['frontLidOpaqueEyeIntersectionPairs']==0, 'Front lid intersects opaque eye'
