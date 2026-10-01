"""Read-only validation of the frozen CPU-exported standalone CC0 donor."""
import argparse,hashlib,json,struct,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import label,center_of_mass

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--out',required=True);ap.add_argument('--evidence',required=True)
a=ap.parse_args();out=Path(a.out);evidence=Path(a.evidence)
data=(out/'eyes.glb').read_bytes();magic,version,total=struct.unpack_from('<4sII',data)
assert magic==b'glTF' and version==2 and total==len(data)
jlen,jtype=struct.unpack_from('<I4s',data,12);assert jtype==b'JSON'
doc=json.loads(data[20:20+jlen]);blen,btype=struct.unpack_from('<I4s',data,20+jlen)
assert btype==b'BIN\0';binary=data[28+jlen:28+jlen+blen]
def accessor(i):
    a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
    dtype={5126:'<f4',5123:'<u2'}[a['componentType']]
    size={'VEC3':3,'VEC2':2,'SCALAR':1}[a['type']]
    result=np.frombuffer(binary,dtype=dtype,count=a['count']*size,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,size)
    assert np.isfinite(result).all()
    return result
source=Path('/Users/raynos/projects/weights/makehuman/system-cc0/eyes')
raw=out/'untouched-sources';raw.mkdir(exist_ok=True)
for p in [source/'high-poly/high-poly.obj',source/'high-poly/high-poly.mhclo',source/'materials/brown.mhmat',source/'materials/brown_eye.png']:
    dest=raw/p.name
    if not dest.exists():shutil.copyfile(p,dest)
    assert dest.read_bytes()==p.read_bytes()
view=doc['bufferViews'][doc['images'][0]['bufferView']]
embedded=binary[view['byteOffset']:view['byteOffset']+view['byteLength']]
assert embedded==(source/'materials/brown_eye.png').read_bytes()
png=np.array(Image.open(source/'materials/brown_eye.png').convert('RGBA'))
dark=(png[:,:,:3].max(2)<20)&(png[:,:,3]==255)
labels,count=label(dark);sizes=np.bincount(labels.ravel());sizes[0]=0
major=np.argsort(sizes)[-2:];pupils=[]
for lab in major:
    cy,cx=center_of_mass(dark,labels,lab)
    # GLB v grows from PNG top towards bottom; source OBJ v grows upwards.
    target=np.array([cx/1023,cy/1023]);hits=[]
    for mesh in [1,3]:
        p=doc['meshes'][mesh]['primitives'][0];pos=accessor(p['attributes']['POSITION']);uv=accessor(p['attributes']['TEXCOORD_0']);norm=accessor(p['attributes']['NORMAL']);idx=accessor(p['indices']).reshape(-1,3)
        assert idx.max()<len(pos) and (uv>=0).all() and (uv<=1).all()
        for tri in idx:
            t=uv[tri].astype(float);e1=t[1]-t[0];e2=t[2]-t[0];q=target-t[0]
            det=e1[0]*e2[1]-e1[1]*e2[0]
            if abs(det)<1e-15:continue
            u=(q[0]*e2[1]-q[1]*e2[0])/det;v=(e1[0]*q[1]-e1[1]*q[0])/det
            if u>=-1e-9 and v>=-1e-9 and u+v<=1+1e-9:
                w=np.array([1-u-v,u,v]);point=np.einsum('i,ij->j',w,pos[tri]);n=np.einsum('i,ij->j',w,norm[tri]);n/=np.linalg.norm(n)
                hits.append(dict(mesh=doc['meshes'][mesh]['name'],pointMeters=point.tolist(),normal=n.tolist(),angleFromFrontDegrees=float(np.degrees(np.arccos(np.clip(n[0],-1,1))))))
    assert len(hits)==1,(target,hits)
    pupils.append(dict(darkConnectedPixels=int(sizes[lab]),sourceImageCenterPixels=[float(cx),float(cy)],gltfUV=target.tolist(),sourceUV=[float(target[0]),float(1-target[1])],surface=hits[0]))
checks=[]
for mesh in doc['meshes']:
    p=mesh['primitives'][0];pos=accessor(p['attributes']['POSITION']);uv=accessor(p['attributes']['TEXCOORD_0']);n=accessor(p['attributes']['NORMAL']);idx=accessor(p['indices'])
    assert idx.max()<len(pos)
    checks.append(dict(name=mesh['name'],vertices=len(pos),triangles=len(idx)//3,normLengthRange=[float(np.linalg.norm(n,axis=1).min()),float(np.linalg.norm(n,axis=1).max())],uvRange=[uv.min(0).tolist(),uv.max(0).tolist()],indexRange=[int(idx.min()),int(idx.max())],allFinite=True))
initial=out.parent/'eyes.glb';initial_compare={}
if initial.exists():
    b=initial.read_bytes();jl=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+jl]);bb=b[28+jl:]
    diffs=[]
    for i,acc in enumerate(doc['accessors']):
        ar=accessor(i);v=d['bufferViews'][d['accessors'][i]['bufferView']];old=np.frombuffer(bb,dtype={5126:'<f4',5123:'<u2'}[acc['componentType']],count=ar.size,offset=v['byteOffset']).reshape(ar.shape)
        diffs.append(dict(accessor=i,maxAbsoluteDelta=float(np.max(np.abs(ar.astype(float)-old.astype(float)))),arrayEqual=bool(np.array_equal(ar,old))))
    assert all(x['maxAbsoluteDelta']==0 for x in diffs)
    initial_compare=dict(initialSHA256=hashlib.sha256(b).hexdigest(),guardedSHA256=hashlib.sha256(data).hexdigest(),allAccessorValuesIdentical=True,limits='Binary SHA differs because signed-zero bits in exact axis rotation differ; geometry, UVs, normals, indices and material parameters have identical numerical values.',accessors=diffs)
report=dict(status='UNACCEPTED donor numerical validation; rendered eye/head fit remains parent work',embeddedSourcePNGByteIdentical=True,untouchedSourceCopies=str(raw),meshes=checks,pupilLandmarks=pupils,initialGuardComparison=initial_compare,limits=['Pupil landmarks locate dark connected source texture regions by UV barycentric interpolation; source pupil normals are tilted slightly and have not been reoriented.','No actual Blender/game render or shader claim; source PNG texture orientation only verified numerically.'])
(evidence/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
