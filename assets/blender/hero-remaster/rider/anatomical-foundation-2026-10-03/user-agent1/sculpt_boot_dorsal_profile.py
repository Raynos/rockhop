"""Recover anatomical dorsal boot form from the frozen moving-fit construction."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
ap = argparse.ArgumentParser(description=__doc__)
for name in ['source','out','evidence']:
    ap.add_argument('--'+name,required=True)
ap.add_argument('--recover-receipt',action='store_true')
a = ap.parse_args(sys.argv[sys.argv.index('--')+1:]); source,out,evidence = [Path(getattr(a,n)).resolve() for n in ['source','out','evidence']]
sha = lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest(); pin = sha(source)
out.mkdir(parents=True,exist_ok=True); evidence.mkdir(parents=True,exist_ok=True)
if (out/'rider.blend').exists() and not a.recover_receipt:
    raise RuntimeError('Frozen dorsal-profile successor exists')
bpy.ops.wm.open_mainfile(filepath=str(source))
body = bpy.data.objects['Canonical anatomical body, baked adult hm08']; boots = bpy.data.objects['Complete worn boot volume on own canonical feet']
rig = bpy.data.objects['Independent anatomical foundation rig']; root = bpy.data.objects['Foundation file frame, game x0.65']
body.data.calc_loop_triangles(); bv = np.array([v.co[:] for v in body.data.vertices]); mesh = boots.data
body_faces = {side:[list(t.vertices) for t in body.data.loop_triangles
    if all(bv[i,2]<.195 and bv[i,1]*sign>.075 for i in t.vertices)] for side,sign in [('L',-1),('R',1)]}
upper_ids = {i for p in mesh.polygons if p.material_index==0 for i in p.vertices}
changes = []
for v in mesh.vertices:
    before = np.array(v.co); x,y,z = before
    if v.index not in upper_ids or not(.035<x<.215 and z>.025 and v.normal.z>.30):
        continue
    side = 'L' if y<0 else 'R'; hits = []
    for ids in body_faces[side]:
        for i,j in zip(ids,ids[1:]+ids[:1]):
            p,q = bv[i],bv[j]
            if (p[0]-x)*(q[0]-x)<=0 and abs(q[0]-p[0])>1e-10:
                t = (x-p[0])/(q[0]-p[0]); point = p+t*(q-p)
                if abs(point[1]-y)<.012:
                    hits.append(point)
    if not hits:
        continue
    guide = max(hits,key=lambda p:p[2]); target = min(z,float(guide[2]+.006))
    if z-target<.001:
        continue
    v.co.z = target
    changes.append({'nativeVertexID':v.index,'beforeNativeM':before.tolist(),'afterNativeM':list(v.co),'dorsalGuideNativeM':guide.tolist(),'loweringM':float(z-target)})
mesh.update(); assert changes,'No anatomical dorsal profile intervention'
# Structural leather panels use the existing support topology. The outsole
# stays slot1 and unchanged; upper slots0/2/3 are still actual upper surfaces.
for name,color,rough in [('Black leather toe reinforcement',(.023,.019,.016),.78),('Black leather heel and ankle counter',(.014,.012,.011),.64)]:
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color,1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = 0; b.inputs['Specular IOR Level'].default_value = .125; mesh.materials.append(m)
for p in mesh.polygons:
    if p.material_index==1:
        continue
    center = p.center
    if center.x>.17:
        p.material_index = 2
    elif center.x<.025 and center.z>.045:
        p.material_index = 3
boots['appearanceConstruction'] = 'Unaccepted10 anatomicaldorsal profile plus toe/heel counter panels;09 plantar topology/weights retained'
root['rockhopAppearanceCandidate'] = 'unaccepted appearance10 anatomical dorsal boot profile'
for o in bpy.data.objects:
    o.select_set(False)
for o in [o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render]+[root,rig]:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
if a.recover_receipt:
    # The first run saved both native/export files before numpy scalar JSON
    # serialization failed. Reconstruct and compare the saved mesh; do not
    # overwrite either source artifact merely to repair its receipt.
    expected = ([list(v.co) for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons],
        [p.material_index for p in mesh.polygons],[m.name for m in mesh.materials])
    frozen = {str(p):sha(p) for p in [out/'rider.blend',out/'rider.glb']}
    bpy.ops.wm.open_mainfile(filepath=str(out/'rider.blend'))
    mesh = bpy.data.objects['Complete worn boot volume on own canonical feet'].data
    actual = ([list(v.co) for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons],
        [p.material_index for p in mesh.polygons],[m.name for m in mesh.materials])
    assert expected==actual,'Saved dorsal mesh differs from reconstructed recipe'
    assert frozen=={p:sha(p) for p in frozen}
else:
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'rider.blend'),compress=True)
    bpy.ops.export_scene.gltf(filepath=str(out/'rider.glb'),export_format='GLB',use_selection=True,export_yup=True,
        export_animations=False,export_attributes=True,export_extras=True,export_morph=True)
controller = json.loads((source.parent/'source-normals-controller.json').read_text())
controller.update(status='UNACCEPTED10 dorsalshape test; rest/motion/art pending',candidateMasterSHA256=sha(out/'rider.blend'),
    candidateGLBSHA256=sha(out/'rider.glb'),parentAppearanceMasterSHA256=pin,parentAppearanceGLBSHA256=sha(source.parent/'rider-source-normals.glb'))
if not a.recover_receipt:
    (out/'corrective-driver.json').write_text(json.dumps(controller,indent=2)+'\n')
assert sha(source)==pin
report = {'status':'UNACCEPTED10 one fixed anatomicaldorsal intervention; qualification follows','sourceMasterSHA256':pin,
    'masterSHA256':sha(out/'rider.blend'),'quantizedGLBSHA256':sha(out/'rider.glb'),'recipeSHA256':sha(__file__),
    'changes':changes,'maximumLoweringM':max(r['loweringM'] for r in changes),'dorsalLocalGuideEaseM':.006,
    'receiptRecoveryWithoutSourceOverwrite':a.recover_receipt,
    'nativeVertices':len(mesh.vertices),'nativePolygons':len(mesh.polygons),
    'limits':['Body triangle sagittal-section dorsal guides lower the convex wedge roof only; no collider projection excuses bad art or body intersection.',
        'Source09 plantar support topology, skin weights, sole positions and real ankle openings retained. Materials are authored prototype leather panels, not learned PBR.',
        'Toe/heel/cuff silhouette, resting enclosure/body contacts, continuous motion and rootplayed art must still qualify before any promotion.']}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print('DORSAL_PROFILE_READY',len(changes),report['maximumLoweringM'],report['masterSHA256'],flush=True)
