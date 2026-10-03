"""Locate frozen footwear failures and expose native skin/edge ancestry for corrections."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source', required=True); ap.add_argument('--motion', required=True); ap.add_argument('--out', required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--')+1:]); source, motion, out = [Path(getattr(a,n)).resolve() for n in ['source','motion','out']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins = {str(p):sha(p) for p in [source,motion]}; d = json.loads(motion.read_text())
assert pins[str(source)] == d['pins'][str(source)]
out.mkdir(parents=True,exist_ok=True)
if (out/'audit.json').exists():
    raise RuntimeError('Frozen footwear skin audit exists')
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']; body = bpy.data.objects['Canonical anatomical body, baked adult hm08']
boot = bpy.data.objects['Complete worn boot volume on own canonical feet']
def weights(o):
    return [{o.vertex_groups[g.group].name:float(g.weight) for g in v.groups
        if g.weight>0 and o.vertex_groups[g.group].name in rig.data.bones} for v in o.data.vertices]
bw,sw = weights(body),weights(boot)
boot.data.calc_loop_triangles(); body.data.calc_loop_triangles()
triangles = [{'nativeTriangleID':t.index,'nativePolygonID':t.polygon_index,'nativeVertexIDs':list(t.vertices),
    'materialSlot':boot.data.polygons[t.polygon_index].material_index} for t in boot.data.loop_triangles]
body_triangles = [list(t.vertices) for t in body.data.loop_triangles]
edges = []
for e in boot.data.edges:
    i,j = e.vertices; names = set(sw[i])|set(sw[j])
    edges.append({'nativeEdgeID':e.index,'nativeVertexIDs':[i,j],
        'restLengthM':float((boot.data.vertices[i].co-boot.data.vertices[j].co).length),
        'skinWeightL1Variation':sum(abs(sw[i].get(n,0)-sw[j].get(n,0)) for n in names)})
def evaluated(o):
    obj = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = obj.to_mesh(); mesh.calc_loop_triangles()
    v = np.array([obj.matrix_world@p.co for p in mesh.vertices]); f = [list(t.vertices) for t in mesh.loop_triangles]
    polygons = [t.polygon_index for t in mesh.loop_triangles]
    slots = [mesh.polygons[t.polygon_index].material_index for t in mesh.loop_triangles]
    obj.to_mesh_clear(); return v,f,polygons,slots
def aggregate(rows,ids):
    result = {}
    for i in ids:
        for name,w in rows[i].items():
            result[name] = result.get(name,0)+w/len(ids)
    return dict(sorted(result.items(),key=lambda r:-r[1]))
failures = []
for index in [564,612]:
    for pb in rig.pose.bones:
        pb.location = (0,0,0); pb.rotation_quaternion = (1,0,0,0); pb.scale = (1,1,1)
    phase = (index-528)/96*2*math.pi
    for side in ['L','R']:
        for name,angle in [('foot.'+side,math.sin(phase)*math.radians(20)),('ball.'+side,math.sin(phase*2)*math.radians(15))]:
            axis = rig.data.bones[name].matrix_local.to_3x3().inverted()@Vector((0,1,0))
            rig.pose.bones[name].rotation_quaternion = Quaternion(axis.normalized(),angle)
    bpy.context.view_layer.update(); body_v,body_f,body_polys,body_slots = evaluated(body)
    boot_v,boot_f,boot_polys,boot_slots = evaluated(boot)
    body_tree = BVHTree.FromPolygons([Vector(v) for v in body_v],body_f,all_triangles=True)
    parts = []
    for slot,name in [(0,'upper'),(1,'outsole')]:
        selected = [{'evaluatedTriangleID':i,'nativePolygonID':boot_polys[i],'nativeVertexIDs':ids}
            for i,ids in enumerate(boot_f) if boot_slots[i]==slot]
        tree = BVHTree.FromPolygons([Vector(v) for v in boot_v],[t['nativeVertexIDs'] for t in selected],all_triangles=True)
        pairs = tree.overlap(body_tree); expected = d['frames'][index]['versions']['new']['parts'][slot]['bodyTriangleContactPairs']
        assert len(pairs)==expected,(index,name,len(pairs),expected)
        witnesses = []
        for part_id,body_id in pairs:
            t = selected[part_id]; ids = t['nativeVertexIDs']; body_ids = body_f[body_id]
            witnesses.append({'bootEvaluatedTriangleID':t['evaluatedTriangleID'],'bootNativePolygonID':t['nativePolygonID'],
                'bootNativeVertexIDs':ids,'bodyEvaluatedTriangleID':body_id,'bodyNativePolygonID':body_polys[body_id],'bodyNativeVertexIDs':body_ids,
                'bootRestCentroidNativeM':np.mean([boot.data.vertices[i].co[:] for i in ids],0).tolist(),
                'bodyRestCentroidNativeM':np.mean([body.data.vertices[i].co[:] for i in body_ids],0).tolist(),
                'bootWorldCentroidM':boot_v[ids].mean(0).tolist(),'bodyWorldCentroidM':body_v[body_ids].mean(0).tolist(),
                'meanBootWeights':aggregate(sw,ids),'meanBodyWeights':aggregate(bw,body_ids)})
        unique = sorted({i for t,b in pairs for i in selected[t]['nativeVertexIDs']})
        unique_body = sorted({i for t,b in pairs for i in body_f[b]})
        parts.append({'part':name,'bodyTriangleContactPairs':len(pairs),'uniqueBootVertexIDs':unique,'uniqueBodyVertexIDs':unique_body,
            'meanContactBootWeights':aggregate(sw,unique) if unique else {},'meanContactBodyWeights':aggregate(bw,unique_body) if unique_body else {},'witnesses':witnesses})
    failures.append({'measurementIndex':index,'timeS':d['frames'][index]['timeS'],'ankleDegrees':math.sin(phase)*20,
        'toeDegrees':math.sin(phase*2)*15,'parts':parts})
assert pins == {p:sha(p) for p in pins}
report = {'status':'UNACCEPTED source08 native failure/skin ancestry; no repair or collision response added','pins':pins,
    'recipeSHA256':sha(__file__),'rootTranslationNativeM':list(boot.matrix_world.translation),
    'vertices':[{'nativeVertexID':v.index,'restNativeM':list(v.co),'skinWeights':sw[v.index]} for v in boot.data.vertices],
    'nativeRestTriangles':triangles,'edges':edges,'highestWeightVariationEdges':sorted(edges,key=lambda r:-r['skinWeightL1Variation'])[:12],
    'failures':failures,'limits':['Matched fullbody triangle-pair counts reproduce source564/612; centroid witnesses locate contacts but do not measure signed penetration.',
        'Witness IDs use evaluated triangle splits plus stable native polygon/vertex ancestry; rest ngon/quad diagonals are not assumed identical after deformation.',
        'Rest edges/weights are source facts, not stiffness settings consumed by a runtime solver. No unused descriptor qualifies actual response.',
        'Footwear remains unaccepted. Primary fitted skinning and bounded collision-aware corrections require held-out motion, all-angle review and mobile cost.']}
(out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('FOOTWEAR_SKIN_AUDIT',[(r['measurementIndex'],[(p['part'],p['bodyTriangleContactPairs'],p['meanContactBootWeights']) for p in r['parts']]) for r in failures],flush=True)
