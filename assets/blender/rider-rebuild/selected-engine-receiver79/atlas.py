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


def unwrap(obj,walls,bpy,np):
    """Pack rebuilt roles, preserving retained UV and role-boundary tangents.

    Separate exterior/cavity/cuff islands ensure each local receiver bake has
    the same tangent discontinuities as the final mesh. Retained materials
    keep their original coordinates in the existing UV layer.
    """
    layer=obj.data.uv_layers.active;assert layer is not None
    before=np.empty((len(obj.data.loops),2),np.float32)
    layer.data.foreach_get('uv',before.ravel())
    bpy.ops.object.select_all(action='DESELECT');obj.hide_set(False);obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.context.tool_settings.mesh_select_mode=(False,False,True)
    sync=bpy.context.tool_settings.use_uv_select_sync
    bpy.context.tool_settings.use_uv_select_sync=True
    def select(faces):
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.data.polygons.foreach_set('select',np.asarray(faces,bool))
        bpy.ops.object.mode_set(mode='EDIT')
    for index,key in enumerate(sorted(set(walls)-{'retained'})):
        selected=walls==key;select(selected)
        assert bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,
            correct_aspect=True,scale_to_bounds=True)=={'FINISHED'}
        bpy.ops.object.mode_set(mode='OBJECT')
        uv=np.empty_like(before);layer.data.foreach_get('uv',uv.ravel())
        loops=np.concatenate([np.arange(p.loop_start,p.loop_start+p.loop_total)
                              for p in obj.data.polygons if selected[p.index]])
        # Keep separately unwrapped roles disjoint while the final pack finds
        # islands; otherwise coincident UVs could reconnect a role boundary.
        uv[loops,0]+=2*index;layer.data.foreach_set('uv',uv.ravel())
    rebuilt=walls!='retained';select(rebuilt)
    assert bpy.ops.uv.pack_islands(rotate=True,margin=.012)=={'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.tool_settings.use_uv_select_sync=sync
    uv=np.empty_like(before);layer.data.foreach_get('uv',uv.ravel())
    retained_loops=np.concatenate([np.arange(p.loop_start,p.loop_start+p.loop_total)
                                  for p in obj.data.polygons if not rebuilt[p.index]])
    assert np.array_equal(before[retained_loops],uv[retained_loops]),'Retained selected UV changed'
    obj.data.calc_loop_triangles()
    loops=np.asarray([t.loops for t in obj.data.loop_triangles],np.int32)
    indices=np.flatnonzero([rebuilt[t.polygon_index] for t in obj.data.loop_triangles])
    report=verify(uv[loops[indices]].reshape(-1,2),np.arange(len(indices)*3).reshape(-1,3),np)
    report.update(scope='Rebuilt polygons only; retained selected UV/PBR preserved',uvLayer=layer.name)
    return uv,loops,indices,report


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
