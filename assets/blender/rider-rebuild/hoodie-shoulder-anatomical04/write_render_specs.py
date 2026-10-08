"""Cheap IO-only matched specs after the actual editable native has been saved.

python3 write_render_specs.py harness/out/.../authored01/author.json
No render or native loading. Uses the exact receipt/native hash and all7 meshes.
Parent runs the existing pinned neutral PBR renderer under its serial CPU2 lease.
"""
import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'docs/evidence/rider-rebuild/hoodie-shoulder-anatomical04/render-specs01'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block:=handle.read(1024*1024):h.update(block)
    return h.hexdigest()


def main():
    assert len(sys.argv)==2
    receipt_path=Path(sys.argv[1]).resolve()
    assert receipt_path.is_relative_to(ROOT/'harness/out/rider-rebuild/hoodie-shoulder-anatomical04')
    receipt=json.loads(receipt_path.read_text())
    assert receipt['stage']=='ACTUAL_BILATERAL_PANEL_GEOMETRY_AND_SELECTED_UV_SAVED_IN_WORKING_OUTFIT'
    assert receipt['accepted'] is False and len(receipt['visibleMeshes'])==7
    assert 'RiderBody' in receipt['visibleMeshes']
    native=(ROOT/receipt['native']['path']).resolve()
    assert sha(native)==receipt['native']['sha256']
    renderer=ROOT/'assets/blender/rider-rebuild/production-assembly01/render.py'
    renderer_sha='e50dd77cfa8ebf4f8a1efbfa81beeaea4e224cdef3b4fd82fe99bb81fd771e4b'
    assert sha(renderer)==renderer_sha
    assert not OUT.exists(), 'Keep existing matched specs frozen'
    cameras={
        'full-outfit':{'focus':[0,-.025,.90],'orthoScale':2.12,'height':1.0},
        'head-hoodie':{'focus':[0,0,1.45],'orthoScale':.92,'height':1.5},
    }
    OUT.mkdir(parents=True)
    specs=[]
    for label,camera in cameras.items():
        z=camera['height']
        spec={'accepted':False,'native':receipt['native'],'mode':'stills',
              'objects':receipt['visibleMeshes'],'bodyObject':'RiderBody','rigObject':'RiderSkeleton',
              'focus':camera['focus'],'orthoScale':camera['orthoScale'],
              'views':{'front':[0,-4,z],'rear':[0,4,z],
                       'left-profile':[4,0,z],'right-profile':[-4,0,z]},
              'privateAuthoringContext':True,
              'bodyContextStatus':'EXACT_UNCHANGED_CONDITIONED_NECK02_WORKING_CONTEXT_UNACCEPTED',
              'limits':['Actual saved clothed source context only. Every actual mesh remains visible in each camera.',
                        'One actual authored axillary panel candidate with original selected PBR; body skin remains visible. No visual acceptance.',
                        'Stills cannot accept motion; no bake, native save or player export.']}
        path=OUT/(label+'.json');path.write_text(json.dumps(spec,indent=2)+'\n')
        destination='harness/out/rider-rebuild/production-assembly01/hoodie-panel04-'+label
        specs.append({'spec':{'path':str(path.relative_to(ROOT)),'sha256':sha(path)},
                      'output':destination,'views':4,
                      'command':['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','2',
                                 '--python-exit-code','1','--python',str(renderer.relative_to(ROOT)),
                                 '--',str(path.relative_to(ROOT)),destination]})
    report={'accepted':False,'stage':'SAVED_NATIVE_EXACT_HASH_MATCHED_CAMERA_SPECS_READY_NO_RENDER',
            'native':receipt['native'],'authorReceiptSHA256':sha(receipt_path),
            'writerSHA256':sha(__file__),'renderer':{'path':str(renderer.relative_to(ROOT)),'sha256':renderer_sha},
            'allSevenVisibleMeshes':receipt['visibleMeshes'],'specs':specs,
            'studio':'Existing matched neutral PBR: Cycles CPU2,12samples,640square,AgX; unchanged key/fill/rim.',
            'limits':['Parent controls serial CPU2 execution and judges. No render executed by spec writer.',
                      'Existing renderer confines fresh outputs to production-assembly01; source master remains in hoodie-shoulder-anatomical04.',
                      'All R0–R5 open. Private working context; no final outfit or motion claim.']}
    (OUT/'readiness.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'stage':report['stage'],'native':receipt['native'],
                      'specFiles':[s['spec']['path'] for s in specs],'noRenderExecuted':True},indent=2))


if __name__=='__main__':main()
