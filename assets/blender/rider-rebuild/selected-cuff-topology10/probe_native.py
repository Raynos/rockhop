"""Parent-only read-only native cuff ownership probe. Does not save or fit.

Run with Blender -b -t 2 --python-exit-code 1 --python THIS -- OUTPUT.json.
The output must be under docs/evidence/rider-rebuild/selected-cuff-topology10.
"""
import gc
import hashlib
import importlib.util
import json
import runpy
import sys
import traceback
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(row):
    path=ROOT/row['path']; assert sha(path)==row['sha256'], row['path']
    return path


def report_boundary(surgery, inner, G, plane):
    source=np.asarray(surgery.source,dtype=float); faces=np.asarray(surgery.faces)
    ids=np.flatnonzero(np.all(source[faces,1] <= plane+1e-8,axis=1))
    edges=G['edges_of'](surgery,ids)
    inner_keys={tuple(sorted((a,b))) for _,_,a,b in inner}
    actual={key for key,rows in edges.items() if len(rows)==1}
    outer=[rows[0] for key,rows in edges.items() if len(rows)==1 and key not in inner_keys]
    rings=G['ring_components'](outer)
    return {'bandTriangles':len(ids),'innerBoundaryEdges':len(inner),
            'innerEdgesPresentInBandBoundary':len(actual&inner_keys),
            'unmatchedInnerEdges':len(inner_keys-actual),
            'outerComponents':[{'vertices':len(r),'sourceYRange':[float(source[r,1].min()),float(source[r,1].max())],
                                'vertexIds':r} for r in rings],
            'newCutSourceYValues':np.unique(source[surgery.old_count:,1]).tolist(),
            'rawBandNonManifoldEdges':sum(len(v)>2 for v in edges.values())}


def main():
    out=Path(sys.argv[sys.argv.index('--')+1]).resolve()
    assert out.is_relative_to(ROOT/'docs/evidence/rider-rebuild/selected-cuff-topology10') and not out.exists()
    config=json.loads((ROOT/'assets/blender/rider-rebuild/astra-cuff-bearing18/input09.json').read_text())
    base_config=json.loads(pin(config['baseInput']).read_text()); prior=json.loads(pin(base_config['priorInputs']).read_text())
    path=pin(config['baseConstructor']); spec=importlib.util.spec_from_file_location('cuff10_base',path)
    B=importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
    B.A=runpy.run_path(str(pin(base_config['intersectionHelper'])))
    B.V=runpy.run_path(str(pin(base_config['volumeHelper'])))
    G=runpy.run_path(str(pin(config['cuffReconstructionHelper'])))
    donor=np.load(pin(prior['originalGloveDense'])); source=donor['vertices']
    placement=json.loads(pin(prior['placement']).read_text())
    settings={**base_config['settings'],**config['settings'],'sourceWrist':placement['sourceRest']['wrist']}
    bpy.ops.wm.open_mainfile(filepath=str(pin(prior['master'])))
    report={'acceptedArt':False,'status':'READ_ONLY_NATIVE_OWNERSHIP_PROBE','recipeSHA256':sha(Path(__file__)),
            'sourceMaster':prior['master'],'sourceGlove':prior['originalGloveDense'],'hands':{},
            'limits':'No contact fit, lining, native save, dense intersection gate, export, or moving-art result.'}
    for side in ('L','R'):
        print('PROBE actual native cuff '+side,flush=True)
        dump=np.load(pin(prior['guideArrays'][side])); obj=bpy.data.objects['ActualSelectedGlove.'+side]
        row={}; report['hands'][side]=row
        for mode in ('originalFloat32','exactFloat64Source'):
            s=B.Surgery(obj, source if mode=='originalFloat32' else source.astype(float))
            row.setdefault('nativeSourceVertexCount',len(s.source))
            row.setdefault('nativeTriangleCount',len(s.faces))
            row.setdefault('nativeFacesMatchDonorIgnoringWinding',bool(np.array_equal(np.sort(s.base_faces,axis=1),np.sort(donor['faces'],axis=1))))
            inner,floor=B.floor_cut(s,dump,settings['gloveFloorCutY'])
            row[mode]={'floor':floor,'boundary':report_boundary(s,inner,G,settings['gloveFloorCutY'])}
            if mode=='exactFloat64Source':
                scale,xb,zb=B.V['cuff_frame'](dump,placement['hands'][side])
                _,x,z=B.V['source_cuff'](np.asarray(s.source),dump,settings['sourceWrist'],scale,xb,zb)
                try:
                    rim,ownership=G['remove_inner_return'](s,inner,x,z,settings)
                    row[mode]['returnOwnership']=ownership
                    row[mode]['returnTopologyCompleted']=True
                except Exception:
                    row[mode]['returnTopologyCompleted']=False
                    row[mode]['returnTopologyError']=traceback.format_exc()
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text(json.dumps(report,indent=2)+'\n')
            del s; gc.collect()
    assert all(r['exactFloat64Source']['returnTopologyCompleted'] for r in report['hands'].values()), 'Native return topology remains unresolved; inspect evidence, do not fit.'
    print(json.dumps({side:{mode:{'outerComponents':[x['vertices'] for x in r[mode]['boundary']['outerComponents']],
                                'matchedInnerEdges':r[mode]['boundary']['innerEdgesPresentInBandBoundary']} for mode in ('originalFloat32','exactFloat64Source')} for side,r in report['hands'].items()}),flush=True)


if __name__=='__main__':
    main()
