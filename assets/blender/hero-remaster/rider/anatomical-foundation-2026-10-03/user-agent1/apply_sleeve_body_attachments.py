"""Test frozen nearest-body sleeve skin/attachment ancestry on identical rest geometry."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
ap = argparse.ArgumentParser(description=__doc__)
for name in ['source','diagnosis','handoff','out','evidence']:
    ap.add_argument('--'+name,required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--')+1:]); source,diagnosis,handoff,out,evidence = [Path(getattr(a,n)).resolve() for n in ['source','diagnosis','handoff','out','evidence']]
sha = lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest(); pins = {str(p):sha(p) for p in [source,diagnosis,handoff]}
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
if (out/'sleeve-rest.glb').exists():
    raise RuntimeError('Frozen sleeve weight control exists')
d,h = json.loads(diagnosis.read_text()),json.loads(handoff.read_text())
assert d['handoffSHA256']==pins[str(handoff)]
assert pins[str(source)]==h['pins']['setup']
bpy.ops.wm.open_mainfile(filepath=str(source))
pattern = bpy.data.objects['Eased sleeve same-pattern skinned control']; body = bpy.data.objects['Canonical anatomical body, baked adult hm08']
rig = bpy.data.objects['Independent anatomical foundation rig']; root = bpy.data.objects['Foundation file frame, game x0.65']
body.data.calc_loop_triangles(); body_triangles = [list(t.vertices) for t in body.data.loop_triangles]
weight = lambda o,v:{o.vertex_groups[g.group].name:float(g.weight) for g in v.groups if g.weight>0 and o.vertex_groups[g.group].name in rig.data.bones}
body_weights = [weight(body,v) for v in body.data.vertices]; records = []; maximum_field_error = 0.
assert len(d['weights'])==len(pattern.data.vertices)==288
for row in d['weights']:
    i = row['garmentVertexID']; v = pattern.data.vertices[i]; before = weight(pattern,v)
    ids = row['bodyNativeVertexIDs']; assert ids==body_triangles[row['nearestNativeBodyTriangleID']]
    factors = np.clip(np.asarray(row['barycentric'],dtype=np.float64),0,1); factors /= factors.sum()
    nearest = sum((np.asarray(body.data.vertices[j].co,dtype=np.float64)*f for j,f in zip(ids,factors)),start=np.zeros(3))
    offset = np.asarray(v.co,dtype=np.float64)-nearest
    assert abs(float(np.linalg.norm(offset))-row['nativeRestGapM'])<2e-6
    assert np.linalg.norm(np.asarray(v.co)-np.asarray(h['pattern']['verticesNativeM'][i]))<2e-7
    field = {}
    for j,f in zip(ids,factors):
        for name,value in body_weights[j].items():
            field[name] = field.get(name,0)+float(f)*value
    error = max(abs(field.get(n,0)-row['nearestBodyWeights'].get(n,0)) for n in set(field)|set(row['nearestBodyWeights']))
    maximum_field_error = max(maximum_field_error,error); assert error<2e-6,(i,error)
    selected = sorted([(n,w) for n,w in field.items() if w>1e-12],key=lambda r:-r[1])[:4]
    total = sum(w for n,w in selected); selected = {n:w/total for n,w in selected}
    remove_names = [pattern.vertex_groups[g.group].name for g in v.groups if pattern.vertex_groups[g.group].name in rig.data.bones]
    for name in remove_names:
        pattern.vertex_groups[name].remove([i])
    for name,value in selected.items():
        if name not in pattern.vertex_groups:
            pattern.vertex_groups.new(name=name)
        pattern.vertex_groups[name].add([i],float(value),'REPLACE')
    after = weight(pattern,v)
    assert set(after)==set(selected) and all(abs(after[n]-selected[n])<1e-7 for n in after),(i,after,selected)
    assert abs(sum(after.values())-1)<1e-6,(i,after)
    pin_weight = next((g.weight for g in v.groups if pattern.vertex_groups[g.group].name=='Proximal sewn ring pins'),0.)
    assert pin_weight==h['pattern']['sewnAnchorWeights'][i]
    records.append({'nativeGarmentVertexID':i,'ring':row['ring'],'column':row['column'],'bodyNativeTriangleID':row['nearestNativeBodyTriangleID'],
        'bodyNativeVertexIDs':ids,'barycentric':factors.tolist(),'restBodyPointNativeM':nearest.tolist(),'restOffsetNativeM':offset.tolist(),
        'restGapM':float(np.linalg.norm(offset)),'beforeWeights':before,'actualNativeAfterWeights':after,'sewnAnchorWeightUnchanged':pin_weight,
        'weightL1Change':sum(abs(before.get(n,0)-after.get(n,0)) for n in set(before)|set(after))})
for o in bpy.data.objects:
    o.select_set(False)
for o in [pattern,root,rig]:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out/'control.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(out/'sleeve-rest.glb'),export_format='GLB',use_selection=True,export_yup=True,
    export_animations=False,export_attributes=True,export_extras=True)
assert pins=={p:sha(p) for p in pins}
report = {'status':'UNACCEPTED same-rest sleeve body-derived skin/attachment control; independent actual game test pending',
    'pins':pins,'candidateMasterSHA256':sha(out/'control.blend'),'candidateGLBSHA256':sha(out/'sleeve-rest.glb'),'recipeSHA256':sha(__file__),
    'maximumNativeVsFrozenDiagnosisWeightError':maximum_field_error,'maximumWeightL1Change':max(r['weightL1Change'] for r in records),
    'attachments':records,'axes':h['axes'],'limits':['Only actual skin weights change; restgeometry/topology/UV/materials/51bind and original24hard24half sewn pin field must remain exact.',
        'Frozen Agent3 body-triangle ancestry is independently recomputed against original native body weights; it is a hypothesis, not a fit acceptance.',
        'Restoffset/triangle attachments expose ancestry only. GLB skin weights are consumed by skinning; no unused attachment table qualifies live collision response.',
        'No projection distance increase, cloth rerun, body/head/bind change, source control overwrite, film or player promotion. Agent3 checks real703tick window and self-folds; root judges.']}
(evidence/'attachments.json').write_text(json.dumps(report,indent=2)+'\n')
print('SLEEVE_BODY_WEIGHT_CONTROL',report['candidateGLBSHA256'],maximum_field_error,report['maximumWeightL1Change'],flush=True)
