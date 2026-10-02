"""Read immutable original-source anatomical anchors; never compute fitted weights."""
from pathlib import Path
from collections import defaultdict
import ast, gzip, hashlib, json, re, struct, subprocess, time
import numpy as np
from scipy.spatial.transform import Rotation

R = Path('/Users/raynos/projects/games/rockhop')
B = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E = R / 'docs/evidence/hero-remaster/one-rider-v2/anatomical-field-design196'
sha = lambda b: hashlib.sha256(b).hexdigest()
pins = {}
start = time.monotonic()

def pin(p, expected=None):
    p = Path(p); b = p.read_bytes(); h = sha(b)
    assert expected is None or h == expected
    pins[str(p)] = {'sha256': h, 'bytes': len(b)}
    return b

def memory():
    s = subprocess.check_output(['vm_stat'], text=True)
    page = int(re.search(r'page size of (\d+)', s).group(1))
    gb = int(re.search(r'Anonymous pages:\s+(\d+)', s).group(1)) * page / 1e9
    assert gb < 70 and time.monotonic() - start < 890
    return gb

def save(name, obj):
    (E / name).write_text(json.dumps(obj, indent=2) + '\n')

memories = [memory()]
source = B / 'source-preserving-garment185/operator/rider.glb'
h = 'ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5'
pin(source, h)
reader = R / 'assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/prepare.py'
cls = next(n for n in ast.parse(pin(reader)).body if isinstance(n, ast.ClassDef) and n.name == 'GLB')
exec(compile(ast.Module(body=[cls], type_ignores=[]), str(reader), 'exec'), globals())
g = GLB(source, h)
a, F = g.primitive(0, 0)
U, q = np.unique(a['POSITION'], axis=0, return_inverse=True); PF = q[F]
base = R / 'docs/evidence/hero-remaster/one-rider-v2'
audit = json.loads(pin(base / 'source-weight-audit194/report.json'))
fields = json.loads(gzip.decompress(pin(base / 'source-weight-audit194/source-fields.json.gz')))
pin(base / 'source-weight-audit194/freeze.json')
construction = json.loads(pin(base / 'extrinsic-seam195/parent-construction-contract.json'))
review = json.loads(pin(base / 'physical-cut193/parent-review.json'))
seam = json.loads(pin(B / 'source-seam191/next-construction-contract.json'))
pin(base / 'physical-cut193/parent-construction-contract.json')
pin(base / 'source-seam191/freeze.json')
learnings = base / 'independent-pipeline-learnings-2026-10-01/README.md'
pin(learnings)
prior_recipe = R / 'assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3/scripts/experiment.py'
pin(prior_recipe)
pin(base / 'candidate-handoff170/mapping-report.json')
actual = json.loads(pin(base / 'source-rig188/actual-three/report.json'))
fixture = Path(actual['fixture']); pin(fixture, actual['fixtureSHA256'])
for rel in ['source-rig188/actual-three/evaluate.mts', 'source-rig188/actual-three/run_cpu.py', 'candidate-handoff170/map_candidate.py']:
    pin(R / 'assets/blender/hero-remaster/rider/one-rider-v2' / rel)

removed = set(review['removedSourceFaceIDs'])
assert len(removed) == 168 and {3823, 3824} <= removed
released = set(construction['exactReleasedInteriorPhysicalIDs'])
boundary = set(review['orientedFillBoundaryPhysicalIDs'])
assert len(released) == 46 and len(boundary) == 78
L194 = set(audit['parentProposedNextRegion']['remainingOriginalLeftRootedPhysicalVertexIDs'])
assert len(L194) == 1692
kept = [i for i in range(len(F)) if i not in removed]
present = set(int(i) for i in PF[kept].ravel())
L = (L194 & present) - released
adj = defaultdict(set); edge_faces = defaultdict(list)
for fi in kept:
    for k in range(3):
        i, j = map(int, [PF[fi, k], PF[fi, (k+1)%3]])
        edge_faces[tuple(sorted((i, j)))].append(fi)
        if i in L and j in L:
            adj[i].add(j); adj[j].add(i)
cuff = {r['physicalSourceID'] for r in fields['leftGloveBodyCuffRecords']}
assert len(cuff) == 65 and cuff <= L
frontier = {i for i in L if any(j not in L for e in edge_faces if i in e for j in e if j != i)}
high_seeds = (boundary & L) | frontier
def grow(seeds, rings):
    result = set(seeds)
    for _ in range(rings): result |= {j for i in result for j in adj[i]}
    return result
