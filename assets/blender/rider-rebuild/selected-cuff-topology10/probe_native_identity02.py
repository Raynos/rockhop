"""Parent-only read-only native ownership replay with original floor identity.

No source coordinate edits, contact fit, lining, native save, or export.
Only six downstream source-floor membership predicates use the existing
floor_cut epsilon. The exact donor/cut ancestry must prove those IDs first.
"""
import hashlib
import importlib.util
import json
import runpy
import sys
import traceback
from pathlib import Path

import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(row):
    path=ROOT/row['path'];assert sha(path)==row['sha256'],row['path'];return path


def main():
    out=Path(sys.argv[sys.argv.index('--')+1]).resolve()
    assert out.is_relative_to(ROOT/'docs/evidence/rider-rebuild/selected-cuff-topology10') and not out.exists()
    config=json.loads((ROOT/'assets/blender/rider-rebuild/astra-cuff-bearing18/input09.json').read_text())
    base_config=json.loads(pin(config['baseInput']).read_text());prior=json.loads(pin(base_config['priorInputs']).read_text())
    path=pin(config['baseConstructor']);spec=importlib.util.spec_from_file_location('identity02_base',path)
    B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
    B.A=runpy.run_path(str(pin(base_config['intersectionHelper'])))
    B.V=runpy.run_path(str(pin(base_config['volumeHelper'])))
    helper=pin(config['cuffReconstructionHelper']).read_text()
    replacements={"settings['gloveFloorCutY']+1e-8":"settings['gloveFloorCutY']+1e-7",
                  "settings['gloveFloorCutY']) < 1e-8":"settings['gloveFloorCutY']) < 1e-7"}
    counts={a:helper.count(a) for a in replacements};assert sorted(counts.values())==[3,3],counts
    for before,after in replacements.items():helper=helper.replace(before,after)
    G={'__name__':'readonly_consistent_floor_identity'};exec(compile(helper,str(pin(config['cuffReconstructionHelper'])),'exec'),G)
    donor=np.load(pin(prior['originalGloveDense']));source=donor['vertices'];assert source.dtype==np.float32
    placement=json.loads(pin(prior['placement']).read_text())
    settings={**base_config['settings'],**config['settings'],'sourceWrist':placement['sourceRest']['wrist']}
    bpy.ops.wm.open_mainfile(filepath=str(pin(prior['master'])))
    report={'acceptedArt':False,'status':'READ_ONLY_NATIVE_CONSISTENT_FLOOR_IDENTITY','recipeSHA256':sha(Path(__file__)),
            'sourceMaster':prior['master'],'sourceGlove':prior['originalGloveDense'],
            'downstreamPredicateReplacementCounts':counts,'modifiedHelperSHA256':hashlib.sha256(helper.encode()).hexdigest(),
            'sourceCoordinatesEdited':False,'floorCutterEdited':False,'existingFloorIdentityEpsilon':1e-7,'hands':{},
            'limits':'No fit, lining, native save, dense intersection gates, export, moving-art review or acceptance.'}
    for side in ('L','R'):
        print('PROBE original native floor identity '+side,flush=True)
        dump=np.load(pin(prior['guideArrays'][side]));obj=bpy.data.objects['ActualSelectedGlove.'+side]
        s=B.Surgery(obj,source);row={};report['hands'][side]=row
        assert np.array_equal(np.sort(s.base_faces,axis=1),np.sort(donor['faces'],axis=1))
        inner,row['floor']=B.floor_cut(s,dump,settings['gloveFloorCutY'])
        xyz=np.asarray(s.source,dtype=float);faces=np.asarray(s.faces);signed=source[:,1]-settings['gloveFloorCutY']
        tagged_plane=np.r_[signed==0,np.ones(len(xyz)-len(source),dtype=bool)]
        legacy_plane=abs(xyz[:,1]-settings['gloveFloorCutY'])<1e-7
        tagged_negative=np.r_[signed<=0,np.ones(len(xyz)-len(source),dtype=bool)]
        tagged_band=np.all(tagged_negative[faces],axis=1)
        legacy_band=np.all(xyz[faces,1]<=settings['gloveFloorCutY']+1e-7,axis=1)
        row['originalCoordinatesExactlyUnchanged']=bool(np.array_equal(xyz[:len(source)],source))
        row['existingFloorPlaneExactlyEqualsCutAncestry']=bool(np.array_equal(tagged_plane,legacy_plane))
        row['existingFloorBandExactlyEqualsNegativeClipAncestry']=bool(np.array_equal(tagged_band,legacy_band))
        assert all(row[k] for k in row if k!='floor'),row
        edges=G['edges_of'](s,np.flatnonzero(legacy_band));inner_keys={tuple(sorted(e[2:])) for e in inner}
        boundary_keys={k for k,r in edges.items() if len(r)==1}
        outer=[r[0] for k,r in edges.items() if len(r)==1 and k not in inner_keys]
        row['matchedInnerBoundaryEdges']=len(inner_keys&boundary_keys)
        row['outerBoundaryVertexCounts']=[len(r) for r in G['ring_components'](outer)]
        assert inner_keys<=boundary_keys
        scale,xb,zb=B.V['cuff_frame'](dump,placement['hands'][side])
        _,x,z=B.V['source_cuff'](xyz,dump,settings['sourceWrist'],scale,xb,zb)
        try:
            rim,ownership=G['remove_inner_return'](s,inner,x,z,settings)
            row['returnOwnership']=ownership
            p=np.asarray(s.source,dtype=float);f=np.asarray(s.faces)
            exterior=np.flatnonzero(np.all(p[f,1]<=settings['gloveFloorCutY']+1e-7,axis=1))
            outer_edges=[r[0] for r in G['edges_of'](s,exterior).values() if len(r)==1]
            proximal=[e for e in outer_edges if abs(p[e[2],1]-settings['gloveFloorCutY'])<1e-7 and abs(p[e[3],1]-settings['gloveFloorCutY'])<1e-7]
            row['finalProximalBoundaryVertices']=len(G['one_ring'](proximal))
            row['finalRimCircuitVertices']=[len(r) for r in G['ring_components'](rim)]
            row['noUnownedFinalExteriorEdges']=len(outer_edges)==len(proximal)+len(rim)
            assert row['noUnownedFinalExteriorEdges']
            row['returnTopologyCompleted']=True
        except Exception:
            row['returnTopologyCompleted']=False;row['returnTopologyError']=traceback.format_exc()
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
    assert all(r['returnTopologyCompleted'] for r in report['hands'].values()),'Actual return topology remains unresolved; do not construct.'
    print(json.dumps({side:{k:v for k,v in r.items() if k not in ('returnOwnership','floor')} for side,r in report['hands'].items()}),flush=True)


if __name__=='__main__':main()
