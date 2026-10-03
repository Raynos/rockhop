"""Independently verify all nonfootwear native fields and the full original bind."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
ap = argparse.ArgumentParser(description=__doc__)
for name in ['source','candidate','out']:
    ap.add_argument('--'+name,required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--')+1:]); source,candidate,out = [Path(getattr(a,n)).resolve() for n in ['source','candidate','out']]
sha = lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def capture(p):
    bpy.ops.wm.open_mainfile(filepath=str(p)); meshes = {}
    rig = bpy.data.objects['Independent anatomical foundation rig']
    bind = [(b.name,b.parent.name if b.parent else None,[list(row) for row in b.matrix_local]) for b in rig.data.bones]
    for o in bpy.data.objects:
        if o.type!='MESH' or o.name=='Complete worn boot volume on own canonical feet':
            continue
        m = o.data
        fields = {'vertices':[list(v.co) for v in m.vertices],'polygons':[list(p.vertices) for p in m.polygons],
            'UV':[[list(v.uv) for v in layer.data] for layer in m.uv_layers],
            'weights':[[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in m.vertices],
            'keys':[(k.name,k.value,[list(v.co) for v in k.data]) for k in m.shape_keys.key_blocks] if m.shape_keys else [],
            'materials':[mat.name for mat in m.materials],'slots':[p.material_index for p in m.polygons],
            'cornerNormals':[list(n.vector) for n in m.corner_normals], 'matrixLocal':[list(row) for row in o.matrix_local],
            'parent':o.parent.name if o.parent else None,'hideRender':o.hide_render}
        meshes[o.name] = hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest()
    return bind,meshes
before = capture(source); after = capture(candidate)
assert before==after,'Nonfootwear native fields or bind changed'
report = {'status':'UNACCEPTED09 native nonfootwear/51bind preservation verified','sourceSHA256':sha(source),
    'candidateSHA256':sha(candidate),'verifierSHA256':sha(__file__),'all51NativeBindExact':True,
    'allNonFootwearMeshFieldsIncludingHiddenControlsExact':after[1],
    'limits':['Only the boot topology/weights are permitted to differ; hashes include normals, UVs, keys, weights, transforms and render visibility.',
        'Field preservation does not certify moving fit, live collision response, art acceptance or mobile cost.']}
out.write_text(json.dumps(report,indent=2)+'\n');print('PLANTAR_NATIVE_FIELDS_VERIFIED',len(after[1]),flush=True)
