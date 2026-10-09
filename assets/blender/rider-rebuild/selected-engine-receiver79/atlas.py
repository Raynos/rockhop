"""Actual packed selected receiver atlas; exact float32 interior-overlap test."""
from collections import defaultdict
import math


def _integers(uv):
    pairs = [[float(value).as_integer_ratio() for value in row] for row in uv]
    denominator = max(d for row in pairs for _,d in row)
    return [[n*(denominator//d) for n,d in row] for row in pairs]


def _overlap(a,b):
    # Exact separating axes of two convex triangles. Equality is shared
    # boundary only; it has no positive-area interior overlap.
    for tri in (a,b):
        for p,q in zip(tri,tri[1:]+tri[:1]):
            axis = (p[1]-q[1],q[0]-p[0])
            aa = [v[0]*axis[0]+v[1]*axis[1] for v in a]
            bb = [v[0]*axis[0]+v[1]*axis[1] for v in b]
            if min(max(aa),max(bb)) <= max(min(aa),min(bb)): return False
    return True


def verify(uv,triangles,np):
    uv = np.asarray(uv,dtype=np.float32)
    assert np.isfinite(uv).all() and np.all((uv>=0)&(uv<=1))
    integer = _integers(uv); bins = defaultdict(list); checked = set()
    for fi,indices in enumerate(triangles):
        tri = [integer[int(i)] for i in indices]
        a,b,c = tri
        assert (b[0]-a[0])*(c[1]-a[1]) != (b[1]-a[1])*(c[0]-a[0]), ('Zero-area atlas triangle',fi)
        actual = uv[indices]
        lo = np.minimum(63,np.floor(actual.min(0)*64).astype(int))
        hi = np.minimum(63,np.floor(actual.max(0)*64).astype(int))
        for x in range(int(lo[0]),int(hi[0])+1):
            for y in range(int(lo[1]),int(hi[1])+1):
                for other in bins[x,y]:
                    pair = (other,fi)
                    if pair in checked: continue
                    checked.add(pair)
                    opposite = [integer[int(i)] for i in triangles[other]]
                    assert not _overlap(tri,opposite), ('Positive-area atlas overlap',other,fi)
                bins[x,y].append(fi)
    return {'float32AtlasInsideUnitSquare':True,'zeroAreaTriangles':0,
            'positiveAreaInteriorOverlapPairs':0,'triangles':len(triangles),
            'candidatePairsExamined':len(checked),'method':'Exact integer separating axes of saved float32 UV triangles'}


def unwrap(obj,bpy,np):
    """Use actual Blender packing; retain immutable sampling UV as another layer."""
    old_layer = obj.data.uv_layers.active
    assert old_layer is not None
    old = np.empty((len(obj.data.loops),2),np.float32)
    old_layer.data.foreach_get('uv',old.ravel())
    old_name = old_layer.name
    bpy.ops.object.select_all(action='DESELECT');obj.hide_set(False);obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    layer=obj.data.uv_layers.new(name='SelectedProductionAtlas')
    obj.data.uv_layers.active=layer
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    assert bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,
        correct_aspect=True,scale_to_bounds=True)=={'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    for uv_layer in obj.data.uv_layers: uv_layer.active_render=uv_layer==layer
    copied=np.empty_like(old);obj.data.uv_layers[old_name].data.foreach_get('uv',copied.ravel())
    assert np.array_equal(old,copied),'Original selected sampling UV changed'
    obj.data.calc_loop_triangles()
    loops=np.empty((len(obj.data.loop_triangles),3),np.int32)
    obj.data.loop_triangles.foreach_get('loops',loops.ravel())
    atlas=np.empty_like(old);layer.data.foreach_get('uv',atlas.ravel())
    return atlas,loops,verify(atlas,loops,np)


def interior_pixels(uv,triangles,size,np):
    """Texel centers strictly inside actual atlas triangles, without padding."""
    mask=np.zeros((size,size),bool);without_centers=0
    for indices in triangles:
        tri=np.asarray(uv[indices],np.float64)*size
        lo=np.maximum(0,np.ceil(tri.min(0)-.5).astype(int))
        hi=np.minimum(size-1,np.floor(tri.max(0)-.5).astype(int))
        if np.any(lo>hi):without_centers+=1;continue
        y,x=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        points=np.stack([x+.5,y+.5],axis=-1)
        sides=[]
        for a,b in zip(tri,np.roll(tri,-1,axis=0)):
            q=points-a;edge=b-a;sides.append(edge[0]*q[:,:,1]-edge[1]*q[:,:,0])
        sides=np.asarray(sides)
        inside=np.all(sides>0,axis=0)|np.all(sides<0,axis=0)
        without_centers+=not bool(inside.any())
        mask[lo[1]:hi[1]+1,lo[0]:hi[0]+1]|=inside
    assert mask.any(),'Atlas has no occupied interior texel centers'
    return mask,{'strictInteriorTexelCenters':int(mask.sum()),'trianglesWithoutInteriorTexelCenter':int(without_centers),
                 'sampleSpace':'Actual atlas texel centers; shared triangle edges and padding excluded'}