cuff_guard = grow(cuff, 2)
high_guard = grow(high_seeds, 2)
editable = L - cuff_guard - high_guard
aliases = defaultdict(list)
for row, i in enumerate(q): aliases[int(i)].append(row)
names = [g.d['nodes'][i]['name'].removeprefix('fresh.') for i in g.d['skins'][0]['joints']]
idx = {name: i for i, name in enumerate(names)}; rest = g.rest(); centres = rest[:, :3, 3]
S, A, W = [centres[idx[n]] for n in ['upperArm.L', 'forearm.L', 'hand.L']]
upper = A-S; fore = W-A; Lu = float(np.linalg.norm(upper)); Lf = float(np.linalg.norm(fore))
du, df = upper/Lu, fore/Lf
normal = du+df; normal /= np.linalg.norm(normal)
cuff_centre = U[sorted(cuff)].astype(float).mean(0)
scuff = Lu + float(np.dot(cuff_centre-A, df))
assert Lu < scuff < Lu+Lf
signed = np.einsum('ij,j->i', U.astype(float)-A, normal, optimize=False)
assert np.isfinite(signed).all()
crossings = []
for i, j in sorted(edge_faces):
    if i in L and j in L and signed[i]*signed[j] < 0:
        t = float(signed[i]/(signed[i]-signed[j]))
        crossings.append({'physicalEdge': [i,j], 'sourceFractionFromFirst': t,
                          'sourcePositionM': (U[i].astype(float)+t*(U[j].astype(float)-U[i])).tolist(),
                          'retainedIncidentOriginalFaces': edge_faces[(i,j)]})
cross_index = {tuple(r['physicalEdge']): k for k,r in enumerate(crossings)}
ring_adj = defaultdict(set); bad_faces = []
for fi in kept:
    t = PF[fi]; edges = [tuple(sorted(map(int,[t[k],t[(k+1)%3]]))) for k in range(3)]
    c = [cross_index[e] for e in edges if e in cross_index]
    if len(c) == 2: ring_adj[c[0]].add(c[1]); ring_adj[c[1]].add(c[0])
    elif c: bad_faces.append({'originalFaceID':fi,'crossingCount':len(c)})
remaining = set(range(len(crossings))); loops = []
while remaining:
    stack=[min(remaining)]; seen=set()
    while stack:
        i=stack.pop()
        if i in seen: continue
        seen.add(i); stack.extend(ring_adj[i]-seen)
    remaining -= seen; loops.append(sorted(seen))
scope = {'physicalIDConvention':'source185 p0 np.unique(Float32 POSITION,axis=0), lexicographic; never candidate dedup IDs',
         'source194LeftIDs':sorted(L194), 'sourceStarReleasedIDsExcluded':sorted(released & L194),
         'remainingSourceLeftIDs':sorted(L), 'fixed78BoundaryIDs':sorted(boundary),
         'fixedCuffIDs':sorted(cuff), 'fixedCuffTwoRingIDs':sorted(cuff_guard),
         'highMixedOwnershipSeedIDs':sorted(high_seeds), 'fixedHighTwoRingIDs':sorted(high_guard),
         'proposedEditablePhysicalIDs':sorted(editable),
         'proposedEditableP0Rows':sorted(row for i in editable for row in aliases[i]),
         'allEditableAliasGroups':{str(i):aliases[i] for i in sorted(editable)},
         'retainedOriginalGraphEdges':[[i,j] for i,j in sorted(edge_faces) if i in L and j in L],
         'elbowPlaneCrossings':crossings,'elbowPlaneComponents':loops}
save('source-anchors-and-scope.json',scope)
report = {'status':'READONLY_ANATOMICAL_FIELD_MECHANISM_DESIGN_NOT_REGISTERED_FOR_EXECUTION',
          'sourceSHA256':h,'candidateGeometryAttempts':0,'weightFieldsComputed':0,'weightsModified':0,
          'exports':0,'rigEdits':0,'GPUWork':False,
          'sourceLeft194Nodes':len(L194),'releasedOriginalLeftNodesExcluded':len(released & L194),
          'retainedSourceLeftNodes':len(L),'proposedEditableNodes':len(editable),
          'proposedEditableRows':len(scope['proposedEditableP0Rows']),
          'cuffGuardNodes':len(cuff_guard),'highGuardNodes':len(high_guard),
          'witnessPhysicalIDs':audit['witnessEdge']['physicalIDs'],
          'witnessesInsideProposedScope':{str(i):i in editable for i in audit['witnessEdge']['physicalIDs']},
          'jointPositionsM':{n:centres[idx[n]].tolist() for n in ['shoulder.L','upperArm.L','forearm.L','hand.L']},
          'upperLengthM':Lu,'forearmLengthM':Lf,'cuffSourceCentreM':cuff_centre.tolist(),
          'cuffLongitudinalStationM':scuff,'elbowPlaneUnitNormal':normal.tolist(),
          'elbowPlaneCrossingEdges':len(crossings),'elbowPlaneComponentSizes':[len(x) for x in loops],
          'elbowPlaneDegreeHistogram':{str(d):sum(len(ring_adj[i])==d for i in range(len(crossings))) for d in sorted({len(ring_adj[i]) for i in range(len(crossings))})},
          'elbowPlaneBadFaces':bad_faces,'named19':names,
          'seconds':time.monotonic()-start,'anonymousGBSamples':memories+[memory()],
          'inputPins':pins}
save('report.json',report)
for p, row in pins.items(): assert sha(Path(p).read_bytes()) == row['sha256']
print(json.dumps({k:v for k,v in report.items() if k not in ['inputPins','named19']}))
