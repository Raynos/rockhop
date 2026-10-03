"""Freeze current constructed boot source IDs and actual native skin fields."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
ap = argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,out = Path(a.source).resolve(),Path(a.out).resolve()
sha = lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
if out.exists():
    raise RuntimeError('Frozen native boot inventory exists')
bpy.ops.wm.open_mainfile(filepath=str(source));o = bpy.data.objects['Complete worn boot volume on own canonical feet']
rig = bpy.data.objects['Independent anatomical foundation rig'];mesh = o.data;mesh.calc_loop_triangles();rows = []
for v in mesh.vertices:
    weights = {o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0 and o.vertex_groups[g.group].name in rig.data.bones}
    total = sum(weights.values());assert total>0
    rows.append({'nativeVertexID':v.index,'restNativeM':list(v.co),'rawNativeWeights':weights,'rawWeightSum':total,
        'normalizedNativeWeights':{n:w/total for n,w in weights.items()}})
report = {'status':'UNACCEPTED09 currentconstructedboot inventory; qualifiednativefit control, art/runtime not accepted',
    'sourceMasterSHA256':sha(source),'recipeSHA256':sha(__file__),'object':o.name,'mesh':mesh.name,
    'axes':{'units':'metres','native':'+X forward/+Z up/-Y left','glTF':'+X forward/+Y up/+Z left','nativeToFileWorld':'[native.x+.65,native.z,-native.y]','runtimeCenterOnceX':-.65},
    'vertices':rows,'triangles':[{'nativeTriangleID':t.index,'nativePolygonID':t.polygon_index,'nativeVertexIDs':list(t.vertices),'materialSlot':mesh.polygons[t.polygon_index].material_index} for t in mesh.loop_triangles],
    'materialNames':[m.name for m in mesh.materials],
    'footParents':{side:{'nativeBoneName':'foot.'+side,'nativeBoneHeadM':list(rig.data.bones['foot.'+side].head_local),
        'nativeBoneTailM':list(rig.data.bones['foot.'+side].tail_local),'nativeBindMatrixRows':[list(r) for r in rig.data.bones['foot.'+side].matrix_local]} for side in ['L','R']},
    'rawNativeWeightSumRange':[min(r['rawWeightSum'] for r in rows),max(r['rawWeightSum'] for r in rows)],
    'nonUnitNativeWeightVertices':sum(abs(r['rawWeightSum']-1)>1e-6 for r in rows),
    'limits':['Inventory reports actual frozen source memberships and normalized skin field, not the intended nearest-body field. Native construction may retain stale old memberships; source09fit evidence remains an empirical control, not a pure-barycentric weighting test.',
        'No source overwrite, body/51bind change, marker injection, runtime collision or footwear-art acceptance. Current05bodysole IDs are unrelated to this constructed outsole.']}
out.write_text(json.dumps(report,indent=2)+'\n');print('BOOT_NATIVE_INVENTORY',report['rawNativeWeightSumRange'],report['nonUnitNativeWeightVertices'],flush=True)
