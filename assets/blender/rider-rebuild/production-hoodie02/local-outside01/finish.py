"""ONE ordinary local OUTSIDE finishing pass; source-only until parent lease.

blender -b -t 2 --python-exit-code 1 --python finish.py -- controls.json FRESH_OUT
Preserves actual selected topology, UV/PBR/fields and all loose/outside points.
Saves native before same-camera views. Does not render, import dense or bake.
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[5]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def frozen_surface(obj):
    state = {'faces': [list(f.vertices) for f in obj.data.polygons],
             'uv': {u.name: [list(v.uv) for v in u.data] for u in obj.data.uv_layers},
             'materials': [m.name if m else None for m in obj.data.materials],
             'faceMaterials': [f.material_index for f in obj.data.polygons],
             'groups': [g.name for g in obj.vertex_groups],
             'weights': [[[g.group,g.weight] for g in v.groups] for v in obj.data.vertices]}
    return hashlib.sha256(json.dumps(state, separators=(',', ':')).encode()).hexdigest()


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 2
    cp, out = (Path(x).resolve() for x in args)
    c = json.loads(cp.read_text())
    assert out.is_relative_to(ROOT/c['outputRoot']) and not out.exists()
    for key,pin in c['pins'].items():
        assert sha(ROOT/pin['path']) == pin['sha256'], ('Changed intake',key)
    h = runpy.run_path(str(ROOT/c['pins']['baseAuthor']['path']))
    spec = json.loads((ROOT/c['pins']['frozenInputs']['path']).read_text())
    receipt = json.loads((ROOT/c['pins']['authorReceipt']['path']).read_text())
    spec['targetHemZ'] = receipt['inputs']['targetHemZ']
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/c['pins']['authoredNative']['path']))
    body,rig,obj = (bpy.data.objects[n] for n in ('RiderBody','RiderSkeleton','RiderHoodie'))
    assert len(body.data.vertices) == 10582 and len(rig.data.bones) == 75
    assert h['hoodie_geometry'](obj) == receipt['targetGeometrySHA256']
    before_body = h['signature'](body,rig)
    assert before_body == receipt['bodyAnd75RigSignature']
    before_surface = frozen_surface(obj)
    positions = [v.co.copy() for v in obj.data.vertices]
    assert obj.matrix_world == body.matrix_world == Matrix.Identity(4)
    targets = h['target_arms'](rig)
    collar = h['fit_point'](Vector(spec['protectedPorts']['sourceCollarCenterM']),spec,targets)[0]

    def protected(p):
        controls = spec['protectedPorts']
        if abs(p.z-spec['targetHemZ']) < controls['hemSlabHalfWidthM']: return True
        if sum(((p[i]-collar[i])/controls['collarRadiiM'][i])**2 for i in range(3)) < 1: return True
        for _,elbow,wrist in targets.values():
            axis = (wrist-elbow).normalized()
            axial = (p-wrist).dot(axis)
            if abs(axial)<controls['cuffSlabHalfWidthM'] and (p-wrist-axis*axial).length<controls['cuffRadiusM']: return True
        return False

    def within_underarm(p):
        return any(all(abs(p[i]-box['center'][i])<=box['halfSize'][i] for i in range(3))
                   for box in c['underarmBoxes'].values())

    patch = obj.data.attributes[c['patchAttribute']]
    assert patch.domain == 'FACE'
    patch_faces = {f.index for f in obj.data.polygons if patch.data[f.index].value in (1,2)}
    assert len(patch_faces) == sum(p['authoredQuads'] for p in receipt['underarmPatches'])
    bm = bmesh.new();bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
    scope_faces = set(patch_faces)
    rings = []
    for _ in range(c['adjacentFaceRings']):
        next_faces = {neighbor.index for fi in scope_faces for v in bm.faces[fi].verts
                      for neighbor in v.link_faces if within_underarm(neighbor.calc_center_median())}-scope_faces
        scope_faces.update(next_faces);rings.append(sorted(next_faces))
    patch_vertices = {v.index for fi in patch_faces for v in bm.faces[fi].verts}
    scoped = {v.index for fi in scope_faces for v in bm.faces[fi].verts
              if within_underarm(v.co) and not protected(v.co)}
    assert patch_vertices <= scoped, 'Authored patch touches protected/outside finishing domain'
    local_open = [e for e in bm.edges if e.is_boundary and any(v.index in scoped for v in e.verts)
                  and not all(protected(v.co) for v in e.verts)]
    body.data.calc_loop_triangles()
    tree = BVHTree.FromPolygons([v.co.copy() for v in body.data.vertices],
                               [tuple(t.vertices) for t in body.data.loop_triangles],all_triangles=True)

    def distance(p):
        point,normal,index,d = tree.find_nearest(p)
        assert point is not None
        return (p-point).dot(normal),d

    before_distances = {i:distance(positions[i]) for i in sorted(scoped)}
    diagnosis = {'accepted':False,'stage':'LOCAL_INTAKE_BEFORE_ANY_EDIT',
                 'nativeInput':c['pins']['authoredNative'],'patchFaces':sorted(patch_faces),
                 'patchVertices':sorted(patch_vertices),'adjacentFaceRings':rings,
                 'scopedVertices':sorted(scoped),'scopeBounds':c['underarmBoxes'],
                 'unexpectedLocalBoundaryEdges':[[v.index for v in e.verts] for e in local_open],
                 'nearestBodyInsideVertices':sum(s<0 for s,d in before_distances.values()),
                 'nearestBodyBelowClothClearanceVertices':sum(s<c['clothClearanceM'] for s,d in before_distances.values()),
                 'classification':'LOCAL_OPEN_BOUNDARY_REQUIRES_ARTIST' if local_open else 'LOCAL_SURFACE_CONTINUOUS_CLIPPING_POSSIBLE',
                 'limits':['Nearest-normal signs diagnose vertex clipping, not closed-surface wearing acceptance.','No local topology replacement or fill operator is authorized.']}
    out.mkdir(parents=True)
    (out/'diagnosis.json').write_text(json.dumps(diagnosis,indent=2)+'\n')
    bm.free()
    assert not local_open, 'Unexpected local open boundary: stop; exact artist package required'
    # Use a disposable native-rest mesh for the ordinary modifier. The source
    # armature/pose/fields are never applied or cleared on the actual garment.
    proxy = obj.copy();proxy.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(proxy)
    proxy.name = 'LocalOutsideHoodieFinishingAid'
    proxy.parent = None;proxy.matrix_world = Matrix.Identity(4);proxy.modifiers.clear()
    body_target = bpy.data.objects.new('CompleteNativeRestBodyFinishingTarget',body.data.copy())
    bpy.context.scene.collection.objects.link(body_target)
    body_target.hide_render = True
    group = proxy.vertex_groups.new(name='LocalAuthoredAxillaOutsideFinish')
    group.add(sorted(scoped),1.,'REPLACE')
    modifier = proxy.modifiers.new('OneLocalOutsideFinish12mm','SHRINKWRAP')
    modifier.target = body_target
    modifier.wrap_method = c['wrapMethod'];modifier.wrap_mode = c['snapMode']
    assert modifier.wrap_mode == 'OUTSIDE'
    modifier.offset = c['clothClearanceM'];modifier.vertex_group = group.name
    h['active'](proxy)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    changed = []
    already_loose = [i for i,(s,d) in before_distances.items() if s>0 and d>=c['clothClearanceM']+1e-5]
    for i,v in enumerate(proxy.data.vertices):
        delta = (v.co-positions[i]).length
        if delta>1e-7:
            assert i in scoped and i not in already_loose, ('Outside aid altered a protected/loose point',i)
            assert delta<=c['maxDisplacementM'], ('Local edit exceeds bounded scope',i,delta)
            changed.append({'vertex':i,'before':list(positions[i]),'after':list(v.co),'displacementM':delta})
            obj.data.vertices[i].co = v.co
    assert changed, 'No concrete local fit correction; no retry campaign'
    obj.data.update()
    for temporary in (proxy,body_target): bpy.data.objects.remove(temporary,do_unlink=True)
    after_distances = {i:distance(obj.data.vertices[i].co) for i in sorted(scoped)}
    assert frozen_surface(obj) == before_surface
    assert h['signature'](body,rig) == before_body
    assert not body.hide_render and not body.hide_viewport and not body.hide_get()
    obj['unaccepted'] = True
    obj['localOutsideFinishRecipeSHA256'] = sha(__file__)
    obj['localOutsideFinishOriginalNativeSHA256'] = c['pins']['authoredNative']['sha256']
    obj['changedTopologyNeedsDenseBake'] = True
    native = out/'local-outside-hoodie.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    result = {'accepted':False,'stage':'ONE_LOCAL_OUTSIDE_PASS_SAVED_BEFORE_MATCHED_VIEWS',
              'native':{'path':str(native),'sha256':sha(native)},'recipeSHA256':sha(__file__),
              'controlsSHA256':sha(cp),'originalAuthorReceiptSHA256':c['pins']['authorReceipt']['sha256'],
              'originalNativeSHA256':c['pins']['authoredNative']['sha256'],
              'targetGeometrySHA256':h['hoodie_geometry'](obj),'frozenTopologyUVPBRFieldsSHA256':before_surface,
              'bodyAnd75RigSignature':before_body,'bodyAnd75RigUnchanged':True,'completeBodyVisible':True,
              'changedVertices':changed,'scopedVertices':sorted(scoped),'alreadyLooseVerticesUnchanged':already_loose,
              'clothClearanceM':c['clothClearanceM'],'mode':'NEAREST_SURFACEPOINT/OUTSIDE',
              'nearestBodyInsideVerticesAfter':sum(s<-1e-5 for s,d in after_distances.values()),
              'nearestBodyBelowClothClearanceVerticesAfter':sum(s<c['clothClearanceM']-1e-5 for s,d in after_distances.values()),
              'limits':c['limits']+['Vertex clearance does not accept face enclosure, silhouette, or movement.',
                                  'Material prep needs an explicit NEW native+receipt intake; frozen original receipt remains untouched.']}
    (out/'finish.json').write_text(json.dumps(result,indent=2)+'\n')
    print('ONE_LOCAL_OUTSIDE_NATIVE_SAVED',str(native),'changed',len(changed),flush=True)


if __name__ == '__main__': main()
