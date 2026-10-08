"""Read-only exact Surgery clip replay on selected original cuff source triangles.

No fit, native save, topology repair, or radius change. The original cutter
methods are extracted unchanged so float32 interpolation is reproduced.
"""
import ast
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT/'assets/blender/rider-rebuild/astra-character-construction12/construct.py'
DONOR = ROOT/'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/gloves/cleaned-donor.npz'
EXPECTED_BASE = '5d13de71e8d724f01cdbd9aa4d0d18e3d351c58f58cc4513d98f5a325f9d1361'
EXPECTED_DONOR = 'f07a705f334d3d2b802fa7d23baec3e9cd54b211d160b7bbd6ab2c9f4a96541c'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(edges):
    graph = defaultdict(set)
    for a, b in edges:
        graph[a].add(b); graph[b].add(a)
    pending = set(graph); result = []
    while pending:
        found = {min(pending)}; todo = list(found)
        while todo:
            for n in graph[todo.pop()]-found:
                found.add(n); todo.append(n)
        pending -= found
        result.append(sorted(found))
    return result, sorted(set(map(len, graph.values())))


def summarize(source, faces, tolerance, weld=False):
    ids = np.flatnonzero(np.all(source[faces, 1] <= -.65+tolerance, axis=1))
    identity = np.unique(np.round(source, 8), axis=0, return_inverse=True)[1] if weld else np.arange(len(source))
    edges = defaultdict(list)
    for fi in ids:
        face = faces[fi]
        for a, b in zip(face, np.roll(face, -1)):
            key = tuple(sorted((int(identity[a]), int(identity[b]))))
            if key[0] != key[1]:
                edges[key].append((int(fi), int(a), int(b)))
    boundary = [e for e, rows in edges.items() if len(rows) == 1]
    rings, degree = components(boundary)
    # Recover exact source vertex identity even when incidence is welded.
    native = {int(identity[i]):i for i in np.unique(faces[ids])}
    rows = []
    for ring in rings:
        actual = [int(native[i]) for i in ring]
        pts = source[actual]
        rows.append({'vertices':len(actual), 'sourceYRange': [float(pts[:,1].min()),float(pts[:,1].max())],
                     'bounds': [pts.min(axis=0).tolist(),pts.max(axis=0).tolist()],
                     'vertexIds':actual})
    return {'selectedFaces':len(ids),'boundaryComponents':sorted(rows,key=lambda r:-r['vertices']),
            'boundaryDegrees':degree,'nonManifoldEdges':sum(len(x)>2 for x in edges.values())}


def main():
    assert sha(BASE) == EXPECTED_BASE and sha(DONOR) == EXPECTED_DONOR
    tree = ast.parse(BASE.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Surgery')
    names = {'add','interpolate_vertex','cut'}
    cls.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in names]
    module = ast.Module(body=[cls], type_ignores=[]); ast.fix_missing_locations(module)
    env = {'np':np}; exec(compile(module, str(BASE), 'exec'),env)
    donor = np.load(DONOR); source = donor['vertices']; original = donor['faces']
    take = np.flatnonzero(np.any(source[original, 1] <= -.64,axis=1))
    f = original[take]
    s = env['Surgery'](); s.source=list(source.copy()); s.world=list(source.astype(float))
    s.parents=[[i,-1,-1] for i in range(len(source))]; s.coefficients=[[1.,0.,0.] for _ in source]
    s.vertex_roles=[0]*len(source); s.old_count=len(source); s.affected_vertices=set(); s.affected_faces=set(); s.edge_cache={}
    s.faces=f.tolist(); s.face_sources=take.tolist(); s.face_roles=[0]*len(f); s.corner_sources=[[-1]*3 for _ in f]
    s.uv=list(donor['originalCornerUV'][take]); s.material=[0]*len(f); s.smooth=[True]*len(f)
    s.cut(source[:,1] - -.65, np.ones(len(f),dtype=bool), keep_both=True)
    p=np.asarray(s.source); faces=np.asarray(s.faces)
    new=p[len(source):]
    report={'acceptedArt':False,'method':'Exact unchanged Surgery.add/interpolate_vertex/cut AST on every original triangle incident to source Y<=-.64. Both floor sides retained; no physical mesh mutation.',
            'originalSource':{'path':str(DONOR.relative_to(ROOT)),'sha256':sha(DONOR)},
            'baseCutter':{'path':str(BASE.relative_to(ROOT)),'sha256':sha(BASE)},
            'sparseSourceFaces':len(f),'clippedFacePieces':len(faces),'newCutVertices':len(new),
            'newCutYValues':np.unique(new[:,1]).tolist(),
            'actualFloat64Strict':summarize(p.astype(float),faces,1e-8), 'actualFloat64FloorTolerance':summarize(p.astype(float),faces,1e-7),
            'rawStrict':summarize(p,faces,1e-8), 'rawFloorTolerance':summarize(p,faces,1e-7),
            'weldedStrict':summarize(p,faces,1e-8,True),'weldedFloorTolerance':summarize(p,faces,1e-7,True)}
    out=ROOT/'docs/evidence/rider-rebuild/selected-cuff-topology10/boundary-source-probe.json'
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k: {**v,'boundaryComponents':[{'vertices':r['vertices'],'sourceYRange':r['sourceYRange']} for r in v['boundaryComponents']]} if isinstance(v,dict) and 'boundaryComponents' in v else v for k,v in report.items()},indent=2))


if __name__ == '__main__':
    main()
