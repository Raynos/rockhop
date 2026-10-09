"""Proof68-supported exact oriented face bearings; new queries stay frozen37."""
import ast
from pathlib import Path
import numpy as np
import intake

FROZEN37=intake.BASE/'selected-production-constructor37/author.py'
FROZEN37_SHA='b5ec57c735a1e2e4c030f14d90597097b043fbe59f945793de42bd134e7556cc'


def key(face):
    values=tuple(int(v) for v in face);return min(values,values[1:]+values[:1],values[2:]+values[:2])


def exact_maps(sp,sf,tp,tf,original,source_materials,target_materials):
    assert len(original)==len(tp) and len(np.unique(original))==len(original)
    assert np.all(original>=0) and np.all(original<len(sp))
    assert np.array_equal(tp,sp[original]),'Exact face ancestry moved original positions'
    assert len(source_materials)==len(sf) and len(target_materials)==len(tf)
    source_keys={key(face):i for i,face in enumerate(sf)}
    assert len(source_keys)==len(sf),'Duplicate oriented source face'
    target_keys=[key(face) for face in original[tf]]
    assert len(set(target_keys))==len(tf),'Duplicate oriented target face'
    forward=np.full(len(tf),-1,np.int32);reverse=np.full(len(sf),-1,np.int32)
    for target_id,face_key in enumerate(target_keys):
        source_id=source_keys.get(face_key)
        if source_id is None:continue
        assert source_materials[source_id]==target_materials[target_id],'Exact inherited face material differs'
        source_order=np.roll(sf[source_id],-int(np.argmin(sf[source_id])))
        target_order=np.roll(tf[target_id],-int(np.argmin(original[tf[target_id]])))
        assert np.array_equal(source_order,original[target_order])
        assert np.array_equal(sp[source_order],tp[target_order]),'Exact oriented face positions differ'
        assert np.array_equal(sp[sf[source_id]].mean(0),tp[tf[target_id]].mean(0)),'Exact inherited centroid differs'
        forward[target_id]=source_id;reverse[source_id]=target_id
    return {'targetToSource':forward,'sourceToTarget':reverse}


def native_maps(engine,source,target,sp,sf,tp,tf):
    attr=target.data.attributes.get('ProductionOriginalVertex')
    assert attr is not None and attr.domain=='POINT' and attr.data_type=='INT'
    original=np.empty(len(tp),np.int32);attr.data.foreach_get('value',original)
    source_materials=np.array([tri.material_index for tri in source.data.loop_triangles],np.int32)
    target_materials=np.array([tri.material_index for tri in target.data.loop_triangles],np.int32)
    return exact_maps(sp,sf,tp,tf,original,source_materials,target_materials)


def adapted_source():
    intake.pin(FROZEN37,FROZEN37_SHA)
    raw=FROZEN37.read_text();tree=ast.parse(raw)
    source=ast.get_source_segment(raw,next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='surface_checks'))
    patches=[
        ('tp = engine.points(target); tf = engine.triangles(target)',
         'tp = engine.points(target); tf = engine.triangles(target)\n    inherited70 = exact_face_maps70(engine, source, target, sp, sf, tp, tf)'),
        ('            near = tree.find_nearest(Vector(point))',
         "            exact = int(inherited70['targetToSource'][i]) if label == 'target-face-centroids' else int(inherited70['sourceToTarget'][i]) if label == 'source-face-centroids' else -1\n            if exact >= 0:\n                reference = sp[sf[exact]].mean(axis=0) if label == 'target-face-centroids' else tp[tf[exact]].mean(axis=0)\n                assert np.array_equal(point, reference), 'Inherited query centroid changed'\n                distances[i] = 0; face_ids[i] = exact\n                if qn is not None: dots[i] = qn[i] @ rn[exact]\n                continue\n            near = tree.find_nearest(Vector(point))"),
        ("report[label] = {'samples': len(query), 'missingBearings':",
         "matched = int(np.count_nonzero(inherited70['targetToSource'] >= 0)) if label == 'target-face-centroids' else int(np.count_nonzero(inherited70['sourceToTarget'] >= 0)) if label == 'source-face-centroids' else 0\n        report[label] = {'samples': len(query), 'exactInheritedAncestryBearings': matched, 'unchangedNearestBVHBearings': len(query)-matched, 'actualProof68': PROOF68_PIN, 'missingBearings':"),
    ]
    for old,new in patches:
        assert source.count(old)==1,('Frozen37 surface patch drift',old);source=source.replace(old,new)
    return source


def install(namespace,proof_pin):
    assert proof_pin=={'path':str(intake.PROOF68.relative_to(intake.ROOT)),'sha256':intake.PROOF68_SHA}
    namespace.update(exact_face_maps70=native_maps,PROOF68_PIN=proof_pin)
    exec(compile(adapted_source(),str(FROZEN37)+'[exact-face70]','exec'),namespace)
