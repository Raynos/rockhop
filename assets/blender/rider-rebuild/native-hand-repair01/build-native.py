"""Intended-final local hand-rest/field derivative of immutable combined04.

Run only through the parent's serialized bounded Blender guard. This makes
body+75 masters and diagnostic transport evidence, never player assets.
"""
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'docs/evidence/rider-rebuild/glove-charts01'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec = importlib.util.spec_from_file_location('field_math', Path(__file__).with_name('field-math.py'))
math = importlib.util.module_from_spec(spec); spec.loader.exec_module(math)


def pin(record):
    path = ROOT / record['path']
    assert sha(path) == record['sha256'], ('Changed source', str(path))
    return path


def geometry(obj):
    h = hashlib.sha256()
    for v in obj.data.vertices: h.update(struct.pack('<3f', *v.co))
    for p in obj.data.polygons:
        h.update(struct.pack('<II', len(p.vertices),p.material_index))
        h.update(struct.pack('<'+'I'*len(p.vertices), *p.vertices))
    for layer in obj.data.uv_layers:
        h.update(layer.name.encode())
        for corner in layer.data:h.update(struct.pack('<2f',*corner.uv))
    for a in obj.data.attributes:
        if a.name in ('_NATIVE_ID', '_SOURCE_VERTEX_ID', '_REGION_ID'):
            h.update(a.name.encode())
            for row in a.data: h.update(struct.pack('<f', row.value))
    return h.hexdigest()


def coefficients(obj, names):
    lookup = {name:i for i,name in enumerate(names)}
    groups = {g.index:g.name for g in obj.vertex_groups}
    fields = np.zeros((len(obj.data.vertices),len(names)),dtype=np.float32)
    for v in obj.data.vertices:
        for group in v.groups:
            assert groups[group.group] in lookup, ('Unexpected group',groups[group.group])
            fields[v.index,lookup[groups[group.group]]] = group.weight
    return fields


