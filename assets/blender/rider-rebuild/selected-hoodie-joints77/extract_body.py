"""Parent-only read of the exact47 complete wearer's own full skin fields.

No save or mutation. This does not use native02's different body surface.
"""
import hashlib
import json
from pathlib import Path
import runpy
import sys
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
COMPONENT={'path':'assets/blender/rider-rebuild/selected-sleeve-component47/component.py',
           'sha256':'6fcc124b1fe5cf69a3cd0cd4114ff3fc16b6bd3e7741fb4b2b7488648c6bbd87'}
RECEIPT={'path':'harness/out/rider-rebuild/selected-sleeve-component47/intake01/intake-qualified.json',
         'sha256':'55adfeb1c0a6ff43d640338af1062d05c2893b56695cc94fa79a46144fd532c5'}
BODY={'path':'harness/out/rider-rebuild/selected-seated-anatomical09/reference05/original-full-reference.npz',
      'sha256':'01f752d72e94dbab81cc7a193adbd2dd7bba26df919b48454d8937fa9665dcc5'}
NAME='RiderBody__FullAnatomyReference'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as stream:
        while block:=stream.read(1024*1024):h.update(block)
    return h.hexdigest()


def pin(path):
    path=Path(path).resolve();return {'path':str(path.relative_to(ROOT)),'sha256':sha(path)}


def checked(row):
    path=ROOT/row['path'];assert sha(path)==row['sha256'];return path


def main(output):
    output=Path(output).resolve()
    assert output.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77')and not output.exists()
    receipt=json.loads(checked(RECEIPT).read_text());C=runpy.run_path(str(checked(COMPONENT)))
    c=C['intake_gate'](receipt);H,geometry=C['helpers'](json.loads(checked(receipt['priorInput']).read_text()))
    assert bpy.ops.wm.open_mainfile(filepath=str(checked(receipt['native'])),use_scripts=False)=={'FINISHED'}
    rig=C['scoped'](bpy);assert C['canonical'](H['rest'](rig))==receipt['expectedRest']
    body=bpy.data.objects[NAME];assert body.matrix_world.is_identity
    actual=geometry(body);assert actual==c['protectedBefore']['fullReference']
    body.data.calc_loop_triangles()
    p=np.empty((len(body.data.vertices),3),np.float32);f=np.empty((len(body.data.loop_triangles),3),np.int32)
    body.data.vertices.foreach_get('co',p.ravel());body.data.loop_triangles.foreach_get('vertices',f.ravel())
    reference=np.load(checked(BODY))
    assert np.array_equal(p,reference[NAME+'_basis'])and np.array_equal(f,reference[NAME+'_triangles'])
    names=[g.name for g in body.vertex_groups];assert all(n in rig.data.bones for n in names)
    fields=np.zeros((len(p),len(names)),np.float32)
    for v in body.data.vertices:
        for group in v.groups:fields[v.index,group.group]=group.weight
    sums=fields.sum(1,dtype=np.float64)
    assert np.isfinite(fields).all()and fields.min()>=0 and np.all(sums>0)
    normalized=fields.astype(np.float64)/sums[:,None]
    arrays={'positions':p,'triangles':f,'groupNames':np.asarray(names),'rawNamedFields':fields,
            'normalizedNamedFields':normalized,'rawFieldSums':sums,
            'nativeIds':reference[NAME+'__NATIVE_ID'],'sourceVertexIds':reference[NAME+'__SOURCE_VERTEX_ID'],
            'regionIds':reference[NAME+'__REGION_ID']}
    assert geometry(body)==actual and C['canonical'](H['rest'](rig))==receipt['expectedRest']
    output.mkdir(parents=True);np.savez(output/'actual-body-fields.npz',**arrays)
    report={'status':'ACTUAL47_COMPLETE_REFERENCE_FULL_FIELDS_READ_ONLY','acceptedArt':False,
        'recipe':pin(__file__),'sourceReceipt':RECEIPT,'native':receipt['native'],'component':COMPONENT,
        'originalBodyCache':BODY,'rest':receipt['expectedRest'],'bodyGeometry':actual,
        'arrays':pin(output/'actual-body-fields.npz'),'nativeMutation':False,
        'vertices':len(p),'triangles':len(f),'groupNames':names,
        'maximumNonzeroSupports':int((fields>0).sum(1).max()),
        'rawFieldSumRange':[float(sums.min()),float(sums.max())],
        'normalization':'All positive native groups divided by their total, matching native linear armature evaluation; raw fields retained exactly.',
        'arrayHashes':{k:hashlib.sha256(v.tobytes()).hexdigest()for k,v in arrays.items()}}
    (output/'actual-body-fields.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k]for k in ('status','vertices','triangles','maximumNonzeroSupports','rawFieldSumRange')}),flush=True)


if __name__=='__main__':main(sys.argv[sys.argv.index('--')+1])
