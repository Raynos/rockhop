"""Cheap read-only exact cuff witnesses. No Blender, browser, pose or render."""
import hashlib
import json
import runpy
import struct
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CONTROL = ROOT/'assets/blender/rider-rebuild/glove-anatomical04/controls-orientation02.json'
SOURCE = ROOT/'harness/out/rider-rebuild/selected-complete-engine01/engine03/rider.glb'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
control = json.loads(CONTROL.read_text())
with SOURCE.open('rb') as stream:
    stream.seek(12)
    size, _ = struct.unpack('<II', stream.read(8))
    doc = json.loads(stream.read(size)); stream.read(8); binary = stream.read()

def accessor(index):
    row = doc['accessors'][index]; view = doc['bufferViews'][row['bufferView']]
    dtype = np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[row['componentType']])
    width = {'VEC3':3,'VEC4':4,'SCALAR':1,'MAT4':16}[row['type']]
    return np.ndarray((row['count'],width), dtype=dtype, buffer=binary,
        offset=view.get('byteOffset',0)+row.get('byteOffset',0),
        strides=(view.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()

def mesh(name):
    node = next(n for n in doc['nodes'] if n.get('name')==name)
    assert not any(k in node for k in ('matrix','translation','rotation','scale'))
    primitive = doc['meshes'][node['mesh']]['primitives'][0]
    points = accessor(primitive['attributes']['POSITION'])[:,[0,2,1]]; points[:,1]*=-1
    return points, accessor(primitive['indices']).reshape(-1,3), primitive['attributes']

def front_ray_depths(point, vertices, faces):
    direction=np.array([0.,3.975,-.1]); direction/=np.linalg.norm(direction)
    origin=point-direction*.3; tri=vertices[faces].astype(float)
    a,b,c=tri[:,0],tri[:,1],tri[:,2]; e1=b-a; e2=c-a
    cross=np.cross(direction,e2); det=np.einsum('ij,ij->i',e1,cross)
    ok=abs(det)>1e-14; inv=np.zeros_like(det); inv[ok]=1/det[ok]
    tv=origin-a; u=np.einsum('ij,ij->i',tv,cross)*inv; q=np.cross(tv,e1)
    v=np.einsum('j,ij->i',direction,q)*inv; t=np.einsum('ij,ij->i',e2,q)*inv
    hit=ok&(u>=0)&(v>=0)&(u+v<=1)&(t>=0)
    return sorted((t[hit]-.3).tolist())

hood_v,hood_f,_=mesh('RiderHoodie')
dense=np.load(ROOT/control['pins']['denseSelected']['path'])['vertices']
native=np.load(ROOT/control['pins']['nativeArrays']['path']); names=native['jointNames'].tolist()
frozen=json.loads((CONTROL.parent/'guide-controls02.json').read_text())
guide=np.load(ROOT/frozen['selectedGuide']['path'])['vertices']
closest=runpy.run_path(str(CONTROL.parent/'audit_local04.py'))['closest']
prior=np.load(ROOT/'harness/out/rider-rebuild/glove-anatomical04/solved03/actual-right.npz')['vertices']
report={'acceptedArt':False,'sourceSHA256':sha(SOURCE),'recipeSHA256':sha(Path(__file__)),
 'method':'Exact current GLB native-ID cuff witnesses; nearest hoodie triangle and ray along existing static front camera. Positive ray depth means hoodie behind cuff.',
 'hands':{},'limits':['Static geometry diagnosis, not moving art acceptance.',
 'Signed nearest normal distances are local surface measurements, not a watertight containment verdict.',
 'Actual Garage pose may amplify overlap; no live bone matrix capture was available in its report.']}
for side in ('L','R'):
    raw,_,attrs=mesh('ActualSelectedGlove.'+side); ids=accessor(attrs['_NATIVE_ID']).ravel().astype(int)
    assert np.array_equal(np.unique(ids),np.arange(len(dense)))
    points=np.zeros(dense.shape); points[ids]=raw
    weights=np.zeros((len(dense),4)); weights[ids]=accessor(attrs['WEIGHTS_0'])
    joints=np.zeros((len(dense),4),int); joints[ids]=accessor(attrs['JOINTS_0'])
    wrist=native['jointHeads'][names.index('DEF-hand.'+side)]
    axis=native['jointHeads'][names.index('DEF-forearm.'+side)]-wrist; axis/=np.linalg.norm(axis)
    longitudinal=np.einsum('ij,j->i',points-wrist,axis)
    radius=np.linalg.norm(points-wrist-longitudinal[:,None]*axis,axis=1)
    cuff=(dense[:,1]<-.52)&(longitudinal>.005)
    maximum=int(np.flatnonzero(cuff)[np.argmax(radius[cuff])]); top=int(np.argmax(points[:,2]))
    witnesses=[maximum,top]; tri=hood_f[np.linalg.norm(hood_v[hood_f].mean(1)-wrist,axis=1)<.15]
    cross=np.cross(hood_v[tri[:,1]]-hood_v[tri[:,0]],hood_v[tri[:,2]]-hood_v[tri[:,0]])
    tri=tri[np.linalg.norm(cross,axis=1)>1e-14]
    near=closest(points[witnesses],hood_v,tri); offsets=np.load(CONTROL.parent/f'local-offsets04-{side}.npz')['offsets']
    rows=[]
    for vertex,proximity in zip(witnesses,near):
        gi=int(np.argmin(np.linalg.norm(guide-dense[vertex],axis=1)))
        delta=np.einsum('ij,j->i',np.asarray(control['hands'][side]['initialPlacement']['linear']),offsets[gi])
        row={'nativeVertex':vertex,'originalSource':dense[vertex].tolist(),'currentNativeXYZ':points[vertex].tolist(),
          'nearestOriginalGuideVertex':gi,'nearestGuideLocal04EditMeters':float(np.linalg.norm(delta)),
          'forearmLongitudinalM':float(longitudinal[vertex]),'forearmRadialM':float(radius[vertex]),
          'weights':[[doc['nodes'][doc['skins'][0]['joints'][j]]['name'],float(w)] for j,w in zip(joints[vertex],weights[vertex]) if w],
          'nearestHoodieSurface':proximity,'hoodieFrontRayRelativeDepthM':front_ray_depths(points[vertex],hood_v,hood_f)}
        if side=='R': row['denseDifferenceFromPrior03M']=float(np.linalg.norm(points[vertex]-prior[vertex]))
        rows.append(row)
    report['hands'][side]=rows
(HERE/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
