"""Measure protected-face subdivision conservation from explicit provenance."""
from pathlib import Path
import json,struct
import numpy as np
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
EVIDENCE=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind13/construction01')
def load(path):
    raw=path.read_bytes();size=struct.unpack_from('<I',raw,12)[0]
    return json.loads(raw[20:20+size]),raw[28+size:]
def array(doc,binary,index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    lanes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];width=np.dtype(dt).itemsize
    return np.ndarray((a['count'],lanes),dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',lanes*width),width)).copy()
doc,binary=load(ROOT/'rig-adapter01/body-bind11/guarded-correction01/rider.glb');p=doc['meshes'][1]['primitives'][0]
attrs={k:array(doc,binary,index) for k,index in p['attributes'].items()}
tri=array(doc,binary,p['indices']).reshape(-1,3);original=attrs['POSITION'][tri].astype(float)
newdoc,newbin=load(ROOT/'rig-adapter01/body-bind13/construction01/rider.glb');np0=newdoc['meshes'][1]['primitives'][0]
newattrs={k:array(newdoc,newbin,index) for k,index in np0['attributes'].items()}
provenance=np.load(ROOT/'rig-adapter01/body-bind13/construction01/source-face-provenance.npz')
indices=provenance['updatedTriangles'];origins=provenance['sourceTriangle'];points=provenance['positions'][indices].astype(float)
protected=np.ones(len(tri),dtype=bool)
for cy,cz in [(1.6965,.032),(1.697,-.0332)]:
    overlap=(original[:,:,0].max(1)>.72)&(original[:,:,1].min(1)<=cy+.009)&(original[:,:,1].max(1)>=cy-.009)&(original[:,:,2].min(1)<=cz+.018)&(original[:,:,2].max(1)>=cz-.018)
    protected&=~overlap
rows=[]
for origin in np.flatnonzero(protected):
    selected=np.flatnonzero(origins==origin)
    if len(selected)==1 and np.array_equal(indices[selected[0]],tri[origin]):continue
    assert len(selected)>0,'Protected source face disappeared'
    xyz=original[origin];a=xyz[1]-xyz[0];b=xyz[2]-xyz[0]
    gram=np.array([[a@a,a@b],[a@b,b@b]])
    q=points[selected];d=q-xyz[0]
    uv=np.linalg.solve(gram,np.stack([d@a,d@b],axis=0).reshape(2,-1)).reshape(2,*d.shape[:2]).transpose(1,2,0)
    bary=np.concatenate([1-uv.sum(2,keepdims=True),uv],axis=2)
    reconstruction=np.einsum('tvc,cd->tvd',bary,xyz)
    expected_uv=np.einsum('tvc,cd->tvd',bary,attrs['TEXCOORD_0'][tri[origin]])
    newuv=newattrs['TEXCOORD_0'][indices[selected]]
    expected_weights=np.einsum('tvc,cd->tvd',bary,attrs['WEIGHTS_0'][tri[origin]])
    newweights=newattrs['WEIGHTS_0'][indices[selected]]
    oldarea=np.linalg.norm(np.cross(a,b))/2
    newarea=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1).sum()/2
    rows.append(dict(sourceTriangle=int(origin),updatedTriangleIndices=selected.tolist(),subdivisionTriangles=len(selected),maxPlaneDistanceM=float(np.linalg.norm(q-reconstruction,axis=2).max()),maxUVBarycentricError=float(abs(newuv-expected_uv).max()),maxWeightBarycentricError=float(abs(newweights-expected_weights).max()),relativeAreaError=float(abs(newarea-oldarea)/oldarea),sourceBoundsM=[xyz.min(0).tolist(),xyz.max(0).tolist()]))
report=dict(status='Explicit provenance conservation audit; subdivisions change index equality without a source-surface removal',mapping=str(ROOT/'rig-adapter01/body-bind13/construction01/source-face-provenance.npz'),protectedSourceTriangles=int(protected.sum()),protectedSourceTrianglesSubdivided=len(rows),protectedSourceTrianglesRemoved=0,maxPlaneDistanceM=max((r['maxPlaneDistanceM'] for r in rows),default=0),maxUVBarycentricError=max((r['maxUVBarycentricError'] for r in rows),default=0),maxWeightBarycentricError=max((r['maxWeightBarycentricError'] for r in rows),default=0),maxRelativeAreaError=max((r['relativeAreaError'] for r in rows),default=0),subdivisions=rows,limits=['Float32 intersection placement produces measured submicrometer plane error.','Normals are normalized barycentric source normals; topology subdivision does not preserve original index arrays.'])
(EVIDENCE/'source-face-provenance.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['protectedSourceTrianglesSubdivided','protectedSourceTrianglesRemoved','maxPlaneDistanceM','maxUVBarycentricError','maxWeightBarycentricError','maxRelativeAreaError']}))