def rest(rig):
    return [{'name':b.name,'parent':b.parent.name if b.parent else None,
        'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local],
        'useConnect':b.use_connect,'useDeform':b.use_deform} for b in rig.data.bones]


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 1
    out = Path(args[0]).resolve()
    assert not out.exists() and out.is_relative_to(ROOT / 'harness/out/rider-rebuild/native-hand-repair01')
    receipt = json.loads((BASE/'rebind-domain01/rebind-domain.json').read_text())
    inputs = {r['path']:pin(r) for r in receipt['inputs']}
    domain = np.load(pin(receipt['arrays']))
    alpha = domain['newFieldBlendAlpha']; changed = np.flatnonzero(alpha > 0).tolist()
    unchanged = np.flatnonzero(alpha == 0)
    assert len(changed) == 1446 and len(unchanged) == 9136
    proposal_path = BASE/'medial-correction01/proposed-joints.npz'
    proposal = np.load(proposal_path); names = proposal['jointNames'].tolist()
    correction_path = BASE/'medial-correction01/medial-correction.json'
    assert sha(correction_path) == '4047b86c8935a303d0158fedb83d3a8cfc2032162f86d8756dc4e9023f2be623'
    correction = json.loads(correction_path.read_text())
    extra_pins=[{'path':str(correction_path.relative_to(ROOT)),'sha256':sha(correction_path)}]
    diagnostic_base=ROOT/'docs/evidence/rider-rebuild/native-hand-repair01/edit-roundtrip01'
    for filename,digest in {'edit-roundtrip.json':'f36b6d1873fd46bf4efb82c9d9d1f1077d51ad2c3e8195e15e52915e034c5a22',
                           'rest-byte-comparison.npz':'bbb8ae3342b471852baf46a2e49513acca5ab0bf74ba419f6f4ced41bbfa3731'}.items():
        record={'path':str((diagnostic_base/filename).relative_to(ROOT)),'sha256':digest}
        pin(record);extra_pins.append(record)
    expected_rest=dict(np.load(diagnostic_base/'rest-byte-comparison.npz'))
    assert np.array_equal(expected_rest['jointNames'],proposal['jointNames'])
    descendants={'DEF-'+stem+'.'+side for side in ('L','R') for stem in ('f_middle.03','f_pinky.02','f_pinky.03')}
    exporter=Path('/Applications/Blender.app/Contents/Resources/5.2/scripts/addons_core/io_scene_gltf2/blender/exp')
    for filename,digest in {'primitive_extract.py':'55e14cbe849b0c4ec5545c85a1aae3d8c2c7d65eade67de43eb1a43b05738684',
                           'primitive_attributes.py':'815331d39cdf06e73ae110e9921ebfc8cb37825290843cbcbf4d1a7559899e5d'}.items():
        record={'path':str(exporter/filename),'sha256':digest};pin(record);extra_pins.append(record)
    original_native = ROOT/'harness/out/rider-rebuild/construction01/combined04/rider-assembled.blend'
    assert sha(original_native) == '26cd01d4ba02be3fbf0f3a5b290c99445ef34d7d18d90012d2ef44913ef06d1d'
    out.mkdir(parents=True)
    bpy.ops.wm.open_mainfile(filepath=str(original_native))
    body,rig = bpy.data.objects['RiderBody'],bpy.data.objects['RiderSkeleton']
    before_geometry = geometry(body)
    assert len(body.data.vertices) == 10582 and len(rig.data.bones) == 75
    assert set(names) == set(b.name for b in rig.data.bones)
    assert body.matrix_world.is_identity and rig.matrix_world.is_identity
    source_rest = {r['name']:r for r in rest(rig)}
    for i,name in enumerate(names):
        for field,plural in [('head','heads'),('tail','tails'),('matrix','matrices')]:
            assert np.array_equal(source_rest[name][field],expected_rest['correction_source_'+plural+'_double'][i])
    old_native = coefficients(body,names)
    for obj in list(bpy.data.objects):
        if obj not in (body,rig): bpy.data.objects.remove(obj,do_unlink=True)
    rig.animation_data_clear()
    for b in rig.pose.bones:
        assert not b.constraints
        b.matrix_basis = Matrix.Identity(4)
    assert rig.animation_data is None
    assert all(m.type in ('TRIANGULATE','ARMATURE') for m in body.modifiers)
    armature = [m for m in body.modifiers if m.type=='ARMATURE']
    assert len(armature) == 1 and armature[0].object == rig
    armature[0].use_deform_preserve_volume = False
    body.parent = rig; body.matrix_parent_inverse = Matrix.Identity(4)
    bpy.ops.object.select_all(action='DESELECT'); rig.hide_set(False); rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    affected = {'DEF-'+stem+'.'+side for side in ('L','R')
                for stem in ('palm.04','f_pinky.01','f_middle.01','f_middle.02')}
    bpy.ops.object.mode_set(mode='EDIT')
    for i,name in enumerate(names):
        b = rig.data.edit_bones[name]
        assert np.max(abs(np.array(b.head)-proposal['originalHeads'][i])) < 1e-7
        assert np.max(abs(np.array(b.tail)-proposal['originalTails'][i])) < 1e-7
        # Assign only changed endpoints, leaving every untouched native endpoint exact.
        if np.any(proposal['heads'][i] != proposal['originalHeads'][i]): b.head = Vector(proposal['heads'][i])
        if np.any(proposal['tails'][i] != proposal['originalTails'][i]): b.tail = Vector(proposal['tails'][i])
        if name in affected:
            palm = Vector(correction['palmNormals'][name[-1]])
            y = (b.tail-b.head).normalized(); z = (palm-y*palm.dot(y)).normalized()
            b.align_roll(z)
    bpy.ops.object.mode_set(mode='OBJECT')
    corrected_rest = {r['name']:r for r in rest(rig)}
    for name,row in corrected_rest.items():
        assert row['parent'] == source_rest[name]['parent']
        assert row['useConnect'] == source_rest[name]['useConnect']
        if name not in affected | descendants:
            assert row == source_rest[name], ('Untouched rest changed',name)
        # The measured six descendant recompositions are explicit lineage,
        # never a widened tolerance. Every actual record must match the pinned
        # prior fresh-load diagnostic byte-for-byte, including all61 others.
        i=names.index(name)
        for field,plural in [('head','heads'),('tail','tails'),('matrix','matrices')]:
            assert np.array_equal(row[field],expected_rest['correction_result_'+plural+'_double'][i]),('New rest differs from measured authority',name,field)
        assert row['useDeform']==source_rest[name]['useDeform']
        frame = np.array(row['matrix'])[:3,:3]
        if name in affected:
            assert abs(np.linalg.det(frame)-1) < 1e-6
            expected = math.proper_frame(np.array(row['head']),np.array(row['tail']),correction['palmNormals'][name[-1]])
            assert np.max(abs(frame-expected)) < 1e-6, name
    for side in ('L','R'):
        for child,parent in [('f_pinky.01','palm.04'),('f_middle.02','f_middle.01')]:
            assert corrected_rest['DEF-'+child+'.'+side]['head'] == corrected_rest['DEF-'+parent+'.'+side]['tail']
    assert geometry(body) == before_geometry
    helpers = [name for name in names if name.startswith(('PalmSocket.','SoleSocket.'))]
    assert len(helpers) == 4
    temporary = body.copy(); temporary.data = body.data.copy(); temporary.name='NativeHeatCandidate'
    bpy.context.scene.collection.objects.link(temporary)
    temporary.parent=None; temporary.matrix_world=Matrix.Identity(4)
    temporary.vertex_groups.clear()
    for modifier in list(temporary.modifiers): temporary.modifiers.remove(modifier)
    assert geometry(temporary) == before_geometry
    for name in helpers: rig.data.bones[name].use_deform=False
    bpy.ops.object.select_all(action='DESELECT');temporary.hide_set(False); temporary.select_set(True);rig.select_set(True)
    bpy.context.view_layer.objects.active=rig
    operator = bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    assert operator == {'FINISHED'},operator
    candidate=[]; groups={g.index:g.name for g in temporary.vertex_groups}
    for v in temporary.data.vertices:
        row=sorted([[groups[g.group],g.weight] for g in v.groups if g.weight>0],key=lambda r:(-r[1],r[0]))
        assert row and not set(n for n,_ in row) & set(helpers), ('Bind missing/helper field',v.index)
        candidate.append(row)
    assert geometry(temporary) == before_geometry
    for name in helpers: rig.data.bones[name].use_deform=True
    bpy.data.objects.remove(temporary,do_unlink=True)
    old_full=json.loads((ROOT/'harness/out/rider-rebuild/construction01/rig04/weights-full.json').read_text())
    old_four=json.loads((ROOT/'harness/out/rider-rebuild/construction01/rig04/weights-four.json').read_text())
    full,four,loss=math.blend_fields(old_full,old_four,candidate,alpha,names,helpers)
    for g in body.vertex_groups: g.remove(changed)
    for index in changed:
        for name,weight in four[index]:
            group=body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
            group.add([index],weight,'REPLACE')
    new_native=coefficients(body,names)
    assert np.array_equal(new_native[unchanged],old_native[unchanged])
    assert all(full[i] == old_full[i] and four[i] == old_four[i] for i in unchanged)
    assert geometry(body) == before_geometry
    bpy.context.view_layer.update()
    dg=bpy.context.evaluated_depsgraph_get(); evaluated=body.evaluated_get(dg)
    bind_delta=max((v.co-evaluated.data.vertices[v.index].co).length for v in body.data.vertices)
    assert bind_delta < 2e-6,bind_delta
    (out/'weights-full.json').write_text(json.dumps(full)+'\n')
    (out/'weights-four.json').write_text(json.dumps(four)+'\n')
    (out/'weights-new-automatic.json').write_text(json.dumps(candidate)+'\n')
    vertices=np.array([list(v.co) for v in body.data.vertices],dtype=np.float32)
    bpy.context.view_layer.objects.active=body
    evaluated.data.calc_loop_triangles()
    faces=np.array([list(t.vertices) for t in evaluated.data.loop_triangles],dtype=np.int32)
    source_membership=[set() for _ in body.data.vertices]
    for polygon in body.data.polygons:
        for vertex in polygon.vertices:source_membership[vertex].add(polygon.index)
    source_polygons=[];source_loops=[]
    for triangle in faces:
        matches=set.intersection(*(source_membership[vertex] for vertex in triangle))
        assert len(matches)==1,('Ambiguous triangulation ancestry',triangle.tolist(),matches)
        index=matches.pop();polygon=body.data.polygons[index]
        loop_lookup={int(vertex):int(loop) for vertex,loop in zip(polygon.vertices,polygon.loop_indices)}
        source_polygons.append(index);source_loops.append([loop_lookup[int(vertex)] for vertex in triangle])
    active_uv=next((layer for layer in body.data.uv_layers if layer.active_render),body.data.uv_layers.active)
    assert active_uv is not None
    triangle_uv=np.array([[list(active_uv.data[loop].uv) for loop in loops] for loops in source_loops],dtype=np.float32)
    rows=rest(rig); by_name={r['name']:r for r in rows}
    assert by_name==corrected_rest, 'Binding changed the measured rest authority'
    np.savez_compressed(out/'native-body.npz',vertices=vertices,faces=faces,nativeCoefficients=new_native,
        originalNativeCoefficients=old_native,jointNames=np.array(names),
        jointHeads=np.array([by_name[n]['head'] for n in names]),jointTails=np.array([by_name[n]['tail'] for n in names]),
        jointMatrices=np.array([by_name[n]['matrix'] for n in names]),newFieldBlendAlpha=alpha,
        nativeSourceVertexIds=domain['nativeSourceVertexIds'],removedFullMass=loss,
        sourcePolygonRows=np.array(source_polygons,dtype=np.int32),sourceLoopRows=np.array(source_loops,dtype=np.int32),
        triangleCornerUV=triangle_uv)
    contract=json.loads((ROOT/'harness/out/rider-rebuild/construction01/combined04/rider-contract.json').read_text())
    contract['nativeRest']['bones']=rows
    contract['driver']['socketOrientationCalibrationRequired']=True
    for key in ('spineFlexTable','poseCalibration','adaptiveSpineFlex'):contract['driver'].pop(key,None)
    for key in ('sourceSHA256','glbSHA256','genericAction','exportedObjectMeshes'):contract.pop(key,None)
    digit_flex={}
    for label,side in [('left','L'),('right','R')]:
        digit_flex[label]={}
        for stem in ('thumb','f_index','f_middle','f_ring','f_pinky'):
            for segment in (1,2,3):
                name='DEF-'+stem+'.%02d.'%segment+side;row=by_name[name]
                local=math.flex_axis(np.array(row['head']),np.array(row['tail']),correction['palmNormals'][side],np.array(row['matrix'])[:3,:3])
                digit_flex[label][name]={'axisLocal':local.tolist(),'maxRadians':.85 if stem=='thumb' else 1.15,
                    'positiveSign':1,'anatomicalRole':'thumb-metacarpal' if stem=='thumb' and segment==1 else
                    ('thumb-MCP' if stem=='thumb' and segment==2 else ('thumb-IP' if stem=='thumb' else ['MCP','PIP','DIP'][segment-1]))}
    contract['driver']['digitFlex']=digit_flex
    (out/'rider-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'anatomical-hand-rig.blend'))
    native_sha=sha(out/'anatomical-hand-rig.blend')
    (out/'digit-controls.json').write_text(json.dumps({'acceptedArt':False,'rigNativeSHA256':native_sha,
        'digitFlex':digit_flex,'measuredPalmNormals':correction['palmNormals'],'socketOrientationCalibrationRequired':True,
        'qualification':'PENDING_INDEPENDENT_REOPEN_SMALL_CURL_SKIN_SIGN_AND_MOVING_REVIEW'},indent=2)+'\n')
    bpy.ops.export_scene.gltf(filepath=str(out/'native-body.glb'),export_format='GLB',use_selection=True,
        export_animations=False,export_def_bones=True,export_skins=True,export_influence_nb=4,
        export_all_influences=False,export_apply=True,export_yup=True,export_attributes=True)
    modifiers=[]
    for index,m in enumerate(body.modifiers):
        properties=['show_viewport','show_render']
        properties+=['quad_method','ngon_method','min_vertices','keep_custom_normals'] if m.type=='TRIANGULATE' else [
            'use_deform_preserve_volume','use_vertex_groups','use_bone_envelopes','use_multi_modifier','vertex_group','invert_vertex_group']
        modifiers.append({'index':index,'name':m.name,'type':m.type,
            'options':{key:getattr(m,key) for key in properties if hasattr(m,key)}})
    report={'acceptedArt':False,'status':'NATIVE_LOCAL_HAND_DERIVATIVE_REOPEN_PENDING',
        'native':{'path':str(out/'anatomical-hand-rig.blend'),'sha256':native_sha},
        'glb':{'path':str(out/'native-body.glb'),'sha256':sha(out/'native-body.glb')},
        'recipeSHA256':sha(__file__),'correctionSHA256':sha(correction_path),
        'sourcePins':receipt['inputs']+[receipt['arrays']]+extra_pins, 'geometryAndSourceIDSHA256':before_geometry,
        'bodyVertices':10582,'skeletonJoints':75,'affectedRestFrames':sorted(affected|descendants),
        'nativeRestLineage':{'authoredAffectedFrames':sorted(affected),
            'measuredDescendantMatrixRecompositions':sorted(descendants),'all75ActualRecordsEqualPinnedDiagnostic':True,
            'unchangedOtherRecords':61,'originalRest':source_rest,'actualRest':corrected_rest,
            'diagnosticArrays':{'path':str(diagnostic_base/'rest-byte-comparison.npz'),
                                'sha256':sha(diagnostic_base/'rest-byte-comparison.npz')}},
        'bodyModifierOperators':modifiers,
        'nativeTriangulationLineage':{'triangles':len(faces),'sourcePolygons':len(body.data.polygons),
            'sourceUVLayer':active_uv.name,'everyTriangleAndUVCornerHasOriginalPolygonLoopAncestry':True,
            'arrays':{'path':str(out/'native-body.npz'),'sha256':sha(out/'native-body.npz')}},
        'bindOperatorOutcome':sorted(operator),'candidateUnweightedVertices':0,'excludedBindHelpers':helpers,
        'domainRows':1446,'verbatimOutsideRows':9136,'nativeOutsideFloat32CoefficientsExact':True,
        'zeroPoseMaximumDisplacementM':bind_delta,'maximumRemovedFullMass':float(loss.max()),
        'limits':['Source and coefficients only; independent native/export readback, moving anatomy and weights remain required.',
                  'MCP/PIP stations retain proposal axial stations; no static certificate grants moving acceptance.',
                  'No source artwork, glove fitting, socket recalibration, complete-outfit, engine or art acceptance.']}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    for record in report['sourcePins']:pin(record)
    print(json.dumps({'status':report['status'],'nativeSHA256':native_sha,'maxRemovedMass':float(loss.max())}))


if __name__=='__main__':main()
