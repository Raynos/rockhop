"""Observed rest-contact inputs only; texture bytes are deliberately separate."""
import hashlib
import json
import runpy
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
c = runpy.run_path(str(HERE/'component.py'))
NAMES = ('RiderHoodie','RiderBody__FullAnatomyReference','ActualSelectedGlove.L','ActualSelectedGlove.R')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def capture(bpy,np,helper):
    """Hash actual arrays the unchanged28 relation consumes and evaluated rest."""
    rig = bpy.data.objects['RiderSkeleton']
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    parts = {};deps = bpy.context.evaluated_depsgraph_get()
    for name in NAMES:
        obj = bpy.data.objects[name]
        assert not obj.data.shape_keys or all(k.value == 0 for k in obj.data.shape_keys.key_blocks)
        field = hashlib.sha256(json.dumps([g.name for g in obj.vertex_groups]).encode())
        for vertex in obj.data.vertices:
            field.update(struct.pack('<I',len(vertex.groups)))
            for group in vertex.groups:field.update(struct.pack('<If',group.group,group.weight))
        evaluated = obj.evaluated_get(deps)
        parts[name] = {'positions':hashlib.sha256(helper['points'](obj)[1].tobytes()).hexdigest(),
            'triangles':hashlib.sha256(helper['faces'](obj).tobytes()).hexdigest(),
            'evaluatedPositions':hashlib.sha256(helper['points'](evaluated)[1].tobytes()).hexdigest(),
            'evaluatedTriangles':hashlib.sha256(helper['faces'](evaluated).tobytes()).hexdigest(),
            'namedFields':field.hexdigest()}
    rest = [{'name':b.name,'parent':b.parent.name if b.parent else None,
             'matrix':[list(r) for r in b.matrix_local],'deform':b.use_deform} for b in rig.data.bones]
    return {'parts':parts,'rest':digest(rest),'motionInput':digest({
        'scope':'REST_ONLY_NO_ACTION_SAMPLES','frame':bpy.context.scene.frame_current,
        'rigWorld':[list(r) for r in rig.matrix_world],
        'poseBasis':{b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones}})}


def helper():
    cuff = c['read'](json.loads(c['INPUT47'].read_text())['pins']['cuffInput'])
    return runpy.run_path(str(c['checked'](c['read'](cuff['baseInput'])['intersectionHelper'])))


def reusable(row,baked):
    assert row['contactRecipe'] == c['pin'](__file__)
    assert baked['contactRecipe'] == row['contactRecipe']
    assert row['contactInputs'] == baked['originalWitness']['contactInputs'], 'Geometry/skin/rest/motion changed'
    # Every texture-only step, including independent reopen, compares the full
    # originalWitness. A matching contact hash alone never qualifies a bake.
    assert baked['independentReopenPassed'] is baked['bakeReopened'] is baked['detailBakePassed'] is True
    original = c['read'](baked['sourceNative77'])
    assert row['sourceNative'] in (original['native'],baked['native'])
