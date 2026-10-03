"""Verify the bounded sleeve control changes only declared native joint weights."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
ap = argparse.ArgumentParser(description=__doc__)
for n in ['source','candidate','attachments','out']:
    ap.add_argument('--'+n,required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--')+1:]); source,candidate,attachments,out = [Path(getattr(a,n)).resolve() for n in ['source','candidate','attachments','out']]
sha = lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def capture(file):
    bpy.ops.wm.open_mainfile(filepath=str(file)); rig = bpy.data.objects['Independent anatomical foundation rig']; rows = {}; skin = []
    bind = [(b.name,b.parent.name if b.parent else None,[list(r) for r in b.matrix_local]) for b in rig.data.bones]
    for o in bpy.data.objects:
        if o.type!='MESH':
            continue
        m = o.data; is_pattern = o.name=='Eased sleeve same-pattern skinned control'
        weights = [[(o.vertex_groups[g.group].name,g.weight) for g in v.groups
            if not is_pattern or o.vertex_groups[g.group].name not in rig.data.bones] for v in m.vertices]
        if is_pattern:
            skin = [{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0 and o.vertex_groups[g.group].name in rig.data.bones} for v in m.vertices]
        fields = {'vertices':[list(v.co) for v in m.vertices],'faces':[list(p.vertices) for p in m.polygons],
            'UV':[[list(v.uv) for v in layer.data] for layer in m.uv_layers],'permittedWeights':weights,
            'materials':[mat.name for mat in m.materials],'slots':[p.material_index for p in m.polygons],
            'normals':[list(n.vector) for n in m.corner_normals],'parent':o.parent.name if o.parent else None,
            'matrixLocal':[list(r) for r in o.matrix_local],'hideRender':o.hide_render,
            'keys':[(k.name,k.value,[list(v.co) for v in k.data]) for k in m.shape_keys.key_blocks] if m.shape_keys else []}
        rows[o.name] = hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest()
    return bind,rows,skin
old,new = capture(source),capture(candidate);d = json.loads(attachments.read_text())
assert old[:2]==new[:2],'Native geometry/body/control/bind field changed'
assert new[2]==[r['actualNativeAfterWeights'] for r in d['attachments']]
report = {'status':'UNACCEPTED same-rest geometry/51bind/othercontrols unchanged, declared skin weights verified',
    'sourceSHA256':sha(source),'candidateSHA256':sha(candidate),'attachmentsSHA256':sha(attachments),'verifierSHA256':sha(__file__),
    'all51BindExact':True,'sameRestPatternGeometryUVMaterialsAndPinFieldExact':True,'allOtherMeshFieldsIncludingPhysicsControlsExact':new[1],
    'changedNativeVertices':sum(a!=b for a,b in zip(old[2],new[2])),'limits':['No cloth simulation run or actual game/live collision acceptance is inferred from source preservation.']}
out.write_text(json.dumps(report,indent=2)+'\n');print('SLEEVE_WEIGHT_NATIVE_VERIFIED',report['changedNativeVertices'],len(new[1]),flush=True)
