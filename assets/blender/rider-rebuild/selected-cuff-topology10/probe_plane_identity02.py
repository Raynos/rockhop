"""Read-only exact cuff floor identity diagnosis, without any native construction."""
import ast
import hashlib
import json
import runpy
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
P=runpy.run_path(str(HERE/'probe_boundary.py'))


def surgery(source, donor, chosen):
    tree=ast.parse(P['BASE'].read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Surgery')
    cls.body=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in {'add','interpolate_vertex','cut'}]
    module=ast.Module(body=[cls],type_ignores=[]);ast.fix_missing_locations(module)
    env={'np':np};exec(compile(module,str(P['BASE']),'exec'),env)
    s=env['Surgery']();s.source=list(source.copy());s.world=list(source.astype(float))
    s.parents=[[i,-1,-1] for i in range(len(source))];s.coefficients=[[1.,0.,0.] for _ in source]
    s.vertex_roles=[0]*len(source);s.old_count=len(source);s.affected_vertices=set();s.affected_faces=set();s.edge_cache={}
    s.faces=donor['faces'][chosen].tolist();s.face_sources=chosen.tolist();s.face_roles=[0]*len(chosen)
    s.corner_sources=[[-1]*3 for _ in chosen];s.uv=list(donor['originalCornerUV'][chosen]);s.material=[0]*len(chosen);s.smooth=[True]*len(chosen)
    s.cut(source[:,1] - -.65,np.ones(len(chosen),dtype=bool),keep_both=True)
    return s


def floor_graph(s, identity):
    edges=set()
    for f in s.faces:
        for a,b in zip(f,f[1:]+f[:1]):
            if identity[a] and identity[b]:edges.add(tuple(sorted((a,b))))
    graph=defaultdict(set)
    for a,b in edges:graph[a].add(b);graph[b].add(a)
    rings,degrees=P['components'](edges)
    return {'edgeCount':len(edges),'componentVertexCounts':sorted(map(len,rings),reverse=True),'degrees':degrees,
            'nonRingVertices':[{'id':int(v),'neighbors':sorted(map(int,n)),'source':np.asarray(s.source[v]).tolist(),
                                'original':v<s.old_count,'parents':s.parents[v],'coefficients':s.coefficients[v]}
                               for v,n in graph.items() if len(n)!=2]}


def main():
    assert P['sha'](P['BASE'])==P['EXPECTED_BASE'] and P['sha'](P['DONOR'])==P['EXPECTED_DONOR']
    donor=np.load(P['DONOR']);original=donor['vertices'];faces=donor['faces']
    chosen=np.flatnonzero(np.any(original[faces,1]<=-.64,axis=1))
    report={'acceptedArt':False,'status':'READ_ONLY_PLANE_IDENTITY_DIAGNOSIS','recipeSHA256':P['sha'](Path(__file__)),
            'baseCutterSHA256':P['EXPECTED_BASE'],'originalDonorSHA256':P['EXPECTED_DONOR'],'modes':{}}
    for mode,source in [('originalFloat32',original),('rejectedExactFloat64',original.astype(float))]:
        s=surgery(source,donor,chosen);xyz=np.asarray(s.source);signed=source[:,1] - -.65
        # This is the floor cutter's exact existing test, not a new tolerance.
        legacy=np.array([abs(p[1] - -.65)<1e-7 for p in s.source])
        tagged=np.r_[signed==0,np.ones(len(s.source)-len(source),dtype=bool)]
        band_legacy=np.all(xyz[ np.asarray(s.faces),1] <= -.65+1e-7,axis=1)
        # Each negative half-space piece must only contain original <=0 or
        # exact newly inserted cut vertices. This avoids proximity altogether.
        nonpositive=np.r_[signed<=0,np.ones(len(s.source)-len(source),dtype=bool)]
        band_tagged=np.all(nonpositive[np.asarray(s.faces)],axis=1)
        row={'originalSignedZeroIds':np.flatnonzero(signed==0).tolist(),'newCutVertices':len(s.source)-len(source),
             'existingFloorGraph':floor_graph(s,legacy),'ancestryTaggedFloorGraph':floor_graph(s,tagged),
             'legacyPlaneIdsEqualTaggedIds':bool(np.array_equal(legacy,tagged)),
             'legacyBandEqualsTaggedNegativeSide':bool(np.array_equal(band_legacy,band_tagged)),
             'legacyBandTriangles':int(band_legacy.sum()),'taggedBandTriangles':int(band_tagged.sum()),
             'extraLegacyPlaneIds':np.flatnonzero(legacy&~tagged).tolist(),
             'maximumNewCutDistanceFromLiteralPlane':float(np.max(abs(xyz[len(source):,1].astype(float)+.65)))}
        report['modes'][mode]=row
    out=ROOT/'docs/evidence/rider-rebuild/selected-cuff-topology10/plane-identity-source-probe02.json'
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
