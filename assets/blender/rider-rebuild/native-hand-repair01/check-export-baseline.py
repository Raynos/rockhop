"""Read-only original GLB calibration for cutoff and bone-local basis proof."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[4]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
    out=ROOT/args.out;assert not out.exists()
    source=ROOT/'assets/blender/rider-rebuild/glove-charts01/prepare-target.py'
    spec=importlib.util.spec_from_file_location('baseline_reader',source)
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    paths={'glb':'harness/out/rider-rebuild/construction01/combined04/rider.glb',
           'four':'harness/out/rider-rebuild/construction01/rig04/weights-four.json',
           'contract':'harness/out/rider-rebuild/construction01/combined04/rider-contract.json'}
    expected={'glb':'58677cc37aff6b22bb98144762eb5a93dfe689ac207ea0b74a214ba60538f6fc',
              'four':'9ce2e702f65c6ea1492750b0e1066e923a96fcb4bcbd301525a38e2d3503c3af',
              'contract':'32d67e9031bd6865a561ba29dc6d2765ace49ad13bfb08bd61df07df85440ee4'}
    pins={key:{'path':path,'sha256':sha(ROOT/path)} for key,path in paths.items()}
    assert all(pins[key]['sha256']==expected[key] for key in pins)
    document,accessor=reader.glb(ROOT/paths['glb'])
    node=next(n for n in document['nodes'] if n.get('name')=='RiderBody')
    skin=document['skins'][node['skin']]
    primitive=document['meshes'][node['mesh']]['primitives'][0]
    ids=accessor(primitive['attributes']['_SOURCE_VERTEX_ID']).ravel().astype(int)
    names=[document['nodes'][i]['name'] for i in skin['joints']];lookup={name:i for i,name in enumerate(names)}
    four=json.loads((ROOT/paths['four']).read_text());native=np.zeros((len(four),75),dtype=np.float32)
    for vertex,row in enumerate(four):
        for name,weight in row:native[vertex,lookup[name]]=weight
    source_fields=native[ids].astype(float)
    cutoff=.0001;expected_fields=np.where(source_fields>cutoff,source_fields,0)
    removed=(source_fields-expected_fields).sum(1);expected_fields/=expected_fields.sum(1)[:,None]
    joints=accessor(primitive['attributes']['JOINTS_0']).astype(int)
    weights=accessor(primitive['attributes']['WEIGHTS_0']);actual=np.zeros_like(expected_fields)
    for slot in range(4):actual[np.arange(len(ids)),joints[:,slot]]+=weights[:,slot]
    coefficient_error=float(np.max(abs(actual-expected_fields)));assert coefficient_error<2e-7
    contract=json.loads((ROOT/paths['contract']).read_text());rest={row['name']:row for row in contract['nativeRest']['bones']}
    convert=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]])
    inverse_bind=accessor(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    inverse_error=max(float(np.max(abs(inverse_bind[i]-(np.linalg.inv(rest[name]['matrix'])@convert.T))))
                      for i,name in enumerate(names));assert inverse_error<2e-6
    conjugation_error=max(float(np.max(abs(inverse_bind[i]-(convert@np.linalg.inv(rest[name]['matrix'])@convert.T))))
                         for i,name in enumerate(names))
    result={'acceptedArt':False,'status':'ORIGINAL_ONLY_READONLY_EXPORT_CALIBRATION_PASS',
        'recipe':{'path':str(Path(__file__).resolve().relative_to(ROOT)),'sha256':sha(__file__)},'inputPins':pins,
        'exportCutoff':cutoff,'exportCutoffComparison':'DROP coefficient <= cutoff then normalize retained native float32 fields',
        'maximumRemovedCutoffMass':float(removed.max()),'coefficientMaximumAfterExplicitCutoff':coefficient_error,
        'maximumNativeVsDecodedNamedCoefficientDelta':float(np.max(abs(actual-source_fields))),
        'boneLocalBasis':'Authored Blender bone-local axes retained; glTF Y-up changes world/input point basis only',
        'expectedInverseBind':'inverse(nativeRest) @ nativeToYUp.transpose()',
        'inverseBindMaximum':inverse_error,'incorrectBasisConjugationMaximum':conjugation_error,
        'limits':['Original transport calibration only; no Blender mutation, native derivative or moving anatomy qualification.']}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    for record in pins.values():assert sha(ROOT/record['path'])==record['sha256']
    print(json.dumps({key:result[key] for key in ('status','maximumRemovedCutoffMass','coefficientMaximumAfterExplicitCutoff','inverseBindMaximum')}))


if __name__=='__main__':main()
