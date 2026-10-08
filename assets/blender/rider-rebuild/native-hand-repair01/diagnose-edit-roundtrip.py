"""Read-only fresh-load no-op versus four-endpoint edit-mode comparison."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[4]
SOURCE=ROOT/'harness/out/rider-rebuild/construction01/combined04/rider-assembled.blend'
SOURCE_SHA='26cd01d4ba02be3fbf0f3a5b290c99445ef34d7d18d90012d2ef44913ef06d1d'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def snapshot(rig,names):
    rows={row['name']:row for row in BUILDER.rest(rig)}
    return {'rows':rows,
        'heads':np.array([rows[n]['head'] for n in names]),
        'tails':np.array([rows[n]['tail'] for n in names]),
        'matrices':np.array([rows[n]['matrix'] for n in names])}


def compare(before,after,names):
    result=[]
    for index,name in enumerate(names):
        source,target=before['rows'][name],after['rows'][name]
        row={'name':name,'parent':source['parent'],'unchangedRecord':source==target}
        for field in ('heads','tails','matrices'):
            a,b=before[field][index],after[field][index]
            a32,b32=a.astype(np.float32),b.astype(np.float32)
            row[field]={'maximumAbsoluteDelta':float(np.max(abs(a-b))),
                'originalDoubleBytesEqual':a.tobytes()==b.tobytes(),
                'nativeFloat32BytesEqual':a32.tobytes()==b32.tobytes(),
                'changedComponentIndices':np.argwhere(a!=b).tolist(),
                'sourceFloat32BytesHex':a32.tobytes().hex(),'resultFloat32BytesHex':b32.tobytes().hex(),
                'source':a.tolist(),'result':b.tolist()}
        for field in ('parent','useConnect','useDeform'):
            row[field+'Comparison']={'source':source[field],'result':target[field],'equal':source[field]==target[field]}
        result.append(row)
    return result


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==1
    out=Path(args[0]).resolve();assert not out.exists()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/native-hand-repair01')
    assert sha(SOURCE)==SOURCE_SHA
    proposal_path=ROOT/'docs/evidence/rider-rebuild/glove-charts01/medial-correction01/proposed-joints.npz'
    correction_path=proposal_path.with_name('medial-correction.json')
    assert sha(proposal_path)=='dd4e9fd55743d879d4cef30719c0213aed07a3d1b07b31ec822065f48c89d1c3'
    assert sha(correction_path)=='4047b86c8935a303d0158fedb83d3a8cfc2032162f86d8756dc4e9023f2be623'
    proposal=dict(np.load(proposal_path));names=proposal['jointNames'].tolist()
    correction=json.loads(correction_path.read_text())
    affected={'DEF-'+stem+'.'+side for side in ('L','R') for stem in ('palm.04','f_pinky.01','f_middle.01','f_middle.02')}
    out.mkdir(parents=True)
    results={};arrays={}
    for mode in ('noOp','correction'):
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        rig,body=bpy.data.objects['RiderSkeleton'],bpy.data.objects['RiderBody']
        before=snapshot(rig,names)
        geometry=BUILDER.geometry(body);fields=BUILDER.coefficients(body,names).copy()
        bpy.ops.object.select_all(action='DESELECT');rig.hide_set(False);rig.select_set(True)
        bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
        edit_before={name:{'head':list(rig.data.edit_bones[name].head),'tail':list(rig.data.edit_bones[name].tail),
            'matrix':[list(r) for r in rig.data.edit_bones[name].matrix],'roll':rig.data.edit_bones[name].roll} for name in names}
        if mode=='correction':
            for i,name in enumerate(names):
                bone=rig.data.edit_bones[name]
                if np.any(proposal['heads'][i]!=proposal['originalHeads'][i]):bone.head=Vector(proposal['heads'][i])
                if np.any(proposal['tails'][i]!=proposal['originalTails'][i]):bone.tail=Vector(proposal['tails'][i])
                if name in affected:
                    normal=Vector(correction['palmNormals'][name[-1]])
                    direction=(bone.tail-bone.head).normalized()
                    bone.align_roll((normal-direction*normal.dot(direction)).normalized())
        edit_after={name:{'head':list(rig.data.edit_bones[name].head),'tail':list(rig.data.edit_bones[name].tail),
            'matrix':[list(r) for r in rig.data.edit_bones[name].matrix],'roll':rig.data.edit_bones[name].roll} for name in names}
        bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
        after=snapshot(rig,names)
        assert BUILDER.geometry(body)==geometry and np.array_equal(BUILDER.coefficients(body,names),fields)
        results[mode]={'all75Records':compare(before,after,names),'editEntryRecords':edit_before,'editExitRecords':edit_after,
            'bodyGeometryUVTopologySourceIDsAndNativeFieldsUnchanged':True,'freshOriginalLoad':True}
        for phase,snapshot_data in [('source',before),('result',after)]:
            for field in ('heads','tails','matrices'):
                arrays[mode+'_'+phase+'_'+field+'_double']=snapshot_data[field]
                arrays[mode+'_'+phase+'_'+field+'_nativeFloat32']=snapshot_data[field].astype(np.float32)
    np.savez_compressed(out/'rest-byte-comparison.npz',jointNames=np.array(names),**arrays)
    report={'acceptedArt':False,'status':'READONLY_NATIVE_EDIT_ROUNDTRIP_MEASURED',
        'originalNative':{'path':str(SOURCE),'sha256':SOURCE_SHA},
        'recipe':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},
        'correction':{'path':str(correction_path),'sha256':sha(correction_path)},
        'proposal':{'path':str(proposal_path),'sha256':sha(proposal_path)},
        'arrays':{'path':str(out/'rest-byte-comparison.npz'),'sha256':sha(out/'rest-byte-comparison.npz')},
        'intendedAffectedRestFrames':sorted(affected),'comparisons':results,
        'limits':['Fresh original loads only; no bind, new native master, export, fields or anatomical qualification.',
                  'Recorded bit changes establish behavior; no tolerance relaxation or structural repair is authorized by this diagnostic.']}
    assert sha(SOURCE)==SOURCE_SHA
    (out/'edit-roundtrip.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],
        'changedRecords':{mode:[row['name'] for row in result['all75Records'] if not row['unchangedRecord']] for mode,result in results.items()}}))


SPEC=importlib.util.spec_from_file_location('readonly_builder',Path(__file__).with_name('build-native.py'))
BUILDER=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(BUILDER)
if __name__=='__main__':main()
