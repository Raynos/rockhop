"""Test measured plantar flexion supports without changing the frozen rest volume."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap = argparse.ArgumentParser(description=__doc__)
for name in ['source','out','evidence']:
    ap.add_argument('--'+name,required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--')+1:])
source,out,evidence = [Path(getattr(a,n)).resolve() for n in ['source','out','evidence']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest(); source_pin = sha(source)
out.mkdir(parents=True,exist_ok=True); evidence.mkdir(parents=True,exist_ok=True)
if (out/'rider.blend').exists():
    raise RuntimeError('Frozen plantar successor exists')
bpy.ops.wm.open_mainfile(filepath=str(source))
body = bpy.data.objects['Canonical anatomical body, baked adult hm08']; rig = bpy.data.objects['Independent anatomical foundation rig']
boots = bpy.data.objects['Complete worn boot volume on own canonical feet']; root = bpy.data.objects['Foundation file frame, game x0.65']
body.data.calc_loop_triangles(); boots.data.calc_loop_triangles()
body_v = np.array([v.co[:] for v in body.data.vertices]); body_f = np.array([t.vertices[:] for t in body.data.loop_triangles])
body_tree = BVHTree.FromPolygons([Vector(p) for p in body_v],body_f.tolist(),all_triangles=True)
old_v = [v.co.copy() for v in boots.data.vertices]; old_f = [list(t.vertices) for t in boots.data.loop_triangles]
old_tree = BVHTree.FromPolygons(old_v,old_f,all_triangles=True)
old_triangles = np.asarray([p[:] for p in old_v],dtype=np.float64)[old_f]
def exact_surface_distance(p):
    # Native BVH is float32 and near-degenerate original slivers can overstate
    # proximity residuals. Verify every source triangle in double precision.
    aa = old_triangles[:,0]; e0 = old_triangles[:,1]-aa; e1 = old_triangles[:,2]-aa
    normals = np.cross(e0,e1); nn = np.einsum('ij,ij->i',normals,normals)
    signed = np.einsum('ij,ij->i',p-aa,normals)/np.maximum(nn,1e-30)
    projected = p-normals*signed[:,None]; q = projected-aa
    d00 = np.einsum('ij,ij->i',e0,e0); d01 = np.einsum('ij,ij->i',e0,e1); d11 = np.einsum('ij,ij->i',e1,e1)
    d20 = np.einsum('ij,ij->i',q,e0); d21 = np.einsum('ij,ij->i',q,e1)
    denominator = d00*d11-d01*d01
    u = (d11*d20-d01*d21)/np.maximum(denominator,1e-30)
    v = (d00*d21-d01*d20)/np.maximum(denominator,1e-30)
    inside = (denominator>1e-25)&(u>=-1e-10)&(v>=-1e-10)&(u+v<=1+1e-10)
    squared = np.where(inside,np.einsum('ij,ij->i',p-projected,p-projected),np.inf)
    for i,j in [(0,1),(1,2),(2,0)]:
        start = old_triangles[:,i]; edge = old_triangles[:,j]-start
        t = np.clip(np.einsum('ij,ij->i',p-start,edge)/np.maximum(np.einsum('ij,ij->i',edge,edge),1e-30),0,1)
        delta = p-(start+edge*t[:,None]); squared = np.minimum(squared,np.einsum('ij,ij->i',delta,delta))
    return float(np.sqrt(squared.min()))
body_weights = [{body.vertex_groups[g.group].name:float(g.weight) for g in v.groups
    if g.weight>0 and body.vertex_groups[g.group].name in rig.data.bones} for v in body.data.vertices]
original = {'vertices':len(boots.data.vertices),'polygons':len(boots.data.polygons),'bounds':[[min(p[i] for p in old_v),max(p[i] for p in old_v)] for i in range(3)]}
bm = bmesh.new(); bm.from_mesh(boots.data)
planes = [.08,.11,.14,.17,.20]
for x in planes:
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,
        plane_co=(x,0,0),plane_no=(1,0,0),clear_inner=False,clear_outer=False)
bm.to_mesh(boots.data); bm.free(); boots.data.update()
maximum_surface_residual = 0.; maximum_bvh_residual = 0.; removed_dust = 0.
for v in boots.data.vertices:
    nearest,normal,face,distance = body_tree.find_nearest(v.co); ids = body_f[face]; points = body_v[ids]
    matrix = np.column_stack([points[1]-points[0],points[2]-points[0]])
    yz = np.linalg.lstsq(matrix,np.array(nearest)-points[0],rcond=None)[0]
    factors = np.clip([1-sum(yz),yz[0],yz[1]],0,1); factors /= sum(factors); weights = {}
    side = 'L' if v.co.y<0 else 'R'; opposite = 'R' if side=='L' else 'L'
    for i,factor in zip(ids,factors):
        for name,value in body_weights[i].items():
            weights[name] = weights.get(name,0)+factor*value
    removed_dust = max(removed_dust,sum(value for name,value in weights.items() if name.endswith('.'+opposite)))
    weights = sorted([(name,value) for name,value in weights.items() if not name.endswith('.'+opposite)],key=lambda r:-r[1])[:4]
    total = sum(value for name,value in weights)
    for g in list(v.groups):
        boots.vertex_groups[g.group].remove([v.index])
    for name,value in weights:
        boots.vertex_groups[name].add([v.index],float(value/total),'REPLACE')
    maximum_bvh_residual = max(maximum_bvh_residual,old_tree.find_nearest(v.co)[3])
    maximum_surface_residual = max(maximum_surface_residual,exact_surface_distance(np.asarray(v.co,dtype=np.float64)))
assert maximum_surface_residual<2e-6,maximum_surface_residual
assert len(boots.data.vertices)<1500,'Fixed lightweight construction cap, no density sweep'
root['rockhopAppearanceCandidate'] = 'unaccepted appearance09 measured plantar flexion support topology'
boots['appearanceConstruction'] = '09 fixedfive plantar flexion support planes; same08 restvolume, body-derived ownside top4 weights'
for o in bpy.data.objects:
    o.select_set(False)
for o in [o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render]+[root,rig]:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out/'rider.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(out/'rider.glb'),export_format='GLB',use_selection=True,export_yup=True,
    export_animations=False,export_attributes=True,export_extras=True,export_morph=True)
controller = json.loads((source.parent/'source-normals-controller.json').read_text())
controller.update(status='UNACCEPTED09 plantar-flexion support test; movingwear/response pending',
    candidateMasterSHA256=sha(out/'rider.blend'),candidateGLBSHA256=sha(out/'rider.glb'),
    parentAppearanceMasterSHA256=source_pin,parentAppearanceGLBSHA256=sha(source.parent/'rider-source-normals.glb'))
(out/'corrective-driver.json').write_text(json.dumps(controller,indent=2)+'\n')
assert sha(source)==source_pin
report = {'status':'UNACCEPTED09 targeted plantar support construction; no motion or response acceptance','sourceMasterSHA256':source_pin,
    'masterSHA256':sha(out/'rider.blend'),'quantizedGLBSHA256':sha(out/'rider.glb'),'recipeSHA256':sha(__file__),
    'original':original,'nativeVertices':len(boots.data.vertices),'nativePolygons':len(boots.data.polygons),
    'fixedNativeXSupportPlanesM':planes,'maximumDistanceToFrozen08SurfaceM':maximum_surface_residual,
    'float32BVHMaximumResidualM':maximum_bvh_residual,'surfaceVerifier':'All674source triangles, float64 face-plane/barycentric and segment minima',
    'maximumRemovedOppositeSideWeight':removed_dust,'skin':'Closest actual native-body triangle barycentric ownside top4 normalized',
    'limits':['One prescribed topology intervention at measured plantar forefoot flexion; no rest gap, material recolor or global density/weight solver sweep.',
        'Restsurface residual is unsigned proximity, not whole-volume equivalence or movement-safe proof; wholepart contact and continuous motion qualification follow.',
        'No native cloth or runtime collision projection added. Actual consumed lightweight corrections and mobile cost still required.',
        'Protected body/head/51bind and previous source08 controls remain; root alone judges played moving footwear.']}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print('PLANTAR_SUPPORT_READY',report['masterSHA256'],report['nativeVertices'],report['nativePolygons'],maximum_surface_residual,flush=True)
