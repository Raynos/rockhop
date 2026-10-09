"""Small numerical source fixtures only: no native, Blender, source47 or bake."""
import json
import numpy as np
import patches
import atlas

checks=[]
# A UV seam duplicates a source position; include only one incident overlap
# ring, not the next ring or the opposite sleeve.
points=np.asarray([[2,0,0],[2,1,0],[1,0,0],[1,0,0],[.5,1,0],[.5,0,0],
                   [.25,1,0],[.25,0,0],[-2,0,0],[-2,1,0],[-1,0,0]],float)
faces=np.asarray([[0,1,2],[3,4,5],[4,6,7],[8,9,10]])
ids,report=patches.source_patch(points,faces,'L',lambda z:np.ones_like(z)*1.5,np)
assert ids.tolist()==[0,1] and report['retainedSideOverlapTriangles']==1
ids,_=patches.source_patch(points,faces,'R',lambda z:np.ones_like(z)*1.5,np)
assert ids.tolist()==[3]
checks.append('literal source triangle selection bridges UV seam positions with exactly one overlap ring')

class Cylinder:
    """Analytic hollow sleeve used only to exercise cage arithmetic."""
    def ray_cast(self,origin,direction,maximum):
        o,d=np.asarray(origin),np.asarray(direction);hits=[]
        aa=float(d[:2]@d[:2]);bb=2*float(o[:2]@d[:2])
        if aa>0:
            for radius,sign in ((1.,1.),(.8,-1.)):
                cc=float(o[:2]@o[:2])-radius*radius;disc=bb*bb-4*aa*cc
                if disc<0:continue
                for t in ((-bb-np.sqrt(disc))/(2*aa),(-bb+np.sqrt(disc))/(2*aa)):
                    p=o+d*t
                    if 0<t<=maximum and -1<=p[2]<=1:
                        n=np.r_[p[:2]/radius*sign,0.];hits.append((t,p,n))
        if d[2]!=0:
            t=(1-o[2])/d[2];p=o+d*t
            if 0<t<=maximum and .8<np.linalg.norm(p[:2])<1:hits.append((t,p,np.asarray([0,0,1.])))
        if not hits:return None,None,None,None
        t,p,n=min(hits,key=lambda x:x[0]);return p,n,0,t

angles=np.arange(16)*2*np.pi/16
ring=np.stack([np.cos(angles),np.sin(angles),np.zeros(16)],axis=1)
source=np.concatenate([ring+[0,0,-1],ring+[0,0,1],ring*.8+[0,0,-1],ring*.8+[0,0,1]])
faces=np.asarray([[i,(i+1)%16,16+i] for i in range(16)]+[[16+i,(i+1)%16,16+(i+1)%16] for i in range(16)])
rest=[['DEF-upper_arm.L',None,[0,0,-1]],['DEF-forearm.L',None,[0,0,0]],['DEF-hand.L',None,[0,0,1]]]
for wall,radius in (('outer',1.02),('inner',.82)):
    target=np.concatenate([ring*radius+[0,0,-.3],ring*radius+[0,0,.3]])
    cage,row=patches.cage(target,faces,source,faces,Cylinder(),rest,'L:'+wall,np.asarray,np)
    assert cage.shape==target.shape and cage.dtype==np.float32
    assert row['vertexAndFaceCenterRays']==len(target)+len(faces)
    assert row['maximumObservedHitDistanceM']<row['maximumBakeRayDistanceLocalM']
    assert row['minimumCageTriangleAreaM2']>0
    radii=np.linalg.norm(cage[:,:2],axis=1)
    assert np.all(radii>1.02) if wall=='outer' else np.all(radii<.8)
checks.append('shared-vertex exterior/cavity cages start on correct side and use finite facing first hits')
# Cuff receiver has an annulus; its cage must retain the same shared IDs/faces.
target=np.concatenate([ring*.84+[0,0,.98],ring*.98+[0,0,.98]])
cage,row=patches.cage(target,faces,source,faces,Cylinder(),rest,'L:rim',np.asarray,np)
assert np.all(cage[:,2]>1) and row['minimumCageTriangleAreaM2']>0
checks.append('matching-topology cuff cage casts back from beyond the actual source bound')
class Miss:
    def ray_cast(self,*_):return None,None,None,None
class Back:
    def ray_cast(self,*_):return [1,0,0],[1,0,0],0,1
for tree in (Miss(),Back()):
    try:patches.first_hit(tree,np.zeros(3),np.asarray([1.,0,0]),2,np.asarray,np)
    except AssertionError:pass
    else:raise AssertionError('Miss or back-facing ray admitted')
checks.append('source miss and back-facing first hit refuse; no nearest fallback')
# Retained UV can overlap the rebuilt atlas because it uses other materials.
uv=np.asarray([[0,0],[1,0],[0,1],[0,0],[1,0],[0,1]],np.float32)
assert atlas.verify(uv[[3,4,5]],np.asarray([[0,1,2]]),np)['triangles']==1
try:atlas.verify(uv,np.asarray([[0,1,2],[3,4,5]]),np)
except AssertionError:pass
else:raise AssertionError('Actual rebuilt atlas overlap admitted')
checks.append('overlap qualification is scoped to baked polygons and still rejects true atlas overlap')
# Witness behavior is tested against tiny objects; it is not a native receipt.
from types import SimpleNamespace as NS
from bake import retained_witness
class Data(list):
    def __init__(self,values):self.values=np.asarray(values,np.float32)
    def __len__(self):return len(self.values)
    def foreach_get(self,field,out):assert field=='uv';out[:]=self.values.ravel()
class Layers(list):
    @property
    def active(self):return self[0]
first,second,baked=[NS(name=name) for name in ('original1','original2','baked')]
layer=NS(name='UVMap',data=Data([[0,0],[1,0],[0,1],[0,0],[1,0],[0,1]]))
polys=[NS(index=i,loop_start=i*3,loop_total=3,material_index=i) for i in range(2)]
obj=NS(data=NS(materials=[first,second],polygons=polys,uv_layers=Layers([layer])))
donor=NS(data=NS(materials=[first,second]));retained=np.asarray([True,False])
before=retained_witness(obj,donor,retained,np)
obj.data.materials.append(baked);polys[1].material_index=2;layer.data.values[3:]*=.5
assert retained_witness(obj,donor,retained,np)==before
layer.data.values[0,0]=.1
assert retained_witness(obj,donor,retained,np)!=before
obj.data.materials[0]=baked
try:retained_witness(obj,donor,retained,np)
except AssertionError:pass
else:raise AssertionError('Replaced selected retained material admitted')
checks.append('healthy UV/material witness tolerates rebuilt-only bake and detects retained changes')
print(json.dumps({'status':'SMALL_NUMERICAL_SOURCE_FIXTURES_ONLY','count':len(checks),'checks':checks,
                  'actualSourceLoaded':False,'nativeExecuted':False,'bakeExecuted':False}))
